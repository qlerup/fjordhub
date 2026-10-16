"""Opt-in FjordCode integration: permissions, Docker isolation and lifecycle."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import docker
from services.auth import AuthService
from services.install_state import InstallState
from services.fjordcode_install import FjordCodeError, FjordCodeManager


def test_manager_status_before_install():
    manager = FjordCodeManager()
    client = MagicMock()
    client.containers.get.side_effect = docker.errors.NotFound("no worker")
    proxy = MagicMock()
    proxy.__enter__.return_value = client
    with patch("services.fjordcode_install.docker.from_env", return_value=proxy):
        assert manager.status()["phase"] == "not_installed"


def test_manager_uses_hubs_existing_volume_and_network():
    client = MagicMock()
    hub = MagicMock()
    hub.labels = {"com.docker.compose.project": "fjordhub"}
    hub.attrs = {
        "Mounts": [{"Destination": "/run/fjordcode-token", "Type": "volume",
                    "Name": "fjordhub_fjordcode-token"}],
        "NetworkSettings": {"Networks": {"fjord-net": {}, "fjordhub_fjord-code": {}}},
    }
    client.containers.get.return_value = hub
    assert FjordCodeManager._runtime_mounts_and_network(client) == (
        "fjordhub_fjordcode-token", "fjordhub_fjord-code", "fjordhub"
    )


def test_manager_refuses_missing_shared_token():
    client = MagicMock()
    hub = MagicMock()
    hub.attrs = {"Mounts": [], "NetworkSettings": {"Networks": {"fjordhub_fjord-code": {}}}}
    client.containers.get.return_value = hub
    with __import__("pytest").raises(FjordCodeError):
        FjordCodeManager._runtime_mounts_and_network(client)


def test_isolated_container_creation():
    manager = FjordCodeManager()
    client = MagicMock()
    hub = MagicMock()
    hub.labels = {"com.docker.compose.project": "fjordhub"}
    hub.attrs = {
        "Mounts": [{"Destination": "/run/fjordcode-token", "Type": "volume",
                    "Name": "fjordhub_fjordcode-token"}],
        "NetworkSettings": {"Networks": {"fjordhub_fjord-code": {}}},
    }
    def get(name):
        if name == "fjordhub-code":
            raise docker.errors.NotFound("not installed")
        if name == "fjordhub":
            return hub
        raise AssertionError(name)
    client.containers.get.side_effect = get
    proxy = MagicMock()
    proxy.__enter__.return_value = client
    with patch("services.fjordcode_install.docker.from_env", return_value=proxy), \
         patch.object(manager, "_build_image") as build:
        manager._install()
    build.assert_called_once_with(client)
    kwargs = client.containers.create.call_args.kwargs
    assert kwargs["network"] == "fjordhub_fjord-code"
    assert kwargs["read_only"] is True
    assert kwargs["cap_drop"] == ["ALL"]
    assert kwargs["user"] == "10001:10001"
    assert kwargs["name"] == "fjordhub-code"
    assert kwargs["volumes"]["fjordhub_fjordcode-token"]["mode"] == "ro"
    assert "/var/run/docker.sock" not in str(kwargs["volumes"])
    assert "/apps" not in str(kwargs["volumes"])
    client.containers.create.return_value.start.assert_called_once()


def test_admin_only_install_chat_and_csrf():
    import app as hub
    with TemporaryDirectory() as temp:
        auth = AuthService(Path(temp) / "auth.db")
        admin = auth.create_user("codex-admin", "strongpassword", role="admin")
        reader = auth.create_user("codex-reader", "strongpassword", role="user")
        with patch.object(hub, "_auth", auth), patch.object(
            hub, "_install_state", InstallState(Path(temp))
        ), patch("services.fjordcode_routes.installer.status",
                 return_value={"phase": "not_installed", "message": ""}), patch(
            "services.fjordcode_routes.installer.begin_install"
        ) as install:
            client = hub.app.test_client()
            assert client.get("/integrations/codex").status_code == 302
            with client.session_transaction() as sess:
                sess["_user_id"] = auth.get_by_id(reader).get_id()
                sess["_fresh"] = True
            assert client.get("/integrations/codex").status_code == 403
            assert client.post("/api/fjordcode/install", json={}).status_code == 403
            with client.session_transaction() as sess:
                sess["_user_id"] = auth.get_by_id(admin).get_id()
                sess["_fresh"] = True
                sess["hub_csrf"] = "real-token"
            assert client.get("/integrations/codex").status_code == 200
            assert client.get("/api/fjordcode/install-status").json["phase"] == "not_installed"
            assert client.post("/api/fjordcode/install", json={},
                               headers={"X-CSRF-Token": "invalid"}).status_code == 403
            assert install.call_count == 0
            result = client.post("/api/fjordcode/install", json={},
                                 headers={"X-CSRF-Token": "real-token"})
            assert result.status_code == 202
            assert install.call_count == 1
            assert client.get("/fjordcode").status_code == 302
