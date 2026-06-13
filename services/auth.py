import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


class User(UserMixin):
    def __init__(self, id: int, username: str, role: str, created_at: str):
        self.id = id
        self.username = username
        self.role = role
        self.created_at = created_at

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
    )


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
                    role TEXT NOT NULL DEFAULT 'user',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS app_hub_keys (
                    app_id TEXT PRIMARY KEY,
                    api_key TEXT NOT NULL,
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

    def check_password(self, username: str, password: str) -> Optional[User]:
        with closing(self._conn()) as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username=?", (username.strip(),)
            ).fetchone()
        if row is None:
            return None
        if not check_password_hash(str(row["password_hash"]), password):
            return None
        return _row_to_user(row)

    def create_user(self, username: str, password: str, role: str = "user") -> int:
        username = username.strip()
        if not username:
            raise ValueError("Brugernavn er påkrævet.")
        if not password:
            raise ValueError("Adgangskode er påkrævet.")
        if len(password) < 6:
            raise ValueError("Adgangskoden skal være mindst 6 tegn.")
        if role not in ("admin", "user"):
            raise ValueError("Ugyldig rolle.")
        pw_hash = generate_password_hash(password)
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        with closing(self._conn()) as conn:
            try:
                cur = conn.execute(
                    "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                    (username, pw_hash, role, now),
                )
                conn.commit()
                return int(cur.lastrowid)
            except sqlite3.IntegrityError:
                raise ValueError("Brugernavnet er allerede i brug.")

    def change_password(self, user_id: int, new_password: str) -> None:
        if len(new_password) < 6:
            raise ValueError("Adgangskoden skal være mindst 6 tegn.")
        pw_hash = generate_password_hash(new_password)
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
                "INSERT OR REPLACE INTO app_hub_keys (app_id, api_key, created_at) VALUES (?, ?, ?)",
                (app_id, key, now),
            )
            conn.commit()

    def get_hub_key(self, app_id: str) -> Optional[str]:
        with closing(self._conn()) as conn:
            row = conn.execute(
                "SELECT api_key FROM app_hub_keys WHERE app_id=?", (app_id,)
            ).fetchone()
            return str(row["api_key"]) if row else None

    def verify_hub_key(self, app_id: str, key: str) -> bool:
        stored = self.get_hub_key(app_id)
        return bool(stored and stored == key)

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
