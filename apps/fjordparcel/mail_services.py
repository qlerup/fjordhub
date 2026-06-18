import gmail_mail
import imap_mail
from gmail_mail import GmailMailError
from imap_mail import ImapMailError, normalize_scan_days


class MailServiceError(RuntimeError):
    pass


def _microsoft_account(account):
    username = str(account.get("username") or "").strip()
    return {
        **account,
        "username": username,
        "provider": "microsoft",
        "provider_label": "Microsoft",
        "method": "IMAP OAuth",
        "account_key": f"microsoft:{username.lower()}",
    }


def get_accounts():
    accounts = []
    try:
        accounts.extend(_microsoft_account(account) for account in imap_mail.get_accounts())
        accounts.extend(gmail_mail.get_accounts())
    except (ImapMailError, GmailMailError) as error:
        raise MailServiceError(str(error)) from error
    return [account for account in accounts if account.get("username")]


def has_accounts():
    return bool(get_accounts())


def is_any_configured():
    return imap_mail.is_configured() or gmail_mail.is_configured()


def find_account(provider, username):
    target_provider = str(provider or "").strip().lower()
    target_username = str(username or "").strip().lower()
    for account in get_accounts():
        if (
            str(account.get("provider") or "").strip().lower() == target_provider
            and str(account.get("username") or "").strip().lower() == target_username
        ):
            return account
    return None


def disconnect(provider, username=None):
    provider_name = str(provider or "").strip().lower()
    if provider_name == "microsoft":
        imap_mail.disconnect(username)
        return
    if provider_name == "gmail":
        gmail_mail.disconnect(username)
        return
    raise MailServiceError("Unknown mail provider.")


def iter_recent_messages(days=14, progress_callback=None, provider=None, username=None):
    provider_name = str(provider or "").strip().lower()
    username_value = str(username or "").strip()

    if provider_name:
        if not username_value:
            raise MailServiceError("Choose a mail account to scan.")
        account = find_account(provider_name, username_value)
        if not account:
            raise MailServiceError("The selected mail account is not connected.")
        if provider_name == "microsoft":
            yield from imap_mail.iter_recent_messages(
                days,
                progress_callback=progress_callback,
                username=username_value,
            )
            return
        if provider_name == "gmail":
            yield from gmail_mail.iter_recent_messages(
                days,
                progress_callback=progress_callback,
                email_address=username_value,
            )
            return
        raise MailServiceError("Unknown mail provider.")

    accounts = get_accounts()
    if not accounts:
        raise MailServiceError("No mail account is connected.")

    providers = {account["provider"] for account in accounts}
    if "microsoft" in providers:
        yield from imap_mail.iter_recent_messages(days, progress_callback=progress_callback)
    if "gmail" in providers:
        yield from gmail_mail.iter_recent_messages(days, progress_callback=progress_callback)
