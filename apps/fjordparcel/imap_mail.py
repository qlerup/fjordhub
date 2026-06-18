import email
import imaplib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from email.header import decode_header

import msal

from app_config import decrypt_value, encrypt_value, load_microsoft_settings

SCOPES = ["https://outlook.office.com/IMAP.AccessAsUser.All"]
TOKEN_CACHE_PATH = os.getenv("MS_TOKEN_CACHE_PATH", os.path.join("data", "msal_cache.json"))
IMAP_MONTHS = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}


class ImapMailError(RuntimeError):
    pass


def microsoft_config():
    settings = load_microsoft_settings()
    return {
        "client_id": settings["client_id"],
        "client_secret": settings["client_secret"],
        "tenant": settings["tenant"],
        "imap_host": settings["imap_host"],
        "imap_port": int(settings["imap_port"]),
        "max_scan_messages": int(settings["max_scan_messages"]),
    }


def is_configured():
    config = microsoft_config()
    return bool(config["client_id"] and config["client_secret"])


def _load_cache():
    cache = msal.SerializableTokenCache()
    if os.path.exists(TOKEN_CACHE_PATH):
        with open(TOKEN_CACHE_PATH, "r", encoding="utf-8") as handle:
            payload, migrated_from_plaintext = _decode_token_cache(handle.read())
        if payload:
            try:
                cache.deserialize(payload)
            except (json.JSONDecodeError, ValueError) as error:
                raise ImapMailError(
                    "Microsoft token cache is invalid. Disconnect and connect Microsoft again."
                ) from error
        if migrated_from_plaintext:
            _write_token_cache(payload)
    return cache


def _save_cache(cache):
    if cache.has_state_changed:
        _write_token_cache(cache.serialize())


def _decode_token_cache(payload):
    text = (payload or "").strip()
    if not text:
        return "", False

    if text.startswith("{"):
        return text, True

    try:
        return decrypt_value(text), False
    except ValueError as error:
        raise ImapMailError("Could not decrypt Microsoft token cache. Check APP_ENCRYPTION_KEY.") from error


def _write_token_cache(payload):
    os.makedirs(os.path.dirname(TOKEN_CACHE_PATH) or ".", exist_ok=True)
    with open(TOKEN_CACHE_PATH, "w", encoding="utf-8") as handle:
        handle.write(encrypt_value(payload or ""))


def _build_app(cache=None):
    config = microsoft_config()
    if not is_configured():
        raise ImapMailError("Microsoft IMAP integration is not configured.")
    return msal.ConfidentialClientApplication(
        config["client_id"],
        authority=f"https://login.microsoftonline.com/{config['tenant']}",
        client_credential=config["client_secret"],
        token_cache=cache,
    )


def build_auth_flow(redirect_uri):
    cache = _load_cache()
    app = _build_app(cache)
    return app.initiate_auth_code_flow(
        scopes=SCOPES,
        redirect_uri=redirect_uri,
        prompt="select_account",
    )


def complete_auth_flow(flow, auth_response):
    cache = _load_cache()
    app = _build_app(cache)
    result = app.acquire_token_by_auth_code_flow(flow, auth_response)
    _save_cache(cache)

    if "error" in result:
        message = result.get("error_description") or result.get("error") or "Microsoft login failed."
        raise ImapMailError(message)
    return result


def get_accounts():
    if not is_configured():
        return []
    cache = _load_cache()
    app = _build_app(cache)
    return app.get_accounts()


def disconnect(username=None):
    if username:
        cache = _load_cache()
        if not is_configured():
            return
        app = _build_app(cache)
        target = str(username or "").strip().lower()
        for account in app.get_accounts():
            if str(account.get("username") or "").strip().lower() == target:
                app.remove_account(account)
                _save_cache(cache)
                return
        return

    if os.path.exists(TOKEN_CACHE_PATH):
        os.remove(TOKEN_CACHE_PATH)


def _acquire_token_for_account(cache, app, account):
    result = app.acquire_token_silent(SCOPES, account=account)
    _save_cache(cache)

    if not result or "access_token" not in result:
        raise ImapMailError("Could not refresh Microsoft access token. Connect the account again.")

    username = account.get("username")
    if not username:
        raise ImapMailError("The connected Microsoft account did not expose an email address.")

    return result["access_token"], username


def _select_accounts(accounts, username=None):
    if not username:
        return list(accounts)

    target = str(username or "").strip().lower()
    selected = [
        account
        for account in accounts
        if str(account.get("username") or "").strip().lower() == target
    ]
    if not selected:
        raise ImapMailError(f"Microsoft account {username} is not connected.")
    return selected


def acquire_token_and_username():
    cache = _load_cache()
    app = _build_app(cache)
    accounts = app.get_accounts()
    if not accounts:
        raise ImapMailError("No Microsoft account is connected.")

    return _acquire_token_for_account(cache, app, accounts[0])


def _xoauth2_authenticator(username, access_token):
    auth_string = f"user={username}\x01auth=Bearer {access_token}\x01\x01"
    return lambda _challenge: auth_string.encode("utf-8")


def _decode_header_value(value):
    if not value:
        return ""

    decoded_parts = []
    for part, encoding in decode_header(value):
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(encoding or "utf-8", errors="replace"))
        else:
            decoded_parts.append(part)
    return "".join(decoded_parts)


def _message_sender(message):
    sender = email.utils.parseaddr(message.get("From", ""))[1]
    return sender or _decode_header_value(message.get("From", ""))


def _message_text(message):
    chunks = []
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            disposition = (part.get("Content-Disposition") or "").lower()
            if "attachment" in disposition or content_type not in {"text/plain", "text/html"}:
                continue
            payload = part.get_payload(decode=True)
            if payload:
                charset = part.get_content_charset() or "utf-8"
                chunks.append(payload.decode(charset, errors="replace"))
    else:
        payload = message.get_payload(decode=True)
        if payload:
            charset = message.get_content_charset() or "utf-8"
            chunks.append(payload.decode(charset, errors="replace"))
    return "\n".join(chunks)


def _strip_html(text):
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_message(raw_message):
    message = email.message_from_bytes(raw_message)
    raw_body = _message_text(message)
    stripped_body = _strip_html(raw_body)
    return {
        "subject": _decode_header_value(message.get("Subject", "")),
        "bodyPreview": raw_body[:5000],
        "body": stripped_body[:15000],
        "receivedDateTime": email.utils.parsedate_to_datetime(message.get("Date")).isoformat()
        if message.get("Date")
        else None,
        "from": {
            "emailAddress": {
                "address": _message_sender(message),
                "name": _decode_header_value(email.utils.parseaddr(message.get("From", ""))[0]),
            }
        },
    }


def normalize_scan_days(days):
    try:
        value = int(days or 14)
    except (TypeError, ValueError) as error:
        raise ValueError("Scan period must be a number of days.") from error

    if value not in {1, 7, 14, 21}:
        raise ValueError("Scan period must be 7, 14, or 21 days.")
    return value


def _imap_since_date(days, now=None):
    scan_days = normalize_scan_days(days)
    current_date = (now or datetime.now(timezone.utc)).date()
    since_date = current_date - timedelta(days=scan_days)
    return f"{since_date.day:02d}-{IMAP_MONTHS[since_date.month]}-{since_date.year}"


def _iter_recent_messages_for_account(access_token, username, config, scan_days, since_date, progress_callback=None):
    try:
        if progress_callback:
            progress_callback(stage=f"Connecting to {username}", scanned=0, total=None)
        with imaplib.IMAP4_SSL(config["imap_host"], config["imap_port"]) as mailbox:
            mailbox.authenticate("XOAUTH2", _xoauth2_authenticator(username, access_token))
            if progress_callback:
                progress_callback(stage=f"Opening {username} inbox", scanned=0, total=None)

            status, _data = mailbox.select("INBOX", readonly=True)
            if status != "OK":
                raise ImapMailError(f"Could not open INBOX for {username} over IMAP.")

            if progress_callback:
                progress_callback(stage=f"Searching {username} for the last {scan_days} days", scanned=0, total=None)
            status, data = mailbox.search(None, "SINCE", since_date)
            if status != "OK":
                raise ImapMailError(f"Could not search INBOX for {username} over IMAP.")

            message_ids = data[0].split()
            limited_message_ids = list(reversed(message_ids[-config["max_scan_messages"] :]))
            total = len(limited_message_ids)
            if progress_callback:
                progress_callback(stage=f"Scanning {username}", scanned=0, total=total)

            for index, message_id in enumerate(limited_message_ids, start=1):
                status, fetched = mailbox.fetch(message_id, "(RFC822)")
                if progress_callback:
                    progress_callback(stage=f"Scanning {username}", scanned=index, total=total)
                if status != "OK" or not fetched:
                    continue
                raw_message = next(
                    (part[1] for part in fetched if isinstance(part, tuple) and part[1]),
                    None,
                )
                if raw_message:
                    yield _parse_message(raw_message)
    except imaplib.IMAP4.error as error:
        raise ImapMailError(f"IMAP authentication or mailbox access failed for {username}: {error}") from error
    except OSError as error:
        raise ImapMailError(f"Could not connect to Microsoft IMAP for {username}: {error}") from error


def iter_recent_messages(days=14, progress_callback=None, username=None):
    cache = _load_cache()
    app = _build_app(cache)
    accounts = app.get_accounts()
    if not accounts:
        raise ImapMailError("No Microsoft account is connected.")

    config = microsoft_config()
    scan_days = normalize_scan_days(days)
    since_date = _imap_since_date(scan_days)

    for account in _select_accounts(accounts, username=username):
        access_token, username = _acquire_token_for_account(cache, app, account)
        yield from _iter_recent_messages_for_account(
            access_token,
            username,
            config,
            scan_days,
            since_date,
            progress_callback=progress_callback,
        )


def fetch_recent_messages(days=14):
    return list(iter_recent_messages(days))
