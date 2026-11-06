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
