"""Bounded, authenticated read of the managed FjordSeed installation."""
import json
import requests

from services.app_integration import AppDataError

FIELDS = ('name', 'state', 'progress', 'upspeed', 'credited_ratio', 'ratio',
          'ratio_limit', 'ratio_only', 'seeding_time', 'seeding_time_limit',
          'seeding_unlimited', 'seeding_goal_reached', 'waiting_for_downloaders')


def fetch_seed_status(base_url, key):
    try:
        with requests.Session() as client:
            client.trust_env = False
            with client.get(base_url + '/api/hub/bot/seeding', headers={'X-Hub-Key': key},
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
