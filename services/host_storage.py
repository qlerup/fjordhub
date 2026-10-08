"""Client for the installer's fixed, root-owned Proxmox storage command."""
import ipaddress
import json
import os
import subprocess
import re


class HostStorage:
    def call(self, action, pool_id=None):
        host = os.getenv('FJORDHUB_STORAGE_SSH_HOST', '')
        if not host:
            raise ValueError('Værtens lageradgang er ikke aktiveret. FjordHubs Proxmox-installer sætter den op automatisk; eksisterende installationer kræver engangsopsætning på værten.')
        try:
            ipaddress.IPv4Address(host)
        except ValueError:
            raise ValueError('FjordHubs værtsadresse er ugyldig.') from None
        if action not in ('inventory', 'connect', 'vpn_tun'):
            raise ValueError('Handlingen er ikke tilladt.')
        if action == 'connect' and (not isinstance(pool_id, str) or not re.fullmatch(r'[a-f0-9]{20}', pool_id)):
            raise ValueError('Vælg et lager fra oversigten.')
        payload = {'action': action}
        if pool_id is not None:
            payload['pool_id'] = pool_id
        try:
            result = subprocess.run(['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes',
                '-o', 'StrictHostKeyChecking=yes', '-o', 'HostKeyAlias=fjordhub-proxmox',
                '-o', 'UserKnownHostsFile=/data/proxmox-agent/known_hosts', '-o', 'ConnectTimeout=8',
                '-i', '/data/proxmox-agent/id_ed25519', 'root@' + host],
                input=json.dumps(payload), text=True, capture_output=True, timeout=45)
            if result.returncode:
                raise ValueError('Den begrænsede lagerforbindelse til Proxmox kunne ikke åbnes.')
            data = json.loads(result.stdout)
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
            raise ValueError('Proxmox svarede ikke. Genindlæs lageroversigten for at se status, før du prøver igen.') from None
        if not isinstance(data, dict) or not data.get('ok'):
            raise ValueError(data.get('error', 'Værtens lageradgang fejlede.') if isinstance(data, dict) else 'Ugyldigt svar fra Proxmox.')
        if str(data.get('ctid', '')) != os.getenv('PROXMOX_VMID', '1000'):
            raise ValueError('Lagerforbindelsen peger på en anden LXC end FjordHubs konfiguration.')
        return data

    def inventory(self):
        if not os.getenv('FJORDHUB_STORAGE_SSH_HOST'):
            return {'available': False, 'pools': [], 'job': {'state': 'idle'}}
        return {'available': True, **self.call('inventory')}

    def connect(self, pool_id):
        return self.call('connect', pool_id)

    def ensure_vpn_tun(self):
        return self.call('vpn_tun')
