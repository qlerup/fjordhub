"""Security and configuration regression tests for Matrix integration."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest

from services.matrix_hub import MatrixError, MatrixHub, validate_domain, validate_username


@pytest.mark.parametrize("domain", [
    "matrix.example.dk", "chat.gleruphub.dk", "EXAMPLE.COM",
])
def test_valid_matrix_domains(domain):
    assert validate_domain(domain) == domain.lower()


@pytest.mark.parametrize("domain", [
    "", "localhost", "127.0.0.1", "matrix.local", "matrix.internal",
    "https://matrix.example.dk", "matrix.example.dk:8448", "domain.tld/evil",
    "a..b.dk", "-evil.example.dk", "a.example.dk\nbad",
])
def test_reject_invalid_domains(domain):
    with pytest.raises(MatrixError):
        validate_domain(domain)


@pytest.mark.parametrize("name", ["admin", "root", "fjordhub-bot", "X; rm -rf /", "", "../evil"])
def test_reject_reserved_or_unsafe_matrix_users(name):
    with pytest.raises(MatrixError):
        validate_username(name)


def test_status_never_exposes_monitor_token_or_password():
    with TemporaryDirectory() as temp:
        integration = MatrixHub(Path(temp))
        integration._save_state(domain="matrix.example.dk", phase="ready",
                                monitor_token="secret-resource-token")
        integration._save(integration.bot_dir / "config.json",
                          {"password": "secret-password", "allowed_users": ["@a:matrix.example.dk"]})
        import docker
        with patch("services.matrix_hub.docker.from_env", side_effect=docker.errors.DockerException("offline")):
            result = integration.status()
        assert result["domain"] == "matrix.example.dk"
        assert result["users"] == ["@a:matrix.example.dk"]
        assert "secret-resource-token" not in json.dumps(result)
        assert "secret-password" not in json.dumps(result)


def test_notification_allowlist_and_queue():
    with TemporaryDirectory() as temp:
        integration = MatrixHub(Path(temp))
        integration._save(integration.bot_dir / "config.json",
                          {"allowed_users": ["@owner:matrix.example.dk"]})
        for bad in ["@intruder:matrix.example.dk", "", None]:
            with pytest.raises(MatrixError):
                integration.send_test(bad)
        assert not (integration.bot_dir / "outbox").exists()
        assert integration.send_test("@owner:matrix.example.dk") is True
        pending = list((integration.bot_dir / "outbox").glob("*.json"))
        assert len(pending) == 1
        assert json.loads(pending[0].read_text())["recipient"] == "@owner:matrix.example.dk"


def test_refuse_reinstall_or_change_matrix_identity():
    with TemporaryDirectory() as temp:
        integration = MatrixHub(Path(temp))
        integration._save_state(domain="matrix.example.dk", phase="ready")
        with pytest.raises(MatrixError):
            integration.begin_install("other.example.dk", "token")
        with pytest.raises(MatrixError):
            integration.begin_install("matrix.example.dk", "token")


def test_matrix_route_requires_authentication_and_csrf():
    import app as fjordhub
    from services.auth import AuthService
    from services.install_state import InstallState
    with TemporaryDirectory() as temp:
        auth = AuthService(Path(temp) / "hub.db")
        admin_id = auth.create_user("matrix-admin", "longpassword", role="admin")
        user_id = auth.create_user("matrix-reader", "longpassword", role="user")
        with patch.object(fjordhub, "_auth", auth), patch.object(
            fjordhub, "_install_state", InstallState(Path(temp))
        ), patch.object(fjordhub._matrix_hub, "status", return_value={
            "domain": "", "phase": "not_installed", "message": "",
            "server": "not_installed", "bot": "not_installed", "bot_ready": False, "users": []
        }), patch.object(fjordhub._matrix_hub, "send_test") as notify:
            client = fjordhub.app.test_client()
            assert client.get("/integrations/matrix").status_code == 302
            with client.session_transaction() as session:
                session["_user_id"] = auth.get_by_id(user_id).get_id()
                session["_fresh"] = True
            assert client.get("/integrations/matrix").status_code == 403
            assert client.post("/api/matrix/test", json={"user_id": "@bad:example.com"}).status_code == 403
            with client.session_transaction() as session:
                session["_user_id"] = auth.get_by_id(admin_id).get_id()
                session["_fresh"] = True
            assert client.get("/integrations/matrix").status_code == 200
            assert client.post("/api/matrix/test", json={"user_id": "x"},
                               headers={"X-CSRF-Token": "bad"}).status_code == 403
            notify.assert_not_called()
