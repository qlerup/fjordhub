"""Authenticated app-origin Matrix notifications with durable deduplication.

Applications can submit *typed* events using their existing FjordHub app key.
No app controls the recipient, Matrix room, or arbitrary bot instructions.
"""
from .bot_queries import download_title
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import sqlite3
import threading
import uuid
from zoneinfo import ZoneInfo

ALLOWED_TYPES = {
    "fjordvpn": {"vpn_failed", "vpn_recovered"},
    "fjordseed": {"rss_started", "rss_completed", "download_started", "download_completed"},
}
EVENT_ID = re.compile(r"[A-Za-z0-9_.:-]{1,120}\Z")
COPENHAGEN = ZoneInfo("Europe/Copenhagen")


def safe_label(value, maximum):
    if not isinstance(value, str):
        return ""
    text = " ".join(value.split())
    text = "".join(ch for ch in text if ch.isprintable())
    return text[:maximum]


class NotificationError(ValueError):
    pass


def clean_event(app_id, value):
    if not isinstance(value, dict) or len(value) > 8:
        raise NotificationError("Ugyldig notifikationshændelse.")
    kind = value.get("type")
    event_id = value.get("event_id")
    if kind not in ALLOWED_TYPES.get(app_id, set()) or not isinstance(event_id, str) or not EVENT_ID.fullmatch(event_id):
        raise NotificationError("Ugyldig hændelsestype eller id.")
    if app_id == "fjordvpn":
        profiles = value.get("profiles")
        if not isinstance(profiles, list) or not 1 <= len(profiles) <= 20 or any(
                not safe_label(x, 90) for x in profiles):
            raise NotificationError("Angiv 1–20 VPN-profilnavne.")
        profiles = list(dict.fromkeys(safe_label(x, 90) for x in profiles))
        return {"type": kind, "event_id": event_id, "profiles": profiles}
    filename = safe_label(value.get("filename"), 200)
    if not filename:
        raise NotificationError("Angiv filnavnet.")
    return {"type": kind, "event_id": event_id, "filename": filename,
            "feed": safe_label(value.get("feed", ""), 90)}


def notification_text(app_id, entry):
    kind = entry["type"]
    if app_id == "fjordvpn":
        heading = ("🚨 FjordVPN: Forbindelsesfejl" if kind == "vpn_failed" else
                   "✅ FjordVPN: Forbindelsen virker igen")
        return heading + "\n" + "\n".join("• " + n for n in entry["profiles"])
    heading = ("⬇️ FjordSeed: RSS-download startet" if kind == "rss_started" else
               "✅ FjordSeed: Download færdig")
    text = heading + "\n\n" + download_title(entry["filename"])
    if entry["feed"]:
        text += "\n\nRSS-feed: " + entry["feed"]
    return text


class NotificationStore:
    def __init__(self, data_dir):
        self.path = Path(data_dir) / "matrix-app-events.sqlite3"
        self.lock = threading.RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.execute("""CREATE TABLE IF NOT EXISTS events(
                 app_id TEXT NOT NULL, event_id TEXT NOT NULL, kind TEXT NOT NULL,
                 occurred_at TEXT NOT NULL, filename TEXT NOT NULL DEFAULT '',
                 feed TEXT NOT NULL DEFAULT '', queued INTEGER NOT NULL DEFAULT 0,
                 PRIMARY KEY(app_id, event_id))""")
            con.execute("CREATE INDEX IF NOT EXISTS idx_events_day ON events(app_id,kind,occurred_at)")

    def _connect(self):
        con = sqlite3.connect(self.path, timeout=10)
        con.row_factory = sqlite3.Row
        return con

    def record(self, app_id, raw_event, matrix_hub):
        entry = clean_event(app_id, raw_event)
        now = datetime.now(timezone.utc).isoformat()
        with self.lock, self._connect() as con:
            con.execute("""INSERT OR IGNORE INTO events
                (app_id,event_id,kind,occurred_at,filename,feed) VALUES (?,?,?,?,?,?)""",
                (app_id, entry["event_id"], entry["type"], now,
                 entry.get("filename", ""), entry.get("feed", "")))
            row = con.execute("SELECT queued FROM events WHERE app_id=? AND event_id=?",
                              (app_id, entry["event_id"])).fetchone()
            # Not installed yet: still keep history for "what downloaded today?".
            notify = entry["type"] in {"vpn_failed", "vpn_recovered", "rss_started"}
            if row["queued"] == 0 and notify and matrix_hub._state().get("phase") == "ready":
                allowed = matrix_hub._load(matrix_hub.bot_dir / "config.json").get("allowed_users", [])
                for recipient in allowed[:50]:
                    if not isinstance(recipient, str) or not recipient.startswith("@"):
                        continue
                    # Stable ID: retries and multiple workers cannot enqueue copies.
                    path = matrix_hub.bot_dir / "outbox" / (
                        __import__("hashlib").sha256(
                            (app_id + ":" + entry["event_id"] + ":" + recipient).encode()).hexdigest() + ".json")
                    matrix_hub._save(path, {"recipient": recipient,
                                             "text": notification_text(app_id, entry)})
                con.execute("UPDATE events SET queued=1 WHERE app_id=? AND event_id=?",
                            (app_id, entry["event_id"]))
            return {"ok": True, "duplicate": bool(row["queued"])}

    def downloads_today(self):
        return self.downloads_period('today')

    def downloads_period(self, period, now=None):
        today = (now or datetime.now(COPENHAGEN)).astimezone(COPENHAGEN).date()
        days = re.fullmatch(r'last_([0-9]{1,3})_days', period)
        if period == 'today':
            first, last, label = today, today + timedelta(days=1), 'i dag'
        elif period == 'yesterday':
            first, last, label = today - timedelta(days=1), today, 'i går'
        elif period == 'since_yesterday':
            first, last, label = today - timedelta(days=1), today + timedelta(days=1), 'siden i går'
        elif days and 1 <= int(days[1]) <= 366:
            first, last = today - timedelta(days=int(days[1]) - 1), today + timedelta(days=1)
            label = 'de sidste ' + days[1] + ' dage'
        else:
            raise ValueError('Ugyldig periode. Brug i dag, i går, siden i går eller de sidste 1–366 dage.')
        start = datetime.combine(first, datetime.min.time(), tzinfo=COPENHAGEN)
        end = datetime.combine(last, datetime.min.time(), tzinfo=COPENHAGEN)
        with self.lock, self._connect() as con:
            records = con.execute("""SELECT filename,feed,kind,occurred_at FROM events
                WHERE app_id='fjordseed' AND
                kind IN ('rss_completed','download_completed','rss_started','download_started')
                AND occurred_at>=? AND occurred_at<?
                ORDER BY occurred_at DESC LIMIT 501""",
                (start.astimezone(timezone.utc).isoformat(),
                 end.astimezone(timezone.utc).isoformat())).fetchall()
        completed = []
        started = []
        unique_done = set()
        for record in records:
            item = {"filename": record["filename"], "feed": record["feed"]}
            identity = (item["filename"], item["feed"])
            if record["kind"].endswith("_completed"):
                if identity not in unique_done:
                    completed.append(item)
                    unique_done.add(identity)
            else:
                started.append(item)
        started = [row for row in started if (row["filename"], row["feed"]) not in unique_done]
        return {"ok": True, "date": str(today), "timezone": "Europe/Copenhagen",
                "period": period, "label": label, "from": str(first), "until": str(last),
                "completed": completed[:50], "started": started[:50],
                "more": len(records) > 500 or len(completed) > 50 or len(started) > 50}
