import base64
import hashlib
import hmac
import secrets
import smtplib
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat()


class PasswordResetService:
    def __init__(self, db_path: Path, secret_key: str, auth_service):
        self._db_path = db_path
        self._secret = str(secret_key or "").encode("utf-8")
        self._auth = auth_service
        key = base64.urlsafe_b64encode(hashlib.sha256(self._secret + b":mail-settings").digest())
        self._fernet = Fernet(key)
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        with closing(self._conn()) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS hub_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS password_reset_challenges (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    code_hash TEXT NOT NULL,
                    reset_token_hash TEXT,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    expires_at TEXT NOT NULL,
                    verified_at TEXT,
                    used_at TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_password_reset_user_created
                ON password_reset_challenges(user_id, created_at DESC);
            """)
            conn.commit()

    def _hash(self, value: str) -> str:
        return hmac.new(self._secret, value.encode("utf-8"), hashlib.sha256).hexdigest()

    def _encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("ascii")

    def _decrypt(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode("ascii")).decode("utf-8")
        except (InvalidToken, ValueError):
            return ""

    def mail_settings(self) -> dict | None:
        with closing(self._conn()) as conn:
            rows = conn.execute(
                "SELECT key, value FROM hub_settings WHERE key IN ('smtp_user','smtp_password','smtp_host','smtp_port')"
            ).fetchall()
        values = {str(row["key"]): str(row["value"]) for row in rows}
        user = self._decrypt(values.get("smtp_user", ""))
        password = self._decrypt(values.get("smtp_password", ""))
        if not user or not password:
            return None
        return {
            "user": user,
            "password": password,
            "host": values.get("smtp_host") or "smtp.gmail.com",
            "port": int(values.get("smtp_port") or 465),
        }

    def save_mail_settings(self, user: str, password: str, host: str, port: int):
        current = self.mail_settings()
        user = str(user or "").strip().lower()
        password = "".join(str(password or "").split()) or (current or {}).get("password", "")
        host = str(host or "smtp.gmail.com").strip()
        port = int(port or 465)
        if "@" not in user or not password:
            raise ValueError("Email og app-adgangskode er påkrævet.")
        with self._smtp(user, password, host, port) as client:
            client.noop()
        values = {
            "smtp_user": self._encrypt(user),
            "smtp_password": self._encrypt(password),
            "smtp_host": host,
            "smtp_port": str(port),
        }
        with closing(self._conn()) as conn:
            for key, value in values.items():
                conn.execute(
                    """INSERT INTO hub_settings (key, value, updated_at) VALUES (?, ?, ?)
                       ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
                    (key, value, _iso(_now())),
                )
            conn.commit()

    @staticmethod
    def _smtp(user: str, password: str, host: str, port: int):
        if port == 465:
            client = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            client = smtplib.SMTP(host, port, timeout=10)
            client.starttls()
        client.login(user, password)
        return client

    def _send_code(self, to: str, code: str):
        settings = self.mail_settings()
        if not settings:
            raise RuntimeError("Mailafsendelse er ikke konfigureret.")
        message = EmailMessage()
        message["From"] = formataddr(("FjordHub", settings["user"]))
        message["To"] = to
        message["Subject"] = f"{code} er din sikkerhedskode til FjordHub"
        message.set_content(
            f"Hej\n\nDin sikkerhedskode til FjordHub er: {code}\n\n"
            "Koden udløber om 5 minutter. Hvis du ikke har bedt om den, kan du ignorere denne mail."
        )
        message.add_alternative(f"""<!doctype html>
<html lang="da"><body style="margin:0;padding:0;background:#f5f1e8">
<div style="background:#f5f1e8;padding:32px 16px;font-family:-apple-system,'Segoe UI',Roboto,sans-serif;color:#29251c">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">
    <table role="presentation" cellpadding="0" cellspacing="0" style="width:100%;max-width:560px">
      <tr><td style="padding:0 6px 14px">
        <div style="font-size:11px;letter-spacing:2px;color:#8a8272;text-transform:uppercase;font-weight:700">FjordHub</div>
        <div style="font-family:'Palatino Linotype',Palatino,Georgia,serif;font-size:28px;font-weight:700;margin-top:4px">Nulstil adgangskode</div>
      </td></tr>
      <tr><td style="background:#fffdf7;border:1px solid #e3dccb;border-radius:14px;padding:24px">
        <div style="font-size:14px;line-height:1.6;color:#514b40">Brug sikkerhedskoden herunder for at vælge en ny adgangskode.</div>
        <div style="margin:22px 0;padding:18px 12px;background:#edf3ff;border:1px solid #3b82f6;border-radius:10px;text-align:center;font-size:30px;font-weight:800;letter-spacing:8px;color:#1d4ed8">{code}</div>
        <div style="font-size:13px;line-height:1.6;color:#8a8272"><strong style="color:#514b40">Koden udløber om 5 minutter.</strong><br>Hvis du ikke har bedt om at nulstille din adgangskode, kan du roligt ignorere mailen.</div>
      </td></tr>
      <tr><td style="padding:14px 6px 0;font-size:12px;color:#8a8272;text-align:center">Sendt automatisk af FjordHub · Du skal ikke besvare denne mail</td></tr>
    </table>
  </td></tr></table>
</div>
</body></html>""", subtype="html")
        with self._smtp(**settings) as client:
            client.send_message(message)

    def request(self, email: str, app_id: str = "") -> str:
        challenge_id = str(uuid.uuid4())
        normalized = str(email or "").strip().lower()
        user = self._auth.get_by_email(normalized)
        if not user or (app_id and not self._auth.get_user_app_role(user.id, app_id)):
            return challenge_id
        now = _now()
        with closing(self._conn()) as conn:
            recent = conn.execute(
                """SELECT id, created_at FROM password_reset_challenges
                   WHERE user_id=? AND used_at IS NULL AND expires_at>?
                   ORDER BY created_at DESC LIMIT 1""",
                (user.id, _iso(now)),
            ).fetchone()
            if recent and datetime.fromisoformat(recent["created_at"]) > now - timedelta(seconds=60):
                return str(recent["id"])
            hourly = conn.execute(
                "SELECT COUNT(*) AS count FROM password_reset_challenges WHERE user_id=? AND created_at>?",
                (user.id, _iso(now - timedelta(hours=1))),
            ).fetchone()
            if int(hourly["count"] or 0) >= 5:
                return str(recent["id"]) if recent else challenge_id
            code = f"{secrets.randbelow(1_000_000):06d}"
            conn.execute(
                """INSERT INTO password_reset_challenges
                   (id, user_id, code_hash, expires_at, created_at) VALUES (?, ?, ?, ?, ?)""",
                (challenge_id, user.id, self._hash(f"{challenge_id}:{code}"),
                 _iso(now + timedelta(minutes=5)), _iso(now)),
            )
            conn.commit()
        try:
            self._send_code(normalized, code)
        except Exception as error:
            print(f"[password-reset] Mail kunne ikke sendes: {error}")
        return challenge_id

    def verify(self, challenge_id: str, code: str) -> str | None:
        with closing(self._conn()) as conn:
            row = conn.execute(
                """SELECT * FROM password_reset_challenges
                   WHERE id=? AND used_at IS NULL AND verified_at IS NULL AND attempts < 5""",
                (challenge_id,),
            ).fetchone()
            valid = bool(
                row and datetime.fromisoformat(row["expires_at"]) > _now()
                and hmac.compare_digest(row["code_hash"], self._hash(f"{challenge_id}:{code}"))
            )
            if not valid:
                if row:
                    conn.execute("UPDATE password_reset_challenges SET attempts=attempts+1 WHERE id=?", (challenge_id,))
                    conn.commit()
                return None
            token = secrets.token_urlsafe(32)
            conn.execute(
                "UPDATE password_reset_challenges SET verified_at=?, reset_token_hash=? WHERE id=?",
                (_iso(_now()), self._hash(f"{challenge_id}:{token}"), challenge_id),
            )
            conn.commit()
            return token

    def complete(self, challenge_id: str, token: str, password: str) -> bool:
        with closing(self._conn()) as conn:
            row = conn.execute(
                """SELECT * FROM password_reset_challenges
                   WHERE id=? AND verified_at IS NOT NULL AND used_at IS NULL""",
                (challenge_id,),
            ).fetchone()
            valid = bool(
                row and datetime.fromisoformat(row["expires_at"]) > _now()
                and hmac.compare_digest(row["reset_token_hash"] or "", self._hash(f"{challenge_id}:{token}"))
            )
            if not valid:
                return False
            user_id = int(row["user_id"])
        self._auth.change_password(user_id, password)
        with closing(self._conn()) as conn:
            conn.execute(
                "UPDATE password_reset_challenges SET used_at=? WHERE user_id=? AND used_at IS NULL",
                (_iso(_now()), user_id),
            )
            conn.commit()
            return True
