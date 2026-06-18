import os
import copy
import shutil
import subprocess
import time
import warnings
import threading
from pathlib import Path
import requests
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from services.auth import AuthService
from services.docker_manager import DockerManager
from services.registry import AppRegistry
from services.remote_registry import RemoteRegistry
from services.install_state import InstallState
from services.installer import Installer, generate_secret, APPS_BASE
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

FJORDHUB_SRC_DIR = os.environ.get("FJORDHUB_SRC_DIR", "")
FJORDHUB_UPDATER_URL = str(os.environ.get("FJORDHUB_UPDATER_URL", "") or "").strip().rstrip("/")
FJORDHUB_IMAGE = str(os.environ.get("FJORDHUB_IMAGE", "fjordhub-fjordhub:latest") or "").strip() or "fjordhub-fjordhub:latest"
_FJORDHUB_APP_DEF = {"id": "fjordhub", "name": "FjordHub"}
LANGUAGE_OPTIONS = [
    {"value": "da", "label": "Dansk"},
    {"value": "en", "label": "English"},
    {"value": "fr", "label": "Français"},
]
LANGUAGE_VALUES = {entry["value"] for entry in LANGUAGE_OPTIONS}


def _normalize_language(value: str) -> str:
    lang = str(value or "da").strip().lower()
    return lang if lang in LANGUAGE_VALUES else "da"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config.update(
    SESSION_COOKIE_NAME=os.environ.get("SESSION_COOKIE_NAME", "fjordhub_session"),
)

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

if FJORDHUB_SRC_DIR:
    _install_state.register("fjordhub", FJORDHUB_SRC_DIR)


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


def _with_nfs_recommendations(app_def: dict) -> dict:
    app_copy = copy.deepcopy(app_def)
    for step in app_copy.get("setup_steps", []):
        for field in step.get("fields", []):
            if field.get("type") != "path":
                continue
            key = str(field.get("key", "")).upper()
            label = str(field.get("label", "")).upper()
            if "UPLOAD" not in key and "UPLOAD" not in label:
                continue
            field["nfs_recommended"] = True
    return app_copy


def _get_apps() -> list[dict]:
    apps = _remote_registry.get_apps()
    apps = apps if apps else _local_registry.get_all()
    return [_with_nfs_recommendations(a) for a in apps]


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
    first_name = ""
    last_name = ""
    language = "da"
    if request.method == "POST":
        username = str(request.form.get("username") or "").strip()
        first_name = str(request.form.get("first_name") or "").strip()
        last_name = str(request.form.get("last_name") or "").strip()
        language = _normalize_language(request.form.get("language"))
        password = str(request.form.get("password") or "")
        password2 = str(request.form.get("password2") or "")
        if not username or not password:
            error = "Brugernavn og adgangskode er påkrævet."
        elif password != password2:
            error = "Adgangskoderne matcher ikke."
        else:
            try:
                _auth.create_user(
                    username,
                    password,
                    role="admin",
                    first_name=first_name,
                    last_name=last_name,
                    language=language,
                )
                _mark_install_initialized("first-admin-created")
                return redirect(url_for("login", created="1"))
            except ValueError as exc:
                error = str(exc)
    return render_template(
        "setup.html",
        error=error,
        username=username,
        first_name=first_name,
        last_name=last_name,
        language=language,
        language_options=LANGUAGE_OPTIONS,
    )


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
    all_apps = _get_apps()
    if not current_user.is_admin:
        user_app_ids = {a["app_id"] for a in _auth.get_user_app_access(current_user.id)}
        all_apps = [a for a in all_apps if a.get("id") in user_app_ids]
    return render_template(
        "dashboard.html",
        apps=all_apps,
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


DOCKER_CLEANUP_COMMANDS = (
    ("Docker diskforbrug foer oprydning", ["docker", "system", "df"], 60),
    ("Rydder Docker build-cache", ["docker", "builder", "prune", "-af"], 600),
    ("Rydder ubrugte images", ["docker", "image", "prune", "-af"], 600),
    ("Rydder stoppede containere", ["docker", "container", "prune", "-f"], 300),
    ("Rydder ubrugte networks", ["docker", "network", "prune", "-f"], 300),
    ("Docker diskforbrug efter oprydning", ["docker", "system", "df"], 60),
)


def _append_command_output(log: list[str], output: str, max_lines: int = 180) -> None:
    lines = [line.rstrip() for line in str(output or "").splitlines() if line.rstrip()]
    if not lines:
        log.append("(ingen output)")
        return
    if len(lines) > max_lines:
        hidden = len(lines) - max_lines
        log.append(f"... {hidden} linjer skjult ...")
        lines = lines[-max_lines:]
    log.extend(lines)


@app.route("/api/docker-cleanup", methods=["POST"])
@login_required
def api_docker_cleanup():
    if not current_user.is_admin:
        return jsonify({"ok": False, "error": "Kraever admin."}), 403

    log: list[str] = [
        "Starter Docker oprydning.",
        "Bevarer Docker volumes og monterede data-mapper.",
    ]
    ok = True
    for label, command, timeout in DOCKER_CLEANUP_COMMANDS:
        log.extend(["", f"=== {label} ===", "$ " + " ".join(command)])
        try:
            result = subprocess.run(
                command,
                env=build_compose_env(),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError:
            return jsonify(
                {
                    "ok": False,
                    "message": "Docker blev ikke fundet.",
                    "log": [*log, "Fejl: docker blev ikke fundet i PATH."],
                }
            ), 500
        except subprocess.TimeoutExpired:
            ok = False
            log.append(f"Fejl: kommandoen timeoutede efter {timeout}s.")
            continue
        except Exception as exc:
            ok = False
            log.append(f"Fejl: {exc}")
            continue

        output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
        _append_command_output(log, output)
        if result.returncode != 0:
            ok = False
            log.append(f"Fejl: returncode {result.returncode}")

    log.extend(["", "Oprydning faerdig." if ok else "Oprydning sluttede med fejl."])
    message = "Docker oprydning faerdig." if ok else "Docker oprydning sluttede med fejl."
    return jsonify({"ok": ok, "message": message, "log": log[-600:]}), 200 if ok else 500


# ── Settings ─────────────────────────────────────────────────────────────────

@app.route("/settings")
def settings():
    if not current_user.is_admin:
        return redirect(url_for("dashboard"))
    section = request.args.get("section", "general")
    return render_template(
        "settings.html",
        active_page="settings",
        section=section,
        hub_src_configured=bool(FJORDHUB_SRC_DIR or FJORDHUB_UPDATER_URL),
    )


def _hub_update_label(state: str, update_available: bool = False) -> str:
    if state == "updating":
        return "Opdaterer..."
    if state == "restarting":
        return "Genstarter..."
    if state == "failed":
        return "Opdatering fejlede"
    if state == "error":
        return "Kunne ikke tjekke"
    if state == "update_available" or update_available:
        return "Ny opdatering klar"
    if state == "up_to_date":
        return "Ingen opdatering"
    return "Klar"


def _normalize_hub_update_payload(data: dict) -> dict:
    data = dict(data or {})
    git = data.get("git") if isinstance(data.get("git"), dict) else {}
    status = str(data.get("status") or "").strip().lower()
    running = bool(data.get("running") or status in {"running", "stopping"})
    update_available = bool(git.get("update_available", data.get("update_available", False)))

    if running:
        state = "updating"
    elif status == "failed":
        state = "failed"
    elif status == "success":
        state = "update_available" if update_available else "up_to_date"
    elif git.get("fetch_error") or (git and not git.get("ok", True)):
        state = "error"
    elif data.get("error") and not data.get("ok", True):
        state = "error"
    elif update_available:
        state = "update_available"
    elif git:
        state = "up_to_date"
    else:
        state = str(data.get("state") or "error")

    normalized = dict(data)
    for key in (
        "available",
        "branch",
        "current_rev",
        "current_short",
        "remote_rev",
        "remote_short",
        "dirty",
        "dirty_lines",
        "fetch_error",
    ):
        if key in git:
            normalized[key] = git.get(key)

    error_raw = str(data.get("error") or git.get("fetch_error") or git.get("error") or "")
    has_active_error = state in {"error", "failed"} or (not bool(data.get("ok", True)) and bool(error_raw))
    error = error_raw if has_active_error else ""
    normalized.update(
        {
            "state": state,
            "available": bool(git.get("available", normalized.get("available", True))),
            "running": running,
            "ok": bool(data.get("ok", git.get("ok", state not in {"error", "failed"}))),
            "update_available": update_available and not running,
            "error": error,
            "label": _hub_update_label(state, update_available),
        }
    )
    return normalized


def _hub_update_proxy(path: str, method: str = "GET", payload: dict | None = None, timeout: int = 10) -> tuple[dict, int]:
    if not FJORDHUB_UPDATER_URL:
        return {"ok": False, "available": False, "error": "FjordHub updater-service er ikke konfigureret."}, 503

    url = f"{FJORDHUB_UPDATER_URL}/{str(path or '').strip('/')}"
    try:
        if method.upper() == "POST":
            response = requests.post(url, json=payload or {}, timeout=timeout)
        else:
            response = requests.get(url, timeout=timeout)
        try:
            data = response.json()
        except Exception:
            data = {"ok": False, "error": response.text[:500] or "Updater-service svarede ikke med JSON."}
        if isinstance(data, dict):
            data.setdefault("service_reachable", True)
            data.setdefault("updater_url", FJORDHUB_UPDATER_URL)
        return _normalize_hub_update_payload(data), response.status_code
    except Exception as error:
        return _normalize_hub_update_payload(
            {
                "ok": False,
                "available": False,
                "service_reachable": False,
                "updater_url": FJORDHUB_UPDATER_URL,
                "error": "FjordHub updater-service er ikke tilgaengelig.",
                "detail": str(error),
            }
        ), 503


@app.route("/api/hub/self/update/status")
@login_required
def api_hub_self_update_status():
    if not current_user.is_admin:
        return jsonify({"ok": False, "error": "Kræver admin."}), 403
    if FJORDHUB_UPDATER_URL:
        payload, code = _hub_update_proxy("/status", method="GET", timeout=5)
        return jsonify(payload), code
    status = _update_manager.get_status(_FJORDHUB_APP_DEF)
    status["log"] = _update_manager.get_log("fjordhub")
    return jsonify(status)


@app.route("/api/hub/self/update/check", methods=["POST"])
@login_required
def api_hub_self_update_check():
    if not current_user.is_admin:
        return jsonify({"ok": False, "error": "Kræver admin."}), 403
    if FJORDHUB_UPDATER_URL:
        payload, code = _hub_update_proxy("/check", method="POST", payload={}, timeout=90)
        return jsonify(payload), code
    status = _update_manager.check_now(_FJORDHUB_APP_DEF)
    status["log"] = _update_manager.get_log("fjordhub")
    return jsonify(status)


@app.route("/api/hub/self/update/start", methods=["POST"])
@login_required
def api_hub_self_update_start():
    if not current_user.is_admin:
        return jsonify({"ok": False, "error": "Kræver admin."}), 403
    if FJORDHUB_UPDATER_URL:
        body = request.get_json(silent=True) or {}
        payload, code = _hub_update_proxy(
            "/start",
            method="POST",
            payload={"cleanup": bool(body.get("cleanup", False))},
            timeout=10,
        )
        return jsonify(payload), code
    payload, code = _update_manager.start_update(_FJORDHUB_APP_DEF)
    return jsonify(payload), code


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
    return render_template(
        "profile.html",
        active_page="profile",
        pw_error=pw_error,
        pw_ok=pw_ok,
        info_ok=str(request.args.get("info") or "") == "1",
        profile_user=_auth.get_by_id(current_user.id) or current_user,
        language_options=LANGUAGE_OPTIONS,
    )


@app.route("/profile/info", methods=["POST"])
def profile_info():
    _auth.update_user_profile(
        current_user.id,
        first_name=str(request.form.get("first_name") or "").strip(),
        last_name=str(request.form.get("last_name") or "").strip(),
        language=_normalize_language(request.form.get("language")),
    )
    return redirect(url_for("profile", info="1"))


def _installed_hub_apps() -> list[dict]:
    """Return app definitions for apps that were installed via FjordHub (have a hub key)."""
    managed_ids = set(_auth.get_apps_with_keys())
    return [a for a in _get_apps() if a.get("id") in managed_ids]


@app.route("/users")
def users():
    if not current_user.is_admin:
        return redirect(url_for("dashboard"))
    _msg_map = {"1": "Bruger oprettet.", "2": "Bruger opdateret."}
    msg = _msg_map.get(str(request.args.get("msg") or ""), "")
    return render_template(
        "users.html",
        active_page="users",
        users=_auth.get_all_users_with_access(),
        admin_count=_auth.admin_count(),
        hub_apps=_installed_hub_apps(),
        language_options=LANGUAGE_OPTIONS,
        msg=msg,
    )


@app.route("/users/create", methods=["POST"])
def create_user():
    if not current_user.is_admin:
        return redirect(url_for("dashboard"))
    username = str(request.form.get("username") or "").strip()
    first_name = str(request.form.get("first_name") or "").strip()
    last_name = str(request.form.get("last_name") or "").strip()
    language = _normalize_language(request.form.get("language"))
    password = str(request.form.get("password") or "")
    role = str(request.form.get("role") or "user")
    app_ids = request.form.getlist("app_access")
    app_roles = {aid: str(request.form.get(f"app_role_{aid}") or "user") for aid in app_ids}
    try:
        user_id = _auth.create_user(
            username,
            password,
            role=role,
            first_name=first_name,
            last_name=last_name,
            language=language,
        )
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
            language_options=LANGUAGE_OPTIONS,
            modal_error=str(exc),
        )


@app.route("/users/<int:user_id>/edit", methods=["POST"])
def edit_user(user_id: int):
    if not current_user.is_admin:
        return redirect(url_for("dashboard"))
    target = _auth.get_by_id(user_id)
    if not target:
        return redirect(url_for("users"))
    username = str(request.form.get("username") or "").strip()
    first_name = str(request.form.get("first_name") or "").strip()
    last_name = str(request.form.get("last_name") or "").strip()
    language = _normalize_language(request.form.get("language"))
    role = str(request.form.get("role") or "user")
    current_password = str(request.form.get("current_password") or "")
    new_password = str(request.form.get("new_password") or "")
    new_password2 = str(request.form.get("new_password2") or "")
    app_ids = request.form.getlist("app_access")
    app_roles = {aid: str(request.form.get(f"app_role_{aid}") or "user") for aid in app_ids}
    if target.is_admin and role != "admin" and _auth.admin_count() <= 1:
        return render_template(
            "users.html",
            active_page="users",
            users=_auth.get_all_users_with_access(),
            admin_count=_auth.admin_count(),
            hub_apps=_installed_hub_apps(),
            language_options=LANGUAGE_OPTIONS,
            edit_error="Kan ikke ændre rolle for den eneste admin.",
            edit_user_id=user_id,
        )
    password_fields_filled = bool(current_password or new_password or new_password2)
    if password_fields_filled:
        if not (current_password and new_password and new_password2):
            return render_template(
                "users.html",
                active_page="users",
                users=_auth.get_all_users_with_access(),
                admin_count=_auth.admin_count(),
                hub_apps=_installed_hub_apps(),
                language_options=LANGUAGE_OPTIONS,
                edit_error="For at ændre adgangskode skal du udfylde nuværende, ny og gentag ny adgangskode.",
                edit_user_id=user_id,
            )
        if new_password != new_password2:
            return render_template(
                "users.html",
                active_page="users",
                users=_auth.get_all_users_with_access(),
                admin_count=_auth.admin_count(),
                hub_apps=_installed_hub_apps(),
                language_options=LANGUAGE_OPTIONS,
                edit_error="Ny adgangskode og gentag ny adgangskode matcher ikke.",
                edit_user_id=user_id,
            )
        if _auth.check_password(target.username, current_password) is None:
            return render_template(
                "users.html",
                active_page="users",
                users=_auth.get_all_users_with_access(),
                admin_count=_auth.admin_count(),
                hub_apps=_installed_hub_apps(),
                language_options=LANGUAGE_OPTIONS,
                edit_error="Nuværende adgangskode er forkert.",
                edit_user_id=user_id,
            )
    try:
        _auth.update_user(
            user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language=language,
            role=role,
            new_password=new_password if password_fields_filled else "",
        )
        existing_ids = {a["app_id"] for a in _auth.get_user_app_access(user_id)}
        new_ids = set(app_ids)
        for aid in existing_ids - new_ids:
            _auth.remove_user_app_access(user_id, aid)
        for aid in app_ids:
            app_role = app_roles.get(aid, "user")
            if app_role not in ("admin", "user"):
                app_role = "user"
            _auth.set_user_app_access(user_id, aid, app_role)
        return redirect(url_for("users", msg="2"))
    except ValueError as exc:
        return render_template(
            "users.html",
            active_page="users",
            users=_auth.get_all_users_with_access(),
            admin_count=_auth.admin_count(),
            hub_apps=_installed_hub_apps(),
            language_options=LANGUAGE_OPTIONS,
            edit_error=str(exc),
            edit_user_id=user_id,
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
    first_name = str(data.get("first_name") or "").strip()
    last_name = str(data.get("last_name") or "").strip()
    language = _normalize_language(data.get("language")) if "language" in data else ""
    if role not in ("admin", "user"):
        role = "user"
    if not username:
        return jsonify({"ok": False, "error": "username påkrævet"}), 400
    try:
        user = _auth.create_or_grant_app_user(
            app_id,
            username,
            password,
            role,
            first_name=first_name,
            last_name=last_name,
            language=language,
        )
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
    first_name = str(data.get("first_name") or "").strip()
    last_name = str(data.get("last_name") or "").strip()
    language = _normalize_language(data.get("language")) if "language" in data else ""
    try:
        user = _auth.create_or_grant_app_user(
            app_id,
            username,
            password,
            role,
            first_name=first_name,
            last_name=last_name,
            language=language,
        )
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
    token, error_response = _create_app_sso_token(app_id)
    if error_response:
        return error_response
    return jsonify({"ok": True, "token": token})


def _create_app_sso_token(app_id: str) -> tuple[str, object | None]:
    app_id = str(app_id or "").strip()
    if not app_id:
        return "", (jsonify({"ok": False, "error": "App mangler"}), 400)
    if not _auth.get_hub_key(app_id):
        return "", (jsonify({"ok": False, "error": "Appen mangler FjordHub-integration. Opdater eller geninstaller appen via FjordHub."}), 400)
    user = _auth.get_by_id(int(current_user.id)) or current_user
    app_role = _auth.get_user_app_role(int(current_user.id), app_id)
    hub_role = "admin" if user.is_admin else "user"
    role = app_role or ("admin" if user.is_admin else "user")
    token = generate_secret(32)
    _sso_tokens[token] = {
        "username": user.username,
        "id": user.id,
        "first_name": getattr(user, "first_name", ""),
        "last_name": getattr(user, "last_name", ""),
        "language": _normalize_language(getattr(user, "language", "da")),
        "role": role,
        "hub_role": hub_role,
        "app_id": app_id,
        "expires_at": time.time() + 60,
    }
    return token, None


def _external_app_url_candidates(app_def: dict) -> list[str]:
    host = request.host.split(":", 1)[0]
    port = int(app_def.get("default_port") or 80)
    return [f"https://{host}:{port}", f"http://{host}:{port}"]


def _app_url_is_reachable(app_url: str, app_def: dict) -> bool:
    health_path = str(app_def.get("health_path") or "/api/health").strip() or "/api/health"
    if not health_path.startswith("/"):
        health_path = f"/{health_path}"
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            resp = requests.get(
                f"{app_url.rstrip('/')}{health_path}",
                timeout=0.8,
                verify=False,
            )
        return 200 <= int(resp.status_code) < 500
    except requests.RequestException:
        return False


def _external_app_url(app_def: dict) -> str:
    candidates = _external_app_url_candidates(app_def)
    for candidate in candidates:
        if _app_url_is_reachable(candidate, app_def):
            return candidate
    return candidates[1]


@app.route("/apps/<app_id>/sso-url")
@login_required
def app_sso_url(app_id):
    app_def = _get_app(app_id)
    if not app_def:
        return jsonify({"ok": False, "error": "Ukendt app"}), 404
    token, error_response = _create_app_sso_token(app_id)
    if error_response:
        return error_response
    app_url = _external_app_url(app_def)
    return jsonify({"ok": True, "url": f"{app_url}/hub-login?token={token}"})


@app.route("/api/apps/<app_id>/link-hub", methods=["POST"])
@login_required
def api_link_hub(app_id):
    if not current_user.is_admin:
        return jsonify({"ok": False, "error": "Kun administratorer kan linke hub-integration"}), 403
    app_def = _get_app(app_id)
    if not app_def:
        return jsonify({"ok": False, "error": "Ukendt app"}), 404
    install_dir = APPS_BASE / app_id
    env_path = install_dir / ".env"
    if not env_path.exists():
        return jsonify({"ok": False, "error": "Appen er ikke installeret via FjordHub"}), 400
    hub_key = generate_secret(32)
    _auth.save_hub_key(app_id, hub_key)
    try:
        content = env_path.read_text(encoding="utf-8")
        lines = [l for l in content.splitlines()
                 if not l.startswith(("FJORDHUB_API_KEY=", "FJORDHUB_APP_ID=", "FJORDHUB_URL="))]
        lines += [
            f"FJORDHUB_API_KEY={hub_key}",
            f"FJORDHUB_APP_ID={app_id}",
            f"FJORDHUB_URL=http://host.docker.internal:{APP_PORT}",
        ]
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception as e:
        return jsonify({"ok": False, "error": f"Kunne ikke opdatere .env: {e}"}), 500
    try:
        result = subprocess.run(
            ["docker", "compose", "up", "-d", "--force-recreate"],
            cwd=str(install_dir),
            env=build_compose_env(),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            return jsonify({"ok": False, "error": f"compose up fejlede: {result.stderr[:400]}"}), 500
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "error": "Timeout ved genstart"}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True, "message": "FjordHub-integration aktiveret — appen genstarter nu."})


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
    return jsonify({
        "ok": True,
        "username": entry["username"],
        "id": entry["id"],
        "first_name": entry.get("first_name", ""),
        "last_name": entry.get("last_name", ""),
        "language": _normalize_language(entry.get("language")),
        "role": entry["role"],
        "hub_role": entry.get("hub_role", entry["role"]),
    })


def _nfs_runtime_info() -> dict:
    kernel_text = ""
    try:
        kernel_text = (
            Path("/proc/sys/kernel/osrelease").read_text(errors="ignore")
            + "\n"
            + Path("/proc/version").read_text(errors="ignore")
        ).lower()
    except Exception:
        pass
    is_wsl2 = any(marker in kernel_text for marker in ("microsoft", "wsl", "docker-desktop", "moby"))
    try:
        uid_map = Path("/proc/self/uid_map").read_text().strip()
        parts = uid_map.split()
        privileged = len(parts) >= 3 and parts[1] == "0"
    except Exception:
        privileged = None
    vmid = os.environ.get("PROXMOX_VMID", "").strip() or None
    return {
        "privileged": privileged,
        "vmid": vmid,
        "runtime": "docker_desktop" if is_wsl2 else "linux",
        "wsl2": is_wsl2,
        "auto_mount_supported": bool(privileged is True and not is_wsl2),
    }


@app.route("/api/lxc-type")
@login_required
def api_lxc_type():
    return jsonify(_nfs_runtime_info())


@app.route("/api/gpu-preflight", methods=["POST"])
@login_required
def api_gpu_preflight():
    command = [
        "docker", "run", "--rm", "--gpus", "all",
        "nvidia/cuda:12.4.1-base-ubuntu22.04",
        "nvidia-smi",
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "error": "GPU-test timeout", "command": " ".join(command)}), 504
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc), "command": " ".join(command)}), 500

    output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    return jsonify(
        {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "command": " ".join(command),
            "output": output[-4000:],
            "error": "" if result.returncode == 0 else (output[-1200:] or "GPU-test fejlede"),
        }
    )


def _detect_nvidia_driver_major() -> str:
    import re

    # Preferred: kernel driver version file exposed through NVIDIA device mounts.
    try:
        text = Path("/proc/driver/nvidia/version").read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"(\d+)\.\d+\.\d+", text)
        if match:
            return match.group(1)
    except Exception:
        pass

    # Fallback: query via nvidia-smi if available.
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode == 0:
            line = (result.stdout or "").strip().splitlines()[0]
            major = line.split(".", 1)[0].strip()
            if major.isdigit():
                return major
    except Exception:
        pass

    return ""


_gpu_setup_lock = threading.Lock()
_gpu_setup_state = {
    "running": False,
    "ok": None,
    "error": "",
    "nvidia_major": "",
    "logs": [],
    "started_at": 0.0,
    "finished_at": 0.0,
}


def _gpu_setup_reset_state() -> None:
    with _gpu_setup_lock:
        _gpu_setup_state.update(
            {
                "running": True,
                "ok": None,
                "error": "",
                "nvidia_major": "",
                "logs": [],
                "started_at": time.time(),
                "finished_at": 0.0,
            }
        )


def _gpu_setup_append(line: str) -> None:
    with _gpu_setup_lock:
        logs = _gpu_setup_state.setdefault("logs", [])
        logs.append(str(line))
        if len(logs) > 400:
            del logs[:-400]


def _gpu_setup_snapshot() -> dict:
    with _gpu_setup_lock:
        state = dict(_gpu_setup_state)
        state["logs"] = list(_gpu_setup_state.get("logs") or [])
    state["output"] = "\n\n".join(state.get("logs") or [])[-12000:]
    return state


def _gpu_setup_finish(ok: bool, error: str = "", nvidia_major: str = "") -> None:
    with _gpu_setup_lock:
        _gpu_setup_state["running"] = False
        _gpu_setup_state["ok"] = bool(ok)
        _gpu_setup_state["error"] = str(error or "")
        _gpu_setup_state["nvidia_major"] = str(nvidia_major or "")
        _gpu_setup_state["finished_at"] = time.time()


def _gpu_setup_run_step(cmd: str, timeout: int = 600) -> bool:
    _gpu_setup_append(f"$ {cmd}")
    try:
        result = subprocess.run(
            ["sh", "-lc", cmd],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        _gpu_setup_append("[timeout]")
        return False
    except Exception as exc:
        _gpu_setup_append(str(exc))
        return False

    out = "\n".join(part for part in ((result.stdout or "").strip(), (result.stderr or "").strip()) if part).strip()
    if out:
        _gpu_setup_append(out[-4000:])
    return result.returncode == 0


def _gpu_setup_worker() -> None:
    major = ""
    try:
        if _nfs_runtime_info().get("runtime") == "docker_desktop":
            _gpu_setup_finish(False, "Automatisk GPU-opsætning understøttes ikke på Docker Desktop/WSL2.")
            return

        if os.geteuid() != 0:
            _gpu_setup_finish(False, "FjordHub-processen skal køre som root for at kunne installere pakker.")
            return

        steps = [
            "export DEBIAN_FRONTEND=noninteractive; apt-get update",
            "export DEBIAN_FRONTEND=noninteractive; apt-get install -y curl gnupg ca-certificates",
            "curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg",
            "curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' > /etc/apt/sources.list.d/nvidia-container-toolkit.list",
            "export DEBIAN_FRONTEND=noninteractive; apt-get update",
            "export DEBIAN_FRONTEND=noninteractive; apt-get install -y nvidia-container-toolkit",
        ]

        for cmd in steps:
            if not _gpu_setup_run_step(cmd, timeout=900):
                _gpu_setup_finish(False, "GPU-opsætning stoppede under installation af NVIDIA toolkit.")
                return

        major = _detect_nvidia_driver_major()
        if not major:
            _gpu_setup_append("[error] Kunne ikke auto-detektere NVIDIA driver major version.")
            _gpu_setup_finish(False, "Kunne ikke auto-detektere NVIDIA driver version. Kontroller at NVIDIA devices er mappet korrekt ind i containeren.")
            return

        libs_cmd = f"export DEBIAN_FRONTEND=noninteractive; apt-get install -y libnvidia-compute-{major} nvidia-utils-{major}"
        if not _gpu_setup_run_step(libs_cmd, timeout=900):
            _gpu_setup_finish(False, f"Installation af NVIDIA userspace-biblioteker fejlede for major {major}.", major)
            return

        tail_steps = [
            "ldconfig",
            "nvidia-ctk runtime configure --runtime=docker",
            "systemctl restart docker || service docker restart",
            "docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi",
        ]

        for cmd in tail_steps:
            if not _gpu_setup_run_step(cmd, timeout=300):
                _gpu_setup_finish(False, "GPU-opsætning blev kørt, men den afsluttende verifikation fejlede.", major)
                return

        _gpu_setup_finish(True, "", major)
    except Exception as exc:
        _gpu_setup_append(str(exc))
        _gpu_setup_finish(False, "Uventet fejl under GPU-opsætning.", major)


@app.route("/api/gpu-setup", methods=["POST"])
@login_required
def api_gpu_setup():
    if not current_user.is_admin:
        return jsonify({"ok": False, "error": "Kun administratorer kan køre GPU-opsætning."}), 403

    state = _gpu_setup_snapshot()
    if state.get("running"):
        return jsonify({"ok": False, "error": "GPU-opsætning kører allerede.", **state}), 409

    _gpu_setup_reset_state()
    thread = threading.Thread(target=_gpu_setup_worker, daemon=True)
    thread.start()
    return jsonify({"ok": True, "started": True, **_gpu_setup_snapshot()}), 202


@app.route("/api/gpu-setup/status")
@login_required
def api_gpu_setup_status():
    if not current_user.is_admin:
        return jsonify({"ok": False, "error": "Kun administratorer kan se GPU-opsætningsstatus."}), 403
    return jsonify({"ok": True, **_gpu_setup_snapshot()})


def _nfs_runtime_options(options: str) -> str:
    fstab_only = {"_netdev", "nofail", "noauto", "auto"}
    runtime_options = []
    for raw_part in str(options or "").split(","):
        part = raw_part.strip()
        if not part or part in fstab_only or part.startswith("x-"):
            continue
        runtime_options.append(part)
    if "noresvport" not in runtime_options and "resvport" not in runtime_options:
        runtime_options.append("resvport")
    return ",".join(runtime_options) or "defaults"


@app.route("/api/mount-nfs", methods=["POST"])
@login_required
def api_mount_nfs():
    import re, shlex
    data       = request.get_json(force=True) or {}
    nfs_export = str(data.get("export", "")).strip()
    mount_root = str(data.get("mount_root", "")).strip()
    subdir     = str(data.get("subdir", "")).strip().strip("/")
    options    = str(data.get("options", "vers=3,resvport,_netdev,nofail")).strip()
    mount_options = _nfs_runtime_options(options)

    if not nfs_export or ":" not in nfs_export:
        return jsonify({"ok": False, "error": "Ugyldig NFS export"}), 400
    nfs_host = nfs_export.split(":", 1)[0].strip()
    if not mount_root or not mount_root.startswith("/"):
        return jsonify({"ok": False, "error": "Ugyldig mount-sti"}), 400
    if not re.fullmatch(r"[a-zA-Z0-9/_.-]+", mount_root):
        return jsonify({"ok": False, "error": "Ugyldig mount-sti"}), 400
    if _nfs_runtime_info().get("auto_mount_supported") is not True:
        return jsonify(
            {
                "ok": False,
                "error": (
                    "Automatisk NFS-mount er kun understoettet i en privilegeret Proxmox LXC. "
                    "Denne FjordHub koerer paa Docker Desktop/WSL2, saa vaelg 'Windows (Docker Desktop)' "
                    "og koer de genererede kommandoer i WSL2-terminalen."
                ),
            }
        ), 400

    final_path = f"{mount_root.rstrip('/')}/{subdir}" if subdir else mount_root
    fstab_line = f"{nfs_export} {mount_root} nfs {options} 0 0"

    lxc_script = "\n".join(
        [
            "set -eu",
            "if ! command -v mount.nfs >/dev/null 2>&1 && [ ! -x /sbin/mount.nfs ] && [ ! -x /usr/sbin/mount.nfs ]; then",
            "  if command -v apt-get >/dev/null 2>&1; then",
            "    export DEBIAN_FRONTEND=noninteractive",
            "    apt-get update >/dev/null",
            "    apt-get install -y nfs-common >/dev/null",
            "  elif command -v apk >/dev/null 2>&1; then",
            "    apk add --no-cache nfs-utils util-linux >/dev/null",
            "  elif command -v dnf >/dev/null 2>&1; then",
            "    dnf install -y nfs-utils >/dev/null",
            "  elif command -v yum >/dev/null 2>&1; then",
            "    yum install -y nfs-utils >/dev/null",
            "  elif command -v zypper >/dev/null 2>&1; then",
            "    zypper --non-interactive install nfs-client >/dev/null",
            "  else",
            "    echo 'NFS-klient mangler i LXC. Installer nfs-common/nfs-utils og prov igen.' >&2",
            "    exit 42",
            "  fi",
            "fi",
            "if ! command -v mount.nfs >/dev/null 2>&1 && [ ! -x /sbin/mount.nfs ] && [ ! -x /usr/sbin/mount.nfs ]; then",
            "  echo 'NFS mount-helper blev ikke fundet i LXC efter installation.' >&2",
            "  exit 43",
            "fi",
            f"client_ip=$(ip route get {shlex.quote(nfs_host)} 2>/dev/null | sed -n 's/.* src \\([^ ]*\\).*/\\1/p' | head -n1 || true)",
            '[ -n "$client_ip" ] && echo "FJORDHUB_NFS_CLIENT_IP=$client_ip"',
            f"mkdir -p {shlex.quote(mount_root)}",
            f"grep -qF {shlex.quote(fstab_line)} /etc/fstab || printf '%s\\n' {shlex.quote(fstab_line)} >> /etc/fstab",
            f"if awk -v p={shlex.quote(mount_root)} '$2==p{{found=1}} END{{exit found?0:1}}' /proc/mounts; then",
            "  :",
            "else",
            f"  mount -t nfs -o {shlex.quote(mount_options)} {shlex.quote(nfs_export)} {shlex.quote(mount_root)}",
            "fi",
            f"mkdir -p {shlex.quote(final_path)}" if subdir else ":",
        ]
    )

    try:
        r = subprocess.run(
            [
                "docker", "run", "--rm",
                "--privileged", "--pid=host", "--network=host",
                FJORDHUB_IMAGE, "sh", "-c",
                f"nsenter -t 1 -m -u -n -i /bin/sh -c {shlex.quote(lxc_script)}",
            ],
            capture_output=True, text=True, timeout=180,
        )
        if r.returncode != 0:
            combined_output = "\n".join(part for part in (r.stdout.strip(), r.stderr.strip()) if part)
            client_match = re.search(r"^FJORDHUB_NFS_CLIENT_IP=(.+)$", combined_output, re.MULTILINE)
            client_ip = client_match.group(1).strip() if client_match else ""
            output = "\n".join(
                line
                for line in combined_output.splitlines()
                if not line.startswith("FJORDHUB_NFS_CLIENT_IP=")
            ).strip()
            if r.returncode in (42, 43):
                output = output or "NFS mount-helper mangler i LXC"
            if "access denied by server" in output.lower():
                client_hint = f" for klient-IP {client_ip}" if client_ip else ""
                output = (
                    f"{output}\n\nNAS'en afviser NFS-mountet{client_hint}. "
                    f"Tjek NFS-tilladelserne for exportet {nfs_export}: tillad Proxmox/LXC-klientens IP eller subnet, "
                    "og kontroller at export-stien og NFS-versionen matcher."
                )
            return jsonify({"ok": False, "error": f"Mount fejlede: {output}"})

        return jsonify({"ok": True, "path": final_path})

    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "error": "Timeout"}), 504
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/mkdir", methods=["POST"])
@login_required
def api_mkdir():
    data = request.get_json(force=True) or {}
    path = str(data.get("path", "")).strip()
    if not path or not path.startswith("/"):
        return jsonify({"ok": False, "error": "Ugyldig sti"}), 400
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", f"--volume={path}:/d", "alpine", "sh", "-c", "mkdir -p /d && chmod 777 /d"],
            capture_output=True, text=True, timeout=20,
        )
        return jsonify({"ok": result.returncode == 0, "error": result.stderr.strip() if result.returncode != 0 else None})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


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
    result = {}
    for a in _get_apps():
        status = docker_mgr.get_status(a)
        app_state = _install_state.get(a["id"])
        if status.get("state") == "not_installed" and app_state.get("state") == "installed":
            status["state"] = "exited"
            status["message"] = "Installeret, men containeren mangler. Start genskaber den."
        status["hub_linked"] = bool(_auth.get_hub_key(a["id"]))
        result[a["id"]] = status
    return jsonify(result)


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
    return render_template(
        "wizard.html",
        app=a,
        pregenerated=pregenerated,
        steps=steps,
        nfs_runtime=_nfs_runtime_info(),
    )


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
