import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from services.auth import AuthService
from services.password_reset import PasswordResetService


class _FakeSmtpClient:
    """Stands in for smtplib's SMTP/SMTP_SSL so tests never touch the network,
    while still exercising the real _send_code/_smtp call signatures."""

    def __init__(self):
        self.sent_messages = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def noop(self):
        return (250, b"OK")

    def send_message(self, message):
        self.sent_messages.append(message)


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

    def test_send_code_calls_smtp_with_the_settings_dicts_exact_keys(self):
        """Regression test: mail_settings() returns a 5-key dict (user/password/host/
        port/from_address), but _smtp() only accepts 4 params. _send_code() previously
        called self._smtp(**settings), which raised a silent TypeError on every real
        send (masked by request()'s broad except) - this exercises the real, unpatched
        _send_code so a signature mismatch like that fails loudly again."""
        real_service = PasswordResetService(self.db_path, "test-secret", self.auth)
        fake_save_client = _FakeSmtpClient()
        with patch.object(real_service, "_smtp", return_value=fake_save_client):
            real_service.save_mail_settings("resend", "api-key", "smtp.resend.com", 465, "noreply@example.com")

        fake_send_client = _FakeSmtpClient()
        with patch.object(real_service, "_smtp", return_value=fake_send_client) as mock_smtp:
            real_service._send_code("someone@example.com", "123456", app_name="Urban Explorer")

        mock_smtp.assert_called_once_with("resend", "api-key", "smtp.resend.com", 465)
        self.assertEqual(len(fake_send_client.sent_messages), 1)
        sent = fake_send_client.sent_messages[0]
        self.assertIn("noreply@example.com", sent["From"])
        self.assertEqual(sent["To"], "someone@example.com")
        self.assertIn("123456", sent["Subject"])

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

    def test_forgot_password_is_enabled_by_default(self):
        self.assertTrue(self.service.is_enabled())

    def test_forgot_password_can_be_disabled_and_reenabled(self):
        self.service.set_enabled(False)
        self.assertFalse(self.service.is_enabled())
        self.service.set_enabled(True)
        self.assertTrue(self.service.is_enabled())

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
