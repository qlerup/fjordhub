import json
import os
import signal
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
STATE_DIR = Path(os.environ.get("FJORDHUB_UPDATER_STATE_DIR", "/state")).resolve()
UPDATE_SCRIPT = Path(os.environ.get("FJORDHUB_UPDATE_SCRIPT", str(APP_DIR / "scripts" / "update.sh"))).resolve()
SERVICE_NAME = str(os.environ.get("SERVICE_NAME", "fjordhub") or "fjordhub").strip()
DEFAULT_BRANCH = str(os.environ.get("REPO_BRANCH", "") or "").strip()
PORT = int(os.environ.get("PORT", "8090") or 8090)

STATE_PATH = STATE_DIR / "update_state.json"
LOG_PATH = STATE_DIR / "update.log"
LOCK = threading.RLock()
RUNNING_PROCESS: Optional[subprocess.Popen] = None
STOP_REQUESTED = False

_IGNORED_DIRTY_PREFIXES = tuple(
    prefix
    for prefix in (
        str(os.environ.get("FJORDHUB_UPDATER_IGNORE_DIRTY_PREFIXES", "data/,apps/fjordparcel") or "").replace(";", ",").split(",")
    )
    for prefix in [prefix.strip().replace("\\", "/").lstrip("./")]
    if prefix
)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def default_state() -> Dict[str, Any]:
    return {
        "running": False,
        "status": "idle",
        "started_at": "",
        "finished_at": "",
        "returncode": None,
        "job_id": "",
        "error": "",
    }


def normalize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    merged = default_state()
    merged.update(state or {})
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
        if state.get("status") != "stopping":
            state["status"] = "running"
    elif state.get("running"):
        state["running"] = False
    return state


def update_state(patch: Dict[str, Any]) -> Dict[str, Any]:
    with LOCK:
        state = read_state()
        state.update(patch)
        state = normalize_state(state)
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
        return lines[-max(1, int(max_lines)):]
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


def _normalize_porcelain_path(line: str) -> str:
    text = str(line or "")
    if len(text) < 3:
        return ""
    # Porcelain status uses two status columns, then path. Be lenient and trim spaces.
    path = text[2:].lstrip()
    if " -> " in path:
        path = path.split(" -> ", 1)[1].strip()
    return path.replace("\\", "/").lstrip("./")


def _is_ignored_dirty_path(path: str) -> bool:
    normalized = str(path or "").strip().replace("\\", "/").lstrip("./")
    if not normalized:
        return False
    for prefix in _IGNORED_DIRTY_PREFIXES:
        p = prefix.rstrip("/")
        if normalized == p or normalized.startswith(p + "/"):
            return True
    return False


def _split_dirty_lines(raw_dirty: str) -> tuple[list[str], list[str]]:
    relevant: list[str] = []
    ignored: list[str] = []
    for line in str(raw_dirty or "").splitlines():
        line = line.rstrip()
        if not line:
            continue
        path = _normalize_porcelain_path(line)
        if path and _is_ignored_dirty_path(path):
            ignored.append(line)
        else:
            relevant.append(line)
    return relevant, ignored


def _head_gitlinks() -> dict[str, str]:
    out = cmd_output(["git", "ls-files", "-s"], timeout=20)
    gitlinks: dict[str, str] = {}
    for line in out.splitlines():
        parts = line.split(maxsplit=3)
        if len(parts) != 4:
            continue
        mode, sha, _stage, path = parts
        if mode == "160000" and sha and path:
            gitlinks[path.strip()] = sha.strip()
    return gitlinks


def _sync_gitlinks_to_head() -> None:
    for rel_path, sha in _head_gitlinks().items():
        nested_repo = APP_DIR / rel_path
        if not (nested_repo / ".git").exists():
            continue
        try:
            has_commit = run_cmd(["git", "-C", str(nested_repo), "cat-file", "-e", f"{sha}^{{commit}}"], timeout=20)
            if has_commit.returncode != 0:
                run_cmd(["git", "-C", str(nested_repo), "fetch", "--all", "--tags"], timeout=120)
            has_commit = run_cmd(["git", "-C", str(nested_repo), "cat-file", "-e", f"{sha}^{{commit}}"], timeout=20)
            if has_commit.returncode != 0:
                continue
            run_cmd(["git", "-C", str(nested_repo), "checkout", "-f", sha], timeout=30)
            run_cmd(["git", "-C", str(nested_repo), "reset", "--hard", sha], timeout=30)
            run_cmd(["git", "-C", str(nested_repo), "clean", "-fd"], timeout=30)
        except Exception:
            continue


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
        dirty_raw = cmd_output(["git", "status", "--porcelain", "--untracked-files=no"], timeout=20)
        dirty_lines, dirty_ignored_lines = _split_dirty_lines(dirty_raw)
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
            "dirty": bool(dirty_lines),
            "dirty_lines": dirty_lines[:40],
            "dirty_ignored_lines": dirty_ignored_lines[:40],
            "fetch_error": fetch_error,
            "app_dir": str(APP_DIR),
            "script": str(UPDATE_SCRIPT),
        }
    except Exception as exc:
        return {"ok": False, "available": False, "error": str(exc), "app_dir": str(APP_DIR)}


def run_update_job(job_id: str, cleanup: bool, branch: str) -> None:
    global RUNNING_PROCESS, STOP_REQUESTED
    cleanup_arg = "--cleanup" if cleanup else "--no-cleanup"
    cmd = ["sh", str(UPDATE_SCRIPT), "--app-dir", str(APP_DIR), cleanup_arg]
    if branch:
        cmd.extend(["--branch", branch])

    env = os.environ.copy()
    env["APP_DIR"] = str(APP_DIR)
    env["SERVICE_NAME"] = SERVICE_NAME or "fjordhub"
    env["CLEANUP_DOCKER"] = "yes" if cleanup else "no"

    reset_log()
    append_log(f"[{now_iso()}] Starting FjordHub update")
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
    force_stopped = False
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(APP_DIR),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            start_new_session=(os.name != "nt"),
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
            force_stopped = bool(STOP_REQUESTED)
            STOP_REQUESTED = False
            RUNNING_PROCESS = None

    status = "stopped" if force_stopped else ("success" if returncode == 0 and not error else "failed")
    if force_stopped and not error:
        error = "Force stop requested."
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


def terminate_process(proc: subprocess.Popen, grace_seconds: float = 5) -> str:
    if proc.poll() is not None:
        return "already-exited"

    method = "terminate"
    if os.name != "nt":
        try:
            pgid = os.getpgid(proc.pid)
            if pgid != os.getpgrp():
                os.killpg(pgid, signal.SIGTERM)
                method = "sigterm-process-group"
            else:
                proc.terminate()
        except ProcessLookupError:
            return "already-exited"
        except Exception:
            proc.terminate()
    else:
        proc.terminate()

    try:
        proc.wait(timeout=grace_seconds)
        return method
    except subprocess.TimeoutExpired:
        method = "kill"
        if os.name != "nt":
            try:
                pgid = os.getpgid(proc.pid)
                if pgid != os.getpgrp():
                    os.killpg(pgid, signal.SIGKILL)
                    method = "sigkill-process-group"
                else:
                    proc.kill()
            except ProcessLookupError:
                return "already-exited"
            except Exception:
                proc.kill()
        else:
            proc.kill()
        try:
            proc.wait(timeout=2)
        except Exception:
            pass
        return method


def force_stop_update() -> tuple[Dict[str, Any], int]:
    global STOP_REQUESTED
    with LOCK:
        proc = RUNNING_PROCESS
        if not proc or proc.poll() is not None:
            state = update_state(
                {
                    "running": False,
                    "status": "idle",
                    "error": "",
                    "finished_at": now_iso(),
                    "returncode": None,
                }
            )
            state["ok"] = False
            state["error"] = "No update is running"
            state["git"] = git_info(fetch=False)
            state["log"] = tail_log()
            return state, 409
        STOP_REQUESTED = True
        update_state(
            {
                "running": True,
                "status": "stopping",
                "error": "Force stop requested.",
            }
        )

    append_log(f"[{now_iso()}] Force stop requested")
    method = terminate_process(proc)
    append_log(f"[{now_iso()}] Force stop signal sent via {method}")
    time.sleep(0.2)
    state = read_state()
    state["ok"] = True
    state["git"] = git_info(fetch=False)
    state["log"] = tail_log()
    return state, 200


def start_update(cleanup: bool) -> tuple[Dict[str, Any], int]:
    global STOP_REQUESTED
    with LOCK:
        if RUNNING_PROCESS and RUNNING_PROCESS.poll() is None:
            state = read_state()
            state["log"] = tail_log()
            return {"ok": False, "error": "Update already running", **state}, 409
        STOP_REQUESTED = False

    info = git_info(fetch=False)
    if not info.get("available"):
        return {"ok": False, "error": info.get("error") or "Updater is not available", "git": info}, 503
    if info.get("dirty"):
        # Try to auto-fix nested gitlink repos (e.g. apps/fjordparcel) before failing.
        _sync_gitlinks_to_head()
        info = git_info(fetch=False)
        if info.get("dirty"):
            return {"ok": False, "error": "Repository has local tracked changes", "git": info}, 409

    branch = str(info.get("branch") or DEFAULT_BRANCH or "").strip()
    job_id = f"upd-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    thread = threading.Thread(target=run_update_job, args=(job_id, cleanup, branch), daemon=True)
    thread.start()
    time.sleep(0.1)
    state = read_state()
    state["git"] = info
    state["log"] = tail_log()
    return {"ok": True, **state}, 202


def run_check(fetch: bool) -> Dict[str, Any]:
    info = git_info(fetch=fetch)
    # Clear stale error/status from previous failed start attempts once a new check succeeds.
    patch: Dict[str, Any] = {"git": info, "last_check_at": now_iso()}
    if info.get("ok"):
        patch.update({"status": "idle", "error": ""})
    state = update_state(patch)
    return {"ok": bool(info.get("ok")), **state}


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
    server_version = "FjordHubUpdater/1.0"

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
            self.send_json({"ok": True, "service": "fjordhub-updater", "time": now_iso()})
            return
        if path == "/status":
            state = read_state()
            state["ok"] = True
            state["service"] = "fjordhub-updater"
            state["git"] = git_info(fetch=False)
            state["log"] = tail_log()
            self.send_json(state)
            return
        self.send_json({"ok": False, "error": "Not found"}, 404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        body = parse_json_body(self)
        if path == "/check":
            state = run_check(fetch=True)
            state["log"] = tail_log()
            self.send_json(state)
            return
        if path == "/start":
            cleanup = bool(body.get("cleanup", False))
            payload, status = start_update(cleanup=cleanup)
            self.send_json(payload, status)
            return
        if path == "/force-stop":
            payload, status = force_stop_update()
            self.send_json(payload, status)
            return
        self.send_json({"ok": False, "error": "Not found"}, 404)


def main() -> None:
    ensure_state_dir()
    ensure_git_safe_dir()
    write_json(STATE_PATH, normalize_state(read_state()))
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"FjordHub updater listening on :{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
