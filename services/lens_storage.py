"""Installation-time storage layout for FjordLens; container paths stay stable."""
import json
import copy
import re
from pathlib import PurePosixPath

OVERRIDE = 'docker-compose.fjordhub-storage.yml'
MEDIA = {'ORIGINALS_HOST_DIR': ('originals', 'Originaler'),
         'CONVERTED_HOST_DIR': ('converted', 'Konverterede filer')}


def media_locations(config):
    """Resolve effective child paths, including older shared-parent installs."""
    result = []
    for key, (folder, label) in MEDIA.items():
        target = PurePosixPath('/uploads') / folder
        mounts = []
        for name in ('fjordlens', 'fjordlens-convert'):
            service = config.get('services', {}).get(name)
            if not service or service.get('environment', {}).get('UPLOAD_DIR') != '/uploads':
                raise ValueError('Denne Fjordlens-version skal opdateres før separat flytning.')
            candidates = [v for v in service.get('volumes', [])
                          if PurePosixPath(v['target']) == target or PurePosixPath(v['target']) in target.parents]
            if not candidates:
                raise ValueError('Upload-lageret kunne ikke findes i konfigurationen.')
            mount = max(candidates, key=lambda v: len(PurePosixPath(v['target']).parts))
            if mount.get('type') != 'bind' or mount.get('read_only'):
                raise ValueError('Flytning kræver et skrivbart mappe-mount til uploads.')
            if any(target in PurePosixPath(v['target']).parents for v in service.get('volumes', [])):
                raise ValueError('Upload-mappen har ekstra mounts. Flyt dem separat først.')
            path = str(PurePosixPath(mount['source']) / target.relative_to(mount['target']))
            mounts.append({'service': name, 'target': mount['target'], 'source': mount['source'],
                           'effective_source': path})
        sources = {v['effective_source'] for v in mounts}
        if len(sources) != 1:
            raise ValueError('Fjordlens og konverteringstjenesten bruger forskellige mapper.')
        result.append({'key': key, 'label': label, 'path': sources.pop(), 'mounts': mounts,
                       'hint': 'Kan flyttes separat til lokal disk eller monteret NAS/NFS. Upload, download og filreferencer bevares.'})
    return result


def migration_config(storage, directory, current, key, destination, job_id, old_env):
    """Prepare an immutable override; only .env is changed at commit time."""
    from services.app_storage import patched_env
    locations = media_locations(current)
    values = {row['key']: row['path'] for row in locations}
    values[key] = destination
    paths = [PurePosixPath(values[k]) for k in MEDIA]
    if paths[0] == paths[1] or paths[0] in paths[1].parents or paths[1] in paths[0].parents:
        raise ValueError('Originaler og konverterede filer må ikke ligge i samme mappe eller inde i hinanden.')
    # Obtain Compose's own interpolation of .env, never log the output (secrets).
    environment = dict(line.split('=', 1) for line in storage.compose(directory, ['config', '--environment']).splitlines() if '=' in line)
    files = environment.get('COMPOSE_FILE', 'docker-compose.yml').split(':')
    files = [f for f in files if not re.fullmatch(r'docker-compose\.fjordhub-storage-[a-f0-9]+\.yml', f)]
    if not re.fullmatch(r'[a-f0-9]+', job_id):
        raise ValueError('Ugyldigt flyttejob.')
    filename = f'docker-compose.fjordhub-storage-{job_id}.yml'
    values['COMPOSE_FILE'] = ':'.join([*files, filename])
    values['FJORDLENS_STORAGE_MODE'] = 'split'
    volumes = [{'type': 'bind', 'source': '${' + k + '}', 'target': '/uploads/' + v[0]} for k, v in MEDIA.items()]
    overlay = {'services': {name: {'volumes': volumes} for name in ('fjordlens', 'fjordlens-convert')}}
    path = directory / filename
    with path.open('x', encoding='utf-8') as stream:
        json.dump(overlay, stream, indent=2)
    try:
        proposed = storage.configuration(directory, values)
        # Only these two mounts may change. Everything else must stay identical,
        # including root uploads, GPU settings, database and legacy upload files.
        def normalized(config):
            value = copy.deepcopy(config)
            updater = value['services'].get('fjordlens-updater', {}).get('environment', {})
            if 'COMPOSE_FILE' in updater:
                updater['COMPOSE_FILE'] = '<compose-files>'
            for name in ('fjordlens', 'fjordlens-convert'):
                value['services'][name]['volumes'] = [v for v in value['services'][name].get('volumes', [])
                    if v['target'] not in ('/uploads/originals', '/uploads/converted')]
            return value
        if normalized(current) != normalized(proposed):
            raise ValueError('Skiftet ændrer andet end mediefilernes placering. Skiftet er afbrudt.')
        if {row['key']: row['path'] for row in media_locations(proposed)} != {k: values[k] for k in MEDIA}:
            raise ValueError('De nye mediemapper kunne ikke kontrolleres.')
        new_env = old_env
        for name, value in values.items():
            new_env = patched_env(new_env, name, value)
        return new_env, path, proposed
    except Exception:
        path.unlink()
        raise


def validate_media_containers(config, containers):
    """Check both media trees, including unexpected mounts below their parents."""
    expected = {row['key']: row['path'] for row in media_locations(config)}
    actual = copy.deepcopy(config)
    for name in ('fjordlens', 'fjordlens-convert'):
        matches = [c for c in containers if c.labels.get('com.docker.compose.service') == name]
        if len(matches) != 1:
            raise ValueError('Fjordlens og konverteringstjenesten skal være installeret før flytning.')
        actual['services'][name]['volumes'] = [
            {'type': m.get('Type'), 'source': m.get('Source', ''), 'target': m['Destination'],
             'read_only': m.get('RW') is False}
            for m in matches[0].attrs.get('Mounts', [])]
    if {row['key']: row['path'] for row in media_locations(actual)} != expected:
        raise ValueError('Appens mediemapper svarer ikke til konfigurationen. De gamle filer bevares.')


def configure(values):
    mode = values.setdefault('FJORDLENS_STORAGE_MODE', 'shared')
    if mode not in ('shared', 'split'):
        raise ValueError('Vælg fælles eller opdelt lager til Fjordlens.')
    files = [f for f in values.get('COMPOSE_FILE', 'docker-compose.yml').split(':') if f != OVERRIDE]
    if mode == 'shared':
        # Hidden defaults must not create unused folders or activate split storage.
        values.pop('ORIGINALS_HOST_DIR', None)
        values.pop('CONVERTED_HOST_DIR', None)
    else:
        from services.app_storage import host_path
        keys = ('ORIGINALS_HOST_DIR', 'CONVERTED_HOST_DIR')
        for key in keys:
            values[key] = host_path(values.get(key, ''))
        paths = [PurePosixPath(values[k]) for k in keys]
        if paths[0] == paths[1] or paths[0] in paths[1].parents or paths[1] in paths[0].parents:
            raise ValueError('Originaler og konverterede filer skal have hver sin mappe uden overlap.')
        values.pop('UPLOADS_HOST_DIR', None)
        files.append(OVERRIDE)
    values['COMPOSE_FILE'] = ':'.join(files)


def write_override(directory, values):
    if values.get('FJORDLENS_STORAGE_MODE') != 'split':
        return
    volumes = [
        {'type': 'bind', 'source': '${DATA_DIR}/uploads', 'target': '/uploads'},
        {'type': 'bind', 'source': '${ORIGINALS_HOST_DIR}', 'target': '/uploads/originals'},
        {'type': 'bind', 'source': '${CONVERTED_HOST_DIR}', 'target': '/uploads/converted'},
    ]
    config = {'services': {name: {'volumes': volumes} for name in ('fjordlens', 'fjordlens-convert')}}
    (directory / OVERRIDE).write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
