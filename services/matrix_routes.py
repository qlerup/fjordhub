"""Admin routes for the built-in Matrix system integration."""
from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user

from services.matrix_hub import MatrixError, validate_domain


def create_matrix_blueprint(hub, auth):
    bp = Blueprint("matrix_integration", __name__)

    def admin():
        return current_user.is_authenticated and current_user.is_admin

    def private(payload, status=200):
        response = jsonify(payload)
        response.status_code = status
        response.headers["Cache-Control"] = "no-store"
        return response

    @bp.get("/integrations/matrix")
    def page():
        if not admin():
            return private({"ok": False, "error": "Kræver administratoradgang."}, 403)
        return render_template("matrix_integration.html", active_page="packages", matrix=hub.status())

    @bp.get("/api/matrix/status")
    def status():
        if not admin():
            return private({"ok": False}, 403)
        return private({"ok": True, **hub.status()})

    @bp.post("/api/matrix/install")
    def install():
        if not admin():
            return private({"ok": False}, 403)
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return private({"ok": False, "error": "Ugyldige oplysninger."}, 400)
        try:
            domain = validate_domain(data.get("domain"))
            state = hub._state()
            if state.get("phase") == "installing" and hub._installer_active():
                raise MatrixError("En Matrix-installation er allerede i gang.")
            if state.get("phase") == "ready":
                raise MatrixError("Matrix er allerede installeret.")
            if state.get("domain") and state["domain"] != domain:
                raise MatrixError("Matrix-domænet kan ikke ændres efter første installering.")
            token = state.get("monitor_token")
            if not token:
                token = auth.create_access_token("Matrix-bot (kun læseadgang)", current_user.id,
                                                 days=0)
            hub.begin_install(domain, token)
            hub._save_state(monitor_token=token)
        except (MatrixError, ValueError) as exc:
            return private({"ok": False, "error": str(exc)}, 400)
        return private({"ok": True, "message": "Installation startet."}, 202)

    @bp.post("/api/matrix/users")
    def create_user():
        if not admin():
            return private({"ok": False}, 403)
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return private({"ok": False, "error": "Ugyldige oplysninger."}, 400)
        try:
            result = hub.create_user(data.get("username"))
        except (MatrixError, docker_error()) as exc:
            return private({"ok": False, "error": str(exc) if isinstance(exc, MatrixError)
                            else "Kunne ikke oprette Matrix-brugeren."}, 400)
        return private({"ok": True, **result}, 201)

    @bp.post("/api/matrix/test")
    def test_message():
        if not admin():
            return private({"ok": False}, 403)
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return private({"ok": False, "error": "Ugyldige oplysninger."}, 400)
        try:
            hub.send_test(data.get("user_id"))
        except MatrixError as exc:
            return private({"ok": False, "error": str(exc)}, 400)
        return private({"ok": True, "message": "Testbeskeden er sat i kø til en krypteret chat."}, 202)

    return bp


def docker_error():
    # Keep Docker SDK exceptions specific without importing the daemon at startup.
    import docker
    return docker.errors.DockerException
