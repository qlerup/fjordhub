import json
from pathlib import Path, PurePosixPath
import shlex
from unittest.mock import Mock

import pytest

from services import library_permissions as access
from services.media_library import write_guide
from scripts import library_write_host as host


def configuration(extra=()):
    return {'services': {'app': {'container_name': 'fjordflix', 'volumes': [
        {'type': 'bind', 'source': '/mnt', 'target': '/library/server', 'read_only': True},
        {'type': 'bind', 'source': '/media/uploads', 'target': '/media'}, *extra]}}}


def fake_docker(monkeypatch, configuration_value):
    calls = []
    def run(args, cwd=None):
        calls.append(args)
        if args[:2] == ['docker', 'info']:
            return '[]'
        if args[1:3] == ['compose', 'config']:
            result = configuration_value()
            if cwd and (cwd / access.OVERRIDE).exists():
                result['services']['app']['volumes'].extend(json.loads((cwd / access.OVERRIDE).read_text())['services']['app']['volumes'])
            return json.dumps(result)
        return ''
    monkeypatch.setattr(access, 'run', run)
    return calls, run


@pytest.mark.parametrize('path', ['/mnt', '/etc/passwd', '/mnt/../etc', '/mnt/$(id)', '/mnt/a\nreboot', '/mnt/a//b', '/mnt/a/.'])
def test_unsafe_paths_have_no_guide(path):
    assert not write_guide('1000', 'mp0', path, '/mnt/Film')
    assert not write_guide('1000', 'mp0', '/mnt/media', path)


def test_guide_is_reviewable_and_handles_spaces():
    result = write_guide('1000', 'mp7', '/mnt/Media Pool', '/mnt/Film')
    command, program = result['commands'].split('\n', 1)
    assert shlex.split(command)[:6] == ['python3', '-', '1000', 'mp7', '/mnt/Media Pool', '/mnt/Film']
    compile(program.rsplit('\nFJORDHUB_WRITE_ACCESS', 1)[0], '<guide>', 'exec')
    assert '--file-permissions' not in command
    assert '--file-permissions' in result['permissions_commands'].splitlines()[0]
    assert write_guide('1000;reboot', 'mp0', '/mnt/media', '/mnt/Film') is None
    assert write_guide('1000', 'rootfs', '/mnt/media', '/mnt/Film') is None


def test_scoped_override_preserves_gpu_other_paths_and_env(monkeypatch, tmp_path):
    monkeypatch.setenv('DATA_DIR', str(tmp_path / 'private'))
    (tmp_path / '.env').write_text('SECRET=value\nCOMPOSE_FILE=docker-compose.yml:docker-compose.gpu.yml\n')
    calls, _ = fake_docker(monkeypatch, configuration)
    access.enable('/mnt/Film', tmp_path)
    result = json.loads((tmp_path / access.OVERRIDE).read_text())
    assert result['services']['app']['volumes'] == [{'type': 'bind', 'source': '/mnt/Film',
        'target': '/library/server/Film', 'read_only': False, 'bind': {'create_host_path': False}}]
    assert 'SECRET=value' in (tmp_path / '.env').read_text()
    assert 'docker-compose.yml:docker-compose.gpu.yml:' + access.OVERRIDE in (tmp_path / '.env').read_text()
    access.enable('/mnt/Serier', tmp_path)
    result = json.loads((tmp_path / access.OVERRIDE).read_text())
    assert len(result['services']['app']['volumes']) == 2
    access.enable('/mnt/Film', tmp_path)
    assert len(json.loads((tmp_path / access.OVERRIDE).read_text())['services']['app']['volumes']) == 2
    assert any(args[:3] == ['docker', 'exec', 'fjordflix'] for args in calls)
    assert all('down' not in args for args in calls)


def test_recreate_failure_restores_private_config(monkeypatch, tmp_path):
    monkeypatch.setenv('DATA_DIR', str(tmp_path / 'private'))
    original = 'SECRET=value\n'
    (tmp_path / '.env').write_text(original)
    calls, run = fake_docker(monkeypatch, configuration)
    def fail(args, cwd=None):
        if '--force-recreate' in args:
            raise ValueError('failed')
        return run(args, cwd)
    monkeypatch.setattr(access, 'run', fail)
    with pytest.raises(ValueError, match='gendannet'):
        access.enable('/mnt/Film', tmp_path)
    assert (tmp_path / '.env').read_text() == original
    assert not (tmp_path / access.OVERRIDE).exists()
    assert list((tmp_path / 'private').rglob('.env'))[0].read_text() == original


@pytest.mark.parametrize('extra', [
    [{'type': 'bind', 'source': '/other', 'target': '/library/server/Film'}],
    [{'type': 'bind', 'source': '/other', 'target': '/library/server/Film/Private'}],
])
def test_refuses_overlapping_mounts(monkeypatch, tmp_path, extra):
    fake_docker(monkeypatch, lambda: configuration(extra))
    with pytest.raises(ValueError):
        access.plan('/mnt/Film', tmp_path)


def test_parent_and_outside_library_are_refused(monkeypatch, tmp_path):
    fake_docker(monkeypatch, configuration)
    for path in ['/mnt', '/srv/Film']:
        with pytest.raises(ValueError):
            access.plan(path, tmp_path)


def test_proxmox_change_preserves_all_existing_mount_options():
    old = '/mnt/Film,mp=/mnt/Film,ro=1,backup=0,acl=1,mountoptions=noatime'
    assert host.write_value(old) == '/mnt/Film,mp=/mnt/Film,backup=0,acl=1,mountoptions=noatime,ro=0'


def test_changed_mount_aborts_before_any_command(monkeypatch):
    class FakePath(PurePosixPath):
        def is_dir(self): return True
        def resolve(self): return self
    monkeypatch.setattr(host, 'Path', FakePath)
    monkeypatch.setattr(host, 'config', lambda ctid: {'mp0': '/mnt/other,mp=/mnt/Film,ro=1', 'digest': 'test'})
    commands = Mock()
    monkeypatch.setattr(host, 'run', commands)
    with pytest.raises(ValueError, match='ændret'):
        host.apply('1000', 'mp0', '/mnt/source', '/mnt/Film')
    commands.assert_not_called()


def test_nested_filesystem_aborts_before_mutation(monkeypatch):
    class FakePath(PurePosixPath):
        def is_dir(self): return True
        def resolve(self): return self
    monkeypatch.setattr(host, 'Path', FakePath)
    monkeypatch.setattr(host, 'config', lambda ctid: {'mp0': '/mnt/source,mp=/mnt/Film,ro=1', 'digest': 'test'})
    commands = Mock(return_value=json.dumps({'filesystems': [{'target': '/mnt/source/private'}]}))
    monkeypatch.setattr(host, 'run', commands)
    with pytest.raises(ValueError, match='andre monteringer'):
        host.apply('1000', 'mp0', '/mnt/source', '/mnt/Film')
    assert len(commands.call_args_list) == 1
    assert commands.call_args.args[0][0] == 'findmnt'


def test_reinstall_retains_explicit_write_grants(monkeypatch, tmp_path):
    from services import installer
    monkeypatch.setattr(installer, 'APPS_BASE', tmp_path)
    monkeypatch.setattr(installer, 'DATA_BASE', tmp_path / 'data')
    monkeypatch.setattr(installer, '_container_path_to_host_path', lambda p: str(p))
    directory = tmp_path / 'fjordflix'
    directory.mkdir()
    (directory / access.OVERRIDE).write_text('{}')
    instance = installer.Installer.__new__(installer.Installer)
    result = instance._resolve_env_values({'id': 'fjordflix'}, {'ENABLE_GPU_COMPOSE': '1'})
    assert result['COMPOSE_FILE'].endswith('docker-compose.fjordhub-gpu.yml:' + access.OVERRIDE)


def test_host_workflow_scopes_change_and_maps_uid(monkeypatch, tmp_path):
    source = str(tmp_path / 'pool')
    Path(source).mkdir()
    uid_map = tmp_path / 'uid_map'
    uid_map.write_text('0 234000 65536\n')
    real_path = Path
    def mapped_path(value):
        if str(value).startswith('/root/'):
            return tmp_path / str(value).removeprefix('/root/')
        if str(value) == '/proc/123/uid_map':
            return uid_map
        return real_path(value)
    monkeypatch.setattr(host, 'Path', mapped_path)
    # Path policy has separate tests; use this fixture's private Windows/Linux directory.
    monkeypatch.setattr(host, 'safe_path', lambda p: p in (source, '/mnt/Film'))
    monkeypatch.setattr(host.shutil, 'copyfile', lambda source, dest: dest.write_text('backup'))
    monkeypatch.setattr(host.shutil, 'which', lambda name: '/usr/bin/' + name)
    cfg = {'mp7': source + ',mp=/mnt/Film,ro=1,backup=0,acl=1', 'digest': 'exact-version'}
    monkeypatch.setattr(host, 'config', lambda ctid: dict(cfg))
    calls, acl = [], []
    def run(args, timeout=180):
        calls.append(args)
        if args[0] == 'findmnt': return '{"filesystems":[]}'
        if args[-2:] == ['id', '-u']: return '42'
        if args[0] == 'lxc-info': return '123'
        if 'findmnt' in args: return '{"filesystems":[{"target":"/mnt/Film","options":"rw"}]}'
        return 'passed'
    def acl_run(args, **kwargs):
        acl.append(args)
        if 'stdout' in kwargs: kwargs['stdout'].write('acl backup')
    monkeypatch.setattr(host, 'run', run)
    monkeypatch.setattr(host.subprocess, 'run', acl_run)
    host.apply('1000', 'mp7', source, '/mnt/Film', True)
    assert [args for args in calls if args[:2] == ['pct', 'set']] == [[
        'pct', 'set', '1000', '--digest', 'exact-version', '--mp7', source + ',mp=/mnt/Film,backup=0,acl=1,ro=0']]
    assert ['setfacl', '-R', '-P', '-m', 'u:234042:rwX', '--', source] in acl
    assert any(args[:3] == ['pct', 'reboot', '1000'] for args in calls)
    assert list(tmp_path.rglob('permissions.acl'))[0].read_text() == 'acl backup'
    calls.clear()
    cfg['mp7'] = host.write_value(cfg['mp7'])
    host.apply('1000', 'mp7', source, '/mnt/Film')
    assert not any(args[:2] in [['pct', 'set'], ['pct', 'reboot']] for args in calls)
