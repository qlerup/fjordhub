"""Real Compose merging and real file transfer; Docker lifecycle is simulated."""
import json
import os
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from services.app_storage import AppStorage
from services.install_state import InstallState
from services.lens_storage import media_locations, write_override, configure
from services.storage_copy import transfer, cleanup


@pytest.fixture
def migration(tmp_path):
    checkout = Path(__file__).parents[2] / 'fjordlens'
    if not shutil.which('docker') or not checkout.is_dir():
        pytest.skip('Requires Docker Compose CLI and FjordLens checkout')
    directory = tmp_path / 'app'
    directory.mkdir()
    for name in ('docker-compose.yml', 'docker-compose.gpu.yml'):
        shutil.copyfile(checkout / name, directory / name)
    env = directory / '.env'
    env.write_text('COMPOSE_PROJECT_NAME=lens-test\nCOMPOSE_FILE=docker-compose.yml:docker-compose.gpu.yml\n'
                   'DATA_DIR=/srv/lens/data\nUPLOADS_HOST_DIR=/srv/lens/uploads\n'
                   'THUMBS_HOST_DIR=/srv/lens/thumbs\n', encoding='utf-8')
    state = InstallState(tmp_path)
    state.set_installing('fjordlens', str(directory))
    manager = Mock()
    storage = AppStorage(manager, state)
    definition = json.loads((checkout.parent / 'fjordhub/app_registry/fjordlens.json').read_text(encoding='utf-8'))
    events, containers = [], []

    def refresh(status='exited'):
        config = storage.configuration(directory)
        containers[:] = [SimpleNamespace(
            labels={'com.docker.compose.project': config['name'], 'com.docker.compose.service': name}, status=status,
            attrs={'Mounts': [{'Type': v['type'], 'Source': v.get('source'), 'Destination': v['target']}
                               for v in service.get('volumes', [])]})
            for name, service in config['services'].items()]

    def compose(directory, args, extra=None, timeout=60):
        if args[0] == 'config':
            result = subprocess.run(['docker', 'compose', *args], cwd=directory,
                env={**os.environ, 'COMPOSE_PATH_SEPARATOR': ':', **(extra or {})}, capture_output=True, text=True, timeout=timeout)
            assert result.returncode == 0, result.stderr
            return result.stdout
        events.append(args[0])
        if args[0] == 'create':
            refresh()
        if args[0] == 'up':
            for container in containers:
                if container.labels['com.docker.compose.service'] in args:
                    container.status = 'running'
        return ''

    storage.compose = Mock(side_effect=compose)
    refresh('running')
    manager.client.containers.list.side_effect = lambda **kwargs: containers

    def local(path):
        return tmp_path / 'host' / path.lstrip('/')

    def helper(source, destination, mode, seal=''):
        events.append(mode)
        if mode == 'cleanup':
            return cleanup(local(source), local(destination), seal)
        return transfer(local(source), local(destination), check_only=mode == 'check',
                        prepare_move=mode == 'prepare-move', progress=lambda value: storage.save('fjordlens', progress=value))

    storage.helper = Mock(side_effect=helper)
    storage.ensure_destination = lambda path: local(path).mkdir(parents=True, exist_ok=True)
    storage.require_mount = Mock()
    for folder in ('originals', 'converted'):
        path = local('/srv/lens/uploads/' + folder) / 'album'
        path.mkdir(parents=True)
        (path / 'image.jpg').write_bytes((folder + ' image bytes').encode())
    # Legacy root uploads must also remain reachable after child mounts are added.
    local('/srv/lens/uploads/legacy.jpg').write_bytes(b'legacy root file')
    return SimpleNamespace(storage=storage, definition=definition, directory=directory,
                           env=env, local=local, containers=containers, events=events, refresh=refresh)


def run(m, key='ORIGINALS_HOST_DIR', destination='/mnt/nas/originals', source='/srv/lens/uploads/originals', mode='move', job='abc123'):
    m.storage.save('fjordlens', id=job, running=True, source=source, destination=destination)
    m.storage.active.add('fjordlens')
    m.storage.run(m.definition, key, destination, source, mode)
    return m.storage.job('fjordlens')


def test_move_from_shared_and_move_back_preserves_paths_data_and_gpu(migration):
    m = migration
    before = m.storage.configuration(m.directory)
    result = run(m)
    assert not result.get('error'), result
    assert m.events == ['check', 'stop', 'prepare-move', 'create', 'up', 'cleanup']
    assert m.local('/mnt/nas/originals/album/image.jpg').read_bytes() == b'originals image bytes'
    assert not list(m.local('/srv/lens/uploads/originals').iterdir())
    assert m.local('/srv/lens/uploads/converted/album/image.jpg').read_bytes() == b'converted image bytes'
    assert m.local('/srv/lens/uploads/legacy.jpg').read_bytes() == b'legacy root file'
    after = m.storage.configuration(m.directory)
    assert before['services']['fjordlens-convert']['gpus'] == after['services']['fjordlens-convert']['gpus']
    assert before['services']['fjordlens-convert']['devices'] == after['services']['fjordlens-convert']['devices']
    assert before['services']['fjordlens']['environment'] == after['services']['fjordlens']['environment']
    assert {r['key']: r['path'] for r in media_locations(after)} == {
        'ORIGINALS_HOST_DIR': '/mnt/nas/originals', 'CONVERTED_HOST_DIR': '/srv/lens/uploads/converted'}
    result = run(m, source='/mnt/nas/originals', destination='/srv/lens/uploads/originals', job='abc124')
    assert not result.get('error'), result
    assert m.local('/srv/lens/uploads/originals/album/image.jpg').read_bytes() == b'originals image bytes'
    assert not list(m.local('/mnt/nas/originals').iterdir())


def test_copy_and_then_move_converted_independently(migration):
    m = migration
    assert not run(m, mode='copy').get('error')
    assert m.local('/srv/lens/uploads/originals/album/image.jpg').exists()
    result = run(m, key='CONVERTED_HOST_DIR', source='/srv/lens/uploads/converted', destination='/mnt/ssd/converted', job='abc125')
    assert not result.get('error'), result
    assert m.local('/mnt/ssd/converted/album/image.jpg').read_bytes() == b'converted image bytes'
    paths = {r['key']: r['path'] for r in media_locations(m.storage.configuration(m.directory))}
    assert paths == {'ORIGINALS_HOST_DIR': '/mnt/nas/originals', 'CONVERTED_HOST_DIR': '/mnt/ssd/converted'}


def test_stopped_installation_gets_new_mounts_without_starting(migration):
    m = migration
    m.refresh('exited')
    result = run(m)
    assert not result.get('error'), result
    assert 'create' in m.events and 'up' not in m.events
    assert all(c.status == 'exited' for c in m.containers)


@pytest.mark.parametrize('failure', ['prepare-move', 'create', 'up', 'cleanup'])
def test_failures_preserve_originals_and_restore_config_before_cleanup(migration, failure):
    m = migration
    old = m.env.read_text(encoding='utf-8')
    tool = m.storage.helper if failure in ('prepare-move', 'cleanup') else m.storage.compose
    previous = tool.side_effect
    failed = False
    def fail(*args, **kwargs):
        nonlocal failed
        action = args[2] if tool is m.storage.helper else args[1][0]
        if action == failure and not failed:
            failed = True
            raise RuntimeError('injected failure')
        return previous(*args, **kwargs)
    tool.side_effect = fail
    result = run(m)
    assert failed, result
    assert result.get('error')
    assert m.local('/srv/lens/uploads/originals/album/image.jpg').read_bytes() == b'originals image bytes'
    if failure == 'cleanup':
        assert result['phase'] == 'cleanup_incomplete'
        assert m.env.read_text(encoding='utf-8') != old
    else:
        assert m.env.read_text(encoding='utf-8') == old
        assert not list(m.directory.glob('docker-compose.fjordhub-storage-*.yml'))


@pytest.mark.parametrize('destination', ['/srv/lens/uploads/converted', '/srv/lens/uploads/converted/nested', '/srv/lens/uploads'])
def test_rejects_overlap_without_stopping(migration, destination):
    m = migration
    result = run(m, destination=destination)
    assert result.get('error')
    assert 'stop' not in m.events


def test_nonempty_destination_does_not_stop_or_overwrite(migration):
    m = migration
    m.local('/mnt/nas/originals').mkdir(parents=True)
    existing = m.local('/mnt/nas/originals/keep.jpg')
    existing.write_bytes(b'keep me')
    result = run(m)
    assert result.get('error')
    assert 'stop' not in m.events
    assert existing.read_bytes() == b'keep me'


def test_already_split_installation_can_move_again(migration):
    m = migration
    values = {'FJORDLENS_STORAGE_MODE': 'split', 'ORIGINALS_HOST_DIR': '/srv/lens/uploads/originals',
              'CONVERTED_HOST_DIR': '/srv/lens/uploads/converted',
              'COMPOSE_FILE': 'docker-compose.yml:docker-compose.gpu.yml'}
    configure(values)
    write_override(m.directory, values)
    with m.env.open('a', encoding='utf-8') as stream:
        for key, value in values.items():
            stream.write(f'{key}={value}\n')
    m.refresh('running')
    result = run(m)
    assert not result.get('error'), result
    assert m.local('/mnt/nas/originals/album/image.jpg').read_bytes() == b'originals image bytes'


def test_unexpected_runtime_mount_is_rejected_before_stop(migration):
    m = migration
    web = next(c for c in m.containers if c.labels['com.docker.compose.service'] == 'fjordlens')
    web.attrs['Mounts'].append({'Type': 'bind', 'Source': '/other/files', 'Destination': '/uploads/converted'})
    result = run(m)
    assert result.get('error')
    assert 'stop' not in m.events


def test_failed_mount_activation_rolls_back_before_deleting(migration):
    m = migration
    old = m.env.read_text(encoding='utf-8')
    previous = m.storage.compose.side_effect
    def wrong_mount(directory, args, *rest, **kwargs):
        value = previous(directory, args, *rest, **kwargs)
        if args[0] == 'up':
            web = next(c for c in m.containers if c.labels['com.docker.compose.service'] == 'fjordlens')
            for mount in web.attrs['Mounts']:
                if mount['Destination'] == '/uploads/originals':
                    mount['Source'] = '/unexpected/files'
        return value
    m.storage.compose.side_effect = wrong_mount
    result = run(m)
    assert result.get('error')
    assert 'cleanup' not in m.events
    assert m.env.read_text(encoding='utf-8') == old
    assert m.local('/srv/lens/uploads/originals/album/image.jpg').exists()


def test_missing_source_mount_prevents_copy(migration):
    m = migration
    m.storage.require_mount.side_effect = ValueError('Source mount missing')
    result = run(m)
    assert result.get('error')
    assert not m.events


def test_stale_source_prevents_copy(migration):
    result = run(migration, source='/wrong/source')
    assert result.get('error')
    assert not migration.events


def test_source_also_used_as_library_is_not_moved(migration):
    m = migration
    web = next(c for c in m.containers if c.labels['com.docker.compose.service'] == 'fjordlens')
    for mount in web.attrs['Mounts']:
        if mount['Destination'] == '/photos':
            mount['Source'] = '/srv/lens/uploads'
    result = run(m)
    assert 'fotobibliotek' in result.get('error', ''), result
    assert 'stop' not in m.events
