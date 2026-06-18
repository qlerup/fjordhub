import json
import os
import re
import sqlite3
import threading
import unicodedata
from datetime import datetime, timedelta, timezone

from tracking import (
    SUPPORTED_SCAN_CARRIERS,
    build_tracking_url,
    classify_shipment_status,
    detect_carrier,
    gls_alias_key,
    gls_alias_preference,
    normalize_pickup_code,
    normalize_pickup_location,
    normalize_tracking_number,
)
from tracking_providers import TrackingLookupResult, fetch_tracking


DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join("data", "fjordparcel.db"))
INSTALL_STATE_PATH = os.getenv(
    "INSTALL_STATE_PATH",
    os.path.join(os.path.dirname(DATABASE_PATH) or ".", "fjordparcel.install.json"),
)
INSTALL_STATE_LOCK = threading.Lock()
SUPPORTED_CARRIER_SETTINGS = tuple(SUPPORTED_SCAN_CARRIERS)
DELIVERED_ARCHIVE_AFTER = timedelta(hours=24)
AUTOMATION_LOCK_NAME = "automation-worker"


def normalize_text(value, max_length=None):
    text = unicodedata.normalize("NFC", str(value or ""))
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if max_length is not None:
        text = text[: int(max_length)]
    return text


def normalize_optional_text(value, max_length=None):
    return normalize_text(value, max_length=max_length) or None


def normalize_key_text(value):
    return normalize_text(value).casefold()


def _as_utc(value):
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value or ""))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def _utc_now_datetime():
    return datetime.now(timezone.utc).replace(microsecond=0)


def utc_now():
    return _utc_now_datetime().isoformat()


def install_state_exists():
    return os.path.exists(INSTALL_STATE_PATH)


def install_state_db_path():
    return DATABASE_PATH


def mark_install_initialized(reason="unknown"):
    if install_state_exists():
        return
    with INSTALL_STATE_LOCK:
        if install_state_exists():
            return
        payload = {
            "app": "fjordparcel",
            "initialized": True,
            "initialized_at": utc_now(),
            "reason": str(reason or "unknown"),
            "db_path": DATABASE_PATH,
        }
        state_dir = os.path.dirname(INSTALL_STATE_PATH) or "."
        os.makedirs(state_dir, exist_ok=True)
        tmp_path = os.path.join(state_dir, f".{os.path.basename(INSTALL_STATE_PATH)}.{os.getpid()}.tmp")
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        os.replace(tmp_path, INSTALL_STATE_PATH)


def ensure_install_state_for_existing_users():
    try:
        if has_any_user():
            mark_install_initialized("existing-users")
    except Exception:
        pass


def get_connection():
    os.makedirs(os.path.dirname(DATABASE_PATH) or ".", exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS shipments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_number TEXT NOT NULL UNIQUE,
                pickup_location TEXT NOT NULL DEFAULT '',
                pickup_code TEXT NOT NULL DEFAULT '',
                label TEXT,
                label_source TEXT NOT NULL DEFAULT '',
                carrier TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Saved',
                status_code TEXT NOT NULL DEFAULT '',
                summary TEXT NOT NULL DEFAULT '',
                last_event_at TEXT NOT NULL DEFAULT '',
                last_event_text TEXT NOT NULL DEFAULT '',
                last_event_location TEXT NOT NULL DEFAULT '',
                events_json TEXT NOT NULL DEFAULT '[]',
                source TEXT NOT NULL DEFAULT 'manual',
                tracking_url TEXT NOT NULL,
                tracking_reference TEXT NOT NULL DEFAULT '',
                tracking_source TEXT NOT NULL DEFAULT '',
                tracking_error TEXT NOT NULL DEFAULT '',
                last_checked_at TEXT NOT NULL DEFAULT '',
                mail_subject TEXT,
                mail_from TEXT,
                mail_received_at TEXT,
                delivered_at TEXT NOT NULL DEFAULT '',
                archived_at TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL
            )
            """
        )
        _ensure_shipments_columns(db)
        _dedupe_gls_alias_shipments(db)
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS scan_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                messages_scanned INTEGER NOT NULL,
                tracking_numbers_found INTEGER NOT NULL,
                new_shipments INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS secure_settings (
                key TEXT PRIMARY KEY,
                value_encrypted TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS carrier_postcodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                carrier TEXT NOT NULL,
                postal_code TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(carrier, postal_code)
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS mail_account_settings (
                provider TEXT NOT NULL,
                username TEXT NOT NULL,
                auto_scan_enabled INTEGER NOT NULL DEFAULT 0,
                auto_scan_minutes INTEGER NOT NULL DEFAULT 30,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY(provider, username)
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'admin',
                created_at TEXT NOT NULL
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS automation_leader_lock (
                lock_name TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL,
                lease_expires_at TEXT NOT NULL,
                heartbeat_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        _ensure_users_columns(db)


def try_acquire_automation_leader_lock(owner_id, lease_seconds=30, lock_name=AUTOMATION_LOCK_NAME):
    owner = str(owner_id or "").strip()
    if not owner:
        return False

    now_dt = _utc_now_datetime()
    now = now_dt.isoformat()
    expires_at = (now_dt + timedelta(seconds=max(5, int(lease_seconds or 30)))).isoformat()

    with get_connection() as db:
        db.execute(
            """
            INSERT INTO automation_leader_lock (
                lock_name,
                owner_id,
                lease_expires_at,
                heartbeat_at,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(lock_name) DO UPDATE SET
                owner_id = excluded.owner_id,
                lease_expires_at = excluded.lease_expires_at,
                heartbeat_at = excluded.heartbeat_at,
                updated_at = excluded.updated_at
            WHERE automation_leader_lock.lease_expires_at <= ?
               OR automation_leader_lock.owner_id = excluded.owner_id
            """,
            (lock_name, owner, expires_at, now, now, now, now),
        )
        row = db.execute(
            "SELECT owner_id FROM automation_leader_lock WHERE lock_name = ?",
            (lock_name,),
        ).fetchone()

    return bool(row and str(row["owner_id"]) == owner)


def renew_automation_leader_lock(owner_id, lease_seconds=30, lock_name=AUTOMATION_LOCK_NAME):
    owner = str(owner_id or "").strip()
    if not owner:
        return False

    now_dt = _utc_now_datetime()
    now = now_dt.isoformat()
    expires_at = (now_dt + timedelta(seconds=max(5, int(lease_seconds or 30)))).isoformat()

    with get_connection() as db:
        cursor = db.execute(
            """
            UPDATE automation_leader_lock
            SET lease_expires_at = ?,
                heartbeat_at = ?,
                updated_at = ?
            WHERE lock_name = ? AND owner_id = ?
            """,
            (expires_at, now, now, lock_name, owner),
        )

    return bool(cursor.rowcount)


def release_automation_leader_lock(owner_id, lock_name=AUTOMATION_LOCK_NAME):
    owner = str(owner_id or "").strip()
    if not owner:
        return False

    with get_connection() as db:
        cursor = db.execute(
            "DELETE FROM automation_leader_lock WHERE lock_name = ? AND owner_id = ?",
            (lock_name, owner),
        )

    return bool(cursor.rowcount)


def _ensure_users_columns(db):
    existing = {row["name"] for row in db.execute("PRAGMA table_info(users)").fetchall()}
    if "role" not in existing:
        db.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'admin'")


def _ensure_shipments_columns(db):
    existing = {row["name"] for row in db.execute("PRAGMA table_info(shipments)").fetchall()}
    additions = {
        "pickup_location": "TEXT NOT NULL DEFAULT ''",
        "pickup_code": "TEXT NOT NULL DEFAULT ''",
        "status_code": "TEXT NOT NULL DEFAULT ''",
        "summary": "TEXT NOT NULL DEFAULT ''",
        "last_event_at": "TEXT NOT NULL DEFAULT ''",
        "last_event_text": "TEXT NOT NULL DEFAULT ''",
        "last_event_location": "TEXT NOT NULL DEFAULT ''",
        "events_json": "TEXT NOT NULL DEFAULT '[]'",
        "label_source": "TEXT NOT NULL DEFAULT ''",
        "tracking_reference": "TEXT NOT NULL DEFAULT ''",
        "tracking_source": "TEXT NOT NULL DEFAULT ''",
        "tracking_error": "TEXT NOT NULL DEFAULT ''",
        "last_checked_at": "TEXT NOT NULL DEFAULT ''",
        "delivered_at": "TEXT NOT NULL DEFAULT ''",
        "archived_at": "TEXT NOT NULL DEFAULT ''",
        "hidden_by": "TEXT NOT NULL DEFAULT ''",
    }
    for column, ddl in additions.items():
        if column not in existing:
            db.execute(f"ALTER TABLE shipments ADD COLUMN {column} {ddl}")


def row_to_dict(row):
    if not row:
        return None

    item = dict(row)
    tracking_digits = re.sub(r"\D+", "", str(item.get("tracking_number") or ""))
    raw_events = item.get("events_json")
    try:
        parsed_events = json.loads(str(raw_events or "[]"))
    except (TypeError, ValueError, json.JSONDecodeError):
        parsed_events = []

    item["events"] = parsed_events if isinstance(parsed_events, list) else []
    item["is_archived"] = bool(item.get("archived_at"))
    item["is_hidden"] = bool(item.get("hidden_by"))
    item["tracking_last_four_digits"] = tracking_digits[-4:] if len(tracking_digits) >= 4 else tracking_digits
    return item


def normalize_settings_carrier(carrier):
    normalized = str(carrier or "").strip().lower()
    lookup = {name.lower(): name for name in SUPPORTED_CARRIER_SETTINGS}
    canonical = lookup.get(normalized)
    if not canonical:
        raise ValueError("Carrier is not supported.")
    return canonical


def normalize_postal_code(value):
    cleaned = re.sub(r"[^0-9A-Za-z]", "", str(value or "").upper())
    if not cleaned:
        raise ValueError("Postal code is required.")
    if len(cleaned) < 3 or len(cleaned) > 10:
        raise ValueError("Postal code must be between 3 and 10 characters.")
    return cleaned


def _parse_datetime(value):
    if not value:
        return None
    try:
        return _as_utc(value)
    except (TypeError, ValueError):
        return None


def _latest_iso_value(*values):
    best_value = None
    best_datetime = None
    for value in values:
        parsed = _parse_datetime(value)
        if parsed and (best_datetime is None or parsed > best_datetime):
            best_value = value
            best_datetime = parsed
        elif value and best_value is None:
            best_value = value
    return best_value


def _should_replace_mail_metadata(existing_received_at, incoming_received_at):
    if not incoming_received_at:
        return False
    if not existing_received_at:
        return True

    existing_datetime = _parse_datetime(existing_received_at)
    incoming_datetime = _parse_datetime(incoming_received_at)
    if existing_datetime and incoming_datetime:
        return incoming_datetime >= existing_datetime
    return incoming_received_at >= existing_received_at


def _preferred_tracking_number(existing_number, incoming_number, carrier):
    if carrier != "GLS":
        return existing_number

    existing_normalized = normalize_tracking_number(existing_number)
    incoming_normalized = normalize_tracking_number(incoming_number)
    if (not existing_normalized.isdigit()) and incoming_normalized.isdigit():
        return incoming_normalized

    existing_key = gls_alias_key(existing_number)
    incoming_key = gls_alias_key(incoming_number)
    if not existing_key or existing_key != incoming_key:
        return existing_number

    if gls_alias_preference(incoming_number) > gls_alias_preference(existing_number):
        return incoming_number
    return existing_number


def _pickup_code_for_carrier(carrier, pickup_code):
    return normalize_pickup_code(pickup_code) or ""


def _pickup_location_for_carrier(carrier, pickup_location):
    return normalize_pickup_location(pickup_location) or ""


def _find_gls_alias(db, tracking_number, carrier):
    if carrier != "GLS":
        return None

    alias_key = gls_alias_key(tracking_number)
    if not alias_key:
        return None

    rows = db.execute("SELECT * FROM shipments WHERE carrier = 'GLS'").fetchall()
    matches = [row for row in rows if gls_alias_key(row["tracking_number"]) == alias_key]
    if not matches:
        return None

    return max(
        matches,
        key=lambda row: (
            gls_alias_preference(row["tracking_number"]),
            _parse_datetime(row["mail_received_at"]) or datetime.min.replace(tzinfo=timezone.utc),
            row["id"],
        ),
    )


def _find_gls_reference_match(db, tracking_number, carrier, label, mail_received_at, pickup_location="", pickup_code=""):
    if carrier != "GLS":
        return None

    incoming_number = normalize_tracking_number(tracking_number)
    if not incoming_number.isdigit():
        return None

    # Only attempt this fallback for pickup-ready mails that include pickup details.
    if not (_pickup_location_for_carrier(carrier, pickup_location) or _pickup_code_for_carrier(carrier, pickup_code)):
        return None

    normalized_label = normalize_text(label, max_length=120)
    if not normalized_label:
        return None

    rows = db.execute(
        """
        SELECT *
        FROM shipments
        WHERE carrier = 'GLS'
          AND COALESCE(label, '') = ?
        """,
        (normalized_label,),
    ).fetchall()

    matches = []
    for row in rows:
        existing_number = normalize_tracking_number(row["tracking_number"])
        if existing_number == incoming_number:
            continue
        if existing_number.isdigit():
            continue

        is_active = 1 if not str(row["archived_at"] or "") else 0
        matches.append((is_active, row["id"], row))

    if not matches:
        return None

    return max(matches, key=lambda item: (item[0], item[1]))[2]


def _cleanup_gls_reference_duplicates(db, keeper_id, tracking_number, label, mail_received_at, now_iso):
    if not label:
        return

    canonical_number = normalize_tracking_number(tracking_number)
    if not canonical_number.isdigit():
        return

    rows = db.execute(
        """
        SELECT *
        FROM shipments
        WHERE carrier = 'GLS'
          AND COALESCE(label, '') = ?
          AND id != ?
        """,
        (label, int(keeper_id)),
    ).fetchall()

    for row in rows:
        candidate_number = normalize_tracking_number(row["tracking_number"])
        if candidate_number.isdigit() or candidate_number == canonical_number:
            continue

        # Delete obsolete GLS reference rows for the same shipment label after numeric package ID is known.
        db.execute("DELETE FROM shipments WHERE id = ?", (int(row["id"]),))


def _refresh_existing_shipment(
    db,
    row,
    tracking_number,
    label,
    source,
    carrier,
    mail_subject,
    mail_from,
    mail_received_at,
    pickup_location,
    pickup_code,
    now,
):
    next_number = _preferred_tracking_number(row["tracking_number"], tracking_number, carrier)
    existing_pickup_location = str(row["pickup_location"] or "") if "pickup_location" in row.keys() else ""
    next_pickup_location = _pickup_location_for_carrier(carrier, pickup_location) or existing_pickup_location
    existing_pickup_code = str(row["pickup_code"] or "") if "pickup_code" in row.keys() else ""
    next_pickup_code = _pickup_code_for_carrier(carrier, pickup_code) or existing_pickup_code
    existing_label_source = str(row["label_source"] or "") if "label_source" in row.keys() else ""
    next_label = row["label"] or label
    next_label_source = existing_label_source
    if source == "mail" and label and existing_label_source != "manual":
        next_label = label
        next_label_source = "mail"
    elif label and not next_label_source:
        next_label_source = "mail" if source == "mail" else "manual"
    next_source = "mail" if source == "mail" else row["source"]
    next_mail_subject = row["mail_subject"] or mail_subject
    next_mail_from = row["mail_from"] or mail_from
    next_mail_received_at = row["mail_received_at"] or mail_received_at

    if source == "mail" and _should_replace_mail_metadata(row["mail_received_at"], mail_received_at):
        next_mail_subject = mail_subject or row["mail_subject"]
        next_mail_from = mail_from or row["mail_from"]
        next_mail_received_at = mail_received_at

    db.execute(
        """
        UPDATE shipments
        SET
            tracking_number = ?,
            pickup_location = ?,
            pickup_code = ?,
            label = ?,
            label_source = ?,
            source = ?,
            carrier = ?,
            tracking_url = ?,
            mail_subject = ?,
            mail_from = ?,
            mail_received_at = ?,
            updated_at = ?,
            last_seen_at = ?
        WHERE id = ?
        """,
        (
            next_number,
            next_pickup_location,
            next_pickup_code,
            next_label,
            next_label_source,
            next_source,
            carrier,
            build_tracking_url(next_number, carrier),
            next_mail_subject,
            next_mail_from,
            next_mail_received_at,
            now,
            now,
            row["id"],
        ),
    )
    return row["id"]


def _dedupe_gls_alias_shipments(db):
    rows = db.execute("SELECT * FROM shipments WHERE carrier = 'GLS'").fetchall()
    groups = {}
    for row in rows:
        alias_key = gls_alias_key(row["tracking_number"])
        if alias_key:
            groups.setdefault(alias_key, []).append(row)

    for group in groups.values():
        if len(group) < 2:
            continue

        keeper = max(
            group,
            key=lambda row: (
                gls_alias_preference(row["tracking_number"]),
                _parse_datetime(row["mail_received_at"]) or datetime.min.replace(tzinfo=timezone.utc),
                row["id"],
            ),
        )
        mail_row = max(
            group,
            key=lambda row: (
                _parse_datetime(row["mail_received_at"]) or datetime.min.replace(tzinfo=timezone.utc),
                row["id"],
            ),
        )
        label = keeper["label"] or next((row["label"] for row in group if row["label"]), None)
        pickup_location = keeper["pickup_location"] or next(
            (row["pickup_location"] for row in group if row["pickup_location"]),
            "",
        )
        pickup_code = keeper["pickup_code"] or next((row["pickup_code"] for row in group if row["pickup_code"]), "")
        source = "mail" if any(row["source"] == "mail" for row in group) else keeper["source"]
        last_seen_at = _latest_iso_value(*(row["last_seen_at"] for row in group)) or keeper["last_seen_at"]

        db.execute(
            """
            UPDATE shipments
            SET
                label = ?,
                pickup_location = ?,
                pickup_code = ?,
                source = ?,
                tracking_url = ?,
                mail_subject = ?,
                mail_from = ?,
                mail_received_at = ?,
                updated_at = ?,
                last_seen_at = ?
            WHERE id = ?
            """,
            (
                label,
                pickup_location,
                pickup_code,
                source,
                build_tracking_url(keeper["tracking_number"], "GLS"),
                mail_row["mail_subject"],
                mail_row["mail_from"],
                mail_row["mail_received_at"],
                utc_now(),
                last_seen_at,
                keeper["id"],
            ),
        )

        delete_ids = [row["id"] for row in group if row["id"] != keeper["id"]]
        db.executemany("DELETE FROM shipments WHERE id = ?", [(row_id,) for row_id in delete_ids])


def _shipment_category_from_row(row):
    return classify_shipment_status(
        carrier=row["carrier"],
        status=row["status"],
        status_code=row["status_code"],
        last_event_text=row["last_event_text"],
    )


def _delivery_fields_for_result(shipment, result, status, now_iso):
    category = classify_shipment_status(
        carrier=str(result.carrier or shipment.get("carrier") or ""),
        status=status,
        status_code=str(result.status_code or ""),
        last_event_text=str(result.last_event_text or ""),
    )
    if category != "delivered":
        return ""
    existing_delivered_at = str(shipment.get("delivered_at") or "")
    if existing_delivered_at:
        return existing_delivered_at

    event_datetime = _parse_datetime(result.last_event_at)
    return event_datetime.isoformat() if event_datetime else now_iso


def archive_due_delivered_shipments(now=None):
    current = _as_utc(now) if now is not None else _utc_now_datetime()
    current_iso = current.isoformat()
    archive_before = current - DELIVERED_ARCHIVE_AFTER
    archived_count = 0

    with get_connection() as db:
        rows = db.execute(
            """
            SELECT *
            FROM shipments
            WHERE COALESCE(archived_at, '') = ''
            """
        ).fetchall()

        for row in rows:
            category = _shipment_category_from_row(row)
            delivered_at = str(row["delivered_at"] or "")

            if category != "delivered":
                if delivered_at:
                    db.execute(
                        """
                        UPDATE shipments
                        SET delivered_at = '', updated_at = ?
                        WHERE id = ?
                        """,
                        (current_iso, row["id"]),
                    )
                continue

            delivered_datetime = _parse_datetime(delivered_at)
            if not delivered_datetime:
                delivered_datetime = _parse_datetime(row["last_event_at"])
                delivered_iso = delivered_datetime.isoformat() if delivered_datetime else current_iso
                if delivered_datetime and delivered_datetime <= archive_before:
                    db.execute(
                        """
                        UPDATE shipments
                        SET delivered_at = ?, archived_at = ?, updated_at = ?
                        WHERE id = ?
                        """,
                        (delivered_iso, current_iso, current_iso, row["id"]),
                    )
                    archived_count += 1
                    continue

                db.execute(
                    """
                    UPDATE shipments
                    SET delivered_at = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (delivered_iso, current_iso, row["id"]),
                )
                continue

            if delivered_datetime <= archive_before:
                db.execute(
                    """
                    UPDATE shipments
                    SET archived_at = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (current_iso, current_iso, row["id"]),
                )
                archived_count += 1

    return archived_count


def list_shipments(include_archived=False, current_user=None):
    clauses = []
    params = []
    if not include_archived:
        clauses.append("COALESCE(archived_at, '') = ''")
    if current_user is not None:
        clauses.append("(COALESCE(hidden_by, '') = '' OR hidden_by = ?)")
        params.append(current_user)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    with get_connection() as db:
        rows = db.execute(
            f"""
            SELECT *
            FROM shipments
            {where}
            ORDER BY datetime(last_seen_at) DESC, id DESC
            """,
            params,
        ).fetchall()
    return [row_to_dict(row) for row in rows]


def get_shipment(shipment_id):
    with get_connection() as db:
        row = db.execute("SELECT * FROM shipments WHERE id = ?", (shipment_id,)).fetchone()
    return row_to_dict(row)


def get_stats(current_user=None):
    with get_connection() as db:
        vis_filter = "COALESCE(archived_at, '') = '' AND (COALESCE(hidden_by, '') = '' OR hidden_by = ?)" if current_user else "COALESCE(archived_at, '') = ''"
        params = (current_user,) if current_user else ()
        active_filter = "COALESCE(archived_at, '') = '' AND (COALESCE(hidden_by, '') = '' OR hidden_by = ?)" if current_user else "COALESCE(archived_at, '') = ''"
        total = db.execute(f"SELECT COUNT(*) FROM shipments WHERE {vis_filter}", params).fetchone()[0]
        mail = db.execute(f"SELECT COUNT(*) FROM shipments WHERE source = 'mail' AND {vis_filter}", params).fetchone()[0]
        manual = db.execute(f"SELECT COUNT(*) FROM shipments WHERE source = 'manual' AND {vis_filter}", params).fetchone()[0]
        archived_params = (current_user,) if current_user else ()
        archived_filter = "(COALESCE(hidden_by, '') = '' OR hidden_by = ?)" if current_user else "1=1"
        archived = db.execute(f"SELECT COUNT(*) FROM shipments WHERE COALESCE(archived_at, '') != '' AND {archived_filter}", archived_params).fetchone()[0]
        latest_scan = db.execute(
            "SELECT * FROM scan_runs ORDER BY datetime(created_at) DESC, id DESC LIMIT 1"
        ).fetchone()
    return {
        "total": total,
        "mail": mail,
        "manual": manual,
        "archived": archived,
        "latest_scan": row_to_dict(latest_scan),
    }


def set_shipment_hidden(shipment_id, hidden_by):
    with get_connection() as db:
        db.execute(
            "UPDATE shipments SET hidden_by = ?, updated_at = ? WHERE id = ?",
            (hidden_by, utc_now(), int(shipment_id)),
        )
        row = db.execute("SELECT * FROM shipments WHERE id = ?", (int(shipment_id),)).fetchone()
    return row_to_dict(row)


def add_shipment(
    tracking_number,
    label=None,
    source="manual",
    carrier=None,
    mail_subject=None,
    mail_from=None,
    mail_received_at=None,
    pickup_location=None,
    pickup_code=None,
):
    number = normalize_tracking_number(tracking_number)
    if not number:
        raise ValueError("Tracking number is required.")

    label = normalize_optional_text(label, max_length=120)
    mail_subject = normalize_optional_text(mail_subject, max_length=500)
    mail_from = normalize_optional_text(mail_from, max_length=320)
    now = utc_now()
    carrier_name = carrier or detect_carrier(number, " ".join(filter(None, [mail_subject, mail_from])))
    tracking_url = build_tracking_url(number, carrier_name)
    normalized_pickup_location = _pickup_location_for_carrier(carrier_name, pickup_location)
    normalized_pickup_code = _pickup_code_for_carrier(carrier_name, pickup_code)

    with get_connection() as db:
        alias_row = _find_gls_alias(db, number, carrier_name)
        if alias_row:
            shipment_id = _refresh_existing_shipment(
                db,
                alias_row,
                number,
                label,
                source,
                carrier_name,
                mail_subject,
                mail_from,
                mail_received_at,
                normalized_pickup_location,
                normalized_pickup_code,
                now,
            )
            _cleanup_gls_reference_duplicates(db, shipment_id, number, label, mail_received_at, now)
            shipment = db.execute("SELECT * FROM shipments WHERE id = ?", (shipment_id,)).fetchone()
            return False, row_to_dict(shipment)

        reference_row = _find_gls_reference_match(
            db,
            number,
            carrier_name,
            label,
            mail_received_at,
            pickup_location=normalized_pickup_location,
            pickup_code=normalized_pickup_code,
        )
        if reference_row:
            try:
                shipment_id = _refresh_existing_shipment(
                    db,
                    reference_row,
                    number,
                    label,
                    source,
                    carrier_name,
                    mail_subject,
                    mail_from,
                    mail_received_at,
                    normalized_pickup_location,
                    normalized_pickup_code,
                    now,
                )
                db.execute(
                    "UPDATE shipments SET archived_at = '', delivered_at = '', updated_at = ? WHERE id = ?",
                    (now, int(shipment_id)),
                )
                _cleanup_gls_reference_duplicates(db, shipment_id, number, label, mail_received_at, now)
                shipment = db.execute("SELECT * FROM shipments WHERE id = ?", (shipment_id,)).fetchone()
                return False, row_to_dict(shipment)
            except sqlite3.IntegrityError:
                pass

        try:
            cursor = db.execute(
                """
                INSERT INTO shipments (
                    tracking_number,
                    pickup_location,
                    pickup_code,
                    label,
                    label_source,
                    carrier,
                    status,
                    source,
                    tracking_url,
                    mail_subject,
                    mail_from,
                    mail_received_at,
                    created_at,
                    updated_at,
                    last_seen_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'Saved', ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    number,
                    normalized_pickup_location,
                    normalized_pickup_code,
                    label,
                    "mail" if source == "mail" and label else ("manual" if label else ""),
                    carrier_name,
                    source,
                    tracking_url,
                    mail_subject,
                    mail_from,
                    mail_received_at,
                    now,
                    now,
                    now,
                ),
            )
            shipment_id = cursor.lastrowid
            created = True
        except sqlite3.IntegrityError:
            row = db.execute(
                "SELECT * FROM shipments WHERE tracking_number = ?",
                (number,),
            ).fetchone()
            created = False
            shipment_id = _refresh_existing_shipment(
                db,
                row,
                number,
                label,
                source,
                carrier_name,
                mail_subject,
                mail_from,
                mail_received_at,
                normalized_pickup_location,
                normalized_pickup_code,
                now,
            )

        shipment = db.execute("SELECT * FROM shipments WHERE id = ?", (shipment_id,)).fetchone()
    return created, row_to_dict(shipment)


def delete_shipment(shipment_id):
    with get_connection() as db:
        db.execute("DELETE FROM shipments WHERE id = ?", (shipment_id,))


def update_shipment_label(shipment_id, label):
    next_label = normalize_optional_text(label, max_length=120)
    next_label_source = "manual" if next_label else ""
    with get_connection() as db:
        db.execute(
            """
            UPDATE shipments
            SET label = ?, label_source = ?, updated_at = ?
            WHERE id = ?
            """,
            (next_label, next_label_source, utc_now(), shipment_id),
        )


def update_shipment_auto_label(shipment_id, label):
    next_label = normalize_optional_text(label, max_length=120)
    if not next_label:
        return get_shipment(shipment_id)

    with get_connection() as db:
        db.execute(
            """
            UPDATE shipments
            SET label = ?, label_source = 'mail', updated_at = ?
            WHERE id = ? AND COALESCE(label_source, '') != 'manual'
            """,
            (next_label, utc_now(), int(shipment_id)),
        )
        row = db.execute("SELECT * FROM shipments WHERE id = ?", (int(shipment_id),)).fetchone()
    return row_to_dict(row)


def update_shipment_mail_status(shipment_id, status, last_event_text=None, last_event_at=None, add_event=False):
    next_status = normalize_text(status, max_length=160) or "Saved"
    next_event_text = normalize_text(last_event_text or next_status, max_length=500)
    next_event_at = normalize_text(last_event_at or utc_now(), max_length=80)
    now = utc_now()

    with get_connection() as db:
        event_args = []
        event_sql = ""
        if add_event and next_event_text:
            row = db.execute("SELECT events_json FROM shipments WHERE id = ?", (int(shipment_id),)).fetchone()
            try:
                events = json.loads(str((row or {})["events_json"] or "[]")) if row else []
            except (TypeError, ValueError, json.JSONDecodeError):
                events = []
            if not isinstance(events, list):
                events = []

            next_event_key = normalize_key_text(next_event_text)

            def is_same_event(event):
                if not isinstance(event, dict):
                    return False
                event_text = normalize_key_text(event.get("description") or event.get("status") or "")
                return event_text == next_event_key

            if not any(is_same_event(event) for event in events):
                events = [
                    {
                        "description": next_event_text,
                        "status": "",
                        "date_iso": next_event_at,
                        "display_date": "",
                        "display_time": "",
                        "location": "",
                    },
                    *events,
                ]
            event_sql = ", events_json = ?"
            event_args.append(json.dumps(events[:30], ensure_ascii=False))

        db.execute(
            f"""
            UPDATE shipments
            SET
                status = ?,
                status_code = '',
                summary = '',
                last_event_at = ?,
                last_event_text = ?,
                tracking_error = '',
                updated_at = ?,
                last_seen_at = ?
                {event_sql}
            WHERE id = ?
            """,
            (
                next_status,
                next_event_at,
                next_event_text,
                now,
                now,
                *event_args,
                int(shipment_id),
            ),
        )
        row = db.execute("SELECT * FROM shipments WHERE id = ?", (int(shipment_id),)).fetchone()

    return row_to_dict(row)


def set_shipment_archived(shipment_id, archived=True):
    archived_at = utc_now() if archived else ""
    with get_connection() as db:
        db.execute(
            """
            UPDATE shipments
            SET archived_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (archived_at, utc_now(), int(shipment_id)),
        )
        row = db.execute("SELECT * FROM shipments WHERE id = ?", (int(shipment_id),)).fetchone()
    return row_to_dict(row)


def list_carrier_postcodes(carrier):
    carrier_name = normalize_settings_carrier(carrier)
    with get_connection() as db:
        rows = db.execute(
            """
            SELECT postal_code
            FROM carrier_postcodes
            WHERE carrier = ?
            ORDER BY postal_code
            """,
            (carrier_name,),
        ).fetchall()
    return [str(row["postal_code"]) for row in rows]


def list_all_carrier_postcodes():
    data = {carrier: [] for carrier in SUPPORTED_CARRIER_SETTINGS}
    with get_connection() as db:
        rows = db.execute(
            """
            SELECT carrier, postal_code
            FROM carrier_postcodes
            ORDER BY carrier, postal_code
            """
        ).fetchall()

    for row in rows:
        carrier = str(row["carrier"])
        if carrier not in data:
            continue
        data[carrier].append(str(row["postal_code"]))
    return data


def add_carrier_postcode(carrier, postal_code):
    carrier_name = normalize_settings_carrier(carrier)
    normalized_code = normalize_postal_code(postal_code)
    now = utc_now()

    with get_connection() as db:
        db.execute(
            """
            INSERT INTO carrier_postcodes (carrier, postal_code, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(carrier, postal_code) DO UPDATE SET updated_at = excluded.updated_at
            """,
            (carrier_name, normalized_code, now, now),
        )

    return normalized_code


def remove_carrier_postcode(carrier, postal_code):
    carrier_name = normalize_settings_carrier(carrier)
    normalized_code = normalize_postal_code(postal_code)
    with get_connection() as db:
        db.execute(
            "DELETE FROM carrier_postcodes WHERE carrier = ? AND postal_code = ?",
            (carrier_name, normalized_code),
        )


def _tracking_error_result(shipment, error):
    tracking_number = str((shipment or {}).get("tracking_number") or "")
    carrier = str((shipment or {}).get("carrier") or "tracking")
    return TrackingLookupResult(
        carrier=carrier,
        tracking_number=tracking_number,
        status="Fejl ved opdatering",
        tracking_url=str((shipment or {}).get("tracking_url") or build_tracking_url(tracking_number, carrier)),
        source="fjordparcel",
        error=str(error)[:260] or "Kunne ikke opdatere tracking",
    )


def refresh_shipment_tracking(shipment_id):
    shipment = get_shipment(shipment_id)
    if not shipment:
        raise LookupError("Shipment was not found.")

    number = str(shipment.get("tracking_number") or "")
    carrier = str(shipment.get("carrier") or "")
    postal_codes = list_carrier_postcodes(carrier) if carrier in SUPPORTED_CARRIER_SETTINGS else []

    try:
        result = fetch_tracking(number, carrier=carrier, postal_codes=postal_codes)
    except Exception as error:
        result = _tracking_error_result(shipment, error)

    resolved_number = number
    try:
        provider_number = normalize_tracking_number(result.tracking_number or number)
    except Exception:
        provider_number = number
    if provider_number and provider_number != number:
        if carrier == "GLS":
            resolved_number = _preferred_tracking_number(number, provider_number, carrier)
        else:
            resolved_number = provider_number

    now = utc_now()
    status = normalize_text(result.status or shipment.get("status") or "Saved", max_length=160) or "Saved"
    tracking_url = normalize_text(
        result.tracking_url or shipment.get("tracking_url") or build_tracking_url(resolved_number, carrier),
        max_length=500,
    )
    tracking_reference = normalize_text(result.reference_number or shipment.get("tracking_reference") or "", max_length=120)
    provider_pickup_location = "" if carrier == "DAO" else getattr(result, "pickup_location", "")
    pickup_location = _pickup_location_for_carrier(carrier, provider_pickup_location) or normalize_text(
        shipment.get("pickup_location") or "",
        max_length=180,
    )
    events_json = json.dumps((result.events or [])[:30], ensure_ascii=False)
    delivered_at = _delivery_fields_for_result(shipment, result, status, now)

    with get_connection() as db:
        if resolved_number != number:
            conflict = db.execute(
                "SELECT id FROM shipments WHERE tracking_number = ? AND id != ?",
                (resolved_number, int(shipment_id)),
            ).fetchone()
            if conflict:
                resolved_number = number
        db.execute(
            """
            UPDATE shipments
            SET
                tracking_number = ?,
                status = ?,
                status_code = ?,
                summary = ?,
                last_event_at = ?,
                last_event_text = ?,
                last_event_location = ?,
                pickup_location = ?,
                events_json = ?,
                tracking_url = ?,
                tracking_reference = ?,
                tracking_source = ?,
                tracking_error = ?,
                delivered_at = ?,
                updated_at = ?,
                last_checked_at = ?,
                last_seen_at = ?
            WHERE id = ?
            """,
            (
                resolved_number,
                status,
                normalize_text(result.status_code, max_length=120),
                normalize_text(result.summary, max_length=500),
                normalize_text(result.last_event_at, max_length=80),
                normalize_text(result.last_event_text, max_length=500),
                normalize_text(result.last_event_location, max_length=220),
                pickup_location,
                events_json,
                tracking_url,
                tracking_reference,
                normalize_text(result.source, max_length=120),
                normalize_text(result.error, max_length=260),
                delivered_at,
                now,
                now,
                now,
                int(shipment_id),
            ),
        )
        updated = db.execute("SELECT * FROM shipments WHERE id = ?", (int(shipment_id),)).fetchone()

    archive_due_delivered_shipments(now)
    return get_shipment(shipment_id) or row_to_dict(updated)


def record_scan_run(source, messages_scanned, tracking_numbers_found, new_shipments):
    with get_connection() as db:
        db.execute(
            """
            INSERT INTO scan_runs (
                source,
                messages_scanned,
                tracking_numbers_found,
                new_shipments,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (source, messages_scanned, tracking_numbers_found, new_shipments, utc_now()),
        )


def _normalize_mail_account_key(provider, username):
    provider_key = str(provider or "").strip().lower()
    username_key = normalize_key_text(username)
    if provider_key not in {"microsoft", "gmail"}:
        raise ValueError("Mail provider is not supported.")
    if not username_key:
        raise ValueError("Mail account is required.")
    return provider_key, username_key


def _normalize_auto_scan_minutes(value, default=30):
    try:
        minutes = int(value or default)
    except (TypeError, ValueError):
        minutes = default
    return max(5, min(1440, minutes))


def load_mail_account_settings(provider, username):
    provider_key, username_key = _normalize_mail_account_key(provider, username)
    with get_connection() as db:
        row = db.execute(
            """
            SELECT auto_scan_enabled, auto_scan_minutes
            FROM mail_account_settings
            WHERE provider = ? AND username = ?
            """,
            (provider_key, username_key),
        ).fetchone()

    if not row:
        return {
            "auto_scan_enabled": False,
            "auto_scan_minutes": 30,
        }
    return {
        "auto_scan_enabled": bool(row["auto_scan_enabled"]),
        "auto_scan_minutes": _normalize_auto_scan_minutes(row["auto_scan_minutes"]),
    }


def save_mail_account_settings(provider, username, form_values):
    provider_key, username_key = _normalize_mail_account_key(provider, username)
    auto_scan_enabled = str(form_values.get("auto_scan_enabled", "0")).lower() in {
        "1",
        "on",
        "true",
        "ja",
        "yes",
    }
    auto_scan_minutes = _normalize_auto_scan_minutes(form_values.get("auto_scan_minutes"), default=30)
    now = utc_now()

    with get_connection() as db:
        db.execute(
            """
            INSERT INTO mail_account_settings (
                provider,
                username,
                auto_scan_enabled,
                auto_scan_minutes,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(provider, username) DO UPDATE SET
                auto_scan_enabled = excluded.auto_scan_enabled,
                auto_scan_minutes = excluded.auto_scan_minutes,
                updated_at = excluded.updated_at
            """,
            (
                provider_key,
                username_key,
                1 if auto_scan_enabled else 0,
                auto_scan_minutes,
                now,
                now,
            ),
        )

    return load_mail_account_settings(provider_key, username_key)


def delete_mail_account_settings(provider, username):
    provider_key, username_key = _normalize_mail_account_key(provider, username)
    with get_connection() as db:
        db.execute(
            "DELETE FROM mail_account_settings WHERE provider = ? AND username = ?",
            (provider_key, username_key),
        )


def list_enabled_mail_account_scans():
    with get_connection() as db:
        rows = db.execute(
            """
            SELECT provider, username, auto_scan_minutes
            FROM mail_account_settings
            WHERE auto_scan_enabled = 1
            ORDER BY provider, username
            """
        ).fetchall()
    return [
        {
            "provider": row["provider"],
            "username": row["username"],
            "auto_scan_minutes": _normalize_auto_scan_minutes(row["auto_scan_minutes"]),
        }
        for row in rows
    ]


def has_any_user():
    with get_connection() as db:
        row = db.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()
        return row["cnt"] > 0


def create_user(name, username, password_hash, role="admin"):
    now = utc_now()
    display_name = normalize_text(name, max_length=120)
    username_key = normalize_key_text(username)
    with get_connection() as db:
        db.execute(
            "INSERT INTO users (name, username, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
            (display_name, username_key, password_hash, role, now),
        )


def get_user_by_username(username):
    with get_connection() as db:
        return db.execute(
            "SELECT * FROM users WHERE username = ?",
            (normalize_key_text(username),),
        ).fetchone()


def list_users():
    with get_connection() as db:
        rows = db.execute(
            "SELECT id, name, username, role, created_at FROM users ORDER BY created_at"
        ).fetchall()
    return [dict(row) for row in rows]


def delete_user(user_id):
    with get_connection() as db:
        db.execute("DELETE FROM users WHERE id = ?", (int(user_id),))


def update_user_role(user_id, role):
    if role not in ("admin", "user"):
        raise ValueError("Ugyldig rolle.")
    with get_connection() as db:
        db.execute("UPDATE users SET role=? WHERE id=?", (role, int(user_id)))
