import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.install_state import InstallState
from services.update_manager import UpdateManager


class UpdateManagerBuildSelectionTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.manager = UpdateManager(InstallState(self.root / "state.json"))

    def tearDown(self):
        self.tempdir.cleanup()

    def _compose_result(self):
        config = {
            "services": {
                "fjordlens": {"build": {"context": str(self.root)}},
                "fjordlens-ai": {"build": {"context": str(self.root / "ai_service")}},
                "database": {"image": "postgres:17"},
            }
        }
        return subprocess.CompletedProcess([], 0, stdout=json.dumps(config), stderr="")

    def test_root_change_rebuilds_root_service_only(self):
        with patch.object(self.manager, "_run", return_value=self._compose_result()):
            selected = self.manager._compose_build_services_for_changes(self.root, ["app.py", "static/app.js"])
        self.assertEqual(selected, ["fjordlens"])

    def test_nested_context_change_rebuilds_root_and_nested_service(self):
        with patch.object(self.manager, "_run", return_value=self._compose_result()):
            selected = self.manager._compose_build_services_for_changes(self.root, ["ai_service/app.py"])
        self.assertEqual(selected, ["fjordlens", "fjordlens-ai"])

    def test_compose_change_rebuilds_all_build_services(self):
        with patch.object(self.manager, "_run", return_value=self._compose_result()):
            selected = self.manager._compose_build_services_for_changes(self.root, ["docker-compose.yml"])
        self.assertEqual(selected, ["fjordlens", "fjordlens-ai"])


class UpdateManagerPackageOnlyTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.manager = UpdateManager(InstallState(self.root / "state.json"))

    def tearDown(self):
        self.tempdir.cleanup()

    def test_package_only_changes_do_not_require_update(self):
        diff = "packages_catalog.json\npackages_src/notepad/app.js\npackages_src/calendar/styles.css\n"
        with patch.object(self.manager, "_git_output", return_value=diff):
            self.assertTrue(self.manager._package_only_update(self.root, "a1", "b2"))

    def test_app_code_changes_require_update(self):
        diff = "packages_catalog.json\napp.py\n"
        with patch.object(self.manager, "_git_output", return_value=diff):
            self.assertFalse(self.manager._package_only_update(self.root, "a1", "b2"))

    def test_empty_diff_keeps_normal_update_semantics(self):
        with patch.object(self.manager, "_git_output", return_value=""):
            self.assertFalse(self.manager._package_only_update(self.root, "a1", "b2"))

    def test_diff_errors_keep_normal_update_semantics(self):
        with patch.object(self.manager, "_git_output", side_effect=RuntimeError("git fejl")):
            self.assertFalse(self.manager._package_only_update(self.root, "a1", "b2"))


if __name__ == "__main__":
    unittest.main()
