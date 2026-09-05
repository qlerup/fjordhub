import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

from services.auth import AuthService
from services.password_reset import PasswordResetService


class PasswordResetTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "hub.db"
        self.auth = AuthService(self.db_path)
        self.user_id = self.auth.create_user("demo", "old-secret", email="demo@example.com")
        self.auth.set_user_app_access(self.user_id, "urban-explorer")
        self.service = PasswordResetService(self.db_path, "test-secret", self.auth)
        self.sent = []
        self.service._send_code = lambda email, code, app_name="FjordHub": self.sent.append((email, code, app_name))

    def tearDown(self):
        self.tempdir.cleanup()

    def test_complete_flow_is_single_use(self):
        challenge = self.service.request("DEMO@example.com", app_id="urban-explorer")
        self.assertEqual(self.sent[0][0], "demo@example.com")
        token = self.service.verify(challenge, self.sent[0][1])
        self.assertTrue(token)
        self.assertTrue(self.service.complete(challenge, token, "new-secret"))
        self.assertFalse(self.service.complete(challenge, token, "another-secret"))
        self.assertIsNotNone(self.auth.check_password("demo", "new-secret"))

    def test_email_is_branded_with_the_requesting_apps_name(self):
        self.service.request("demo@example.com", app_id="urban-explorer", app_name="Urban Explorer")
        self.assertEqual(self.sent[0][2], "Urban Explorer")

    def test_email_defaults_to_fjordhub_branding_without_an_app_name(self):
        self.service.request("demo@example.com")
        self.assertEqual(self.sent[0][2], "FjordHub")

    def test_unknown_email_has_same_shape_but_no_challenge(self):
        challenge = self.service.request("missing@example.com", app_id="urban-explorer")
        self.assertTrue(challenge)
        self.assertEqual(self.sent, [])
        self.assertIsNone(self.service.verify(challenge, "123456"))

    def test_request_within_one_minute_keeps_active_code(self):
        first = self.service.request("demo@example.com")
        second = self.service.request("demo@example.com")
        self.assertEqual(second, first)
        self.assertEqual(len(self.sent), 1)

    def test_user_without_app_access_does_not_receive_code(self):
        challenge = self.service.request("demo@example.com", app_id="other-app")
        self.assertTrue(challenge)
        self.assertEqual(self.sent, [])

    def test_code_expires_and_attempts_are_limited(self):
        challenge = self.service.request("demo@example.com")
        code = self.sent[0][1]
        with closing(sqlite3.connect(self.db_path)) as conn:
            expired = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
            conn.execute("UPDATE password_reset_challenges SET expires_at=? WHERE id=?", (expired, challenge))
            conn.commit()
        self.assertIsNone(self.service.verify(challenge, code))

        second_user = self.auth.create_user("second", "old-secret", email="second@example.com")
        challenge = self.service.request("second@example.com")
        for _ in range(5):
            self.assertIsNone(self.service.verify(challenge, "000000"))
        self.assertIsNone(self.service.verify(challenge, self.sent[-1][1]))


if __name__ == "__main__":
    unittest.main()
