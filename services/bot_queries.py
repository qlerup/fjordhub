"""Small, local intent recognizer and plain-text torrent summaries. No AI service."""
from difflib import get_close_matches
from html import escape
import math
import re
import unicodedata


def words(message):
    text = unicodedata.normalize('NFKD', message.lower()).encode('ascii', 'ignore').decode()
    return re.findall(r'[a-z0-9]+', text)


def torrent_query(message):
    tokens = words(message)
    # A status question must never pretend to execute a requested change.
    if set(tokens) & {'stop', 'stoppe', 'slet', 'slette', 'fjern', 'fjernelse', 'pause', 'start'}:
        return None
    seed = {'seed', 'seeder', 'seeding', 'seede', 'seedning'}
    download = {'download', 'downloads', 'downloader', 'downloading', 'henter', 'hentninger'}
    transfer = {'torrent', 'torrents'}
    for vocabulary, intent in ((seed, 'seeding'), (download, 'downloading'), (transfer, 'transfers')):
        if any(token in vocabulary or (len(token) >= 5 and
               get_close_matches(token, sorted(vocabulary), n=1, cutoff=0.8)) for token in tokens):
            return intent
    return None


def download_period(message):
    tokens = words(message)
    if set(tokens) & {'stop', 'stoppe', 'slet', 'slette', 'fjern', 'pause', 'start'}:
        return None
    text = ' '.join(tokens)
    if not any(term in text for term in ('download', 'hentet', 'hent', 'frdig', 'nyt', 'rss')):
        return None
    if re.search(r'\bsiden (?:i gar|igar|yesterday)\b', text) or 'since yesterday' in text:
        return 'since_yesterday'
    match = re.search(r'\b(?:sidste|seneste|last) (\d{1,3}) (?:dage|days)\b', text)
    if match and 1 <= int(match[1]) <= 366:
        return 'last_' + str(int(match[1])) + '_days'
    if re.search(r'\b(?:i gar|igar|yesterday)\b', text):
        return 'yesterday'
    if re.search(r'\b(?:i dag|idag|today)\b', text):
        return 'today'
    return None


def download_title(filename):
    name = ' '.join(str(filename or 'Ukendt fil').split())[:200]
    name = re.sub(r'\.(?:mkv|mp4|avi|mov|m4v|ts)$', '', name, flags=re.I)
    # Only remove a suffix when it starts with a recognizable release tag.
    name = re.split(r'[. _-]+(?:DANISH|NORDIC|MULTI|1080[pi]|2160p|720p|480p|WEB-DL|WEBRip|BluRay|HDTV)\b', name, maxsplit=1, flags=re.I)[0]
    episode = re.search(r'(?:[. _-]+)(S(\d{1,2})(?:E(\d{1,3}))?)$', name, re.I)
    detail = ''
    if episode:
        detail = 'Sæson ' + str(int(episode[2]))
        if episode[3]:
            detail += ' · Episode ' + str(int(episode[3]))
        name = name[:episode.start()]
    title = re.sub(r'[._]+', ' ', name).strip(' -') or 'Ukendt fil'
    return title + ('\n   ' + detail if detail else '')


def download_history_messages(payload):
    label = payload.get('label')
    if not isinstance(label, str) or not label.strip():
        label = 'i dag'
    done = payload.get('completed', [])
    if not done:
        return [f'FjordSeed: Ingen færdige downloads registreret {label}.']
    heading = f'FjordSeed · Færdigdownloadet {label}'
    pages = []
    for offset in range(0, len(done), 10):
        lines = [f'{offset + index}. ' + download_title(item.get('filename'))
                 for index, item in enumerate(done[offset:offset + 10], 1)]
        page = f' · Side {offset // 10 + 1}/{math.ceil(len(done) / 10)}' if len(done) > 10 else ''
        pages.append(heading + page + f'\n{len(done)} færdige downloads\n\n' + '\n\n'.join(lines))
    if payload.get('more'):
        pages[-1] += '\n\nDer er flere registreringer end vist her.'
    return pages


def number(value, fallback=0):
    return value if type(value) in (int, float) and math.isfinite(value) else fallback


def decimal(value):
    return f'{value:.2f}'.rstrip('0').rstrip('.').replace('.', ',')


def duration(hours):
    minutes = int(max(0, hours) * 60)
    return f'{minutes // 60} t {minutes % 60:02} min'


def progress_bar(fraction):
    filled = min(10, max(0, int(fraction * 10)))
    return '▰' * filled + '▱' * (10 - filled)


def torrent_message_html(body):
    blocks = re.split(r'\n{2,}', body)
    heading, _, summary = blocks[0].partition('\n')
    output = ['<h3>' + escape(heading) + '</h3><p>' + escape(summary) + '</p>']
    for block in blocks[1:]:
        lines = block.split('\n')
        rendered = []
        for i, line in enumerate(lines):
            if i == 0 and re.match(r'^\d+\. ', line):
                rendered.append('<strong>' + escape(line) + '</strong>')
            elif '▰' in line or '▱' in line:
                rendered.append('<code>' + escape(line) + '</code>')
            else:
                rendered.append(escape(line))
        output.append('<p>' + '<br>'.join(rendered) + '</p>')
    return '<br>'.join(output)


ACTIVE_SEEDS = {'uploading', 'stalledUP', 'forcedUP'}
ACTIVE_DOWNLOADS = {'downloading', 'forcedDL', 'stalledDL', 'metaDL', 'forcedMetaDL'}
STATE_NAMES = {
    'uploading': 'Seeder – uploader', 'stalledUP': 'Seeder – venter på downloadere',
    'forcedUP': 'Seeder – tvunget start', 'queuedUP': 'I kø til seeding',
    'pausedUP': 'Seeding på pause', 'stoppedUP': 'Seeding stoppet',
    'checkingUP': 'Kontrollerer filer før seeding',
    'downloading': 'Downloader', 'stalledDL': 'Download venter på peers',
    'forcedDL': 'Downloader', 'queuedDL': 'Download i kø',
    'pausedDL': 'Download på pause', 'stoppedDL': 'Download stoppet',
    'metaDL': 'Henter torrentoplysninger', 'forcedMetaDL': 'Henter torrentoplysninger',
    'checkingDL': 'Kontrollerer download', 'checkingResumeData': 'Kontrollerer fremdrift',
    'moving': 'Flytter filer', 'error': 'Fejl', 'missingFiles': 'Filer mangler',
}


def torrent_messages(payload, intent='seeding'):
    rows = payload['torrents']
    seeds = [row for row in rows if row.get('state') in ACTIVE_SEEDS]
    downloads = [row for row in rows if row.get('state') in ACTIVE_DOWNLOADS and number(row.get('progress')) < 1]
    selected = seeds if intent == 'seeding' else downloads if intent == 'downloading' else rows
    count = ('Mindst ' if payload.get('more') else '') + str(len(seeds)) + ' seeder'
    uploading = sum(number(row.get('upspeed')) > 0 for row in seeds)
    count += f' · {uploading} uploader lige nu'
    if intent == 'downloading':
        count = ('Mindst ' if payload.get('more') else '') + str(len(downloads)) + ' downloader lige nu'
    elif intent != 'seeding':
        count = str(len(rows)) + ' torrents i oversigten · ' + count
    blocks = []
    for index, row in enumerate(selected, 1):
        title = ' '.join(str(row.get('name') or 'Ukendt titel').split())[:200]
        state = STATE_NAMES.get(row.get('state'), 'Ukendt status')
        progress = min(1, max(0, number(row.get('progress')))) * 100
        ratio = max(0, number(row.get('credited_ratio'), number(row.get('ratio'))))
        hours = max(0, number(row.get('seeding_time'))) / 3600
        text = f'{index}. {title}\n{state}'
        if progress < 100 or intent != 'seeding':
            text += f'\nDownload: {progress_bar(progress / 100)} {decimal(progress)} %'
        if intent == 'downloading':
            blocks.append(text)
            continue
        speed = max(0, number(row.get('upspeed'))) / 1024
        if speed > 0:
            text += '\nUpload: ' + (decimal(speed / 1024) + ' MiB/s' if speed >= 1024 else decimal(speed) + ' KiB/s')
        if row.get('seeding_unlimited') is True:
            text += f'\nRatio: {decimal(ratio)} · Seedtid: {duration(hours)}'
            text += '\nUbegrænset seeding · manuelt stop'
        elif row.get('seeding_unlimited') is False:
            target = max(1, number(row.get('ratio_limit'), 1))
            minutes = 0 if row.get('ratio_only') else max(0, number(row.get('seeding_time_limit')))
            fraction = min(1, max(ratio / target, hours / (minutes / 60) if minutes else 0))
            text += f'\nRatio: {decimal(ratio)} / {decimal(target)}'
            text += f'\nSeedtid: {duration(hours)}'
            if minutes:
                text += f' / {duration(minutes / 60)}'
            text += f'\n{progress_bar(fraction)} {decimal(fraction * 100)} % af seedingmålet'
            if minutes:
                text += '\nStopmål: ratio ELLER seedtid'
            if row.get('waiting_for_downloaders'):
                text += '\nMål nået · seeder videre til aktive downloadere er færdige'
            elif row.get('seeding_goal_reached'):
                text += '\nSeedingmålet er nået'
        else:
            text += f'\nRatio: {decimal(ratio)} · Seedtid: {duration(hours)}'
            text += '\nSeedingmål er ikke tilgængeligt'
        blocks.append(text)
    if payload.get('more'):
        blocks.append('Oversigten er begrænset til 500 torrents. Se hele listen i FjordSeed.')
    # Five titles per message keeps a long list readable on a phone.
    pages, current, items = [], '', 0
    for block in blocks:
        if current and (items == 5 or len(current) + len(block) + 2 > 5500):
            pages.append(current)
            current, items = '', 0
        current += ('\n\n\n' if current else '') + block
        items += 1
    pages.append(current or ('Ingen aktive seedinger.' if intent == 'seeding' else 'Ingen aktive downloads.' if intent == 'downloading' else 'Ingen torrents.'))
    heading = 'FjordSeed · Seeding' if intent == 'seeding' else 'FjordSeed · Downloads'
    return [heading + (f' · {i}/{len(pages)}' if len(pages) > 1 else '') + '\n' + count + '\n\n' + page
            for i, page in enumerate(pages, 1)]
