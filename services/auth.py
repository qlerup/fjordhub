import hashlib
import secrets
import sqlite3
import re
import threading
import time
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from services.app_identity import canonical_app_id

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from argon2.low_level import Type
from flask_login import UserMixin
from werkzeug.security import check_password_hash


class User(UserMixin):
    def __init__(
        self,
        id: int,
        username: str,
        role: str,
        created_at: str,
        first_name: str = "",
        last_name: str = "",
        email: str = "",
        language: str = "da",
        must_change_password: bool = False,
    ):
        self.id = id
        self.username = username
        self.role = role
        self.created_at = created_at
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.language = language
        self.must_change_password = bool(must_change_password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


def _row_to_user(row) -> Optional[User]:
    if row is None:
        return None
    return User(
        id=int(row["id"]),
        username=str(row["username"]),
        role=str(row["role"] or "user"),
        created_at=str(row["created_at"] or ""),
        first_name=str(row["first_name"] or ""),
        last_name=str(row["last_name"] or ""),
        email=str(row["email"] or ""),
        language=_normalize_language(row["language"]),
        must_change_password=bool(int(row["must_change_password"] or 0)),
    )


def _hash_api_key(key: str) -> str:
    return hashlib.sha256(str(key or "").encode("utf-8")).hexdigest()


def _user_access_dict(row) -> dict:
    return {
        "id": int(row["id"]),
        "username": str(row["username"]),
        "first_name": str(row["first_name"] or ""),
        "last_name": str(row["last_name"] or ""),
        "email": str(row["email"] or ""),
        "language": _normalize_language(row["language"]),
        "hub_role": str(row["hub_role"] or "user"),
        "role": str(row["app_role"] or "user"),
        "created_at": str(row["created_at"] or ""),
        "must_change_password": bool(row["must_change_password"]) if "must_change_password" in row.keys() else False,
    }


LANGUAGE_VALUES = {"da", "en", "fr"}
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_PASSWORD_HASHER = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=32,
    type=Type.ID,
)


def _hash_password(password: str) -> str:
    return _PASSWORD_HASHER.hash(password)


def _verify_password(stored_hash: str, password: str) -> bool:
    try:
        if stored_hash.startswith("$argon2"):
            return _PASSWORD_HASHER.verify(stored_hash, password)
        return check_password_hash(stored_hash, password)
    except (TypeError, ValueError, VerificationError):
        return False


def _password_needs_rehash(stored_hash: str) -> bool:
    if not stored_hash.startswith("$argon2"):
        return True
    try:
        return _PASSWORD_HASHER.check_needs_rehash(stored_hash)
    except (TypeError, ValueError):
        return True


def _validate_imported_password_hash(password_hash: str) -> str:
    imported_hash = str(password_hash or "").strip()
    if not imported_hash.startswith("$argon2"):
        raise ValueError("Kun Argon2-adgangskodehashes kan importeres.")
    try:
        _PASSWORD_HASHER.check_needs_rehash(imported_hash)
    except (TypeError, ValueError):
        raise ValueError("Ugyldig Argon2-adgangskodehash.")
    return imported_hash


def _normalize_language(value) -> str:
    lang = str(value or "da").strip().lower()
    return lang if lang in LANGUAGE_VALUES else "da"


def _normalize_email(value, required: bool = False) -> str:
    email = str(value or "").strip().lower()
    if not email and not required:
        return ""
    if not EMAIL_RE.fullmatch(email):
        raise ValueError("Indtast en gyldig email-adresse.")
    return email


class AuthService:
    @staticmethod
    def app_roles(app_id: str) -> tuple[str, ...]:
        app_id = canonical_app_id(app_id)
        return ("admin", "manager", "user") if app_id == "fjordlens" else ("admin", "user")

    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._login_attempt_lock = threading.Lock()
        self._login_failures: dict[str, list[float]] = {}
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with closing(self._conn()) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    first_name TEXT NOT NULL DEFAULT '',
                    last_name TEXT NOT NULL DEFAULT '',
                    email TEXT NOT NULL DEFAULT '',
                    language TEXT NOT NULL DEFAULT 'da',
                    role TEXT NOT NULL DEFAULT 'user',
                    must_change_password INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS access_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    token_hash TEXT UNIQUE NOT NULL,
                    prefix TEXT NOT NULL,
                    created_by INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    last_used_at TEXT,
                    revoked_at TEXT
                );
                CREATE TABLE IF NOT EXISTS app_hub_keys (
                    app_id TEXT PRIMARY KEY,
                    api_key TEXT NOT NULL,
                    api_key_hash TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS access_token_apps (
                    token_id INTEGER NOT NULL REFERENCES access_tokens(id) ON DELETE CASCADE,
                    app_id TEXT NOT NULL,
                    PRIMARY KEY(token_id, app_id)
                );
                CREATE TABLE IF NOT EXISTS access_token_updates (
                    token_id INTEGER NOT NULL REFERENCES access_tokens(id) ON DELETE CASCADE,
                    app_id TEXT NOT NULL,
                    PRIMARY KEY(token_id, app_id)
                );
                CREATE TABLE IF NOT EXISTS access_token_metadata (
                    token_id INTEGER NOT NULL REFERENCES access_tokens(id) ON DELETE CASCADE,
                    app_id TEXT NOT NULL,
                    PRIMARY KEY(token_id, app_id)
                );
                CREATE TABLE IF NOT EXISTS user_app_access (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    app_id TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    synced_at TEXT,
                    UNIQUE(user_id, app_id)
                );
            """)
            cols = {r["name"] for r in conn.execute("PRAGMA table_info(app_hub_keys)").fetchall()}
            if "api_key_hash" not in cols:
                conn.execute("ALTER TABLE app_hub_keys ADD COLUMN api_key_hash TEXT")
            user_cols = {r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
            if "first_name" not in user_cols:
                conn.execute("ALTER TABLE users ADD COLUMN first_name TEXT NOT NULL DEFAULT ''")
            if "last_name" not in user_cols:
                conn.execute("ALTER TABLE users ADD COLUMN last_name TEXT NOT NULL DEFAULT ''")
            if "language" not in user_cols:
                conn.execute("ALTER TABLE users ADD COLUMN language TEXT NOT NULL DEFAULT 'da'")
            if "email" not in user_cols:
                conn.execute("ALTER TABLE users ADD COLUMN email TEXT NOT NULL DEFAULT ''")
            if "must_change_password" not in user_cols:
                conn.execute("ALTER TABLE users ADD COLUMN must_change_password INTEGER NOT NULL DEFAULT 0")
            if "onboarding_pending" not in user_cols:
                conn.execute("ALTER TABLE users ADD COLUMN onboarding_pending INTEGER NOT NULL DEFAULT 0")
            conn.execute("UPDATE users SET first_name=COALESCE(first_name, '')")
            conn.execute("UPDATE users SET last_name=COALESCE(last_name, '')")
            conn.execute("UPDATE users SET email=LOWER(TRIM(COALESCE(email, '')))")
            conn.execute("UPDATE users SET language=COALESCE(NULLIF(language, ''), 'da')")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique ON users(email COLLATE NOCASE) WHERE email <> ''")
            # Move existing keys and access grants to the new canonical identity.
            # Existing canonical rows win; repeated startup is idempotent.
            for table in ('app_hub_keys', 'user_app_access', 'access_token_apps', 'access_token_updates', 'access_token_metadata'):
                conn.execute(f"UPDATE OR IGNORE {table} SET app_id='fjord3d' WHERE app_id='fjordshare'")
                conn.execute(f"DELETE FROM {table} WHERE app_id='fjordshare'")
            conn.commit()

    # ── Users ────────────────────────────────────────────────────────────────

    def users_count(self) -> int:
        with closing(self._conn()) as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
            return int(row["c"] if row else 0)

    def create_access_token(self, name: str, created_by: int, days: int = 90, apps=None, update_apps=None, metadata_apps=None) -> str:
        apps = self._validate_token_apps(apps)
        update_apps = self._validate_token_update_apps(update_apps)
        metadata_apps = self._validate_token_update_apps(metadata_apps)
        name = name.strip()
        if not name or len(name) > 80:
            raise ValueError("Navnet skal være mellem 1 og 80 tegn.")
        if type(days) is not int or days not in (0, 30, 90, 365):
            raise ValueError("Vælg en gyldig levetid.")
        owner = self.get_by_id(created_by)
        if not owner or not owner.is_admin or owner.must_change_password:
            raise ValueError("Kræver en administrator med en aktiv adgangskode.")
        token = "fh_at_" + secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        # An empty expiry represents no expiry in the existing NOT NULL column.
        expires_at = (now + timedelta(days=days)).isoformat() if days else ""
        with closing(self._conn()) as conn:
            cursor = conn.execute(
                """INSERT INTO access_tokens
                   (name, token_hash, prefix, created_by, created_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (name, _hash_api_key(token), token[:12], created_by,
                 now.isoformat(), expires_at),
            )
            conn.executemany('INSERT INTO access_token_apps VALUES(?,?)',
                             ((cursor.lastrowid, app_id) for app_id in apps))
            conn.executemany('INSERT INTO access_token_updates VALUES(?,?)',
                             ((cursor.lastrowid, app_id) for app_id in update_apps))
            conn.executemany('INSERT INTO access_token_metadata VALUES(?,?)',
                             ((cursor.lastrowid, app_id) for app_id in metadata_apps))
            conn.commit()
        return token

    def list_access_tokens(self) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        with closing(self._conn()) as conn:
            rows = conn.execute(
                """SELECT t.id, t.name, t.prefix, t.created_at, t.expires_at,
                          t.last_used_at, t.revoked_at,
                          u.role AS owner_role, u.must_change_password
                   FROM access_tokens t LEFT JOIN users u ON u.id=t.created_by
                   ORDER BY t.id DESC"""
            ).fetchall()
            scopes = {}
            for token_id, app_id in conn.execute('SELECT token_id,app_id FROM access_token_apps ORDER BY app_id'):
                scopes.setdefault(token_id, []).append(app_id)
            updates = {}
            for token_id, app_id in conn.execute('SELECT token_id,app_id FROM access_token_updates ORDER BY app_id'):
                updates.setdefault(token_id, []).append(app_id)
            metadata = {}
            for token_id, app_id in conn.execute('SELECT token_id,app_id FROM access_token_metadata ORDER BY app_id'):
                metadata.setdefault(token_id, []).append(app_id)
        result = []
        for row in rows:
            item = dict(row)
            item['apps'] = scopes.get(item['id'], [])
            item['update_apps'] = updates.get(item['id'], [])
            item['metadata_apps'] = metadata.get(item['id'], [])
            item["status"] = (
                "Tilbagekaldt" if item["revoked_at"] else
                "Udløbet" if item["expires_at"] and item["expires_at"] <= now else
                "Inaktiv" if item["owner_role"] != "admin" or item["must_change_password"] else
                "Aktivt"
            )
            result.append(item)
        return result

    def revoke_access_token(self, token_id: int) -> bool:
        with closing(self._conn()) as conn:
            cursor = conn.execute(
                "UPDATE access_tokens SET revoked_at=? WHERE id=? AND revoked_at IS NULL",
                (datetime.now(timezone.utc).isoformat(), token_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_access_token(self, token_id: int) -> bool:
        with closing(self._conn()) as conn:
            conn.execute('BEGIN IMMEDIATE')
            cursor = conn.execute(
                'DELETE FROM access_tokens WHERE id=? AND revoked_at IS NOT NULL',
                (token_id,),
            )
            if not cursor.rowcount:
                return False
            conn.execute('DELETE FROM access_token_apps WHERE token_id=?', (token_id,))
            conn.execute('DELETE FROM access_token_updates WHERE token_id=?', (token_id,))
            conn.execute('DELETE FROM access_token_metadata WHERE token_id=?', (token_id,))
            conn.commit()
            return True

    @staticmethod
    def _validate_token_apps(apps):
        if apps is None:
            return []
        if not isinstance(apps, list) or len(apps) > 20 or any(
                not isinstance(app_id, str) or app_id not in {'fjordflix'} for app_id in apps):
            raise ValueError('Vælg apps med understøttet datadeling.')
        return sorted(set(apps))

    @staticmethod
    def _validate_token_update_apps(apps):
        if apps is None:
            return []
        if not isinstance(apps, list) or len(apps) > 50 or any(
                not isinstance(a, str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,79}', a) for a in apps):
            raise ValueError('Vælg gyldige apps.')
        return sorted(set(apps))

    def update_access_token_apps(self, token_id: int, apps, update_apps=None, metadata_apps=None) -> bool:
        apps = self._validate_token_apps(apps)
        updates = self._validate_token_update_apps(update_apps) if update_apps is not None else None
        metadata = self._validate_token_update_apps(metadata_apps) if metadata_apps is not None else None
        with closing(self._conn()) as conn:
            conn.execute('BEGIN IMMEDIATE')
            if not conn.execute('SELECT 1 FROM access_tokens WHERE id=? AND revoked_at IS NULL', (token_id,)).fetchone():
                return False
            conn.execute('DELETE FROM access_token_apps WHERE token_id=?', (token_id,))
            conn.executemany('INSERT INTO access_token_apps VALUES(?,?)', ((token_id, a) for a in apps))
            if updates is not None:
                conn.execute('DELETE FROM access_token_updates WHERE token_id=?', (token_id,))
                conn.executemany('INSERT INTO access_token_updates VALUES(?,?)', ((token_id, a) for a in updates))
            if metadata is not None:
                conn.execute('DELETE FROM access_token_metadata WHERE token_id=?', (token_id,))
                conn.executemany('INSERT INTO access_token_metadata VALUES(?,?)', ((token_id, a) for a in metadata))
            conn.commit()
            return True

    def authenticate_access_token(self, token: str) -> bool:
        return self.access_token_grant(token) is not None

    def access_token_grant(self, token: str):
        if not re.fullmatch(r"fh_at_[A-Za-z0-9_-]{43}", token):
            return None
        now = datetime.now(timezone.utc).isoformat()
        with closing(self._conn()) as conn:
            cursor = conn.execute(
                """UPDATE access_tokens SET last_used_at=?
                   WHERE token_hash=? AND revoked_at IS NULL
                   AND (expires_at='' OR expires_at>?)
                   AND created_by IN (
                       SELECT id FROM users WHERE role='admin' AND must_change_password=0
                   )""",
                (now, _hash_api_key(token), now),
            )
            if cursor.rowcount != 1:
                conn.commit()
                return None
            token_id = conn.execute('SELECT id FROM access_tokens WHERE token_hash=?', (_hash_api_key(token),)).fetchone()[0]
            apps = [r[0] for r in conn.execute('SELECT app_id FROM access_token_apps WHERE token_id=? ORDER BY app_id', (token_id,))]
            updates = [r[0] for r in conn.execute('SELECT app_id FROM access_token_updates WHERE token_id=? ORDER BY app_id', (token_id,))]
            metadata = [r[0] for r in conn.execute('SELECT app_id FROM access_token_metadata WHERE token_id=? ORDER BY app_id', (token_id,))]
            conn.commit()
            return {'id': token_id, 'apps': apps, 'update_apps': updates, 'metadata_apps': metadata}

    def admin_count(self) -> int:
        with closing(self._conn()) as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM users WHERE role='admin'").fetchone()
            return int(row["c"] if row else 0)

    def get_by_id(self, user_id: int) -> Optional[User]:
        with closing(self._conn()) as conn:
            row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
            return _row_to_user(row)

    def get_by_username(self, username: str) -> Optional[User]:
        with closing(self._conn()) as conn:
            row = conn.execute("SELECT * FROM users WHERE username=?", (username.strip(),)).fetchone()
            return _row_to_user(row)

    def get_by_email(self, email: str) -> Optional[User]:
        normalized_email = str(email or "").strip().lower()
        if not normalized_email:
            return None
        with closing(self._conn()) as conn:
            row = conn.execute("SELECT * FROM users WHERE email=?", (normalized_email,)).fetchone()
            return _row_to_user(row)

    def _available_username(self, base_username: str) -> str:
        normalized_base = str(base_username or "").strip().lower()
        if not normalized_base:
            raise ValueError("Brugernavn eller email-adresse er påkrævet.")
        candidate = normalized_base
        suffix = 2
        while self.get_by_username(candidate) is not None:
            candidate = f"{normalized_base}-{suffix}"
            suffix += 1
        return candidate

    def _login_key(self, row, login: str) -> str:
        return f"user:{int(row['id'])}" if row is not None else f"login:{login.casefold()}"

    def _login_locked(self, key: str) -> bool:
        now = time.monotonic()
        with self._login_attempt_lock:
            recent = [stamp for stamp in self._login_failures.get(key, []) if now - stamp < 300]
            if recent:
                self._login_failures[key] = recent
            else:
                self._login_failures.pop(key, None)
            return len(recent) >= 5

    def _login_failed(self, key: str) -> None:
        now = time.monotonic()
        with self._login_attempt_lock:
            cutoff = now - 300
            for stale_key in list(self._login_failures):
                recent = [stamp for stamp in self._login_failures[stale_key] if stamp >= cutoff]
                if recent:
                    self._login_failures[stale_key] = recent
                else:
                    self._login_failures.pop(stale_key, None)
            if key not in self._login_failures and len(self._login_failures) >= 4096:
                self._login_failures.pop(next(iter(self._login_failures)), None)
            self._login_failures.setdefault(key, []).append(now)

    def _login_succeeded(self, key: str) -> None:
        with self._login_attempt_lock:
            self._login_failures.pop(key, None)

    def check_password(self, username: str, password: str) -> Optional[User]:
        login = str(username or "").strip()
        with closing(self._conn()) as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username=? OR email=?", (login, login)
            ).fetchone()
            key = self._login_key(row, login)
            if self._login_locked(key):
                return None
            if row is None:
                self._login_failed(key)
                return None
            stored_hash = str(row["password_hash"] or "")
            if not _verify_password(stored_hash, password):
                self._login_failed(key)
                return None
            self._login_succeeded(key)
            if _password_needs_rehash(stored_hash):
                conn.execute(
                    "UPDATE users SET password_hash=? WHERE id=?",
                    (_hash_password(password), int(row["id"])),
                )
                conn.commit()
        return _row_to_user(row)

    def create_user(
        self,
        username: str,
        password: str,
        role: str = "user",
        first_name: str = "",
        last_name: str = "",
        email: str = "",
        language: str = "da",
        require_password_change: bool = False,
        first_setup: bool = False,
    ) -> int:
        username = username.strip()
        first_name = str(first_name or "").strip()
        last_name = str(last_name or "").strip()
        email = _normalize_email(email)
        language = _normalize_language(language)
        if not username:
            raise ValueError("Brugernavn er påkrævet.")
        if not password:
            raise ValueError("Adgangskode er påkrævet.")
        if len(password) < 6:
            raise ValueError("Adgangskoden skal være mindst 6 tegn.")
        if role not in ("admin", "user"):
            raise ValueError("Ugyldig rolle.")
        return self._create_user_record(
            username,
            _hash_password(password),
            role,
            first_name,
            last_name,
            email,
            language,
            require_password_change,
            first_setup,
        )

    def create_user_with_password_hash(
        self,
        username: str,
        password_hash: str,
        role: str = "user",
        first_name: str = "",
        last_name: str = "",
        email: str = "",
        language: str = "da",
        require_password_change: bool = False,
    ) -> int:
        username = username.strip()
        first_name = str(first_name or "").strip()
        last_name = str(last_name or "").strip()
        email = _normalize_email(email)
        language = _normalize_language(language)
        if not username:
            raise ValueError("Brugernavn er påkrævet.")
        if role not in ("admin", "user"):
            raise ValueError("Ugyldig rolle.")
        return self._create_user_record(
            username,
            _validate_imported_password_hash(password_hash),
            role,
            first_name,
            last_name,
            email,
            language,
            require_password_change,
        )

    def _create_user_record(
        self,
        username: str,
        password_hash: str,
        role: str,
        first_name: str,
        last_name: str,
        email: str,
        language: str,
        require_password_change: bool = False,
        first_setup: bool = False,
    ) -> int:
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        with closing(self._conn()) as conn:
            try:
                if first_setup:
                    conn.execute("BEGIN IMMEDIATE")
                    if role != "admin" or conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
                        raise ValueError("FjordHub er allerede opsat.")
                cur = conn.execute(
                    """
                    INSERT INTO users (username, password_hash, first_name, last_name, email, language, role, must_change_password, created_at, onboarding_pending)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (username, password_hash, first_name, last_name, email, language, role, int(bool(require_password_change)), now, int(first_setup)),
                )
                conn.commit()
                return int(cur.lastrowid)
            except sqlite3.IntegrityError:
                raise ValueError("Brugernavnet eller email-adressen er allerede i brug.")

    def onboarding_pending(self, user_id: int) -> bool:
        with closing(self._conn()) as conn:
            row = conn.execute("SELECT onboarding_pending FROM users WHERE id=? AND role='admin'", (user_id,)).fetchone()
        return bool(row and row[0])

    def onboarding_step(self, user_id: int) -> int:
        with closing(self._conn()) as conn:
            row = conn.execute("SELECT onboarding_pending FROM users WHERE id=? AND role='admin'", (user_id,)).fetchone()
        return int(row[0]) if row else 0

    def advance_onboarding(self, user_id: int) -> None:
        with closing(self._conn()) as conn:
            conn.execute("UPDATE users SET onboarding_pending=2 WHERE id=? AND onboarding_pending=1", (user_id,))
            conn.commit()

    def finish_onboarding(self, user_id: int) -> None:
        with closing(self._conn()) as conn:
            conn.execute("UPDATE users SET onboarding_pending=0 WHERE id=?", (user_id,))
            conn.commit()

    def update_user(
        self,
        user_id: int,
        username: str = "",
        first_name: str = "",
        last_name: str = "",
        email: str = "",
        language: str = "da",
        role: str = "user",
        new_password: str = "",
    ) -> Optional[User]:
        username = username.strip()
        if not username:
            raise ValueError("Brugernavn er påkrævet.")
        if role not in ("admin", "user"):
            raise ValueError("Ugyldig rolle.")
        first_name = str(first_name or "").strip()
        last_name = str(last_name or "").strip()
        email = _normalize_email(email)
        language = _normalize_language(language)
        with closing(self._conn()) as conn:
            try:
                conn.execute(
                    """UPDATE users SET username=?, first_name=?, last_name=?, email=?, language=?, role=?
                       WHERE id=?""",
                    (username, first_name, last_name, email, language, role, int(user_id)),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                raise ValueError("Brugernavnet eller email-adressen er allerede i brug.")
        if new_password:
            self.change_password(user_id, new_password)
        return self.get_by_id(int(user_id))

    def update_user_profile(
        self,
        user_id: int,
        first_name: str = "",
        last_name: str = "",
        email: str | None = None,
        language: str = "da",
    ) -> Optional[User]:
        with closing(self._conn()) as conn:
            conn.execute(
                """
                UPDATE users
                SET first_name=?, last_name=?, email=COALESCE(?, email), language=?
                WHERE id=?
                """,
                (
                    str(first_name or "").strip(),
                    str(last_name or "").strip(),
                    None if email is None else _normalize_email(email),
                    _normalize_language(language),
                    int(user_id),
                ),
            )
            conn.commit()
        return self.get_by_id(int(user_id))

    def change_password(self, user_id: int, new_password: str) -> None:
        if len(new_password) < 6:
            raise ValueError("Adgangskoden skal være mindst 6 tegn.")
        pw_hash = _hash_password(new_password)
        with closing(self._conn()) as conn:
            conn.execute(
                "UPDATE users SET password_hash=?, must_change_password=0 WHERE id=?", (pw_hash, user_id)
            )
            conn.commit()

    def delete_user(self, user_id: int) -> None:
        with closing(self._conn()) as conn:
            conn.execute("DELETE FROM users WHERE id=?", (user_id,))
            conn.commit()

    def get_all_users(self) -> list:
        with closing(self._conn()) as conn:
            rows = conn.execute(
                "SELECT * FROM users ORDER BY id ASC"
            ).fetchall()
            return [_row_to_user(r) for r in rows]

    def get_all_users_with_access(self) -> list[dict]:
        users = self.get_all_users()
        result = []
        for u in users:
            access = self.get_user_app_access(u.id)
            result.append({
                "id": u.id,
                "username": u.username,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "email": u.email,
                "language": u.language,
                "role": u.role,
                "is_admin": u.is_admin,
                "created_at": u.created_at,
                "app_access": access,
            })
        return result

    # ── Hub keys ─────────────────────────────────────────────────────────────

    def save_hub_key(self, app_id: str, key: str) -> None:
        app_id = canonical_app_id(app_id)
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        with closing(self._conn()) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO app_hub_keys (app_id, api_key, api_key_hash, created_at) VALUES (?, ?, ?, ?)",
                (app_id, "", _hash_api_key(key), now),
            )
            conn.commit()

    def get_hub_key(self, app_id: str) -> Optional[str]:
        app_id = canonical_app_id(app_id)
        with closing(self._conn()) as conn:
            row = conn.execute(
                "SELECT api_key, api_key_hash FROM app_hub_keys WHERE app_id=?", (app_id,)
            ).fetchone()
            if not row:
                return None
            return str(row["api_key_hash"] or row["api_key"] or "")

    def verify_hub_key(self, app_id: str, key: str) -> bool:
        app_id = canonical_app_id(app_id)
        if not app_id or not key:
            return False
        with closing(self._conn()) as conn:
            row = conn.execute(
                "SELECT api_key, api_key_hash FROM app_hub_keys WHERE app_id=?", (app_id,)
            ).fetchone()
            if not row:
                return False
            stored_hash = str(row["api_key_hash"] or "")
            if stored_hash:
                return secrets.compare_digest(stored_hash, _hash_api_key(key))
            stored_plain = str(row["api_key"] or "")
            ok = bool(stored_plain and secrets.compare_digest(stored_plain, key))
            if ok:
                conn.execute(
                    "UPDATE app_hub_keys SET api_key='', api_key_hash=? WHERE app_id=?",
                    (_hash_api_key(key), app_id),
                )
                conn.commit()
            return ok

    def delete_hub_key(self, app_id: str) -> None:
        app_id = canonical_app_id(app_id)
        with closing(self._conn()) as conn:
            conn.execute("DELETE FROM app_hub_keys WHERE app_id=?", (app_id,))
            conn.execute("DELETE FROM user_app_access WHERE app_id=?", (app_id,))
            conn.commit()

    def get_apps_with_keys(self) -> list[str]:
        with closing(self._conn()) as conn:
            rows = conn.execute(
                "SELECT app_id FROM app_hub_keys ORDER BY app_id"
            ).fetchall()
            return [str(r["app_id"]) for r in rows]

    # ── User app access ──────────────────────────────────────────────────────

    def set_user_app_access(self, user_id: int, app_id: str, role: str = "user") -> None:
        app_id = canonical_app_id(app_id)
        if role not in self.app_roles(app_id):
            role = "user"
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        with closing(self._conn()) as conn:
            conn.execute(
                """INSERT INTO user_app_access (user_id, app_id, role, synced_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(user_id, app_id)
                   DO UPDATE SET role=excluded.role, synced_at=excluded.synced_at""",
                (user_id, app_id, role, now),
            )
            conn.commit()

    def remove_user_app_access(self, user_id: int, app_id: str) -> None:
        app_id = canonical_app_id(app_id)
        with closing(self._conn()) as conn:
            conn.execute(
                "DELETE FROM user_app_access WHERE user_id=? AND app_id=?",
                (user_id, app_id),
            )
            conn.commit()

    def get_user_app_access(self, user_id: int) -> list[dict]:
        with closing(self._conn()) as conn:
            rows = conn.execute(
                "SELECT app_id, role, synced_at FROM user_app_access WHERE user_id=? ORDER BY app_id",
                (user_id,),
            ).fetchall()
            return [
                {"app_id": r["app_id"], "role": r["role"], "synced_at": r["synced_at"]}
                for r in rows
            ]

    def get_user_app_role(self, user_id: int, app_id: str) -> Optional[str]:
        app_id = canonical_app_id(app_id)
        with closing(self._conn()) as conn:
            row = conn.execute(
                "SELECT role FROM user_app_access WHERE user_id=? AND app_id=?",
                (int(user_id), str(app_id)),
            ).fetchone()
            return str(row["role"]) if row else None

    def authenticate_app_user(self, app_id: str, username: str, password: str) -> Optional[dict]:
        app_id = canonical_app_id(app_id)
        user = self.check_password(username, password)
        if not user:
            return None
        role = self.get_user_app_role(user.id, app_id)
        if not role:
            return None
        return {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "language": user.language,
            "hub_role": user.role,
            "role": role,
            "created_at": user.created_at,
            "must_change_password": user.must_change_password,
        }

    def change_app_user_password(
        self, app_id: str, username: str, current_password: str, new_password: str
    ) -> Optional[dict]:
        """Skift adgangskode på vegne af en app (fx ved tvungent skift ved første login).

        Kræver at den nuværende adgangskode er korrekt, og at brugeren har adgang
        til appen. Rydder must_change_password-flaget.
        """
        app_id = canonical_app_id(app_id)
        user = self.check_password(username, current_password)
        if not user:
            return None
        role = self.get_user_app_role(user.id, app_id)
        if not role:
            return None
        self.change_password(user.id, new_password)
        return {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "language": user.language,
            "hub_role": user.role,
            "role": role,
            "created_at": user.created_at,
            "must_change_password": False,
        }

    def list_app_users(self, app_id: str) -> list[dict]:
        app_id = canonical_app_id(app_id)
        with closing(self._conn()) as conn:
            rows = conn.execute(
                """
                SELECT u.id, u.username, u.first_name, u.last_name, u.email, u.language,
                       u.role AS hub_role, u.created_at, u.must_change_password,
                       a.role AS app_role
                FROM user_app_access a
                JOIN users u ON u.id = a.user_id
                WHERE a.app_id=?
                ORDER BY u.username COLLATE NOCASE
                """,
                (str(app_id),),
            ).fetchall()
            return [_user_access_dict(r) for r in rows]

    def create_or_grant_app_user(
        self,
        app_id: str,
        username: str,
        password: str = "",
        role: str = "user",
        first_name: str = "",
        last_name: str = "",
        email: str = "",
        language: str = "",
        password_hash: str = "",
    ) -> dict:
        app_id = canonical_app_id(app_id)
        username = str(username or "").strip()
        first_name = str(first_name or "").strip()
        last_name = str(last_name or "").strip()
        email = _normalize_email(email)
        raw_language = str(language or "").strip()
        metadata_provided = bool(first_name or last_name or email or raw_language)
        language = _normalize_language(raw_language) if raw_language else "da"
        if role not in self.app_roles(app_id):
            role = "user"
        user = self.get_by_username(username) if username else None
        if user is None and email:
            user = self.get_by_email(email)
        if user:
            user_id = user.id
            username = user.username
            if metadata_provided:
                user = self.update_user(
                    user_id, username=user.username, first_name=first_name or user.first_name,
                    last_name=last_name or user.last_name, email=email or user.email,
                    language=language, role=user.role,
                ) or user
        else:
            if not username:
                if not email:
                    raise ValueError("Brugernavn eller email-adresse er påkrævet.")
                username = self._available_username(email.split("@", 1)[0])
            if password_hash:
                user_id = self.create_user_with_password_hash(
                    username,
                    password_hash,
                    role="user",
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    language=language,
                )
            else:
                # Admin har valgt startkoden i appen; brugeren skal selv vælge en ny ved første login
                user_id = self.create_user(
                    username,
                    password,
                    role="user",
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    language=language,
                    require_password_change=True,
                )
            user = self.get_by_id(user_id)
        self.set_user_app_access(user_id, app_id, role)
        return {
            "id": int(user_id),
            "username": username if user is None else user.username,
            "first_name": "" if user is None else user.first_name,
            "last_name": "" if user is None else user.last_name,
            "email": "" if user is None else user.email,
            "language": language if user is None else user.language,
            "hub_role": "user" if user is None else user.role,
            "role": role,
            "created_at": "" if user is None else user.created_at,
        }

    def update_app_user_role(self, user_id: int, app_id: str, role: str) -> Optional[dict]:
        app_id = canonical_app_id(app_id)
        if role not in self.app_roles(app_id):
            raise ValueError("Ugyldig rolle.")
        user = self.get_by_id(int(user_id))
        if not user:
            return None
        if not self.get_user_app_role(user.id, app_id):
            return None
        self.set_user_app_access(user.id, app_id, role)
        return {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "language": user.language,
            "hub_role": user.role,
            "role": role,
            "created_at": user.created_at,
        }
