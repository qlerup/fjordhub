"""FjordCode worker regression checks that do not require Codex credentials."""
import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "fjordcode_worker" / "worker.py"
SPEC = importlib.util.spec_from_file_location("fjordcode_worker_test_module", SCRIPT)
worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker)


@pytest.mark.parametrize("invalid", [
    "../passwd", "/etc/passwd", "owner/../repo", "owner/repo/other",
    "git@github.com:owner/repo", "https://github.com/owner/repo", "",
    "user name/repo", "owner/.repo",
])
def test_repo_path_rejects_untrusted_names(invalid):
    with pytest.raises(ValueError):
        worker.repo_path(invalid)


def test_repo_path_requires_local_git_directory(tmp_path):
    with patch.object(worker, "ROOT", tmp_path):
        folder = tmp_path / "qlerup--fjordflix"
        folder.mkdir()
        with pytest.raises(ValueError):
            worker.repo_path("qlerup/fjordflix")
        (folder / ".git").mkdir()
        assert worker.repo_path("qlerup/fjordflix") == folder


def test_projects_only_lists_cloned_dirs(tmp_path):
    with patch.object(worker, "ROOT", tmp_path):
        good = tmp_path / "qlerup--fjordhub"
        good.mkdir()
        (good / ".git").mkdir()
        (tmp_path / "not-a-project").mkdir()
        assert worker.projects() == ["qlerup/fjordhub"]
