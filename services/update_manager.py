import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from services.compose_env import build_compose_env
from services.install_state import InstallState


CHECK_TTL_SECONDS = 60


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _short_sha(value: str) -> str:
    return str(value or "")[:12]


class UpdateManager:
    def __init__(self, install_state: InstallState):
        self.install_state = install_state
        self._lock = threading.Lock()
        self._cache: dict[str, dict] = {}
        self._jobs: dict[str, dict] = {}

    def get_status(self, app_def: dict, fetch: bool = False) -> dict:
        app_id = app_def["id"]
        with self._lock:
            job = self._jobs.get(app_id)
            if job and job.get("running"):
                return dict(job)
            cached = self._cache.get(app_id)

        install_dir = self.install_state.get_install_dir(app_id)
        if not install_dir:
            status = {
                "state": "not_installed",
                "available": False,
                "update_available": False,
                "label": "Ikke installeret",
            }
            self._set_cache(app_id, status)
            return status

        if not fetch and cached:
            checked_at_epoch = float(cached.get("checked_at_epoch") or 0)
            if time.time() - checked_at_epoch < CHECK_TTL_SECONDS:
                return dict(cached)

        status = self._git_info(Path(install_dir), fetch=True)
        self._set_cache(app_id, status)
        return status

    def get_all_statuses(self, app_defs: list[dict]) -> dict[str, dict]:
        return {app_def["id"]: self.get_status(app_def, fetch=False) for app_def in app_defs}

    def check_now(self, app_def: dict) -> dict:
        return self.get_status(app_def, fetch=True)

    def start_update(self, app_def: dict) -> tuple[dict, int]:
        app_id = app_def["id"]
        install_dir = self.install_state.get_install_dir(app_id)
        if not install_dir:
            return {"ok": False, "error": "Appen er ikke installeret."}, 404

        with self._lock:
            job = self._jobs.get(app_id)
            if job and job.get("running"):
                return {"ok": False, "error": "Opdatering kører allerede.", **job}, 409

            job = {
                "state": "updating",
                "available": True,
                "running": True,
                "update_available": False,
                "label": "Opdaterer...",
                "started_at": _now_iso(),
                "finished_at": "",
                "error": "",
                "log": [],
            }
            self._jobs[app_id] = job

        thread = threading.Thread(
            target=self._run_update,
            args=(app_def, Path(install_dir)),
            daemon=True,
        )
        thread.start()
        return {"ok": True, **job}, 202

    def _set_cache(self, app_id: str, status: dict) -> None:
        status = dict(status)
        status["checked_at"] = _now_iso()
        status["checked_at_epoch"] = time.time()
        with self._lock:
            self._cache[app_id] = status

    def _set_job(self, app_id: str, patch: dict) -> dict:
        with self._lock:
            job = self._jobs.setdefault(app_id, {})
            job.update(patch)
            return dict(job)

    def _append_job_log(self, app_id: str, line: str) -> None:
        with self._lock:
            job = self._jobs.setdefault(app_id, {})
            job.setdefault("log", []).append(str(line).rstrip())
            job["log"] = job["log"][-240:]

    def _run(self, args: list[str], cwd: Path, timeout: int = 60) -> subprocess.CompletedProcess:
        return subprocess.run(
            args,
            cwd=str(cwd),
            env=build_compose_env(),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def _run_logged(self, app_id: str, args: list[str], cwd: Path, timeout: int = 900) -> int:
        self._append_job_log(app_id, "$ " + " ".join(args))
        proc = subprocess.Popen(
            args,
            cwd=str(cwd),
            env=build_compose_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            if proc.stdout:
                for line in proc.stdout:
                    self._append_job_log(app_id, line)
            return int(proc.wait(timeout=timeout))
        except subprocess.TimeoutExpired:
            proc.kill()
            raise

    def _ensure_git_safe_dir(self, install_dir: Path) -> None:
        try:
            subprocess.run(
                ["git", "config", "--global", "--add", "safe.directory", str(install_dir)],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except Exception:
            pass

    def _git_output(self, install_dir: Path, args: list[str], timeout: int = 60) -> str:
        result = self._run(["git", *args], cwd=install_dir, timeout=timeout)
        if result.returncode != 0:
            message = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(message or f"git {' '.join(args)} failed")
        return (result.stdout or "").strip()

    def _current_branch(self, install_dir: Path) -> str:
        branch = self._git_output(install_dir, ["rev-parse", "--abbrev-ref", "HEAD"], timeout=20)
        if not branch or branch == "HEAD":
            return "main"
        return branch

    def _git_info(self, install_dir: Path, fetch: bool = False) -> dict:
        if not install_dir.exists():
            return self._error_status(f"Installationsmappen findes ikke: {install_dir}")
        if not (install_dir / ".git").exists():
            return self._error_status(f"Ikke et git-repo: {install_dir}")

        self._ensure_git_safe_dir(install_dir)
        try:
            branch = self._current_branch(install_dir)
            current = self._git_output(install_dir, ["rev-parse", "HEAD"], timeout=20)
            dirty = self._git_output(
                install_dir,
                ["status", "--porcelain", "--untracked-files=no"],
                timeout=20,
            )

            fetch_error = ""
            if fetch:
                fetched = self._run(["git", "fetch", "origin", branch], cwd=install_dir, timeout=180)
                if fetched.returncode != 0:
                    fetch_error = (fetched.stderr or fetched.stdout or "").strip()

            remote = ""
            try:
                remote = self._git_output(install_dir, ["rev-parse", f"origin/{branch}"], timeout=20)
            except Exception as error:
                fetch_error = fetch_error or str(error)

            update_available = bool(remote and current != remote)
            state = "update_available" if update_available else "up_to_date"
            label = "Ny opdatering klar" if update_available else "Ingen opdatering"
            if fetch_error:
                state = "error"
                label = "Kunne ikke tjekke"

            return {
                "state": state,
                "available": True,
                "running": False,
                "ok": not bool(fetch_error),
                "update_available": update_available,
                "dirty": bool(dirty),
                "dirty_lines": dirty.splitlines()[:40],
                "branch": branch,
                "current_rev": current,
                "current_short": _short_sha(current),
                "remote_rev": remote,
                "remote_short": _short_sha(remote),
                "fetch_error": fetch_error,
                "label": label,
            }
        except Exception as error:
            return self._error_status(str(error))

    def _error_status(self, error: str) -> dict:
        return {
            "state": "error",
            "available": False,
            "running": False,
            "ok": False,
            "update_available": False,
            "error": error,
            "label": "Update-tjek fejlede",
        }

    def _run_update(self, app_def: dict, install_dir: Path) -> None:
        app_id = app_def["id"]
        try:
            self._append_job_log(app_id, f"[{_now_iso()}] Starter opdatering af {app_def.get('name', app_id)}")
            info = self._git_info(install_dir, fetch=True)
            if not info.get("ok", False):
                raise RuntimeError(info.get("fetch_error") or info.get("error") or "Kunne ikke tjekke git-status")
            if info.get("dirty"):
                raise RuntimeError("Repoet har lokale ændringer i trackede filer. Opdatering er stoppet.")

            branch = str(info.get("branch") or "main")
            if not info.get("update_available"):
                self._append_job_log(app_id, "Ingen opdatering fundet.")
                status = {**info, "state": "up_to_date", "label": "Ingen opdatering"}
                self._set_cache(app_id, status)
                self._set_job(
                    app_id,
                    {
                        **status,
                        "running": False,
                        "finished_at": _now_iso(),
                        "error": "",
                    },
                )
                return

            self._append_job_log(
                app_id,
                f"Opdaterer {info.get('current_short')} -> {info.get('remote_short')} ({branch})",
            )
            merge_code = self._run_logged(
                app_id,
                ["git", "merge", "--ff-only", f"origin/{branch}"],
                cwd=install_dir,
                timeout=300,
            )
            if merge_code != 0:
                raise RuntimeError("git merge --ff-only fejlede")

            compose_code = self._run_logged(
                app_id,
                ["docker", "compose", "up", "-d", "--build"],
                cwd=install_dir,
                timeout=900,
            )
            if compose_code != 0:
                raise RuntimeError("docker compose up -d --build fejlede")

            final_info = self._git_info(install_dir, fetch=False)
            final_info.update({"state": "up_to_date", "label": "Opdateret", "update_available": False})
            self._append_job_log(app_id, "Opdatering færdig.")
            self._set_cache(app_id, final_info)
            self._set_job(
                app_id,
                {
                    **final_info,
                    "running": False,
                    "finished_at": _now_iso(),
                    "error": "",
                },
            )
        except Exception as error:
            status = self._error_status(str(error))
            status.update({"state": "failed", "label": "Opdatering fejlede"})
            self._append_job_log(app_id, f"Fejl: {error}")
            self._set_cache(app_id, status)
            self._set_job(
                app_id,
                {
                    **status,
                    "running": False,
                    "finished_at": _now_iso(),
                    "error": str(error),
                },
            )
