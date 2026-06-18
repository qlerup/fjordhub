import json
import os
import subprocess
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse


APP_DIR = Path(os.environ.get("APP_DIR", "/repo")).resolve()
STATE_DIR = Path(os.environ.get("FJORDLENS_UPDATER_STATE_DIR", "/state")).resolve()
UPDATE_SCRIPT = Path(os.environ.get("FJORDLENS_UPDATE_SCRIPT", str(APP_DIR / "scripts" / "update.sh"))).resolve()
SERVICE_NAME = str(os.environ.get("SERVICE_NAME", "fjordlens") or "fjordlens").strip()
DEFAULT_BRANCH = str(os.environ.get("REPO_BRANCH", "") or "").strip()
DEFAULT_COMPOSE_SERVICES = str(os.environ.get("COMPOSE_SERVICES", "fjordlens fjordlens-ai") or "").strip()
PORT = int(os.environ.get("PORT", "8090") or 8090)
DEFAULT_AUTO_CHECK_ENABLED = str(os.environ.get("FJORDLENS_AUTO_UPDATE_CHECK", "1") or "1").strip().lower() in {"1", "true", "yes", "on"}
try:
    DEFAULT_AUTO_CHECK_INTERVAL_MINUTES = int(os.environ.get("FJORDLENS_AUTO_UPDATE_CHECK_INTERVAL_MINUTES", "30") or 30)
except Exception:
    DEFAULT_AUTO_CHECK_INTERVAL_MINUTES = 30

STATE_PATH = STATE_DIR / "update_state.json"
LOG_PATH = STATE_DIR / "update.log"
LOCK = threading.RLock()
RUNNING_PROCESS: Optional[subprocess.Popen] = None


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def clamp_auto_check_interval(value: Any) -> int:
    try:
        minutes = int(float(value))
    except Exception:
        minutes = DEFAULT_AUTO_CHECK_INTERVAL_MINUTES
    return max(5, min(1440, minutes))


def default_state() -> Dict[str, Any]:
    interval = clamp_auto_check_interval(DEFAULT_AUTO_CHECK_INTERVAL_MINUTES)
    return {
        "running": False,
        "status": "idle",
        "started_at": "",
        "finished_at": "",
        "returncode": None,
        "job_id": "",
        "auto_check_enabled": bool(DEFAULT_AUTO_CHECK_ENABLED),
        "auto_check_interval_minutes": interval,
        "last_check_at": "",
        "last_check_source": "",
        "last_auto_check_at": "",
        "next_auto_check_at": "",
        "next_auto_check_epoch": 0,
    }


def normalize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    merged = default_state()
    merged.update(state or {})
    merged["auto_check_enabled"] = bool(merged.get("auto_check_enabled"))
    merged["auto_check_interval_minutes"] = clamp_auto_check_interval(merged.get("auto_check_interval_minutes"))
    try:
        merged["next_auto_check_epoch"] = float(merged.get("next_auto_check_epoch") or 0)
    except Exception:
        merged["next_auto_check_epoch"] = 0
    return merged


def read_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if not path.exists():
            return dict(default)
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else dict(default)
    except Exception:
        return dict(default)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    ensure_state_dir()
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def read_state() -> Dict[str, Any]:
    state = normalize_state(read_json(STATE_PATH, default_state()))
    with LOCK:
        running = bool(RUNNING_PROCESS and RUNNING_PROCESS.poll() is None)
    if running:
        state["running"] = True
        state["status"] = "running"
    elif state.get("running"):
        state["running"] = False
    return state


def set_next_auto_check(state: Dict[str, Any], from_epoch: Optional[float] = None) -> Dict[str, Any]:
    base = float(from_epoch or time.time())
    interval_sec = clamp_auto_check_interval(state.get("auto_check_interval_minutes")) * 60
    next_epoch = base + interval_sec
    state["next_auto_check_epoch"] = next_epoch
    state["next_auto_check_at"] = datetime.fromtimestamp(next_epoch, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return state


def update_state(patch: Dict[str, Any]) -> Dict[str, Any]:
    with LOCK:
        state = read_state()
        state.update(patch)
        state = normalize_state(state)
        write_json(STATE_PATH, state)
        return state


def update_auto_check_settings(enabled: Optional[bool] = None, interval_minutes: Any = None) -> Dict[str, Any]:
    with LOCK:
        state = read_state()
        if enabled is not None:
            state["auto_check_enabled"] = bool(enabled)
        if interval_minutes is not None:
            state["auto_check_interval_minutes"] = clamp_auto_check_interval(interval_minutes)
        if state.get("auto_check_enabled"):
            set_next_auto_check(state)
        else:
            state["next_auto_check_epoch"] = 0
            state["next_auto_check_at"] = ""
        write_json(STATE_PATH, state)
        return state


def append_log(line: str) -> None:
    ensure_state_dir()
    with LOG_PATH.open("a", encoding="utf-8", errors="replace") as f:
        f.write(line.rstrip("\n") + "\n")


def reset_log() -> None:
    ensure_state_dir()
    LOG_PATH.write_text("", encoding="utf-8")


def tail_log(max_lines: int = 240) -> list[str]:
    try:
        lines = LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-max(1, int(max_lines)) :]
    except Exception:
        return []


def run_cmd(args: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=str(APP_DIR),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def ensure_git_safe_dir() -> None:
    try:
        subprocess.run(
            ["git", "config", "--global", "--add", "safe.directory", str(APP_DIR)],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        pass


def cmd_output(args: list[str], timeout: int = 60) -> str:
    result = run_cmd(args, timeout=timeout)
    if result.returncode != 0:
        msg = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(msg or f"Command failed: {' '.join(args)}")
    return (result.stdout or "").strip()


def current_branch() -> str:
    if DEFAULT_BRANCH:
        return DEFAULT_BRANCH
    branch = cmd_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], timeout=20)
    if not branch or branch == "HEAD":
        return "main"
    return branch


def git_info(fetch: bool = False) -> Dict[str, Any]:
    ensure_git_safe_dir()
    if not APP_DIR.exists():
        return {"ok": False, "available": False, "error": f"APP_DIR does not exist: {APP_DIR}"}
    if not (APP_DIR / ".git").exists():
        return {"ok": False, "available": False, "error": f"Not a git repository: {APP_DIR}"}
    if not UPDATE_SCRIPT.exists():
        return {"ok": False, "available": False, "error": f"Update script not found: {UPDATE_SCRIPT}"}

    try:
        branch = current_branch()
        current = cmd_output(["git", "rev-parse", "HEAD"], timeout=20)
        dirty = cmd_output(["git", "status", "--porcelain", "--untracked-files=no"], timeout=20)
        fetch_error = ""
        if fetch:
            fetched = run_cmd(["git", "fetch", "origin", branch], timeout=180)
            if fetched.returncode != 0:
                fetch_error = (fetched.stderr or fetched.stdout or "").strip()
        remote = ""
        try:
            remote = cmd_output(["git", "rev-parse", f"origin/{branch}"], timeout=20)
        except Exception as exc:
            if not fetch_error:
                fetch_error = str(exc)
        return {
            "ok": not bool(fetch_error),
            "available": True,
            "branch": branch,
            "current_rev": current,
            "current_short": current[:12],
            "remote_rev": remote,
            "remote_short": remote[:12] if remote else "",
            "update_available": bool(remote and current != remote),
            "dirty": bool(dirty),
            "dirty_lines": dirty.splitlines()[:40],
            "fetch_error": fetch_error,
            "app_dir": str(APP_DIR),
            "script": str(UPDATE_SCRIPT),
        }
    except Exception as exc:
        return {"ok": False, "available": False, "error": str(exc), "app_dir": str(APP_DIR)}


def run_update_job(job_id: str, cleanup: bool, branch: str) -> None:
    global RUNNING_PROCESS
    cleanup_arg = "--cleanup" if cleanup else "--no-cleanup"
    cmd = ["sh", str(UPDATE_SCRIPT), "--app-dir", str(APP_DIR), cleanup_arg]
    if branch:
        cmd.extend(["--branch", branch])

    env = os.environ.copy()
    env["APP_DIR"] = str(APP_DIR)
    env["SERVICE_NAME"] = SERVICE_NAME or "fjordlens"
    env["CLEANUP_DOCKER"] = "yes" if cleanup else "no"
    if DEFAULT_COMPOSE_SERVICES:
        env["COMPOSE_SERVICES"] = DEFAULT_COMPOSE_SERVICES

    reset_log()
    append_log(f"[{now_iso()}] Starting FjordLens update")
    append_log(f"[{now_iso()}] Docker cleanup: {'yes' if cleanup else 'no'}")
    append_log("$ " + " ".join(cmd))
    update_state(
        {
            "running": True,
            "status": "running",
            "job_id": job_id,
            "started_at": now_iso(),
            "finished_at": "",
            "returncode": None,
            "cleanup": cleanup,
            "command": cmd,
            "branch": branch,
            "error": "",
        }
    )

    returncode = 1
    error = ""
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(APP_DIR),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        with LOCK:
            RUNNING_PROCESS = proc
        if proc.stdout is not None:
            for line in proc.stdout:
                append_log(line.rstrip("\n"))
        returncode = int(proc.wait())
    except Exception as exc:
        error = str(exc)
        append_log(f"[{now_iso()}] ERROR: {error}")
    finally:
        with LOCK:
            RUNNING_PROCESS = None

    status = "success" if returncode == 0 and not error else "failed"
    append_log(f"[{now_iso()}] Update finished with status={status} returncode={returncode}")
    info = git_info(fetch=False)
    update_state(
        {
            "running": False,
            "status": status,
            "finished_at": now_iso(),
            "returncode": returncode,
            "error": error,
            "git": info,
        }
    )


def start_update(cleanup: bool) -> tuple[Dict[str, Any], int]:
    with LOCK:
        if RUNNING_PROCESS and RUNNING_PROCESS.poll() is None:
            state = read_state()
            state["log"] = tail_log()
            return {"ok": False, "error": "Update already running", **state}, 409

    info = git_info(fetch=False)
    if not info.get("available"):
        return {"ok": False, "error": info.get("error") or "Updater is not available", "git": info}, 503
    if info.get("dirty"):
        return {"ok": False, "error": "Repository has local tracked changes", "git": info}, 409

    branch = str(info.get("branch") or DEFAULT_BRANCH or "").strip()
    job_id = f"upd-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    thread = threading.Thread(target=run_update_job, args=(job_id, cleanup, branch), daemon=True)
    thread.start()
    time.sleep(0.1)
    state = read_state()
    state["log"] = tail_log()
    return {"ok": True, **state}, 202


def run_check(fetch: bool, source: str) -> Dict[str, Any]:
    info = git_info(fetch=fetch)
    patch: Dict[str, Any] = {
        "git": info,
        "last_check_at": now_iso(),
        "last_check_source": source,
    }
    if source == "auto":
        patch["last_auto_check_at"] = patch["last_check_at"]
    state = update_state(patch)
    if state.get("auto_check_enabled"):
        state = update_state(set_next_auto_check(state))
    return {"ok": bool(info.get("ok")), **state}


def auto_check_loop() -> None:
    while True:
        try:
            time.sleep(15)
            state = read_state()
            if not state.get("auto_check_enabled"):
                continue
            with LOCK:
                running = bool(RUNNING_PROCESS and RUNNING_PROCESS.poll() is None)
            if running:
                continue
            next_epoch = float(state.get("next_auto_check_epoch") or 0)
            if next_epoch <= 0:
                update_state(set_next_auto_check(state, from_epoch=time.time()))
                continue
            if time.time() < next_epoch:
                continue
            append_log(f"[{now_iso()}] Auto-checking for FjordLens updates")
            result = run_check(fetch=True, source="auto")
            git = result.get("git") if isinstance(result, dict) else {}
            if isinstance(git, dict) and git.get("update_available"):
                append_log(f"[{now_iso()}] Update available: {git.get('current_short')} -> {git.get('remote_short')}")
            elif isinstance(git, dict) and git.get("fetch_error"):
                append_log(f"[{now_iso()}] Auto-check failed: {git.get('fetch_error')}")
            else:
                append_log(f"[{now_iso()}] Auto-check complete: no update available")
        except Exception as exc:
            try:
                append_log(f"[{now_iso()}] Auto-check error: {exc}")
                state = read_state()
                if state.get("auto_check_enabled"):
                    update_state(set_next_auto_check(state, from_epoch=time.time()))
            except Exception:
                pass


def parse_json_body(handler: BaseHTTPRequestHandler) -> Dict[str, Any]:
    try:
        length = int(handler.headers.get("Content-Length", "0") or 0)
    except Exception:
        length = 0
    if length <= 0:
        return {}
    raw = handler.rfile.read(min(length, 1024 * 1024))
    try:
        data = json.loads(raw.decode("utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


class Handler(BaseHTTPRequestHandler):
    server_version = "FjordLensUpdater/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self.send_json({"ok": True, "service": "fjordlens-updater", "time": now_iso()})
            return
        if path == "/status":
            state = read_state()
            state["ok"] = True
            state["service"] = "fjordlens-updater"
            state["git"] = git_info(fetch=False)
            state["log"] = tail_log()
            self.send_json(state)
            return
        if path == "/settings":
            state = read_state()
            self.send_json(
                {
                    "ok": True,
                    "auto_check_enabled": bool(state.get("auto_check_enabled")),
                    "auto_check_interval_minutes": clamp_auto_check_interval(state.get("auto_check_interval_minutes")),
                    "last_check_at": state.get("last_check_at") or "",
                    "last_check_source": state.get("last_check_source") or "",
                    "last_auto_check_at": state.get("last_auto_check_at") or "",
                    "next_auto_check_at": state.get("next_auto_check_at") or "",
                }
            )
            return
        self.send_json({"ok": False, "error": "Not found"}, 404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        body = parse_json_body(self)
        if path == "/check":
            state = run_check(fetch=True, source="manual")
            state["log"] = tail_log()
            self.send_json(state)
            return
        if path == "/start":
            cleanup = bool(body.get("cleanup", True))
            payload, status = start_update(cleanup=cleanup)
            self.send_json(payload, status)
            return
        if path == "/settings":
            enabled_raw = body.get("auto_check_enabled")
            enabled = bool(enabled_raw) if "auto_check_enabled" in body else None
            interval = body.get("auto_check_interval_minutes") if "auto_check_interval_minutes" in body else None
            state = update_auto_check_settings(enabled=enabled, interval_minutes=interval)
            self.send_json(
                {
                    "ok": True,
                    "auto_check_enabled": bool(state.get("auto_check_enabled")),
                    "auto_check_interval_minutes": clamp_auto_check_interval(state.get("auto_check_interval_minutes")),
                    "last_check_at": state.get("last_check_at") or "",
                    "last_check_source": state.get("last_check_source") or "",
                    "last_auto_check_at": state.get("last_auto_check_at") or "",
                    "next_auto_check_at": state.get("next_auto_check_at") or "",
                }
            )
            return
        self.send_json({"ok": False, "error": "Not found"}, 404)


def main() -> None:
    ensure_state_dir()
    ensure_git_safe_dir()
    state = read_state()
    if state.get("auto_check_enabled") and not state.get("next_auto_check_epoch"):
        set_next_auto_check(state, from_epoch=time.time())
    write_json(STATE_PATH, normalize_state(state))
    threading.Thread(target=auto_check_loop, daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"FjordLens updater listening on :{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
