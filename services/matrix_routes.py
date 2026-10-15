"""Admin routes for the built-in Matrix system integration."""
from flask import Blueprint, Response, current_app, jsonify, render_template, request, stream_with_context
from urllib.parse import quote, urlsplit
import requests
from flask_login import current_user

from services.matrix_hub import MatrixError, validate_domain, SYNAPSE_NAME


def create_matrix_blueprint(hub, auth):
    bp = Blueprint("matrix_integration", __name__)

    def admin():
        return current_user.is_authenticated and current_user.is_admin

    def private(payload, status=200):
        response = jsonify(payload)
        response.status_code = status
        response.headers["Cache-Control"] = "no-store"
        return response


    def existing_hub_origin(browser_origin=None):
        """Use the canonical FjordHub URL or the admin's actual HTTPS origin.

        Never use a guessed domain or a freely supplied JSON field. A LAN-IP
        session without a public URL must be opened via the existing HTTPS URL.
        """
        policy = current_app.config["FJORDHUB_TRANSPORT_POLICY"]
        if policy.public_url:
            parsed = urlsplit(policy.public_url)
        else:
            parsed = urlsplit(request.headers.get("Origin") or browser_origin or request.referrer or "")
            actual_host = urlsplit("https://" + request.host).hostname
            if (parsed.scheme != "https" or
                    (parsed.hostname or "").lower() != (actual_host or "").lower()):
                raise MatrixError("Åbn FjordHub via dit eksisterende HTTPS-domæne og prøv igen.")
        if parsed.scheme != "https" or parsed.port not in (None, 443):
            raise MatrixError("FjordHubs offentlige URL skal bruge HTTPS på standardport 443.")
        return validate_domain(parsed.hostname)

    @bp.get("/.well-known/matrix/client")
    def matrix_well_known():
        data = hub._state()
        domain = data.get("domain")
        host = urlsplit("https://" + request.host).hostname
        if data.get("phase") != "ready" or not domain or host != domain:
            return private({"errcode": "M_NOT_FOUND", "error": "Matrix er ikke installeret."}, 404)
        response = jsonify({"m.homeserver": {"base_url": "https://" + domain}})
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Cache-Control"] = "public, max-age=300"
        return response

    @bp.route("/_matrix/client/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    @bp.route("/_matrix/media/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    def matrix_proxy(subpath):
        """Forward only well-defined Matrix paths to our *fixed* internal Synapse.

        This is required when an existing Cloudflare Tunnel points at FjordHub's
        published app port rather than its Traefik HTTP entrypoint.
        """
        state = hub._state()
        host = urlsplit("https://" + request.host).hostname
        if state.get("phase") != "ready" or host != state.get("domain"):
            return private({"errcode": "M_NOT_FOUND", "error": "Matrix er ikke installeret."}, 404)
        if ".." in subpath.split("/") or "\\" in subpath or not subpath:
            return private({"errcode": "M_UNRECOGNIZED", "error": "Ugyldig Matrix-sti."}, 400)
        prefix = "client" if request.path.startswith("/_matrix/client/") else "media"
        safe_path = quote(subpath, safe="/:@+-._~")
        target = "http://" + SYNAPSE_NAME + ":8008/_matrix/" + prefix + "/" + safe_path
        if request.query_string:
            target += "?" + request.query_string.decode("latin-1")
        max_size = 100 * 1024 * 1024
        if request.content_length is not None and request.content_length > max_size:
            return private({"errcode": "M_TOO_LARGE", "error": "Filen er for stor (maks. 100 MB)."}, 413)
        allowed_request = ("Authorization", "Content-Type", "Content-Length",
                           "Accept", "Accept-Language", "Range", "If-None-Match",
                           "If-Modified-Since", "If-Match", "Origin",
                           "Access-Control-Request-Method", "Access-Control-Request-Headers")
        headers = {key: request.headers[key] for key in allowed_request if key in request.headers}
        headers["Accept-Encoding"] = "identity"
        headers["X-Forwarded-For"] = request.remote_addr or "127.0.0.1"
        headers["X-Forwarded-Proto"] = "https"
        try:
            upstream = requests.request(
                request.method, target, headers=headers, data=request.stream if request.method in ("POST", "PUT") else None,
                timeout=(5, 55), stream=True, allow_redirects=False)
        except requests.RequestException:
            return private({"errcode": "M_UNKNOWN", "error": "Matrix-serveren svarer ikke."}, 503)

        forwarded = ("Content-Type", "Content-Length", "Content-Encoding", "ETag",
                     "Last-Modified", "Cache-Control", "Content-Range", "Accept-Ranges",
                     "Access-Control-Allow-Origin", "Access-Control-Allow-Headers",
                     "Access-Control-Allow-Methods", "Access-Control-Expose-Headers",
                     "Access-Control-Max-Age", "Vary", "Retry-After")
        reply_headers = {key: upstream.headers[key] for key in forwarded if key in upstream.headers}

        def chunks():
            try:
                yield from upstream.raw.stream(64 * 1024, decode_content=False)
            finally:
                upstream.close()

        response = Response(stream_with_context(chunks()), status=upstream.status_code,
                            headers=reply_headers, direct_passthrough=True)
        response.call_on_close(upstream.close)
        return response

    @bp.get("/integrations/matrix")
    def page():
        if not admin():
            return private({"ok": False, "error": "Kræver administratoradgang."}, 403)
        return render_template("matrix_integration.html", active_page="packages", matrix=hub.status(), hub_public_url=current_app.config["FJORDHUB_TRANSPORT_POLICY"].public_url)

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
            domain = existing_hub_origin(data.get("origin"))
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
