"""Real login-route regressions for attacker-controlled return destinations."""
from urllib.parse import quote, urljoin, urlsplit

import pytest

import app as hub
from services.auth import AuthService
from services.install_state import InstallState
from services.redirects import safe_login_next


@pytest.fixture
def login_client(tmp_path, monkeypatch):
    auth = AuthService(tmp_path / "auth.db")
    auth.create_user("redirect-reader", "synthetic-password", role="user")
    monkeypatch.setattr(hub, "_auth", auth)
    monkeypatch.setattr(hub, "_install_state", InstallState(tmp_path))
    return hub.app.test_client()


def submit_login(client, target):
    response = client.post(
        "/login?next=" + quote(target, safe=""),
        data={"username": "redirect-reader", "password": "synthetic-password"},
    )
    assert response.status_code == 302
    with client.session_transaction() as session:
        assert session.get("_user_id"), "Test must reach a successful real login"
    return response


@pytest.mark.parametrize("target", [
    "//attacker.example/landing", "///attacker.example/landing",
    "////attacker.example/landing", "https://attacker.example/landing",
    "http://localhost/profile", "javascript:alert(1)",
    "/\\attacker.example/landing", "\\\\attacker.example/landing",
    "/%2fattacker.example/landing", "/%2F%2fattacker.example/landing",
    "/%5cattacker.example/landing", "/%255cattacker.example/landing",
    "/%252fattacker.example/landing", "/%25252fattacker.example/landing",
    "/\t/attacker.example/landing", "/\n/attacker.example/landing",
    "/%0d%0a/attacker.example/landing", "/%2509/attacker.example/landing",
    " //attacker.example/landing", "/\x00/attacker.example/landing",
    "/\x7f/attacker.example/landing", "/%ff/attacker.example/landing",
])
def test_login_rejects_external_and_ambiguous_destinations(login_client, target):
    response = submit_login(login_client, target)
    assert response.headers["Location"] == "/"
    assert urlsplit(urljoin("http://localhost/login", response.location)).netloc == "localhost"


@pytest.mark.parametrize("target", [
    "/", "/profile", "/apps/demo?view=details&tab=settings", "/profile#password",
    "/apps/demo?return=https%3A%2F%2Fexample.test%2Fdocs",
    "/apps/demo?name=Summer%20photos", "/apps/demo?name=bl%C3%A5",
])
def test_login_preserves_internal_destinations_and_queries(login_client, target):
    assert submit_login(login_client, target).headers["Location"] == target


@pytest.mark.parametrize("target", [None, "", "profile", "/%" + "25" * 10 + "2fexample.test"])
def test_empty_relative_and_excessively_encoded_values_fall_back(target):
    assert safe_login_next(target) == "/"
