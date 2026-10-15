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

def test_matrix_installer_uses_existing_public_origin_without_manual_domain():
    """An existing FjordHub HTTPS origin is the Matrix identity."""
    import app as fjordhub
    from services.auth import AuthService
    from services.install_state import InstallState
    from services.transport_security import TransportPolicy
    with TemporaryDirectory() as tmp:
        auth = AuthService(Path(tmp) / "users.db")
        admin_id = auth.create_user("matrix-owner", "securepassword", role="admin")
        with patch.object(fjordhub, "_auth", auth), patch.object(
                fjordhub, "_install_state", InstallState(Path(tmp))), patch.object(
                fjordhub._matrix_hub, "_state", return_value={}), patch.object(
                fjordhub._matrix_hub, "begin_install") as begin, patch.object(
                fjordhub._matrix_hub, "_save_state"), patch.dict(
                fjordhub.app.config, {"FJORDHUB_TRANSPORT_POLICY":
                                      TransportPolicy.from_config("https://hub.example.dk")}):
            client = fjordhub.app.test_client()
            with client.session_transaction() as session:
                session["_user_id"] = auth.get_by_id(admin_id).get_id()
                session["_fresh"] = True
                session["hub_csrf"] = "valid-matrix-csrf"
            result = client.post("/api/matrix/install", json={},
                                 headers={"X-CSRF-Token": "valid-matrix-csrf"})
            assert result.status_code == 202
            assert begin.call_count == 1
            assert begin.call_args.args[0] == "hub.example.dk"
            assert begin.call_args.args[1].startswith("fh_at_")
            result = client.post("/api/matrix/install", json={"domain": "attacker.example.com"},
                                 headers={"X-CSRF-Token": "valid-matrix-csrf"})
            assert result.status_code == 202
            assert begin.call_args.args[0] == "hub.example.dk"


def test_matrix_install_needs_https_on_existing_domain():
    import app as fjordhub
    from services.auth import AuthService
    from services.install_state import InstallState
    from services.transport_security import TransportPolicy
    with TemporaryDirectory() as tmp:
        auth = AuthService(Path(tmp) / "users.db")
        user_id = auth.create_user("matrix-owner", "securepassword", role="admin")
        with patch.object(fjordhub, "_auth", auth), patch.object(
                fjordhub, "_install_state", InstallState(Path(tmp))), patch.object(
                fjordhub._matrix_hub, "_state", return_value={}), patch.object(
                fjordhub._matrix_hub, "begin_install") as begin, patch.dict(
                fjordhub.app.config, {"FJORDHUB_TRANSPORT_POLICY": TransportPolicy.from_config()}):
            client = fjordhub.app.test_client()
            with client.session_transaction() as session:
                session["_user_id"] = auth.get_by_id(user_id).get_id()
                session["_fresh"] = True
                session["hub_csrf"] = "valid-matrix-csrf"
            headers = {"X-CSRF-Token": "valid-matrix-csrf"}
            assert client.post("/api/matrix/install", json={}, headers=headers).status_code == 400
            assert client.post("/api/matrix/install", json={}, headers={
                **headers, "Origin": "https://other.example.dk"
            }, base_url="https://hub.example.dk").status_code == 400
            begin.assert_not_called()


def test_matrix_proxy_forwards_only_matrix_headers_and_needs_ready_host():
    import app as fjordhub
    from types import SimpleNamespace
    body = b'{"versions":["v1.16"]}'
    state = {"phase": "ready", "domain": "hub.example.dk"}
    fake = SimpleNamespace(status_code=200, headers={
        "Content-Type": "application/json", "Content-Length": str(len(body)),
        "Access-Control-Allow-Origin": "*", "Set-Cookie": "should-not-forward"
    }, raw=SimpleNamespace(stream=lambda *a, **k: iter((body,))),
       close=lambda: None)
    with patch.object(fjordhub._matrix_hub, "_state", return_value=state), patch(
            "services.matrix_routes.requests.request", return_value=fake) as upstream:
        client = fjordhub.app.test_client()
        response = client.get("/_matrix/client/versions", base_url="https://hub.example.dk",
                              headers={"Authorization": "Bearer matrix-token",
                                       "Cookie": "session-is-not-forwarded"})
        assert response.status_code == 200
        assert response.json["versions"] == ["v1.16"]
        assert "Set-Cookie" not in response.headers
        args, kwargs = upstream.call_args
        assert args[1] == "http://fjordhub-matrix:8008/_matrix/client/versions"
        assert kwargs["headers"]["Authorization"] == "Bearer matrix-token"
        assert "Cookie" not in kwargs["headers"]
        assert client.get("/_matrix/client/versions", base_url="https://other.example.dk").status_code == 404
        assert upstream.call_count == 1
        well_known = client.get("/.well-known/matrix/client",
                                base_url="https://hub.example.dk")
        assert well_known.json == {"m.homeserver": {"base_url": "https://hub.example.dk"}}


def test_matrix_proxy_login_upload_uses_single_content_length():
    """Synapse rejects requests mixing Content-Length and Transfer-Encoding.

    Prepare the actual outbound request inside the mocked upstream call, while
    the bounded spool is still open, so this catches regressions in body encoding.
    """
    import app as fjordhub
    import requests
    from types import SimpleNamespace

    payload = b'{"type":"m.login.password","identifier":{"type":"m.id.user","user":"qlerup"},"password":"test-only"}'
    captured = {}

    def fake_upstream(method, url, **kwargs):
        prepared = requests.Request(method, url, headers=kwargs["headers"], data=kwargs["data"]).prepare()
        captured["headers"] = dict(prepared.headers)
        captured["body"] = prepared.body.read()
        reply = b'{"errcode":"M_FORBIDDEN","error":"Invalid username or password"}'
        return SimpleNamespace(
            status_code=403,
            headers={"Content-Type": "application/json", "Content-Length": str(len(reply))},
            raw=SimpleNamespace(stream=lambda *args, **kw: iter([reply])),
            close=lambda: None,
        )

    with patch.object(fjordhub._matrix_hub, "_state", return_value={
        "phase": "ready", "domain": "hub.example.dk"
    }), patch("services.matrix_routes.requests.request", side_effect=fake_upstream):
        client = fjordhub.app.test_client()
        result = client.post("/_matrix/client/v3/login", base_url="https://hub.example.dk",
                             data=payload, content_type="application/json")
        assert result.status_code == 403
        assert result.json["errcode"] == "M_FORBIDDEN"
        assert captured["body"] == payload
        assert captured["headers"]["Content-Length"] == str(len(payload))
        assert "Transfer-Encoding" not in captured["headers"]
