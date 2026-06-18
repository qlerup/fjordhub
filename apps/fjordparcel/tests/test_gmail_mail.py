import base64
import urllib.parse

import app_config
import gmail_mail
import storage


def configure_tmp_gmail(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    monkeypatch.setattr(app_config, "ENCRYPTION_KEY_FILE", str(tmp_path / "encryption.key"))
    monkeypatch.setenv("APP_ENCRYPTION_KEY", app_config.generate_encryption_key())
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("GOOGLE_GMAIL_MAX_SCAN_MESSAGES", raising=False)
    storage.init_db()
    app_config.save_google_settings(
        {
            "client_id": "google-client.apps.googleusercontent.com",
            "client_secret": "google-secret",
            "max_scan_messages": "1000",
        }
    )


def b64url(text):
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii").rstrip("=")


def gmail_payload(message_id="m1"):
    return {
        "id": message_id,
        "internalDate": "1780488000000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Din pakke fra MyTrendyPhone er snart paa vej"},
                {"name": "From", "value": "Bring <noreply@bring.com>"},
                {"name": "Date", "value": "Wed, 03 Jun 2026 16:29:00 +0200"},
            ],
            "mimeType": "multipart/alternative",
            "parts": [
                {
                    "mimeType": "text/html",
                    "body": {
                        "data": b64url(
                            'Din pakke fra MyTrendyPhone er snart hos os. '
                            '<a href="https://bring.dk/t/370722152477343049">Spor pakken</a>'
                        )
                    },
                }
            ],
        },
    }


def test_google_auth_flow_uses_readonly_offline_scope(tmp_path, monkeypatch):
    configure_tmp_gmail(tmp_path, monkeypatch)

    flow = gmail_mail.build_auth_flow("http://localhost:8096/auth/google/callback")
    query = urllib.parse.parse_qs(urllib.parse.urlparse(flow["auth_uri"]).query)

    assert flow["state"]
    assert query["scope"] == ["https://www.googleapis.com/auth/gmail.readonly"]
    assert query["access_type"] == ["offline"]
    assert "select_account" in query["prompt"][0]


def test_gmail_credentials_are_saved_encrypted(tmp_path, monkeypatch):
    configure_tmp_gmail(tmp_path, monkeypatch)

    gmail_mail._save_account_credentials(
        "USER@GMAIL.COM",
        {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "expires_at": 9999999999,
        },
    )

    with storage.get_connection() as db:
        row = db.execute("SELECT * FROM gmail_accounts WHERE email = 'user@gmail.com'").fetchone()

    assert "access-token" not in row["credentials_encrypted"]
    assert "refresh-token" not in row["credentials_encrypted"]
    assert gmail_mail.get_accounts()[0]["username"] == "user@gmail.com"
    assert gmail_mail.get_accounts()[0]["provider"] == "gmail"


def test_parse_gmail_message_extracts_headers_body_and_date():
    parsed = gmail_mail._parse_gmail_message(gmail_payload())

    assert parsed["subject"] == "Din pakke fra MyTrendyPhone er snart paa vej"
    assert parsed["from"]["emailAddress"]["address"] == "noreply@bring.com"
    assert parsed["receivedDateTime"].startswith("2026-06-03T16:29:00")
    assert "MyTrendyPhone" in parsed["bodyPreview"]
    assert "370722152477343049" in parsed["bodyPreview"]


def test_iter_recent_messages_refreshes_token_and_reads_messages(tmp_path, monkeypatch):
    configure_tmp_gmail(tmp_path, monkeypatch)
    gmail_mail._save_account_credentials(
        "user@gmail.com",
        {
            "access_token": "expired-access-token",
            "refresh_token": "refresh-token",
            "expires_at": 1,
        },
    )

    token_requests = []
    api_calls = []

    def fake_token_request(form_values):
        token_requests.append(form_values)
        return {"access_token": "fresh-access-token", "expires_in": 3600}

    def fake_api_get(url, access_token, params=None):
        api_calls.append((url, access_token, params))
        if url.endswith("/users/me/messages"):
            return {"messages": [{"id": "m1"}]}
        if url.endswith("/users/me/messages/m1"):
            return gmail_payload("m1")
        raise AssertionError(url)

    monkeypatch.setattr(gmail_mail, "_token_request", fake_token_request)
    monkeypatch.setattr(gmail_mail, "_api_get", fake_api_get)

    messages = list(gmail_mail.iter_recent_messages(14))

    assert token_requests[0]["grant_type"] == "refresh_token"
    assert api_calls[0][1] == "fresh-access-token"
    assert api_calls[0][2]["q"] == "newer_than:14d"
    assert messages[0]["from"]["emailAddress"]["address"] == "noreply@bring.com"
    assert "370722152477343049" in messages[0]["bodyPreview"]
