"""Authenticated reverse proxy for the VS Code desktop's HTTP and WebSocket paths.

This proxy runs at FjordHub's existing public URL, even if the user's Cloudflare
Tunnel targets Flask port 8091 rather than Traefik port 80. WebSockets rely on
Gunicorn's gthread worker and simple-websocket support.
"""
import logging
import threading
from urllib.parse import quote, urlsplit

import requests
from flask import Response, jsonify, request, stream_with_context
from flask_login import current_user
from simple_websocket import Server as WebSocketServer, ConnectionClosed
from websocket import create_connection, ABNF

from services.fjordcode_desktop import desktop_manager, DESKTOP_PREFIX

LOG = logging.getLogger(__name__)
UPSTREAM = "http://fjordhub-vscode:3000"
WS_UPSTREAM = "ws://fjordhub-vscode:3000"
ALLOWED_METHODS = {"GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS"}


def same_origin(value):
    if not value:
        return False
    url = urlsplit(value)
    return (url.scheme in ("https", "http") and url.netloc.lower() ==
            request.host.lower() and not url.username and not url.password)


def check_access():
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify(ok=False, error="Kræver administratoradgang."), 403
    # No website may hijack a logged-in user's desktop WebSocket or write API.
    if request.headers.get("Upgrade", "").lower() == "websocket":
        if not same_origin(request.headers.get("Origin")):
            return jsonify(ok=False, error="Ugyldig WebSocket-origin."), 403
    elif request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("Origin") or request.headers.get("Referer")
        if not same_origin(origin):
            return jsonify(ok=False, error="Ugyldig forespørgselsorigin."), 403
    if desktop_manager.status()["phase"] != "ready":
        return jsonify(ok=False, error="Installér og start VS Code under Integrationer først."), 503
    return None


def proxy_desktop(subpath=""):
    denial = check_access()
    if denial is not None:
        return denial
    if not isinstance(subpath, str) or ".." in subpath.split("/") or "\\" in subpath:
        return jsonify(ok=False, error="Ugyldig sti."), 400
    path = DESKTOP_PREFIX + quote(subpath, safe="/-._~")
    if request.query_string:
        path += "?" + request.query_string.decode("latin-1")
    if request.headers.get("Upgrade", "").lower() == "websocket":
        return _relay_websocket(path)
    if request.method not in ALLOWED_METHODS:
        return jsonify(ok=False, error="Ikke tilladt."), 405
    max_body = 50 * 1024 * 1024
    if request.content_length is not None and request.content_length > max_body:
        return jsonify(ok=False, error="Fil er for stor (maks. 50 MB)."), 413
    headers = {"Accept-Encoding": "identity"}
    for key in ("Accept", "Content-Type", "Range", "If-None-Match", "If-Modified-Since",
                "Accept-Language"):
        if key in request.headers:
            headers[key] = request.headers[key]
    data = None
    if request.method in ("POST", "PUT"):
        data = request.get_data(cache=False)
        if len(data) > max_body:
            return jsonify(ok=False, error="Fil er for stor."), 413
    try:
        upstream = requests.request(
            request.method, UPSTREAM + path, headers=headers, data=data,
            timeout=(5, 3600), stream=True, allow_redirects=False)
    except requests.RequestException:
        return jsonify(ok=False, error="VS Code-skrivebordet starter stadig. Prøv igen om lidt."), 503
    allowed = ("Content-Type", "Content-Encoding", "Cache-Control", "ETag",
               "Last-Modified", "Content-Range", "Accept-Ranges", "Location")
    response_headers = {key: upstream.headers[key] for key in allowed if key in upstream.headers}
    if "Location" in response_headers:
        location = response_headers["Location"]
        if location.startswith("http://") or location.startswith("https://"):
            parsed = urlsplit(location)
            if parsed.netloc not in ("fjordhub-vscode:3000",):
                response_headers.pop("Location", None)
            else:
                response_headers["Location"] = parsed.path + ("?" + parsed.query if parsed.query else "")

    def chunks():
        try:
            yield from upstream.raw.stream(65536, decode_content=False)
        finally:
            upstream.close()

    response = Response(stream_with_context(chunks()), status=upstream.status_code,
                        headers=response_headers, direct_passthrough=True)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.call_on_close(upstream.close)
    return response


def _relay_websocket(path):
    """Bridge binary Selkies streams through the authenticated Flask endpoint."""
    try:
        ws_client = WebSocketServer.accept(request.environ)
    except Exception:
        LOG.exception("Browser WebSocket upgrade failed")
        return jsonify(ok=False, error="WebSocket kan ikke åbnes."), 503
    peer = None
    finished = threading.Event()
    try:
        peer = create_connection(WS_UPSTREAM + path, timeout=15,
                                 origin=request.headers.get("Origin"))
        peer.settimeout(1.0)

        def back_to_browser():
            while not finished.is_set():
                try:
                    opcode, payload = peer.recv_data(control_frame=True)
                    if opcode == ABNF.OPCODE_CLOSE:
                        break
                    if opcode == ABNF.OPCODE_PING:
                        peer.pong(payload)
                    elif opcode == ABNF.OPCODE_BINARY:
                        ws_client.send(payload)
                    elif opcode == ABNF.OPCODE_TEXT:
                        ws_client.send(payload.decode("utf-8", errors="replace"))
                except TimeoutError:
                    continue
                except Exception:
                    break
            finished.set()

        reader = threading.Thread(target=back_to_browser, daemon=True)
        reader.start()
        while not finished.is_set():
            try:
                packet = ws_client.receive(timeout=1)
                if packet is None:
                    break
                if isinstance(packet, bytes):
                    peer.send_binary(packet)
                else:
                    peer.send(packet)
            except TimeoutError:
                continue
            except ConnectionClosed:
                break
    except Exception:
        LOG.warning("VS Code desktop WebSocket disconnected", exc_info=True)
    finally:
        finished.set()
        if peer:
            peer.close()
        try:
            ws_client.close()
        except Exception:
            pass
    return ""
