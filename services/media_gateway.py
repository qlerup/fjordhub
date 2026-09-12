"""FjordHub-owned Caddy gateway. No host paths or shell scripts required."""
import io
import json
import re
import secrets
import tarfile
import threading
import time
from urllib.parse import urlsplit

import docker
import requests

NAME = 'fjordhub-media-gateway'
LABEL = 'dk.fjordhub.media-gateway'
STATE = '__media_gateway__'


def domain(value):
    value = str(value or '').strip().lower()
    parsed = urlsplit(value if '://' in value else 'https://' + value)
    host = parsed.hostname or ''
    if (parsed.scheme != 'https' or parsed.netloc != host or parsed.path not in ('', '/')
            or parsed.query or parsed.fragment or len(host) > 253
            or not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}', host)):
        raise ValueError('Indtast et offentligt domæne uden port eller sti, fx media.ditdomæne.dk.')
    return host


def caddyfile(host, upstream):
    # The domain is validated; upstream is a Docker-generated container IP.
    return f'''{host} {{
    handle /media/* {{
        reverse_proxy {upstream}
    }}
    handle {{
        respond "Not found" 404
    }}
}}
'''


def configure_file(container, contents):
    data = contents.encode()
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode='w') as tar:
        item = tarfile.TarInfo('Caddyfile'); item.size = len(data); item.mode = 0o644
        tar.addfile(item, io.BytesIO(data))
    if not container.put_archive('/etc/caddy', archive.getvalue()):
        raise RuntimeError('Kunne ikke gemme gateway-konfigurationen.')


def flix(container, action, payload=None):
    # Use the existing Docker authority, not user cookies or an extra shared secret.
    code = '''import os,sqlite3,json
from app import media
def db():
 c=sqlite3.connect(os.path.join(os.environ.get('DATA_DIR','/data'),'fjordflix.db'),timeout=15)
 c.row_factory=sqlite3.Row
 return c
if not hasattr(media,'prepare_probe'): raise RuntimeError('Opdater FjordFlix først')
media.init(db)
'''
    if action == 'probe':
        code += f'media.prepare_probe({payload[0]!r},{payload[1]!r},db)\n'
    elif action == 'activate':
        code += f'media.save_config({payload[0]!r},{payload[1]!r},db)\n'
    code += "print(json.dumps(dict(zip(('media_url','web_url'),media.config()))))"
    result = container.exec_run(['python', '-c', code])
    if result.exit_code:
        raise RuntimeError('FjordFlix kunne ikke konfigureres. Opdater FjordFlix og kontrollér at appen kører.')
    return json.loads(result.output.decode().strip().splitlines()[-1])


class MediaGateway:
    def __init__(self, manager, state):
        self.manager, self.state = manager, state
        self.lock = threading.Lock()
        self.running = False

    def status(self):
        value = self.state.get(STATE)
        if value.get('waiting_install') and self.state.get('fjordflix').get('state') == 'failed':
            value.update(waiting_install=False, phase='Installationen af FjordFlix fejlede. Ret den før videoopsætning.')
        if value.get('running') and not self.running:
            value.update(running=False, phase='Afbrudt af genstart. Kør guiden igen.')
        return value

    def save(self, **values):
        self.state._update(STATE, values)

    def start(self, app_def, host, web, mode):
        host = domain(host)
        web = 'https://' + domain(web)
        if host == domain(web):
            raise ValueError('Web og video skal bruge forskellige domæner.')
        if mode not in ('managed', 'existing'):
            raise ValueError('Ukendt gatewayvalg.')
        if not self.lock.acquire(blocking=False):
            raise ValueError('Opsætningen kører allerede.')
        self.running = True
        self.save(running=True, waiting_install=False, phase='Kontrollerer FjordFlix…', error='', domain=host, mode=mode)
        threading.Thread(target=self.run, args=(app_def, host, web, mode), daemon=True).start()

    def run(self, app_def, host, web, mode):
        try:
            client = self.manager.client
            if not client:
                raise RuntimeError('Ingen forbindelse til Docker.')
            app_container = client.containers.get(app_def['container_name'])
            current = flix(app_container, 'status')
            if current['media_url'] and current['media_url'] != 'https://' + host:
                raise RuntimeError('En anden videoadresse er aktiv. Deaktivér den i FjordFlix før du skifter domæne.')
            nonce = secrets.token_urlsafe(32)
            flix(app_container, 'probe', (host, nonce))
            if mode == 'managed':
                self.ensure_gateway(client, app_container, host)
            self.save(phase='Tester HTTPS og direkte forbindelse. Certifikatet kan tage et par minutter…')
            self.verify(host, nonce)
            self.save(phase='HTTPS virker. Aktiverer direkte video i FjordFlix…')
            flix(app_container, 'activate', ('https://' + host, web))
            self.save(phase='Direkte video er aktiveret. Genindlæs FjordFlix før afspilning.', active=True, error='')
        except Exception as exc:
            self.save(phase='Opsætningen blev ikke gennemført.', error=str(exc)[:600])
        finally:
            self.save(running=False)
            self.running = False
            self.lock.release()

    def ensure_gateway(self, client, app_container, host):
        try:
            gateway = client.containers.get(NAME)
        except docker.errors.NotFound:
            gateway = None
        if gateway and gateway.labels.get(LABEL) != '1':
            raise RuntimeError('Gateway-navnet bruges af en anden container. Den er ikke ændret.')
        if gateway and gateway.labels.get('dk.fjordhub.media-domain') != host:
            raise RuntimeError('FjordHubs gateway bruger et andet domæne. Den er ikke ændret.')
        for container in client.containers.list():
            if gateway and container.id == gateway.id:
                continue
            for bindings in container.attrs.get('NetworkSettings', {}).get('Ports', {}).values():
                if any(b.get('HostPort') in ('80','443') for b in (bindings or [])):
                    raise RuntimeError('Port 80 eller 443 bruges allerede. Vælg eksisterende HTTPS-indgang og konfigurér video-ruten dér.')
        app_container.reload()
        bindings = app_container.attrs['NetworkSettings']['Ports'].get('8080/tcp') or []
        bindings = [b for b in bindings if b.get('HostIp') in ('0.0.0.0', '')]
        if not bindings:
            raise RuntimeError('FjordFlix skal have sin web-port udgivet på Docker-værten.')
        port = int(bindings[0]['HostPort'])
        if not gateway:
            self.save(phase='Henter og installerer HTTPS-gateway…')
            client.images.pull('caddy:2')
            gateway = client.containers.create('caddy:2', name=NAME,
                command=['caddy','run','--config','/etc/caddy/Caddyfile','--adapter','caddyfile'],
                labels={LABEL:'1', 'dk.fjordhub.media-domain':host},
                ports={'80/tcp':80,'443/tcp':443}, extra_hosts={'host.docker.internal':'host-gateway'},
                volumes={NAME+'-data':{'bind':'/data','mode':'rw'}, NAME+'-config':{'bind':'/config','mode':'rw'}, NAME+'-etc':{'bind':'/etc/caddy','mode':'rw'}},
                restart_policy={'Name':'unless-stopped'})
        configure_file(gateway, caddyfile(host, f'host.docker.internal:{port}'))
        gateway.reload()
        if gateway.status == 'running':
            result = gateway.exec_run(['caddy','reload','--config','/etc/caddy/Caddyfile','--adapter','caddyfile'])
            if result.exit_code:
                raise RuntimeError('Gateway-konfigurationen kunne ikke indlæses.')
        else:
            try:
                gateway.start()
            except docker.errors.APIError:
                raise RuntimeError('Gatewayen kunne ikke starte. Kontrollér om en anden tjeneste bruger port 80 eller 443.')

    def verify(self, host, nonce):
        with requests.Session() as session:
            session.trust_env = False
            for _ in range(30):
                try:
                    response = session.get(f'https://{host}/media/connection-check', timeout=5, allow_redirects=False)
                    if 'cf-ray' in response.headers:
                        raise RuntimeError('Videodomænet bruger Cloudflare-proxy. Vælg DNS only og kør guiden igen.')
                    if response.status_code == 200 and response.json().get('nonce') == nonce:
                        return
                except (requests.RequestException, ValueError):
                    pass
                time.sleep(3)
        raise RuntimeError('HTTPS-testen kunne ikke nå FjordFlix. Kontrollér DNS only, offentlig IP, port 80/443 og routerens NAT loopback. Prøv derefter igen.')
