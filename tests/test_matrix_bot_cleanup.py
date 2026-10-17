import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from nio import RoomMessagesResponse, RoomMessagesError, RoomRedactResponse, RoomRedactError
from services import matrix_bot


@pytest.fixture
def setup_bot(monkeypatch):
    bot = matrix_bot.FjordBot.__new__(matrix_bot.FjordBot)
    bot.client = SimpleNamespace(user_id='@bot', room_messages=AsyncMock(),
                                 room_redact=AsyncMock(return_value=RoomRedactResponse('$redaction','!room')))
    bot.send = AsyncMock()
    bot.cleaning_rooms = set()
    monkeypatch.setattr(matrix_bot, 'read', lambda path: {'allowed_users':['@user']})
    room = SimpleNamespace(room_id='!room', encrypted=True, users={'@bot':{}, '@user':{}})
    return bot, room


def event(ident, sender='@bot', kind='m.room.encrypted', redacted=False):
    return SimpleNamespace(event_id=ident, sender=sender,
                           source={'type':kind,'unsigned':{'redacted_because':{}} if redacted else {}})


def command(bot, room, sender='@user', decrypted=True, body='ryd botbeskeder'):
    asyncio.run(bot.on_message(room,SimpleNamespace(sender=sender,decrypted=decrypted,body=body)))


def test_cleanup_only_redacts_own_messages_in_current_room_and_pages_history(setup_bot):
    bot,room=setup_bot
    old=event('$old'); old.source['unsigned']={'redacted_because':{'event_id':'$already'}}
    bot.client.room_messages.side_effect=[
        RoomMessagesResponse('!room',[event('$one'),event('$user','@user'),event('$state',kind='m.room.member'),old], 'start','page2'),
        RoomMessagesResponse('!room',[event('$two',kind='m.room.message')],'page2',None)]
    command(bot,room,body='/ryd botbeskeder')
    assert [call.args[:2] for call in bot.client.room_redact.call_args_list] == [('!room','$one'),('!room','$two')]
    assert bot.client.room_messages.call_args_list[1].kwargs['start']=='page2'
    assert bot.client.room_messages.call_args.kwargs['message_filter']['senders']==['@bot']
    assert '2 af mine beskeder' in bot.send.call_args.args[1]
    assert 'Dine beskeder er bevaret' in bot.send.call_args.args[1]
    assert not bot.cleaning_rooms


@pytest.mark.parametrize('sender,decrypted,encrypted', [('@other',True,True),('@user',False,True),('@user',True,False)])
def test_untrusted_commands_cannot_trigger_cleanup(setup_bot,sender,decrypted,encrypted):
    bot,room=setup_bot;room.encrypted=encrypted
    command(bot,room,sender=sender,decrypted=decrypted)
    bot.client.room_messages.assert_not_awaited()
    bot.client.room_redact.assert_not_awaited()
    bot.send.assert_not_awaited()


def test_group_room_is_not_cleared(setup_bot):
    bot,room=setup_bot;room.users['@someone']={}
    command(bot,room)
    bot.client.room_messages.assert_not_awaited()
    bot.client.room_redact.assert_not_awaited()
    assert 'private' in bot.send.call_args.args[1]


def test_redaction_error_reports_partial_result_and_releases_lock(setup_bot):
    bot,room=setup_bot
    bot.client.room_messages.return_value=RoomMessagesResponse('!room',[event('$one'),event('$two')],'start','page2')
    bot.client.room_redact.side_effect=[RoomRedactResponse('$redaction','!room'),RoomRedactError('forbidden','M_FORBIDDEN')]
    command(bot,room)
    assert '1 af mine beskeder' in bot.send.call_args.args[1]
    assert 'afbrudt' in bot.send.call_args.args[1]
    assert not bot.cleaning_rooms


def test_empty_filtered_page_does_not_hide_older_messages(setup_bot):
    bot,room=setup_bot
    bot.client.room_messages.side_effect=[RoomMessagesResponse('!room',[],'start','older'),
                                        RoomMessagesResponse('!room',[event('$one')],'older',None)]
    command(bot,room)
    assert bot.client.room_redact.await_count==1


def test_duplicate_events_are_not_redacted_twice(setup_bot):
    bot,room=setup_bot
    bot.client.room_messages.side_effect=[RoomMessagesResponse('!room',[event('$one')],'start','older'),
                                        RoomMessagesResponse('!room',[event('$one')],'older',None)]
    command(bot,room)
    assert bot.client.room_redact.await_count==1


def test_history_error_does_not_claim_success(setup_bot):
    bot,room=setup_bot
    bot.client.room_messages.return_value=RoomMessagesError('unavailable','M_UNKNOWN')
    command(bot,room)
    assert 'afbrudt' in bot.send.call_args.args[1]
    assert not bot.cleaning_rooms


def test_concurrent_room_cleanup_is_not_started_twice(setup_bot):
    bot,room=setup_bot
    bot.cleaning_rooms.add(room.room_id)
    command(bot,room)
    bot.client.room_messages.assert_not_awaited()
