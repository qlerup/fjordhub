"""Regression tests for isolated full VS Code desktop installation and proxy."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import docker
from services.auth import AuthService
from services.install_state import InstallState
from services.fjordcode_desktop import CodexDesktop, DesktopError


def test_desktop_not_installed_closes_client():
    manager = CodexDesktop()
    docker_client = MagicMock()
    docker_client.containers.get.side_effect = docker.errors.NotFound("missing")
    with patch("services.fjordcode_desktop.docker.from_env", return_value=docker_client):
        assert manager.status()["phase"] == "not_installed"
    docker_client.close.assert_called_once()


def test_runtime_reuses_fjord_code_network():
    client = MagicMock()
    hub = MagicMock()
    hub.labels = {"com.docker.compose.project": "fjordhub"}
    hub.attrs = {"NetworkSettings": {"Networks": {
        "fjord-net": {}, "fjordhub_fjord-code": {}}}}
    client.containers.get.return_value = hub
    assert CodexDesktop._existing_network_and_project(client) == (
        "fjordhub_fjord-code", "fjordhub")


def test_desktop_install_isolated_and_shares_project_volumes():
    manager = CodexDesktop()
    client = MagicMock()
    hub = MagicMock()
    hub.labels = {"com.docker.compose.project": "fjordhub"}
    hub.attrs = {"NetworkSettings": {"Networks": {"fjordhub_fjord-code": {}}}}

    def get(name):
        if name == "fjordhub":
            return hub
        raise docker.errors.NotFound("missing")
    client.containers.get.side_effect = get
    client.containers.create.return_value.exec_run.return_value.exit_code = 0
    with patch("services.fjordcode_desktop.docker.from_env", return_value=client):
        manager._install()
    kwargs = client.containers.create.call_args.kwargs
    assert kwargs["network"] == "fjordhub_fjord-code"
    assert kwargs["ports"] == {}
    assert kwargs["volumes"]["fjordhub_fjordcode-workspaces"]["bind"] == "/workspaces"
    assert kwargs["volumes"]["fjordhub_fjordcode-home"]["bind"] == "/config/fjordcode-home"
    assert kwargs["environment"]["CODEX_HOME"] == "/config/fjordcode-home/.codex"
    assert kwargs["environment"]["SUBFOLDER"] == "/fjordcode/desktop/"
    assert "/var/run/docker.sock" not in str(kwargs)
    assert kwargs["security_opt"] == ["no-new-privileges:true"]
    client.close.assert_called_once()


def test_nonadmin_cannot_install_or_open_desktop():
    import app as hub
    with TemporaryDirectory() as temp:
        auth = AuthService(Path(temp) / "auth.db")
        administrator = auth.create_user("desktop-admin", "longpassword", role="admin")
        reader = auth.create_user("desktop-reader", "longpassword", role="user")
        with patch.object(hub, "_auth", auth), patch.object(
            hub, "_install_state", InstallState(Path(temp))), patch(
            "services.fjordcode_routes.desktop_manager.status",
            return_value={"phase": "not_installed", "message": "", "extension": ""}
        ), patch("services.fjordcode_routes.desktop_manager.begin_install") as start:
            client = hub.app.test_client()
            assert client.get("/api/fjordcode/desktop/status").status_code == 401
            with client.session_transaction() as session:
                session["_user_id"] = auth.get_by_id(reader).get_id()
                session["_fresh"] = True
            assert client.get("/integrations/codex").status_code == 403
            assert client.post("/api/fjordcode/desktop/install", json={}).status_code == 403
            assert client.get("/fjordcode/desktop/").status_code == 403
            with client.session_transaction() as session:
                session["_user_id"] = auth.get_by_id(administrator).get_id()
                session["_fresh"] = True
                session["hub_csrf"] = "codex-expected"
            assert client.get("/api/fjordcode/desktop/status").status_code == 200
            assert client.post("/api/fjordcode/desktop/install", json={},
                               headers={"X-CSRF-Token": "wrong"}).status_code == 403
            assert start.call_count == 0
            assert client.post("/api/fjordcode/desktop/install", json={},
                               headers={"X-CSRF-Token": "codex-expected"}).status_code == 202
            assert start.call_count == 1


def test_proxy_origin_and_paths_with_mocked_desktop():
    import app as hub
    from services.auth import AuthService
    from services.fjordcode_desktop_proxy import same_origin
    from flask import Flask
    local = Flask("test-origin")
    with local.test_request_context("/fjordcode/desktop/", base_url="https://fjordhub.gleruphub.dk/"):
        assert same_origin("https://fjordhub.gleruphub.dk")
        assert not same_origin("https://attacker.example")
        assert not same_origin("https://fjordhub.gleruphub.dk.attacker.net")
        assert not same_origin("")


def test_desktop_errors_do_not_disable_reinstall():
    manager = CodexDesktop()
    client = MagicMock()
    client.containers.get.side_effect = docker.errors.NotFound("absent")
    with patch("services.fjordcode_desktop.docker.from_env", return_value=client):
        assert manager.status()["phase"] == "not_installed"

def test_http_and_websocket_desktop_routes_are_separate():
    import app as hub
    rules = [rule for rule in hub.app.url_map.iter_rules()
             if rule.rule.startswith("/fjordcode/desktop/")]
    assert any(rule.websocket for rule in rules)
    assert any(not rule.websocket for rule in rules)
    assert all(rule.endpoint == "fjordcode.desktop_proxy" for rule in rules)
