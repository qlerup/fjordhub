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
