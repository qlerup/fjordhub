import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import app as fjordhub
from services.auth import AuthService
from services.install_state import InstallState
from services.package_catalog import PackageCatalog
from services.package_manager import PackageError, PackageManager


def package_archive(package_id="notepad", version="1.0.0", extra=None):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("manifest.json", json.dumps({"id": package_id, "version": version}))
        archive.writestr("body.html", "<p>Package body</p>")
        archive.writestr("app.js", "console.log('package')")
        archive.writestr("styles.css", ".package{}")
        if extra:
            archive.writestr(extra[0], extra[1])
    return output.getvalue()


class PackageManagerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.manager = PackageManager(Path(self.tempdir.name))

    def tearDown(self):
        self.tempdir.cleanup()

    @patch("services.package_manager.requests.get")
    def test_downloads_validates_and_removes_package_files(self, get):
        content = package_archive()
        get.return_value = Mock(content=content, raise_for_status=Mock())
        definition = {"id": "notepad", "version": "1.0.0", "download_url": "https://example.test/notepad.zip", "sha256": hashlib.sha256(content).hexdigest()}
        self.manager.install(definition)
        self.assertTrue(self.manager.is_installed("notepad"))
        self.assertIn("Package body", self.manager.read_text("notepad", "body.html"))
        self.manager.uninstall("notepad")
        self.assertFalse(self.manager.is_installed("notepad"))

    @patch("services.package_manager.requests.get")
    def test_rejects_wrong_checksum(self, get):
        get.return_value = Mock(content=package_archive(), raise_for_status=Mock())
        definition = {"id": "notepad", "version": "1.0.0", "download_url": "https://example.test/notepad.zip", "sha256": "0" * 64}
        with self.assertRaisesRegex(PackageError, "checksum"):
            self.manager.install(definition)

    @patch("services.package_manager.requests.get")
    def test_rejects_zip_path_traversal(self, get):
        content = package_archive(extra=("../escape.txt", "bad"))
        get.return_value = Mock(content=content, raise_for_status=Mock())
        definition = {"id": "notepad", "version": "1.0.0", "download_url": "https://example.test/notepad.zip", "sha256": hashlib.sha256(content).hexdigest()}
        with self.assertRaisesRegex(PackageError, "filsti"):
            self.manager.install(definition)
        self.assertFalse((Path(self.tempdir.name) / "escape.txt").exists())


class PackageCatalogTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_empty_url_uses_fallback_without_fetching(self):
        fallback = [{"id": "notepad", "version": "1.0.0"}]
        catalog = PackageCatalog(Path(self.tempdir.name), "", fallback=fallback)
        self.assertEqual(catalog.get_packages(), fallback)
        ok, message = catalog.refresh()
        self.assertFalse(ok)
        self.assertIn("PACKAGES_URL", message)

    @patch("services.package_catalog.fetch_json")
    def test_refresh_validates_entries_and_caches(self, fetch):
        valid = {
            "id": "calendar",
            "name": "Kalender",
            "version": "2.0.0",
            "download_url": "https://example.test/calendar.zip",
            "sha256": "a" * 64,
        }
        fetch.return_value = {"packages": [
            valid,
            {"id": "Bad Id!", "version": "1.0.0", "download_url": "https://x", "sha256": "a" * 64},
            {"id": "http-pakke", "version": "1.0.0", "download_url": "http://usikker", "sha256": "a" * 64},
            {"id": "kort-sha", "version": "1.0.0", "download_url": "https://x/z.zip", "sha256": "abc"},
        ]}
        catalog = PackageCatalog(Path(self.tempdir.name), "https://example.test/catalog.json")
        ok, _ = catalog.refresh()
        self.assertTrue(ok)
        packages = catalog.get_packages()
        self.assertEqual([p["id"] for p in packages], ["calendar"])
        self.assertEqual(packages[0]["accent"], "#3b82f6")

        reloaded = PackageCatalog(Path(self.tempdir.name), "https://example.test/catalog.json")
        self.assertEqual([p["id"] for p in reloaded.get_packages()], ["calendar"])


class PackageRouteTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.previous_state = fjordhub._install_state
        self.previous_auth = fjordhub._auth
        self.previous_manager = fjordhub.package_manager
        self.previous_catalog = fjordhub._package_catalog
        fjordhub._install_state = InstallState(Path(self.tempdir.name))
        fjordhub._auth = AuthService(Path(self.tempdir.name) / "hub.db")
        fjordhub.package_manager = PackageManager(Path(self.tempdir.name))
        fjordhub._package_catalog = PackageCatalog(
            Path(self.tempdir.name), "", fallback=fjordhub.BUILTIN_PACKAGES
        )
        admin_id = fjordhub._auth.create_user("admin", "secret123", role="admin")
        self.admin = fjordhub._auth.get_by_id(admin_id)
        self.client = fjordhub.app.test_client()
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.admin.id)
            session["_fresh"] = True

    def tearDown(self):
        fjordhub._install_state = self.previous_state
        fjordhub._auth = self.previous_auth
        fjordhub.package_manager = self.previous_manager
        fjordhub._package_catalog = self.previous_catalog
        self.tempdir.cleanup()

    def test_store_and_installed_apps_are_separate(self):
        store = self.client.get("/store")
        installed = self.client.get("/packages")
        self.assertIn("Kalender", store.get_data(as_text=True))
        self.assertNotIn("package-card", installed.get_data(as_text=True))

    def test_package_must_be_installed_before_opening(self):
        response = self.client.get("/packages/notepad")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/packages"))

    @patch("services.package_manager.requests.get")
    def test_admin_can_install_open_and_uninstall_package(self, get):
        package = next(item for item in fjordhub.BUILTIN_PACKAGES if item["id"] == "notepad")
        content = package_archive(version=package["version"])
        get.return_value = Mock(content=content, raise_for_status=Mock())
        definition = dict(
            package,
            sha256=hashlib.sha256(content).hexdigest(),
            download_url="https://example.test/notepad.zip",
        )
        fjordhub._package_catalog = PackageCatalog(Path(self.tempdir.name) / "cat", "", fallback=[definition])
        response = self.client.post("/api/packages/notepad/install")
        self.assertEqual(response.status_code, 200)
        page = self.client.get("/packages/notepad")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Package body", page.get_data(as_text=True))
        asset = self.client.get("/packages/notepad/asset/styles.css")
        self.assertEqual(asset.status_code, 200)
        self.assertEqual(asset.headers.get("Cache-Control"), "no-cache")
        asset.close()  # send_file holder ellers filen åben på Windows
        self.assertTrue((Path(self.tempdir.name) / "packages" / "notepad").exists())
        self.client.post("/api/packages/notepad/uninstall")
        self.assertFalse((Path(self.tempdir.name) / "packages" / "notepad").exists())

    @patch("services.package_manager.requests.get")
    def test_store_shows_update_button_and_reinstall_updates_package(self, get):
        old = package_archive(version="1.0.0")
        get.return_value = Mock(content=old, raise_for_status=Mock())
        definition = {
            "id": "notepad",
            "name": "Whiteboard",
            "version": "1.0.0",
            "download_url": "https://example.test/notepad.zip",
            "sha256": hashlib.sha256(old).hexdigest(),
        }
        fjordhub._package_catalog = PackageCatalog(Path(self.tempdir.name) / "cat1", "", fallback=[definition])
        self.assertEqual(self.client.post("/api/packages/notepad/install").status_code, 200)

        new = package_archive(version="2.0.0")
        get.return_value = Mock(content=new, raise_for_status=Mock())
        new_definition = dict(definition, version="2.0.0", sha256=hashlib.sha256(new).hexdigest())
        fjordhub._package_catalog = PackageCatalog(Path(self.tempdir.name) / "cat2", "", fallback=[new_definition])

        store = self.client.get("/store").get_data(as_text=True)
        self.assertIn("v1.0.0 → v2.0.0", store)
        self.assertNotIn('class="btn-install package-update" hidden', store)

        # Asset-URL'er skal cache-buste med den INSTALLEREDE version, ikke katalogets.
        page = self.client.get("/packages/notepad").get_data(as_text=True)
        self.assertIn("app.js?v=1.0.0", page)

        self.assertEqual(self.client.post("/api/packages/notepad/install").status_code, 200)
        self.assertEqual(fjordhub.package_manager.installed_manifest("notepad")["version"], "2.0.0")
        page = self.client.get("/packages/notepad").get_data(as_text=True)
        self.assertIn("app.js?v=2.0.0", page)
        store = self.client.get("/store").get_data(as_text=True)
        self.assertNotIn("v1.0.0 → v2.0.0", store)
        self.assertIn('class="btn-install package-update" hidden', store)

    def test_unknown_package_returns_not_found_from_api(self):
        response = self.client.post("/api/packages/unknown/install")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
