import base64
import json
import os
from hashlib import sha256
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken

from storage import get_connection, utc_now


LEGACY_CONFIG_PATH = os.getenv("APP_CONFIG_PATH", os.path.join("data", "app_config.json"))
ENCRYPTION_KEY_FILE = os.getenv("APP_ENCRYPTION_KEY_FILE", os.path.join("data", "encryption.key"))

DEFAULT_MICROSOFT_SETTINGS = {
    "client_id": "",
    "client_secret": "",
    "tenant": "consumers",
    "imap_host": "outlook.office365.com",
    "imap_port": "993",
    "max_scan_messages": "1000",
}

DEFAULT_GOOGLE_SETTINGS = {
    "google_client_id": "",
    "google_client_secret": "",
    "google_max_scan_messages": "1000",
}

PUBLIC_BASE_URL_KEY = "public_base_url"

SENSITIVE_KEYS = {
    "client_id",
    "client_secret",
    "google_client_id",
    "google_client_secret",
    "track17_api_key",
}


def _first_value(*values):
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def generate_encryption_key():
    return Fernet.generate_key().decode("ascii")


def _normalize_encryption_key(value):
    text = str(value or "").strip()
    if not text:
        return ""

    try:
        Fernet(text.encode("ascii"))
        return text
    except (ValueError, TypeError):
        digest = sha256(text.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest).decode("ascii")


def _load_or_create_file_key():
    if os.path.exists(ENCRYPTION_KEY_FILE):
        with open(ENCRYPTION_KEY_FILE, "r", encoding="utf-8") as handle:
            return _normalize_encryption_key(handle.read())

    os.makedirs(os.path.dirname(ENCRYPTION_KEY_FILE) or ".", exist_ok=True)
    key = generate_encryption_key()
    with open(ENCRYPTION_KEY_FILE, "w", encoding="utf-8") as handle:
        handle.write(key)
    return key


def encryption_key_source():
    if _first_value(os.getenv("APP_ENCRYPTION_KEY")):
        return "environment"
    return "generated-file"


def _fernet():
    env_key = _normalize_encryption_key(os.getenv("APP_ENCRYPTION_KEY"))
    key = env_key or _load_or_create_file_key()
    return Fernet(key.encode("ascii"))


def encrypt_value(value):
    return _fernet().encrypt(str(value or "").encode("utf-8")).decode("ascii")


def decrypt_value(value):
    try:
        return _fernet().decrypt(str(value or "").encode("ascii")).decode("utf-8")
    except InvalidToken as error:
        raise ValueError("Could not decrypt saved app settings. Check APP_ENCRYPTION_KEY.") from error


def _ensure_secure_settings_table():
    with get_connection() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS secure_settings (
                key TEXT PRIMARY KEY,
                value_encrypted TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def _load_secure_settings():
    _ensure_secure_settings_table()
    with get_connection() as db:
        rows = db.execute("SELECT key, value_encrypted FROM secure_settings").fetchall()

    settings = {}
    for row in rows:
        key = row["key"]
        value = decrypt_value(row["value_encrypted"]) if key in SENSITIVE_KEYS else row["value_encrypted"]
        settings[key] = value
    return settings


def _save_secure_settings(settings):
    _ensure_secure_settings_table()
    now = utc_now()
    with get_connection() as db:
        for key, value in settings.items():
            stored_value = encrypt_value(value) if key in SENSITIVE_KEYS else str(value or "")
            db.execute(
                """
                INSERT INTO secure_settings (key, value_encrypted, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value_encrypted = excluded.value_encrypted,
                    updated_at = excluded.updated_at
                """,
                (key, stored_value, now, now),
            )


def _read_legacy_config_file():
    if not os.path.exists(LEGACY_CONFIG_PATH):
        return {}
    with open(LEGACY_CONFIG_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _maybe_migrate_legacy_config():
    secure_settings = _load_secure_settings()
    if secure_settings.get("client_id") or not os.path.exists(LEGACY_CONFIG_PATH):
        return secure_settings

    legacy = _read_legacy_config_file().get("microsoft", {})
    if not legacy:
        return secure_settings

    migrated = {
        "client_id": legacy.get("client_id", ""),
        "client_secret": legacy.get("client_secret", ""),
        "tenant": legacy.get("tenant", DEFAULT_MICROSOFT_SETTINGS["tenant"]),
        "imap_host": legacy.get("imap_host", DEFAULT_MICROSOFT_SETTINGS["imap_host"]),
        "imap_port": legacy.get("imap_port", DEFAULT_MICROSOFT_SETTINGS["imap_port"]),
        "max_scan_messages": legacy.get(
            "max_scan_messages",
            DEFAULT_MICROSOFT_SETTINGS["max_scan_messages"],
        ),
    }
    _save_secure_settings(migrated)
    os.replace(LEGACY_CONFIG_PATH, f"{LEGACY_CONFIG_PATH}.migrated")
    return _load_secure_settings()


def load_microsoft_settings():
    stored = _maybe_migrate_legacy_config()
    return {
        "client_id": _first_value(stored.get("client_id"), os.getenv("MS_CLIENT_ID")),
        "client_secret": _first_value(stored.get("client_secret"), os.getenv("MS_CLIENT_SECRET")),
        "tenant": _first_value(stored.get("tenant"), os.getenv("MS_TENANT"), DEFAULT_MICROSOFT_SETTINGS["tenant"]),
        "imap_host": _first_value(
            stored.get("imap_host"),
            os.getenv("MS_IMAP_HOST"),
            DEFAULT_MICROSOFT_SETTINGS["imap_host"],
        ),
        "imap_port": _first_value(
            stored.get("imap_port"),
            os.getenv("MS_IMAP_PORT"),
            DEFAULT_MICROSOFT_SETTINGS["imap_port"],
        ),
        "max_scan_messages": _first_value(
            stored.get("max_scan_messages"),
            os.getenv("MS_IMAP_MAX_SCAN_MESSAGES"),
            DEFAULT_MICROSOFT_SETTINGS["max_scan_messages"],
        ),
    }


def load_google_settings():
    stored = _load_secure_settings()
    return {
        "client_id": _first_value(stored.get("google_client_id"), os.getenv("GOOGLE_CLIENT_ID")),
        "client_secret": _first_value(stored.get("google_client_secret"), os.getenv("GOOGLE_CLIENT_SECRET")),
        "max_scan_messages": _first_value(
            stored.get("google_max_scan_messages"),
            os.getenv("GOOGLE_GMAIL_MAX_SCAN_MESSAGES"),
            DEFAULT_GOOGLE_SETTINGS["google_max_scan_messages"],
        ),
    }


def load_track17_settings():
    stored = _load_secure_settings()
    return {
        "api_key": _first_value(stored.get("track17_api_key"), os.getenv("TRACK17_API_KEY")),
    }


def save_track17_api_key(api_key):
    _save_secure_settings({"track17_api_key": str(api_key or "").strip()})


def normalize_public_base_url(value):
    text = str(value or "").strip().rstrip("/")
    if not text:
        return ""
    if "://" not in text:
        text = f"https://{text}"
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Domænet skal være en gyldig http(s)-adresse.")
    if parsed.path not in {"", "/"}:
        raise ValueError("Domænet må ikke indeholde en sti. Brug kun fx https://dit-domæne.dk.")
    if parsed.query or parsed.fragment:
        raise ValueError("Domænet må ikke indeholde querystring eller fragment.")
    return text.rstrip("/")


def load_public_base_url():
    stored = _load_secure_settings()
    return str(_first_value(stored.get(PUBLIC_BASE_URL_KEY), os.getenv("PUBLIC_BASE_URL"))).rstrip("/")


def save_public_base_url(value):
    public_base_url = normalize_public_base_url(value)
    _save_secure_settings({PUBLIC_BASE_URL_KEY: public_base_url})
    return public_base_url


# --- Automation settings (auto mail scan + tracking refresh) ---

DEFAULT_AUTOMATION_SETTINGS = {
    "auto_scan_enabled": "0",
    "auto_scan_minutes": "30",
    "auto_refresh_enabled": "1",
    # Tracking opdateres altid hver 30. minut (ingen felter nødvendig)
}


def load_automation_settings():
    stored = _load_secure_settings()
    def _v(key):
        return str(stored.get(key, DEFAULT_AUTOMATION_SETTINGS[key])).strip() or DEFAULT_AUTOMATION_SETTINGS[key]

    try:
        scan_minutes = max(5, min(1440, int(_v("auto_scan_minutes"))))
    except ValueError:
        scan_minutes = int(DEFAULT_AUTOMATION_SETTINGS["auto_scan_minutes"])  # 30

    return {
        "auto_scan_enabled": _v("auto_scan_enabled") == "1",
        "auto_scan_minutes": scan_minutes,
        "auto_refresh_enabled": _v("auto_refresh_enabled") == "1",
    }


def save_automation_settings(form_values):
    current = load_automation_settings()
    has_scan_enabled = "auto_scan_enabled" in form_values or "auto_scan_present" in form_values
    has_scan_minutes = "auto_scan_minutes" in form_values
    has_refresh_enabled = "auto_refresh_enabled" in form_values or "auto_refresh_present" in form_values

    enabled_scan = (
        str(form_values.get("auto_scan_enabled", "0")).lower() in {"1", "on", "true", "ja", "yes"}
        if has_scan_enabled
        else current["auto_scan_enabled"]
    )
    enabled_refresh = (
        str(form_values.get("auto_refresh_enabled", "0")).lower() in {"1", "on", "true", "ja", "yes"}
        if has_refresh_enabled
        else current["auto_refresh_enabled"]
    )
    try:
        minutes = int(form_values.get("auto_scan_minutes", current["auto_scan_minutes"]))
    except (TypeError, ValueError):
        minutes = current["auto_scan_minutes"]
    if not has_scan_minutes:
        minutes = current["auto_scan_minutes"]
    minutes = max(5, min(1440, minutes))

    to_store = {
        "auto_scan_enabled": "1" if enabled_scan else "0",
        "auto_scan_minutes": str(minutes),
        "auto_refresh_enabled": "1" if enabled_refresh else "0",
    }
    _save_secure_settings(to_store)
    return load_automation_settings()


def save_microsoft_settings(form_values):
    current_stored = _load_secure_settings()
    current_effective = load_microsoft_settings()

    next_settings = {
        "client_id": str(form_values.get("client_id", "")).strip(),
        "client_secret": str(form_values.get("client_secret", "")).strip()
        or current_stored.get("client_secret", "")
        or current_effective.get("client_secret", ""),
        "tenant": str(form_values.get("tenant", "")).strip() or DEFAULT_MICROSOFT_SETTINGS["tenant"],
        "imap_host": str(form_values.get("imap_host", "")).strip()
        or DEFAULT_MICROSOFT_SETTINGS["imap_host"],
        "imap_port": str(form_values.get("imap_port", "")).strip() or DEFAULT_MICROSOFT_SETTINGS["imap_port"],
        "max_scan_messages": str(form_values.get("max_scan_messages", "")).strip()
        or DEFAULT_MICROSOFT_SETTINGS["max_scan_messages"],
    }

    _validate_microsoft_settings(next_settings)
    _save_secure_settings(next_settings)

    auth_keys = {"client_id", "client_secret", "tenant"}
    auth_changed = any(current_effective.get(key) != next_settings.get(key) for key in auth_keys)
    return next_settings, auth_changed


def save_google_settings(form_values):
    current_stored = _load_secure_settings()
    current_effective = load_google_settings()

    next_settings = {
        "client_id": str(form_values.get("client_id", "")).strip(),
        "client_secret": str(form_values.get("client_secret", "")).strip()
        or current_stored.get("google_client_secret", "")
        or current_effective.get("client_secret", ""),
        "max_scan_messages": str(form_values.get("max_scan_messages", "")).strip()
        or DEFAULT_GOOGLE_SETTINGS["google_max_scan_messages"],
    }

    _validate_google_settings(next_settings)
    _save_secure_settings(
        {
            "google_client_id": next_settings["client_id"],
            "google_client_secret": next_settings["client_secret"],
            "google_max_scan_messages": next_settings["max_scan_messages"],
        }
    )

    auth_changed = any(
        current_effective.get(key) != next_settings.get(key)
        for key in ("client_id", "client_secret")
    )
    return next_settings, auth_changed


def _validate_microsoft_settings(settings):
    if not settings["client_id"]:
        raise ValueError("Microsoft client ID is required.")
    if not settings["client_secret"]:
        raise ValueError("Microsoft client secret is required.")
    if not settings["tenant"]:
        raise ValueError("Microsoft tenant is required.")

    try:
        imap_port = int(settings["imap_port"])
    except ValueError as error:
        raise ValueError("IMAP port must be a number.") from error
    if not 1 <= imap_port <= 65535:
        raise ValueError("IMAP port must be between 1 and 65535.")

    try:
        max_scan_messages = int(settings["max_scan_messages"])
    except ValueError as error:
        raise ValueError("Max scan messages must be a number.") from error
    if not 1 <= max_scan_messages <= 10000:
        raise ValueError("Max scan messages must be between 1 and 10000.")


def _validate_google_settings(settings):
    if not settings["client_id"]:
        raise ValueError("Google client ID is required.")
    if not settings["client_secret"]:
        raise ValueError("Google client secret is required.")

    try:
        max_scan_messages = int(settings["max_scan_messages"])
    except ValueError as error:
        raise ValueError("Max scan messages must be a number.") from error
    if not 1 <= max_scan_messages <= 10000:
        raise ValueError("Max scan messages must be between 1 and 10000.")


def secure_settings_snapshot():
    _ensure_secure_settings_table()
    with get_connection() as db:
        return [dict(row) for row in db.execute("SELECT key, value_encrypted FROM secure_settings").fetchall()]
