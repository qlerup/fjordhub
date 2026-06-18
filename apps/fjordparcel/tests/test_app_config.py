import json

import app_config
import pytest
import storage


def configure_tmp_config(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    monkeypatch.setattr(app_config, "LEGACY_CONFIG_PATH", str(tmp_path / "app_config.json"))
    monkeypatch.setattr(app_config, "ENCRYPTION_KEY_FILE", str(tmp_path / "encryption.key"))
    monkeypatch.setenv("APP_ENCRYPTION_KEY", app_config.generate_encryption_key())
    for name in (
        "MS_CLIENT_ID",
        "MS_CLIENT_SECRET",
        "MS_TENANT",
        "MS_IMAP_HOST",
        "MS_IMAP_PORT",
        "MS_IMAP_MAX_SCAN_MESSAGES",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_GMAIL_MAX_SCAN_MESSAGES",
        "PUBLIC_BASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)


def test_saves_and_loads_microsoft_settings_encrypted(tmp_path, monkeypatch):
    configure_tmp_config(tmp_path, monkeypatch)

    saved, changed = app_config.save_microsoft_settings(
        {
            "client_id": "client-123",
            "client_secret": "secret-456",
            "tenant": "consumers",
            "imap_host": "outlook.office365.com",
            "imap_port": "993",
            "max_scan_messages": "1000",
        }
    )

    snapshot = app_config.secure_settings_snapshot()
    stored_client_id = next(row["value_encrypted"] for row in snapshot if row["key"] == "client_id")
    stored_client_secret = next(row["value_encrypted"] for row in snapshot if row["key"] == "client_secret")

    assert changed is True
    assert saved["client_id"] == "client-123"
    assert app_config.load_microsoft_settings()["client_secret"] == "secret-456"
    assert "client-123" not in stored_client_id
    assert "secret-456" not in stored_client_secret


def test_saves_and_loads_google_settings_encrypted(tmp_path, monkeypatch):
    configure_tmp_config(tmp_path, monkeypatch)

    saved, changed = app_config.save_google_settings(
        {
            "client_id": "google-client-123.apps.googleusercontent.com",
            "client_secret": "google-secret-456",
            "max_scan_messages": "750",
        }
    )

    snapshot = app_config.secure_settings_snapshot()
    stored_client_id = next(row["value_encrypted"] for row in snapshot if row["key"] == "google_client_id")
    stored_client_secret = next(row["value_encrypted"] for row in snapshot if row["key"] == "google_client_secret")

    assert changed is True
    assert saved["client_id"] == "google-client-123.apps.googleusercontent.com"
    assert app_config.load_google_settings()["client_secret"] == "google-secret-456"
    assert app_config.load_google_settings()["max_scan_messages"] == "750"
    assert "google-client-123" not in stored_client_id
    assert "google-secret-456" not in stored_client_secret


def test_blank_secret_keeps_existing_secret(tmp_path, monkeypatch):
    configure_tmp_config(tmp_path, monkeypatch)
    app_config.save_microsoft_settings(
        {
            "client_id": "old-client",
            "client_secret": "keep-this-secret",
            "tenant": "consumers",
            "imap_host": "outlook.office365.com",
            "imap_port": "993",
            "max_scan_messages": "1000",
        }
    )

    saved, changed = app_config.save_microsoft_settings(
        {
            "client_id": "new-client",
            "client_secret": "",
            "tenant": "consumers",
            "imap_host": "outlook.office365.com",
            "imap_port": "993",
            "max_scan_messages": "1000",
        }
    )

    assert changed is True
    assert saved["client_secret"] == "keep-this-secret"
    assert app_config.load_microsoft_settings()["client_secret"] == "keep-this-secret"


def test_saved_settings_override_env_defaults(tmp_path, monkeypatch):
    configure_tmp_config(tmp_path, monkeypatch)
    monkeypatch.setenv("MS_TENANT", "consumers")
    app_config.save_microsoft_settings(
        {
            "client_id": "saved-client",
            "client_secret": "saved-secret",
            "tenant": "common",
            "imap_host": "imap.example.test",
            "imap_port": "1993",
            "max_scan_messages": "500",
        }
    )

    settings = app_config.load_microsoft_settings()

    assert settings["tenant"] == "common"
    assert settings["imap_host"] == "imap.example.test"


def test_saves_and_loads_public_base_url(tmp_path, monkeypatch):
    configure_tmp_config(tmp_path, monkeypatch)

    saved = app_config.save_public_base_url("https://fjordparcel.example.dk/")

    assert saved == "https://fjordparcel.example.dk"
    assert app_config.load_public_base_url() == "https://fjordparcel.example.dk"


def test_saved_public_base_url_overrides_env(tmp_path, monkeypatch):
    configure_tmp_config(tmp_path, monkeypatch)
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://env.example.dk")

    assert app_config.load_public_base_url() == "https://env.example.dk"

    app_config.save_public_base_url("db.example.dk")

    assert app_config.load_public_base_url() == "https://db.example.dk"


def test_public_base_url_rejects_callback_path(tmp_path, monkeypatch):
    configure_tmp_config(tmp_path, monkeypatch)

    with pytest.raises(ValueError):
        app_config.save_public_base_url("https://fjordparcel.example.dk/auth/microsoft/callback")


def test_migrates_legacy_json_to_encrypted_sqlite(tmp_path, monkeypatch):
    configure_tmp_config(tmp_path, monkeypatch)
    legacy_path = tmp_path / "app_config.json"
    legacy_path.write_text(
        json.dumps(
            {
                "microsoft": {
                    "client_id": "legacy-client",
                    "client_secret": "legacy-secret",
                    "tenant": "consumers",
                    "imap_host": "outlook.office365.com",
                    "imap_port": "993",
                    "max_scan_messages": "1000",
                }
            }
        ),
        encoding="utf-8",
    )

    settings = app_config.load_microsoft_settings()
    snapshot = app_config.secure_settings_snapshot()
    stored_client_secret = next(row["value_encrypted"] for row in snapshot if row["key"] == "client_secret")

    assert settings["client_id"] == "legacy-client"
    assert settings["client_secret"] == "legacy-secret"
    assert "legacy-secret" not in stored_client_secret
    assert not legacy_path.exists()
    assert (tmp_path / "app_config.json.migrated").exists()


def test_partial_automation_save_preserves_other_section(tmp_path, monkeypatch):
    configure_tmp_config(tmp_path, monkeypatch)

    app_config.save_automation_settings(
        {
            "auto_scan_present": "1",
            "auto_scan_enabled": "on",
            "auto_scan_minutes": "45",
            "auto_refresh_present": "1",
            "auto_refresh_enabled": "on",
        }
    )

    saved = app_config.save_automation_settings(
        {
            "auto_refresh_present": "1",
        }
    )

    assert saved["auto_scan_enabled"] is True
    assert saved["auto_scan_minutes"] == 45
    assert saved["auto_refresh_enabled"] is False
