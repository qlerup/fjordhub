"""Opt-in Codex CLI + full VS Code desktop installation, isolated from FjordHub."""
import io
import logging
import tarfile
import threading
from pathlib import Path

import docker

LOG = logging.getLogger(__name__)
WORKER_NAME = "fjordhub-code"
WORKER_IMAGE = "fjordhub-code:integration"
IDE_NAME = "fjordhub-vscode"
IDE_IMAGE = "fjordhub-vscode:integration"
HUB_NAME = "fjordhub"
IDE_PREFIX = "/integrations/codex/desktop/"


class FjordCodeError(ValueError):
    pass


class FjordCodeManager:
    """Install a desktop and CLI in separate Docker containers, with shared project volumes."""

    def __init__(self):
        self._lock = threading.Lock()
        self._installing = False
        self._error = ""

    @staticmethod
    def _container_status(client, name=WORKER_NAME):
        try:
            container = client.containers.get(name)
            container.reload()
            return container.status
        except docker.errors.NotFound:
            return "not_installed"

    def status(self):
        with self._lock:
            if self._installing:
                return {"phase": "installing",
                        "message": "Installerer Codex og VS Code i isolerede Docker-containere...",
                        "worker": "installing", "desktop": "installing"}
            last_error = self._error
        client = None
        try:
            client = docker.from_env(timeout=5)
            worker = self._container_status(client)
            desktop = self._container_status(client, IDE_NAME)
        except Exception:
            LOG.exception("Could not query FjordCode Docker status")
            return {"phase": "error", "message": "Docker-forbindelsen er ikke tilgængelig.",
                    "worker": "unknown", "desktop": "unknown"}
        finally:
            if client is not None:
                client.close()
        if worker == "running" and desktop == "running":
            return {"phase": "ready", "message": "VS Code og Codex kører på serveren.",
                    "worker": worker, "desktop": desktop}
        if worker == "not_installed" and desktop == "not_installed" and not last_error:
            return {"phase": "not_installed", "message": "Klar til installation.",
                    "worker": worker, "desktop": desktop}
        return {
            "phase": "error" if last_error or worker not in ("running", "not_installed")
            or desktop not in ("running", "not_installed") else "partial",
            "message": last_error or "Installationen mangler en komponent. Tryk Installér for at færdiggøre.",
            "worker": worker, "desktop": desktop,
        }

    def begin_install(self):
        with self._lock:
            if self._installing:
                raise FjordCodeError("Installationen kører allerede.")
            self._installing = True
            self._error = ""
        threading.Thread(target=self._install, name="fjordcode-installer",
                         daemon=True).start()

    @staticmethod
    def _runtime_mounts_and_network(client):
        """Reuse the existing FjordHub volume and private execution network."""
        hub = client.containers.get(HUB_NAME)
        hub.reload()
        mounts = hub.attrs.get("Mounts") or []
        token_mount = next((m for m in mounts if m.get("Destination") ==
                            "/run/fjordcode-token" and m.get("Type") == "volume"), None)
        if not token_mount or not token_mount.get("Name"):
            raise FjordCodeError("Opdatér FjordHub først: det delte Codex-token-volume mangler.")
        networks = hub.attrs.get("NetworkSettings", {}).get("Networks") or {}
        candidates = [name for name in networks if name == "fjord-code" or name.endswith("_fjord-code")]
        if len(candidates) != 1:
            raise FjordCodeError("Opdatér FjordHub først: Codex-netværket mangler.")
        project = hub.labels.get("com.docker.compose.project", "fjordhub")
        if not project or any(ch not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for ch in project):
            raise FjordCodeError("Ugyldigt Docker Compose-projektnavn.")
        return token_mount["Name"], candidates[0], project

    @staticmethod
    def _build_image(client):
        root = Path(__file__).resolve().parents[1]
        content = io.BytesIO()
        with tarfile.open(fileobj=content, mode="w") as archive:
            for source, archive_name in [
                (root / "fjordcode_worker" / "Dockerfile", "Dockerfile"),
                (root / "fjordcode_worker" / "worker.py", "fjordcode_worker/worker.py"),
            ]:
                blob = source.read_bytes()
                member = tarfile.TarInfo(archive_name)
                member.size = len(blob)
                member.mode = 0o644
                archive.addfile(member, io.BytesIO(blob))
        content.seek(0)
        client.images.build(fileobj=content, custom_context=True,
                            tag=WORKER_IMAGE, rm=True, forcerm=True)

    @staticmethod
    def _build_ide_image(client):
        root = Path(__file__).resolve().parents[1] / "fjordcode_worker"
        content = io.BytesIO()
        with tarfile.open(fileobj=content, mode="w") as archive:
            for filename, name, mode in [
                ("Dockerfile.vscode", "Dockerfile", 0o644),
                ("install-codex-extension.sh", "install-codex-extension.sh", 0o755),
            ]:
                blob = (root / filename).read_bytes()
                member = tarfile.TarInfo(name)
                member.size = len(blob)
                member.mode = mode
                archive.addfile(member, io.BytesIO(blob))
        content.seek(0)
        client.images.build(fileobj=content, custom_context=True,
                            tag=IDE_IMAGE, rm=True, forcerm=True, pull=True)

    @staticmethod
    def _ensure_volume(client, name):
        client.volumes.create(name=name)

    def _ensure_worker(self, client, token, network, project):
        status = self._container_status(client)
        if status == "running":
            return
        if status != "not_installed":
            client.containers.get(WORKER_NAME).start()
            return
        self._build_image(client)
        home = project + "_fjordcode-home"
        workspace = project + "_fjordcode-workspaces"
        self._ensure_volume(client, home)
        self._ensure_volume(client, workspace)
        container = client.containers.create(
            WORKER_IMAGE, name=WORKER_NAME, network=network,
            user="10001:10001",
            volumes={
                token: {"bind": "/run/fjordcode-token", "mode": "ro"},
                home: {"bind": "/home/codex", "mode": "rw"},
                workspace: {"bind": "/workspaces", "mode": "rw"},
            },
            environment={"HOME": "/home/codex", "CODEX_HOME": "/home/codex/.codex"},
            read_only=True, tmpfs={"/tmp": "size=128m"},
            cap_drop=["ALL"], security_opt=["no-new-privileges:true"],
            mem_limit="3g", pids_limit=256,
            restart_policy={"Name": "unless-stopped"},
            labels={"dk.fjordhub.integration": "codex"},
        )
        container.start()

    def _ensure_desktop(self, client, network, project):
        status = self._container_status(client, IDE_NAME)
        if status == "running":
            return
        if status != "not_installed":
            client.containers.get(IDE_NAME).start()
            return
        self._build_ide_image(client)
        desktop_home = project + "_fjordcode-vscode-config"
        codex_home = project + "_fjordcode-home"
        workspace = project + "_fjordcode-workspaces"
        for name in (desktop_home, codex_home, workspace):
            self._ensure_volume(client, name)
        # No socket or host bind mounts. The shared CODEX_HOME exposes skills and
        # login state in BOTH the CLI worker and the VS Code extension.
        container = client.containers.create(
            IDE_IMAGE, name=IDE_NAME, network=network,
            environment={
                "PUID": "10001", "PGID": "10001", "TZ": "Europe/Copenhagen",
                "SUBFOLDER": IDE_PREFIX, "TITLE": "FjordCode VS Code",
                "HOME": "/config", "CODEX_HOME": "/home/codex/.codex",
                "PIXELFLUX_WAYLAND": "false",
                "START_DOCKER": "false",
            },
            volumes={
                desktop_home: {"bind": "/config", "mode": "rw"},
                codex_home: {"bind": "/home/codex", "mode": "rw"},
                workspace: {"bind": "/workspaces", "mode": "rw"},
            },
            # The LinuxServer entrypoint needs its ordinary container permissions
            # for user mapping; it does NOT need Docker, Proxmox or host devices.
            security_opt=["no-new-privileges:true"],
            cap_drop=["NET_ADMIN", "SYS_ADMIN", "SYS_PTRACE", "MKNOD"],
            cap_add=["IPC_LOCK"],
            shm_size="1g", mem_limit="4g", pids_limit=512,
            restart_policy={"Name": "unless-stopped"},
            labels={"dk.fjordhub.integration": "codex-vscode"},
        )
        container.start()

    def _install(self):
        client = None
        try:
            client = docker.from_env(timeout=900)
            token, network, project = self._runtime_mounts_and_network(client)
            self._ensure_worker(client, token, network, project)
            self._ensure_desktop(client, network, project)
        except Exception:
            LOG.exception("Could not provision FjordCode")
            with self._lock:
                self._error = ("Installation mislykkedes. Kontrollér FjordHub-/Docker-loggen "
                               "og prøv igen. Eksisterende projektdata er bevaret.")
        finally:
            if client is not None:
                try:
                    client.close()
                except Exception:
                    LOG.warning("Could not close Codex Docker client", exc_info=True)
            with self._lock:
                self._installing = False
