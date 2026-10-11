"""Control-plane regressions with synthetic HTTP streams and no Docker/network."""
import io
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from services.security_config import load_session_secret, load_updater_token
from updater_service import app as updater


@pytest.mark.parametrize("value", ["dev-secret-change-me", "change-me-in-production", "changeme", "change-me", "   "])
def test_known_session_secrets_are_rejected(monkeypatch, tmp_path, value):
    monkeypatch.setenv("SECRET_KEY", value)
    with pytest.raises(RuntimeError):
        load_session_secret(tmp_path)


def test_session_key_persists_and_keeps_custom_encryption_key(monkeypatch, tmp_path):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with ThreadPoolExecutor(max_workers=8) as workers:
        keys = list(workers.map(lambda _: load_session_secret(tmp_path), range(24)))
    assert len(set(keys)) == 1
    assert len(keys[0]) == 64
    assert load_session_secret(tmp_path) == keys[0]
    monkeypatch.setenv("SECRET_KEY", "existing-installation-key-exactly")
    assert load_session_secret(tmp_path) == "existing-installation-key-exactly"


def test_invalid_persisted_secret_is_not_silently_rotated(monkeypatch, tmp_path):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    security = tmp_path / "security"
    security.mkdir()
    (security / "session_key").write_text("broken", encoding="utf-8")
    with pytest.raises(RuntimeError):
        load_session_secret(tmp_path)
    assert (security / "session_key").read_text() == "broken"


class HttpSocket:
    def __init__(self, request):
        self.request = io.BytesIO(request)
        self.response = bytearray()

    def makefile(self, *_args, **_kwargs):
        return self.request

    def sendall(self, data):
        self.response.extend(data)


def request(method, path, authorization=None):
    headers = f"{method} {path} HTTP/1.0\r\nHost: updater\r\nContent-Length: 2\r\n"
    if authorization is not None:
        headers += f"Authorization: {authorization}\r\n"
    sock = HttpSocket((headers + "\r\n{}").encode())
    updater.Handler(sock, ("127.0.0.1", 1), None)
    head, body = bytes(sock.response).split(b"\r\n\r\n", 1)
    return int(head.split()[1]), json.loads(body)


@pytest.fixture
def controls(monkeypatch, tmp_path):
    monkeypatch.setenv("FJORDHUB_UPDATER_TOKEN_FILE", str(tmp_path / "control" / "token"))
    token = load_updater_token(tmp_path)
    assert load_updater_token(tmp_path / "other-service") == token
    callbacks = {}
    for name, result in {
        "read_state": {"status": "idle"}, "git_info": {"ok": True}, "tail_log": "synthetic-log",
        "run_check": {"ok": True}, "start_update": ({"ok": True}, 202),
        "force_stop_update": ({"ok": True}, 200),
    }.items():
        callbacks[name] = Mock(return_value=result)
        monkeypatch.setattr(updater, name, callbacks[name])
    return token, callbacks


@pytest.mark.parametrize("method,path", [("GET", "/status"), ("POST", "/check"), ("POST", "/start"), ("POST", "/force-stop")])
@pytest.mark.parametrize("authorization", [None, "Bearer wrong", "Basic incorrect"])
def test_updater_denies_before_any_operation(controls, method, path, authorization):
    _, callbacks = controls
    status, body = request(method, path, authorization)
    assert status == 401
    assert body == {"ok": False, "error": "Unauthorized"}
    for callback in callbacks.values():
        callback.assert_not_called()


@pytest.mark.parametrize("method,path,callback,status", [
    ("GET", "/status", "read_state", 200), ("POST", "/check", "run_check", 200),
    ("POST", "/start", "start_update", 202), ("POST", "/force-stop", "force_stop_update", 200),
])
def test_updater_authorized_control(controls, method, path, callback, status):
    token, callbacks = controls
    actual_status, body = request(method, path, "Bearer " + token)
    assert actual_status == status
    assert body["ok"] is True
    callbacks[callback].assert_called_once()


def test_health_is_public_but_discloses_no_state(controls):
    status, body = request("GET", "/health")
    assert status == 200
    assert set(body) == {"ok", "service", "time"}
    for callback in controls[1].values():
        callback.assert_not_called()


def test_compose_separates_control_and_closes_traefik_api():
    config = yaml.safe_load((Path(__file__).parents[1] / "docker-compose.yml").read_text())
    services = config["services"]
    hub, worker, proxy = (services[name] for name in ("fjordhub", "fjordhub-updater", "traefik"))
    assert set(worker["networks"]) == {"fjord-control"}
    assert "fjord-control" in hub["networks"]
    assert "fjord-control" not in proxy["networks"]
    assert not worker.get("ports")
    assert hub["environment"]["FJORDHUB_UPDATER_TOKEN_FILE"] == worker["environment"]["FJORDHUB_UPDATER_TOKEN_FILE"]
    assert "fjordhub-control-secrets:/run/fjordhub-control" in hub["volumes"]
    assert "fjordhub-control-secrets:/run/fjordhub-control" in worker["volumes"]
    assert "--api.insecure=false" in proxy["command"]
    assert "--api.dashboard=false" in proxy["command"]
    assert all(not str(port).endswith(":8080") for port in proxy["ports"])
