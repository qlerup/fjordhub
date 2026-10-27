import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from services.bot_queries import storage_question, storage_answer
from services.matrix_bot import FjordBot
from services.seed_status import fetch_seed_storage
from services.app_integration import AppDataError
from test_seed_status import response, client_for


@pytest.mark.parametrize('text', [
    'Hvor meget midlertidig plads er brugt fra RSS feed som auto slettes?',
    'Hvor meget fylder RSS?', 'midlertidigt pladsforbrug', 'rss plads',
    'Hvor meget plads bruger RSS downloads i dag?',
])
def test_recognition(text):
    assert storage_question(text)


@pytest.mark.parametrize('text', ['slet RSS filer', 'ryd midlertidig plads', 'hvad seeder nu?', 'status'])
def test_other_intents(text):
    assert not storage_question(text)


def test_amounts_and_unknown():
    assert 'RSS-filer: 1,5 GiB' in storage_answer({'rss_temporary_bytes': 3*1024**3//2})
    assert 'RSS-filer: 0 B' in storage_answer({'rss_temporary_bytes': 0})
    assert 'RSS-filer: Ukendt' in storage_answer({'rss_temporary_bytes': None})


@pytest.mark.parametrize('value', [-1, True, '12', 1.5])
def test_invalid_payload(value):
    data={'ok': True, 'temporary_bytes': 50, 'rss_temporary_bytes': value}
    with patch('services.seed_status.requests.Session', return_value=client_for(response(chunks=[json.dumps(data).encode()]))):
        with pytest.raises(AppDataError):
            fetch_seed_storage('http://seed', 'key')


def test_projection():
    data={'ok':True, 'temporary_bytes':50, 'rss_temporary_bytes':None, 'path':'private'}
    client=client_for(response(chunks=[json.dumps(data).encode()]))
    with patch('services.seed_status.requests.Session', return_value=client):
        assert fetch_seed_storage('http://seed','key') == {k:v for k,v in data.items() if k!='path'}
    assert client.trust_env is False
    assert client.get.call_args.kwargs['allow_redirects'] is False


def test_dispatch_before_download_intent():
    bot=FjordBot.__new__(FjordBot)
    bot.client=SimpleNamespace(user_id='@bot:test')
    bot.send=AsyncMock()
    room=SimpleNamespace(room_id='room', encrypted=True)
    event=SimpleNamespace(sender='@owner:test', decrypted=True, body='Hvor meget plads bruger RSS downloads i dag?')
    with patch('services.matrix_bot.allowed',return_value=True), patch('services.matrix_bot.storage_snapshot',return_value={'ok':True,'temporary_bytes':1024,'rss_temporary_bytes':1024}):
        asyncio.run(bot.on_message(room,event))
    assert 'RSS-filer: 1 KiB' in bot.send.call_args.args[1]
