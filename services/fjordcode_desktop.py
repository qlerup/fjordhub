"""Optional, isolated full VS Code desktop managed by FjordHub.

No host Docker socket, host source tree or Proxmox mounts enter the desktop.
Both Codex runtimes may share the persistent workspace/home volumes.
"""
import logging
import re
import threading

import docker

LOG = logging.getLogger(__name__)
IMAGE = "lscr.io/linuxserver/vscode:latest"
NAME = "fjordhub-vscode"
DESKTOP_PREFIX = "/fjordcode/desktop/"
VALID_PROJECT = re.compile(r"^[a-z0-9_-]{1,63}$")


class DesktopError(ValueError):
    pass


class CodexDesktop:
    def __init__(self):
        self._lock = threading.RLock()
        self._installing = False
        self._phase = ""
        self._message = ""
        self._extension = ""

    @staticmethod
    def _get_container(client):
        try:
            return client.containers.get(NAME)
        except docker.errors.NotFound:
            return None

    @staticmethod
    def _existing_network_and_project(client):
        hub = client.containers.get("fjordhub")
        hub.reload()
        networks = hub.attrs.get("NetworkSettings", {}).get("Networks") or {}
        names = [n for n in networks if n == "fjord-code" or n.endswith("_fjord-code")]
        if len(names) != 1:
            raise DesktopError("Codex-netværket mangler. Opdatér FjordHub og prøv igen.")
        project = hub.labels.get("com.docker.compose.project", "fjordhub")
        if not VALID_PROJECT.fullmatch(project):
            raise DesktopError("FjordHubs Docker Compose-projektnavn er ugyldigt.")
        return names[0], project

    def status(self):
        with self._lock:
            if self._installing:
                return {"phase": "installing", "message": self._message or "Klargør VS Code...",
                        "extension": self._extension}
            problem = self._message if self._phase == "error" else ""
            extension = self._extension
        client = None
        try:
            client = docker.from_env(timeout=5)
            container = self._get_container(client)
            if container is None:
                return {"phase": "error" if problem else "not_installed",
                        "message": problem or "VS Code er ikke installeret.", "extension": extension}
            container.reload()
            phase = "ready" if container.status == "running" else "stopped"
            return {"phase": phase,
                    "message": ("VS Code kører i sin egen Docker-container." if phase == "ready"
                                else "VS Code er stoppet. Tryk Start VS Code."),
                    "extension": extension}
        except docker.errors.DockerException:
            LOG.exception("Unable to check VS Code desktop")
            return {"phase": "error", "message": "Docker-forbindelsen er ikke tilgængelig.",
                    "extension": extension}
        finally:
            if client:
                client.close()

    def begin_install(self):
        with self._lock:
            if self._installing:
                raise DesktopError("Installationen kører allerede.")
            self._installing = True
            self._phase = "installing"
            self._message = "Henter VS Code-containeren..."
            self._extension = ""
        threading.Thread(target=self._install, daemon=True, name="fjordcode-desktop-installer").start()

    def _progress(self, message):
        with self._lock:
            self._message = message

    @staticmethod
    def _install_codex_extension(container):
        """Install the *official* marketplace extension into the persistent user profile.

        Do not block opening the desktop when marketplace installs are temporarily
        unavailable. An administrator can also install OpenAI.chatgpt in the GUI.
        """
        command = [
            "/bin/bash", "-lc",
            "runuser -u abc -- env HOME=/config "
            "code --install-extension OpenAI.chatgpt --force"
        ]
        response = container.exec_run(command, demux=True)
        return response.exit_code == 0

    def _install(self):
        client = None
        try:
            client = docker.from_env(timeout=900)
            existing = self._get_container(client)
            if existing is not None:
                if existing.status != "running":
                    self._progress("Starter eksisterende VS Code...")
                    existing.start()
                container = existing
            else:
                network, project = self._existing_network_and_project(client)
                self._progress("Henter LinuxServer VS Code...")
                client.images.pull(IMAGE)
                config = project + "_fjordcode-vscode-config"
                workspaces = project + "_fjordcode-workspaces"
                codex_home = project + "_fjordcode-home"
                for name in (config, workspaces, codex_home):
                    client.volumes.create(name=name)
                self._progress("Opretter isoleret VS Code-container...")
                container = client.containers.create(
                    IMAGE,
                    name=NAME,
                    network=network,
                    environment={
                        "PUID": "10001", "PGID": "10001", "TZ": "Europe/Copenhagen",
                        "SUBFOLDER": DESKTOP_PREFIX,
                        "TITLE": "FjordCode VS Code",
                        "CODEX_HOME": "/config/fjordcode-home/.codex",
                        "START_DOCKER": "false",
                    },
                    volumes={
                        config: {"bind": "/config", "mode": "rw"},
                        workspaces: {"bind": "/workspaces", "mode": "rw"},
                        codex_home: {"bind": "/config/fjordcode-home", "mode": "rw"},
                    },
                    ports={},
                    shm_size="1g",
                    cap_drop=["NET_RAW", "SYS_ADMIN"],
                    security_opt=["no-new-privileges:true"],
                    mem_limit="4g",
                    pids_limit=512,
                    restart_policy={"Name": "unless-stopped"},
                    labels={"dk.fjordhub.integration": "codex-desktop"},
                )
                container.start()
            self._progress("Installerer OpenAI Codex-udvidelsen...")
            try:
                installed = self._install_codex_extension(container)
            except Exception:
                LOG.exception("Automatic Codex extension installation failed")
                installed = False
            with self._lock:
                self._extension = "installed" if installed else "manual"
                self._phase = "ready"
                self._message = ("VS Code er klar." if installed else
                                 "VS Code kører, men Codex-udvidelsen skal muligvis installeres manuelt.")
        except Exception:
            LOG.exception("VS Code desktop installation failed")
            with self._lock:
                self._phase = "error"
                self._message = "Kunne ikke installere VS Code. Se FjordHub-loggen og prøv igen."
        finally:
            if client:
                try:
                    client.close()
                except Exception:
                    LOG.warning("Could not close Docker connection", exc_info=True)
            with self._lock:
                self._installing = False


desktop_manager = CodexDesktop()
