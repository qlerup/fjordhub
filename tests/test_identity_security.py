"""Synthetic regression coverage for app identity and cookie revocation boundaries."""
import sqlite3
from contextlib import closing

import pytest
from flask import Flask, request
from flask_login import LoginManager, current_user, login_required, login_user

from services.auth import AuthService
from services import auth as auth_module
from werkzeug.security import generate_password_hash


@pytest.fixture
def auth(tmp_path):
    return AuthService(tmp_path / "auth.db")


@pytest.mark.parametrize("hub_role", ["admin", "user"])
@pytest.mark.parametrize("lookup", ["username", "email"])
def test_app_cannot_link_existing_identity(auth, hub_role, lookup):
    uid = auth.create_user("owner", "original-password", role=hub_role, email="owner@example.test")
    auth.set_user_app_access(uid, "other-app")
    before = auth.get_by_id(uid)
    with pytest.raises(ValueError, match="appadgang"):
        auth.create_or_grant_app_user(
            "fjordlens", "OWNER" if lookup == "username" else "",
            password="replacement-password", role="admin", first_name="Replacement",
            email="replacement@example.test" if lookup == "username" else "OWNER@example.test",
        )
    after = auth.get_by_id(uid)
    assert after.__dict__ == before.__dict__
    assert auth.get_user_app_role(uid, "fjordlens") is None
    assert auth.get_user_app_role(uid, "other-app") == "user"
    assert auth.check_password("owner", "original-password") is not None


def test_linked_app_changes_only_its_membership(auth):
    uid = auth.create_user("owner", "original-password", role="admin", email="owner@example.test", first_name="Original")
    auth.set_user_app_access(uid, "fjordlens")
    auth.set_user_app_access(uid, "other-app")
    before = auth.get_by_id(uid)
    result = auth.create_or_grant_app_user(
        "fjordlens", "owner", password="replacement-password", password_hash="invalid-unused-hash",
        role="manager", email="replacement@example.test", first_name="Changed", last_name="Changed", language="fr",
    )
    assert auth.get_by_id(uid).__dict__ == before.__dict__
    assert result["email"] == "owner@example.test"
    assert auth.get_user_app_role(uid, "fjordlens") == "manager"
    assert auth.get_user_app_role(uid, "other-app") == "user"
    assert auth.check_password("owner", "original-password") is not None
    auth.remove_user_app_access(uid, "fjordlens")
    with pytest.raises(ValueError, match="appadgang"):
        auth.create_or_grant_app_user("fjordlens", "owner")


def test_conflicting_identity_fields_are_rejected(auth):
    first = auth.create_user("first", "original-password", email="first@example.test")
    second = auth.create_user("second", "original-password", email="second@example.test")
    auth.set_user_app_access(first, "fjordlens")
    with pytest.raises(ValueError, match="forskellige"):
        auth.create_or_grant_app_user("fjordlens", "first", role="admin", email="second@example.test")
    assert auth.get_user_app_role(first, "fjordlens") == "user"
    assert auth.get_user_app_role(second, "fjordlens") is None


def test_app_can_create_new_regular_identity(auth):
    result = auth.create_or_grant_app_user("fjordlens", "new-user", "temporary-password", role="manager", email="new@example.test")
    user = auth.get_by_id(result["id"])
    assert user.role == "user"
    assert user.must_change_password
    assert auth.authenticate_app_user("fjordlens", "new-user", "temporary-password")["role"] == "manager"


@pytest.mark.parametrize("change", ["password", "admin_edit", "app_password", "role"])
def test_security_changes_revoke_existing_cookies(auth, change):
    uid = auth.create_user("owner", "original-password", role="admin")
    auth.set_user_app_access(uid, "fjordlens")
    app = Flask(__name__)
    app.secret_key = "isolated-identity-regression-secret"
    manager = LoginManager(app)
    manager.user_loader(auth.get_by_session_id)

    @app.post("/login")
    def login():
        user = auth.check_password("owner", request.form["password"])
        if user is None:
            return "invalid", 401
        login_user(user)
        return "ok"

    @app.get("/private")
    @login_required
    def private():
        return current_user.username

    clients = [app.test_client(), app.test_client()]
    old_id = auth.get_by_id(uid).get_id()
    for client in clients:
        assert client.post("/login", data={"password": "original-password"}).status_code == 200
        assert client.get("/private").status_code == 200
    if change == "password":
        auth.change_password(uid, "new-password")
    elif change == "admin_edit":
        auth.update_user(uid, username="owner", role="admin", new_password="new-password")
    elif change == "app_password":
        assert auth.change_app_user_password("fjordlens", "owner", "original-password", "new-password")
    else:
        auth.update_user(uid, username="owner", role="user")
    for client in clients:
        assert client.get("/private").status_code == 401
    restarted = AuthService(auth._db_path)
    assert restarted.get_by_session_id(old_id) is None
    assert restarted.get_by_session_id(str(uid)) is None
    assert restarted.get_by_session_id(auth.get_by_id(uid).get_id()).id == uid
    fresh = app.test_client()
    password = "original-password" if change == "role" else "new-password"
    assert fresh.post("/login", data={"password": password}).status_code == 200
    assert fresh.get("/private").status_code == 200


def test_migration_preserves_users_and_session_version(tmp_path):
    path = tmp_path / "legacy.db"
    with closing(sqlite3.connect(path)) as conn:
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT, role TEXT, created_at TEXT)")
        conn.execute("INSERT INTO users VALUES (1, 'legacy', 'not-a-password-hash', 'user', '')")
        conn.commit()
    auth = AuthService(path)
    assert auth.get_by_id(1).get_id() == "1:1"
    auth.change_password(1, "new-password")
    assert AuthService(path).get_by_id(1).get_id() == "1:2"


@pytest.mark.parametrize("session_id", [None, "", "1", "1:0", "1:-1", "1:1:1", "1:9999999999999999999", "9999999999999999999:1"])
def test_invalid_session_ids_fail_closed(auth, session_id):
    assert auth.get_by_session_id(session_id) is None


def test_hash_upgrade_cannot_undo_concurrent_password_reset(auth, monkeypatch):
    uid = auth.create_user("owner", "original-password")
    with closing(auth._conn()) as conn:
        conn.execute("UPDATE users SET password_hash=? WHERE id=?", (generate_password_hash("original-password"), uid))
        conn.commit()
    old_session_id = auth.get_by_id(uid).get_id()
    original_hash = auth_module._hash_password

    def reset_during_rehash(password):
        monkeypatch.setattr(auth_module, "_hash_password", original_hash)
        auth.change_password(uid, "reset-password")
        return original_hash(password)

    monkeypatch.setattr(auth_module, "_hash_password", reset_during_rehash)
    assert auth.check_password("owner", "original-password") is None
    assert auth.get_by_session_id(old_session_id) is None
    assert auth.check_password("owner", "reset-password") is not None
    assert auth.check_password("owner", "original-password") is None
