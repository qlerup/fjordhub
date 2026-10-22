import asyncio
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from services.bot_queries import upload_question, upload_menu, upload_answer
from services.matrix_bot import FjordBot


OPTIONS=[dict(kind='rss',id='f1',name='Film',credited_uploaded=1024**3,estimated=False),
         dict(kind='tracker',id='t1',name='Tracker',credited_uploaded=5*1024**4,estimated=False)]


def test_upload_question_menu_and_reply():
    for text in ('kan du sende det krediteret upload','hvor meget krediteret upload har jeg?',
                 'mit krediterede upload','upload','credited upload'):
        assert upload_question(text),text
    assert not upload_question('slet krediteret upload')
    assert not upload_question('hvad downloader jeg?')
    menu=upload_menu(OPTIONS)
    assert '1. RSS-feed: Film' in menu and '2. Tracker: Tracker' in menu
    assert '1 GiB' in upload_answer(OPTIONS[0])
    assert '5 TiB' in upload_answer(OPTIONS[1])
    assert 'hele kontoen' in upload_answer(OPTIONS[1])
    assert 'estimeret' in upload_answer(dict(OPTIONS[0],estimated=True))
    assert 'ikke tilgængeligt' in upload_answer(dict(OPTIONS[0],credited_uploaded=None))


def bot():
    b=FjordBot.__new__(FjordBot)
    b.send=AsyncMock()
    return b


def test_number_selection_fetches_fresh_value_and_survives_reordering():
    b=bot()
    with patch('services.matrix_bot.credit_snapshot',side_effect=[OPTIONS,
                [OPTIONS[1],dict(OPTIONS[0],credited_uploaded=2*1024**3)]]):
        assert asyncio.run(b.handle_upload('room','owner','krediteret upload'))
        assert asyncio.run(b.handle_upload('room','owner','1.'))
    b.send.assert_awaited_with('room',upload_answer(dict(OPTIONS[0],credited_uploaded=2*1024**3)))


def test_menus_are_private_expire_and_can_be_cancelled_or_retried():
    b=bot()
    with patch('services.matrix_bot.credit_snapshot',return_value=OPTIONS) as fetch:
        asyncio.run(b.handle_upload('room','owner','krediteret upload'))
        assert not asyncio.run(b.handle_upload('other-room','owner','1'))
        assert not asyncio.run(b.handle_upload('room','other-user','1'))
        asyncio.run(b.handle_upload('room','owner','99'))
        assert '1 til 2' in b.send.call_args.args[1]
        assert fetch.call_count==1
        asyncio.run(b.handle_upload('room','owner','2'))
        assert 'Tracker: Tracker' in b.send.call_args.args[1]
        b.upload_menus['owner','room']['expires']=time.time()-1
        asyncio.run(b.handle_upload('room','owner','1'))
        assert 'udløbet' in b.send.call_args.args[1]
        asyncio.run(b.handle_upload('room','owner','krediteret upload'))
        asyncio.run(b.handle_upload('room','owner','annuller'))
        assert not b.upload_menus


def test_removed_choice_does_not_return_another_feed():
    b=bot()
    with patch('services.matrix_bot.credit_snapshot',side_effect=[OPTIONS,[OPTIONS[1]]]):
        asyncio.run(b.handle_upload('room','owner','krediteret upload'))
        asyncio.run(b.handle_upload('room','owner','1'))
    assert 'findes ikke længere' in b.send.call_args.args[1]


def test_encrypted_allowlisted_message_dispatch_supports_question_then_number():
    b=bot();b.client=SimpleNamespace(user_id='@bot:test')
    room=SimpleNamespace(room_id='room',encrypted=True)
    with patch('services.matrix_bot.allowed',return_value=True),patch('services.matrix_bot.credit_snapshot',return_value=OPTIONS):
        for text in ('kan du sende mit krediterede upload','1'):
            event=SimpleNamespace(sender='@owner:test',decrypted=True,body=text)
            asyncio.run(b.on_message(room,event))
    assert '1 GiB' in b.send.call_args.args[1]
