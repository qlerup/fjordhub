"""Restart must preserve the bot's actual Matrix identity and credentials."""
import asyncio
from unittest.mock import AsyncMock, create_autospec

from nio import AsyncClient
from services.matrix_bot import FjordBot


def test_restart_restores_correct_device_and_access_token_without_new_login():
    bot = FjordBot.__new__(FjordBot)
    bot.saved = {'user_id':'@bot:example.org', 'device_id':'EXISTINGDEVICE',
                 'access_token':'existing-secret-token'}
    bot.client = create_autospec(AsyncClient, instance=True)
    bot.client.login = AsyncMock()
    asyncio.run(bot.login())
    # Bind against the library's real signature, including positional argument order.
    import inspect
    args, kwargs = bot.client.restore_login.call_args
    restored = inspect.signature(AsyncClient.restore_login).bind(bot.client, *args, **kwargs).arguments
    assert restored['user_id'] == bot.saved['user_id']
    assert restored['device_id'] == bot.saved['device_id']
    assert restored['access_token'] == bot.saved['access_token']
    bot.client.login.assert_not_awaited()
