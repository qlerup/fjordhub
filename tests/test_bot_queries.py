from services.bot_queries import torrent_query, torrent_messages


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
    assert 'Du seeder 1 torrents' in text
    assert 'venter på downloadere' in text
    assert 'Seedingmål: 100 %' in text
    assert 'Ratio 0,5/1' in text and '49/49 timer' in text
    assert 'Paused' not in text and 'Next ISO' not in text
    text = '\n'.join(torrent_messages(payload, 'transfers'))
    assert 'Paused' in text and 'Next ISO' in text and '25 %' in text
    row['ratio_only'] = True
    text = '\n'.join(torrent_messages(payload))
    assert 'Seedingmål: 50 %' in text and 'eller' not in text


def test_all_titles_are_delivered_across_bounded_messages():
    rows = [dict(name=f'Title {i} ' + 'x'*180, state='uploading', progress=1,
                 seeding_unlimited=True) for i in range(120)]
    messages = torrent_messages(dict(torrents=rows))
    assert len(messages) > 1
    assert all(len(message) <= 6500 for message in messages)
    for i in range(120):
        assert f'Title {i} ' in '\n'.join(messages)
    assert 'intet automatisk mål' in messages[0]


def test_empty_and_truncated_counts_are_explicit():
    assert 'Ingen aktive seedinger' in torrent_messages(dict(torrents=[]))[0]
    assert 'mindst 0' in torrent_messages(dict(torrents=[], more=True))[0]
