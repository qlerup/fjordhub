import json
import subprocess
from unittest.mock import patch

import pytest

from services.uninstaller import remove_runtime


def response(output='', code=0):
    return subprocess.CompletedProcess([], code, output, 'failure' if code else '')


def test_runtime_removal_preserves_all_files_and_never_removes_volumes(tmp_path):
    media = tmp_path / 'data' / 'movie.mp4'
    media.parent.mkdir()
    media.write_bytes(b'original media')
    env = tmp_path / '.env'
    env.write_text('DATA_DIR=./data\n')
    with patch('services.uninstaller.subprocess.run', side_effect=[
        response(json.dumps({'name': 'fjordflix-hub'})),
        response('container-id fjordflix-hub'), response(), response(),
    ]) as run:
        remove_runtime({'container_name': 'fjordflix'}, tmp_path)
    commands = [call.args[0] for call in run.call_args_list]
    assert commands[2] == ['docker', 'compose', 'down', '--remove-orphans', '--timeout', '20']
    assert all('--volumes' not in args and '--rmi' not in args for args in commands)
    assert media.read_bytes() == b'original media'
    assert env.read_text() == 'DATA_DIR=./data\n'


@pytest.mark.parametrize('name', ['fjordflix', 'fjordhub'])
def test_uninstall_keeps_writable_mounts_and_permission_overrides(tmp_path, name):
    directory = tmp_path / 'installation'
    directory.mkdir()
    external = tmp_path / 'media-pool'
    external.mkdir()
    movie = external / 'original.mp4'
    movie.write_bytes(b'original mounted media')
    override = directory / 'docker-compose.fjordhub-library.yml'
    override.write_text(json.dumps({'services': {'app': {'volumes': [{
        'type': 'bind', 'source': str(external), 'target': '/library/server/Film', 'read_only': False}]}}}))
    env = directory / '.env'
    env.write_text('COMPOSE_FILE=docker-compose.yml:docker-compose.fjordhub-library.yml\n')
    original = {p: p.read_bytes() for p in (movie, override, env)}
    config = {'name': name, 'services': {'app': {'volumes': [
        {'type': 'bind', 'source': str(external), 'target': '/library/server/Film', 'read_only': False},
        {'type': 'volume', 'source': 'persistent', 'target': '/data'}]}}}
    with patch('services.uninstaller.subprocess.run', side_effect=[
        response(json.dumps(config)), response('id ' + name), response(), response(),
    ]) as run:
        remove_runtime({'container_name': name}, directory)
    for path, contents in original.items():
        assert path.read_bytes() == contents
    # The same storage-preserving runtime path serves both the app and hub CLI.
    assert [call.args[0] for call in run.call_args_list][2] == [
        'docker', 'compose', 'down', '--remove-orphans', '--timeout', '20']
    assert all(call.kwargs['cwd'] == str(directory) for call in run.call_args_list)


def test_hub_uninstall_cli_uses_runtime_only(tmp_path, monkeypatch, capsys):
    from scripts import uninstall
    monkeypatch.setattr('sys.argv', ['uninstall.py', '--directory', str(tmp_path)])
    with patch.object(uninstall, 'remove_runtime') as remove:
        uninstall.main()
    remove.assert_called_once_with({'container_name': 'fjordhub'}, tmp_path, required_service='fjordhub')
    assert 'LXC-containeren er ikke slettet' in capsys.readouterr().out


def test_hub_uninstall_cli_does_not_claim_success_on_failure(tmp_path, monkeypatch, capsys):
    from scripts import uninstall
    monkeypatch.setattr('sys.argv', ['uninstall.py', '--directory', str(tmp_path)])
    with patch.object(uninstall, 'remove_runtime', side_effect=RuntimeError('Docker failed')):
        with pytest.raises(SystemExit) as error:
            uninstall.main()
    assert error.value.code == 1
    output = capsys.readouterr()
    assert not output.out and 'Docker failed' in output.err


def test_hub_uninstall_rejects_another_apps_compose_directory(tmp_path):
    with patch('services.uninstaller.subprocess.run', return_value=response(json.dumps({
        'name': 'fjordflix-hub', 'services': {'app': {'container_name': 'fjordflix'}}}))) as run:
        with pytest.raises(RuntimeError, match='ikke den forventede'):
            remove_runtime({'container_name': 'fjordhub'}, tmp_path, required_service='fjordhub')
    assert run.call_count == 1


@pytest.mark.parametrize('existing', ['container-id other-project', 'container-id'])
def test_foreign_or_unlabelled_container_is_not_removed(tmp_path, existing):
    with patch('services.uninstaller.subprocess.run', side_effect=[
        response('{"name":"fjordflix-hub"}'), response(existing),
    ]) as run:
        with pytest.raises(RuntimeError, match='anden eller ukendt'):
            remove_runtime({'container_name': 'fjordflix'}, tmp_path)
    assert run.call_count == 2


def test_missing_compose_directory_fails_without_docker(tmp_path):
    with patch('services.uninstaller.subprocess.run') as run:
        with pytest.raises(RuntimeError, match='mangler'):
            remove_runtime({}, tmp_path / 'missing')
        run.assert_not_called()


@pytest.mark.parametrize('failure', ['docker', 'timeout', 'remaining'])
def test_cleanup_must_be_verified(tmp_path, failure):
    results = [response('{"name":"fjordflix-hub"}'), response()]
    if failure == 'docker':
        results += [response(code=1)]
    elif failure == 'timeout':
        results += [subprocess.TimeoutExpired('docker', 90)]
    else:
        results += [response(), response('still-present')]
    with patch('services.uninstaller.subprocess.run', side_effect=results):
        with pytest.raises((RuntimeError, subprocess.TimeoutExpired)):
            remove_runtime({'container_name': 'fjordflix'}, tmp_path)


@pytest.mark.parametrize('failure', [None, 'docker', 'busy', 'storage'])
def test_endpoint_preserves_registration_and_key_until_success(tmp_path, failure):
    import app as hub
    from services.auth import AuthService
    from services.installer import Installer
    from services.install_state import InstallState

    auth = AuthService(tmp_path / 'auth.db')
    auth.create_user('delete-admin', 'test-password', role='admin')
    auth.save_hub_key('fjordflix', 'existing-app-key')
    state = InstallState(tmp_path)
    state.register('fjordflix', str(tmp_path))
    installer = Installer(state)
    if failure == 'busy':
        installer._active_installs.add('fjordflix')
    if failure == 'storage':
        state.set_storage_job('fjordflix', {'running': True})
    with patch.object(hub, '_auth', auth), patch.object(hub, '_install_state', state), \
         patch.object(hub, '_installer', installer), \
         patch.object(hub, '_get_app', return_value={'id': 'fjordflix'}), \
         patch.object(hub, 'remove_runtime', side_effect=RuntimeError('Docker failed') if failure == 'docker' else None) as remove:
        with hub.app.test_client() as client:
            client.post('/login', data={'username': 'delete-admin', 'password': 'test-password'})
            result = client.post('/apps/fjordflix/uninstall')
    if failure:
        assert result.status_code == 409
        assert not result.json['ok']
        assert state.get_install_dir('fjordflix') == str(tmp_path)
        assert auth.verify_hub_key('fjordflix', 'existing-app-key')
        if failure != 'docker':
            remove.assert_not_called()
    else:
        assert result.status_code == 200
        assert result.json['data_preserved']
        assert state.get('fjordflix') == {}
        assert not auth.get_hub_key('fjordflix')
        assert tmp_path.is_dir()
    assert ('fjordflix' in installer._active_installs) == (failure == 'busy')


def test_uninstall_reservation_blocks_installer_and_releases_after_error(tmp_path):
    from services.installer import Installer
    from services.install_state import InstallState

    installer = Installer(InstallState(tmp_path))
    with pytest.raises(RuntimeError, match='cleanup failed'):
        with installer.reserve_operation('fjordflix'):
            assert not installer.start_install({'id': 'fjordflix'}, {})
            with pytest.raises(RuntimeError, match='allerede'):
                with installer.reserve_operation('fjordflix'):
                    pass
            raise RuntimeError('cleanup failed')
    assert not installer._active_installs
