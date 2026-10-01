"""Proxmox inventory for reading existing media, never allocating or copying disks."""
import re
import shlex
from pathlib import PurePosixPath


def beneath(path, root):
    return bool(path and root and PurePosixPath(path).is_relative_to(PurePosixPath(root)))


def mount_commands(ctid, storage_id, source):
    """Reviewable, read-only bind mount of existing files. Run on PVE, not here."""
    if not re.fullmatch(r'[1-9][0-9]{2,8}', str(ctid)) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', storage_id):
        return ''
    if not re.fullmatch(r'/(?:mnt|media|srv|var/lib/vz)(?:/[A-Za-z0-9_. -]+)*', source) or '..' in PurePosixPath(source).parts:
        return ''
    target = '/mnt/fjordflix/' + storage_id
    return f'''bash <<'FJORDFLIX_LIBRARY'
set -euo pipefail
ctid={shlex.quote(str(ctid))}
source={shlex.quote(source)}
target={shlex.quote(target)}
[ -d "$source" ] || {{ echo 'Kildemappen findes ikke'; exit 1; }}
[ "$(readlink -f "$source")" = "$source" ] || {{ echo 'Kildestien må ikke indeholde links'; exit 1; }}
config=$(pct config "$ctid")
if printf '%s\\n' "$config" | grep -Fq "mp=$target"; then
  echo 'Mountpunktet findes allerede. Kontrollér det i Proxmox.'; exit 1
fi
slot=''
for i in $(seq 0 255); do
  if ! printf '%s\\n' "$config" | grep -q "^mp$i:"; then slot="mp$i"; break; fi
done
[ -n "$slot" ] || {{ echo 'Ingen ledige mount-numre'; exit 1; }}
pct exec "$ctid" -- sh -c '[ ! -e "$1" ]' sh "$target" || {{ echo 'Målstien findes allerede; kontrollér den først'; exit 1; }}
cp -- "/etc/pve/lxc/$ctid.conf" "/root/fjordflix-library-$ctid-$(date +%Y%m%d-%H%M%S).conf"
pct set "$ctid" "-$slot" "$source,mp=$target,ro=1"
# Genstarter denne LXC og dens apps for at aktivere monteringen.
pct reboot "$ctid"
FJORDFLIX_LIBRARY'''


class MediaLibrary:
    def __init__(self, proxmox):
        self.proxmox = proxmox

    def inventory(self):
        pve = self.proxmox
        errors = []
        def read(path, label, fallback):
            try:
                return pve.get(path)
            except ValueError:
                errors.append(f'{label} kunne ikke læses. Kontrollér Proxmox-forbindelsen og læserettighederne.')
                return fallback
        rows = read(pve.node_path + '/storage', 'Storage-listen', [])
        definitions = {r['storage']: r for r in read('/storage', 'Storage-stier', [])}
        config = read(pve.node_path + '/lxc/' + pve.ctid + '/config', 'LXC-monteringer', {})
        disks = read(pve.node_path + '/disks/list?include-partitions=1&skipsmart=1', 'Diske og partitioner', [])
        directories = read(pve.node_path + '/disks/directory', 'Diskenes monteringspunkter', [])
        mounts = []
        for key, value in config.items():
            if not re.fullmatch(r'mp\d+', key):
                continue
            volume, *options = str(value).split(',')
            options = dict(item.split('=', 1) for item in options if '=' in item)
            target = options.get('mp', '')
            if target.startswith('/') and '..' not in PurePosixPath(target).parts:
                mounts.append({'source': volume, 'path': target})

        def paths_for(source='', storage_id=''):
            result = []
            for mount in mounts:
                volume = mount['source']
                if storage_id and volume.startswith(storage_id + ':'):
                    result.append(mount['path'])
                elif source and volume.startswith('/') and not volume.startswith('/dev/'):
                    # A pool may expose only a subfolder. Never claim access to
                    # the rest of that pool just because one child is mounted.
                    if beneath(volume, source):
                        result.append(mount['path'])
                    elif beneath(source, volume):
                        relative = PurePosixPath(source).relative_to(PurePosixPath(volume))
                        result.append(str(PurePosixPath(mount['path']) / relative))
                elif source and source == volume:
                    result.append(mount['path'])
            return sorted(set(result))

        storages = []
        for row in rows:
            sid, kind = row['storage'], row.get('type', '')
            definition = definitions.get(sid, {})
            path = definition.get('path') or (f'/mnt/pve/{sid}' if kind in ('nfs', 'cifs') else '')
            paths = paths_for(path, sid)
            online = bool(row.get('active')) and bool(row.get('enabled', 1))
            file_based = kind in ('dir', 'nfs', 'cifs', 'btrfs')
            reason = ('Lageret er offline.' if not online else
                      'Vælg en eksisterende mediemappe i det monterede lager.' if paths else
                      'Lagerets mediemappe skal deles med FjordHubs LXC, før den kan vælges.' if file_based else
                      'Dette lager indeholder virtuelle diske. En eksisterende disk med mediefiler skal først monteres som filsystem i appens LXC/VM.')
            storages.append({'id': sid, 'type': kind, 'path': path, 'online': online,
                             'paths': paths if online else [], 'reason': reason,
                             'commands': mount_commands(pve.ctid, sid, path) if online and file_based and path and not paths else '',
                             'free_bytes': row.get('avail', 0), 'total_bytes': row.get('total', 0)})
        devices = []
        for row in disks:
            device = row.get('devpath', '')
            paths = paths_for(device)
            for directory in directories:
                if directory.get('device') == device:
                    paths.extend(paths_for(directory.get('path', '')))
            devices.append({key: row.get(key) for key in ('devpath', 'parent', 'model', 'size', 'used', 'mounted', 'type')} |
                           {'paths': sorted(set(paths)), 'reason': 'Vælg en mediemappe på partitionen.' if paths else
                            'Vælg dens storage-pool nedenfor, eller montér det eksisterende filsystem i appens LXC/VM. Diskoversigten alene giver ikke adgang til filerne.'})
        # Include actual LXC mounts separately: PVE directory devices may be
        # reported by UUID, so never guess which /dev/sdX owns a mount.
        return {'storages': storages, 'disks': devices, 'mounts': mounts,
                'errors': errors, 'ctid': pve.ctid}
