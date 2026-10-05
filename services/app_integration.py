"""Bounded reads from managed apps. External tokens never become app logins."""
import re
import requests

SUPPORTED_APPS = {'fjordflix': {'name': 'FjordFlix',
    'description': 'De 10 senest tilføjede film/serieafsnit med posters samt aktive streams og seernavne.'}}
MAX_JSON_BYTES = 512 * 1024
MAX_POSTER_BYTES = 8 * 1024 * 1024


class AppDataError(Exception):
    def __init__(self, message, status=503):
        super().__init__(message)
        self.status = status


def fetch(base_url, key, mid=None):
    suffix = ''
    if mid is not None:
        if not re.fullmatch(r'[a-f0-9]{32}', mid):
            raise AppDataError('Poster findes ikke.', 404)
        suffix = '/posters/' + mid
    limit = MAX_POSTER_BYTES if mid is not None else MAX_JSON_BYTES
    try:
        with requests.Session() as client:
            client.trust_env = False
            with client.get(base_url + '/api/hub/integration-data' + suffix,
                            headers={'X-Hub-Key': key}, timeout=(2, 5),
                            allow_redirects=False, stream=True) as response:
                if response.status_code == 404:
                    raise AppDataError('Opdater FjordFlix for datadeling, eller kontrollér at posteren findes.', 404)
                if response.status_code != 200:
                    raise AppDataError('FjordFlix kunne ikke levere data.')
                chunks, size = [], 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > limit:
                        raise AppDataError('FjordFlix returnerede for mange data.')
                    chunks.append(chunk)
                body = b''.join(chunks)
                if mid is not None:
                    if response.headers.get('Content-Type', '').split(';')[0] != 'image/jpeg':
                        raise AppDataError('FjordFlix returnerede et ugyldigt billede.')
                    return body
        import json
        payload = json.loads(body)
        if not isinstance(payload, dict) or payload.get('ok') is not True or not isinstance(payload.get('items'), list) or not isinstance(payload.get('streams'), list):
            raise ValueError()
        fields = ('id', 'title', 'overview', 'release_date', 'genres', 'rating', 'media_type', 'series_title', 'season', 'episode')
        stream_fields = ('id', 'movie_id', 'title', 'user', 'client', 'state', 'mode', 'position', 'duration', 'height', 'mbps', 'encoder', 'video', 'audio', 'subtitle')
        if any(not isinstance(item, dict) for item in payload['items'] + payload['streams']):
            raise ValueError()
        return {'ok': True, 'generated_at': payload.get('generated_at'),
                'library_count': payload.get('library_count', 0),
                'items': [{k: item[k] for k in fields if k in item} for item in payload['items'][:10]],
                'streams': [{k: item[k] for k in stream_fields if k in item} for item in payload['streams'][:100]]}
    except (requests.RequestException, ValueError):
        raise AppDataError('FjordFlix er ikke tilgængelig. Kontrollér at appen er startet og opdateret.') from None
