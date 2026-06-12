import os
import secrets
import subprocess
import threading
from pathlib import Path

from services.install_state import InstallState

# Inside the container, apps live under /apps/<id>.
# On the host this maps to $APPS_DIR/<id> (configured in docker-compose.yml).
APPS_BASE = Path(os.environ.get("APPS_DIR", "/apps"))


def generate_secret(length: int = 64) -> str:
    return secrets.token_urlsafe(length)[:length]


class Installer:
    def __init__(self, state: InstallState):
        self.state = state

    def start_install(self, app_def: dict, env_values: dict):
        app_id = app_def["id"]
        install_dir = APPS_BASE / app_id
        self.state.set_installing(app_id, str(install_dir))
        t = threading.Thread(
            target=self._run,
            args=(app_def, env_values, install_dir),
            daemon=True,
        )
        t.start()

    def _run(self, app_def: dict, env_values: dict, install_dir: Path):
        app_id = app_def["id"]
        source_url = app_def.get("source_url", "")
        log = lambda msg: self.state.append_log(app_id, msg)

        try:
            # ── 1. Clone ────────────────────────────────────────────────────
            if install_dir.exists() and (install_dir / ".git").exists():
                log(f"↻ Repo eksisterer — henter seneste version...")
                r = subprocess.run(
                    ["git", "-C", str(install_dir), "pull", "--ff-only"],
                    capture_output=True, text=True, timeout=60,
                )
                log(r.stdout.strip() or r.stderr.strip() or "OK")
            else:
                log(f"⬇ Kloner {source_url} ...")
                install_dir.mkdir(parents=True, exist_ok=True)
                r = subprocess.run(
                    ["git", "clone", "--depth", "1", source_url, str(install_dir)],
                    capture_output=True, text=True, timeout=120,
                )
                if r.returncode != 0:
                    log(f"✗ git clone fejlede:\n{r.stderr[:400]}")
                    self.state.set_failed(app_id, r.stderr[:400])
                    return
                log("✓ Klon færdig")

            # ── 2. Write .env ───────────────────────────────────────────────
            log("→ Skriver .env ...")
            lines = [f"# Genereret af FjordHub"]
            for k, v in env_values.items():
                lines.append(f"{k}={v}")
            (install_dir / ".env").write_text("\n".join(lines) + "\n", encoding="utf-8")
            log("✓ .env skrevet")

            # ── 3. docker compose up ────────────────────────────────────────
            log("→ Starter docker compose up -d --build ...")
            log("  (dette kan tage flere minutter første gang)")
            proc = subprocess.Popen(
                ["docker", "compose", "up", "-d", "--build"],
                cwd=str(install_dir),
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
                log("✗ docker compose fejlede")
                self.state.set_failed(app_id, "docker compose returncode != 0")
                return

            log(f"✓ {app_def['name']} er installeret og kører!")
            self.state.set_installed(app_id)

        except subprocess.TimeoutExpired:
            log("✗ Timeout — processen tog for lang tid")
            self.state.set_failed(app_id, "Timeout")
        except Exception as e:
            log(f"✗ Uventet fejl: {e}")
            self.state.set_failed(app_id, str(e))
