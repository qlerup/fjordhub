import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from services.bot_queries import ratio_question, ratio_answer
from services.matrix_bot import FjordBot, HELP_TEXT
from services.seed_status import fetch_seed_upload
from services.app_integration import AppDataError
from test_seed_status import response, client_for


OPTIONS=[dict(kind='rss',id='f',name='RSS',ratio=99),
         dict(kind='tracker',id='t',name='Tracker',ratio=2.75,credited_uploaded=11*1024**3,
              credited_downloaded=4*1024**3,updated_at=1793530800)]


@pytest.mark.parametrize('text',['ratio','/ratio','Hvad er min ratio lige nu?','Kan du vise min ratio?',
                                'Hvad er ratioen?','Vis mine ratioer','What is my ratio?',
                                'Hvad er min ratio fra seneste opdatering?'])
def test_recognizes_ratio_questions(text):
    assert ratio_question(text)


@pytest.mark.parametrize('text',['stop seeding ved ratio 2','slet ratio','ændr min ratio til 3',
                                'sæt ratio til 4','krediteret upload','rapport'])
def test_not_a_ratio_query(text):
    assert not ratio_question(text)


def test_reports_account_ratios_instead_of_feed_ratios_with_time():
    text=ratio_answer(OPTIONS)
    assert 'Ratio: 2,75' in text and 'Tracker' in text and 'RSS' not in text
    assert 'Senest opdateret: 01-11-2026 kl.' in text
    assert 'hele kontoen' in text and 'ratio' in HELP_TEXT
    assert 'Tilføj en tracker' in ratio_answer(OPTIONS[:1])


def test_multiple_trackers_missing_or_zero_stats_and_fallbacks():
    assert ratio_answer([dict(OPTIONS[1],ratio=0)]).count('Ratio: 0')==1
    assert 'Ratio: 2,75' in ratio_answer([dict(OPTIONS[1],ratio=None)])
    assert 'Ratio: ∞' in ratio_answer([dict(OPTIONS[1],ratio=None,credited_downloaded=0)])
    for fields in [dict(ratio=None,credited_uploaded=None),dict(ratio=None,credited_downloaded=None),
                   dict(ratio=None,credited_uploaded=0,credited_downloaded=0),
                   dict(ratio=True,credited_uploaded=None),dict(ratio=float('nan'),credited_uploaded=None)]:
        assert 'ikke tilgængelig' in ratio_answer([dict(OPTIONS[1],**fields)])
    assert ratio_answer([OPTIONS[1],dict(OPTIONS[1],id='t2',name='Second')]).count('Ratio: 2,75')==2


@pytest.mark.parametrize('text',['ratio','/ratio','Hvad er min ratio lige nu?','Hvad er min ratio fra seneste opdatering?'])
def test_live_dispatch_uses_snapshot_and_does_not_trigger_update_or_upload_menu(text):
    bot=FjordBot.__new__(FjordBot);bot.send=AsyncMock();bot.handle_updates=AsyncMock();bot.handle_upload=AsyncMock()
    bot.client=SimpleNamespace(user_id='@bot:test')
    room=SimpleNamespace(room_id='private-room',encrypted=True)
    event=SimpleNamespace(sender='@owner:test',decrypted=True,body=text)
    with patch('services.matrix_bot.allowed',return_value=True),patch('services.matrix_bot.credit_snapshot',return_value=OPTIONS) as fetch:
        asyncio.run(bot.on_message(room,event))
    fetch.assert_called_once();bot.send.assert_awaited_once_with('private-room',ratio_answer(OPTIONS))
    bot.handle_updates.assert_not_awaited();bot.handle_upload.assert_not_awaited()


@pytest.mark.parametrize('encrypted,decrypted,allowed',[(False,True,True),(True,False,True),(True,True,False)])
def test_ratio_access_requires_encryption_and_allowlist(encrypted,decrypted,allowed):
    bot=FjordBot.__new__(FjordBot);bot.send=AsyncMock();bot.client=SimpleNamespace(user_id='@bot:test')
    room=SimpleNamespace(room_id='room',encrypted=encrypted)
    event=SimpleNamespace(sender='@someone:test',decrypted=decrypted,body='ratio')
    with patch('services.matrix_bot.allowed',return_value=allowed),patch('services.matrix_bot.credit_snapshot') as fetch:
        asyncio.run(bot.on_message(room,event))
    fetch.assert_not_called();bot.send.assert_not_awaited()


def test_hub_forwards_validated_ratio_fields_and_filters_secrets():
    choice=dict(OPTIONS[1],api_key='private')
    client=client_for(response(chunks=[json.dumps({'ok':True,'options':[choice]}).encode()]))
    with patch('services.seed_status.requests.Session',return_value=client):
        result=fetch_seed_upload('http://seed','secret')
    assert result['options'][0]['ratio']==2.75
    assert result['options'][0]['credited_downloaded']==4*1024**3
    assert 'private' not in str(result)
    for field in ('ratio','credited_downloaded'):
        for bad in (-1,True,'2.75',float('nan')):
            item=response(chunks=[json.dumps({'ok':True,'options':[dict(choice,**{field:bad})]}).encode()])
            with patch('services.seed_status.requests.Session',return_value=client_for(item)):
                with pytest.raises(AppDataError):fetch_seed_upload('http://seed','secret')
