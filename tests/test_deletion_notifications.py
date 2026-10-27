import json
import pytest
from services.notification_events import clean_event, notification_text, NotificationError, NotificationStore
from services.matrix_hub import MatrixHub


def event(**changes):
    return dict(type='download_deleted',event_id='deleted-123',filename='Example.Show.S02E03.1080p.mkv',
                reason='time',ratio_limit=1,seed_hours=49,library_retained=False,**changes)


def test_title_reason_and_preserved_library():
    data=event()
    text=notification_text('fjordseed',clean_event('fjordseed',data))
    assert 'Example Show' in text and 'Sæson 2' in text and 'Episode 3' in text
    assert '49 timers seeding nået' in text
    data.update(reason='ratio',ratio_limit=1.5,library_retained=True)
    text=notification_text('fjordseed',clean_event('fjordseed',data))
    assert 'Ratio-mål nået: 1,5:1' in text and 'biblioteket er bevaret' in text


@pytest.mark.parametrize('field,value',[('reason','manual'),('seed_hours',-1),('seed_hours',float('nan')),
                                      ('ratio_limit',True),('library_retained','true')])
def test_reject_invalid(field,value):
    data=event();data[field]=value
    with pytest.raises(NotificationError): clean_event('fjordseed',data)
    with pytest.raises(NotificationError): clean_event('fjordvpn',event())


def test_retries_deduplicate_and_do_not_pollute_download_history(tmp_path):
    store=NotificationStore(tmp_path)
    matrix=MatrixHub(tmp_path)
    matrix._save_state(phase='ready')
    matrix._save(matrix.bot_dir/'config.json',{'allowed_users':['@owner:test']})
    assert store.record('fjordseed',event(),matrix)['ok']
    paths=list((matrix.bot_dir/'outbox').glob('*.json'))
    assert len(paths)==1
    assert '49 timers' in json.loads(paths[0].read_text())['text']
    paths[0].unlink()  # Bot delivered it.
    assert store.record('fjordseed',event(),matrix)['duplicate']
    assert not list((matrix.bot_dir/'outbox').glob('*.json'))
    assert not store.downloads_today()['completed']


@pytest.mark.parametrize('size,text',[(2350000000,'ca. 2,35 GB'),(850000000,'ca. 850 MB'),(0,'ca. 0 B'),(None,'ukendt')])
def test_freed_space_format_and_app_id_payload(size,text):
    data=event(freed_bytes=size,app_id='fjordseed')
    cleaned=clean_event('fjordseed',data)
    assert 'Frigjort plads: '+text in notification_text('fjordseed',cleaned)


@pytest.mark.parametrize('size',[-1,True,'1024',1.5,2**63])
def test_invalid_size(size):
    with pytest.raises(NotificationError):clean_event('fjordseed',event(freed_bytes=size))


def test_old_event_remains_supported():
    assert 'Frigjort plads: ukendt' in notification_text('fjordseed',clean_event('fjordseed',event()))


def test_transfer_values_and_achieved_ratio_are_distinct_from_target(tmp_path):
    data=event(app_id='fjordseed',freed_bytes=10**9,transfer={'uploaded':2350000000,'credited_uploaded':850000000,'ratio':2.35})
    cleaned=clean_event('fjordseed',data)
    text=notification_text('fjordseed',cleaned)
    assert 'Reel upload: 2,35 GB' in text
    assert 'Krediteret upload: 850 MB' in text
    assert 'Opnået ratio: 2,35:1' in text
    matrix=MatrixHub(tmp_path);matrix._save_state(phase='ready')
    matrix._save(matrix.bot_dir/'config.json',{'allowed_users':['@owner:test']})
    NotificationStore(tmp_path).record('fjordseed',data,matrix)
    assert json.loads(next((matrix.bot_dir/'outbox').glob('*.json')).read_text())['text']==text


@pytest.mark.parametrize('transfer',[None,[],{'uploaded':-1},{'ratio':True},{'credited_uploaded':'123'},
                                      {'ratio':float('nan')},{'uploaded':float('inf')},{'unknown':1}])
def test_invalid_transfer_rejected(transfer):
    with pytest.raises(NotificationError):clean_event('fjordseed',event(transfer=transfer))


def test_old_receipts_and_zero_transfer():
    text=notification_text('fjordseed',clean_event('fjordseed',event()))
    assert 'Reel upload: ukendt' in text and 'Opnået ratio: ukendt' in text
    text=notification_text('fjordseed',clean_event('fjordseed',event(transfer={'uploaded':0,'credited_uploaded':0,'ratio':0})))
    assert 'Reel upload: 0 B' in text and 'Krediteret upload: 0 B' in text and 'Opnået ratio: 0:1' in text
