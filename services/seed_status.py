"""Bounded, authenticated read of the managed FjordSeed installation."""
import json
import math
import requests

from services.app_integration import AppDataError


def fetch_seed_upload(base_url, key):
    try:
        with requests.Session() as client:
            client.trust_env = False
            with client.get(base_url + '/api/hub/bot/upload', headers={'X-Hub-Key': key},
                            timeout=(2, 12), allow_redirects=False, stream=True) as response:
                if response.status_code != 200:
                    raise ValueError('Unavailable upload data')
                body = bytearray()
                for chunk in response.iter_content(8192):
                    body.extend(chunk)
                    if len(body) > 65536:
                        raise ValueError('Response too large')
        data = json.loads(body)
        if not isinstance(data, dict) or data.get('ok') is not True or not isinstance(data.get('options'), list) or len(data['options']) > 30:
            raise ValueError('Invalid upload data')
        options, seen = [], set()
        for row in data['options']:
            if (not isinstance(row, dict) or row.get('kind') not in ('rss', 'tracker') or
                    not isinstance(row.get('id'), str) or not 1 <= len(row['id']) <= 100 or
                    not isinstance(row.get('name'), str) or not row['name'].strip()):
                raise ValueError('Invalid upload choice')
            identity = row['kind'], row['id']
            if identity in seen:
                raise ValueError('Duplicate upload choice')
            seen.add(identity)
            item = {k: row.get(k) for k in ('kind', 'id', 'name', 'credited_uploaded', 'estimated', 'updated_at')}
            item['name'] = ' '.join(row['name'].split())[:90]
            for key in ('credited_uploaded', 'updated_at'):
                value = item[key]
                if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value < 0):
                    raise ValueError('Invalid upload amount')
            item['estimated'] = row.get('estimated') is True
            options.append(item)
        return {'ok': True, 'options': options}
    except (requests.RequestException, ValueError):
        raise AppDataError('Kunne ikke hente uploadtal. Kontrollér at FjordSeed er startet og opdateret.') from None

FIELDS = ('name', 'state', 'progress', 'upspeed', 'credited_ratio', 'ratio',
          'ratio_limit', 'ratio_only', 'seeding_time', 'seeding_time_limit',
          'seeding_unlimited', 'seeding_goal_reached', 'waiting_for_downloaders')


def fetch_seed_status(base_url, key, activity='all'):
    try:
        with requests.Session() as client:
            client.trust_env = False
            suffix = '' if activity == 'all' else '?activity=' + activity
            with client.get(base_url + '/api/hub/bot/seeding' + suffix, headers={'X-Hub-Key': key},
                            timeout=(2, 12), allow_redirects=False, stream=True) as response:
                if response.status_code != 200:
                    raise AppDataError('FjordSeed er ikke klar. Kontrollér at appen er startet og opdateret.')
                body = bytearray()
                for chunk in response.iter_content(65536):
                    body.extend(chunk)
                    if len(body) > 512 * 1024:
                        raise ValueError('Response too large')
        data = json.loads(body)
        if (not isinstance(data, dict) or data.get('ok') is not True or
                not isinstance(data.get('torrents'), list) or len(data['torrents']) > 500 or
                any(not isinstance(row, dict) for row in data['torrents'])):
            raise ValueError('Invalid snapshot')
        return {'ok': True, 'more': bool(data.get('more')),
                'torrents': [{k: row[k] for k in FIELDS if k in row} for row in data['torrents']]}
    except (requests.RequestException, ValueError):
        raise AppDataError('Kunne ikke hente en gyldig torrentstatus fra FjordSeed.') from None


def fetch_seed_storage(base_url, key):
    try:
        with requests.Session() as client:
            client.trust_env = False
            with client.get(base_url + '/api/hub/bot/storage', headers={'X-Hub-Key': key},
                            timeout=(2, 40), allow_redirects=False, stream=True) as response:
                if response.status_code != 200:
                    raise ValueError('Storage unavailable')
                body = bytearray()
                for chunk in response.iter_content(4096):
                    body.extend(chunk)
                    if len(body) > 8192:
                        raise ValueError('Response too large')
        data = json.loads(body)
        if not isinstance(data, dict) or data.get('ok') is not True:
            raise ValueError('Invalid storage data')
        result = {'ok': True}
        for field in ('temporary_bytes', 'rss_temporary_bytes'):
            value = data[field]
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError('Invalid storage amount')
            result[field] = value
        return result
    except (requests.RequestException, ValueError, KeyError):
        raise AppDataError('Kunne ikke måle pladsforbrug. Kontrollér at FjordSeed er startet og opdateret.') from None
