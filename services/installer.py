import json
import os
import re
import secrets
import subprocess
import threading
from pathlib import Path

from services.compose_env import build_compose_env
from services.install_state import InstallState


# Inside the container, apps live under /apps/<id>.
# On the host this maps to $APPS_DIR/<id> from fjordhub/docker-compose.yml.
APPS_BASE = Path(os.environ.get("APPS_DIR", "/apps"))
DATA_BASE = Path(os.environ.get("DATA_DIR", "/data"))
WINDOWS_DRIVE_RE = re.compile(r"^([A-Za-z]):[\\/](.*)$")


def generate_secret(length: int = 64) -> str:
    return secrets.token_urlsafe(length)[:length]


def _stringify_env(values: dict) -> dict[str, str]:
    return {
        str(key): str(value)
        for key, value in values.items()
        if key and value is not None
    }


def _normalize_host_path_for_linux_client(path: str) -> str:
    match = WINDOWS_DRIVE_RE.match(str(path))
    if not match:
        return str(path)

    drive, rest = match.groups()
    rest = rest.replace("\\", "/").lstrip("/")
    return f"/run/desktop/mnt/host/{drive.lower()}/{rest}"


def _join_host_path(source: str, suffix: str) -> str:
    suffix = str(suffix or "").strip("/\\")
    if not suffix:
        return _normalize_host_path_for_linux_client(source)

    if WINDOWS_DRIVE_RE.match(source):
        path = source.rstrip("\\/") + "\\" + suffix.replace("/", "\\")
    else:
        path = source.rstrip("/") + "/" + suffix.replace("\\", "/")
    return _normalize_host_path_for_linux_client(path)


def _current_container_mounts() -> list[dict]:
    container_id = os.environ.get("HOSTNAME", "").strip()
    if not container_id:
        return []
    try:
        result = subprocess.run(
            ["docker", "inspect", container_id, "--format", "{{json .Mounts}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return []
    if result.returncode != 0:
        return []
    try:
        mounts = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return []
    return mounts if isinstance(mounts, list) else []


def _container_path_to_host_path(container_path: Path) -> str | None:
    path = "/" + str(container_path).replace("\\", "/").strip("/")
    best_match: tuple[int, dict] | None = None
    for mount in _current_container_mounts():
        target = str(mount.get("Destination") or "").rstrip("/")
        source = str(mount.get("Source") or "")
        if not target or not source:
            continue
        if path == target or path.startswith(target + "/"):
            score = len(target)
            if best_match is None or score > best_match[0]:
                best_match = (score, mount)

    if not best_match:
        return None

    target = str(best_match[1]["Destination"]).rstrip("/")
    source = str(best_match[1]["Source"])
    suffix = path[len(target):].strip("/")
    return _join_host_path(source, suffix)


def _field_default(app_def: dict, field_key: str) -> str:
    for step in app_def.get("setup_steps", []):
        for field in step.get("fields", []):
            if field.get("key") == field_key:
                return str(field.get("default", ""))
    return ""


class Installer:
    def __init__(self, state: InstallState):
        self.state = state

    def start_install(self, app_def: dict, env_values: dict, on_success=None):
        app_id = app_def["id"]
        install_dir = APPS_BASE / app_id
        self.state.set_installing(app_id, str(install_dir))
        t = threading.Thread(
            target=self._run,
            args=(app_def, env_values, install_dir, on_success),
            daemon=True,
        )
        t.start()

    def _run(self, app_def: dict, env_values: dict, install_dir: Path, on_success=None):
        app_id = app_def["id"]
        source_url = app_def.get("source_url", "")
        log = lambda msg: self.state.append_log(app_id, msg)

        try:
            env_values = self._resolve_env_values(app_def, env_values)

            if install_dir.exists() and (install_dir / ".git").exists():
                log("Repo eksisterer - henter seneste version...")
                r = subprocess.run(
                    ["git", "-C", str(install_dir), "pull", "--ff-only"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                log(r.stdout.strip() or r.stderr.strip() or "OK")
            else:
                log(f"Kloner {source_url} ...")
                install_dir.mkdir(parents=True, exist_ok=True)
                r = subprocess.run(
                    ["git", "clone", "--depth", "1", source_url, str(install_dir)],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if r.returncode != 0:
                    log(f"git clone fejlede:\n{r.stderr[:400]}")
                    self.state.set_failed(app_id, r.stderr[:400])
                    return
                log("Klon faerdig")

            log("Skriver .env ...")
            lines = ["# Genereret af FjordHub"]
            for key, value in env_values.items():
                lines.append(f"{key}={value}")
            (install_dir / ".env").write_text("\n".join(lines) + "\n", encoding="utf-8")
            log(".env skrevet")

            data_dir = env_values.get("DATA_DIR", "").strip()
            if data_dir:
                log(f"Opretter data-mappe {data_dir} ...")
                r = subprocess.run(
                    [
                        "docker",
                        "run",
                        "--rm",
                        f"--volume={data_dir}:/d",
                        "alpine",
                        "sh",
                        "-c",
                        "mkdir -p /d && chmod 777 /d",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if r.returncode == 0:
                    log("Data-mappe klar")
                else:
                    log(f"Kunne ikke pre-oprette data-mappe: {r.stderr[:200]}")

            log("Starter docker compose up -d --build ...")
            log("  (dette kan tage flere minutter foerste gang)")
            proc = subprocess.Popen(
                ["docker", "compose", "up", "-d", "--build"],
                cwd=str(install_dir),
                env=build_compose_env(env_values),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            try:
                for line in proc.stdout:
                    line = line.rstrip()
                    if line:
                        log(f"  {line}")
                proc.wait(timeout=900)
            except subprocess.TimeoutExpired:
                proc.kill()
                raise
            if proc.returncode != 0:
                log("docker compose fejlede")
                self.state.set_failed(app_id, "docker compose returncode != 0")
                return

            log(f"{app_def['name']} er installeret og koerer!")
            self.state.set_installed(app_id)
            if on_success:
                try:
                    on_success()
                except Exception:
                    pass

        except subprocess.TimeoutExpired:
            log("Timeout - processen tog for lang tid")
            self.state.set_failed(app_id, "Timeout")
        except Exception as e:
            log(f"Uventet fejl: {e}")
            self.state.set_failed(app_id, str(e))

    def _resolve_env_values(self, app_def: dict, env_values: dict) -> dict[str, str]:
        resolved: dict[str, str] = {}
        for step in app_def.get("setup_steps", []):
            for field in step.get("fields", []):
                key = str(field.get("key") or "").strip()
                if not key:
                    continue
                if field.get("type") == "auto_secret":
                    resolved[key] = generate_secret()
                else:
                    resolved[key] = str(field.get("default", ""))

        resolved.update(_stringify_env(env_values or {}))

        if not str(resolved.get("APP_PORT", "")).strip() and app_def.get("default_port"):
            resolved["APP_PORT"] = str(app_def["default_port"])
        if not str(resolved.get("TZ", "")).strip():
            resolved["TZ"] = os.environ.get("TZ", "Europe/Copenhagen")

        data_dir = str(resolved.get("DATA_DIR", "")).strip()
        default_data_dir = _field_default(app_def, "DATA_DIR").strip()
        if not data_dir or data_dir == str(DATA_BASE) or data_dir == default_data_dir:
            app_data_dir = DATA_BASE / "apps" / app_def["id"]
            try:
                app_data_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            resolved["DATA_DIR"] = _container_path_to_host_path(app_data_dir) or str(app_data_dir)

        return resolved
