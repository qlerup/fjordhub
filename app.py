import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from services.auth import AuthService
from services.docker_manager import DockerManager
from services.registry import AppRegistry
from services.remote_registry import RemoteRegistry
from services.install_state import InstallState
from services.installer import Installer, generate_secret
from services.compose_env import build_compose_env
from services.update_manager import UpdateManager

APP_PORT = int(os.environ.get("APP_PORT", 8080))
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data")).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
AUTH_DB_PATH = DATA_DIR / "hub.db"
AUTH_INSTALL_STATE_KEY = "__fjordhub_auth__"

REGISTRY_URL = os.environ.get(
    "REGISTRY_URL",
    "https://raw.githubusercontent.com/qlerup/fjordhub/main/registry.json",
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

_auth            = AuthService(AUTH_DB_PATH)
_local_registry  = AppRegistry(Path(__file__).parent / "app_registry")
_remote_registry = RemoteRegistry(DATA_DIR, REGISTRY_URL)
_install_state   = InstallState(DATA_DIR)
_installer       = Installer(_install_state)
_update_manager  = UpdateManager(_install_state)
docker_mgr       = DockerManager()

# ── Auth setup ───────────────────────────────────────────────────────────────

login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def _load_user(user_id: str):
    try:
        return _auth.get_by_id(int(user_id))
    except Exception:
        return None


@login_manager.unauthorized_handler
def _unauthorized():
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": "Kræver login."}), 401
    return redirect(url_for("login", next=request.path))


_AUTH_EXEMPT = {"static", "setup", "login", "health", "hub_user_sync"}


def _install_state_exists() -> bool:
    return _install_state.is_initialized(AUTH_INSTALL_STATE_KEY)


def _mark_install_initialized(reason: str = "unknown") -> None:
    _install_state.mark_initialized(
        AUTH_INSTALL_STATE_KEY,
        "fjordhub",
        str(AUTH_DB_PATH),
        reason,
    )


def _ensure_install_state_for_existing_users() -> None:
    try:
        if _auth.users_count() > 0:
            _mark_install_initialized("existing-users")
    except Exception:
        pass


def _setup_locked_response():
    message = "FjordHub er allerede initialiseret, men databasen mangler eller er tom."
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": message, "recovery_required": True}), 503
    return render_template(
        "setup_locked.html",
        app_name="FjordHub",
        db_path=str(AUTH_DB_PATH),
    ), 503


_ensure_install_state_for_existing_users()


@app.before_request
def _auth_gate():
    if request.endpoint in _AUTH_EXEMPT:
        return None
    user_count = _auth.users_count()
    if user_count > 0:
        _ensure_install_state_for_existing_users()
    if user_count == 0 and _install_state_exists():
        return _setup_locked_response()
    if user_count == 0:
        if request.path.startswith("/api/"):
            return jsonify({"ok": False, "error": "Opsætning kræves."}), 503
        return redirect(url_for("setup"))
    if not current_user.is_authenticated:
        if request.path.startswith("/api/"):
            return jsonify({"ok": False, "error": "Kræver login."}), 401
        return redirect(url_for("login", next=request.path))
    return None


def _get_apps() -> list[dict]:
    apps = _remote_registry.get_apps()
    return apps if apps else _local_registry.get_all()


def _get_app(app_id: str) -> dict | None:
    return next((a for a in _get_apps() if a.get("id") == app_id), None)


@app.context_processor
def inject_globals():
    return {"app_name": "FjordHub", "active_page": ""}


# ── Auth routes ──────────────────────────────────────────────────────────────

@app.route("/setup", methods=["GET", "POST"])
def setup():
    if _auth.users_count() > 0:
        _ensure_install_state_for_existing_users()
        return redirect(url_for("login"))
    if _install_state_exists():
        return _setup_locked_response()
    error = ""
    username = ""
    if request.method == "POST":
        username = str(request.form.get("username") or "").strip()
        password = str(request.form.get("password") or "")
        password2 = str(request.form.get("password2") or "")
        if not username or not password:
            error = "Brugernavn og adgangskode er påkrævet."
        elif password != password2:
            error = "Adgangskoderne matcher ikke."
        else:
            try:
                _auth.create_user(username, password, role="admin")
                _mark_install_initialized("first-admin-created")
                return redirect(url_for("login", created="1"))
            except ValueError as exc:
                error = str(exc)
    return render_template("setup.html", error=error, username=username)


@app.route("/login", methods=["GET", "POST"])
def login():
    if _auth.users_count() == 0:
        if _install_state_exists():
            return _setup_locked_response()
        return redirect(url_for("setup"))
    _ensure_install_state_for_existing_users()
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    error = ""
    created = str(request.args.get("created") or "") == "1"
    if request.method == "POST":
        username = str(request.form.get("username") or "").strip()
        password = str(request.form.get("password") or "")
        user = _auth.check_password(username, password)
        if user is None:
            error = "Forkert brugernavn eller adgangskode."
        else:
            login_user(user, remember=True)
            next_url = str(request.args.get("next") or "") or url_for("dashboard")
            if not next_url.startswith("/"):
                next_url = url_for("dashboard")
            return redirect(next_url)
    return render_template("login.html", error=error, created=created)


@app.route("/logout", methods=["POST"])
def logout():
    logout_user()
    return redirect(url_for("login"))


# ── Dashboard ────────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    return render_template(
        "dashboard.html",
        apps=_get_apps(),
        reg_status=_remote_registry.get_status(),
        active_page="apps",
    )


# ── Settings ─────────────────────────────────────────────────────────────────

@app.route("/settings")
def settings():
    if not current_user.is_admin:
        return redirect(url_for("dashboard"))
    return render_template("settings.html", active_page="settings")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    pw_error = ""
    pw_ok = False
    if request.method == "POST":
        current_pw = str(request.form.get("current_password") or "")
        new_pw = str(request.form.get("new_password") or "")
        new_pw2 = str(request.form.get("new_password2") or "")
        user = _auth.check_password(current_user.username, current_pw)
        if user is None:
            pw_error = "Nuværende adgangskode er forkert."
        elif new_pw != new_pw2:
            pw_error = "De nye adgangskoder matcher ikke."
        else:
            try:
                _auth.change_password(current_user.id, new_pw)
                pw_ok = True
            except ValueError as exc:
                pw_error = str(exc)
    return render_template("profile.html", active_page="profile", pw_error=pw_error, pw_ok=pw_ok)


def _installed_hub_apps() -> list[dict]:
    """Return app definitions for apps that were installed via FjordHub (have a hub key)."""
    managed_ids = set(_auth.get_apps_with_keys())
    return [a for a in _get_apps() if a.get("id") in managed_ids]


def _read_app_port(app_id: str) -> str | None:
    install_dir = _install_state.get_install_dir(app_id)
    if not install_dir:
        return None
    env_path = Path(install_dir) / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("APP_PORT="):
            return line[len("APP_PORT="):].strip()
    return None


def _sync_user_to_app(app_id: str, username: str, password: str, role: str) -> bool:
    hub_key = _auth.get_hub_key(app_id)
    app_port = _read_app_port(app_id)
    if not hub_key or not app_port:
        return False
    url = f"http://host.docker.internal:{app_port}/api/hub/users"
    payload = json.dumps({"username": username, "password": password, "role": role, "name": username}).encode()
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Hub-Key", hub_key)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status in (200, 201, 409)
    except Exception:
        return False


def _post_install_provision(app_id: str, username: str, password: str, user_id: int) -> None:
    """Background: retry syncing admin user to newly installed app until container is ready."""
    for _ in range(12):
        time.sleep(5)
        if _sync_user_to_app(app_id, username, password, "admin"):
            try:
                _auth.set_user_app_access(user_id, app_id, "admin")
            except Exception:
                pass
            return


@app.route("/users")
def users():
    if not current_user.is_admin:
        return redirect(url_for("dashboard"))
    msg = "Bruger oprettet." if str(request.args.get("msg") or "") == "1" else ""
    return render_template(
        "users.html",
        active_page="users",
        users=_auth.get_all_users_with_access(),
        admin_count=_auth.admin_count(),
        hub_apps=_installed_hub_apps(),
        msg=msg,
    )


@app.route("/users/create", methods=["POST"])
def create_user():
    if not current_user.is_admin:
        return redirect(url_for("dashboard"))
    username = str(request.form.get("username") or "").strip()
    password = str(request.form.get("password") or "")
    role = str(request.form.get("role") or "user")
    app_ids = request.form.getlist("app_access")
    app_roles = {aid: str(request.form.get(f"app_role_{aid}") or "user") for aid in app_ids}
    try:
        user_id = _auth.create_user(username, password, role=role)
        for aid in app_ids:
            app_role = app_roles.get(aid, "user")
            if app_role not in ("admin", "user"):
                app_role = "user"
            _auth.set_user_app_access(user_id, aid, app_role)
            _sync_user_to_app(aid, username, password, app_role)
        return redirect(url_for("users", msg="1"))
    except ValueError as exc:
        return render_template(
            "users.html",
            active_page="users",
            users=_auth.get_all_users_with_access(),
            admin_count=_auth.admin_count(),
            hub_apps=_installed_hub_apps(),
            modal_error=str(exc),
        )


@app.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id: int):
    if not current_user.is_admin:
        return redirect(url_for("dashboard"))
    if user_id == current_user.id:
        return redirect(url_for("users"))
    target = _auth.get_by_id(user_id)
    if target and target.is_admin and _auth.admin_count() <= 1:
        return redirect(url_for("users"))
    _auth.delete_user(user_id)
    return redirect(url_for("users", msg="1"))


# ── Hub user sync (called by sub-apps when a user is created locally) ────────

@app.route("/api/hub/user-sync", methods=["POST"])
def hub_user_sync():
    data = request.get_json(silent=True) or {}
    app_id = str(data.get("app_id") or "")
    key = request.headers.get("X-Hub-Key") or str(data.get("hub_key") or "")
    if not app_id or not key:
        return jsonify({"ok": False, "error": "app_id og hub_key påkrævet"}), 400
    if not _auth.verify_hub_key(app_id, key):
        return jsonify({"ok": False, "error": "Uautoriseret"}), 401
    username = str(data.get("username") or "").strip()
    role = str(data.get("role") or "user").strip()
    password = str(data.get("password") or "").strip()
    if role not in ("admin", "user"):
        role = "user"
    if not username:
        return jsonify({"ok": False, "error": "username påkrævet"}), 400
    user = _auth.get_by_username(username)
    if user:
        user_id = user.id
    else:
        effective_pw = password if len(password) >= 6 else generate_secret(16)
        user_id = _auth.create_user(username, effective_pw, role="user")
    _auth.set_user_app_access(user_id, app_id, role)
    return jsonify({"ok": True, "user_id": user_id})


# ── App status & control ─────────────────────────────────────────────────────

@app.route("/api/apps-status")
def api_apps_status():
    return jsonify({a["id"]: docker_mgr.get_status(a) for a in _get_apps()})


@app.route("/api/apps-updates")
def api_apps_updates():
    return jsonify(_update_manager.get_all_statuses(_get_apps()))


def _with_compose_dir(app_def: dict, app_id: str) -> dict:
    """Inject compose_dir from install_state for wizard-installed apps."""
    install_dir = _install_state.get_install_dir(app_id)
    if install_dir:
        return {**app_def, "compose_dir": install_dir}
    return app_def


@app.route("/apps/<app_id>/start", methods=["POST"])
def start_app(app_id):
    a = _get_app(app_id)
    if not a:
        return jsonify({"error": "Unknown app"}), 404
    ok, msg = docker_mgr.start(_with_compose_dir(a, app_id))
    return jsonify({"ok": ok, "message": msg})


@app.route("/apps/<app_id>/stop", methods=["POST"])
def stop_app(app_id):
    a = _get_app(app_id)
    if not a:
        return jsonify({"error": "Unknown app"}), 404
    ok, msg = docker_mgr.stop(_with_compose_dir(a, app_id))
    return jsonify({"ok": ok, "message": msg})


@app.route("/apps/<app_id>/update/check", methods=["POST"])
def check_app_update(app_id):
    a = _get_app(app_id)
    if not a:
        return jsonify({"error": "Unknown app"}), 404
    return jsonify(_update_manager.check_now(a))


@app.route("/apps/<app_id>/update/start", methods=["POST"])
def start_app_update(app_id):
    a = _get_app(app_id)
    if not a:
        return jsonify({"error": "Unknown app"}), 404
    payload, status = _update_manager.start_update(a)
    return jsonify(payload), status


@app.route("/apps/<app_id>/uninstall", methods=["POST"])
def uninstall_app(app_id):
    a = _get_app(app_id)
    if not a:
        return jsonify({"error": "Unknown app"}), 404
    install_dir = _install_state.get_install_dir(app_id)
    errors = []

    # 1. docker compose down (stop + remove containers and app images)
    compose_dir = install_dir or str(_with_compose_dir(a, app_id).get("compose_dir", ""))
    if compose_dir and Path(compose_dir).exists():
        try:
            result = subprocess.run(
                ["docker", "compose", "down", "--remove-orphans", "--rmi", "all"],
                cwd=compose_dir,
                env=build_compose_env(),
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                msg = result.stderr.strip() or result.stdout.strip() or "docker compose down failed"
                errors.append(f"compose down: {msg[:400]}")
        except Exception as e:
            errors.append(f"compose down: {e}")

    # 2. Remove app directory
    if install_dir and Path(install_dir).exists():
        try:
            shutil.rmtree(install_dir)
        except Exception as e:
            errors.append(f"rm dir: {e}")

    # 3. Clear install state and hub key
    _install_state.clear(app_id)
    _auth.delete_hub_key(app_id)

    return jsonify({"ok": not errors, "errors": errors})


# ── Install wizard ───────────────────────────────────────────────────────────

@app.route("/apps/<app_id>/wizard")
def install_wizard(app_id):
    a = _get_app(app_id)
    if not a:
        return redirect(url_for("dashboard"))
    # Pre-generate secrets for auto_secret fields so the page loads ready
    pregenerated = {}
    for step in a.get("setup_steps", []):
        for field in step.get("fields", []):
            if field.get("type") == "auto_secret":
                pregenerated[field["key"]] = generate_secret()
    steps = a.get("setup_steps", [])
    return render_template("wizard.html", app=a, pregenerated=pregenerated, steps=steps)


@app.route("/apps/<app_id>/install", methods=["POST"])
def install_app(app_id):
    a = _get_app(app_id)
    if not a:
        return jsonify({"error": "Unknown app"}), 404
    body = request.get_json(silent=True) or {}
    env_values = body.get("env", {})
    if not isinstance(env_values, dict):
        return jsonify({"error": "env must be an object"}), 400
    # Generate hub key and inject so the app can authenticate back to FjordHub
    hub_key = generate_secret(32)
    _auth.save_hub_key(app_id, hub_key)
    env_values["FJORDHUB_API_KEY"] = hub_key
    env_values["FJORDHUB_APP_ID"] = app_id
    env_values["FJORDHUB_URL"] = f"http://host.docker.internal:{APP_PORT}"

    # Post-install: auto-provision the hub admin user in the new app
    on_success = None
    hub_admin = body.get("hub_admin", {}) if isinstance(body.get("hub_admin"), dict) else {}
    hub_admin_user = str(hub_admin.get("username") or "").strip()
    hub_admin_pass = str(hub_admin.get("password") or "").strip()
    if hub_admin_user and hub_admin_pass:
        admin_obj = _auth.get_by_username(hub_admin_user)
        if admin_obj:
            uid = admin_obj.id
            on_success = lambda: _post_install_provision(app_id, hub_admin_user, hub_admin_pass, uid)

    _installer.start_install(a, env_values, on_success=on_success)
    return jsonify({"ok": True, "message": "Installation startet"})


@app.route("/apps/<app_id>/install/status")
def install_status(app_id):
    s = _install_state.get(app_id)
    return jsonify({
        "state":   s.get("state", "idle"),
        "log":     s.get("log", []),
        "error":   s.get("error"),
    })


@app.route("/api/generate-secret")
def api_generate_secret():
    return jsonify({"secret": generate_secret()})


# ── Registry ─────────────────────────────────────────────────────────────────

@app.route("/api/registry/refresh", methods=["POST"])
def api_registry_refresh():
    ok, msg = _remote_registry.refresh()
    return jsonify({"ok": ok, "message": msg, "app_count": len(_remote_registry.get_apps())})


@app.route("/api/registry/status")
def api_registry_status():
    return jsonify(_remote_registry.get_status())


# ── Health ───────────────────────────────────────────────────────────────────

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "docker": docker_mgr.client is not None})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT, debug=False)
