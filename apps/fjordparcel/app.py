import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import atexit
from datetime import datetime, timezone
import random

from dotenv import load_dotenv

# Load environment variables early so runtime config is consistent in all start modes.
load_dotenv()

from flask import Flask, flash, jsonify, redirect, render_template, request, send_from_directory, session, url_for

from app_config import (
    save_google_settings,
    save_microsoft_settings,
    load_public_base_url,
    save_public_base_url,
    load_automation_settings,
    save_automation_settings,
)
import gmail_mail
import imap_mail
import mail_services
from gmail_mail import GmailMailError
from imap_mail import ImapMailError
from mail_services import MailServiceError
from werkzeug.security import check_password_hash, generate_password_hash

from storage import (
    SUPPORTED_CARRIER_SETTINGS,
    add_shipment,
    add_carrier_postcode,
    archive_due_delivered_shipments,
    create_user,
    delete_shipment,
    delete_mail_account_settings,
    delete_user,
    update_user_role,
    get_stats,
    get_user_by_username,
    has_any_user,
    ensure_install_state_for_existing_users,
    init_db,
    install_state_db_path,
    install_state_exists,
    list_enabled_mail_account_scans,
    list_all_carrier_postcodes,
    list_shipments,
    list_users,
    load_mail_account_settings,
    normalize_settings_carrier,
    mark_install_initialized,
    record_scan_run,
    release_automation_leader_lock,
    refresh_shipment_tracking,
    renew_automation_leader_lock,
    remove_carrier_postcode,
    save_mail_account_settings,
    set_shipment_archived,
    set_shipment_hidden,
    update_shipment_auto_label,
    update_shipment_label,
    update_shipment_mail_status,
    try_acquire_automation_leader_lock,
)
from tracking import (
    SUPPORTED_SCAN_CARRIERS,
    classify_shipment_status,
    extract_bring_mail_tracking_numbers,
    extract_dao_mail_event_text,
    extract_dao_mail_tracking_numbers,
    extract_fedex_mail_tracking_numbers,
    extract_gls_mail_label,
    extract_gls_mail_tracking_numbers,
    extract_postnord_mail_tracking_numbers,
    extract_gls_reference_numbers,
    extract_mail_label,
    extract_postnord_pickup_links,
    extract_postnord_pickup_page_details,
    extract_postnord_pincode,
    extract_pickup_code,
    extract_pickup_location,

    gls_alias_key,
    is_gls_ready_mail,
    is_postnord_ready_mail,
    normalize_gls_reference,
)


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "fjordparcel-dev-secret")
app.json.ensure_ascii = False
APP_BUILD = os.getenv("APP_BUILD", str(max(
    int(os.path.getmtime(__file__)),
    int(os.path.getmtime(os.path.join(os.path.dirname(__file__), "static", "styles.css")))
    if os.path.exists(os.path.join(os.path.dirname(__file__), "static", "styles.css")) else 0,
    int(os.path.getmtime(os.path.join(os.path.dirname(__file__), "static", "app.js")))
    if os.path.exists(os.path.join(os.path.dirname(__file__), "static", "app.js")) else 0,
)))

APP_UPDATE_SERVICE_URL = str(os.environ.get("FJORDPARCEL_UPDATER_URL", "http://fjordparcel-updater:8090") or "").strip().rstrip("/")
try:
    APP_UPDATE_SERVICE_TIMEOUT_SEC = float(os.environ.get("FJORDPARCEL_UPDATER_TIMEOUT_SEC", "20") or 20)
except Exception:
    APP_UPDATE_SERVICE_TIMEOUT_SEC = 20.0
APP_UPDATE_SERVICE_TIMEOUT_SEC = max(2.0, min(120.0, APP_UPDATE_SERVICE_TIMEOUT_SEC))

init_db()
ensure_install_state_for_existing_users()

SCAN_JOBS = {}
SCAN_JOBS_LOCK = threading.Lock()
SCAN_JOB_TTL_SECONDS = 60 * 60
SETTINGS_SECTIONS = {"general", "mails", "carriers", "users", "update"}
GLS_MERCHANT_LABEL_LOOKBACK_SECONDS = 7 * 24 * 60 * 60
POSTNORD_PICKUP_LINK_TIMEOUT_SECONDS = float(os.getenv("POSTNORD_PICKUP_LINK_TIMEOUT_SECONDS", "8") or "8")
POSTNORD_PICKUP_LINK_MAX_BYTES = 250_000

# Automation scheduler state
_AUTO_NEXT_SCAN_AT = {}
_AUTO_NEXT_REFRESH_AT = 0.0
_AUTO_THREAD_STARTED = False
_AUTO_LEADER_OWNER_ID = uuid.uuid4().hex
_AUTO_IS_LEADER = False
_AUTO_LEASE_SECONDS = max(10, int(str(os.getenv("FJORDPARCEL_AUTOMATION_LEASE_SECONDS", "45") or "45")) )
_AUTO_HEARTBEAT_INTERVAL_SECONDS = max(3, int(str(os.getenv("FJORDPARCEL_AUTOMATION_HEARTBEAT_SECONDS", "10") or "10")) )
_AUTO_NEXT_HEARTBEAT_AT = 0.0

_AUTH_EXEMPT = frozenset({
    "setup", "login", "logout", "hub_login",
    "api_health",
    "favicon_ico", "favicon_32_png", "favicon_16_png",
    "apple_touch_icon", "site_webmanifest",
    "manifest_webmanifest", "browserconfig_xml",
    "static",
})

_ADMIN_ONLY_ENDPOINTS = frozenset({
    "settings",
    "save_automation_config",
    "save_mail_account_automation_config",
    "save_microsoft_config",
    "save_google_config",
    "mail_connect",
    "microsoft_mail_connect",
    "mail_callback",
    "google_mail_connect",
    "google_mail_callback",
    "mail_disconnect",
    "disconnect_mail_account",
    "add_carrier_postal_code",
    "remove_carrier_postal_code_entry",
    "create_user_settings",
    "delete_user_settings",
    "save_track17_api_key",
})


def _setup_locked_response():
    message = "FjordParcel er allerede initialiseret, men databasen mangler eller er tom."
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": message, "recovery_required": True}), 503
    return render_template(
        "auth.html",
        mode="setup_locked",
        db_path=install_state_db_path(),
    ), 503


@app.before_request
def require_auth():
    if request.endpoint in _AUTH_EXEMPT or request.endpoint is None:
        return
    if _fjordhub_managed():
        if "user_id" not in session:
            return redirect(url_for("login"))
        if request.endpoint in _ADMIN_ONLY_ENDPOINTS and session.get("role") != "admin":
            flash("Du har ikke adgang til indstillinger.", "error")
            return redirect(url_for("index"))
        return
    if not has_any_user():
        if install_state_exists():
            return _setup_locked_response()
        if _FJORDHUB_API_KEY:
            if request.endpoint != "login":
                return redirect(url_for("login"))
            return None
        return redirect(url_for("setup"))
    ensure_install_state_for_existing_users()
    if "user_id" not in session:
        return redirect(url_for("login"))
    if "role" not in session:
        user = get_user_by_username(session["user_id"])
        if not user:
            session.clear()
            return redirect(url_for("login"))
        session["role"] = user["role"]
        session["user_name"] = user["name"]
    if request.endpoint in _ADMIN_ONLY_ENDPOINTS and session.get("role") != "admin":
        flash("Du har ikke adgang til indstillinger.", "error")
        return redirect(url_for("index"))


@app.template_filter("dmy")
def _format_dmy(value):
    text = str(value or "").strip()
    if not text:
        return ""
    # Try ISO8601
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        d = parsed.date()
        return f"{d.day:02d}-{d.month:02d}-{d.year:04d}"
    except Exception:
        pass
    # YYYY-MM-DD (or / .)
    m = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", text)
    if m:
        y, mth, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{d:02d}-{mth:02d}-{y:04d}"
    # DD-MM-YYYY
    m = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$", text)
    if m:
        d, mth, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{d:02d}-{mth:02d}-{y:04d}"
    # Fallback: first 10 chars may be date-like
    return text[:10]


def _settings_section(value):
    section = str(value or "").strip().lower()
    return section if section in SETTINGS_SECTIONS else "general"


def _settings_carrier(value):
    preferred = str(value or "").strip() or "GLS"
    try:
        return normalize_settings_carrier(preferred)
    except ValueError:
        if "GLS" in SUPPORTED_CARRIER_SETTINGS:
            return "GLS"
        return SUPPORTED_CARRIER_SETTINGS[0]


def _message_scan_text(message):
    from_info = (message.get("from") or {}).get("emailAddress") or {}
    sender = from_info.get("address") or from_info.get("name")
    subject = message.get("subject") or ""
    body_preview = message.get("bodyPreview") or ""
    body = message.get("body") or ""
    if isinstance(body, dict):
        body = body.get("content") or ""
    return f"{subject}\n{sender or ''}\n{body_preview}\n{body}"


def _message_received_datetime(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _nearest_gls_merchant_label(received_at, label_mentions):
    received_dt = _message_received_datetime(received_at)
    if received_dt is None:
        return None

    candidates = []
    for item in label_mentions:
        label = str(item.get("label") or "").strip()
        label_dt = item.get("received_dt")
        if not label or label_dt is None:
            continue
        delta_seconds = (received_dt - label_dt).total_seconds()
        if 0 <= delta_seconds <= GLS_MERCHANT_LABEL_LOOKBACK_SECONDS:
            candidates.append((delta_seconds, label))

    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    unique_labels = {label.casefold() for _delta, label in candidates}
    if len(unique_labels) != 1:
        return None
    return candidates[0][1]


def _gls_merchant_label_for_reference(reference_number, label_mentions):
    reference = normalize_gls_reference(reference_number)
    if not reference:
        return None

    matches = []
    for item in label_mentions:
        label = str(item.get("label") or "").strip()
        references = item.get("references") or []
        if label and reference in references:
            matches.append(label)

    if not matches:
        return None
    unique_labels = {label.casefold() for label in matches}
    if len(unique_labels) != 1:
        return None
    return matches[0]


def _fetch_postnord_pickup_link_text(url):
    request_obj = urllib.request.Request(
        url,
        headers={
            "User-Agent": "fjordparcel-mail-scan/1.0",
            "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request_obj, timeout=POSTNORD_PICKUP_LINK_TIMEOUT_SECONDS) as response:
        payload = response.read(POSTNORD_PICKUP_LINK_MAX_BYTES)
        charset = response.headers.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def _postnord_pickup_candidates_from_links(text):
    candidates = []
    seen = set()
    for link in extract_postnord_pickup_links(text):
        try:
            page_text = _fetch_postnord_pickup_link_text(link)
        except (OSError, TimeoutError, urllib.error.URLError, ValueError):
            app.logger.info("Could not read PostNord pickup link during mail scan: %s", link)
            continue

        details = extract_postnord_pickup_page_details(page_text)
        tracking_number = details.get("tracking_number")
        if not tracking_number or tracking_number in seen:
            continue
        seen.add(tracking_number)
        candidates.append(
            {
                "tracking_number": tracking_number,
                "carrier": "PostNord",
                "pickup_code": details.get("pickup_code"),
                "mail_ready_for_pickup": True,
            }
        )
    return candidates


def public_url_for(endpoint, **values):
    base_url = load_public_base_url()
    if base_url:
        return f"{base_url}{url_for(endpoint, **values)}"
    return url_for(endpoint, _external=True, **values)


def localhost_url_for(endpoint, **values):
    port = str(os.environ.get("APP_PORT", "8096") or "8096").strip()
    return f"http://localhost:{port}{url_for(endpoint, **values)}"


def _shipment_category(shipment):
    return classify_shipment_status(
        carrier=shipment.get("carrier"),
        status=shipment.get("status"),
        status_code=shipment.get("status_code"),
        last_event_text=shipment.get("last_event_text"),
    )


def connected_account():
    try:
        accounts = mail_services.get_accounts()
    except MailServiceError:
        return None
    return accounts[0] if accounts else None


def connected_accounts():
    try:
        return mail_services.get_accounts()
    except MailServiceError:
        return []


def _mail_account_from_values(values):
    provider = str(values.get("provider") or "").strip().lower()
    username = str(values.get("username") or "").strip()
    if not provider or not username:
        raise ValueError("Choose a mail account before scanning.")
    account = mail_services.find_account(provider, username)
    if not account:
        raise ValueError("The selected mail account is not connected.")
    return account


def _mail_account_settings_redirect(account):
    return redirect(
        url_for(
            "settings",
            section="mails",
            provider=account["provider"],
            account=account["username"],
        )
    )


def _new_scan_job(scan_days, account=None):
    job_id = uuid.uuid4().hex
    now = time.time()
    job = {
        "id": job_id,
        "state": "queued",
        "stage": "Queued",
        "days": scan_days,
        "provider": account.get("provider") if account else "",
        "username": account.get("username") if account else "",
        "account_label": account.get("username") if account else "",
        "scanned": 0,
        "total": None,
        "found": 0,
        "new_shipments": 0,
        "messages_scanned": 0,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }
    with SCAN_JOBS_LOCK:
        _cleanup_scan_jobs_locked(now)
        SCAN_JOBS[job_id] = job
    return job_id


def _cleanup_scan_jobs_locked(now=None):
    current_time = now or time.time()
    expired_ids = [
        job_id
        for job_id, job in SCAN_JOBS.items()
        if current_time - job.get("updated_at", job.get("created_at", current_time)) > SCAN_JOB_TTL_SECONDS
    ]
    for job_id in expired_ids:
        SCAN_JOBS.pop(job_id, None)


def _update_scan_job(job_id, **updates):
    with SCAN_JOBS_LOCK:
        job = SCAN_JOBS.get(job_id)
        if not job:
            return
        job.update(updates)
        job["updated_at"] = time.time()


def _get_scan_job(job_id):
    with SCAN_JOBS_LOCK:
        job = SCAN_JOBS.get(job_id)
        return dict(job) if job else None


def _scan_messages(scan_days, progress_callback, only_today=False, provider=None, username=None):
    found = 0
    created_count = 0
    messages_scanned = 0
    found_keys = set()
    refreshed_keys = set()
    if provider and username:
        messages = list(
            mail_services.iter_recent_messages(
                scan_days,
                progress_callback=progress_callback,
                provider=provider,
                username=username,
            )
        )
    else:
        messages = list(mail_services.iter_recent_messages(scan_days, progress_callback=progress_callback))
    if only_today:
        today_utc = datetime.now(timezone.utc).date()
        filtered = []
        for m in messages:
            dt = _message_received_datetime(m.get("receivedDateTime"))
            if dt and dt.astimezone(timezone.utc).date() == today_utc:
                filtered.append(m)
        messages = filtered
    label_mentions = []

    for message in messages:
        received_at = message.get("receivedDateTime")
        text = _message_scan_text(message)
        label = extract_gls_mail_label(text)
        if label:
            label_mentions.append({
                "label": label,
                "received_dt": _message_received_datetime(received_at),
                "references": extract_gls_reference_numbers(text),
            })

    extracted = []
    for message in messages:
        messages_scanned += 1
        from_info = (message.get("from") or {}).get("emailAddress") or {}
        sender = from_info.get("address") or from_info.get("name")
        subject = message.get("subject") or ""
        received_at = message.get("receivedDateTime")
        text = _message_scan_text(message)

        candidates = []
        candidates.extend(_postnord_pickup_candidates_from_links(text))
        seen_numbers = {(c["carrier"], c["tracking_number"]) for c in candidates}
        for _carrier, _nums in (
            ("DAO", extract_dao_mail_tracking_numbers(text)),
            ("Bring", extract_bring_mail_tracking_numbers(text)),
            ("GLS", extract_gls_mail_tracking_numbers(text)),
            ("PostNord", extract_postnord_mail_tracking_numbers(text)),
            ("FedEx", extract_fedex_mail_tracking_numbers(text)),
        ):
            for _num in _nums:
                if (_carrier, _num) not in seen_numbers:
                    candidates.append({"tracking_number": _num, "carrier": _carrier, "tracking_url": ""})
                    seen_numbers.add((_carrier, _num))

        postnord_ready_mail = is_postnord_ready_mail(text)
        gls_ready_mail = is_gls_ready_mail(text)

        for candidate in candidates:
            carrier = candidate.get("carrier")
            if carrier not in SUPPORTED_SCAN_CARRIERS:
                continue

            pickup_location = extract_pickup_location(text, carrier)
            if carrier == "PostNord":
                pickup_code = candidate.get("pickup_code") or extract_postnord_pincode(text)
            else:
                pickup_code = candidate.get("pickup_code") or extract_pickup_code(text, carrier)

            mail_ready_for_pickup = (
                carrier == "PostNord" and (candidate.get("mail_ready_for_pickup") or postnord_ready_mail)
            ) or (
                carrier == "GLS" and (candidate.get("mail_ready_for_pickup") or gls_ready_mail)
            )

            extracted.append(
                {
                    "carrier": carrier,
                    "tracking_number": candidate.get("tracking_number"),
                    "subject": subject,
                    "sender": sender,
                    "received_at": received_at,
                    "text": text,
                    "pickup_location": pickup_location,
                    "pickup_code": pickup_code,
                    "mail_ready_for_pickup": mail_ready_for_pickup,
                    "dao_mail_event_text": extract_dao_mail_event_text(text) if carrier == "DAO" else None,
                }
            )

    # Two-phase processing for GLS: process in-transit matches before ready mails.
    def _record_priority(item):
        if item["carrier"] == "GLS" and item["mail_ready_for_pickup"]:
            return 2
        return 1

    for candidate in sorted(extracted, key=_record_priority):
        carrier = candidate["carrier"]
        candidate_key = candidate["tracking_number"]

        if carrier == "GLS":
            candidate_key = gls_alias_key(candidate_key) or candidate_key
            label = extract_mail_label(carrier, candidate["text"])
            if not label:
                label = _gls_merchant_label_for_reference(candidate["tracking_number"], label_mentions)
        else:
            label = extract_mail_label(carrier, candidate["text"])

        found_key = (carrier, candidate_key)
        if found_key not in found_keys:
            found_keys.add(found_key)
            found += 1

        created, shipment = add_shipment(
            candidate["tracking_number"],
            label=label,
            source="mail",
            carrier=carrier,
            mail_subject=candidate["subject"],
            mail_from=candidate["sender"],
            mail_received_at=candidate["received_at"],
            pickup_location=candidate["pickup_location"],
            pickup_code=candidate["pickup_code"],
        )
        if created:
            created_count += 1

        if shipment and candidate["mail_ready_for_pickup"]:
            refreshed = None
            if found_key not in refreshed_keys:
                refreshed_keys.add(found_key)
                try:
                    refreshed = refresh_shipment_tracking(shipment["id"])
                except Exception:
                    refreshed = None
            ready_text = "PostNord-pakken er klar til afhentning"
            if carrier == "GLS":
                ready_text = "GLS-pakken er klar til afhentning"
            update_shipment_mail_status(
                shipment["id"],
                "Klar til afhentning",
                ready_text,
                candidate["received_at"],
            )
            if refreshed and carrier == "GLS":
                reference_label = _gls_merchant_label_for_reference(
                    refreshed.get("tracking_reference"),
                    label_mentions,
                )
                if reference_label:
                    update_shipment_auto_label(refreshed["id"], reference_label)
            continue

        if shipment and candidate["dao_mail_event_text"]:
            if found_key not in refreshed_keys:
                refreshed_keys.add(found_key)
                try:
                    refresh_shipment_tracking(shipment["id"])
                except Exception:
                    pass
            update_shipment_mail_status(
                shipment["id"],
                "Afhentet",
                candidate["dao_mail_event_text"],
                candidate["received_at"],
                add_event=True,
            )
            archive_due_delivered_shipments()
            continue

        if shipment and found_key not in refreshed_keys:
            refreshed_keys.add(found_key)
            try:
                refreshed = refresh_shipment_tracking(shipment["id"])
            except Exception:
                refreshed = None
            if refreshed and carrier == "GLS":
                reference_label = _gls_merchant_label_for_reference(
                    refreshed.get("tracking_reference"),
                    label_mentions,
                )
                if reference_label:
                    update_shipment_auto_label(refreshed["id"], reference_label)

    record_scan_run("mail", messages_scanned, found, created_count)
    return {
        "messages_scanned": messages_scanned,
        "found": found,
        "new_shipments": created_count,
    }


def _run_scan_job(job_id, scan_days, account=None):
    def progress_callback(stage, scanned=None, total=None):
        updates = {"state": "running", "stage": stage}
        if scanned is not None:
            updates["scanned"] = scanned
            updates["messages_scanned"] = scanned
        if total is not None:
            updates["total"] = total
        _update_scan_job(job_id, **updates)

    try:
        _update_scan_job(job_id, state="running", stage="Starting scan")
        summary = _scan_messages(
            scan_days,
            progress_callback,
            provider=account.get("provider") if account else None,
            username=account.get("username") if account else None,
        )
        _update_scan_job(
            job_id,
            state="complete",
            stage="Scan complete",
            scanned=summary["messages_scanned"],
            messages_scanned=summary["messages_scanned"],
            found=summary["found"],
            new_shipments=summary["new_shipments"],
        )
    except (ImapMailError, GmailMailError, MailServiceError, ValueError) as error:
        _update_scan_job(job_id, state="error", stage="Scan failed", error=str(error))
    except Exception as error:
        app.logger.exception("Unhandled mail scan error")
        _update_scan_job(
            job_id,
            state="error",
            stage="Scan failed",
            error=f"Unexpected scan error: {type(error).__name__}",
        )


@app.context_processor
def inject_globals():
    accounts = connected_accounts()
    return {
        "app_name": "FjordParcel",
        "app_build": APP_BUILD,
        "mail_configured": mail_services.is_any_configured(),
        "mail_account": accounts[0] if accounts else None,
        "mail_accounts": accounts,
        "current_user_name": session.get("user_name"),
        "current_user_role": session.get("role"),
    }


@app.route("/setup", methods=["GET", "POST"])
def setup():
    if has_any_user():
        ensure_install_state_for_existing_users()
        return redirect(url_for("index"))
    if _fjordhub_managed():
        return redirect(url_for("login"))
    if install_state_exists():
        return _setup_locked_response()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")
        errors = []
        if not name:
            errors.append("Navn er påkrævet.")
        if not username:
            errors.append("Brugernavn er påkrævet.")
        if not password:
            errors.append("Adgangskode er påkrævet.")
        elif len(password) < 6:
            errors.append("Adgangskoden skal være mindst 6 tegn.")
        if password and password != password2:
            errors.append("Adgangskoderne matcher ikke.")
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("auth.html", mode="setup", form_name=name, form_username=username)
        create_user(name, username, generate_password_hash(password), role="admin")
        mark_install_initialized("first-admin-created")
        session["user_id"] = username.lower()
        session["user_name"] = name
        session["role"] = "admin"
        flash(f"Velkommen, {name}!", "success")
        return redirect(url_for("index"))
    return render_template("auth.html", mode="setup")


@app.route("/login", methods=["GET", "POST"])
def login():
    if _fjordhub_managed():
        if "user_id" in session:
            return redirect(url_for("index"))
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = _hub_authenticate(username, password)
            if user:
                session["hub_user_id"] = int(user["id"])
                session["user_id"] = str(user["username"]).strip().lower()
                session["user_name"] = str(user.get("name") or user["username"])
                session["role"] = "admin" if user.get("role") == "admin" else "user"
                return redirect(url_for("index"))
            flash("Forkert brugernavn/adgangskode eller ingen adgang til FjordParcel.", "error")
        return render_template("auth.html", mode="login")
    if not has_any_user():
        if install_state_exists():
            return _setup_locked_response()
        if not _FJORDHUB_API_KEY:
            return redirect(url_for("setup"))
    ensure_install_state_for_existing_users()
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_user_by_username(username)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["username"]
            session["user_name"] = user["name"]
            session["role"] = user["role"]
            return redirect(url_for("index"))
        flash("Forkert brugernavn eller adgangskode.", "error")
    return render_template("auth.html", mode="login")


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/hub-login")
def hub_login():
    if not _fjordhub_managed():
        return redirect(url_for("login"))
    token = request.args.get("token", "").strip()
    if not token:
        return redirect(url_for("login"))
    result = _hub_api("/api/hub/sso-verify", {"token": token}, method="GET")
    if not result.get("ok"):
        return redirect(url_for("login"))
    username = str(result.get("username") or "").strip()
    role = str(result.get("role") or "user").strip()
    hub_user_id = result.get("id")
    if not username:
        return redirect(url_for("login"))
    session["user_id"] = username.lower()
    session["user_name"] = username
    session["role"] = role
    if hub_user_id:
        session["hub_user_id"] = int(hub_user_id)
    return redirect(url_for("index"))


@app.route("/favicon.ico")
def favicon_ico():
    return send_from_directory(
        os.path.join(app.static_folder, "logos", "web"),
        "favicon.ico",
        mimetype="image/x-icon",
    )


@app.route("/favicon-32x32.png")
def favicon_32_png():
    return send_from_directory(
        os.path.join(app.static_folder, "logos", "web"),
        "favicon-32x32.png",
        mimetype="image/png",
    )


@app.route("/favicon-16x16.png")
def favicon_16_png():
    return send_from_directory(
        os.path.join(app.static_folder, "logos", "web"),
        "favicon-16x16.png",
        mimetype="image/png",
    )


@app.route("/apple-touch-icon.png")
@app.route("/apple-touch-icon-precomposed.png")
@app.route("/apple-touch-icon-180x180.png")
@app.route("/apple-touch-icon-167x167.png")
@app.route("/apple-touch-icon-152x152.png")
@app.route("/apple-touch-icon-120x120.png")
def apple_touch_icon():
    return send_from_directory(
        os.path.join(app.static_folder, "logos", "web"),
        "apple-touch-icon.png",
        mimetype="image/png",
    )


@app.route("/site.webmanifest")
def site_webmanifest():
    return send_from_directory(
        os.path.join(app.static_folder, "logos", "web"),
        "site.webmanifest",
        mimetype="application/manifest+json",
    )


@app.route("/manifest.webmanifest")
def manifest_webmanifest():
    return send_from_directory(
        os.path.join(app.static_folder, "logos", "web"),
        "manifest.webmanifest",
        mimetype="application/manifest+json",
    )


@app.route("/browserconfig.xml")
def browserconfig_xml():
    return send_from_directory(
        os.path.join(app.static_folder, "logos", "web"),
        "browserconfig.xml",
        mimetype="application/xml",
    )


@app.route("/")
def index():
    archive_due_delivered_shipments()
    show_archived = request.args.get("archived") == "1"
    current_user = session.get("user_id")
    active_shipments = list_shipments(current_user=current_user)
    archived_shipments = [s for s in list_shipments(include_archived=True, current_user=current_user) if s.get("is_archived")]
    ready = [s for s in active_shipments if _shipment_category(s) == "ready"]
    delivered = [s for s in active_shipments if _shipment_category(s) == "delivered"]
    in_transit = [s for s in active_shipments if _shipment_category(s) == "in_transit"]
    return render_template(
        "index.html",
        shipments=active_shipments,
        shipments_ready=ready,
        shipments_delivered=delivered,
        shipments_in_transit=in_transit,
        shipments_archived=archived_shipments if show_archived else [],
        active_count=len(active_shipments),
        archived_count=len(archived_shipments),
        show_archived=show_archived,
        stats=get_stats(current_user=current_user),
    )


def _redirect_index_from_form():
    if request.form.get("show_archived") == "1":
        return redirect(url_for("index", archived="1"))
    return redirect(url_for("index"))


@app.post("/shipments")
def create_shipment():
    tracking_number = request.form.get("tracking_number", "")
    label = request.form.get("label", "").strip() or None

    try:
        created, shipment = add_shipment(tracking_number, label=label, source="manual")
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("index"))

    if created:
        flash(f"Added {shipment['tracking_number']}.", "success")
    else:
        flash(f"{shipment['tracking_number']} was already saved, so I refreshed it.", "info")
    return redirect(url_for("index"))


@app.post("/shipments/<int:shipment_id>/delete")
def remove_shipment(shipment_id):
    delete_shipment(shipment_id)
    flash("Shipment removed.", "info")
    return _redirect_index_from_form()


@app.post("/shipments/<int:shipment_id>/archive")
def archive_shipment(shipment_id):
    shipment = set_shipment_archived(shipment_id, True)
    if shipment:
        flash(f"{shipment['tracking_number']} er arkiveret.", "success")
    return _redirect_index_from_form()


@app.post("/shipments/<int:shipment_id>/restore")
def restore_shipment(shipment_id):
    shipment = set_shipment_archived(shipment_id, False)
    if shipment:
        flash(f"{shipment['tracking_number']} er gendannet.", "success")
    return _redirect_index_from_form()


@app.post("/shipments/<int:shipment_id>/hide")
def hide_shipment(shipment_id):
    current_user = session.get("user_id", "")
    set_shipment_hidden(shipment_id, current_user)
    return _redirect_index_from_form()


@app.post("/shipments/<int:shipment_id>/unhide")
def unhide_shipment(shipment_id):
    set_shipment_hidden(shipment_id, "")
    return _redirect_index_from_form()


@app.post("/shipments/<int:shipment_id>/label")
def rename_shipment(shipment_id):
    update_shipment_label(shipment_id, request.form.get("label", ""))
    flash("Package name saved.", "success")
    return _redirect_index_from_form()


@app.post("/shipments/<int:shipment_id>/refresh")
def refresh_shipment(shipment_id):
    try:
        shipment = refresh_shipment_tracking(shipment_id)
    except LookupError as error:
        flash(str(error), "error")
        return _redirect_index_from_form()

    if shipment.get("tracking_error"):
        flash(
            f"{shipment['tracking_number']} update failed: {shipment['tracking_error']}",
            "error",
        )
    else:
        detail = shipment.get("last_event_text") or shipment.get("summary") or "No event details from provider yet."
        flash(
            f"{shipment['tracking_number']} updated. Status: {shipment.get('status') or 'Updated'}. {detail}",
            "success",
        )
    return _redirect_index_from_form()


@app.route("/mail/connect")
def mail_connect():
    return redirect(url_for("microsoft_mail_connect"))


@app.route("/mail/microsoft/connect")
def microsoft_mail_connect():
    if not imap_mail.is_configured():
        flash("Add Microsoft client settings before connecting Hotmail.", "error")
        return redirect(url_for("settings", section="mails", provider="microsoft", setup="1"))

    redirect_uri = public_url_for("mail_callback")
    flow = imap_mail.build_auth_flow(redirect_uri)
    session["ms_auth_flow"] = flow
    return redirect(flow["auth_uri"])


@app.route("/auth/microsoft/callback")
def mail_callback():
    flow = session.pop("ms_auth_flow", None)
    if not flow:
        flash("Microsoft login session expired. Try connecting again.", "error")
        return redirect(url_for("settings", section="mails"))

    try:
        imap_mail.complete_auth_flow(flow, dict(request.args))
    except ImapMailError as error:
        flash(str(error), "error")
        return redirect(url_for("settings", section="mails"))

    flash("Microsoft IMAP mail connected.", "success")
    return redirect(url_for("settings", section="mails"))


@app.route("/mail/google/connect")
def google_mail_connect():
    if not gmail_mail.is_configured():
        flash("Add Google client settings before connecting Gmail.", "error")
        return redirect(url_for("settings", section="mails", provider="gmail", setup="1"))

    redirect_uri = public_url_for("google_mail_callback")
    flow = gmail_mail.build_auth_flow(redirect_uri)
    session["google_auth_flow"] = flow
    return redirect(flow["auth_uri"])


@app.route("/auth/google/callback")
def google_mail_callback():
    flow = session.pop("google_auth_flow", None)
    if not flow:
        flash("Google login session expired. Try connecting again.", "error")
        return redirect(url_for("settings", section="mails"))

    try:
        account = gmail_mail.complete_auth_flow(flow, dict(request.args))
    except GmailMailError as error:
        flash(str(error), "error")
        return redirect(url_for("settings", section="mails", provider="gmail", setup="1"))

    flash("Gmail connected.", "success")
    return redirect(
        url_for(
            "settings",
            section="mails",
            provider=account["provider"],
            account=account["username"],
        )
    )


@app.post("/mail/disconnect")
def mail_disconnect():
    imap_mail.disconnect()
    flash("Microsoft mail disconnected.", "info")
    return redirect(url_for("settings", section="mails"))


@app.post("/mail/<provider>/<path:username>/disconnect")
def disconnect_mail_account(provider, username):
    try:
        mail_services.disconnect(provider, username)
    except (ImapMailError, GmailMailError, MailServiceError) as error:
        flash(str(error), "error")
        return redirect(url_for("settings", section="mails", provider=provider, account=username))

    try:
        delete_mail_account_settings(provider, username)
    except ValueError:
        pass
    flash("Mailkonto afbrudt.", "info")
    return redirect(url_for("settings", section="mails"))


@app.post("/settings/microsoft")
def save_microsoft_config():
    try:
        _settings, auth_changed = save_microsoft_settings(request.form)
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("settings", section="mails", provider="microsoft", setup="1"))

    if auth_changed:
        imap_mail.disconnect()
        flash("Microsoft settings saved. Connect Microsoft again to authorize this app.", "success")
    else:
        flash("Microsoft settings saved.", "success")
    return redirect(url_for("settings", section="mails", provider="microsoft", setup="1"))


@app.post("/settings/google")
def save_google_config():
    try:
        _settings, auth_changed = save_google_settings(request.form)
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("settings", section="mails", provider="gmail", setup="1"))

    if auth_changed:
        gmail_mail.disconnect()
        flash("Google settings saved. Connect Gmail again to authorize this app.", "success")
    else:
        flash("Google settings saved.", "success")
    return redirect(url_for("settings", section="mails", provider="gmail", setup="1"))


@app.post("/settings/carriers/<carrier>/postal-codes/add")
def add_carrier_postal_code(carrier):
    active_carrier = _settings_carrier(carrier)
    try:
        added_code = add_carrier_postcode(active_carrier, request.form.get("postal_code", ""))
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("settings", section="carriers", carrier=active_carrier))

    flash(f"Saved postal code {added_code} for {active_carrier}.", "success")
    return redirect(url_for("settings", section="carriers", carrier=active_carrier))


@app.post("/settings/carriers/<carrier>/postal-codes/remove")
def remove_carrier_postal_code_entry(carrier):
    active_carrier = _settings_carrier(carrier)
    try:
        remove_carrier_postcode(active_carrier, request.form.get("postal_code", ""))
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("settings", section="carriers", carrier=active_carrier))

    flash(f"Postal code removed for {active_carrier}.", "info")
    return redirect(url_for("settings", section="carriers", carrier=active_carrier))


@app.post("/settings/postnord/apikey")
def save_track17_api_key():
    import tracking_providers.postnord as _postnord
    from app_config import save_track17_api_key as _save_key
    api_key = str(request.form.get("api_key") or "").strip()
    if not api_key:
        flash("API-nøgle må ikke være tom.", "error")
        return redirect(url_for("settings", section="carriers", carrier="PostNord"))
    _save_key(api_key)
    _postnord.TRACK17_API_KEY = api_key
    flash("17TRACK API-nøgle gemt og krypteret.", "success")
    return redirect(url_for("settings", section="carriers", carrier="PostNord"))


@app.post("/mail/scan")
def scan_mail():
    try:
        scan_days = mail_services.normalize_scan_days(request.form.get("days", 14))
        account = _mail_account_from_values(request.form)
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("settings", section="mails"))

    try:
        summary = _scan_messages(
            scan_days,
            lambda **_updates: None,
            provider=account["provider"],
            username=account["username"],
        )
    except (ImapMailError, GmailMailError, MailServiceError, ValueError) as error:
        flash(str(error), "error")
        return _mail_account_settings_redirect(account)

    flash(
        f"Scanned {summary['messages_scanned']} messages from {account['username']} from the last {scan_days} days and found {summary['found']} tracking number(s). {summary['new_shipments']} were new.",
        "success",
    )
    return _mail_account_settings_redirect(account)


@app.post("/mail/scan/start")
def start_scan_mail():
    try:
        scan_days = mail_services.normalize_scan_days(request.form.get("days", 14))
        account = _mail_account_from_values(request.form)
    except ValueError as error:
        return jsonify({"ok": False, "error": str(error)}), 400

    job_id = _new_scan_job(scan_days, account=account)
    thread = threading.Thread(target=_run_scan_job, args=(job_id, scan_days, account), daemon=True)
    thread.start()
    return jsonify({"ok": True, "job_id": job_id})


@app.get("/mail/scan/status/<job_id>")
def scan_mail_status(job_id):
    job = _get_scan_job(job_id)
    if not job:
        return jsonify({"ok": False, "error": "Scan job was not found."}), 404
    return jsonify({"ok": True, "job": job})


@app.route("/settings")
def settings():
    section = _settings_section(request.args.get("section"))
    active_carrier = _settings_carrier(request.args.get("carrier"))
    mail_accounts = connected_accounts()
    requested_mail_provider = str(request.args.get("provider") or "").strip().lower()
    requested_mail_account = str(request.args.get("account") or "").strip().lower()
    setup_provider = str(request.args.get("setup") or "").strip() == "1" and requested_mail_provider in {
        "microsoft",
        "gmail",
    }
    edit_app_registration = str(request.args.get("edit_app") or "").strip() == "1"
    active_mail_account = next(
        (
            account
            for account in mail_accounts
            if str(account.get("username") or "").strip().lower() == requested_mail_account
            and (
                not requested_mail_provider
                or str(account.get("provider") or "").strip().lower() == requested_mail_provider
            )
        ),
        None,
    )
    automation = load_automation_settings()
    public_base_url = load_public_base_url()
    if active_mail_account:
        account_automation = load_mail_account_settings(
            active_mail_account["provider"],
            active_mail_account["username"],
        )
    else:
        account_automation = {
            "auto_scan_enabled": False,
            "auto_scan_minutes": 30,
        }

    import tracking_providers.postnord as _postnord
    from app_config import load_track17_settings as _load_track17
    return render_template(
        "settings.html",
        section=section,
        active_carrier=active_carrier,
        carrier_names=SUPPORTED_CARRIER_SETTINGS,
        track17_api_key_set=bool(_postnord.TRACK17_API_KEY or _load_track17().get("api_key")),
        public_base_url=public_base_url,
        redirect_uri=public_url_for("mail_callback"),
        google_redirect_uri=public_url_for("google_mail_callback"),
        localhost_redirect_uri=localhost_url_for("mail_callback"),
        localhost_google_redirect_uri=localhost_url_for("google_mail_callback"),
        microsoft_config=imap_mail.microsoft_config(),
        google_config=gmail_mail.google_config(),
        microsoft_configured=imap_mail.is_configured(),
        google_configured=gmail_mail.is_configured(),
        automation=automation,
        account_automation=account_automation,
        mail_accounts=mail_accounts,
        active_mail_account=active_mail_account,
        requested_mail_provider=requested_mail_provider,
        setup_provider=setup_provider,
        edit_app_registration=edit_app_registration,
        users=_app_users(),
        fjordhub_managed=_fjordhub_managed(),
    )


@app.post("/settings/automation")
def save_automation_config():
    settings = save_automation_settings(request.form)
    flash("Automatiske scanninger er gemt.", "success")
    section = _settings_section(request.form.get("section"))
    return redirect(url_for("settings", section=section))


@app.post("/settings/mail-account-automation")
def save_mail_account_automation_config():
    try:
        account = _mail_account_from_values(request.form)
        save_mail_account_settings(account["provider"], account["username"], request.form)
    except (MailServiceError, ValueError) as error:
        flash(str(error), "error")
        return redirect(url_for("settings", section="mails"))

    flash(f"Automatisk mailscan er gemt for {account['username']}.", "success")
    return _mail_account_settings_redirect(account)


@app.post("/settings/users")
def create_user_settings():
    name = request.form.get("name", "").strip()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    password2 = request.form.get("password2", "")
    role = request.form.get("role", "user")
    if role not in ("admin", "user"):
        role = "user"
    errors = []
    if not name:
        errors.append("Navn er påkrævet.")
    if not username:
        errors.append("Brugernavn er påkrævet.")
    if not password:
        errors.append("Adgangskode er påkrævet.")
    elif len(password) < 6:
        errors.append("Adgangskoden skal være mindst 6 tegn.")
    if password and password != password2:
        errors.append("Adgangskoderne matcher ikke.")
    if not errors:
        try:
            if _fjordhub_managed():
                result = _hub_create_user({
                    "username": username,
                    "password": password,
                    "role": role,
                    "first_name": name,
                    "last_name": "",
                })
                if not result.get("ok"):
                    flash(str(result.get("error") or "Kunne ikke oprette bruger i FjordHub."), "error")
                    return redirect(url_for("settings", section="users"))
                flash(f"Bruger '{name}' er oprettet.", "success")
            else:
                create_user(name, username, generate_password_hash(password), role=role)
                flash(f"Bruger '{name}' er oprettet.", "success")
                _hub_sync_user(username, role, password=password, name=name)
        except Exception:
            flash("Brugernavnet er allerede i brug.", "error")
    else:
        for error in errors:
            flash(error, "error")
    return redirect(url_for("settings", section="users"))


@app.post("/settings/users/<int:user_id>/delete")
def delete_user_settings(user_id):
    users = list_users()
    if _fjordhub_managed():
        users = _app_users()
    target = next((u for u in users if u["id"] == user_id), None)
    if not target:
        flash("Brugeren blev ikke fundet.", "error")
        return redirect(url_for("settings", section="users"))
    if str(target.get("username") or "").strip().lower() == str(session.get("user_id", "")).strip().lower():
        flash("Du kan ikke slette din egen bruger.", "error")
        return redirect(url_for("settings", section="users"))
    admins = [u for u in users if u["role"] == "admin"]
    if target["role"] == "admin" and len(admins) <= 1:
        flash("Du kan ikke slette den eneste admin-bruger.", "error")
        return redirect(url_for("settings", section="users"))
    if _fjordhub_managed():
        result = _hub_delete_user_access(int(user_id))
        if not result.get("ok"):
            flash(str(result.get("error") or "Kunne ikke fjerne brugeradgang i FjordHub."), "error")
            return redirect(url_for("settings", section="users"))
    else:
        delete_user(user_id)
    flash(f"Bruger '{target['name']}' er slettet.", "success")
    return redirect(url_for("settings", section="users"))


# ── FjordHub integration ──────────────────────────────────────────────────────

_FJORDHUB_API_KEY = os.environ.get("FJORDHUB_API_KEY", "")
_FJORDHUB_URL = os.environ.get("FJORDHUB_URL", "")
_FJORDHUB_APP_ID = os.environ.get("FJORDHUB_APP_ID", "fjordparcel")


def _fjordhub_managed() -> bool:
    return bool(_FJORDHUB_URL and _FJORDHUB_API_KEY and _FJORDHUB_APP_ID)


def _hub_authorized() -> bool:
    if not _FJORDHUB_API_KEY:
        return False
    return request.headers.get("X-Hub-Key") == _FJORDHUB_API_KEY


def _hub_api(path: str, payload: dict | None = None, method: str = "POST") -> dict:
    if not _fjordhub_managed():
        return {"ok": False, "error": "FjordHub integration er ikke aktiv."}
    method = method.upper()
    data = dict(payload or {})
    data.setdefault("app_id", _FJORDHUB_APP_ID)
    url = f"{_FJORDHUB_URL.rstrip('/')}{path}"
    body = None
    if method == "GET":
        url = f"{url}?{urllib.parse.urlencode(data)}"
    else:
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("X-Hub-Key", _FJORDHUB_API_KEY)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            return json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        try:
            return json.loads(exc.read().decode("utf-8") or "{}")
        except Exception:
            return {"ok": False, "error": f"FjordHub svarede HTTP {exc.code}"}
    except Exception as exc:
        return {"ok": False, "error": f"Kunne ikke kontakte FjordHub: {exc}"}


def _hub_authenticate(username: str, password: str) -> dict | None:
    result = _hub_api(
        "/api/hub/apps/authenticate",
        {"username": username, "password": password},
    )
    return result.get("user") if result.get("ok") and isinstance(result.get("user"), dict) else None


def _hub_create_user(payload: dict) -> dict:
    return _hub_api("/api/hub/apps/users", payload, method="POST")


def _hub_delete_user_access(user_id: int) -> dict:
    return _hub_api(f"/api/hub/apps/users/{int(user_id)}", {}, method="DELETE")


def _app_users() -> list[dict]:
    if not _fjordhub_managed():
        return list_users()
    result = _hub_api("/api/hub/apps/users", {}, method="GET")
    if not result.get("ok"):
        flash(str(result.get("error") or "Kunne ikke hente brugere fra FjordHub."), "error")
        return []
    users: list[dict] = []
    for item in result.get("items", []):
        if not isinstance(item, dict):
            continue
        first_name = str(item.get("first_name") or "").strip()
        last_name = str(item.get("last_name") or "").strip()
        username = str(item.get("username") or "").strip()
        display_name = (first_name + " " + last_name).strip() or username
        users.append(
            {
                "id": item.get("id"),
                "name": display_name,
                "username": username,
                "role": item.get("role") or "user",
                "created_at": item.get("created_at") or "",
            }
        )
    return users


def _hub_sync_user(username: str, role: str, password: str = "", name: str = "") -> None:
    if not _fjordhub_managed():
        return
    payload: dict[str, str] = {"username": username, "role": role}
    if password:
        payload["password"] = password
    if name:
        payload["first_name"] = name
    _hub_create_user(payload)


@app.route("/api/hub/users", methods=["GET", "POST"])
def hub_users():
    if not _hub_authorized():
        return jsonify({"ok": False, "error": "Uautoriseret"}), 401
    if _fjordhub_managed():
        return jsonify({"ok": False, "error": "Lokal bruger-provisionering er slået fra i FjordHub-managed mode."}), 410
    if request.method == "GET":
        return jsonify({"ok": True, "items": list_users()})
    data = request.get_json(silent=True) or {}
    username = str(data.get("username") or "").strip()
    password = str(data.get("password") or "")
    role = str(data.get("role") or "user").strip()
    name = str(data.get("name") or username).strip()
    if role not in ("admin", "user"):
        role = "user"
    if not username or not password:
        return jsonify({"ok": False, "error": "username og password påkrævet"}), 400
    if len(password) < 6:
        return jsonify({"ok": False, "error": "Adgangskode skal være mindst 6 tegn"}), 400
    try:
        create_user(name, username, generate_password_hash(password), role=role)
        return jsonify({"ok": True}), 201
    except Exception as exc:
        if "UNIQUE" in str(exc) or "unique" in str(exc).lower():
            return jsonify({"ok": False, "error": "Brugernavn findes allerede"}), 409
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/hub/users/<int:user_id>", methods=["PATCH", "DELETE"])
def hub_user(user_id: int):
    if not _hub_authorized():
        return jsonify({"ok": False, "error": "Uautoriseret"}), 401
    if _fjordhub_managed():
        return jsonify({"ok": False, "error": "Lokal bruger-provisionering er slået fra i FjordHub-managed mode."}), 410
    if request.method == "DELETE":
        delete_user(user_id)
        return jsonify({"ok": True})
    data = request.get_json(silent=True) or {}
    role = str(data.get("role") or "user").strip()
    if role not in ("admin", "user"):
        return jsonify({"ok": False, "error": "Ugyldig rolle"}), 400
    update_user_role(user_id, role)
    return jsonify({"ok": True})


def _automation_worker():
    global _AUTO_NEXT_SCAN_AT, _AUTO_NEXT_REFRESH_AT, _AUTO_IS_LEADER, _AUTO_NEXT_HEARTBEAT_AT
    while True:
        try:
            now = time.time()

            if now >= _AUTO_NEXT_HEARTBEAT_AT:
                if _AUTO_IS_LEADER:
                    _AUTO_IS_LEADER = renew_automation_leader_lock(
                        _AUTO_LEADER_OWNER_ID,
                        lease_seconds=_AUTO_LEASE_SECONDS,
                    )
                if not _AUTO_IS_LEADER:
                    _AUTO_IS_LEADER = try_acquire_automation_leader_lock(
                        _AUTO_LEADER_OWNER_ID,
                        lease_seconds=_AUTO_LEASE_SECONDS,
                    )
                _AUTO_NEXT_HEARTBEAT_AT = now + _AUTO_HEARTBEAT_INTERVAL_SECONDS

            if not _AUTO_IS_LEADER:
                time.sleep(5)
                continue

            try:
                archive_due_delivered_shipments()
            except Exception:
                pass

            cfg = load_automation_settings()
            now = time.time()
            # Auto mail scan is configured per connected mail account.
            accounts = {
                (account["provider"], str(account["username"]).lower()): account
                for account in connected_accounts()
            }
            for scan_cfg in list_enabled_mail_account_scans():
                key = (scan_cfg["provider"], str(scan_cfg["username"]).lower())
                account = accounts.get(key)
                if not account:
                    continue
                if now >= _AUTO_NEXT_SCAN_AT.get(key, 0):
                    try:
                        _scan_messages(
                            1,
                            lambda **_u: None,
                            only_today=True,
                            provider=account["provider"],
                            username=account["username"],
                        )
                    except Exception:
                        app.logger.exception("Auto mail scan failed for %s/%s", account.get("provider"), account.get("username"))
                    _AUTO_NEXT_SCAN_AT[key] = now + int(scan_cfg.get("auto_scan_minutes", 30)) * 60

            # Auto tracking refresh (randomized interval)
            if cfg.get("auto_refresh_enabled"):
                if now >= _AUTO_NEXT_REFRESH_AT:
                    try:
                        for s in list_shipments(include_archived=True):
                            try:
                                refresh_shipment_tracking(s["id"])
                            except Exception:
                                continue
                    finally:
                        # Fast hvert 30. minut (ingen randomisering)
                        _AUTO_NEXT_REFRESH_AT = now + 30 * 60
        except Exception:
            # Never crash the loop
            pass
        time.sleep(5)


def _ensure_automation_thread():
    global _AUTO_THREAD_STARTED
    if _AUTO_THREAD_STARTED:
        return
    th = threading.Thread(target=_automation_worker, name="automation-worker", daemon=True)
    th.start()
    _AUTO_THREAD_STARTED = True


def _should_start_automation_on_boot():
    enabled_raw = str(os.getenv("FJORDPARCEL_AUTOMATION_ENABLED", "1") or "1").strip().lower()
    if enabled_raw in {"0", "false", "no", "off"}:
        return False

    # Avoid starting duplicate worker in Flask dev reloader parent process.
    if app.debug and os.getenv("WERKZEUG_RUN_MAIN") != "true":
        return False
    return True


def _start_automation_on_boot():
    if not _should_start_automation_on_boot():
        return
    _ensure_automation_thread()


def _release_automation_lock_on_exit():
    try:
        release_automation_leader_lock(_AUTO_LEADER_OWNER_ID)
    except Exception:
        pass


def _require_admin_for_app_update():
    if "user_id" not in session:
        return jsonify({"ok": False, "error": "Forbidden"}), 403
    if session.get("role") != "admin":
        return jsonify({"ok": False, "error": "Forbidden"}), 403
    return None


def _app_update_proxy(path, method="GET", payload=None, timeout=None):
    if not APP_UPDATE_SERVICE_URL:
        return jsonify({"ok": False, "available": False, "service_reachable": False,
                        "error": "FjordParcel updater-service er ikke konfigureret."}), 503
    clean_path = "/" + str(path or "").strip("/")
    url = f"{APP_UPDATE_SERVICE_URL}{clean_path}"
    try:
        body = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(url, data=body, method=method.upper())
        if body:
            req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=float(timeout or APP_UPDATE_SERVICE_TIMEOUT_SEC)) as resp:
            raw = resp.read().decode("utf-8")
        try:
            data = json.loads(raw)
        except Exception:
            data = {"ok": False, "error": raw[:500] or "Updater-service svarede ikke med JSON."}
        if isinstance(data, dict):
            data.setdefault("service_reachable", True)
            data.setdefault("updater_url", APP_UPDATE_SERVICE_URL)
        return jsonify(data), resp.status if hasattr(resp, "status") else 200
    except urllib.error.HTTPError as e:
        try:
            data = json.loads(e.read().decode("utf-8"))
        except Exception:
            data = {"ok": False, "error": str(e)}
        if isinstance(data, dict):
            data.setdefault("service_reachable", True)
        return jsonify(data), e.code
    except Exception as e:
        return jsonify({"ok": False, "available": False, "service_reachable": False,
                        "updater_url": APP_UPDATE_SERVICE_URL,
                        "error": "FjordParcel updater-service er ikke tilgaengelig.",
                        "detail": str(e)}), 503


@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({"ok": True}), 200


@app.route("/api/app-update/status", methods=["GET"])
def api_app_update_status():
    fb = _require_admin_for_app_update()
    if fb:
        return fb
    return _app_update_proxy("/status", method="GET", timeout=5)


@app.route("/api/app-update/check", methods=["POST"])
def api_app_update_check():
    fb = _require_admin_for_app_update()
    if fb:
        return fb
    return _app_update_proxy("/check", method="POST", payload={}, timeout=90)


@app.route("/api/app-update/start", methods=["POST"])
def api_app_update_start():
    fb = _require_admin_for_app_update()
    if fb:
        return fb
    body = request.get_json(silent=True) or {}
    cleanup = bool(body.get("cleanup", True))
    return _app_update_proxy("/start", method="POST", payload={"cleanup": cleanup}, timeout=10)


@app.route("/api/app-update/force-stop", methods=["POST"])
def api_app_update_force_stop():
    fb = _require_admin_for_app_update()
    if fb:
        return fb
    return _app_update_proxy("/force-stop", method="POST", payload={}, timeout=15)


@app.route("/api/app-update/settings", methods=["GET", "POST"])
def api_app_update_settings():
    fb = _require_admin_for_app_update()
    if fb:
        return fb
    if request.method == "GET":
        return _app_update_proxy("/settings", method="GET", timeout=5)
    body = request.get_json(silent=True) or {}
    payload = {
        "auto_check_enabled": bool(body.get("auto_check_enabled")),
        "auto_check_interval_minutes": body.get("auto_check_interval_minutes"),
    }
    return _app_update_proxy("/settings", method="POST", payload=payload, timeout=10)


@app.route("/api/settings/public-base-url", methods=["POST"])
def api_settings_public_base_url():
    fb = _require_admin_for_app_update()
    if fb:
        return fb
    body = request.get_json(silent=True) or {}
    try:
        public_base_url = save_public_base_url(body.get("public_base_url", ""))
    except ValueError as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    return jsonify(
        {
            "ok": True,
            "public_base_url": public_base_url,
            "microsoft_redirect_uri": public_url_for("mail_callback"),
            "google_redirect_uri": public_url_for("google_mail_callback"),
        }
    )


_start_automation_on_boot()
atexit.register(_release_automation_lock_on_exit)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
