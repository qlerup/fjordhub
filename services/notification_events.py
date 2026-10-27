"""Authenticated app-origin Matrix notifications with durable deduplication.

Applications can submit *typed* events using their existing FjordHub app key.
No app controls the recipient, Matrix room, or arbitrary bot instructions.
"""
from .bot_queries import download_title
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import sqlite3
import threading
import uuid
from zoneinfo import ZoneInfo

ALLOWED_TYPES = {
    "fjordlens": {"upload_finished"},
    "fjordvpn": {"vpn_failed", "vpn_recovered", "vpn_port_changed"},
    "fjordseed": {"rss_started", "rss_completed", "download_started", "download_completed", "download_deleted"},
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
    if not isinstance(value, dict) or len(value) > 9:
        raise NotificationError("Ugyldig notifikationshændelse.")
    kind = value.get("type")
    event_id = value.get("event_id")
    if kind not in ALLOWED_TYPES.get(app_id, set()) or not isinstance(event_id, str) or not EVENT_ID.fullmatch(event_id):
        raise NotificationError("Ugyldig hændelsestype eller id.")
    if app_id == "fjordvpn":
        if kind == "vpn_port_changed":
            profile = safe_label(value.get("profile"), 90)
            port, previous = value.get("port"), value.get("previous_port")
            if (not profile or type(port) is not int or not 1 <= port <= 65535 or
                    (previous is not None and (type(previous) is not int or not 1 <= previous <= 65535)) or
                    previous == port):
                raise NotificationError("Ugyldig VPN-portændring.")
            return {"type": kind, "event_id": event_id, "profile": profile,
                    "port": port, "previous_port": previous}
        profiles = value.get("profiles")
        if not isinstance(profiles, list) or not 1 <= len(profiles) <= 20 or any(
                not safe_label(x, 90) for x in profiles):
            raise NotificationError("Angiv 1–20 VPN-profilnavne.")
        profiles = list(dict.fromkeys(safe_label(x, 90) for x in profiles))
        return {"type": kind, "event_id": event_id, "profiles": profiles}
    if app_id == 'fjordlens':
        stats = value.get('stats')
        counts = ('files', 'images', 'videos', 'indexed', 'heic_converted', 'faces_done', 'face_count',
                  'ai_done', 'ai_desc_done', 'index_errors', 'thumb_errors', 'faces_errors', 'ai_errors', 'ai_desc_errors')
        flags = ('faces_enabled', 'ai_enabled', 'ai_desc_enabled')
        if not isinstance(stats, dict) or set(stats) != set(counts + flags) or any(
                type(stats.get(k)) is not int or not 0 <= stats[k] <= 100000000 for k in counts) or any(
                type(stats.get(k)) is not bool for k in flags):
            raise NotificationError('Ugyldig uploadstatistik.')
        if stats['images'] + stats['videos'] != stats['files'] or value.get('status') not in {'completed', 'stopped', 'failed'}:
            raise NotificationError('Ugyldig uploadstatus.')
        return {'type': kind, 'event_id': event_id, 'stats': {k: stats[k] for k in counts + flags},
                'status': value['status'], 'uploader': safe_label(value.get('uploader'), 90)}
    filename = safe_label(value.get("filename"), 200)
    if not filename:
        raise NotificationError("Angiv filnavnet.")
    if kind == 'download_deleted':
        reason = value.get('reason')
        ratio, hours = value.get('ratio_limit'), value.get('seed_hours')
        import math
        if (reason not in {'ratio', 'time'} or
                any(type(v) not in (int, float) or not math.isfinite(v) or v < 1
                    for v in (ratio, hours)) or hours > 8809 or
                type(value.get('library_retained')) is not bool):
            raise NotificationError('Ugyldig automatisk sletning.')
        freed = value.get('freed_bytes')
        if freed is not None and (type(freed) is not int or not 0 <= freed <= 2**63 - 1):
            raise NotificationError('Ugyldig filstørrelse.')
        return {'type': kind, 'event_id': event_id, 'filename': filename,
                'reason': reason, 'ratio_limit': ratio, 'seed_hours': hours,
                'library_retained': value['library_retained'], 'freed_bytes': freed}
    return {"type": kind, "event_id": event_id, "filename": filename,
            "feed": safe_label(value.get("feed", ""), 90)}


def notification_text(app_id, entry):
    kind = entry["type"]
    if app_id == "fjordvpn":
        if kind == "vpn_port_changed":
            previous = entry["previous_port"]
            change = f"{previous} → {entry['port']}" if previous is not None else str(entry["port"])
            return f"🔌 FjordVPN: Ny offentlig port\n\n{entry['profile']}\nPort: {change}"
        heading = ("🚨 FjordVPN: Forbindelsesfejl" if kind == "vpn_failed" else
                   "✅ FjordVPN: Forbindelsen virker igen")
        return heading + "\n" + "\n".join("• " + n for n in entry["profiles"])
    if app_id == 'fjordlens':
        st = entry['stats']
        errors = [('Metadata/konvertering', st['index_errors']), ('Miniaturer', st['thumb_errors']),
                  ('Ansigtsanalyse', st['faces_errors']), ('Billedanalyse', st['ai_errors']), ('Beskrivelser', st['ai_desc_errors'])]
        count = sum(n for _, n in errors)
        heading = ('⚠️ FjordLens · Behandling afbrudt' if entry['status'] == 'stopped' else
                   '🚨 FjordLens · Behandling fejlede' if entry['status'] == 'failed' else
                   '⚠️ FjordLens · Upload behandlet med fejl' if count else '✅ FjordLens · Upload færdigbehandlet')
        blocks = [heading]
        if entry['uploader']:
            blocks.append('Uploadet af: ' + entry['uploader'])
        blocks.append(f"Filer: {st['files']}\nBilleder: {st['images']}\nVideoer: {st['videos']}\nIndekseret: {st['indexed']}\nKonverteret: {st['heic_converted']}")
        blocks.append(f"Ansigtsanalyse\nFiler analyseret: {st['faces_done']}\nFundne ansigter: {st['face_count']}" if st['faces_enabled'] else 'Ansigtsanalyse: slået fra')
        blocks.append('Billedanalyse: ' + (str(st['ai_done']) + ' filer' if st['ai_enabled'] else 'slået fra') +
                      '\nBeskrivelser: ' + (str(st['ai_desc_done']) + ' filer' if st['ai_desc_enabled'] else 'slået fra'))
        blocks.append('Fejl\n' + '\n'.join(f'• {name}: {n}' for name, n in errors if n) if count else
                      'Behandlingen kunne ikke gennemføres. Se detaljer i FjordLens.' if entry['status'] != 'completed' else 'Ingen registrerede behandlingsfejl.')
        if count or entry['status'] != 'completed':
            blocks.append('Se fejl og mulighed for genkørsel i FjordLens.')
        return '\n\n'.join(blocks)
    if kind == 'download_deleted':
        from .bot_queries import decimal
        reason = ('Ratio-mål nået: ' + decimal(entry['ratio_limit']) + ':1' if entry['reason'] == 'ratio' else
                  decimal(entry['seed_hours']) + ' timers seeding nået')
        text = '🗑️ FjordSeed · Automatisk slettet\n\n' + download_title(entry['filename']) + '\n\nÅrsag: ' + reason
        freed = entry.get('freed_bytes')
        if freed is None:
            text += '\nFrigjort plads: ukendt'
        else:
            unit = 'GB' if freed >= 10**9 else 'MB' if freed >= 10**6 else 'kB' if freed >= 1000 else 'B'
            divisor = {'GB': 10**9, 'MB': 10**6, 'kB': 1000, 'B': 1}[unit]
            text += '\nFrigjort plads: ca. ' + decimal(freed / divisor) + ' ' + unit
        if entry['library_retained']:
            text += '\nDen konverterede kopi i biblioteket er bevaret.'
        return text
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

    @contextmanager
    def _connect(self):
        con = sqlite3.connect(self.path, timeout=10)
        con.row_factory = sqlite3.Row
        try:
            with con:
                yield con
        finally:
            con.close()

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
            notify = entry["type"] in {"vpn_failed", "vpn_recovered", "vpn_port_changed", "rss_started", "rss_completed", "download_deleted", "upload_finished"}
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
