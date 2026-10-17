from datetime import datetime, timedelta, timezone

import pytest
from services.notification_events import NotificationStore, COPENHAGEN


def insert(store, ident, at, kind='download_completed'):
    with store._connect() as conn:
        conn.execute('INSERT INTO events(app_id,event_id,kind,occurred_at,filename) VALUES(?,?,?,?,?)',
                     ('fjordseed',ident,kind,at.astimezone(timezone.utc).isoformat(),ident))


def test_calendar_periods_respect_copenhagen_and_completion_boundaries(tmp_path):
    store = NotificationStore(tmp_path)
    now = datetime(2026,10,17,12,tzinfo=COPENHAGEN)
    start = datetime(2026,10,16,tzinfo=COPENHAGEN)
    insert(store,'too old',start-timedelta(seconds=1))
    insert(store,'yesterday',start)
    insert(store,'today',datetime(2026,10,17,tzinfo=COPENHAGEN))
    insert(store,'tomorrow',datetime(2026,10,18,tzinfo=COPENHAGEN))
    insert(store,'unfinished',now,'download_started')
    def titles(period):
        return [row['filename'] for row in store.downloads_period(period,now)['completed']]
    assert set(titles('since_yesterday')) == {'yesterday','today'}
    assert titles('yesterday') == ['yesterday']
    assert titles('today') == ['today']
    assert set(titles('last_2_days')) == {'yesterday','today'}
    with pytest.raises(ValueError):
        store.downloads_period('last_999_days',now)


def test_yesterday_on_end_of_summer_time_includes_both_repeated_hours(tmp_path):
    store=NotificationStore(tmp_path)
    for ident,hour in [('first hour',0),('second hour',1)]:
        insert(store,ident,datetime(2026,10,25,hour,30,tzinfo=timezone.utc))
    report=store.downloads_period('yesterday',datetime(2026,10,26,12,tzinfo=COPENHAGEN))
    assert {row['filename'] for row in report['completed']} == {'first hour','second hour'}


def test_period_label_stays_text_with_recorded_downloads(tmp_path):
    store = NotificationStore(tmp_path)
    now = datetime(2026,10,17,12,tzinfo=COPENHAGEN)
    insert(store, 'Finished', now)
    insert(store, 'Pending', now, 'download_started')
    assert store.downloads_period('last_7_days', now)['label'] == 'de sidste 7 dage'
