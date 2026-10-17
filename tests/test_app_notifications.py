"""App-origin Matrix notifications: authentication, formatting and idempotence."""
from pathlib import Path
import tempfile
from unittest.mock import patch

import app as fjordhub
from services.auth import AuthService
from services.install_state import InstallState
from services.matrix_hub import MatrixHub
from services.notification_events import NotificationError, NotificationStore, clean_event


def test_validation_rejects_arbitrary_commands_and_overlong_filenames():
    for event in (
        {"type": "shell", "event_id": "x", "text": "rm -rf /"},
        {"type": "vpn_failed", "event_id": "x", "profiles": []},
        {"type": "rss_started", "event_id": "../../bad", "filename": "download"},
    ):
        try:
            clean_event("fjordvpn" if event["type"].startswith("vpn") else "fjordseed", event)
        except NotificationError:
            pass
        else:
            raise AssertionError("Untrusted application event accepted")
    record = clean_event("fjordseed", {
        "type": "rss_started", "event_id": "abcd", "filename": "a" * 300
    })
    assert len(record["filename"]) == 200


def test_events_enqueue_once_for_allowlisted_matrix_user_and_query_downloads():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        matrix = MatrixHub(root)
        matrix._save_state(phase="ready", domain="matrix.example.dk")
        matrix._save(matrix.bot_dir / "config.json", {
            "allowed_users": ["@owner:matrix.example.dk"]
        })
        store = NotificationStore(root)
        payload = {"type": "rss_started", "event_id": "a1",
                   "filename": "new Linux.iso", "feed": "Linux RSS"}
        assert store.record("fjordseed", payload, matrix)["ok"]
        assert store.record("fjordseed", payload, matrix)["duplicate"]
        outbox = list((matrix.bot_dir / "outbox").glob("*.json"))
        assert len(outbox) == 1
        assert "new Linux iso" in outbox[0].read_text()
        store.record("fjordseed", {"type": "rss_completed", "event_id": "a2",
                                    "filename": "new Linux.iso", "feed": "Linux RSS"}, matrix)
        store.record("fjordseed", {"type": "download_completed", "event_id": "a3",
                                    "filename": "manual.mp4"}, matrix)
        assert len(list((matrix.bot_dir / "outbox").glob("*.json"))) == 1
        report = store.downloads_today()
        assert {row["filename"] for row in report["completed"]} == {"new Linux.iso", "manual.mp4"}
        assert not report["started"]


def test_hub_notifications_use_existing_per_app_key_and_bot_token():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        auth = AuthService(root / "users.db")
        admin_id = auth.create_user("notify-admin", "longpassword", role="admin")
        auth.save_hub_key("fjordseed", "seed-app-secret")
        matrix = MatrixHub(root)
        matrix._save_state(phase="ready", domain="matrix.example.dk")
        matrix._save(matrix.bot_dir / "config.json", {"allowed_users": ["@owner:matrix.example.dk"]})
        store = NotificationStore(root)
        token = auth.create_access_token("Matrix-bot (kun læseadgang)", admin_id, days=0)
        matrix._save_state(monitor_token=token)
        with patch.object(fjordhub, "_auth", auth), patch.object(
            fjordhub, "_app_notifications", store
        ), patch.object(fjordhub, "_matrix_hub", matrix), patch.object(
            fjordhub, "_install_state", InstallState(root)
        ):
            client = fjordhub.app.test_client()
            data = {"app_id": "fjordseed", "type": "rss_completed", "event_id": "ok-123",
                    "filename": "Linux.iso"}
            url = "/api/hub/apps/notifications"
            assert client.post(url, json=data).status_code == 403
            assert client.post(url, json=data, headers={"X-Hub-Key": "bad"}).status_code == 403
            assert client.post(url, json=data, headers={"X-Hub-Key": "seed-app-secret"}).status_code == 200
            endpoint = "/api/matrix/bot/downloads/today"
            assert client.get(endpoint).status_code == 401
            assert client.get(endpoint, headers={
                "Authorization": "Bearer " + token
            }).json["completed"][0]["filename"] == "Linux.iso"
            assert client.get(endpoint, headers={
                "Authorization": "Bearer " + token
            }, environ_overrides={"REMOTE_ADDR": "8.8.8.8"}).status_code == 403
            endpoint = '/api/matrix/bot/downloads?period=since_yesterday'
            assert client.get(endpoint).status_code == 401
            history = client.get(endpoint, headers={'Authorization': 'Bearer '+token})
            assert history.status_code == 200
            assert history.json['period'] == 'since_yesterday'
            assert history.headers['Cache-Control'] == 'no-store'
            assert client.get('/api/matrix/bot/downloads?period=invalid', headers={'Authorization':'Bearer '+token}).status_code == 400
            assert client.get(endpoint, headers={'Authorization':'Bearer '+token}, environ_overrides={'REMOTE_ADDR':'8.8.8.8'}).status_code == 403
            endpoint = '/api/matrix/bot/seeding'
            assert client.get(endpoint).status_code == 401
            assert client.get(endpoint, headers={'Authorization': 'Bearer seed-app-secret'}).status_code == 401
            with patch.object(fjordhub, '_integration_app_connection', return_value=('http://seed', 'key')), patch(
                'services.seed_status.fetch_seed_status', return_value={'ok': True, 'torrents': []}
            ) as fetch:
                assert client.get(endpoint, headers={'Authorization': 'Bearer '+token}).json == {
                    'ok': True, 'torrents': []}
                fetch.assert_called_once_with('http://seed', 'key')
                assert client.get(endpoint, headers={'Authorization': 'Bearer '+token},
                                  environ_overrides={'REMOTE_ADDR':'8.8.8.8'}).status_code == 403


def test_seed_notification_uses_readable_title():
    from services.notification_events import notification_text
    text = notification_text('fjordseed', {'type': 'rss_started',
        'filename': 'Example.Show.S02E03.DANISH.1080p.WEB-DL.H264.mkv', 'feed': 'My feed'})
    assert 'Example Show\n   Sæson 2 · Episode 3' in text
    assert 'WEB-DL' not in text
    assert '\n\nRSS-feed: My feed' in text
