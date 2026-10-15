"""Small, local intent recognizer and plain-text torrent summaries. No AI service."""
from difflib import get_close_matches
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
    transfer = {'torrent', 'torrents', 'download', 'downloads', 'downloader', 'hentninger'}
    for vocabulary, intent in ((seed, 'seeding'), (transfer, 'transfers')):
        if any(token in vocabulary or (len(token) >= 5 and
               get_close_matches(token, sorted(vocabulary), n=1, cutoff=0.8)) for token in tokens):
            return intent
    return None


def number(value, fallback=0):
    return value if type(value) in (int, float) and math.isfinite(value) else fallback


def decimal(value):
    return f'{value:.2f}'.rstrip('0').rstrip('.').replace('.', ',')


ACTIVE_SEEDS = {'uploading', 'stalledUP', 'forcedUP'}
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
    selected = seeds if intent == 'seeding' else rows
    heading = ('FjordSeed: Du seeder ' + str(len(seeds)) + ' torrents lige nu.' if not payload.get('more')
               else 'FjordSeed: Du seeder mindst ' + str(len(seeds)) + ' torrents (udsnit).')
    if intent != 'seeding':
        heading += '\n' + str(len(rows)) + ' torrents i alt i oversigten.'
    if not selected:
        heading += '\nIngen aktive seedinger.' if intent == 'seeding' else '\nIngen torrents.'
    blocks = [heading]
    for index, row in enumerate(selected, 1):
        title = ' '.join(str(row.get('name') or 'Ukendt titel').split())[:200]
        state = STATE_NAMES.get(row.get('state'), 'Ukendt status')
        progress = min(1, max(0, number(row.get('progress')))) * 100
        ratio = max(0, number(row.get('credited_ratio'), number(row.get('ratio'))))
        hours = max(0, number(row.get('seeding_time'))) / 3600
        text = f'{index}. {title}\n{state} · Download: {decimal(progress)} %'
        text += f'\nRatio: {decimal(ratio)} · Seedet: {decimal(hours)} timer'
        speed = max(0, number(row.get('upspeed'))) / 1024
        text += f' · Upload: {decimal(speed)} KiB/s'
        if row.get('seeding_unlimited') is True:
            text += '\nFortsætter indtil manuelt stop (intet automatisk mål).'
        elif row.get('seeding_unlimited') is False:
            target = max(1, number(row.get('ratio_limit'), 1))
            minutes = 0 if row.get('ratio_only') else max(0, number(row.get('seeding_time_limit')))
            fraction = min(1, max(ratio / target, hours / (minutes / 60) if minutes else 0))
            text += f'\nSeedingmål: {decimal(fraction * 100)} % · Ratio {decimal(ratio)}/{decimal(target)}'
            if minutes:
                text += f' eller {decimal(hours)}/{decimal(minutes / 60)} timer'
            if row.get('waiting_for_downloaders'):
                text += '\nMålet er nået; seeder videre, mens downloadere mangler data.'
            elif row.get('seeding_goal_reached'):
                text += '\nSeedingmålet er nået.'
        else:
            text += '\nSeedingmål er ikke tilgængeligt.'
        blocks.append(text)
    if payload.get('more'):
        blocks.append('Oversigten er begrænset til 500 torrents. Se hele listen i FjordSeed.')
    # Deliver every displayed title across messages, rather than silently cutting at 8k.
    messages, current = [], ''
    for block in blocks:
        if current and len(current) + len(block) + 2 > 6500:
            messages.append(current)
            current = ''
        current += ('\n\n' if current else '') + block
    if current:
        messages.append(current)
    return messages
