import json

import app as app_module
import storage
from tracking_providers import TrackingLookupResult


def test_gls_scan_uses_merchant_as_label(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()

    messages = [
        {
            "subject": "GLS pakke",
            "from": {
                "emailAddress": {
                    "address": "noreply@gls-denmark.com",
                    "name": "GLS",
                }
            },
            "bodyPreview": (
                "Tak fordi du handlede hos ELEXTRA.dk. Din pakke er afsendt med GLS.\n"
            ),
            "receivedDateTime": "2026-05-28T19:19:00+02:00",
        },
        {
            "subject": "GLS pakke",
            "from": {
                "emailAddress": {
                    "address": "noreply@gls-denmark.com",
                    "name": "GLS",
                }
            },
            "bodyPreview": (
                "Tak fordi du handlede hos Magnetz og Magnordic. Din pakke er afsendt med GLS.\n"
            ),
            "receivedDateTime": "2026-05-28T17:26:20+02:00",
        },
        {
            "subject": "Du kan nu hente pakke 027624557628",
            "from": {
                "emailAddress": {
                    "address": "pakke-shop@pakkeshop.dk",
                    "name": "GLS PakkeShop",
                }
            },
            "bodyPreview": (
                "Nu kan du godt begynde at glaede dig. Din pakke fra Magnetz og Magnordic "
                "er blevet leveret af din lokale GLS-chauffoer. Dit pakkenummer er 027624557628."
            ),
            "receivedDateTime": "2026-05-29T08:55:48+00:00",
        },
        {
            "subject": "Du kan nu hente pakke 075624238061",
            "from": {
                "emailAddress": {
                    "address": "pakke-shop@pakkeshop.dk",
                    "name": "GLS PakkeShop",
                }
            },
            "bodyPreview": (
                "Nu kan du godt begynde at glaede dig. Din pakke fra ELEXTRA.dk "
                "er blevet leveret af din lokale GLS-chauffoer. GLS pakkenummer: 075624238061 er klar til afhentning"
            ),
            "receivedDateTime": "2026-05-29T08:55:41+00:00",
        }
    ]
    refresh_calls = []

    def fake_fetch_tracking(number, carrier="", postal_codes=None, timeout=None):
        refresh_calls.append((number, carrier))
        return TrackingLookupResult(
            carrier="GLS",
            tracking_number=number,
            status="leveret",
            status_code="DELIVERED",
            summary="Leveret med kvittering",
            last_event_at="2026-05-29T08:03:41",
            last_event_text="Pakken er leveret",
            events=[
                {
                    "description": "Pakken er leveret",
                    "status": "DELIVERED",
                    "date_iso": "2026-05-29T08:03:41",
                    "display_date": "29-05-2026",
                    "display_time": "08:03",
                    "location": "Ringsted, Danmark",
                }
            ],
            tracking_url="https://gls-group.com/DK/da/find-pakke?match=075624238061",
            source="gls-rstt028",
        )

    monkeypatch.setattr(
        app_module.mail_services,
        "iter_recent_messages",
        lambda _days, progress_callback=None: iter(messages),
    )
    monkeypatch.setattr(storage, "fetch_tracking", fake_fetch_tracking)

    summary = app_module._scan_messages(14, lambda **_updates: None)
    shipments = storage.list_shipments(include_archived=True)

    by_number = {item["tracking_number"]: item for item in shipments}

    assert summary["found"] == 2
    assert summary["new_shipments"] == 2
    assert by_number["027624557628"]["carrier"] == "GLS"
    assert by_number["027624557628"]["label"] == "Magnetz og Magnordic"
    assert by_number["075624238061"]["label"] == "ELEXTRA.dk"
    assert by_number["027624557628"]["last_event_text"] == "GLS-pakken er klar til afhentning"
    assert by_number["027624557628"]["events"][0]["location"] == "Ringsted, Danmark"
    assert refresh_calls == [("027624557628", "GLS"), ("075624238061", "GLS")]


def test_gls_scan_matches_merchant_label_by_tracking_reference(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()

    messages = [
        {
            "subject": "GLS pakke",
            "from": {"emailAddress": {"address": "noreply@gls-denmark.com", "name": "GLS"}},
            "bodyPreview": (
                'Tak fordi du handlede hos ELEXTRA.dk. Din pakke er afsendt med GLS. '
                '<a href="https://gls-group.com/DK/da/find-pakke?txtRefNo=YOXVB8CE">GLS Track & Trace</a>'
            ),
            "receivedDateTime": "2026-05-28T19:19:00+02:00",
        },
        {
            "subject": "GLS pakke",
            "from": {"emailAddress": {"address": "noreply@gls-denmark.com", "name": "GLS"}},
            "bodyPreview": (
                'Tak fordi du handlede hos Magnetz og Magnordic. Din pakke er afsendt med GLS. '
                '<a href="https://gls-group.com/DK/da/find-pakke?txtRefNo=YMQHJ9AQ">GLS Track & Trace</a>'
            ),
            "receivedDateTime": "2026-05-28T17:26:20+02:00",
        },
        {
            "subject": "Du kan nu hente pakke 027624557628",
            "from": {"emailAddress": {"address": "pakke-shop@pakkeshop.dk", "name": "GLS PakkeShop"}},
            "bodyPreview": (
                "Nu kan du godt begynde at glaede dig. Din pakke fra Magnetz og Magnordic "
                "er blevet leveret af din lokale GLS-chauffoer. Dit pakkenummer er 027624557628."
            ),
            "receivedDateTime": "2026-05-29T08:55:48+00:00",
        },
        {
            "subject": "Du kan nu hente pakke 075624238061",
            "from": {"emailAddress": {"address": "pakke-shop@pakkeshop.dk", "name": "GLS PakkeShop"}},
            "bodyPreview": (
                "Nu kan du godt begynde at glaede dig. Din pakke fra ELEXTRA.dk "
                "er blevet leveret af din lokale GLS-chauffoer. Dit pakkenummer er 075624238061."
            ),
            "receivedDateTime": "2026-05-29T08:55:41+00:00",
        },
    ]

    def fake_fetch_tracking(number, carrier="", postal_codes=None, timeout=None):
        references = {
            "027624557628": "YMQHJ9AQ",
            "075624238061": "YOXVB8CE",
        }
        return TrackingLookupResult(
            carrier="GLS",
            tracking_number=number,
            status="leveret",
            last_event_text="Pakken er leveret",
            reference_number=references[number],
            tracking_url=f"https://gls-group.com/DK/da/find-pakke?match={number}",
            source="gls-rstt029",
        )

    monkeypatch.setattr(
        app_module.mail_services,
        "iter_recent_messages",
        lambda _days, progress_callback=None: iter(messages),
    )
    monkeypatch.setattr(storage, "fetch_tracking", fake_fetch_tracking)

    summary = app_module._scan_messages(14, lambda **_updates: None)
    by_number = {item["tracking_number"]: item for item in storage.list_shipments()}

    assert summary["found"] == 4
    assert by_number["027624557628"]["label"] == "Magnetz og Magnordic"
    assert by_number["075624238061"]["label"] == "ELEXTRA.dk"
    assert by_number["027624557628"]["tracking_reference"] == "YMQHJ9AQ"
    assert by_number["075624238061"]["tracking_reference"] == "YOXVB8CE"


def test_scan_updates_existing_gls_pickup_location_and_code(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()
    _created, existing = storage.add_shipment(
        "027624557628",
        label="Magnetz og Magnordic",
        source="mail",
        carrier="GLS",
    )

    messages = [
        {
            "subject": "Din pakke er nu klar til afhentning",
            "from": {"emailAddress": {"address": "noreply@gls-denmark.com", "name": "GLS"}},
            "bodyPreview": (
                "Hej Christian Glerup\n\n"
                "Nu kan du godt begynde at glaede dig. Din pakke fra Magnetz og Magnordic er blevet leveret af "
                "din lokale GLS-chauffoer. Den venter paa dig i PakkeShoppen hos:\n\n"
                "7-Eleven Odensevej\n"
                "Odensevej 102\n"
                "4700 Naestved\n\n"
                "Dit pakkenummer er 027624557628.\n\n"
                "Naar du henter din pakke, skal du ogsaa oplyse hentekode 090."
            ),
            "receivedDateTime": "2026-06-06T10:30:00+02:00",
        },
    ]

    def fake_fetch_tracking(number, carrier="", postal_codes=None, timeout=None):
        return TrackingLookupResult(
            carrier=carrier,
            tracking_number=number,
            status="leveret",
            last_event_text="Din pakke er udleveret i PakkeShoppen.",
            tracking_url=f"https://example.test/{number}",
            source=f"{carrier}-test",
        )

    monkeypatch.setattr(
        app_module.mail_services,
        "iter_recent_messages",
        lambda _days, progress_callback=None: iter(messages),
    )
    monkeypatch.setattr(storage, "fetch_tracking", fake_fetch_tracking)

    summary = app_module._scan_messages(14, lambda **_updates: None)
    updated = storage.get_shipment(existing["id"])

    assert summary["found"] == 1
    assert summary["new_shipments"] == 0
    assert updated["pickup_location"] == "7-Eleven Odensevej Odensevej 102 4700 Naestved"
    assert updated["pickup_code"] == "090"


def test_scan_uses_dao_and_bring_mail_labels(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()

    messages = [
        {
            "subject": "dao pakke",
            "from": {"emailAddress": {"address": "noreply@dao.as", "name": "dao"}},
            "bodyPreview": (
                "Hej Christian\n\n"
                "bent Foelvg har netop indleveret en pakke som nu er paa vej til dig.\n"
                "Pakkenr.: 00057151273676436276"
            ),
            "receivedDateTime": "2026-06-03T13:09:00+02:00",
        },
        {
            "subject": "Din pakke fra MyTrendyPhone er snart paa vej",
            "from": {"emailAddress": {"address": "noreply@bring.com", "name": "Bring"}},
            "bodyPreview": (
                "Din pakke fra MyTrendyPhone er snart hos os. "
                "Brug 370722152477343049 paa vores hjemmeside."
            ),
            "receivedDateTime": "2026-06-03T16:29:00+02:00",
        },
    ]

    def fake_fetch_tracking(number, carrier="", postal_codes=None, timeout=None):
        return TrackingLookupResult(
            carrier=carrier,
            tracking_number=number,
            status="fundet",
            last_event_text="Pakken er fundet",
            tracking_url=f"https://example.test/{number}",
            source=f"{carrier}-test",
        )

    monkeypatch.setattr(
        app_module.mail_services,
        "iter_recent_messages",
        lambda _days, progress_callback=None: iter(messages),
    )
    monkeypatch.setattr(storage, "fetch_tracking", fake_fetch_tracking)

    summary = app_module._scan_messages(14, lambda **_updates: None)
    by_number = {item["tracking_number"]: item for item in storage.list_shipments()}

    assert summary["found"] == 2
    assert by_number["00057151273676436276"]["carrier"] == "DAO"
    assert by_number["00057151273676436276"]["label"] == "bent Foelvg"
    assert by_number["370722152477343049"]["carrier"] == "Bring"
    assert by_number["370722152477343049"]["label"] == "MyTrendyPhone"


def test_scan_uses_postnord_mail_label(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()

    messages = [
        {
            "subject": "Der er nyt om din PostNord-pakke",
            "from": {"emailAddress": {"address": "no-reply@postnord.com", "name": "PostNord"}},
            "bodyPreview": (
                "Hej, der er nyt om din PostNord-pakke.\n\n"
                "Vi har modtaget din pakke 00073215400568030824 fra Proshop a/s som har sendt den "
                "med udlevering til dig via en PostNord Pakkeshop eller en PostNord Pakkeboks. "
                "Naar pakken er klar til afhentning, modtager du en ny besked fra os."
            ),
            "receivedDateTime": "2026-05-10T20:51:00+02:00",
        },
    ]

    def fake_fetch_tracking(number, carrier="", postal_codes=None, timeout=None):
        return TrackingLookupResult(
            carrier=carrier,
            tracking_number=number,
            status="fundet",
            last_event_text="Pakken er registreret",
            tracking_url=f"https://example.test/{number}",
            source=f"{carrier}-test",
        )

    monkeypatch.setattr(
        app_module.mail_services,
        "iter_recent_messages",
        lambda _days, progress_callback=None: iter(messages),
    )
    monkeypatch.setattr(storage, "fetch_tracking", fake_fetch_tracking)

    summary = app_module._scan_messages(14, lambda **_updates: None)
    by_number = {item["tracking_number"]: item for item in storage.list_shipments()}

    assert summary["found"] == 1
    assert summary["new_shipments"] == 1
    assert by_number["00073215400568030824"]["carrier"] == "PostNord"
    assert by_number["00073215400568030824"]["label"] == "Proshop a/s"


def test_scan_updates_existing_postnord_pickup_from_link(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()
    _created, existing = storage.add_shipment(
        "00073215400568030824",
        label="Proshop a/s",
        source="mail",
        carrier="PostNord",
    )

    messages = [
        {
            "subject": "Din PostNord-pakke er klar til afhentning",
            "from": {"emailAddress": {"address": "no-reply@postnord.com", "name": "PostNord"}},
            "bodyPreview": (
                "Hej, der er nyt om din PostNord-pakke.\n\n"
                "Din pakke fra Proshop a/s er klar til afhentning i Pakkeshop "
                "7-Eleven , Odensevej 102, 4700 Naestved. Hent senest den 18.5. "
                "Vis din hentekode via https://l.postnord.com/Yj7b49l0G2E_ eller PostNord app."
            ),
            "receivedDateTime": "2026-05-10T20:51:00+02:00",
        },
    ]
    refresh_calls = []

    def fake_fetch_tracking(number, carrier="", postal_codes=None, timeout=None):
        refresh_calls.append((number, carrier))
        return TrackingLookupResult(
            carrier=carrier,
            tracking_number=number,
            status="fundet",
            last_event_text="Pakken er registreret",
            tracking_url=f"https://example.test/{number}",
            source=f"{carrier}-test",
        )

    def fake_fetch_postnord_link(url):
        assert url == "https://l.postnord.com/Yj7b49l0G2E_"
        return """
        Vis denne QR-kode, naar du skal hente din pakke
        08 24 13 14
        Pakkenummer
        00073215400568030824
        Leveret
        """

    monkeypatch.setattr(
        app_module.mail_services,
        "iter_recent_messages",
        lambda _days, progress_callback=None: iter(messages),
    )
    monkeypatch.setattr(storage, "fetch_tracking", fake_fetch_tracking)
    monkeypatch.setattr(app_module, "_fetch_postnord_pickup_link_text", fake_fetch_postnord_link)

    summary = app_module._scan_messages(14, lambda **_updates: None)
    updated = storage.get_shipment(existing["id"])

    assert summary["found"] == 1
    assert summary["new_shipments"] == 0
    assert updated["pickup_location"] == "7-Eleven, Odensevej 102, 4700 Naestved"
    assert updated["pickup_code"] == "08241314"
    assert updated["label"] == "Proshop a/s"
    assert updated["status"] == "Klar til afhentning"
    assert updated["last_event_text"] == "PostNord-pakken er klar til afhentning"
    assert refresh_calls == [("00073215400568030824", "PostNord")]


def test_scan_updates_existing_dao_pickup_location_and_code_from_mail(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()
    _created, existing = storage.add_shipment(
        "00057151273676436276",
        label="bent Felvoe",
        source="mail",
        carrier="DAO",
    )

    messages = [
        {
            "subject": "Din pakke er klar til afhentning",
            "from": {"emailAddress": {"address": "noreply@notificationmail.com", "name": "Levering"}},
            "bodyPreview": (
                "Hej Christian\n\n"
                "Din pakke 00057151273676436276 fra bent Felvø er klar til afhentning hos:\n\n"
                "7-Eleven Uno-X Odensevej\n"
                "Odensevej 102\n"
                "4700 Næstved\n\n"
                "Åbningstider:\n"
                "Mandag: 06:00 - 22:00\n"
                "Tirsdag: 06:00 - 22:00\n\n"
                "Brug afhentningskode 53828 når du henter pakken.\n\n"
                "Pakken skal afhentes senest 12.06.2026."
            ),
            "receivedDateTime": "2026-06-06T10:30:00+02:00",
        },
    ]
    refresh_calls = []

    def fake_fetch_tracking(number, carrier="", postal_codes=None, timeout=None):
        refresh_calls.append((number, carrier))
        return TrackingLookupResult(
            carrier=carrier,
            tracking_number=number,
            status="klar til afhentning",
            last_event_text="Pakken er klar til afhentning",
            pickup_location="Hentested fra DAO tracking skal ignoreres",
            tracking_url=f"https://example.test/{number}",
            source=f"{carrier}-test",
        )

    monkeypatch.setattr(
        app_module.mail_services,
        "iter_recent_messages",
        lambda _days, progress_callback=None: iter(messages),
    )
    monkeypatch.setattr(storage, "fetch_tracking", fake_fetch_tracking)

    summary = app_module._scan_messages(14, lambda **_updates: None)
    updated = storage.get_shipment(existing["id"])

    assert summary["found"] == 1
    assert summary["new_shipments"] == 0
    assert updated["tracking_number"] == "00057151273676436276"
    assert updated["pickup_location"] == "7-Eleven Uno-X Odensevej Odensevej 102 4700 Næstved"
    assert updated["pickup_code"] == "53828"
    assert updated["label"] == "bent Felvø"
    assert refresh_calls == [("00057151273676436276", "DAO")]


def test_scan_marks_dao_udleveret_mail_as_picked_up(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()
    _created, existing = storage.add_shipment(
        "00057151273676436276",
        label="bent Felvoe",
        source="mail",
        carrier="DAO",
        pickup_location="7-Eleven Uno-X Odensevej Odensevej 102 4700 Næstved",
        pickup_code="53828",
    )
    with storage.get_connection() as db:
        db.execute(
            """
            UPDATE shipments
            SET status = 'klar til afhentning',
                last_event_at = '2026-06-06T08:00:00+02:00',
                last_event_text = 'Pakken er klar til afhentning',
                events_json = ?
            WHERE id = ?
            """,
            (
                json.dumps(
                    [
                        {
                            "description": "Pakken er klar til afhentning",
                            "status": "",
                            "date_iso": "2026-06-06T08:00:00+02:00",
                            "display_date": "",
                            "display_time": "",
                            "location": "",
                        }
                    ]
                ),
                existing["id"],
            ),
        )

    messages = [
        {
            "subject": "Din pakke er udleveret",
            "from": {"emailAddress": {"address": "noreply@dao.as", "name": "dao"}},
            "bodyPreview": (
                "Hej Christian\n\n"
                "Pakken er udleveret.\n"
                "Pakkenr.: 00057151273676436276"
            ),
            "receivedDateTime": "2999-06-06T10:30:00+02:00",
        },
    ]
    refresh_calls = []

    def fake_fetch_tracking(number, carrier="", postal_codes=None, timeout=None):
        refresh_calls.append((number, carrier))
        return TrackingLookupResult(
            carrier=carrier,
            tracking_number=number,
            status="klar til afhentning",
            last_event_text="Pakken er klar til afhentning",
            events=[
                {
                    "description": "Pakken er klar til afhentning",
                    "status": "",
                    "date_iso": "2026-06-06T08:00:00+02:00",
                    "display_date": "",
                    "display_time": "",
                    "location": "",
                }
            ],
            pickup_location="Hentested fra DAO tracking skal ignoreres",
            tracking_url=f"https://example.test/{number}",
            source=f"{carrier}-test",
        )

    monkeypatch.setattr(
        app_module.mail_services,
        "iter_recent_messages",
        lambda _days, progress_callback=None: iter(messages),
    )
    monkeypatch.setattr(storage, "fetch_tracking", fake_fetch_tracking)

    summary = app_module._scan_messages(14, lambda **_updates: None)
    updated = storage.get_shipment(existing["id"])

    assert summary["found"] == 1
    assert summary["new_shipments"] == 0
    assert updated["status"] == "Afhentet"
    assert updated["last_event_text"] == "Pakken er udleveret"
    assert updated["pickup_location"] == "7-Eleven Uno-X Odensevej Odensevej 102 4700 Næstved"
    assert updated["pickup_code"] == "53828"
    assert updated["events"][0]["description"] == "Pakken er udleveret"
    assert updated["events"][1]["description"] == "Pakken er klar til afhentning"
    assert refresh_calls == [("00057151273676436276", "DAO")]


def test_scan_keeps_dao_delivered_status_when_older_pickup_mail_adds_code(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()

    messages = [
        {
            "subject": "Din pakke er udleveret",
            "from": {"emailAddress": {"address": "noreply@dao.as", "name": "dao"}},
            "bodyPreview": (
                "Hej Christian\n\n"
                "Pakken er udleveret.\n"
                "Pakkenr.: 00057151273676436276"
            ),
            "receivedDateTime": "2026-06-08T10:30:00+02:00",
        },
        {
            "subject": "Din pakke er klar til afhentning",
            "from": {"emailAddress": {"address": "noreply@dao.as", "name": "dao"}},
            "bodyPreview": (
                "Hej Christian\n\n"
                "Din pakke 00057151273676436276 fra bent Felvø er klar til afhentning hos:\n\n"
                "7-Eleven Uno-X Odensevej\n"
                "Odensevej 102\n"
                "4700 Næstved\n\n"
                "Åbningstider:\n"
                "Mandag: 06:00 - 22:00\n\n"
                "Brug afhentningskode 53828 når du henter pakken."
            ),
            "receivedDateTime": "2026-06-06T10:30:00+02:00",
        },
    ]
    refresh_calls = []

    def fake_fetch_tracking(number, carrier="", postal_codes=None, timeout=None):
        refresh_calls.append((number, carrier))
        return TrackingLookupResult(
            carrier=carrier,
            tracking_number=number,
            status="klar til afhentning",
            last_event_text="Pakken er klar til afhentning",
            tracking_url=f"https://example.test/{number}",
            source=f"{carrier}-test",
        )

    monkeypatch.setattr(
        app_module.mail_services,
        "iter_recent_messages",
        lambda _days, progress_callback=None: iter(messages),
    )
    monkeypatch.setattr(storage, "fetch_tracking", fake_fetch_tracking)

    summary = app_module._scan_messages(7, lambda **_updates: None)
    updated = storage.list_shipments(include_archived=True)[0]

    assert summary["found"] == 1
    assert updated["status"] == "Afhentet"
    assert updated["last_event_text"] == "Pakken er udleveret"
    assert updated["pickup_location"] == "7-Eleven Uno-X Odensevej Odensevej 102 4700 Næstved"
    assert updated["pickup_code"] == "53828"
    assert updated["label"] == "bent Felvø"
    assert refresh_calls == [("00057151273676436276", "DAO")]


def test_scan_updates_existing_bring_pickup_location_and_code(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()
    _created, existing = storage.add_shipment(
        "370722152477343049",
        label="MyTrendyPhone",
        source="mail",
        carrier="Bring",
    )

    messages = [
        {
            "subject": "Nu kan du hente din pakke fra MyTrendyPhone",
            "from": {"emailAddress": {"address": "noreply@bring.com", "name": "Bring"}},
            "bodyPreview": (
                "Hej Christian Glerup,\n\n"
                "Din pakke 370722152477343049 fra MyTrendyPhone kan nu hentes.\n\n"
                "Hentested: UnoX/7-Eleven Odensevej Odensevej 102, 4700 Naestved DK.\n"
                "Hentekode: KX83.\n"
                "Sporingsnummer: 370722152477343049\n"
                "Medbring ID naar du afhenter pakken."
            ),
            "receivedDateTime": "2026-06-06T10:30:00+02:00",
        },
    ]

    def fake_fetch_tracking(number, carrier="", postal_codes=None, timeout=None):
        return TrackingLookupResult(
            carrier=carrier,
            tracking_number=number,
            status="leveret",
            last_event_text="Pakken er leveret.",
            tracking_url=f"https://example.test/{number}",
            source=f"{carrier}-test",
        )

    monkeypatch.setattr(
        app_module.mail_services,
        "iter_recent_messages",
        lambda _days, progress_callback=None: iter(messages),
    )
    monkeypatch.setattr(storage, "fetch_tracking", fake_fetch_tracking)

    summary = app_module._scan_messages(14, lambda **_updates: None)
    updated = storage.get_shipment(existing["id"])

    assert summary["found"] == 1
    assert summary["new_shipments"] == 0
    assert updated["pickup_location"] == "UnoX/7-Eleven Odensevej Odensevej 102, 4700 Naestved DK"
    assert updated["pickup_code"] == "KX83"
