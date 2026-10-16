"""Tiny isolated HTTP worker for Codex CLI. No Docker socket or host mounts."""
import hmac
import json
import os
import re
import signal
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

HOME = Path("/home/codex")
ROOT = Path("/workspaces")
STATE_FILE = HOME / "fjordcode-state.json"
TOKEN_FILE = Path("/run/fjordcode-token/token")
REPO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,60}/[A-Za-z0-9][A-Za-z0-9_.-]{0,90}$")
LOCK = threading.RLock()
active = {"process": None, "project": None}
auth_process = None
auth_lines = []
auth_status = "idle"


def load_state():
    try:
        obj = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except (OSError, ValueError):
        return {}


state = load_state()


def save_state():
    temporary = STATE_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    temporary.replace(STATE_FILE)


def repo_path(name):
    if not isinstance(name, str) or not REPO.fullmatch(name) or ".." in name:
        raise ValueError("Ugyldigt GitHub-repository.")
    path = ROOT / name.replace("/", "--")
    if path.parent != ROOT or not path.is_dir() or not (path / ".git").exists():
        raise ValueError("Projektet er ikke klonet.")
    return path


def projects():
    return sorted(
        [p.name.replace("--", "/", 1) for p in ROOT.iterdir()
         if p.is_dir() and (p / ".git").is_dir() and "--" in p.name]
    )


def authenticate():
    global auth_process, auth_status
    if auth_process and auth_process.poll() is None:
        return
    auth_lines.clear()
    auth_status = "running"
    try:
        auth_process = subprocess.Popen(
            ["codex", "login", "--device-auth"], stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1, cwd=str(HOME)
        )
    except OSError as exc:
        auth_lines.append(str(exc))
        auth_status = "failed"
        return

    def capture():
        global auth_status
        try:
            for line in auth_process.stdout:
                with LOCK:
                    auth_lines.append(line.rstrip()[:800])
                    del auth_lines[:-24]
            result = auth_process.wait()
            with LOCK:
                auth_status = "complete" if result == 0 else "failed"
        except Exception:
            with LOCK:
                auth_status = "failed"
    threading.Thread(target=capture, daemon=True).start()


def login_ok():
    try:
        p = subprocess.run(["codex", "login", "status"], cwd=str(HOME),
                           capture_output=True, text=True, timeout=5)
        return p.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def git_status(folder):
    try:
        p = subprocess.run(["git", "status", "--short"], cwd=folder, capture_output=True,
                           text=True, timeout=5)
        if p.returncode:
            return []
        return p.stdout.splitlines()[:100]
    except (OSError, subprocess.TimeoutExpired):
        return []


def run_job(name, prompt):
    """Stream JSONL from an isolated workspace, persisting chat and actions."""
    global active
    folder = repo_path(name)
    with LOCK:
        info = state.setdefault(name, {"session": "", "messages": [], "events": [], "status": "idle"})
        previous = info.get("session") or ""
        info.setdefault("messages", []).append({"role": "user", "text": prompt})
        info["messages"] = info["messages"][-60:]
        info["events"] = []
        info["status"] = "running"
        save_state()
    if previous:
        cmd = ["codex", "exec", "resume", "--json", previous, prompt]
    else:
        cmd = ["codex", "exec", "--json", "--sandbox", "workspace-write",
               "--skip-git-repo-check", prompt]
    try:
        # No shell invocation. The CLI itself enforces workspace-write sandboxing.
        proc = subprocess.Popen(
            cmd, cwd=str(folder), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1, start_new_session=True
        )
        with LOCK:
            active = {"process": proc, "project": name}
        for line in proc.stdout:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            kind = event.get("type", "")
            item = event.get("item") or {}
            with LOCK:
                if kind == "thread.started":
                    info["session"] = str(event.get("thread_id") or "")[:128]
                elif kind == "item.completed" and item.get("type") == "agent_message":
                    message = str(item.get("text") or "")
                    if message:
                        info["messages"].append({"role": "assistant", "text": message[:20000]})
                        info["messages"] = info["messages"][-60:]
                elif kind in {"item.started", "item.completed", "turn.failed", "error"}:
                    if kind == "error":
                        detail = str(event.get("message") or "Codex-fejl")
                    elif kind == "turn.failed":
                        detail = str(event.get("error") or "Opgaven fejlede")
                    elif item.get("type") == "command_execution":
                        detail = str(item.get("command") or "")[:400]
                    elif item.get("type") == "file_change":
                        detail = "Filer ændret"
                    else:
                        detail = ""
                    if detail:
                        info["events"].append({"type": kind, "text": detail})
                        info["events"] = info["events"][-70:]
                elif kind == "turn.completed":
                    info["status"] = "complete"
                save_state()
        try:
            errors = proc.stderr.read()[-1800:]
        except Exception:
            errors = ""
        code = proc.wait()
        with LOCK:
            if code != 0:
                info["status"] = "failed"
                info["events"].append({"type": "error", "text": errors or f"Codex sluttede med kode {code}"})
            elif info["status"] == "running":
                info["status"] = "complete"
            save_state()
    except Exception as exc:
        with LOCK:
            info["status"] = "failed"
            info["events"].append({"type": "error", "text": type(exc).__name__})
            save_state()
    finally:
        with LOCK:
            active = {"process": None, "project": None}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def reply(self, payload, status=200):
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def handle_action(self):
        try:
            expected = TOKEN_FILE.read_text(encoding="utf-8").strip()
        except OSError:
            return self.reply({"ok": False, "error": "Worker-token mangler."}, 503)
        supplied = self.headers.get("X-FjordCode-Token", "")
        if not expected or not hmac.compare_digest(supplied, expected):
            return self.reply({"ok": False, "error": "Ikke tilladt."}, 403)
        path = urlsplit(self.path)
        action = path.path.lstrip("/")
        if self.command == "POST":
            length = int(self.headers.get("Content-Length", "0"))
            if length < 2 or length > 12000:
                return self.reply({"ok": False, "error": "Ugyldig størrelse."}, 413)
            try:
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError()
            except ValueError:
                return self.reply({"ok": False, "error": "JSON kræves."}, 400)
        else:
            data = {}
        try:
            if action == "status" and self.command == "GET":
                with LOCK:
                    return self.reply({"ok": True, "logged_in": login_ok(),
                                       "auth_status": auth_status,
                                       "auth_output": "\n".join(auth_lines[-24:]),
                                       "busy": bool(active["process"])})
            if action == "auth/start" and self.command == "POST":
                with LOCK:
                    authenticate()
                return self.reply({"ok": True, "started": True})
            if action == "projects" and self.command == "GET":
                return self.reply({"ok": True, "projects": projects()})
            if action == "projects/clone" and self.command == "POST":
                name = str(data.get("repository") or "").strip()
                if not REPO.fullmatch(name) or ".." in name:
                    raise ValueError("Brug formatet ejer/repository.")
                folder = ROOT / name.replace("/", "--")
                if folder.exists():
                    raise ValueError("Projektet findes allerede.")
                # Intentionally only HTTPS public GitHub clones; no uploaded credentials.
                clone = subprocess.run(
                    ["git", "clone", "--depth=1", "--", "https://github.com/" + name + ".git", str(folder)],
                    capture_output=True, text=True, timeout=30, cwd=str(ROOT)
                )
                if clone.returncode:
                    raise ValueError("Kunne ikke hente repository. Er det offentligt?")
                return self.reply({"ok": True, "project": name})
            if action == "chat/status" and self.command == "GET":
                query = parse_qs(path.query)
                name = (query.get("project") or [""])[0]
                repo = repo_path(name)
                with LOCK:
                    entry = state.get(name, {})
                    snapshot = json.loads(json.dumps(entry))
                return self.reply({"ok": True, "chat": snapshot, "changes": git_status(repo)})
            if action == "git/status" and self.command == "GET":
                query = parse_qs(path.query)
                repo = repo_path((query.get("project") or [""])[0])
                return self.reply({"ok": True, "changes": git_status(repo)})
            if action == "chat/start" and self.command == "POST":
                name = data.get("project")
                prompt = str(data.get("prompt") or "").strip()
                repo_path(name)
                if not prompt or len(prompt) > 5000:
                    raise ValueError("Skriv en besked på højst 5.000 tegn.")
                if not login_ok():
                    raise ValueError("Forbind først din ChatGPT-konto.")
                with LOCK:
                    if active["process"] or state.get(name, {}).get("status") == "running":
                        # A stale running flag can remain after container restart.
                        if active["process"]:
                            raise ValueError("Codex arbejder allerede med en opgave.")
                    # Reserve slot before launching the background thread.
                    active.update({"process": True, "project": name})
                threading.Thread(target=run_job, args=(name, prompt), daemon=True).start()
                return self.reply({"ok": True, "started": True})
            if action == "chat/stop" and self.command == "POST":
                with LOCK:
                    proc = active["process"]
                    if proc and hasattr(proc, "pid"):
                        os.killpg(proc.pid, signal.SIGTERM)
                    elif proc:
                        raise ValueError("Opgaven starter. Prøv igen.")
                return self.reply({"ok": True})
        except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
            return self.reply({"ok": False, "error": str(exc)}, 400)
        return self.reply({"ok": False, "error": "Ukendt handling."}, 404)

    def do_GET(self):
        self.handle_action()

    def do_POST(self):
        self.handle_action()


if __name__ == "__main__":
    HOME.mkdir(parents=True, exist_ok=True)
    ROOT.mkdir(parents=True, exist_ok=True)
    ThreadingHTTPServer(("0.0.0.0", 8811), Handler).serve_forever()
