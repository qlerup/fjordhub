from services.bot_queries import torrent_query, torrent_messages, torrent_message_html


def test_flexible_queries_and_typing_errors():
    for text in ['Hvor mange seeder jeg på lige nu?', 'hvad seeder jeg?', 'SEEDING',
                 'hvor mnage seder nu', 'vis mine seedinger', 'hvad seedr jeg']:
        assert torrent_query(text) == 'seeding', text
    for text in ['vis mine torrents', 'hvor langt er mine downloads?', 'mine downlaods']:
        assert torrent_query(text) == 'transfers', text
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
