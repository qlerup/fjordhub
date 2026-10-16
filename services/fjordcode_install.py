"""Opt-in installation of the isolated Codex worker via the Docker SDK."""
import io
import logging
import tarfile
import threading
from pathlib import Path

import docker

LOG = logging.getLogger(__name__)
WORKER_NAME = "fjordhub-code"
WORKER_IMAGE = "fjordhub-code:integration"
HUB_NAME = "fjordhub"


class FjordCodeError(ValueError):
    pass


class FjordCodeManager:
    """Works in Docker-based FjordHub hosts without SSH or a shell command."""

    def __init__(self):
        self._lock = threading.Lock()
        self._installing = False
        self._error = ""

    @staticmethod
    def _container_status(client):
        try:
            container = client.containers.get(WORKER_NAME)
            container.reload()
            return container.status
        except docker.errors.NotFound:
            return "not_installed"

    def status(self):
        with self._lock:
            if self._installing:
                return {"phase": "installing", "message": "Installerer Codex i isoleret Docker-container..."}
            last_error = self._error
        try:
            with docker.from_env(timeout=5) as client:
                status = self._container_status(client)
        except Exception:
            return {"phase": "error", "message": "Docker-forbindelsen er ikke tilgængelig."}
        if status == "running":
            return {"phase": "ready", "message": "Codex-containeren kører."}
        if status == "not_installed":
            return {"phase": "error" if last_error else "not_installed",
                    "message": last_error or "Klar til installation."}
        return {"phase": "error", "message": last_error or
                "Codex-containeren er stoppet. Tryk Installér for at starte den igen."}

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
        """Derive names from FjordHub's real Docker mounts and network."""
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
        client.images.build(fileobj=content, custom_context=True, tag=WORKER_IMAGE,
                            rm=True, forcerm=True, timeout=900)

    def _install(self):
        try:
            with docker.from_env(timeout=900) as client:
                status = self._container_status(client)
                if status == "running":
                    return
                if status != "not_installed":
                    client.containers.get(WORKER_NAME).start()
                    return
                token, network, project = self._runtime_mounts_and_network(client)
                self._build_image(client)
                home = project + "_fjordcode-home"
                workspace = project + "_fjordcode-workspaces"
                client.volumes.create(name=home)
                client.volumes.create(name=workspace)
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
        except Exception:
            LOG.exception("Could not provision FjordCode")
            with self._lock:
                self._error = ("Installation mislykkedes. Kontrollér FjordHub-/Docker-loggen "
                               "og prøv igen.")
        finally:
            with self._lock:
                self._installing = False
