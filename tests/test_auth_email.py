import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from services.auth import AuthService


class AuthEmailTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "hub.db"
        self.auth = AuthService(self.db_path)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_existing_database_is_migrated_with_email_column(self):
        legacy_path = Path(self.tempdir.name) / "legacy.db"
        with closing(sqlite3.connect(legacy_path)) as conn:
            conn.execute(
                """CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    created_at TEXT NOT NULL
                )"""
            )
        migrated = AuthService(legacy_path)
        self.assertEqual(migrated.get_all_users(), [])
        with closing(sqlite3.connect(legacy_path)) as conn:
            columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
        self.assertIn("email", columns)

    def test_email_is_normalized_unique_and_returned_to_apps(self):
        user_id = self.auth.create_user(
            "demo", "secret1", email=" Demo@Example.COM ", first_name="Demo"
        )
        self.auth.set_user_app_access(user_id, "urban-explorer", "user")

        user = self.auth.get_by_id(user_id)
        self.assertEqual(user.email, "demo@example.com")
        self.assertEqual(
            self.auth.list_app_users("urban-explorer")[0]["email"],
            "demo@example.com",
        )
        self.assertEqual(
            self.auth.authenticate_app_user("urban-explorer", "demo@example.com", "secret1")["id"],
            user_id,
        )
        with self.assertRaisesRegex(ValueError, "allerede i brug"):
            self.auth.create_user("other", "secret2", email="DEMO@example.com")

    def test_invalid_email_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "gyldig email"):
            self.auth.create_user("demo", "secret1", email="not-an-email")


if __name__ == "__main__":
    unittest.main()
