from datetime import datetime, timezone
import json

import pytest

import app_config
import imap_mail
from imap_mail import _imap_since_date, _parse_message, _xoauth2_authenticator, normalize_scan_days


def test_xoauth2_auth_string_format():
    authenticator = _xoauth2_authenticator("user@hotmail.com", "abc123")

    assert authenticator(None) == b"user=user@hotmail.com\x01auth=Bearer abc123\x01\x01"


def test_parse_plain_text_message():
    raw = (
        b"From: Fjord Shop <shop@example.com>\r\n"
        b"Subject: Your package is on the way\r\n"
        b"Date: Wed, 03 Jun 2026 20:00:00 +0000\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"PostNord tracking number: 1234567890123\r\n"
    )

    message = _parse_message(raw)

    assert message["subject"] == "Your package is on the way"
    assert message["from"]["emailAddress"]["address"] == "shop@example.com"
    assert "1234567890123" in message["bodyPreview"]
    assert message["receivedDateTime"].startswith("2026-06-03T20:00:00")


def test_scan_days_options_are_week_based():
    assert normalize_scan_days("7") == 7
    assert normalize_scan_days("14") == 14
    assert normalize_scan_days("21") == 21

    with pytest.raises(ValueError):
        normalize_scan_days("50")


def test_imap_since_date_uses_english_month_names():
    now = datetime(2026, 6, 3, 12, 0, tzinfo=timezone.utc)

    assert _imap_since_date(7, now=now) == "27-May-2026"
    assert _imap_since_date(14, now=now) == "20-May-2026"
    assert _imap_since_date(21, now=now) == "13-May-2026"


def test_token_cache_write_is_encrypted(tmp_path, monkeypatch):
    cache_path = tmp_path / "msal_cache.json"
    monkeypatch.setattr(imap_mail, "TOKEN_CACHE_PATH", str(cache_path))
    monkeypatch.setattr(app_config, "ENCRYPTION_KEY_FILE", str(tmp_path / "encryption.key"))
    monkeypatch.setenv("APP_ENCRYPTION_KEY", app_config.generate_encryption_key())

    payload = '{"AccessToken":{"a":{"secret":"access-token"}},"RefreshToken":{"r":{"secret":"refresh-token"}}}'

    imap_mail._write_token_cache(payload)
    stored = cache_path.read_text(encoding="utf-8")
    decoded, migrated = imap_mail._decode_token_cache(stored)

    assert "access-token" not in stored
    assert "refresh-token" not in stored
    assert decoded == payload
    assert migrated is False


def test_plaintext_token_cache_is_migrated_to_encrypted(tmp_path, monkeypatch):
    cache_path = tmp_path / "msal_cache.json"
    monkeypatch.setattr(imap_mail, "TOKEN_CACHE_PATH", str(cache_path))
    monkeypatch.setattr(app_config, "ENCRYPTION_KEY_FILE", str(tmp_path / "encryption.key"))
    monkeypatch.setenv("APP_ENCRYPTION_KEY", app_config.generate_encryption_key())

    payload = '{"AccessToken":{"a":{"secret":"access-token"}},"RefreshToken":{"r":{"secret":"refresh-token"}}}'
    cache_path.write_text(payload, encoding="utf-8")

    cache = imap_mail._load_cache()
    stored = cache_path.read_text(encoding="utf-8")

    assert json.loads(cache.serialize()) == json.loads(payload)
    assert "access-token" not in stored
    assert "refresh-token" not in stored
