import tempfile
import unittest
from pathlib import Path

import app as fjordhub
from services.auth import AuthService
from services.install_state import InstallState


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.previous_state = fjordhub._install_state
        self.previous_auth = fjordhub._auth
        fjordhub._install_state = InstallState(Path(self.tempdir.name))
        fjordhub._auth = AuthService(Path(self.tempdir.name) / "hub.db")
        admin_id = fjordhub._auth.create_user("admin", "secret123", role="admin")
        self.admin = fjordhub._auth.get_by_id(admin_id)
        self.client = fjordhub.app.test_client()
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.admin.id)
            session["_fresh"] = True

    def tearDown(self):
        fjordhub._install_state = self.previous_state
        fjordhub._auth = self.previous_auth
        self.tempdir.cleanup()

    def test_package_must_be_installed_before_opening(self):
        response = self.client.get("/packages/notepad")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/packages"))

    def test_admin_can_install_and_open_package(self):
        response = self.client.post("/api/packages/notepad/install")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])
        page = self.client.get("/packages/notepad")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Notesblok", page.get_data(as_text=True))

    def test_unknown_package_returns_not_found_from_api(self):
        response = self.client.post("/api/packages/unknown/install")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
