#!/usr/bin/python3
"""Root-owned SSH forced command. No shell, arbitrary paths, CTIDs or commands.

The installer fixes one CTID in authorized_keys. Only supported mounted filesystems
below approved media roots can be attached, always read-only at a fixed target.
VPN installation can also grant only /dev/net/tun to that same fixed CTID.
"""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import uuid

ROOT = Path('/var/lib/fjordhub-storage')
MEDIA_ROOTS = (Path('/mnt'), Path('/media'), Path('/srv'))
FILESYSTEMS = {'fuse.mergerfs', 'mergerfs', 'ext4', 'xfs', 'btrfs', 'zfs', 'nfs', 'nfs4', 'cifs'}


def run(args, timeout=25):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    if result.returncode:
        raise ValueError('Værtshandlingen mislykkedes: ' + args[0])
    return result.stdout


def pool_id(path):
    return hashlib.sha256(path.encode()).hexdigest()[:20]


def discover():
    mounts = json.loads(run(['findmnt', '--json', '--list', '--output', 'TARGET,FSTYPE,OPTIONS']))
    pools = []
    for mount in mounts.get('filesystems', []):
        path = Path(mount['target'])
        if mount.get('fstype') not in FILESYSTEMS:
            continue
        if not any(path != root and path.is_relative_to(root) for root in MEDIA_ROOTS):
            continue
        if not re.fullmatch(r'/[A-Za-z0-9_./ -]+', str(path)) or path.resolve() != path or not path.is_dir():
            continue
        pools.append({'id': pool_id(str(path)), 'source': str(path), 'type': mount['fstype'],
                      'allow_other': mount['fstype'] not in ('fuse.mergerfs', 'mergerfs') or 'allow_other' in mount.get('options', '').split(',')})
    return sorted(pools, key=lambda item: item['source'])


def config(ctid):
    node = socket.gethostname().split('.')[0]
    return json.loads(run(['pvesh', 'get', f'/nodes/{node}/lxc/{ctid}/config', '--output-format', 'json']))


def target_for(identifier):
    return '/mnt/fjordflix/pool-' + identifier


def verify_boot(ctid):
    pools = {p['source']: p for p in discover()}
    for key, value in config(ctid).items():
        if not re.fullmatch(r'mp\d+', key):
            continue
        source, *parts = value.split(',')
        options = dict(p.split('=', 1) for p in parts if '=' in p)
        if options.get('mp', '').startswith('/mnt/fjordflix/pool-') and source not in pools:
            raise ValueError('Et tilsluttet medielager er ikke monteret på Proxmox. Start lageret før LXC.')


def configure_boot(ctid, sources):
    folder = Path('/etc/systemd/system') / ('pve-container@' + ctid + '.service.d')
    folder.mkdir(parents=True, exist_ok=True)
    paths = ' '.join('"' + source + '"' for source in sorted(set(sources)))
    text = '[Unit]\n' + ('RequiresMountsFor=' + paths + '\n' if paths else '')
    text += '[Service]\nExecStartPre=/usr/bin/python3 /usr/local/lib/fjordhub/storage.py --verify ' + ctid + '\n'
    (folder / '20-fjordhub-storage.conf').write_text(text)
    run(['systemctl', 'daemon-reload'])


def matching_mount(configuration, pool):
    target = target_for(pool['id'])
    for key, value in configuration.items():
        if not re.fullmatch(r'mp\d+', key):
            continue
        volume, *parts = value.split(',')
        options = dict(part.split('=', 1) for part in parts if '=' in part)
        if options.get('mp') == target:
            if volume != pool['source']:
                raise ValueError('Målmappen bruges allerede af en anden montering. Intet er ændret.')
            return key
    return None


def visible(ctid, target):
    try:
        result = json.loads(run(['pct', 'exec', ctid, '--', 'findmnt', '-J', '-T', target, '-o', 'TARGET,FSTYPE,OPTIONS']))
        entry = result['filesystems'][0]
        return entry['target'] == target and entry['fstype'] in FILESYSTEMS
    except (ValueError, KeyError, IndexError):
        return False


class Agent:
    def __init__(self, ctid):
        if not re.fullmatch(r'[1-9][0-9]{2,8}', ctid):
            raise ValueError('Ugyldigt container-ID.')
        self.ctid = ctid
        self.folder = ROOT / ctid
        self.folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.state_file = self.folder / 'state.json'

    @contextlib.contextmanager
    def locked(self):
        import fcntl
        with (self.folder / 'lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            yield

    def state(self):
        return json.loads(self.state_file.read_text()) if self.state_file.exists() else {'state': 'idle'}

    def save(self, state):
        state['updated'] = time.time()
        tmp = self.folder / 'state.tmp'
        tmp.write_text(json.dumps(state))
        tmp.chmod(0o600)
        tmp.replace(self.state_file)

    def inventory(self):
        cfg = config(self.ctid)
        pools = discover()
        for pool in pools:
            pool['target'] = target_for(pool['id'])
            pool['configured'] = bool(matching_mount(cfg, pool))
        state = self.state()
        if state['state'] in ('queued', 'applying', 'restarting') and time.time() - state.get('updated', 0) > 600:
            state = {**state, 'state': 'interrupted', 'message': 'Tilslutningen blev afbrudt. Værtsadministratoren skal kontrollere jobbet og monteringen på Proxmox.'}
        return {'ctid': self.ctid, 'pools': pools, 'job': state}

    def ensure_vpn_tun(self):
        """Grant only the fixed TUN device to the installer's fixed LXC."""
        with self.locked():
            if self.state().get('state') in ('queued', 'applying', 'restarting'):
                raise ValueError('Vent til lageropsætningen er færdig, før VPN installeres.')
            run(['modprobe', 'tun'])
            path = Path(f'/etc/pve/lxc/{self.ctid}.conf')
            original = path.read_text()
            lines = original.splitlines()
            has_device = any(re.fullmatch(r'dev\d+:\s*/dev/net/tun(?:,.*)?', line) for line in lines)
            additions = []
            if not has_device:
                expected = 'lxc.mount.entry: /dev/net/tun dev/net/tun none bind,create=file'
                matches = [line for line in lines if line.startswith('lxc.mount.entry:') and
                           'dev/net/tun' in line.split()]
                if matches and not any(line.split()[1:3] == ['/dev/net/tun', 'dev/net/tun'] for line in matches):
                    raise ValueError('Der findes en anden TUN-montering. Kontrollér LXC-konfigurationen.')
                if not matches:
                    additions.append(expected)
                permission = 'lxc.cgroup2.devices.allow: c 10:200 rwm'
                if permission not in lines:
                    additions.append(permission)
            if additions:
                backup = self.folder / ('before-vpn-tun-' + uuid.uuid4().hex + '.conf')
                backup.write_text(original); backup.chmod(0o600)
                if path.read_text() != original:
                    raise ValueError('LXC-konfigurationen blev ændret. Prøv installationen igen.')
                path.write_text(original.rstrip() + '\n' + '\n'.join(additions) + '\n')
            probe = ['pct', 'exec', self.ctid, '--', 'python3', '-c',
                     "import os; fd=os.open('/dev/net/tun',os.O_RDWR); os.close(fd)"]
            try:
                run(probe)
            except ValueError:
                run(['lxc-device', '-n', self.ctid, 'add', '/dev/net/tun'])
                run(probe)
            return {'ctid': self.ctid, 'ready': True, 'changed': bool(additions)}

    def connect(self, identifier):
        if not isinstance(identifier, str) or not re.fullmatch(r'[a-f0-9]{20}', identifier):
            raise ValueError('Vælg en pool fra lageroversigten.')
        with self.locked():
            previous = self.state()
            if previous['state'] in ('queued', 'applying', 'restarting'):
                if time.time() - previous['updated'] < 600:
                    if previous.get('pool_id') == identifier:
                        return previous
                    raise ValueError('En anden pool er ved at blive tilsluttet.')
                # A dead worker must not cause a blind second reboot.
                raise ValueError('Den tidligere tilslutning blev afbrudt. Kontrollér værtens fjordhub-storage-job først.')
            pool = next((p for p in discover() if p['id'] == identifier), None)
            if not pool:
                raise ValueError('Poolen er ikke længere monteret på Proxmox. Genindlæs lageroversigten.')
            if not pool['allow_other']:
                raise ValueError('Poolens FUSE-opsætning mangler allow_other. Værtsadministratoren skal give containeren læseadgang.')
            cfg = config(self.ctid)
            mount = matching_mount(cfg, pool)
            state = {'id': uuid.uuid4().hex, 'pool_id': identifier, 'source': pool['source'],
                     'target': target_for(identifier), 'state': 'queued', 'message': 'Tilslutningen er sat i kø.'}
            if mount and visible(self.ctid, state['target']):
                state.update(state='ready', message='Poolen er allerede tilsluttet med læseadgang.')
            self.save(state)
            if state['state'] == 'queued':
                try:
                    run(['systemd-run', '--quiet', '--collect', '--unit=fjordhub-storage-' + state['id'],
                         '--property=RuntimeMaxSec=300', '/usr/bin/python3', str(Path(__file__).resolve()),
                         '--apply', self.ctid, state['id']])
                except Exception:
                    state.update(state='failed', message='Tilslutningen kunne ikke startes. Intet er monteret.')
                    self.save(state)
                    raise
            return state

    def apply(self, job_id):
        with self.locked():
            state = self.state()
            if state.get('id') != job_id or state['state'] != 'queued':
                return
            try:
                pool = next((p for p in discover() if p['id'] == state['pool_id'] and p['source'] == state['source']), None)
                if not pool or not pool['allow_other']:
                    raise ValueError('Poolen er ikke længere tilgængelig med den krævede læseadgang.')
                cfg = config(self.ctid)
                mount = matching_mount(cfg, pool)
                if not mount:
                    # Do not hide an existing guest directory or overwrite any mp slot.
                    run(['pct', 'exec', self.ctid, '--', 'sh', '-c', '[ ! -e "$1" ] && [ ! -L "$1" ]', 'sh', state['target']])
                    slot = next((f'mp{i}' for i in range(256) if f'mp{i}' not in cfg), None)
                    if not slot or not cfg.get('digest'):
                        raise ValueError('Der er ikke et ledigt mountpunkt eller en gyldig konfigurationsversion.')
                    backup = self.folder / (job_id + '.conf')
                    backup.write_bytes(Path(f'/etc/pve/lxc/{self.ctid}.conf').read_bytes())
                    backup.chmod(0o600)
                    state.update(state='applying', message='Monterer poolen skrivebeskyttet.')
                    self.save(state)
                    run(['pct', 'set', self.ctid, '--digest', cfg['digest'], '--' + slot,
                         pool['source'] + ',mp=' + state['target'] + ',ro=1,backup=0'])
                state.update(state='restarting', message='FjordHubs container og apps genstarter.')
                self.save(state)
                updated_config = config(self.ctid)
                mounted_sources = [p['source'] for p in discover() if matching_mount(updated_config, p)]
                configure_boot(self.ctid, mounted_sources)
                run(['pct', 'reboot', self.ctid, '--timeout', '60'], timeout=90)
                deadline = time.monotonic() + 120
                while time.monotonic() < deadline:
                    if visible(self.ctid, state['target']):
                        # Check actual directory reads as the unprivileged guest user.
                        run(['pct', 'exec', self.ctid, '--', 'python3', '-c', 'import os,sys; next(os.scandir(sys.argv[1]),None)', state['target']])
                        state.update(state='ready', message='Poolen er tilsluttet. Vælg din mediemappe i FjordFlix.')
                        self.save(state)
                        return
                    time.sleep(2)
                raise ValueError('Containeren genstartede, men poolen kunne ikke bekræftes. Kontrollér monteringen og læserettighederne.')
            except Exception as exc:
                state.update(state='failed', message=str(exc) if isinstance(exc, ValueError) else 'Tilslutningen blev afbrudt. Kontrollér Proxmox. Konfigurationsbackup er bevaret.')
                self.save(state)


def dispatch(agent, request):
    if not isinstance(request, dict) or set(request) - {'action', 'pool_id'}:
        raise ValueError('Ugyldig forespørgsel.')
    if request.get('action') == 'inventory':
        return agent.inventory()
    if request.get('action') == 'connect':
        return agent.connect(request.get('pool_id'))
    if request == {'action': 'vpn_tun'}:
        return agent.ensure_vpn_tun()
    raise ValueError('Handlingen er ikke tilladt.')


def main():
    os.umask(0o077)
    if os.geteuid() != 0:
        raise SystemExit('Root-owned helper required')
    if len(sys.argv) == 3 and sys.argv[1] == '--verify':
        verify_boot(sys.argv[2])
        return
    if len(sys.argv) == 4 and sys.argv[1] == '--apply':
        Agent(sys.argv[2]).apply(sys.argv[3])
        return
    if len(sys.argv) != 2:
        raise SystemExit(1)
    try:
        raw = sys.stdin.buffer.read(4097)
        if len(raw) > 4096:
            raise ValueError('Forespørgslen er for stor.')
        result = dispatch(Agent(sys.argv[1]), json.loads(raw))
        print(json.dumps({'ok': True, **result, 'ctid': sys.argv[1]}))
    except Exception as exc:
        print(json.dumps({'ok': False, 'error': str(exc) if isinstance(exc, ValueError) else 'Værtens lagerforbindelse fejlede.'}))


if __name__ == '__main__':
    main()
