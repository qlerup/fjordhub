import os
import shutil
import subprocess
from pathlib import Path
from flask import Flask, render_template, jsonify, request, redirect, url_for

from services.docker_manager import DockerManager
from services.registry import AppRegistry
from services.remote_registry import RemoteRegistry
from services.install_state import InstallState
from services.installer import Installer, generate_secret
from services.compose_env import build_compose_env

APP_PORT = int(os.environ.get("APP_PORT", 8080))
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data")).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

REGISTRY_URL = os.environ.get(
    "REGISTRY_URL",
    "https://raw.githubusercontent.com/qlerup/fjordhub/main/registry.json",
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

_local_registry  = AppRegistry(Path(__file__).parent / "app_registry")
_remote_registry = RemoteRegistry(DATA_DIR, REGISTRY_URL)
_install_state   = InstallState(DATA_DIR)
_installer       = Installer(_install_state)
docker_mgr       = DockerManager()


def _get_apps() -> list[dict]:
    apps = _remote_registry.get_apps()
    return apps if apps else _local_registry.get_all()


def _get_app(app_id: str) -> dict | None:
    return next((a for a in _get_apps() if a.get("id") == app_id), None)


@app.context_processor
def inject_globals():
    return {"app_name": "FjordHub"}


# ── Dashboard ────────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    return render_template(
        "dashboard.html",
        apps=_get_apps(),
        reg_status=_remote_registry.get_status(),
    )


# ── App status & control ─────────────────────────────────────────────────────

@app.route("/api/apps-status")
def api_apps_status():
    return jsonify({a["id"]: docker_mgr.get_status(a) for a in _get_apps()})


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

    # 3. Clear install state
    _install_state.clear(app_id)

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
    return render_template("wizard.html", app=a, pregenerated=pregenerated)


@app.route("/apps/<app_id>/install", methods=["POST"])
def install_app(app_id):
    a = _get_app(app_id)
    if not a:
        return jsonify({"error": "Unknown app"}), 404
    body = request.get_json(silent=True) or {}
    env_values = body.get("env", {})
    if not isinstance(env_values, dict):
        return jsonify({"error": "env must be an object"}), 400
    _installer.start_install(a, env_values)
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
