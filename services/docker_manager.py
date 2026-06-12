import os
import subprocess
from datetime import datetime, timezone, timedelta

from services.compose_env import build_compose_env

try:
    import docker
    _docker_available = True
except ImportError:
    _docker_available = False


def _parse_started_at(started_str: str) -> datetime | None:
    if not started_str or started_str.startswith("0001"):
        return None
    try:
        # Docker returns RFC3339 with nanoseconds: "2024-01-15T10:30:00.123456789Z"
        trimmed = started_str[:26].rstrip("Z").rstrip("0").rstrip(".")
        return datetime.fromisoformat(trimmed + "+00:00")
    except Exception:
        return None


def _format_uptime(started_at: datetime) -> str:
    delta = datetime.now(timezone.utc) - started_at
    total = int(delta.total_seconds())
    if total < 60:
        return f"{total}s"
    if total < 3600:
        return f"{total // 60}m"
    if total < 86400:
        h = total // 3600
        m = (total % 3600) // 60
        return f"{h}t {m}m" if m else f"{h}t"
    d = total // 86400
    h = (total % 86400) // 3600
    return f"{d}d {h}t" if h else f"{d}d"


class DockerManager:
    def __init__(self):
        self.client = None
        if _docker_available:
            try:
                self.client = docker.from_env()
                self.client.ping()
            except Exception:
                self.client = None

    def get_status(self, app_def: dict) -> dict:
        container_name = app_def.get("container_name")
        if not container_name or not self.client:
            return {"state": "unknown", "uptime": None}
        try:
            container = self.client.containers.get(container_name)
            state = container.status  # "running", "exited", "paused", "restarting", etc.
            uptime = None
            if state == "running":
                started_str = container.attrs.get("State", {}).get("StartedAt", "")
                started_at = _parse_started_at(started_str)
                if started_at:
                    uptime = _format_uptime(started_at)
            return {"state": state, "uptime": uptime}
        except Exception as e:
            err = str(e)
            if "404" in err or "No such container" in err:
                return {"state": "not_installed", "uptime": None}
            return {"state": "error", "uptime": None, "message": err[:120]}

    def start(self, app_def: dict) -> tuple[bool, str]:
        compose_dir = self._resolve_compose_dir(app_def)
        if not compose_dir:
            return False, "Compose-mappe ikke konfigureret. Sæt miljøvariablen."
        try:
            result = subprocess.run(
                ["docker", "compose", "up", "-d"],
                cwd=compose_dir,
                env=build_compose_env(),
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                return True, "App startet"
            return False, result.stderr[:200] or "Ukendt fejl"
        except FileNotFoundError:
            return False, "docker compose ikke fundet"
        except subprocess.TimeoutExpired:
            return False, "Timeout ved opstart"

    def stop(self, app_def: dict) -> tuple[bool, str]:
        compose_dir = self._resolve_compose_dir(app_def)
        if not compose_dir:
            return False, "Compose-mappe ikke konfigureret."
        try:
            result = subprocess.run(
                ["docker", "compose", "stop"],
                cwd=compose_dir,
                env=build_compose_env(),
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                return True, "App stoppet"
            return False, result.stderr[:200] or "Ukendt fejl"
        except FileNotFoundError:
            return False, "docker compose ikke fundet"
        except subprocess.TimeoutExpired:
            return False, "Timeout ved stop"

    def _resolve_compose_dir(self, app_def: dict) -> str | None:
        env_key = app_def.get("compose_dir_env")
        if env_key:
            path = os.environ.get(env_key, "").strip()
            if path:
                return path
        fallback = app_def.get("compose_dir", "").strip()
        return fallback or None
