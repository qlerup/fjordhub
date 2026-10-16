"""Admin-only HTTP/WebSocket gateway for the isolated LinuxServer VS Code desktop.

The Cloudflare Tunnel may terminate at FjordHub's published port rather than its
Traefik port, so browser WebSockets MUST pass through this Flask application.
Never proxy arbitrary origins, ports or paths and never forward FjordHub cookies.
"""
import logging
import threading
from urllib.parse import quote, urlsplit

import requests
import websocket
from flask import Response, jsonify, request, stream_with_context
from flask_login import current_user
from flask_sock import Sock

LOG = logging.getLogger(__name__)
PREFIX = "/integrations/codex/desktop/"
BACKEND = "http://fjordhub-vscode:3000"
MAX_REQUEST_BYTES = 12 * 1024 * 1024
sock = Sock()


def target_url(path="", query=b""):
    if not isinstance(path, str) or "\\" in path or ".." in path.split("/"):
        raise ValueError("Ugyldig sti.")
    normalized = quote(path, safe="/:@+._~-")
    url = BACKEND + PREFIX + normalized
    if query:
        url += "?" + query.decode("latin-1")
    return url


def _desktop_ready(installer):
    # Don't allow public routing into an uninstalled application.
    return installer.status().get("desktop") == "running"


def register_desktop_routes(blueprint, installer):
    """Mount the desktop on a fixed same-origin prefix protected by hub auth."""
    @blueprint.route(PREFIX, defaults={"path": ""}, methods=["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS"])
    @blueprint.route(PREFIX + "<path:path>", methods=["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS"])
    def desktop_http(path):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify(ok=False, error="Kræver administratoradgang."), 403
        if not _desktop_ready(installer):
            return jsonify(ok=False, error="Installér VS Code under Integrationer først."), 503
        try:
            target = target_url(path, request.query_string)
        except ValueError:
            return jsonify(ok=False, error="Ugyldig sti."), 400
        if request.content_length is not None and request.content_length > MAX_REQUEST_BYTES:
            return jsonify(ok=False, error="Anmodningen er for stor."), 413
        # Only controlled transport headers. Never forward user's cookies,
        # authorization, proxy headers, or host.
        allow = {"Content-Type", "Accept", "Accept-Language",
                 "Range", "If-None-Match", "If-Modified-Since"}
        headers = {h: request.headers[h] for h in allow if h in request.headers}
        headers["Accept-Encoding"] = "identity"
        body = None
        if request.method in ("POST", "PUT"):
            body = request.get_data(cache=False)
            if len(body) > MAX_REQUEST_BYTES:
                return jsonify(ok=False, error="Anmodningen er for stor."), 413
        upstream = None
        try:
            upstream = requests.request(
                request.method, target, headers=headers, data=body,
                timeout=(5, 120), stream=True, allow_redirects=False,
            )
        except requests.RequestException:
            LOG.exception("VS Code desktop HTTP proxy unavailable")
            return jsonify(ok=False, error="VS Code-skrivebordet svarer ikke."), 503
        response_headers = {}
        for name in ("Content-Type", "Content-Encoding", "ETag", "Last-Modified",
                     "Cache-Control", "Content-Range", "Accept-Ranges", "Vary"):
            if name in upstream.headers:
                response_headers[name] = upstream.headers[name]
        location = upstream.headers.get("Location")
        if location:
            parsed = urlsplit(location)
            if parsed.netloc and parsed.netloc not in {"fjordhub-vscode:3000"}:
                upstream.close()
                return jsonify(ok=False, error="Uventet omdirigering."), 502
            response_headers["Location"] = location.replace(BACKEND, "", 1) if location.startswith(BACKEND) else location
        response_headers["Cache-Control"] = "no-store" if "Cache-Control" not in response_headers else response_headers["Cache-Control"]
        response_headers["X-Content-Type-Options"] = "nosniff"

        def stream():
            try:
                yield from upstream.raw.stream(65536, decode_content=False)
            finally:
                upstream.close()

        return Response(stream_with_context(stream()), status=upstream.status_code,
                        headers=response_headers, direct_passthrough=True)

    @sock.route(PREFIX, bp=blueprint)
    @sock.route(PREFIX + "<path:path>", bp=blueprint)
    def desktop_websocket(ws, path=""):
        if not current_user.is_authenticated or not current_user.is_admin or not _desktop_ready(installer):
            ws.close()
            return
        try:
            target = target_url(path, request.query_string)
        except ValueError:
            ws.close()
            return
        uri = "ws://" + target[len("http://"):]
        upstream = None
        stop = threading.Event()
        try:
            upstream = websocket.create_connection(uri, timeout=10,
                origin="http://fjordhub-vscode:3000",
                enable_multithread=True)
            upstream.settimeout(1)
        except (OSError, websocket.WebSocketException):
            LOG.warning("VS Code desktop WebSocket upstream unavailable", exc_info=True)
            ws.close()
            return

        def downstream():
            try:
                while not stop.is_set():
                    try:
                        kind, payload = upstream.recv_data()
                    except websocket.WebSocketTimeoutException:
                        continue
                    if kind == websocket.ABNF.OPCODE_CLOSE:
                        break
                    if kind == websocket.ABNF.OPCODE_BINARY:
                        ws.send(payload)
                    elif kind == websocket.ABNF.OPCODE_TEXT:
                        ws.send(payload.decode("utf-8") if isinstance(payload, bytes) else payload)
            except Exception:
                LOG.debug("VS Code WebSocket closed from upstream", exc_info=True)
            finally:
                stop.set()
                try:
                    ws.close()
                except Exception:
                    pass

        reader = threading.Thread(target=downstream, name="fjordcode-ws-bridge", daemon=True)
        reader.start()
        try:
            while not stop.is_set():
                try:
                    payload = ws.receive(timeout=1)
                except TimeoutError:
                    continue
                if payload is None:
                    continue
                opcode = websocket.ABNF.OPCODE_BINARY if isinstance(payload, bytes) else websocket.ABNF.OPCODE_TEXT
                upstream.send(payload, opcode=opcode)
        except Exception:
            LOG.debug("VS Code WebSocket closed from browser", exc_info=True)
        finally:
            stop.set()
            if upstream is not None:
                upstream.close()
            reader.join(timeout=2)
