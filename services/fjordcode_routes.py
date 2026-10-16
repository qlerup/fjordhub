"""Admin-only reverse proxy for the isolated FjordCode worker."""
import hmac
import os
import secrets
from pathlib import Path

import requests
from flask import Blueprint, current_app, jsonify, render_template, request, redirect, url_for
from flask_login import current_user, login_required
from services.fjordcode_install import FjordCodeManager, FjordCodeError
from services.fjordcode_desktop import desktop_manager, DesktopError
from services.fjordcode_desktop_proxy import proxy_desktop

fjordcode_blueprint = Blueprint("fjordcode", __name__)
CONTROL_DIR = Path(os.environ.get("FJORDCODE_TOKEN_DIR", "/run/fjordcode-token"))
WORKER_URL = os.environ.get("FJORDCODE_WORKER_URL", "http://fjordhub-code:8811").rstrip("/")
installer = FjordCodeManager()
GET_ACTIONS = {"status", "projects", "chat/status", "git/status"}
POST_ACTIONS = {"auth/start", "projects/clone", "chat/start", "chat/stop"}


def _shared_secret():
    CONTROL_DIR.mkdir(parents=True, exist_ok=True)
    path = CONTROL_DIR / "token"
    if not path.exists():
        # Only FjordHub should provision this one-time private-volume secret.
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            with os.fdopen(fd, "w") as handle:
                handle.write(secrets.token_urlsafe(40))
        except FileExistsError:
            pass
    return path.read_text(encoding="utf-8").strip()


@fjordcode_blueprint.get("/integrations/codex")
@login_required
def codex_integration_page():
    if not current_user.is_admin:
        return "Kræver administratoradgang", 403
    return render_template("codex_integration.html", active_page="packages")


@fjordcode_blueprint.get("/api/fjordcode/install-status")
@login_required
def codex_install_status():
    if not current_user.is_admin:
        return jsonify(ok=False, error="Kræver administratoradgang."), 403
    return jsonify(ok=True, **installer.status())


@fjordcode_blueprint.post("/api/fjordcode/install")
@login_required
def codex_install():
    if not current_user.is_admin:
        return jsonify(ok=False, error="Kræver administratoradgang."), 403
    try:
        installer.begin_install()
    except FjordCodeError as exc:
        return jsonify(ok=False, error=str(exc)), 409
    return jsonify(ok=True, phase="installing"), 202



@fjordcode_blueprint.get("/api/fjordcode/desktop/status")
@login_required
def desktop_status():
    if not current_user.is_admin:
        return jsonify(ok=False, error="Kræver administratoradgang."), 403
    return jsonify(ok=True, **desktop_manager.status())


@fjordcode_blueprint.post("/api/fjordcode/desktop/install")
@login_required
def desktop_install():
    if not current_user.is_admin:
        return jsonify(ok=False, error="Kræver administratoradgang."), 403
    try:
        desktop_manager.begin_install()
    except DesktopError as error:
        return jsonify(ok=False, error=str(error)), 409
    return jsonify(ok=True, phase="installing"), 202


# Werkzeug distinguishes browser WebSocket upgrades from ordinary HTTP requests.
@fjordcode_blueprint.route("/fjordcode/desktop/", defaults={"subpath": ""},
                           methods=["GET"], websocket=True)
@fjordcode_blueprint.route("/fjordcode/desktop/<path:subpath>",
                           methods=["GET"], websocket=True)
@fjordcode_blueprint.route("/fjordcode/desktop/", defaults={"subpath": ""},
                           methods=["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS"])
@fjordcode_blueprint.route("/fjordcode/desktop/<path:subpath>",
                           methods=["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS"])
def desktop_proxy(subpath):
    return proxy_desktop(subpath)


@fjordcode_blueprint.route("/fjordcode")
@login_required
def fjordcode_home():
    if not current_user.is_admin:
        return "Kræver administratoradgang", 403
    if installer.status()["phase"] != "ready":
        return redirect(url_for("fjordcode.codex_integration_page"))
    return render_template("fjordcode.html", active_page="packages")


@fjordcode_blueprint.route("/api/fjordcode/<path:action>", methods=["GET", "POST"])
@login_required
def fjordcode_api(action):
    if not current_user.is_admin:
        return jsonify(ok=False, error="Kræver administratoradgang."), 403
    if request.method == "GET" and action not in GET_ACTIONS:
        return jsonify(ok=False, error="Ukendt handling."), 404
    if request.method == "POST" and action not in POST_ACTIONS:
        return jsonify(ok=False, error="Ukendt handling."), 404
    if request.method == "POST":
        if request.content_length is None or request.content_length > 12000:
            return jsonify(ok=False, error="Ugyldig beskedstørrelse."), 413
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify(ok=False, error="JSON kræves."), 400
    else:
        body = None
    try:
        token = _shared_secret()
        response = requests.request(
            request.method,
            WORKER_URL + "/" + action,
            headers={"X-FjordCode-Token": token},
            json=body,
            params=request.args if request.method == "GET" else None,
            timeout=35 if action == "projects/clone" else 8,
            allow_redirects=False,
        )
        # Only accept JSON; never echo worker HTML or authentication secrets.
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("invalid response")
        return jsonify(payload), response.status_code
    except (requests.RequestException, ValueError, OSError) as exc:
        current_app.logger.warning("FjordCode worker unavailable: %s", type(exc).__name__)
        return jsonify(ok=False, error="FjordCode-worker er ikke klar. Kontrollér Docker-service fjordcode."), 503
