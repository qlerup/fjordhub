"""Explicit administrator CLI for scoped Docker library write mounts.

There is deliberately no HTTP action that calls enable(). The UI only renders
commands for an administrator to review and run on the Proxmox host.
"""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import uuid

from services.compose_env import build_compose_env

OVERRIDE = 'docker-compose.fjordhub-library.yml'


def atomic_write(path, content):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('xb') as output:
            temporary.chmod(0o600)
            output.write(content)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def safe_path(value):
    return (isinstance(value, str) and bool(re.fullmatch(r'/(?:mnt|media|srv)/[A-Za-z0-9_./ -]+', value))
            and str(PurePosixPath(value)) == value and '..' not in PurePosixPath(value).parts)


def run(args, cwd=None):
    result = subprocess.run(args, cwd=cwd, env=build_compose_env(), capture_output=True, text=True, timeout=180)
    if result.returncode:
        # Compose output may contain expanded secrets. Never echo it.
        raise ValueError('Kommandoen mislykkedes: ' + ' '.join(args[:3]))
    return result.stdout


def compose_files(value):
    files = value.split(':') if value else ['docker-compose.yml']
    if any(not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*\.ya?ml', name) for name in files):
        raise ValueError('Denne Compose-opsætning kræver manuel kontrol.')
    return list(dict.fromkeys(files + [OVERRIDE]))


def plan(path, directory):
    if not safe_path(path):
        raise ValueError('Vælg en konkret mappe under /mnt, /media eller /srv.')
    security = json.loads(run(['docker', 'info', '--format', '{{json .SecurityOptions}}']))
    if any('userns' in item or 'rootless' in item for item in (security or [])):
        raise ValueError('Docker userns/rootless kræver manuel rettighedsopsætning.')
    config = json.loads(run(['docker', 'compose', 'config', '--format', 'json'], directory))
    service = config.get('services', {}).get('app', {})
    if service.get('container_name') != 'fjordflix' or service.get('userns_mode'):
        raise ValueError('Guiden kræver FjordHubs almindelige FjordFlix-installation uden Docker userns.')
    root = next((v for v in service.get('volumes', []) if v.get('target') == '/library/server'), None)
    if not root or root.get('type') != 'bind' or not root.get('read_only'):
        raise ValueError('Bibliotekets overordnede Docker-montering skal være skrivebeskyttet.')
    source_root = PurePosixPath(root['source'])
    source = PurePosixPath(path)
    if source == source_root or not source.is_relative_to(source_root):
        raise ValueError('Mappen skal ligge under biblioteksroden; hele roden kan ikke åbnes for skrivning.')
    target = str(PurePosixPath('/library/server') / source.relative_to(source_root))
    for volume in service.get('volumes', []):
        destination = PurePosixPath(volume['target'])
        if destination == PurePosixPath('/library/server'):
            continue
        if destination == PurePosixPath(target):
            if volume.get('type') != 'bind' or volume.get('source') != path:
                raise ValueError('Docker-målmappen bruges af en anden montering.')
        elif destination.is_relative_to(target) or PurePosixPath(target).is_relative_to(destination):
            raise ValueError('Der er en overlappende Docker-montering. Kontrollér den manuelt.')
    return target


def enable(path, directory):
    target = plan(path, directory)
    override = directory / OVERRIDE
    env_path = directory / '.env'
    original_env = env_path.read_text(encoding='utf-8')
    original_override = override.read_bytes() if override.exists() else None
    content = json.loads(original_override) if original_override else {'services': {'app': {'volumes': []}}}
    if set(content) != {'services'} or set(content['services']) != {'app'} or set(content['services']['app']) != {'volumes'}:
        raise ValueError('Den eksisterende biblioteksfil skal kontrolleres manuelt.')
    volumes = content['services']['app']['volumes']
    volumes[:] = [v for v in volumes if v['target'] != target]
    volumes.append({'type': 'bind', 'source': path, 'target': target, 'read_only': False,
                    'bind': {'create_host_path': False}})
    # Back up the exact private configuration; never expose its contents.
    backup = Path(os.getenv('DATA_DIR', '/data')) / 'library-permission-backups' / uuid.uuid4().hex
    backup.mkdir(parents=True, mode=0o700)
    (backup / '.env').write_text(original_env, encoding='utf-8')
    (backup / '.env').chmod(0o600)
    if original_override is not None:
        (backup / OVERRIDE).write_bytes(original_override)
    lines = original_env.splitlines()
    values = [line.split('=', 1)[1].strip().strip('"\'') for line in lines if line.startswith('COMPOSE_FILE=')]
    if len(values) > 1:
        raise ValueError('Flere COMPOSE_FILE-værdier kræver manuel kontrol.')
    files = compose_files(values[0] if values else '')
    updated_env = '\n'.join([line for line in lines if not line.startswith('COMPOSE_FILE=')] + ['COMPOSE_FILE=' + ':'.join(files)]) + '\n'
    try:
        atomic_write(override, (json.dumps(content, indent=2) + '\n').encode())
        atomic_write(env_path, updated_env.encode())
        plan(path, directory)  # Validate the effective Compose configuration before recreation.
        run(['docker', 'compose', 'up', '-d', '--no-build', '--no-deps', '--force-recreate', '--wait', '--wait-timeout', '120', 'app'], directory)
    except Exception:
        atomic_write(env_path, original_env.encode())
        if original_override is None:
            override.unlink(missing_ok=True)
        else:
            atomic_write(override, original_override)
        try:
            run(['docker', 'compose', 'up', '-d', '--no-build', '--no-deps', 'app'], directory)
        except Exception:
            pass
        raise ValueError('Docker-ændringen fejlede. De tidligere konfigurationsfiler er gendannet; kontrollér FjordFlix. Backup: ' + str(backup)) from None
    # Actual create/read/delete test, limited to a new random temporary file.
    probe = 'import tempfile,sys; f=tempfile.TemporaryFile(dir=sys.argv[1]); f.write(b"fjordhub"); f.seek(0); assert f.read()==b"fjordhub"; f.close()'
    run(['docker', 'exec', 'fjordflix', 'python', '-c', probe, target])
    print('Skriveadgang testet i ' + target + '. Konfigurationsbackup: ' + str(backup))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['check', 'enable'])
    parser.add_argument('path')
    args = parser.parse_args()
    directory = Path(os.getenv('APPS_DIR', '/apps')) / 'fjordflix'
    # Separate command executions must not overwrite one another's grants.
    import fcntl
    with (directory / '.library-permissions.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if args.action == 'check':
            print(plan(args.path, directory))
        else:
            enable(args.path, directory)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(str(exc)) from None
