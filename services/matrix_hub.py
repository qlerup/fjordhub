"""Built-in, self-hosted Matrix/Element X integration.

Synapse and the bot are services, not FjordHub catalog apps. Secrets stay on the
installation's DATA_DIR, and containers only receive the mounts they need.
"""
import io
import logging
from contextlib import contextmanager
import json
import os
import re
import secrets
import tarfile
import threading
import time
import uuid
from pathlib import Path

import docker
import requests

from services.installer import _container_path_to_host_path

SYNAPSE_IMAGE = "matrixdotorg/synapse:latest"
BOT_IMAGE = "fjordhub-matrix-bot:1"
SYNAPSE_NAME = "fjordhub-matrix"
BOT_NAME = "fjordhub-matrix-bot"
NETWORK = "fjord-net"
DOMAIN_RE = re.compile(r"(?=.{4,253}$)[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+\Z")


@contextmanager
def managed_docker(**kwargs):
    """Close Docker SDK clients explicitly, even on errors."""
    client = docker.from_env(**kwargs)
    try:
        yield client
    finally:
        client.close()


class MatrixError(ValueError):
    pass


def validate_domain(value):
    if not isinstance(value, str):
        raise MatrixError("Angiv et fuldt Matrix-domæne.")
    domain = value.strip().lower()
    if not DOMAIN_RE.fullmatch(domain) or domain.endswith((".local", ".localhost", ".internal")):
        raise MatrixError("Brug et gyldigt offentligt domæne, fx matrix.ditdomæne.dk.")
    return domain


def validate_username(value):
    name = str(value or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9._=-]{1,30}", name):
        raise MatrixError("Brug 2-31 små bogstaver, tal, punktum, underscore eller bindestreg.")
    if name in {"fjordhub", "fjordhub-bot", "admin", "root", "synapse"}:
        raise MatrixError("Brugernavnet er reserveret.")
    return name


class MatrixHub:
    def __init__(self, data_dir):
        self.root = Path(data_dir) / "matrix"
        self.state_file = self.root / "config.json"
        self.bot_dir = self.root / "bot"
        self._lock = threading.RLock()

    @staticmethod
    def _save(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(path.parent, 0o700)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
        os.chmod(temporary, 0o600)
        temporary.replace(path)

    @staticmethod
    def _load(path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _state(self):
        return self._load(self.state_file)

    def _save_state(self, **changes):
        with self._lock:
            current = self._state()
            current.update(changes)
            self._save(self.state_file, current)
            return current

    @staticmethod
    def _host_dir(local_dir):
        host_path = _container_path_to_host_path(local_dir)
        if not host_path or not Path(host_path).is_absolute():
            raise MatrixError("FjordHubs DATA_DIR skal være et vedvarende bind-mount på Docker-værten.")
        return host_path

    @staticmethod
    def _container_status(client, name):
        try:
            container = client.containers.get(name)
            return container.status
        except docker.errors.NotFound:
            return "not_installed"

    @staticmethod
    def _installer_active():
        return any(t.name == "fjordhub-matrix-installer" and t.is_alive()
                   for t in threading.enumerate())

    def status(self):
        data = self._state()
        if not isinstance(data, dict):
            data = {}
        phase = data.get("phase", "not_installed")
        message = data.get("message", "")
        if phase == "installing" and not self._installer_active() and (
                time.time() - float(data.get("started_at", 0)) > 20):
            phase = "error"
            message = "Installationen blev afbrudt. Prøv igen med samme domæne."
        server = "unavailable"
        bot = "unavailable"
        if phase != "not_installed":
            try:
                with managed_docker(timeout=5) as client:
                    server = self._container_status(client, SYNAPSE_NAME)
                    bot = self._container_status(client, BOT_NAME)
            except Exception:
                logging.getLogger(__name__).warning("Matrix runtime status unavailable", exc_info=True)
        runtime = self._load(self.bot_dir / "health.json")
        return {
            "domain": data.get("domain", ""),
            "url": "https://" + data["domain"] if data.get("domain") else "",
            "phase": phase,
            "message": message,
            "server": server, "bot": bot,
            "bot_update": data.get("bot_update", "idle"),
            "bot_update_message": data.get("bot_update_message", ""),
            "bot_ready": (bot == "running" and
                          time.time() - float(runtime.get("updated", 0)) < 120 and
                          runtime.get("connected", False)),
            "bot_identity": runtime.get("identity", {"status":"pending", "message":"Opdatér botten for automatisk enhedsverificering."}),
            "update_users": self._load(self.bot_dir / "config.json").get("update_users", []),
            "users": sorted(self._load(self.bot_dir / "config.json").get("allowed_users", [])),
            "push": "Element X App Store → Elements pushgateway → Apple APNs",
        }

    def begin_install(self, domain, monitor_token):
        domain = validate_domain(domain)
        with self._lock:
            old = self._state()
            if old.get("domain") and old["domain"] != domain:
                raise MatrixError("Matrix-domænet kan ikke ændres efter installation. Bevar eksisterende identiteter og data.")
            if old.get("phase") == "installing" and (
                    self._installer_active() or time.time() - float(old.get("started_at", 0)) < 20):
                raise MatrixError("Matrix-installationen kører allerede.")
            if old.get("phase") == "ready":
                raise MatrixError("Matrix er allerede installeret.")
            self._save_state(domain=domain, phase="installing", message="Klargør Matrix...", started_at=time.time())
        # A failed installation is deliberately resumable on the same domain.
        worker = threading.Thread(target=self._install, args=(domain, monitor_token), daemon=True,
                                  name="fjordhub-matrix-installer")
        worker.start()

    def _install(self, domain, monitor_token):
        try:
            self._install_containers(domain, monitor_token)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Matrix deployment failed")
            self._save_state(phase="error", message="Installation mislykkedes. Kontrollér Docker-logfilerne og prøv igen.")
        else:
            self._save_state(phase="ready", message="Server og bot er installeret. Opret en Matrix-bruger og forbind Element X.")

    def _install_containers(self, domain, monitor_token):
        self.root.mkdir(parents=True, exist_ok=True)
        self.bot_dir.mkdir(parents=True, exist_ok=True)
        host_synapse = self._host_dir(self.root / "synapse")
        host_bot = self._host_dir(self.bot_dir)
        (self.root / "synapse").mkdir(parents=True, exist_ok=True)
        self._save_state(message="Henter Synapse og klargør serverdata...")
        with managed_docker(timeout=600) as client:
            try:
                client.networks.get(NETWORK)
            except docker.errors.NotFound:
                raise MatrixError("Docker-netværket fjord-net mangler. Start FjordHub med Docker Compose først.")
            client.images.pull(SYNAPSE_IMAGE)
            config_file = self.root / "synapse" / "homeserver.yaml"
            if not config_file.exists():
                client.containers.run(
                    SYNAPSE_IMAGE, command="generate",
                    environment={"SYNAPSE_SERVER_NAME": domain, "SYNAPSE_REPORT_STATS": "no"},
                    volumes={host_synapse: {"bind": "/data", "mode": "rw"}}, remove=True)
            self._configure_synapse(client, host_synapse, domain)
            self._save_state(message="Starter Matrix-serveren...")
            if self._container_status(client, SYNAPSE_NAME) == "not_installed":
                rule = ("Host(`" + domain + "`) && "
                        "(PathPrefix(`/_matrix/client`) || PathPrefix(`/_matrix/media`))")
                client.containers.run(
                    SYNAPSE_IMAGE, detach=True, name=SYNAPSE_NAME, network=NETWORK,
                    volumes={host_synapse: {"bind": "/data", "mode": "rw"}},
                    environment={"SYNAPSE_CONFIG_PATH": "/data/homeserver.yaml"},
                    restart_policy={"Name": "unless-stopped"},
                    labels={"dk.fjordhub.integration": "matrix",
                            "traefik.enable": "true", "traefik.docker.network": NETWORK,
                            "traefik.http.routers.fjordhub-matrix.rule": rule,
                            "traefik.http.routers.fjordhub-matrix.entrypoints": "web",
                            "traefik.http.services.fjordhub-matrix.loadbalancer.server.port": "8008"})
            else:
                existing = client.containers.get(SYNAPSE_NAME)
                if existing.status != "running":
                    existing.start()
            self._wait_for_synapse()
            self._save_state(message="Opretter krypteret Matrix-bot...")
            bot_cfg_path = self.bot_dir / "config.json"
            cfg = self._load(bot_cfg_path)
            if not cfg.get("password"):
                cfg = {"user_id": "@fjordhub-bot:" + domain,
                       "password": secrets.token_urlsafe(36), "allowed_users": [],
                       "monitor_token": monitor_token}
                self._save(bot_cfg_path, cfg)
            if not cfg.get("registered"):
                # A retried install may have registered the bot just before interruption.
                response = requests.post(
                    "http://" + SYNAPSE_NAME + ":8008/_matrix/client/v3/login",
                    json={"type": "m.login.password", "identifier": {
                        "type": "m.id.user", "user": cfg["user_id"]},
                        "password": cfg["password"]}, timeout=10)
                if not response.ok:
                    server = client.containers.get(SYNAPSE_NAME)
                    command = ["register_new_matrix_user", "-c", "/data/homeserver.yaml",
                               "-u", "fjordhub-bot", "-p", cfg["password"],
                               "--no-admin", "http://127.0.0.1:8008"]
                    result = server.exec_run(command)
                    if result.exit_code != 0:
                        raise MatrixError("Kunne ikke oprette bot-kontoen. Kontrollér Synapse-loggen.")
                cfg["registered"] = True
                self._save(bot_cfg_path, cfg)
            if monitor_token and not cfg.get("monitor_token"):
                cfg["monitor_token"] = monitor_token
                self._save(bot_cfg_path, cfg)
            self._save_state(message="Bygger den krypterede FjordHub-bot...")
            self._build_bot_image(client)
            if self._container_status(client, BOT_NAME) == "not_installed":
                client.containers.run(
                    BOT_IMAGE, detach=True, name=BOT_NAME, network=NETWORK,
                    volumes={host_bot: {"bind": "/config", "mode": "rw"}},
                    restart_policy={"Name": "unless-stopped"},
                    environment={"MATRIX_HOMESERVER": "http://" + SYNAPSE_NAME + ":8008",
                                 "FJORDHUB_RESOURCE_API": "http://fjordhub:8080/api/integrations/v1/resources"},
                    labels={"dk.fjordhub.integration": "matrix"})
            else:
                existing = client.containers.get(BOT_NAME)
                if existing.status != "running":
                    existing.start()

    @staticmethod
    def _configure_synapse(client, host_synapse, domain):
        script = """
import os, yaml
p = '/data/homeserver.yaml'
with open(p, encoding='utf-8') as f: config = yaml.safe_load(f)
assert config['server_name'] == os.environ['MATRIX_DOMAIN'], 'Matrix identity mismatch'
config['public_baseurl'] = 'https://' + config['server_name'] + '/'
config['enable_registration'] = False
config['report_stats'] = False
config['federation_domain_whitelist'] = []
config['url_preview_enabled'] = False
config.setdefault('registration_shared_secret', os.environ['REG_SECRET'])
for listener in config.get('listeners', []):
    if listener.get('type') == 'http':
        listener['x_forwarded'] = True
        for resource in listener.get('resources', []):
            resource['names'] = ['client']
with open(p, 'w', encoding='utf-8') as f: yaml.safe_dump(config, f, sort_keys=False)
"""
        secret = secrets.token_urlsafe(40)
        client.containers.run(
            SYNAPSE_IMAGE, command=[], entrypoint=["python", "-c", script],
            environment={"MATRIX_DOMAIN": domain, "REG_SECRET": secret},
            volumes={host_synapse: {"bind": "/data", "mode": "rw"}}, remove=True)

    @staticmethod
    def _wait_for_synapse():
        for _ in range(80):
            try:
                response = requests.get("http://" + SYNAPSE_NAME + ":8008/_matrix/client/versions", timeout=2)
                if response.ok:
                    return
            except requests.RequestException:
                pass
            time.sleep(2)
        raise MatrixError("Matrix-serveren blev ikke klar. Kontrollér Synapse-containeren.")

    @staticmethod
    def _build_bot_image(client):
        root = Path(__file__).resolve().parent
        bundle = io.BytesIO()
        with tarfile.open(fileobj=bundle, mode="w") as archive:
            for filename in ("matrix_bot.py", "bot_queries.py", "bot_identity.py", "matrix_bot.Dockerfile"):
                data = (root / filename).read_bytes()
                item = tarfile.TarInfo("Dockerfile" if filename.endswith(".Dockerfile") else filename)
                item.size = len(data)
                archive.addfile(item, io.BytesIO(data))
        bundle.seek(0)
        client.images.build(fileobj=bundle, custom_context=True, tag=BOT_IMAGE, rm=True, pull=False)

    def update_bot(self):
        """Rebuild bot after FjordHub code updates; keep data and Matrix keys."""
        with self._lock:
            state = self._state()
            if state.get("phase") != "ready":
                raise MatrixError("Installér Matrix først.")
            if state.get("bot_update") == "running" and (
                    self._installer_active() or
                    time.time() - float(state.get("bot_update_started_at", 0)) < 600):
                raise MatrixError("En Matrix-opdatering er allerede i gang.")
            self._save_state(bot_update="running", bot_update_started_at=time.time(),
                             bot_update_message="Bygger ny bot...")
        threading.Thread(target=self._update_bot, daemon=True,
                         name="fjordhub-matrix-installer").start()

    def _update_bot(self):
        try:
            host_bot = self._host_dir(self.bot_dir)
            with managed_docker(timeout=600) as client:
                old = client.containers.get(BOT_NAME)
                if old.labels.get("dk.fjordhub.integration") != "matrix":
                    raise MatrixError("Bot-containeren tilhører ikke FjordHub.")
                old_image = old.image.id
                self._build_bot_image(client)  # Fail before stopping the old bot.
                configuration = {
                    "detach": True, "name": BOT_NAME, "network": NETWORK,
                    "volumes": {host_bot: {"bind": "/config", "mode": "rw"}},
                    "restart_policy": {"Name": "unless-stopped"},
                    "environment": {
                        "MATRIX_HOMESERVER": "http://" + SYNAPSE_NAME + ":8008",
                        "FJORDHUB_RESOURCE_API": "http://fjordhub:8080/api/integrations/v1/resources"},
                    "labels": {"dk.fjordhub.integration": "matrix"},
                }
                old.stop(timeout=15)
                old.remove()
                try:
                    client.containers.run(BOT_IMAGE, **configuration)
                except Exception:
                    logging.getLogger(__name__).exception("Bot restart failed; restoring old image")
                    client.containers.run(old_image, **configuration)
                    raise
        except Exception:
            logging.getLogger(__name__).exception("Matrix bot upgrade failed")
            self._save_state(bot_update="error",
                             bot_update_message="Botopdatering mislykkedes. Kontrollér Docker-loggen.")
        else:
            self._save_state(bot_update="idle",
                             bot_update_message="Botten er opdateret. Krypteringsnøgler er bevaret.")

    def create_user(self, username):
        username = validate_username(username)
        state = self._state()
        if state.get("phase") != "ready":
            raise MatrixError("Installér Matrix først.")
        password = secrets.token_urlsafe(27)
        with self._lock, managed_docker(timeout=30) as client:
            container = client.containers.get(SYNAPSE_NAME)
            if container.status != "running":
                raise MatrixError("Matrix-serveren kører ikke.")
            result = container.exec_run(
                ["register_new_matrix_user", "-c", "/data/homeserver.yaml",
                 "-u", username, "-p", password, "--no-admin", "http://127.0.0.1:8008"])
            if result.exit_code != 0:
                raise MatrixError("Kunne ikke oprette brugeren. Måske findes brugernavnet allerede.")
            matrix_id = "@" + username + ":" + state["domain"]
            cfg_path = self.bot_dir / "config.json"
            cfg = self._load(cfg_path)
            cfg["allowed_users"] = sorted(set(cfg.get("allowed_users", [])) | {matrix_id})
            self._save(cfg_path, cfg)
            return {"user_id": matrix_id, "password": password, "url": "https://" + state["domain"]}

    def send_test(self, user_id):
        if not isinstance(user_id, str):
            raise MatrixError("Vælg en Matrix-bruger.")
        allowed = self._load(self.bot_dir / "config.json").get("allowed_users", [])
        if user_id not in allowed:
            raise MatrixError("Brugeren er ikke tilknyttet.")
        queue = self.bot_dir / "outbox"
        queue.mkdir(parents=True, exist_ok=True)
        file = queue / (uuid.uuid4().hex + ".json")
        self._save(file, {"recipient": user_id,
                          "text": "✅ FjordHub-test: Matrix-beskeder fungerer. Lås din iPhone for at kontrollere push."})
        return True
