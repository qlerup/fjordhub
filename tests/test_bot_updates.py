import asyncio
import json
from types import SimpleNamespace
from unittest.mock import Mock, AsyncMock, patch

from services.bot_updates import handle_updates
from services import matrix_bot


def setup(tmp_path):
    config = {'allowed_users': ['@owner:test', '@reader:test'], 'update_users': ['@owner:test']}
    def load(path):
        try:
            return json.loads(path.read_text())
        except FileNotFoundError:
            return {}
    def save(path, value):
        path.write_text(json.dumps(value))
    hub = SimpleNamespace(bot_dir=tmp_path, _load=load, _save=save)
    save(tmp_path / 'config.json', config)
    manager = Mock()
    manager.check_now.side_effect = lambda app: {'update_available': app['id'] != 'current', 'dirty': app['id'] == 'dirty'}
    manager.start_all_updates.return_value = ({'ok': True, 'queued': ['seed']}, 202)
    state = Mock()
    state.get_install_dir.side_effect = lambda ident: '/apps/' + ident if ident != 'missing' else None
    apps = [{'id': i, 'name': i.title()} for i in ['seed', 'current', 'dirty', 'missing', 'fjordhub']]
    def request(action='check', sender='@owner:test', room='!private:test', **extra):
        return handle_updates(hub, manager, state, apps, dict(action=action, sender=sender, room=room, **extra))
    return request, manager, hub


def test_only_confirmed_exact_apps_enter_existing_update_queue(tmp_path):
    call, manager, hub = setup(tmp_path)
    result, code = call()
    assert code == 200 and result['confirmation']
    assert {row['id'] for row in result['apps']} == {'seed', 'current', 'dirty'}
    manager.start_all_updates.assert_not_called()
    token = result['confirmation']
    assert call('confirm', confirmation=token)[1] == 202
    assert [a['id'] for a in manager.start_all_updates.call_args.args[0]] == ['seed']
    assert call('confirm', confirmation=token)[1] == 409
    assert manager.start_all_updates.call_count == 1


def test_scope_expiry_cancel_and_permission_revocation(tmp_path):
    call, manager, hub = setup(tmp_path)
    assert call(sender='@stranger:test')[1] == 403
    reader, _ = call(sender='@reader:test')
    assert not reader['confirmation'] and not reader['can_update']
    result, _ = call()
    token = result['confirmation']
    assert call('confirm', room='!other:test', confirmation=token)[1] == 409
    assert call('confirm', sender='@reader:test', confirmation=token)[1] == 403
    with patch('services.bot_updates.time.time', return_value=10**12):
        assert call('confirm', confirmation=token)[1] == 409
    token = call()[0]['confirmation']
    assert call('cancel', confirmation=token)[0]['cancelled']
    assert call('confirm', confirmation=token)[1] == 409
    token = call()[0]['confirmation']
    config = hub._load(tmp_path / 'config.json')
    config['update_users'] = []
    hub._save(tmp_path / 'config.json', config)
    assert call('confirm', confirmation=token)[1] == 403
    manager.start_all_updates.assert_not_called()


def test_new_check_invalidates_old_confirmation(tmp_path):
    call, manager, _ = setup(tmp_path)
    old = call()[0]['confirmation']
    new = call()[0]['confirmation']
    assert old != new
    assert call('confirm', confirmation=old)[1] == 409
    assert call('confirm', confirmation=new)[1] == 202


def test_bot_requires_private_room_and_confirmation():
    bot = object.__new__(matrix_bot.FjordBot)
    bot.client = SimpleNamespace(user_id='@bot:test')
    bot.send = AsyncMock()
    room = SimpleNamespace(room_id='!private:test', users={'@owner:test': {}, '@bot:test': {}})
    result = {'ok': True, 'apps': [{'id': 'seed', 'name': 'FjordSeed', 'update_available': True}], 'confirmation': 'token'}
    with patch.object(matrix_bot, 'update_request', return_value=result) as request:
        asyncio.run(bot.handle_updates(room, '@owner:test', 'er der opdateringer?'))
        request.assert_called_once_with('check', '@owner:test', room.room_id)
    assert 'Svar ja eller nej' in bot.send.call_args.args[1]
    with patch.object(matrix_bot, 'update_request', return_value={'ok': True, 'queued': ['seed']}) as request:
        asyncio.run(bot.handle_updates(room, '@owner:test', 'ja'))
        request.assert_called_once_with('confirm', '@owner:test', room.room_id, 'token')
    assert 'FjordSeed' in bot.send.call_args.args[1]
    room.users['@other:test'] = {}
    with patch.object(matrix_bot, 'update_request') as request:
        asyncio.run(bot.handle_updates(room, '@owner:test', 'opdateringer'))
        request.assert_not_called()


def test_internal_api_rejects_browser_and_unauthorized_calls(tmp_path):
    import app as fjordhub
    from services.auth import AuthService
    from services.matrix_hub import MatrixHub
    from services.install_state import InstallState
    auth = AuthService(tmp_path / 'users.db')
    owner = auth.create_user('updater-admin', 'longpassword', role='admin')
    token = auth.create_access_token('Matrix bot', owner, days=0)
    hub = MatrixHub(tmp_path)
    hub.bot_dir.mkdir(parents=True, exist_ok=True)
    hub._save_state(monitor_token=token)
    hub._save(hub.bot_dir / 'config.json', {'allowed_users': ['@owner:test'], 'update_users': []})
    with patch.object(fjordhub, '_auth', auth), patch.object(fjordhub, '_matrix_hub', hub), patch.object(fjordhub, '_install_state', InstallState(tmp_path)), patch.object(fjordhub, '_get_apps', return_value=[]):
        client = fjordhub.app.test_client()
        url = '/api/matrix/bot/updates'
        data = {'action': 'check', 'sender': '@owner:test', 'room': '!private:test'}
        assert client.post(url, json=data).status_code == 401
        headers = {'Authorization': 'Bearer ' + token}
        assert client.post(url, json=data, headers=headers).status_code == 200
        assert client.post(url, json=dict(data, action='confirm', confirmation='fake'), headers=headers).status_code == 403
        assert client.post(url, json=data, headers=headers, environ_base={'REMOTE_ADDR': '8.8.8.8'}).status_code == 403
        assert client.post(url, json=dict(data, sender='@other:test'), headers=headers).status_code == 403
