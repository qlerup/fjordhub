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
            """)
            conn.commit()

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
