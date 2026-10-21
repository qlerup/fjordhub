"""Health alerts need confirmed observations and a delivered outage first."""
import asyncio
from unittest.mock import AsyncMock

import pytest

from services import matrix_bot


@pytest.fixture
def bot(monkeypatch, tmp_path):
    bot = matrix_bot.FjordBot.__new__(matrix_bot.FjordBot)
    bot.old_status = {}
    bot.pending_status = {}
    bot.alerted_users = {}
    bot.send = AsyncMock()
    bot.rooms_for = lambda user: ['!room']
    monkeypatch.setattr(matrix_bot, 'ALERTS', tmp_path/'status-alerts.json', raising=False)
    monkeypatch.setattr(matrix_bot, 'read', lambda path: {'allowed_users': ['@user']})
    return bot


def poll(monkeypatch, bot, running=1, total=1, **kwargs):
    snapshot = {'ok': True, 'apps': [{'name': 'FjordBudget',
                'running_count': running, 'container_count': total}], **kwargs}
    monkeypatch.setattr(matrix_bot, 'resources', lambda: snapshot)
    asyncio.run(bot.watch_status())


def test_startup_and_single_bad_sample_are_silent(monkeypatch, bot):
    poll(monkeypatch, bot)
    poll(monkeypatch, bot, 0)
    poll(monkeypatch, bot)
    poll(monkeypatch, bot)
    bot.send.assert_not_awaited()


def test_confirmed_outage_and_recovery_each_send_once(monkeypatch, bot):
    poll(monkeypatch, bot)
    poll(monkeypatch, bot, 0)
    bot.send.assert_not_awaited()
    poll(monkeypatch, bot, 0)
    assert bot.send.await_count == 1
    assert 'stoppede containere' in bot.send.call_args.args[1]
    poll(monkeypatch, bot, 0)
    poll(monkeypatch, bot)
    assert bot.send.await_count == 1
    poll(monkeypatch, bot)
    assert bot.send.await_count == 2
    assert 'kører igen' in bot.send.call_args.args[1]
    poll(monkeypatch, bot)
    assert bot.send.await_count == 2


def test_initial_down_requires_confirmation(monkeypatch, bot):
    poll(monkeypatch, bot, 0)
    poll(monkeypatch, bot)
    poll(monkeypatch, bot)
    bot.send.assert_not_awaited()


def test_recovery_without_delivered_outage_is_silent(monkeypatch, bot):
    bot.rooms_for = lambda user: []
    poll(monkeypatch, bot, 0)
    poll(monkeypatch, bot, 0)
    bot.rooms_for = lambda user: ['!room']
    poll(monkeypatch, bot)
    poll(monkeypatch, bot)
    bot.send.assert_not_awaited()


@pytest.mark.parametrize('unknown', [{'apps': []}, {'ok': False},
                                   {'apps': [{'name': 'FjordBudget', 'container_count': 0}]}])
def test_unknown_data_breaks_confirmation(monkeypatch, bot, unknown):
    poll(monkeypatch, bot)
    poll(monkeypatch, bot, 0)
    poll(monkeypatch, bot, **unknown)
    poll(monkeypatch, bot, 0)
    bot.send.assert_not_awaited()
    poll(monkeypatch, bot, 0)
    assert bot.send.await_count == 1


def test_new_recipient_does_not_get_recovery_for_someone_elses_alert(monkeypatch, bot):
    poll(monkeypatch, bot, 0)
    poll(monkeypatch, bot, 0)
    monkeypatch.setattr(matrix_bot, 'read', lambda path: {'allowed_users': ['@other']})
    poll(monkeypatch, bot)
    poll(monkeypatch, bot)
    assert bot.send.await_count == 1


def test_delivered_outage_is_followed_by_recovery_after_bot_restart(monkeypatch, bot, tmp_path):
    from unittest.mock import Mock
    monkeypatch.setattr(matrix_bot,'ROOT',tmp_path)
    monkeypatch.setattr(matrix_bot,'AsyncClient',Mock())
    monkeypatch.setattr(matrix_bot,'ClientConfig',Mock())
    def read(path):
        if path==matrix_bot.CONFIG:return {'user_id':'@bot','allowed_users':['@user']}
        try:
            import json
            return json.loads(path.read_text(encoding='utf-8'))
        except (OSError,ValueError):return {}
    monkeypatch.setattr(matrix_bot,'read',read)
    poll(monkeypatch,bot,0);poll(monkeypatch,bot,0)
    assert bot.send.await_count==1
    restarted=matrix_bot.FjordBot()
    restarted.send=AsyncMock();restarted.rooms_for=lambda user:['!room']
    poll(monkeypatch,restarted);restarted.send.assert_not_awaited()
    poll(monkeypatch,restarted)
    assert restarted.send.await_count==1
    restarted_again=matrix_bot.FjordBot()
    restarted_again.send=AsyncMock();restarted_again.rooms_for=lambda user:['!room']
    poll(monkeypatch,restarted_again);poll(monkeypatch,restarted_again)
    restarted_again.send.assert_not_awaited()
    assert 'kører igen' in restarted.send.call_args.args[1]
    assert 'Alle containere er startet (1/1)' in restarted.send.call_args.args[1]
    poll(monkeypatch,restarted)
    assert restarted.send.await_count==1


def test_recovery_waits_for_private_room_to_be_available(monkeypatch,bot):
    poll(monkeypatch,bot,0);poll(monkeypatch,bot,0)
    bot.rooms_for=lambda user:[]
    poll(monkeypatch,bot);poll(monkeypatch,bot)
    assert bot.send.await_count==1
    bot.rooms_for=lambda user:['!room']
    poll(monkeypatch,bot);poll(monkeypatch,bot)
    assert bot.send.await_count==2


def test_partial_restart_does_not_report_recovery(monkeypatch,bot):
    poll(monkeypatch,bot,0,2);poll(monkeypatch,bot,0,2)
    poll(monkeypatch,bot,1,2);poll(monkeypatch,bot,1,2)
    assert bot.send.await_count==1
    poll(monkeypatch,bot,2,2);poll(monkeypatch,bot,2,2)
    assert bot.send.await_count==2
    assert '(2/2)' in bot.send.call_args.args[1]


def test_failed_recovery_delivery_is_retried_without_losing_alert(monkeypatch,bot):
    poll(monkeypatch,bot,0);poll(monkeypatch,bot,0)
    bot.send.side_effect=ConnectionError('offline')
    poll(monkeypatch,bot);poll(monkeypatch,bot)
    assert bot.alerted_users=={'FjordBudget':{'@user'}}
    bot.send.side_effect=None
    poll(monkeypatch,bot);poll(monkeypatch,bot)
    assert not bot.alerted_users
    assert 'kører igen' in bot.send.call_args.args[1]


def test_matrix_error_response_is_not_treated_as_delivered(bot):
    from types import SimpleNamespace
    from nio import RoomSendError
    bot.client=SimpleNamespace(room_send=AsyncMock(return_value=RoomSendError('Unavailable')))
    with pytest.raises(RuntimeError,match='Matrix'):
        asyncio.run(matrix_bot.FjordBot.send(bot,'!room','Recovery'))


def test_live_queries_choose_the_correct_activity(monkeypatch, bot):
    from types import SimpleNamespace
    from unittest.mock import Mock
    bot.client=SimpleNamespace(user_id='@bot')
    snapshot=Mock(return_value={'ok':True,'torrents':[]})
    monkeypatch.setattr(matrix_bot,'seeding_snapshot',snapshot)
    room=SimpleNamespace(encrypted=True,room_id='!room')
    for question,intent in [('hvad downloader nu','downloading'),('hvad seeder nu','seeding')]:
        asyncio.run(bot.on_message(room,SimpleNamespace(decrypted=True,sender='@user',body=question)))
        assert snapshot.call_args.args == (intent,)
    assert 'Ingen aktive downloads' in bot.send.call_args_list[0].args[1]
    assert 'Ingen aktive seedinger' in bot.send.call_args_list[1].args[1]


def test_history_question_is_not_mistaken_for_live_status(monkeypatch, bot):
    from types import SimpleNamespace
    from unittest.mock import Mock
    bot.client=SimpleNamespace(user_id='@bot')
    history=Mock(return_value=['Downloadet siden i går: Test.iso'])
    live=Mock(side_effect=AssertionError('history must not query live status'))
    monkeypatch.setattr(matrix_bot,'download_history',history)
    monkeypatch.setattr(matrix_bot,'seeding_snapshot',live)
    asyncio.run(bot.on_message(SimpleNamespace(encrypted=True,room_id='!room'),
                              SimpleNamespace(decrypted=True,sender='@user',body='Har du downloadet noget nyt siden i går?')))
    history.assert_called_once_with('since_yesterday')
    live.assert_not_called()
    assert 'Test.iso' in bot.send.call_args.args[1]
