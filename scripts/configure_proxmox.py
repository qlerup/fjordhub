#!/usr/bin/python3
"""Run by FjordHub's Proxmox installer, or once on the host for an existing LXC.

Installs a forced-command key for one CTID and a separate read-only API token.
No password or unrestricted root credential is delivered to the container.
"""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import tempfile


def run(args, input=None):
    result = subprocess.run(args, input=input, text=True, capture_output=True, timeout=240)
    if result.returncode:
        raise SystemExit('FjordHub setup failed: ' + args[0] + ' (see host logs; secrets are not printed)')
    return result.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('ctid')
    parser.add_argument('--directory', default='/opt/fjordhub')
    parser.add_argument('--host', required=True, help='Proxmox IP reachable from the LXC')
    args = parser.parse_args()
    if os.geteuid() != 0 or not Path('/etc/pve').is_dir():
        raise SystemExit('Run on the Proxmox node as root.')
    if not re.fullmatch(r'[1-9][0-9]{2,8}', args.ctid):
        raise SystemExit('Invalid CTID')
    import ipaddress
    ipaddress.IPv4Address(args.host)
    if not re.fullmatch(r'/[A-Za-z0-9_./-]+', args.directory) or '..' in Path(args.directory).parts:
        raise SystemExit('Invalid install directory')
    node = socket.gethostname().split('.')[0]
    run(['pct', 'status', args.ctid])
    execute = ['pct', 'exec', args.ctid, '--']
    mounts = json.loads(run(execute + ['docker', 'inspect', 'fjordhub', '--format', '{{json .Mounts}}']))
    data = next((m['Source'] for m in mounts if m['Destination'] == '/data' and m['Type'] == 'bind'), None)
    if not data or not data.startswith('/'):
        raise SystemExit('FjordHub needs a persistent /data bind mount before setup.')
    helper = Path('/usr/local/lib/fjordhub/storage.py')
    helper.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
    helper.write_bytes((Path(__file__).resolve().parents[1] / 'host_agent' / 'storage.py').read_bytes())
    helper.chmod(0o755)
    config = {
        'PROXMOX_API_URL': 'https://' + args.host + ':8006', 'PROXMOX_NODE': node,
        'PROXMOX_VMID': args.ctid, 'PROXMOX_VERIFY_SSL': 'false',
        'FJORDHUB_STORAGE_SSH_HOST': args.host,
    }
    os.umask(0o077)
    with tempfile.TemporaryDirectory(prefix='fjordhub-proxmox-') as folder:
        folder = Path(folder)
        private = folder / 'id_ed25519'
        run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-f', str(private)])
        public = private.with_suffix('.pub').read_text().split()
        marker = 'fjordhub-storage-' + args.ctid
        authorized = Path('/root/.ssh/authorized_keys')
        authorized.parent.mkdir(mode=0o700, exist_ok=True)
        old = authorized.read_text() if authorized.exists() else ''
        lines = [line for line in old.splitlines() if not line.endswith(' ' + marker)]
        lines.append(f'restrict,command="/usr/bin/python3 {helper} {args.ctid}" {public[0]} {public[1]} {marker}')
        authorized.write_text('\n'.join(lines) + '\n')
        authorized.chmod(0o600)
        host_key = Path('/etc/ssh/ssh_host_ed25519_key.pub').read_text().split()
        known = folder / 'known_hosts'
        known.write_text('fjordhub-proxmox ' + ' '.join(host_key[:2]) + '\n')
        destination = data.rstrip('/') + '/proxmox-agent'
        run(execute + ['install', '-d', '-m', '700', destination])
        for source, name in ((private, 'id_ed25519'), (known, 'known_hosts')):
            run(['pct', 'push', args.ctid, str(source), destination + '/' + name, '--perms', '0600'])
        # Reuse read credentials when this script is run again.
        saved = Path('/var/lib/fjordhub-storage') / args.ctid / 'api.json'
        saved.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if saved.exists():
            config.update(json.loads(saved.read_text()))
        else:
            user = 'fjordhub-' + args.ctid + '-' + secrets.token_hex(3) + '@pve'
            run(['pveum', 'user', 'add', user, '--comment', 'FjordHub read-only inventory'])
            for acl in ('/',):
                run(['pveum', 'acl', 'modify', acl, '--users', user, '--roles', 'PVEAuditor', '--propagate', '1'])
            token = json.loads(run(['pveum', 'user', 'token', 'add', user, 'inventory', '--privsep', '1', '--output-format', 'json']))
            for acl in ('/',):
                run(['pveum', 'acl', 'modify', acl, '--tokens', token['full-tokenid'], '--roles', 'PVEAuditor', '--propagate', '1'])
            credentials = {'PROXMOX_TOKEN_ID': token['full-tokenid'], 'PROXMOX_TOKEN_SECRET': token['value']}
            saved.write_text(json.dumps(credentials))
            saved.chmod(0o600)
            config.update(credentials)
        update_env = '''import json,sys,os
from pathlib import Path
values=json.load(sys.stdin); p=Path(sys.argv[1])/'.env'
lines=p.read_text().splitlines()
lines=[line for line in lines if line.partition('=')[0] not in values]
tmp=p.with_name('.env.proxmox-new')
tmp.write_text('\\n'.join(lines+[key+'='+value for key,value in values.items()])+'\\n')
tmp.chmod(0o600); tmp.replace(p)
'''
        run(execute + ['python3', '-c', update_env, args.directory], json.dumps(config))
    run(execute + ['sh', '-c', 'cd "$1" && docker compose up -d --build --wait --wait-timeout 180 fjordhub', 'sh', args.directory])
    # Verify the restricted channel from inside the rebuilt hub, not just on the host.
    run(execute + ['docker', 'exec', 'fjordhub', 'python', '-c',
                  'from services.host_storage import HostStorage; assert HostStorage().inventory()["available"]'])
    print('FjordHub is configured: read-only inventory and restricted pool access for LXC ' + args.ctid)


if __name__ == '__main__':
    main()
