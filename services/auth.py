import hashlib
import secrets
import sqlite3
import re
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Optional

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
    ):
        self.id = id
        self.username = username
        self.role = role
        self.created_at = created_at
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.language = language

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
    def __init__(self, db_path: Path):
        self._db_path = db_path
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
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS app_hub_keys (
                    app_id TEXT PRIMARY KEY,
                    api_key TEXT NOT NULL,
                    api_key_hash TEXT,
                    created_at TEXT NOT NULL
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
            conn.execute("UPDATE users SET first_name=COALESCE(first_name, '')")
            conn.execute("UPDATE users SET last_name=COALESCE(last_name, '')")
            conn.execute("UPDATE users SET email=LOWER(TRIM(COALESCE(email, '')))")
            conn.execute("UPDATE users SET language=COALESCE(NULLIF(language, ''), 'da')")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique ON users(email COLLATE NOCASE) WHERE email <> ''")
            conn.commit()

    # ── Users ────────────────────────────────────────────────────────────────

    def users_count(self) -> int:
        with closing(self._conn()) as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
            return int(row["c"] if row else 0)

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

    def check_password(self, username: str, password: str) -> Optional[User]:
        login = str(username or "").strip()
        with closing(self._conn()) as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username=? OR email=?", (login, login)
            ).fetchone()
            if row is None:
                return None
            stored_hash = str(row["password_hash"] or "")
            if not _verify_password(stored_hash, password):
                return None
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
    ) -> int:
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        with closing(self._conn()) as conn:
            try:
                cur = conn.execute(
                    """
                    INSERT INTO users (username, password_hash, first_name, last_name, email, language, role, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (username, password_hash, first_name, last_name, email, language, role, now),
                )
                conn.commit()
                return int(cur.lastrowid)
            except sqlite3.IntegrityError:
                raise ValueError("Brugernavnet eller email-adressen er allerede i brug.")

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
                "UPDATE users SET password_hash=? WHERE id=?", (pw_hash, user_id)
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
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        with closing(self._conn()) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO app_hub_keys (app_id, api_key, api_key_hash, created_at) VALUES (?, ?, ?, ?)",
                (app_id, "", _hash_api_key(key), now),
            )
            conn.commit()

    def get_hub_key(self, app_id: str) -> Optional[str]:
        with closing(self._conn()) as conn:
            row = conn.execute(
                "SELECT api_key, api_key_hash FROM app_hub_keys WHERE app_id=?", (app_id,)
            ).fetchone()
            if not row:
                return None
            return str(row["api_key_hash"] or row["api_key"] or "")

    def verify_hub_key(self, app_id: str, key: str) -> bool:
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
        if role not in ("admin", "user"):
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
        with closing(self._conn()) as conn:
            row = conn.execute(
                "SELECT role FROM user_app_access WHERE user_id=? AND app_id=?",
                (int(user_id), str(app_id)),
            ).fetchone()
            return str(row["role"]) if row else None

    def authenticate_app_user(self, app_id: str, username: str, password: str) -> Optional[dict]:
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
        }

    def list_app_users(self, app_id: str) -> list[dict]:
        with closing(self._conn()) as conn:
            rows = conn.execute(
                """
                SELECT u.id, u.username, u.first_name, u.last_name, u.email, u.language,
                       u.role AS hub_role, u.created_at,
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
        username = str(username or "").strip()
        first_name = str(first_name or "").strip()
        last_name = str(last_name or "").strip()
        email = _normalize_email(email)
        raw_language = str(language or "").strip()
        metadata_provided = bool(first_name or last_name or email or raw_language)
        language = _normalize_language(raw_language) if raw_language else "da"
        if role not in ("admin", "user"):
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
                user_id = self.create_user(
                    username,
                    password,
                    role="user",
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    language=language,
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
        if role not in ("admin", "user"):
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
