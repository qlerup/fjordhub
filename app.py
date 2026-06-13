import os
import shutil
import subprocess
import time
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
from services.resource_monitor import ResourceMonitor

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
resource_monitor = ResourceMonitor(docker_mgr)

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


_AUTH_EXEMPT = {
    "static",
    "setup",
    "login",
    "health",
    "hub_user_sync",
    "api_hub_app_authenticate",
    "api_hub_app_users",
    "api_hub_app_user",
    "api_hub_sso_verify",
}

_sso_tokens: dict = {}


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


def _apps_with_install_dirs() -> list[dict]:
    return [_with_compose_dir(a, str(a.get("id") or "")) for a in _get_apps()]


@app.route("/resources")
def resources():
    if not current_user.is_admin:
        return redirect(url_for("dashboard"))
    return render_template("resources.html", active_page="resources")


@app.route("/api/resources")
def api_resources():
    if not current_user.is_admin:
        return jsonify({"ok": False, "error": "Kræver admin."}), 403
    return jsonify(resource_monitor.collect(_apps_with_install_dirs()))


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
    """Backward-compatible grant endpoint for older app builds."""
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
    try:
        user = _auth.create_or_grant_app_user(app_id, username, password, role)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True, "user": user, "user_id": user["id"]})


# ── App status & control ─────────────────────────────────────────────────────

def _require_app_key(data: dict) -> tuple[str, tuple | None]:
    app_id = str(data.get("app_id") or "").strip()
    key = request.headers.get("X-Hub-Key") or str(data.get("hub_key") or "")
    if not app_id or not key:
        return "", (jsonify({"ok": False, "error": "app_id og hub_key påkrævet"}), 400)
    if not _auth.verify_hub_key(app_id, key):
        return "", (jsonify({"ok": False, "error": "Uautoriseret"}), 401)
    return app_id, None


@app.route("/api/hub/apps/authenticate", methods=["POST"])
def api_hub_app_authenticate():
    data = request.get_json(silent=True) or {}
    app_id, error_response = _require_app_key(data)
    if error_response:
        return error_response
    username = str(data.get("username") or "").strip()
    password = str(data.get("password") or "")
    if not username or not password:
        return jsonify({"ok": False, "error": "Brugernavn og adgangskode påkrævet"}), 400
    user = _auth.authenticate_app_user(app_id, username, password)
    if not user:
        return jsonify({"ok": False, "error": "Forkert login eller ingen adgang til appen"}), 401
    return jsonify({"ok": True, "user": user})


@app.route("/api/hub/apps/users", methods=["GET", "POST"])
def api_hub_app_users():
    data = request.get_json(silent=True) or {}
    if request.method == "GET":
        data = {"app_id": request.args.get("app_id", "")}
    app_id, error_response = _require_app_key(data)
    if error_response:
        return error_response
    if request.method == "GET":
        return jsonify({"ok": True, "items": _auth.list_app_users(app_id)})
    username = str(data.get("username") or "").strip()
    password = str(data.get("password") or "")
    role = str(data.get("role") or "user").strip()
    try:
        user = _auth.create_or_grant_app_user(app_id, username, password, role)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True, "user": user, "item": user}), 201


@app.route("/api/hub/apps/users/<int:user_id>", methods=["PATCH", "DELETE"])
def api_hub_app_user(user_id: int):
    data = request.get_json(silent=True) or {}
    if request.method == "DELETE" and not data:
        data = {"app_id": request.args.get("app_id", "")}
    app_id, error_response = _require_app_key(data)
    if error_response:
        return error_response
    if request.method == "DELETE":
        _auth.remove_user_app_access(user_id, app_id)
        return jsonify({"ok": True})
    role = str(data.get("role") or "user").strip()
    try:
        user = _auth.update_app_user_role(user_id, app_id, role)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    if not user:
        return jsonify({"ok": False, "error": "Brugeren har ikke adgang til appen"}), 404
    return jsonify({"ok": True, "user": user, "item": user})


@app.route("/api/hub/sso-token")
@login_required
def api_hub_sso_token():
    app_id = request.args.get("app_id", "").strip()
    if not app_id or not _auth.get_hub_key(app_id):
        return jsonify({"ok": False, "error": "App ikke installeret"}), 400
    token = generate_secret(32)
    _sso_tokens[token] = {
        "username": current_user.username,
        "id": current_user.id,
        "role": "admin",
        "app_id": app_id,
        "expires_at": time.time() + 60,
    }
    return jsonify({"ok": True, "token": token})


@app.route("/api/hub/sso-verify")
def api_hub_sso_verify():
    app_id = request.args.get("app_id", "").strip()
    token = request.args.get("token", "").strip()
    hub_key = request.headers.get("X-Hub-Key", "")
    if not app_id or not token or not hub_key:
        return jsonify({"ok": False, "error": "app_id, token og X-Hub-Key påkrævet"}), 400
    if not _auth.verify_hub_key(app_id, hub_key):
        return jsonify({"ok": False, "error": "Uautoriseret"}), 401
    entry = _sso_tokens.pop(token, None)
    if not entry:
        return jsonify({"ok": False, "error": "Ugyldigt token"}), 401
    if entry["app_id"] != app_id:
        return jsonify({"ok": False, "error": "Token tilhører en anden app"}), 401
    if time.time() > entry["expires_at"]:
        return jsonify({"ok": False, "error": "Token er udløbet"}), 401
    return jsonify({"ok": True, "username": entry["username"], "id": entry["id"], "role": entry["role"]})


@app.route("/api/verify-nfs-mount")
@login_required
def api_verify_nfs_mount():
    import subprocess
    path = request.args.get("path", "").strip()
    if not path or not path.startswith("/"):
        return jsonify({"mounted": False, "error": "Ugyldig sti"})
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", f"--volume={path}:/d", "alpine",
             "sh", "-c", "awk '$2==\"/d\"{print $3; exit}' /proc/mounts"],
            capture_output=True, text=True, timeout=15,
        )
        fstype = result.stdout.strip()
        if fstype in ("nfs", "nfs4", "nfs3"):
            return jsonify({"mounted": True, "fstype": fstype})
        elif fstype:
            return jsonify({"mounted": False, "fstype": fstype, "error": f"Filsystem er '{fstype}', ikke NFS"})
        else:
            return jsonify({"mounted": False, "error": "Ingen NFS mount ved stien"})
    except subprocess.TimeoutExpired:
        return jsonify({"mounted": False, "error": "Timeout"})
    except Exception as e:
        return jsonify({"mounted": False, "error": str(e)})


@app.route("/api/list-nfs-exports")
@login_required
def api_list_nfs_exports():
    import socket, subprocess
    host = request.args.get("host", "").strip()
    if not host:
        return jsonify({"exports": [], "error": "host mangler"})
    try:
        sock = socket.create_connection((host, 2049), timeout=4)
        sock.close()
    except OSError as e:
        return jsonify({"exports": [], "error": f"Port 2049 ikke tilgængelig: {e}"})
    try:
        result = subprocess.run(
            ["showmount", "-e", "--no-headers", host],
            capture_output=True, text=True, timeout=8
        )
        if result.returncode == 0:
            exports = [line.split()[0].rstrip("/") for line in result.stdout.strip().splitlines() if line.strip()]
            return jsonify({"exports": exports})
        return jsonify({"exports": [], "error": result.stderr.strip()})
    except FileNotFoundError:
        return jsonify({"exports": [], "error": "showmount ikke installeret"})
    except subprocess.TimeoutExpired:
        return jsonify({"exports": [], "error": "timeout"})


@app.route("/api/check-nfs")
@login_required
def api_check_nfs():
    import socket
    import subprocess
    nfs_export = request.args.get("export", "").strip()
    if not nfs_export or ":" not in nfs_export:
        return jsonify({"ok": False, "error": "Ugyldig NFS export (format: server:/sti)"}), 400
    host, path = nfs_export.split(":", 1)
    host = host.strip()
    path = path.rstrip("/").strip()
    try:
        sock = socket.create_connection((host, 2049), timeout=4)
        sock.close()
    except OSError as e:
        return jsonify({"ok": False, "error": f"Port 2049 ikke tilgængelig på {host}: {e}"})
    try:
        result = subprocess.run(
            ["showmount", "-e", "--no-headers", host],
            capture_output=True, text=True, timeout=8
        )
        if result.returncode == 0:
            exports = [line.split()[0].rstrip("/") for line in result.stdout.strip().splitlines() if line.strip()]
            if path and path not in exports:
                return jsonify({"ok": False, "error": f"Stien '{path}' er ikke eksporteret af {host}. Tilgængelige: {', '.join(exports) or 'ingen'}"})
    except FileNotFoundError:
        pass  # showmount ikke installeret, TCP-tjek var OK
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "error": f"showmount timeout mod {host}"})
    return jsonify({"ok": True})


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

    installer_user_id = int(current_user.id)
    on_success = lambda: _auth.set_user_app_access(installer_user_id, app_id, "admin")

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
