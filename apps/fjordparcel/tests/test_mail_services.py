import mail_services


def test_iter_recent_messages_scans_only_selected_gmail_account(monkeypatch):
    calls = []

    monkeypatch.setattr(
        mail_services.imap_mail,
        "get_accounts",
        lambda: [{"username": "user@hotmail.com"}],
    )
    monkeypatch.setattr(
        mail_services.gmail_mail,
        "get_accounts",
        lambda: [
            {
                "username": "user@gmail.com",
                "provider": "gmail",
                "provider_label": "Gmail",
                "method": "Gmail API OAuth",
                "account_key": "gmail:user@gmail.com",
            }
        ],
    )

    def fake_imap_iter(*_args, **_kwargs):
        calls.append(("microsoft", _kwargs.get("username")))
        return iter([{"subject": "wrong"}])

    def fake_gmail_iter(*_args, **kwargs):
        calls.append(("gmail", kwargs.get("email_address")))
        return iter([{"subject": "right"}])

    monkeypatch.setattr(mail_services.imap_mail, "iter_recent_messages", fake_imap_iter)
    monkeypatch.setattr(mail_services.gmail_mail, "iter_recent_messages", fake_gmail_iter)

    messages = list(
        mail_services.iter_recent_messages(
            14,
            provider="gmail",
            username="user@gmail.com",
        )
    )

    assert messages == [{"subject": "right"}]
    assert calls == [("gmail", "user@gmail.com")]
