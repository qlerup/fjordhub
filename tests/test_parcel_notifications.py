import pytest
from services.notification_events import clean_event, notification_text, NotificationStore, NotificationError
from services.matrix_hub import MatrixHub


def event(kind='tracking_event'):
    return dict(type=kind,event_id='parcel-event-1',tracking_number='ABC12345',label='Sko',carrier='DHL',
                description='Pakken er klar til afhentning',occurred_at='2026-11-06T12:00:00Z',location='Aarhus')


def test_parcel_format_and_validation():
    text=notification_text('fjordparcel',clean_event('fjordparcel',event()))
    assert all(value in text for value in ('Ny hændelse','Sko','ABC12345','DHL','klar til afhentning','13:00','Aarhus'))
    for field,value in [('tracking_number','bad/link'),('type','command'),('description','')]:
        with pytest.raises(NotificationError):clean_event('fjordparcel',{**event(),field:value})
    with pytest.raises(NotificationError):clean_event('fjordseed',event())


def test_parcel_queue_waits_for_bot_and_deduplicates(tmp_path):
    matrix=MatrixHub(tmp_path)
    store=NotificationStore(tmp_path)
    assert not store.record('fjordparcel',event(),matrix)['queued']
    matrix._save_state(phase='ready')
    matrix._save(matrix.bot_dir/'config.json',{'allowed_users':[]})
    assert not store.record('fjordparcel',event(),matrix)['queued']
    matrix._save(matrix.bot_dir/'config.json',{'allowed_users':['@owner:example.test']})
    assert store.record('fjordparcel',event(),matrix)['queued']
    assert NotificationStore(tmp_path).record('fjordparcel',event(),matrix)['duplicate']
    assert len(list((matrix.bot_dir/'outbox').glob('*.json')))==1


def test_parcel_endpoint_requires_its_own_app_key(tmp_path,monkeypatch):
    import app as hub
    from services.auth import AuthService
    auth=AuthService(tmp_path/'auth.db')
    auth.save_hub_key('fjordparcel','parcel-secret')
    auth.save_hub_key('fjordseed','seed-secret')
    monkeypatch.setattr(hub,'_auth',auth)
    monkeypatch.setattr(hub,'_app_notifications',NotificationStore(tmp_path))
    monkeypatch.setattr(hub,'_matrix_hub',MatrixHub(tmp_path))
    client=hub.app.test_client()
    payload=dict(event(),app_id='fjordparcel')
    assert client.post('/api/hub/apps/notifications',json=payload,headers={'X-Hub-Key':'seed-secret'}).status_code==403
    result=client.post('/api/hub/apps/notifications',json=payload,headers={'X-Hub-Key':'parcel-secret'})
    assert result.status_code==200 and not result.json['queued']


@pytest.mark.parametrize('kind', ['tracking_event', 'tracking_snapshot'])
def test_map_is_validated_and_preserved_in_durable_queue(tmp_path, kind):
    import base64
    import struct
    import json
    raw = b'\x89PNG\r\n\x1a\n' + struct.pack('>I', 13) + b'IHDR' + struct.pack('>II', 960, 460) + b'\x08\x02\x00\x00\x00' + b'\x00'*4
    image = base64.b64encode(raw).decode()
    payload = dict(event(kind), map_png=image, app_id='fjordparcel')
    assert clean_event('fjordparcel',payload)['map_png'] == image
    for bad in ('invalid base64!', 'a'*700001, base64.b64encode(b'not a png').decode()):
        with pytest.raises(NotificationError):
            clean_event('fjordparcel',dict(event(),map_png=bad))
    matrix = MatrixHub(tmp_path)
    matrix._save_state(phase='ready')
    matrix._save(matrix.bot_dir/'config.json',{'allowed_users':['@owner:example.test']})
    assert NotificationStore(tmp_path).record('fjordparcel',payload,matrix)['queued']
    queued = list((matrix.bot_dir/'outbox').glob('*.json'))
    assert json.loads(queued[0].read_text())['map_png'] == image


def test_bot_uploads_encrypted_map_and_reports_delivery_failure():
    import asyncio
    import base64
    from types import SimpleNamespace
    from unittest.mock import AsyncMock
    from services.matrix_bot import FjordBot
    from nio import RoomSendError
    bot = FjordBot.__new__(FjordBot)
    bot.client = SimpleNamespace(upload=AsyncMock(return_value=(SimpleNamespace(content_uri='mxc://test/map'),{'key': {'k':'secret'}})),
                                 room_send=AsyncMock(return_value=SimpleNamespace(event_id='$sent')))
    import struct
    raw = b'\x89PNG\r\n\x1a\n' + struct.pack('>I',13) + b'IHDR' + struct.pack('>II',456,760) + b'\x00'*9
    encoded = base64.b64encode(raw).decode()
    asyncio.run(bot.send_parcel_map('!room:test',encoded,'stable-transaction'))
    assert bot.client.upload.call_args.kwargs['encrypt'] is True
    content = bot.client.room_send.call_args.args[2]
    assert content['info']['w'] == 456 and content['info']['h'] == 760
    assert content['msgtype'] == 'm.image' and content['file']['url'] == 'mxc://test/map'
    assert 'url' not in content
    assert bot.client.room_send.call_args.kwargs['tx_id'] == 'stable-transaction'
    bot.client.room_send.return_value = RoomSendError('offline','M_UNKNOWN')
    with pytest.raises(RuntimeError):
        asyncio.run(bot.send_parcel_map('!room:test',encoded,'stable-transaction'))


def test_snapshot_heading_validation_and_retry_deduplication(tmp_path):
    payload = event('tracking_snapshot')
    text = notification_text('fjordparcel', clean_event('fjordparcel', payload))
    assert 'Opdateret status' in text and 'Sko' in text and 'Aarhus' in text
    assert 'Ny hændelse' not in text
    with pytest.raises(NotificationError):
        clean_event('fjordparcel', dict(payload, description=''))
    matrix = MatrixHub(tmp_path)
    matrix._save_state(phase='ready')
    matrix._save(matrix.bot_dir/'config.json', {'allowed_users':['@owner:example.test']})
    store = NotificationStore(tmp_path)
    assert store.record('fjordparcel', payload, matrix)['queued']
    assert store.record('fjordparcel', payload, matrix)['duplicate']
    assert len(list((matrix.bot_dir/'outbox').glob('*.json'))) == 1


@pytest.mark.parametrize('width,height,accepted', [(456,760,True),(960,533,True),(640,640,True),(960,460,True),(0,760,False),(2000,760,False),(1280,1280,False)])
def test_route_image_dimensions_follow_route_orientation(width,height,accepted):
    import base64,struct
    raw=b'\x89PNG\r\n\x1a\n'+struct.pack('>I',13)+b'IHDR'+struct.pack('>II',width,height)+b'\x00'*9
    payload=dict(event(),map_png=base64.b64encode(raw).decode())
    if accepted:
        assert clean_event('fjordparcel',payload)['map_png']==payload['map_png']
    else:
        with pytest.raises(NotificationError):clean_event('fjordparcel',payload)
