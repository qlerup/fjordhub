"""Cloudflare DNS and published tunnel routes for the hub administrator."""
import base64
import copy
import hashlib
import ipaddress
import re
import sqlite3
from contextlib import closing
from urllib.parse import urlsplit

import requests
from cryptography.fernet import Fernet, InvalidToken


class CloudflareError(ValueError):
    pass


def origin_options(data):
    """Validate explicit per-route overrides; null restores tunnel defaults."""
    if not isinstance(data, dict) or set(data) - {'noTLSVerify', 'originServerName', 'httpHostHeader'}:
        raise CloudflareError('Ugyldige forbindelsesindstillinger.')
    for key, value in data.items():
        if value is None:
            continue
        if key == 'noTLSVerify':
            if type(value) is not bool:
                raise CloudflareError('Certifikatkontrol skal være til eller fra.')
        elif not isinstance(value, str) or not value or len(value) > 255 or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value) or any(c in value for c in '/\\@?#'):
            raise CloudflareError('Angiv et gyldigt servernavn eller en Host-header uden protokol og sti.')
    return data


def service_address(value):
    try:
        parsed = urlsplit(value) if isinstance(value, str) else None
        if not parsed or parsed.scheme not in {'http','https','tcp','ssh','rdp','smb'} or not parsed.hostname or parsed.username or parsed.password or any(c.isspace() for c in value):
            raise ValueError()
        if parsed.port is not None and not 1 <= parsed.port <= 65535:
            raise ValueError()
    except (TypeError, ValueError):
        raise CloudflareError('Angiv en gyldig lokal adresse og port.') from None
    return value


def identifier(value):
    value = str(value or '')
    if not re.fullmatch(r'[a-fA-F0-9-]{20,40}', value):
        raise CloudflareError('Ugyldigt Cloudflare-id.')
    return value


def hostname(value, zone=None):
    value = str(value or '').strip().rstrip('.').lower()
    if zone and value == '@':
        return zone
    if zone and '.' not in value and value != zone:
        value += '.' + zone
    try:
        value = value.encode('idna').decode('ascii')
    except UnicodeError:
        raise CloudflareError('Ugyldigt domænenavn.') from None
    labels = value.split('.')
    if len(value) > 253 or len(labels) < 2 or any(
        not re.fullmatch(r'(?:[a-z0-9_](?:[a-z0-9_-]{0,61}[a-z0-9_])?|\*)', label)
        for label in labels
    ):
        raise CloudflareError('Indtast et gyldigt domænenavn.')
    if zone and value != zone and not value.endswith('.' + zone):
        raise CloudflareError('Navnet skal høre til det valgte domæne.')
    return value


class CloudflareAPI:
    def __init__(self, token):
        self.token = token

    def call(self, method, path, **kwargs):
        try:
            response = requests.request(method, 'https://api.cloudflare.com/client/v4' + path,
                headers={'Authorization': 'Bearer ' + self.token}, timeout=(5, 25),
                allow_redirects=False, **kwargs)
            data = response.json()
        except (requests.RequestException, ValueError):
            raise CloudflareError('Cloudflare kunne ikke kontaktes. Prøv igen.') from None
        if not response.ok or not isinstance(data, dict) or data.get('success') is not True:
            # Do not forward upstream text: it may contain credentials or request values.
            codes = ', '.join(str(e.get('code')) for e in data.get('errors', []) if isinstance(e, dict)) if isinstance(data, dict) else ''
            hint = 'Kontrollér token og rettigheder.' if response.status_code in (401, 403) else 'Kontrollér felterne og prøv igen.'
            if response.status_code == 429:
                hint = 'For mange forespørgsler. Vent lidt og prøv igen.'
            raise CloudflareError(f'Cloudflare afviste forespørgslen ({response.status_code}{": " + codes if codes else ""}). {hint}')
        return data

    def all(self, path, **params):
        result, page = [], 1
        while True:
            data = self.call('GET', path, params={**params, 'page': page, 'per_page': 100})
            items = data.get('result') or []
            result.extend(items)
            pages = (data.get('result_info') or {}).get('total_pages')
            if (pages is not None and page >= pages) or (pages is None and len(items) < 100):
                return result
            page += 1
            if page > 1000:
                raise CloudflareError('For mange resultater fra Cloudflare.')


class CloudflareService:
    def __init__(self, db_path, secret):
        self.db_path = str(db_path)
        self.cipher = Fernet(base64.urlsafe_b64encode(hashlib.sha256((str(secret) + ':cloudflare').encode()).digest()))
        with closing(self.conn()) as db, db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS cloudflare_domains (
                    id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
                    zone_id TEXT NOT NULL, account_id TEXT NOT NULL, token TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS cloudflare_preferences (
                    id INTEGER PRIMARY KEY CHECK(id=1), enabled INTEGER NOT NULL DEFAULT 0
                );
                INSERT OR IGNORE INTO cloudflare_preferences(id,enabled) VALUES(1,0);
            ''')
            if 'label' not in {row['name'] for row in db.execute('PRAGMA table_info(cloudflare_domains)')}:
                db.execute("ALTER TABLE cloudflare_domains ADD COLUMN label TEXT NOT NULL DEFAULT ''")

    def conn(self):
        db = sqlite3.connect(self.db_path, timeout=40)
        db.row_factory = sqlite3.Row
        return db

    def settings(self):
        with closing(self.conn()) as db:
            return {'enabled': bool(db.execute('SELECT enabled FROM cloudflare_preferences WHERE id=1').fetchone()[0]),
                    'domains': [dict(r) for r in db.execute("SELECT id,name,zone_id,account_id,COALESCE(NULLIF(label,''),name) AS label FROM cloudflare_domains ORDER BY label,name")]}

    def enable(self, enabled):
        if not isinstance(enabled, bool):
            raise CloudflareError('Aktivering skal være ja eller nej.')
        with closing(self.conn()) as db, db:
            db.execute('UPDATE cloudflare_preferences SET enabled=? WHERE id=1', (int(enabled),))

    def require_enabled(self):
        if not self.settings()['enabled']:
            raise CloudflareError('Slå Cloudflare-administration til først.')

    def connect(self, name, token, label=None):
        self.require_enabled()
        name = hostname(name) if name else None
        if label is not None:
            if not isinstance(label,str) or not label.strip() or len(label.strip())>80 or any(ord(c)<32 for c in label):
                raise CloudflareError('Giv forbindelsen et navn på højst 80 tegn.')
            label=label.strip()
        if not isinstance(token, str) or not token.strip() or len(token) > 2048 or any(c.isspace() for c in token.strip()):
            raise CloudflareError('Indtast et gyldigt Cloudflare API-token.')
        token = token.strip()
        api = CloudflareAPI(token)
        zones = api.all('/zones', **({'name':name} if name else {}))
        zones = [z for z in zones if isinstance(z,dict) and isinstance(z.get('name'),str)
                 and (name is None or z['name'].lower() == name)]
        if name is None and len(zones)>1:
            return {'selection_required':True,'choices':sorted({hostname(z['name']) for z in zones})}
        if len(zones) != 1:
            raise CloudflareError('Domænet blev ikke fundet. Tokenet skal have Zone Read og DNS Edit for domænet.')
        zone = zones[0]
        name = hostname(zone['name'])
        zone_id, account_id = identifier(zone['id']), identifier(zone['account']['id'])
        api.call('GET', f'/zones/{zone_id}/dns_records', params={'per_page': 1})
        encrypted = self.cipher.encrypt(token.encode()).decode()
        with closing(self.conn()) as db, db:
            db.execute('INSERT INTO cloudflare_domains(name,zone_id,account_id,token,label) VALUES(?,?,?,?,?) '
                'ON CONFLICT(name) DO UPDATE SET zone_id=excluded.zone_id,account_id=excluded.account_id,token=excluded.token,'
                "label=COALESCE(?,NULLIF(cloudflare_domains.label,''),excluded.name)",
                (name, zone_id, account_id, encrypted,label or name,label))
        return {'connected_domain':name}

    def disconnect(self, domain_id):
        with closing(self.conn()) as db, db:
            db.execute('DELETE FROM cloudflare_domains WHERE id=?', (domain_id,))

    def domain(self, domain_id):
        self.require_enabled()
        with closing(self.conn()) as db:
            row = db.execute('SELECT * FROM cloudflare_domains WHERE id=?', (domain_id,)).fetchone()
        if not row:
            raise CloudflareError('Domænet er ikke tilknyttet.')
        domain = dict(row)
        try:
            api = CloudflareAPI(self.cipher.decrypt(domain.pop('token').encode()).decode())
        except InvalidToken:
            raise CloudflareError('Tokenet kunne ikke dekrypteres. Tilknyt domænet igen.') from None
        return domain, api

    def overview(self, domain_id):
        domain, api = self.domain(domain_id)
        records = api.all(f'/zones/{domain["zone_id"]}/dns_records')
        tunnels, warnings = [], []
        try:
            for tunnel in api.all(f'/accounts/{domain["account_id"]}/cfd_tunnel', is_deleted='false'):
                item = {k: tunnel.get(k) for k in ('id', 'name', 'status', 'config_src')}
                item['routes'] = []
                if tunnel.get('config_src') == 'cloudflare':
                    try:
                        config = api.call('GET', f'/accounts/{domain["account_id"]}/cfd_tunnel/{identifier(tunnel["id"])}/configurations')['result']
                        item['version'] = config.get('version')
                        item['routes'] = [{**{k: r[k] for k in ('hostname', 'service', 'path') if k in r},
                            'originRequest': {k: v for k, v in (r.get('originRequest') or {}).items() if k in {'noTLSVerify','originServerName','httpHostHeader'}}}
                            for r in config.get('config', {}).get('ingress', [])
                            if r.get('hostname') and (r['hostname'] == domain['name'] or r['hostname'].endswith('.' + domain['name']))]
                    except CloudflareError as exc:
                        item['error'] = str(exc)
                tunnels.append(item)
        except CloudflareError as exc:
            warnings.append('Tunneloversigt er utilgængelig. DNS virker stadig. ' + str(exc))
        return {'domain': domain, 'records': records, 'tunnels': tunnels, 'warnings': warnings}

    def record_payload(self, data, zone):
        if not isinstance(data, dict):
            raise CloudflareError('Ugyldig DNS-post.')
        kind = str(data.get('type', '')).upper()
        if kind not in {'A','AAAA','CNAME','TXT','MX','SRV','CAA','NS','HTTPS','SVCB','TLSA','SSHFP','DS','DNSKEY','NAPTR','PTR','URI','CERT','SMIMEA','LOC'}:
            raise CloudflareError('Vælg en understøttet DNS-type.')
        payload = {'type': kind, 'name': hostname(data.get('name'), zone)}
        ttl = data.get('ttl', 1)
        if isinstance(ttl, bool) or not isinstance(ttl, int) or (ttl != 1 and not 60 <= ttl <= 86400):
            raise CloudflareError('TTL skal være 1 (automatisk) eller 60–86400 sekunder.')
        payload['ttl'] = ttl
        if kind in {'A', 'AAAA', 'CNAME'}:
            if not isinstance(data.get('proxied', False), bool):
                raise CloudflareError('Proxy skal være ja eller nej.')
            payload['proxied'] = data.get('proxied', False)
            if payload['proxied']:
                payload['ttl'] = 1
        if 'data' in data:
            if not isinstance(data['data'], dict):
                raise CloudflareError('Data skal være et JSON-objekt.')
            payload['data'] = data['data']
        else:
            content = data.get('content')
            if not isinstance(content, str) or not content or len(content) > 65536:
                raise CloudflareError('Indtast postens værdi.')
            if kind in {'A','AAAA'}:
                try:
                    address = ipaddress.ip_address(content)
                    if address.version != (4 if kind == 'A' else 6):
                        raise ValueError()
                except ValueError:
                    raise CloudflareError('IP-adressen passer ikke til postens type.') from None
            payload['content'] = content
        if kind in {'MX','URI'}:
            priority = data.get('priority', 10)
            if isinstance(priority, bool) or not isinstance(priority, int) or not 0 <= priority <= 65535:
                raise CloudflareError('Prioritet skal være 0–65535.')
            payload['priority'] = priority
        if 'comment' in data:
            if not isinstance(data['comment'], str) or len(data['comment']) > 500:
                raise CloudflareError('Kommentaren må højst være 500 tegn.')
            payload['comment'] = data['comment']
        return payload

    def save_record(self, domain_id, data, record_id=None):
        domain, api = self.domain(domain_id)
        path = f'/zones/{domain["zone_id"]}/dns_records'
        if record_id:
            path += '/' + identifier(record_id)
            existing = api.call('GET', path)['result']
            # Changing type may leave incompatible upstream fields on a PATCH.
            if existing['type'] != data.get('type'):
                raise CloudflareError('Opret en ny post for at ændre DNS-type.')
        return api.call('PATCH' if record_id else 'POST', path,
            json=self.record_payload(data, domain['name']))['result']

    def delete_record(self, domain_id, record_id):
        domain, api = self.domain(domain_id)
        api.call('DELETE', f'/zones/{domain["zone_id"]}/dns_records/{identifier(record_id)}')

    def create_address(self,domain_id,data):
        if data.get('kind')=='dns':
            return self.save_record(domain_id,data)
        if data.get('kind')!='tunnel':raise CloudflareError('Vælg DNS-post eller tunneladresse.')
        domain,api=self.domain(domain_id)
        name=hostname(data.get('name'),domain['name'])
        tunnel=identifier(data.get('tunnel_id'))
        service=service_address(data.get('service',''))
        overrides = origin_options(data['originRequest']) if 'originRequest' in data else None
        path=f'/accounts/{domain["account_id"]}/cfd_tunnel/{tunnel}/configurations'
        current=api.call('GET',path)['result']
        if current.get('source')=='local':raise CloudflareError('Lokalt styrede tunneler redigeres i deres konfigurationsfil.')
        if type(data.get('version')) is not int or current.get('version')!=data['version']:
            raise CloudflareError('Tunnelopsætningen er ændret. Genindlæs og prøv igen.')
        ingress=(current.get('config') or {}).get('ingress',[])
        if any(r.get('hostname')==name for r in ingress):raise CloudflareError('Tunneladressen findes allerede. Rediger den i oversigten.')
        if not ingress or ingress[-1].get('hostname'):raise CloudflareError('Tunnelen mangler sin afsluttende standardregel.')
        dns_path=f'/zones/{domain["zone_id"]}/dns_records'
        if api.all(dns_path,name=name):raise CloudflareError('Der findes allerede en DNS-post på adressen. Rediger den i oversigten.')
        record=api.call('POST',dns_path,json={'type':'CNAME','name':name,'content':tunnel+'.cfargotunnel.com','proxied':True,'ttl':1})['result']
        try:
            record_id=identifier(record.get('id'))
        except CloudflareError:
            raise CloudflareError('DNS-posten blev oprettet, men svaret kunne ikke bekræftes. Genindlæs oversigten, før du prøver igen.') from None
        try:
            self.route(domain_id,tunnel,{'hostname':name,'service':service,'version':data['version'],
                **({'originRequest':overrides} if overrides is not None else {})})
        except CloudflareError as exc:
            try:api.call('DELETE',dns_path+'/'+record_id)
            except CloudflareError:
                raise CloudflareError('Tunnelreglen kunne ikke gemmes, og DNS-posten kunne ikke fjernes igen. Genindlæs oversigten og kontrollér adressen. '+str(exc)) from None
            raise CloudflareError('Tunnelreglen kunne ikke bekræftes. Den nye DNS-post er fjernet igen. Genindlæs tunneloversigten, før du prøver igen. '+str(exc)) from None
        return record

    def route(self, domain_id, tunnel_id, data, delete=False):
        domain, api = self.domain(domain_id)
        tunnel_id = identifier(tunnel_id)
        name = hostname(data.get('hostname'), domain['name'])
        service = data.get('service', '')
        overrides = None
        if not delete:
            service = service_address(service)
            if 'originRequest' in data:
                overrides = origin_options(data['originRequest'])
        path = f'/accounts/{domain["account_id"]}/cfd_tunnel/{tunnel_id}/configurations'
        # Serialize writes from this hub across workers. Version protects edits made
        # since the overview was loaded; external edits during a PUT remain an API limitation.
        with closing(self.conn()) as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                current = api.call('GET', path)['result']
                if current.get('source') == 'local':
                    raise CloudflareError('Lokalt styrede tunneler skal ændres i deres konfigurationsfil.')
                if data.get('version') is None or current.get('version') != data['version']:
                    raise CloudflareError('Tunnelopsætningen er ændret. Genindlæs og prøv igen.')
                config = copy.deepcopy(current.get('config') or {})
                ingress = config.get('ingress', [])
                matches = [r for r in ingress if r.get('hostname') == name]
                if len(matches) > 1 or any(r.get('path') for r in matches):
                    raise CloudflareError('Dette værtsnavn har stibaserede regler. Rediger det hos Cloudflare.')
                if delete and not matches:
                    raise CloudflareError('Tunnelreglen findes ikke længere. Genindlæs oversigten.')
                if delete:
                    config['ingress'] = [r for r in ingress if r.get('hostname') != name]
                elif matches:
                    matches[0]['service'] = service
                    target = matches[0]
                else:
                    if not ingress or ingress[-1].get('hostname'):
                        raise CloudflareError('Tunnelen mangler sin afsluttende standardregel. Ret den hos Cloudflare.')
                    target = {'hostname': name, 'service': service}
                    ingress.insert(len(ingress)-1, target)
                if not delete and overrides is not None:
                    options = target.setdefault('originRequest', {})
                    for key, value in overrides.items():
                        if value is None:
                            options.pop(key, None)
                        else:
                            options[key] = value
                    if not options:
                        target.pop('originRequest', None)
                api.call('PUT', path, json={'config': config})
            finally:
                db.rollback()
