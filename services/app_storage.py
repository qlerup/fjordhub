"""Change an installed app's bind-mounted storage with verified copy or move."""
import copy
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import subprocess
import threading

from docker.types import Mount
from services.compose_env import build_compose_env
from services.storage_mount import MountRequired, pve_commands, volume_commands
from services.proxmox_storage import ProxmoxStorage


def host_path(value):
    if not isinstance(value, str) or len(value) > 1024:
        raise ValueError('Indtast en absolut mappesti på Docker-serveren.')
    value = value.strip()
    if not value.startswith('/') or any(c in value for c in "\r\n\x00$'\"\\,:"):
        raise ValueError('Brug en absolut mappesti uden specialtegn som $, citationstegn eller kolon.')
    path = PurePosixPath(value)
    if '..' in path.parts or len(path.parts) < 3 or path.parts[1] in ('proc', 'sys', 'dev', 'etc', 'bin', 'sbin', 'lib', 'usr', 'run'):
        raise ValueError('Vælg en særskilt mappe til appens filer, ikke en systemmappe.')
    if str(path).startswith('/var/lib/docker'):
        raise ValueError('Dockers interne mapper kan ikke vælges som filplacering.')
    return str(path)


def fields(app_def):
    return [f for step in app_def.get('setup_steps', []) for f in step.get('fields', [])
            if f.get('type') == 'path' and re.fullmatch(r'[A-Z][A-Z0-9_]*', f.get('key', ''))]


def patched_env(contents, key, destination):
    lines = contents.splitlines(keepends=True)
    pattern = re.compile(r'^\s*(?:export\s+)?' + re.escape(key) + r'\s*=')
    result, found = [], False
    for line in lines:
        if pattern.match(line):
            if not found:
                result.append(f"{key}='{destination}'\n")
            found = True
        else:
            result.append(line)
    if not found:
        if result and not result[-1].endswith('\n'):
            result.append('\n')
        result.append(f"{key}='{destination}'\n")
    return ''.join(result)


def without_sources(config):
    result = copy.deepcopy(config)
    for service in result.get('services', {}).values():
        for volume in service.get('volumes', []):
            if volume.get('type') == 'bind':
                volume['source'] = '<bind>'
    return result


class AppStorage:
    def __init__(self, manager, state):
        self.manager, self.state = manager, state
        self.lock = threading.RLock()
        self.active = set()
        self.proxmox = ProxmoxStorage()

    def storage_plan(self, storage_id, folder, size):
        plan = self.proxmox.selection(storage_id, folder, size)
        host_path(plan['destination'])
        status = self.folders('mount', plan['destination'])
        plan['ready'] = plan['configured'] and status['ready'] and status.get('mount_target') == plan['target']
        plan['commands'] = (volume_commands(plan['ctid'], plan['id'], plan['target'], plan['size_gib'] or 1)
                            if plan['needs_size'] else pve_commands(plan['ctid'],plan['disk'],plan['target']))
        plan['message'] = 'Lageret er tilsluttet og klar.' if plan['ready'] else 'Lageret skal tilsluttes FjordHubs LXC. Kør kommandoerne på PVE.'
        return plan

    def job(self, app_id):
        value = self.state.get(app_id).get('storage_job', {})
        if value.get('running') and app_id not in self.active:
            return {**value, 'interrupted': True,
                    'message': 'FjordHub blev genstartet under flytningen. Start ikke appen før placering og kopijob er kontrolleret.'}
        return value

    def busy(self, app_id):
        return bool(self.job(app_id).get('running'))

    def save(self, app_id, **patch):
        with self.lock:
            value = {**self.state.get(app_id).get('storage_job', {}), **patch}
            self.state.set_storage_job(app_id, value)

    def directory(self, app_def):
        directory = self.state.get_install_dir(app_def['id']) or self.manager._resolve_compose_dir(app_def)
        if not directory or not (Path(directory) / '.env').is_file():
            raise ValueError('Appen skal være installeret gennem FjordHub først.')
        return Path(directory)

    def compose(self, directory, args, extra=None, timeout=60):
        result = subprocess.run(['docker', 'compose', *args], cwd=str(directory),
                                env=build_compose_env(extra), capture_output=True, text=True, timeout=timeout)
        if result.returncode:
            # Compose output may contain interpolated secrets; never send it to the browser.
            raise RuntimeError('Docker Compose kunne ikke udføre handlingen. Kontrollér appens konfiguration og Docker-status.')
        return result.stdout

    def configuration(self, directory, extra=None):
        return json.loads(self.compose(directory, ['config', '--format', 'json'], extra))

    def mappings(self, app_def):
        directory = self.directory(app_def)
        definitions = fields(app_def)
        if not definitions:
            return directory, {}, []
        current = self.configuration(directory)
        markers = {f['key']: '/__fjordhub_storage_' + f['key'] for f in definitions}
        marked = self.configuration(directory, markers)
        result = []
        for field in definitions:
            matches = []
            for name, service in marked.get('services', {}).items():
                originals = {v.get('target'): v for v in current['services'][name].get('volumes', [])}
                for volume in service.get('volumes', []):
                    if volume.get('type') == 'bind' and volume.get('source') == markers[field['key']]:
                        original = originals.get(volume.get('target'), {})
                        if original.get('type') == 'bind':
                            matches.append({'service': name, 'target': volume['target'], 'source': original['source']})
            sources = {v['source'] for v in matches}
            if len(sources) == 1:
                result.append({'key': field['key'], 'label': field.get('label', field['key']),
                               'hint': field.get('hint', ''), 'path': sources.pop(), 'mounts': matches})
        return directory, current, result

    def describe(self, app_def):
        try:
            _, _, locations = self.mappings(app_def)
            error = ''
        except (ValueError, RuntimeError, OSError, subprocess.SubprocessError):
            locations, error = [], 'Filplaceringer kunne ikke læses. Appen skal være installeret, og Docker skal være tilgængelig.'
        return {'fields': [{k: v for k, v in row.items() if k != 'mounts'} for row in locations],
                'job': self.job(app_def['id']), 'error': error}

    def start(self, app_def, key, destination, expected, mode="copy"):
        if mode not in ("copy", "move"):
            raise ValueError("Vælg enten kopiér eller flyt.")
        destination = host_path(destination)
        app_id = app_def['id']
        with self.lock:
            if self.busy(app_id):
                raise ValueError('En flytning er allerede i gang eller kræver kontrol efter en genstart.')
            if not isinstance(key, str) or key not in {f['key'] for f in fields(app_def)}:
                raise ValueError('Ukendt filplacering.')
            if not isinstance(expected, str):
                raise ValueError('Genåbn indstillingerne og prøv igen.')
            selected = [PurePosixPath(host_path(expected)), PurePosixPath(destination)]
            for job in self.state.storage_jobs().values():
                if not job.get('running'):
                    continue
                for value in (job.get('source'), job.get('destination')):
                    if not value:
                        continue
                    occupied = PurePosixPath(value)
                    if any(p == occupied or p in occupied.parents or occupied in p.parents for p in selected):
                        raise ValueError('En anden flytning bruger denne mappe. Vent til den er færdig.')
            self.require_mount(destination)
            self.save(app_id, running=True, interrupted=False, message='Kontrollerer mapper og ledig plads…',
                      error='', mode=mode, key=key, source=expected, destination=destination, id=secrets.token_hex(8))
            self.active.add(app_id)
            threading.Thread(target=self.run, args=(app_def, key, destination, expected, mode), daemon=True).start()

    def folders(self, action='browse', value='', source='/'):
        client = self.manager.client
        if not client:
            raise RuntimeError('Docker er ikke tilgængelig.')
        hub = client.containers.get(os.environ.get('HOSTNAME', 'fjordhub'))
        script = Path(__file__).with_name('storage_browser.py').read_text(encoding='utf-8')
        worker = client.containers.create(hub.image.id, entrypoint=['python', '-c', script],
            command=[action, value], mounts=[Mount('/folder' if action == 'create' else '/host',
            source, type='bind', read_only=action != 'create')],
            network_disabled=True, read_only=True)
        try:
            worker.start()
            status = worker.wait(timeout=30)
            result = json.loads(worker.logs().decode('utf-8').strip().splitlines()[-1])
            if status.get('StatusCode') or result.get('error'):
                raise ValueError(result.get('error') or 'Mappen kunne ikke åbnes.')
            return result
        finally:
            worker.remove(force=True)

    def ensure_destination(self, destination):
        host_path(destination)
        self.require_mount(destination)
        location = self.folders('probe', destination)
        self.folders('create', location['relative'], location['ancestor'])

    def require_mount(self, destination):
        status = self.folders('mount', destination)
        if not status['ready']:
            raise MountRequired(status)

    def mount_guide(self, destination, ctid=None, disk=None):
        destination = host_path(destination)
        status = self.folders('mount', destination)
        ctid = ctid or os.environ.get('PROXMOX_CT_ID', '1000')
        disk = disk or os.environ.get('PROXMOX_STORAGE_PATH', '/mnt/pve/Storage-pool1')
        return {**status, 'ctid': str(ctid), 'disk': disk,
                'commands': pve_commands(ctid, disk, status['mount_target']) if status['required'] else ''}

    def helper(self, source, destination, mode, manifest_digest=''):
        client = self.manager.client
        if not client:
            raise RuntimeError('Docker er ikke tilgængelig.')
        hub = client.containers.get(os.environ.get('HOSTNAME', 'fjordhub'))
        script = Path(__file__).with_name('storage_copy.py').read_text(encoding='utf-8')
        worker = client.containers.create(hub.image.id, entrypoint=['python', '-c', script], command=[mode, manifest_digest],
            mounts=[Mount('/source', source, type='bind', read_only=mode != 'cleanup'),
                    Mount('/destination', destination, type='bind', read_only=mode == 'check')],
            network_disabled=True, read_only=True, labels={'dk.fjordhub.storage-copy': '1'})
        try:
            worker.start()
            # Poll rather than impose a short timeout on a large film library.
            import time
            while True:
                worker.reload()
                if worker.status in ('exited', 'dead'):
                    break
                time.sleep(1)
            output = worker.logs().decode('utf-8', errors='replace')
            try:
                result = json.loads(output.strip().splitlines()[-1])
            except (ValueError, IndexError):
                raise RuntimeError('Kopihjælperen kunne ikke gennemføre kontrollen.')
            if worker.attrs.get('State', {}).get('ExitCode') or result.get('error'):
                raise RuntimeError(result.get('error') or 'Kopiering fejlede.')
            return result
        finally:
            worker.remove(force=True)

    def run(self, app_def, key, destination, expected, mode="copy"):
        app_id = app_def['id']
        directory, old_env, new_env, running = None, None, None, []
        stopped, committed, cleanup_started = False, False, False
        try:
            directory, current, locations = self.mappings(app_def)
            location = next((row for row in locations if row['key'] == key), None)
            if not location or location['path'] != expected:
                raise ValueError('Placeringen er ændret. Genåbn indstillingerne og prøv igen.')
            source = host_path(location['path'])
            a, b = PurePosixPath(source), PurePosixPath(destination)
            if a == b or a in b.parents or b in a.parents:
                raise ValueError('Vælg en ny mappe uden for den gamle mappe.')
            proposed = self.configuration(directory, {key: destination})
            if without_sources(current) != without_sources(proposed):
                raise ValueError('Denne indstilling ændrer mere end en filplacering og skal tilpasses manuelt.')
            changed = []
            for name, service in current['services'].items():
                future = {v['target']: v for v in proposed['services'][name].get('volumes', [])}
                for volume in service.get('volumes', []):
                    other = future[volume['target']]
                    if volume.get('source') != other.get('source'):
                        if volume.get('source') != source or other.get('source') != destination:
                            raise ValueError('Indstillingen påvirker flere mapper. Skiftet er afbrudt.')
                        changed.append((name, volume['target']))
            if not changed:
                raise ValueError('Placeringen bruges ikke af appens aktive konfiguration.')
            old_env = (directory / '.env').read_text(encoding='utf-8')
            new_env = patched_env(old_env, key, destination)
            client = self.manager.client
            if not client:
                raise RuntimeError('Docker er ikke tilgængelig.')
            containers = client.containers.list(all=True, filters={'label': 'com.docker.compose.project=' + current['name']})
            for container in containers:
                service = container.labels.get('com.docker.compose.service')
                if service not in current['services']:
                    raise ValueError('Projektet indeholder en ukendt service. Kontrollér Compose-konfigurationen først.')
                for mapping in location['mounts']:
                    if service == mapping['service']:
                        actual = next((m for m in container.attrs.get('Mounts', []) if m.get('Destination') == mapping['target']), {})
                        if actual.get('Source') != source:
                            raise ValueError('Den installerede app bruger en anden mappe end konfigurationen. Skiftet er afbrudt.')
                if container.status == 'running':
                    running.append(service)
                elif container.status not in ('exited', 'created'):
                    raise ValueError('Appen skal være startet normalt eller stoppet før flytning.')
            # A destination used by another app must not be treated as an empty spare directory.
            for container in client.containers.list(all=True):
                for mount in container.attrs.get('Mounts', []):
                    if mount.get('Type') != 'bind':
                        continue
                    used = PurePosixPath(mount.get('Source', '/'))
                    if used == b or b in used.parents:
                        raise ValueError('Destinationen bruges allerede af en container.')
                    if (used == a or used in a.parents or a in used.parents) and container.labels.get('com.docker.compose.project') != current['name']:
                        raise ValueError('Kildemappen deles med en anden app. Flyt den manuelt med begge apps stoppet.')
            self.ensure_destination(destination)
            self.helper(source, destination, 'check')
            self.save(app_id, message='Pauser appen og kopierer filerne. Den gamle mappe bevares…')
            stopped = True
            self.compose(directory, ['stop'], timeout=180)
            copied = self.helper(source, destination, 'prepare-move' if mode == 'move' else 'copy')
            if mode == 'move':
                self.save(app_id, manifest_sha256=copied['manifest_sha256'])
            if (directory / '.env').read_text(encoding='utf-8') != old_env:
                raise ValueError('Konfigurationen blev ændret under kopieringen. Placeringen er ikke skiftet.')
            backup_dir = self.state.data_dir / 'storage-backups' / app_id
            backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            backup = backup_dir / (self.job(app_id)['id'] + '.env')
            with os.fdopen(os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w', encoding='utf-8') as out:
                out.write(old_env)
            temporary = directory / '.env.storage-new'
            temporary.write_text(new_env, encoding='utf-8'); temporary.chmod(0o600)
            temporary.replace(directory / '.env')
            committed = True
            self.save(app_id, message='Kopien er kontrolleret. Aktiverer den nye placering…')
            if running:
                self.compose(directory, ['up', '-d', '--no-build', '--pull', 'never', '--no-deps', '--force-recreate', '--wait', '--wait-timeout', '120', *sorted(set(running))], timeout=180)
            if mode == 'move':
                cleanup_started = True
                self.save(app_id, phase='cleanup', message='Den nye placering er aktiveret. Fjerner de kontrollerede originaler…')
                self.helper(source, destination, 'cleanup', copied['manifest_sha256'])
            self.save(app_id, running=False, phase='complete', message=(
                'Filerne er flyttet. Den gamle mappe er nu tom.' if mode == 'move' else
                'Placeringen er ændret. Den gamle mappe er bevaret og kan ryddes op efter kontrol.'), error='')
        except Exception as exc:
            if cleanup_started:
                self.save(app_id, running=False, phase='cleanup_incomplete',
                          message='Den nye placering bruges. Oprydningen i den gamle mappe er ikke færdig.',
                          error='Resterende originaler er bevaret. Kontrollér mapperne før manuel oprydning.')
                return
            recovery = ''
            if stopped and not committed and old_env is not None:
                try:
                    if (directory / '.env').read_text(encoding='utf-8') != old_env:
                        recovery = ' Konfigurationen er ændret af en anden handling; appen forbliver stoppet til kontrol.'
                except OSError:
                    recovery = ' Konfigurationen kunne ikke læses; appen forbliver stoppet til kontrol.'
            if committed:
                try:
                    if (directory / '.env').read_text(encoding='utf-8') != new_env:
                        raise RuntimeError('Konfigurationen er ændret af en anden handling.')
                    temporary = directory / '.env.storage-restore'
                    temporary.write_text(old_env, encoding='utf-8'); temporary.chmod(0o600)
                    temporary.replace(directory / '.env')
                except Exception:
                    recovery = ' Konfigurationen kunne ikke gendannes automatisk. Kontrollér appen før opstart.'
            if stopped and running and not recovery:
                try:
                    self.compose(directory, ['up', '-d', '--no-build', '--pull', 'never', '--no-deps', '--force-recreate', '--wait', '--wait-timeout', '120', *sorted(set(running))], timeout=180)
                except Exception:
                    recovery = ' Appen kunne ikke genstartes automatisk.'
            message = str(exc) if isinstance(exc, (ValueError, RuntimeError)) else 'Flytningen kunne ikke gennemføres. Kontrollér mapper og Docker.'
            self.save(app_id, running=False, message='Skiftet blev ikke gennemført. Den gamle mappe er bevaret.',
                      error=message + recovery)
        finally:
            with self.lock:
                self.active.discard(app_id)
