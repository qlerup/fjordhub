from services.bot_queries import torrent_query, torrent_messages, torrent_message_html


def test_flexible_queries_and_typing_errors():
    for text in ['Hvor mange seeder jeg på lige nu?', 'hvad seeder jeg?', 'SEEDING',
                 'hvor mnage seder nu', 'vis mine seedinger', 'hvad seedr jeg']:
        assert torrent_query(text) == 'seeding', text
    for text in ['vis mine torrents']:
        assert torrent_query(text) == 'transfers', text
    for text in ['hvor langt er mine downloads?', 'mine downlaods', 'hvad downloader nu?']:
        assert torrent_query(text) == 'downloading', text
    for text in ['hej', 'hvad sker der?', 'stop seeding', 'slet mine torrents']:
        assert torrent_query(text) is None, text


def test_summary_separates_active_seeds_and_reports_goal_alternatives():
    row = dict(name='Test ISO', state='stalledUP', progress=1, credited_ratio=.5,
               ratio=2, ratio_limit=1, seeding_time=49*3600, seeding_time_limit=49*60,
               seeding_unlimited=False, seeding_goal_reached=True)
    payload = dict(torrents=[row, dict(name='Paused', state='stoppedUP'),
                             dict(name='Next ISO', state='downloading', progress=.25)], more=False)
    text = '\n'.join(torrent_messages(payload))
    assert '1 seeder' in text
    assert 'venter på downloadere' in text
    assert '100 % af seedingmålet' in text
    assert 'Ratio: 0,5 / 1' in text and '49 t 00 min / 49 t 00 min' in text
    assert 'Paused' not in text and 'Next ISO' not in text
    text = '\n'.join(torrent_messages(payload, 'transfers'))
    assert 'Paused' in text and 'Next ISO' in text and '25 %' in text
    row['ratio_only'] = True
    text = '\n'.join(torrent_messages(payload))
    assert '50 % af seedingmålet' in text and 'ELLER' not in text


def test_all_titles_are_delivered_across_bounded_messages():
    rows = [dict(name=f'Title {i} ' + 'x'*180, state='uploading', progress=1,
                 seeding_unlimited=True) for i in range(120)]
    messages = torrent_messages(dict(torrents=rows))
    assert len(messages) > 1
    assert all(len(message) <= 6500 for message in messages)
    for i in range(120):
        assert f'Title {i} ' in '\n'.join(messages)
    assert 'Ubegrænset seeding' in messages[0]
    assert len(messages) == 24
    import re
    assert all(len(re.findall(r'^\d+\. ', message, re.MULTILINE)) == 5 for message in messages)
    assert '1/24' in messages[0] and '24/24' in messages[-1]
    assert '\n\n\n2. Title 1 ' in messages[0]
    assert '</p><br><p><strong>2. Title 1 ' in torrent_message_html(messages[0])


def test_empty_and_truncated_counts_are_explicit():
    assert 'Ingen aktive seedinger' in torrent_messages(dict(torrents=[]))[0]
    assert 'Mindst 0' in torrent_messages(dict(torrents=[], more=True))[0]


def test_rich_message_has_clear_titles_and_escapes_file_names():
    text = torrent_messages(dict(torrents=[dict(name='<img src=x> & test', state='uploading',
        progress=1, seeding_unlimited=True, seeding_time=4500, ratio=.25, upspeed=2*1024**2)]))[0]
    rendered = torrent_message_html(text)
    assert '<strong>1. &lt;img src=x&gt; &amp; test</strong>' in rendered
    assert '<h3>FjordSeed · Seeding</h3>' in rendered
    assert '<img ' not in rendered
    assert '1 t 15 min' in text and '2 MiB/s' in text
    assert 'Download: 100' not in text
    assert not any(ord(char) >= 0x1F000 for char in text)


def test_downloads_only_show_running_download_states():
    from services.bot_queries import ACTIVE_DOWNLOADS
    rows = [dict(name=state, state=state, progress=.5) for state in ACTIVE_DOWNLOADS]
    rows += [dict(name='Not ' + state, state=state, progress=.2)
             for state in ['queuedDL','pausedDL','stoppedDL','checkingDL','error','missingFiles']]
    rows += [dict(name='Done seed', state='uploading', progress=1),
             dict(name='Complete but stale state', state='downloading', progress=1)]
    text = '\n'.join(torrent_messages({'torrents': rows}, 'downloading'))
    assert all(state in text for state in ACTIVE_DOWNLOADS)
    assert 'Not ' not in text and 'Done seed' not in text and 'Complete but stale state' not in text
    assert 'seedingmål' not in text and 'Ratio:' not in text
    assert 'Ingen aktive downloads' in torrent_messages({'torrents': []}, 'downloading')[0]


def test_download_period_questions_and_completion_only_replies():
    from services.bot_queries import download_period, download_history_messages
    for question in ['Har du downloadet noget nyt siden i går?', 'hvad har du hentet siden igår']:
        assert download_period(question) == 'since_yesterday'
    assert download_period('hvad downloadede du i går') == 'yesterday'
    assert download_period('er der hentet noget i dag') == 'today'
    assert download_period('hvad er downloadet de sidste 7 dage') == 'last_7_days'
    assert download_period('stop downloads siden i går') is None
    assert download_period('hvad downloader nu') is None
    assert download_period('hvad er downloadet de sidste 999 dage') is None
    payload = {'label':'siden i går', 'completed':[{'filename':'Done'}], 'started':[{'filename':'Still running'}]}
    text = '\n'.join(download_history_messages(payload))
    assert 'Done' in text and 'Still running' not in text and 'siden i går' in text
    payload['completed'] = [{'filename':str(i)} for i in range(24)]
    assert len(download_history_messages(payload)) == 3
