"""Read-only Proxmox storage discovery using the existing hub API token."""
import os
import re
import shlex
from urllib.parse import quote
import requests


class ProxmoxStorage:
    def get(self, path):
        base = os.environ.get('PROXMOX_API_URL', '').rstrip('/')
        token = os.environ.get('PROXMOX_TOKEN_ID', '')
        secret = os.environ.get('PROXMOX_TOKEN_SECRET', '')
        if not base or not token or not secret:
            raise ValueError('FjordHubs Proxmox API-forbindelse skal konfigureres først.')
        verify = os.environ.get('PROXMOX_VERIFY_SSL', 'false').lower() in ('1','true','yes')
        try:
            response = requests.get(base + '/api2/json' + path,
                headers={'Authorization':f'PVEAPIToken={token}={secret}'}, timeout=8, verify=verify)
            response.raise_for_status()
            return response.json()['data']
        except (requests.RequestException, ValueError, KeyError):
            raise ValueError('Proxmox kunne ikke læses. Kontrollér forbindelsen og API-adgangens læserettigheder.') from None

    @property
    def node_path(self):
        return '/nodes/' + quote(os.environ.get('PROXMOX_NODE', 'pve'), safe='')

    @property
    def ctid(self):
        value = os.environ.get('PROXMOX_VMID', '1000')
        if not re.fullmatch(r'[1-9][0-9]{2,8}', value):
            raise ValueError('FjordHubs PROXMOX_VMID er ugyldigt.')
        return value

    def access_commands(self):
        token = os.environ.get('PROXMOX_TOKEN_ID', '')
        if not re.fullmatch(r'[A-Za-z0-9_.@!+-]+', token) or '!' not in token:
            return ''
        user = token.split('!',1)[0]
        return ('# Læseadgang til lagerlisten. Ændrer ikke diske eller mounts.\n'
                f'pveum acl modify /storage --users {shlex.quote(user)} --roles PVEAuditor\n'
                f'pveum acl modify /storage --tokens {shlex.quote(token)} --roles PVEAuditor')

    def inventory(self):
        rows = self.get(self.node_path + '/storage')
        config = self.get(self.node_path + '/lxc/' + self.ctid + '/config')
        root_pool = str(config.get('rootfs','')).split(':',1)[0]
        supported = ('dir','nfs','cifs','lvmthin','lvm','zfspool','rbd','btrfs')
        result = []
        for row in rows:
            if 'rootdir' not in str(row.get('content','')).split(','):
                continue
            kind = row.get('type')
            ready = bool(row.get('active')) and bool(row.get('enabled',1)) and kind in supported
            result.append({'id':row['storage'], 'type':kind, 'available':ready,
                'free_bytes':row.get('avail',0), 'total_bytes':row.get('total',0),
                'system_pool':row['storage'] == root_pool,
                'needs_size':bool(config.get('unprivileged')) or kind not in ('dir','nfs','cifs'),
                'reason':'' if ready else 'Lageret er offline eller typen understøttes ikke.'})
        return {'storages':result, 'ctid':self.ctid, 'needs_access':not rows,
                'access_commands':self.access_commands() if not rows else '',
                'message':'Proxmox viser ingen lagre. Giv API-adgangen læserettigheder til lagerlisten.' if not rows else
                          'Ingen lagre på denne node tillader containerdiske (rootdir).' if not result else ''}

    def selection(self, storage_id, folder, size):
        if not isinstance(storage_id,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',storage_id):
            raise ValueError('Vælg et Proxmox-lager.')
        if not isinstance(folder,str) or not re.fullmatch(r'[\w .-]{1,100}', folder) or folder in ('.','..') or folder != folder.strip():
            raise ValueError('Skriv et mappenavn uden skråstreger eller specialtegn.')
        storage = next((s for s in self.inventory()['storages'] if s['id'] == storage_id),None)
        if not storage or not storage['available']:
            raise ValueError('Det valgte Proxmox-lager er ikke tilgængeligt til containerdata.')
        # GET /storage/{id} requires Datastore.Allocate even for reads.
        # The filtered collection exposes configuration with Datastore.Audit.
        definition = next((item for item in self.get('/storage') if item.get('storage') == storage_id), None)
        if definition is None:
            raise ValueError('Det valgte lager kunne ikke læses fra Proxmox. Hent lagerlisten igen.')
        config = self.get(self.node_path + '/lxc/' + self.ctid + '/config')
        target = '/mnt/fjordhub/' + storage_id
        disk = definition.get('path') or ('/mnt/pve/' + storage_id if storage['type'] in ('nfs','cifs') else '')
        source = str(disk).rstrip('/') + '/fjordhub'
        mounted_config = False
        for key, value in sorted(config.items()):
            if not re.fullmatch(r'mp\d+',key):
                continue
            volume, *options = str(value).split(',')
            options = dict(item.split('=',1) for item in options if '=' in item)
            if (volume == source if not storage['needs_size'] else volume.startswith(storage_id + ':')) and options.get('ro','0') != '1':
                candidate = options.get('mp','')
                if re.fullmatch(r'/(?:mnt|media)/[A-Za-z0-9_./ -]+',candidate) and '..' not in candidate.split('/'):
                    target = candidate; mounted_config = True; break
        if storage['needs_size'] and not mounted_config:
            if isinstance(size,bool) or not str(size).isdigit() or not 1 <= int(size) <= 1048576:
                raise ValueError('Angiv størrelsen på den nye containerdisk i GiB.')
            if int(size) * 1024**3 > storage['free_bytes']:
                raise ValueError('Den valgte diskstørrelse overstiger den ledige plads på lageret.')
        return {**storage,'destination':target + '/' + folder,'target':target,
                'disk':disk,'ctid':self.ctid,'configured':mounted_config,
                'size_gib':int(size) if str(size).isdigit() else None}
