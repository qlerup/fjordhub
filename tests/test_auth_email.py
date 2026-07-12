import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from services.auth import AuthService
from werkzeug.security import generate_password_hash


URBAN_EXPLORER_ARGON2_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$QZV0ILuFRpAnAxwM15BS3g$"
    "XhiBx0n5XkjsBZ3+01PxXGimKmCBV535JrxzcE5KHuE"
)


class AuthEmailTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "hub.db"
        self.auth = AuthService(self.db_path)

    def tearDown(self):
        self.tempdir.cleanup()

    def _stored_password_hash(self, username: str) -> str:
        with closing(sqlite3.connect(self.db_path)) as conn:
            row = conn.execute(
                "SELECT password_hash FROM users WHERE username=?", (username,)
            ).fetchone()
        return str(row[0])

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

    def test_new_users_use_urban_explorer_compatible_argon2id(self):
        self.auth.create_user("demo", "secret1")

        stored_hash = self._stored_password_hash("demo")
        self.assertTrue(stored_hash.startswith("$argon2id$"))
        self.assertIsNotNone(self.auth.check_password("demo", "secret1"))

    def test_legacy_werkzeug_hash_is_upgraded_after_correct_login(self):
        legacy_hash = generate_password_hash("secret1")
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                ("legacy", legacy_hash, "user", "2026-07-12 12:00"),
            )
            conn.commit()

        self.assertIsNone(self.auth.check_password("legacy", "wrong-password"))
        self.assertEqual(self._stored_password_hash("legacy"), legacy_hash)
        self.assertIsNotNone(self.auth.check_password("legacy", "secret1"))
        self.assertTrue(self._stored_password_hash("legacy").startswith("$argon2id$"))

    def test_urban_explorer_argon2id_hash_can_log_in(self):
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                ("urban-explorer", URBAN_EXPLORER_ARGON2_HASH, "user", "2026-07-12 12:00"),
            )
            conn.commit()

        self.assertIsNone(self.auth.check_password("urban-explorer", "wrong-password"))
        self.assertIsNotNone(
            self.auth.check_password("urban-explorer", "urban-explorer-fixture")
        )
        migrated_hash = self._stored_password_hash("urban-explorer")
        self.assertTrue(migrated_hash.startswith("$argon2id$"))
        self.assertNotEqual(migrated_hash, URBAN_EXPLORER_ARGON2_HASH)

    def test_app_user_can_be_imported_with_an_urban_explorer_hash(self):
        self.auth.create_or_grant_app_user(
            "urban-explorer",
            "imported-user",
            password_hash=URBAN_EXPLORER_ARGON2_HASH,
        )

        user = self.auth.authenticate_app_user(
            "urban-explorer", "imported-user", "urban-explorer-fixture"
        )
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "imported-user")
        self.assertTrue(self._stored_password_hash("imported-user").startswith("$argon2id$"))

    def test_app_user_import_derives_username_from_email(self):
        imported = self.auth.create_or_grant_app_user(
            "urban-explorer",
            "",
            email="Imported.User@Example.com",
            password_hash=URBAN_EXPLORER_ARGON2_HASH,
        )

        self.assertEqual(imported["username"], "imported.user")
        self.assertIsNotNone(
            self.auth.authenticate_app_user(
                "urban-explorer", "imported.user", "urban-explorer-fixture"
            )
        )

    def test_app_user_import_uses_a_suffix_for_username_collision(self):
        self.auth.create_user("imported", "secret1", email="imported@first.example")

        imported = self.auth.create_or_grant_app_user(
            "urban-explorer",
            "",
            email="imported@second.example",
            password_hash=URBAN_EXPLORER_ARGON2_HASH,
        )

        self.assertEqual(imported["username"], "imported-2")

    def test_app_user_import_reuses_an_existing_email_account(self):
        existing_id = self.auth.create_user(
            "existing-user", "secret1", email="existing@example.com"
        )

        imported = self.auth.create_or_grant_app_user(
            "urban-explorer",
            "",
            email="existing@example.com",
            password_hash=URBAN_EXPLORER_ARGON2_HASH,
        )

        self.assertEqual(imported["id"], existing_id)
        self.assertEqual(imported["username"], "existing-user")
        self.assertIsNotNone(self.auth.check_password("existing-user", "secret1"))


if __name__ == "__main__":
    unittest.main()
