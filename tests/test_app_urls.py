import tempfile
import unittest
from pathlib import Path

import app as fjordhub
from services.install_state import InstallState


class AppUrlTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.previous_state = fjordhub._install_state
        fjordhub._install_state = InstallState(Path(self.tempdir.name))

    def tearDown(self):
        fjordhub._install_state = self.previous_state
        self.tempdir.cleanup()

    def test_normalizes_domains_and_private_addresses(self):
        self.assertEqual(
            fjordhub._normalize_external_url("photos.example.com"),
            "https://photos.example.com",
        )
        self.assertEqual(
            fjordhub._normalize_external_url("10.10.0.238:9080"),
            "http://10.10.0.238:9080",
        )

    def test_rejects_credentials_query_and_invalid_port(self):
        invalid = (
            "https://user:password@example.com",
            "https://example.com?token=secret",
            "https://example.com:99999",
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                fjordhub._normalize_external_url(value)

    def test_saved_url_is_authoritative(self):
        fjordhub._install_state.set_external_url("demo", "https://demo.example.com")
        with fjordhub.app.test_request_context("/", base_url="https://hub.example.com"):
            self.assertEqual(
                fjordhub._external_app_url({"id": "demo", "default_port": 8080}),
                "https://demo.example.com",
            )

    def test_fallback_uses_installed_app_port(self):
        install_dir = Path(self.tempdir.name) / "demo"
        install_dir.mkdir()
        (install_dir / ".env").write_text("APP_PORT=4321\n", encoding="utf-8")
        fjordhub._install_state.register("demo", str(install_dir))
        with fjordhub.app.test_request_context("/", base_url="http://10.10.0.10"):
            candidates = fjordhub._external_app_url_candidates({"id": "demo", "default_port": 8080})
        self.assertIn("http://10.10.0.10:4321", candidates)


if __name__ == "__main__":
    unittest.main()
