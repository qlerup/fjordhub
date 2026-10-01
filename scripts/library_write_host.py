#!/usr/bin/env python3
"""Reviewable guide executed manually on PVE; never exposed by the SSH agent."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import time


def run(args, timeout=180):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise ValueError('Kommandoen fejlede: ' + ' '.join(args[:3]) + '. Kontrollér den i Proxmox.')
    return result.stdout.strip()


def config(ctid):
    return json.loads(run(['pvesh', 'get', '/nodes/' + socket.gethostname().split('.')[0] + '/lxc/' + ctid + '/config', '--output-format', 'json']))


def safe_path(value):
    return (bool(re.fullmatch(r'/(?:mnt|media|srv)/[A-Za-z0-9_./ -]+', value))
            and '..' not in Path(value).parts and str(Path(value)) == value)


def write_value(value):
    parts = value.split(',')
    return ','.join([p for p in parts if not p.startswith('ro=')] + ['ro=0'])


def apply(ctid, slot, source, target, file_permissions=False):
    if not re.fullmatch(r'[1-9][0-9]{2,8}', ctid) or not re.fullmatch(r'mp[0-9]{1,3}', slot):
        raise ValueError('Ugyldig container eller montering.')
    if not safe_path(source) or not safe_path(target):
        raise ValueError('Stien er ikke en understøttet mediemappe.')
    if not Path(source).is_dir() or str(Path(source).resolve()) != source:
        raise ValueError('Kildemappen mangler eller indeholder symbolske links.')
    cfg = config(ctid)
    old = cfg.get(slot, '')
    volume, *parts = old.split(',')
    options = dict(p.split('=', 1) for p in parts if '=' in p)
    if volume != source or options.get('mp') != target or not cfg.get('digest'):
        raise ValueError('Monteringen er ændret. Hent en ny guide; intet er ændret.')
    # Do not grant access to a nested filesystem unintentionally.
    mounts = json.loads(run(['findmnt', '--json', '--list', '--output', 'TARGET']))['filesystems']
    if any(Path(m['target']) != Path(source) and Path(m['target']).is_relative_to(source) for m in mounts):
        raise ValueError('Mappen indeholder andre monteringer. Vælg en mere afgrænset mappe.')
    guest = ['pct', 'exec', ctid, '--']
    hub = guest + ['docker', 'exec', 'fjordhub', 'python', '-m', 'services.library_permissions']
    run(hub + ['check', target])  # Docker/Compose preflight before changing PVE.
    backup = Path('/root/fjordhub-library-backups') / (ctid + '-' + str(time.time_ns()))
    backup.mkdir(parents=True, mode=0o700)
    shutil.copyfile('/etc/pve/lxc/' + ctid + '.conf', backup / 'lxc.conf')
    (backup / 'mount.json').write_text(json.dumps({'ctid': ctid, 'slot': slot, 'value': old}))
    print('Konfigurationsbackup: ' + str(backup), flush=True)
    if file_permissions:
        if not shutil.which('getfacl') or not shutil.which('setfacl'):
            raise ValueError('Installér acl på Proxmox først: apt-get install acl. Intet er ændret.')
        # Resolve the actual app UID through the running LXC's mapping; do not
        # assume that every unprivileged container uses 100000.
        uid = int(run(guest + ['docker', 'exec', 'fjordflix', 'id', '-u']))
        pid = int(run(['lxc-info', '-n', ctid, '-pH']))
        ranges = [list(map(int, row.split())) for row in Path('/proc/' + str(pid) + '/uid_map').read_text().splitlines()]
        mapped = next((outside + uid - inside for inside, outside, size in ranges if inside <= uid < inside + size), None)
        if mapped is None:
            raise ValueError('Appens bruger kunne ikke oversættes til Proxmox.')
        with (backup / 'permissions.acl').open('w') as output:
            subprocess.run(['getfacl', '-R', '-P', '-p', '--', source], stdout=output, check=True, timeout=600)
        subprocess.run(['setfacl', '-R', '-P', '-m', 'u:' + str(mapped) + ':rwX', '--', source], check=True, timeout=600)
        # POSIX ACL owner entries take precedence over named-user entries.
        # Only adjust owners that are this app user; never follow symlinks.
        subprocess.run(['find', source, '-xdev', '-uid', str(mapped), '!', '-type', 'l',
                        '-exec', 'setfacl', '-m', 'u::rwX', '--', '{}', '+'], check=True, timeout=600)
        print('Filrettigheder er sikkerhedskopieret. Gendan om nødvendigt med: setfacl --restore=' + str(backup / 'permissions.acl'), flush=True)
    # Digest prevents overwriting a concurrently edited LXC configuration.
    if options.get('ro') == '1':
        run(['pct', 'set', ctid, '--digest', cfg['digest'], '--' + slot, write_value(old)])
        run(['pct', 'reboot', ctid, '--timeout', '60'])
    deadline = time.monotonic() + 150
    while time.monotonic() < deadline:
        try:
            mounted = json.loads(run(guest + ['findmnt', '-J', '-T', target, '-o', 'TARGET,OPTIONS'], timeout=15))['filesystems'][0]
            if mounted['target'] == target and 'rw' in mounted['options'].split(','):
                run(hub + ['check', target], timeout=15)
                break
        except (ValueError, KeyError, IndexError, subprocess.TimeoutExpired):
            pass
        time.sleep(3)
    else:
        raise ValueError('Monteringen blev ikke klar. Kontrollér LXC og backup: ' + str(backup))
    try:
        print(run(hub + ['enable', target]), flush=True)
    except ValueError:
        raise ValueError('Docker-opsætningen eller skrivetesten fejlede. Se FjordHubs containerlog og backup: ' + str(backup) + '. Hvis filrettigheder spærrer, hent guiden igen med filrettigheder valgt.') from None


def main():
    parser = argparse.ArgumentParser()
    for name in ('ctid', 'slot', 'source', 'target'):
        parser.add_argument(name)
    parser.add_argument('--file-permissions', action='store_true')
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit('Kør guiden som root i Proxmox Shell.')
    os.umask(0o077)
    try:
        if not re.fullmatch(r'[1-9][0-9]{2,8}', args.ctid):
            raise ValueError('Ugyldigt container-ID.')
        import fcntl
        lock_path = Path('/var/lib/fjordhub-storage') / args.ctid
        lock_path.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (lock_path / 'lock').open('a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError('En anden lagerændring er i gang. Vent på den først.') from None
            apply(args.ctid, args.slot, args.source, args.target, args.file_permissions)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc)) from None


if __name__ == '__main__':
    main()
