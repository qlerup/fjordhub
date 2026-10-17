"""Health alerts need confirmed observations and a delivered outage first."""
import asyncio
from unittest.mock import AsyncMock

import pytest

from services import matrix_bot


@pytest.fixture
def bot(monkeypatch):
    bot = matrix_bot.FjordBot.__new__(matrix_bot.FjordBot)
    bot.old_status = {}
    bot.pending_status = {}
    bot.alerted_users = {}
    bot.send = AsyncMock()
    bot.rooms_for = lambda user: ['!room']
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
