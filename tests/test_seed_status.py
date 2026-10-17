from unittest.mock import Mock, patch

import pytest

from services.app_integration import AppDataError
from services.seed_status import fetch_seed_status


def response(status=200, chunks=None):
    item = Mock(status_code=status)
    item.iter_content.return_value = chunks or [b'{"ok":true,"torrents":[{"name":"ISO","state":"uploading","tracker":"private"}]}']
    item.__enter__ = Mock(return_value=item)
    item.__exit__ = Mock(return_value=False)
    return item


def client_for(item):
    client = Mock()
    client.__enter__ = Mock(return_value=client)
    client.__exit__ = Mock(return_value=False)
    client.get.return_value = item
    return client


def test_reads_only_trusted_target_without_redirects_and_filters_private_fields():
    client = client_for(response())
    with patch('services.seed_status.requests.Session', return_value=client):
        assert fetch_seed_status('http://seed:8088', 'secret') == {
            'ok':True, 'more':False, 'torrents':[{'name':'ISO', 'state':'uploading'}]}
    assert client.trust_env is False
    client.get.assert_called_once_with('http://seed:8088/api/hub/bot/seeding',
        headers={'X-Hub-Key':'secret'}, timeout=(2,12), allow_redirects=False, stream=True)


@pytest.mark.parametrize('item', [response(302), response(503),
    response(chunks=[b'{"ok":true,"torrents":[null]}']), response(chunks=[b'x'*(512*1024+1)])])
def test_rejects_unavailable_invalid_or_unbounded_data(item):
    with patch('services.seed_status.requests.Session', return_value=client_for(item)):
        with pytest.raises(AppDataError):
            fetch_seed_status('http://seed', 'secret')


@pytest.mark.parametrize('activity', ['downloading','seeding'])
def test_requests_filtered_activity_before_server_limit(activity):
    client=client_for(response())
    with patch('services.seed_status.requests.Session',return_value=client):
        fetch_seed_status('http://seed','secret',activity=activity)
    assert client.get.call_args.args[0] == 'http://seed/api/hub/bot/seeding?activity='+activity
