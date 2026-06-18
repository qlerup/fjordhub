import base64
import email.utils
import html
import json
import os
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from app_config import decrypt_value, encrypt_value, load_google_settings
from imap_mail import normalize_scan_days
from storage import get_connection, utc_now


AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
GMAIL_API = "https://gmail.googleapis.com/gmail/v1"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
MAX_GMAIL_PAGE_SIZE = 500


class GmailMailError(RuntimeError):
    pass


def google_config():
    settings = load_google_settings()
    return {
        "client_id": settings["client_id"],
        "client_secret": settings["client_secret"],
        "max_scan_messages": int(settings["max_scan_messages"]),
    }


def is_configured():
    config = google_config()
    return bool(config["client_id"] and config["client_secret"])


def _ensure_gmail_accounts_table():
    with get_connection() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS gmail_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                credentials_encrypted TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def _credentials_from_row(row):
    try:
        credentials = json.loads(decrypt_value(row["credentials_encrypted"]))
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise GmailMailError("Could not decrypt saved Gmail credentials. Check APP_ENCRYPTION_KEY.") from error
    if not isinstance(credentials, dict):
        raise GmailMailError("Saved Gmail credentials are invalid. Connect Gmail again.")
    return credentials


def _load_account_row(email_address):
    _ensure_gmail_accounts_table()
    with get_connection() as db:
        return db.execute(
            "SELECT * FROM gmail_accounts WHERE lower(email) = lower(?)",
            (str(email_address or "").strip(),),
        ).fetchone()


def _load_account_rows():
    _ensure_gmail_accounts_table()
    with get_connection() as db:
        return db.execute("SELECT * FROM gmail_accounts ORDER BY lower(email)").fetchall()


def _save_account_credentials(email_address, credentials):
    email_address = str(email_address or "").strip().lower()
    if not email_address:
        raise GmailMailError("Google did not expose an email address for this account.")

    now = utc_now()
    stored_credentials = dict(credentials)
    stored_credentials["email"] = email_address
    _ensure_gmail_accounts_table()
    with get_connection() as db:
        db.execute(
            """
            INSERT INTO gmail_accounts (email, credentials_encrypted, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                credentials_encrypted = excluded.credentials_encrypted,
                updated_at = excluded.updated_at
            """,
            (email_address, encrypt_value(json.dumps(stored_credentials)), now, now),
        )


def get_accounts():
    accounts = []
    for row in _load_account_rows():
        email_address = str(row["email"] or "").strip()
        if not email_address:
            continue
        accounts.append(
            {
                "username": email_address,
                "provider": "gmail",
                "provider_label": "Gmail",
                "method": "Gmail API OAuth",
                "account_key": f"gmail:{email_address.lower()}",
            }
        )
    return accounts


def disconnect(email_address=None):
    _ensure_gmail_accounts_table()
    if email_address:
        row = _load_account_row(email_address)
        if row:
            credentials = _credentials_from_row(row)
            token = credentials.get("refresh_token") or credentials.get("access_token")
            if token:
                _revoke_token(token)
        with get_connection() as db:
            db.execute("DELETE FROM gmail_accounts WHERE lower(email) = lower(?)", (str(email_address),))
        return

    for row in _load_account_rows():
        credentials = _credentials_from_row(row)
        token = credentials.get("refresh_token") or credentials.get("access_token")
        if token:
            _revoke_token(token)
    with get_connection() as db:
        db.execute("DELETE FROM gmail_accounts")


def build_auth_flow(redirect_uri):
    if not is_configured():
        raise GmailMailError("Google Gmail integration is not configured.")

    config = google_config()
    state = secrets.token_urlsafe(32)
    query = urllib.parse.urlencode(
        {
            "client_id": config["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "consent select_account",
            "state": state,
        }
    )
    return {
        "auth_uri": f"{AUTH_URL}?{query}",
        "state": state,
        "redirect_uri": redirect_uri,
    }


def complete_auth_flow(flow, auth_response):
    expected_state = str((flow or {}).get("state") or "")
    received_state = str((auth_response or {}).get("state") or "")
    if not expected_state or received_state != expected_state:
        raise GmailMailError("Google login session expired. Try connecting again.")

    if auth_response.get("error"):
        detail = auth_response.get("error_description") or auth_response.get("error")
        raise GmailMailError(f"Google login failed: {detail}")

    code = str(auth_response.get("code") or "").strip()
    if not code:
        raise GmailMailError("Google login did not return an authorization code.")

    token_payload = _token_request(
        {
            "code": code,
            "client_id": google_config()["client_id"],
            "client_secret": google_config()["client_secret"],
            "redirect_uri": flow["redirect_uri"],
            "grant_type": "authorization_code",
        }
    )
    credentials = _credentials_from_token_payload(token_payload)
    profile = _api_get(f"{GMAIL_API}/users/me/profile", credentials["access_token"])
    email_address = str(profile.get("emailAddress") or "").strip().lower()
    if not email_address:
        raise GmailMailError("Google did not expose an email address for this account.")

    if not credentials.get("refresh_token"):
        existing = _load_account_row(email_address)
        if existing:
            existing_credentials = _credentials_from_row(existing)
            credentials["refresh_token"] = existing_credentials.get("refresh_token")
        if not credentials.get("refresh_token"):
            raise GmailMailError(
                "Google did not return a refresh token. Remove FjordParcel access in your Google account and connect Gmail again."
            )

    _save_account_credentials(email_address, credentials)
    return {
        "username": email_address,
        "provider": "gmail",
        "provider_label": "Gmail",
        "method": "Gmail API OAuth",
        "account_key": f"gmail:{email_address}",
    }


def _credentials_from_token_payload(payload):
    access_token = str(payload.get("access_token") or "").strip()
    if not access_token:
        raise GmailMailError("Google did not return an access token.")

    expires_in = int(payload.get("expires_in") or 3600)
    return {
        "access_token": access_token,
        "refresh_token": str(payload.get("refresh_token") or "").strip(),
        "scope": str(payload.get("scope") or " ".join(SCOPES)),
        "token_type": str(payload.get("token_type") or "Bearer"),
        "expires_at": int(time.time()) + max(60, expires_in) - 60,
    }


def _token_request(form_values):
    return _request_json(TOKEN_URL, method="POST", form_values=form_values)


def _api_get(url, access_token, params=None):
    return _request_json(url, access_token=access_token, params=params)


def _revoke_token(token):
    try:
        _request_json(REVOKE_URL, method="POST", form_values={"token": token})
    except GmailMailError:
        pass


def _request_json(url, method="GET", access_token=None, form_values=None, params=None, timeout=30):
    if params:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{urllib.parse.urlencode(params)}"

    data = None
    headers = {"Accept": "application/json"}
    if form_values is not None:
        data = urllib.parse.urlencode(form_values).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        detail = _google_error_message(raw) or error.reason or "Google API request failed."
        raise GmailMailError(detail) from error
    except OSError as error:
        raise GmailMailError(f"Could not connect to Google Gmail API: {error}") from error

    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise GmailMailError("Google returned an invalid JSON response.") from error


def _google_error_message(raw_body):
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        return raw_body.strip()[:260]
    error = payload.get("error")
    if isinstance(error, dict):
        return str(error.get("message") or error.get("status") or "Google API request failed.")
    if isinstance(error, str):
        return str(payload.get("error_description") or error)
    return ""


def _ensure_access_token(email_address, credentials):
    expires_at = int(credentials.get("expires_at") or 0)
    if credentials.get("access_token") and expires_at > int(time.time()) + 60:
        return credentials

    refresh_token = str(credentials.get("refresh_token") or "").strip()
    if not refresh_token:
        raise GmailMailError(f"Gmail access for {email_address} has expired. Connect Gmail again.")

    payload = _token_request(
        {
            "client_id": google_config()["client_id"],
            "client_secret": google_config()["client_secret"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    )
    refreshed = _credentials_from_token_payload({**payload, "refresh_token": refresh_token})
    _save_account_credentials(email_address, refreshed)
    return refreshed


def _list_message_ids(access_token, scan_days, max_messages):
    message_ids = []
    page_token = None

    while len(message_ids) < max_messages:
        page_size = min(MAX_GMAIL_PAGE_SIZE, max_messages - len(message_ids))
        params = {
            "q": f"newer_than:{scan_days}d",
            "maxResults": page_size,
        }
        if page_token:
            params["pageToken"] = page_token

        payload = _api_get(f"{GMAIL_API}/users/me/messages", access_token, params=params)
        message_ids.extend(item["id"] for item in payload.get("messages", []) if item.get("id"))
        page_token = payload.get("nextPageToken")
        if not page_token:
            break

    return message_ids[:max_messages]


def _get_message(access_token, message_id):
    return _api_get(
        f"{GMAIL_API}/users/me/messages/{urllib.parse.quote(str(message_id))}",
        access_token,
        params={"format": "full"},
    )


def _decode_base64url(value):
    text = str(value or "")
    if not text:
        return ""
    padded = text + ("=" * (-len(text) % 4))
    return base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8", errors="replace")


def _header(payload, name):
    target = str(name or "").lower()
    for header in payload.get("headers", []) or []:
        if str(header.get("name") or "").lower() == target:
            return str(header.get("value") or "")
    return ""


def _body_chunks(payload):
    chunks = []
    filename = str(payload.get("filename") or "")
    mime_type = str(payload.get("mimeType") or "").lower()
    body = payload.get("body") or {}
    data = body.get("data")

    if not filename and data and mime_type in {"text/plain", "text/html"}:
        chunks.append(_decode_base64url(data))

    for part in payload.get("parts", []) or []:
        chunks.extend(_body_chunks(part))

    if not chunks and not filename and data and not payload.get("parts"):
        chunks.append(_decode_base64url(data))
    return chunks


def _message_datetime(headers_payload, message_payload):
    date_header = _header(headers_payload, "Date")
    if date_header:
        try:
            parsed = email.utils.parsedate_to_datetime(date_header)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.isoformat()
        except (TypeError, ValueError):
            pass

    internal_date = str(message_payload.get("internalDate") or "").strip()
    if internal_date.isdigit():
        return datetime.fromtimestamp(int(internal_date) / 1000, tz=timezone.utc).isoformat()
    return None


def _parse_gmail_message(message_payload):
    payload = message_payload.get("payload") or {}
    from_header = _header(payload, "From")
    sender_name, sender_address = email.utils.parseaddr(from_header)
    body_text = "\n".join(_body_chunks(payload)).strip()
    if not body_text:
        body_text = str(message_payload.get("snippet") or "")
    raw_body = html.unescape(body_text)
    stripped_body = re.sub(r"<[^>]+>", " ", raw_body)
    stripped_body = re.sub(r"\s+", " ", stripped_body).strip()

    return {
        "subject": _header(payload, "Subject"),
        "bodyPreview": raw_body[:5000],
        "body": stripped_body[:15000],
        "receivedDateTime": _message_datetime(payload, message_payload),
        "from": {
            "emailAddress": {
                "address": sender_address or from_header,
                "name": sender_name,
            }
        },
    }


def iter_recent_messages(days=14, progress_callback=None, email_address=None):
    if not is_configured():
        raise GmailMailError("Google Gmail integration is not configured.")

    if email_address:
        row = _load_account_row(email_address)
        rows = [row] if row else []
    else:
        rows = _load_account_rows()
    if not rows:
        if email_address:
            raise GmailMailError(f"Gmail account {email_address} is not connected.")
        raise GmailMailError("No Gmail account is connected.")

    scan_days = normalize_scan_days(days)
    config = google_config()

    for row in rows:
        email_address = str(row["email"] or "")
        credentials = _ensure_access_token(email_address, _credentials_from_row(row))
        access_token = credentials["access_token"]

        if progress_callback:
            progress_callback(stage=f"Searching Gmail {email_address}", scanned=0, total=None)
        message_ids = _list_message_ids(access_token, scan_days, config["max_scan_messages"])
        total = len(message_ids)
        if progress_callback:
            progress_callback(stage=f"Scanning Gmail {email_address}", scanned=0, total=total)

        for index, message_id in enumerate(message_ids, start=1):
            payload = _get_message(access_token, message_id)
            if progress_callback:
                progress_callback(stage=f"Scanning Gmail {email_address}", scanned=index, total=total)
            yield _parse_gmail_message(payload)


def fetch_recent_messages(days=14):
    return list(iter_recent_messages(days))
