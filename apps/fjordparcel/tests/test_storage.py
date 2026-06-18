import storage
from tracking_providers import TrackingLookupResult


def test_update_shipment_label(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()
    _created, shipment = storage.add_shipment("00057151273676436276", source="manual", carrier="DAO")

    storage.update_shipment_label(shipment["id"], "  Work keyboard  ")
    renamed = storage.list_shipments()[0]

    assert renamed["label"] == "Work keyboard"

    storage.update_shipment_label(shipment["id"], "")
    cleared = storage.list_shipments()[0]

    assert cleared["label"] is None


def test_user_text_fields_keep_danish_characters(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()

    _created, shipment = storage.add_shipment(
        "370722152477343049",
        label="  Æblekasse fra Øko Årstid  ",
        source="mail",
        carrier="Bring",
        mail_subject="Din pakke fra Ærø Købmand er på vej",
        mail_from="Søren Ågård <shop@example.com>",
        pickup_location="Nærboks ved Åvej, 4700 Næstved",
    )

    assert shipment["label"] == "Æblekasse fra Øko Årstid"
    assert shipment["mail_subject"] == "Din pakke fra Ærø Købmand er på vej"
    assert shipment["mail_from"] == "Søren Ågård <shop@example.com>"
    assert shipment["pickup_location"] == "Nærboks ved Åvej, 4700 Næstved"

    storage.update_shipment_label(shipment["id"], "  Åben æske fra Østerbro  ")
    assert storage.get_shipment(shipment["id"])["label"] == "Åben æske fra Østerbro"


def test_users_keep_danish_name_and_username(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()

    storage.create_user("  Åse Østergaard  ", "SØREN", "hash", role="admin")

    user = storage.get_user_by_username("søren")
    assert user["name"] == "Åse Østergaard"
    assert user["username"] == "søren"
    assert storage.get_user_by_username("SØREN")["id"] == user["id"]


def test_mail_received_at_is_saved_with_shipment(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()

    storage.add_shipment(
        "370722152477343049",
        source="mail",
        carrier="Bring",
        mail_received_at="2026-06-01T14:30:00+00:00",
    )

    shipment = storage.list_shipments()[0]

    assert shipment["mail_received_at"] == "2026-06-01T14:30:00+00:00"


def test_shipment_includes_last_four_tracking_digits(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()

    storage.add_shipment("RR123456789DK", source="manual", carrier="PostNord")

    shipment = storage.list_shipments()[0]

    assert shipment["tracking_last_four_digits"] == "6789"


def test_existing_shipment_can_receive_pickup_code_from_mail(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()
    _created, shipment = storage.add_shipment("00057151273676436276", source="manual", carrier="DAO")

    created, updated = storage.add_shipment(
        "00057151273676436276",
        source="mail",
        carrier="DAO",
        pickup_code="53828",
        mail_received_at="2026-06-06T10:30:00+02:00",
    )

    assert created is False
    assert updated["id"] == shipment["id"]
    assert updated["pickup_code"] == "53828"
    assert storage.list_shipments()[0]["pickup_code"] == "53828"


def test_existing_shipment_can_receive_pickup_location_from_mail(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()
    _created, shipment = storage.add_shipment("370722152477343049", source="manual", carrier="Bring")

    created, updated = storage.add_shipment(
        "370722152477343049",
        source="mail",
        carrier="Bring",
        pickup_location="UnoX/7-Eleven Odensevej Odensevej 102, 4700 Naestved DK",
        pickup_code="KX83",
        mail_received_at="2026-06-06T10:30:00+02:00",
    )

    assert created is False
    assert updated["id"] == shipment["id"]
    assert updated["pickup_location"] == "UnoX/7-Eleven Odensevej Odensevej 102, 4700 Naestved DK"
    assert updated["pickup_code"] == "KX83"


def test_gls_shipments_can_receive_pickup_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()

    _created, shipment = storage.add_shipment(
        "075624238061",
        source="mail",
        carrier="GLS",
        pickup_location="PakkeShoppen",
        pickup_code="844",
    )

    assert shipment["pickup_location"] == "PakkeShoppen"
    assert shipment["pickup_code"] == "844"

    _created_again, updated = storage.add_shipment(
        "075624238061",
        source="mail",
        carrier="GLS",
        pickup_location="Anden pakkeshop",
        pickup_code="090",
    )

    assert updated["pickup_location"] == "Anden pakkeshop"
    assert updated["pickup_code"] == "090"
    assert storage.list_shipments()[0]["pickup_location"] == "Anden pakkeshop"
    assert storage.list_shipments()[0]["pickup_code"] == "090"


def test_mail_status_can_mark_postnord_ready(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()

    _created, shipment = storage.add_shipment("00073215400568030824", source="mail", carrier="PostNord")

    updated = storage.update_shipment_mail_status(
        shipment["id"],
        "Klar til afhentning",
        "PostNord-pakken er klar til afhentning",
        "2026-05-10T20:51:00+02:00",
    )

    assert updated["status"] == "Klar til afhentning"
    assert updated["last_event_text"] == "PostNord-pakken er klar til afhentning"
    assert updated["last_event_at"] == "2026-05-10T20:51:00+02:00"


def test_init_db_keeps_existing_gls_pickup_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()
    _created, shipment = storage.add_shipment("075624238061", source="mail", carrier="GLS")

    with storage.get_connection() as db:
        db.execute(
            """
            UPDATE shipments
            SET pickup_location = 'PakkeShoppen',
                pickup_code = '844'
            WHERE id = ?
            """,
            (shipment["id"],),
        )

    storage.init_db()

    assert storage.get_shipment(shipment["id"])["pickup_location"] == "PakkeShoppen"
    assert storage.get_shipment(shipment["id"])["pickup_code"] == "844"


def test_shipments_can_be_archived_and_restored(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()
    _created, shipment = storage.add_shipment("370722152477343049", source="manual", carrier="Bring")

    archived = storage.set_shipment_archived(shipment["id"], True)

    assert archived["is_archived"] is True
    assert storage.list_shipments() == []
    assert storage.list_shipments(include_archived=True)[0]["tracking_number"] == "370722152477343049"
    assert storage.get_stats()["archived"] == 1

    restored = storage.set_shipment_archived(shipment["id"], False)

    assert restored["is_archived"] is False
    assert storage.list_shipments()[0]["tracking_number"] == "370722152477343049"


def test_delivered_archive_clock_starts_from_delivery_event_time(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()
    _created, shipment = storage.add_shipment("075624238061", source="manual", carrier="GLS")

    with storage.get_connection() as db:
        db.execute(
            """
            UPDATE shipments
            SET status = 'leveret',
                status_code = 'DELIVERED',
                last_event_at = '2026-06-05T09:00:00+00:00',
                last_event_text = 'Din pakke er udleveret i PakkeShoppen.'
            WHERE id = ?
            """,
            (shipment["id"],),
        )

    archived_count = storage.archive_due_delivered_shipments("2026-06-05T10:00:00+00:00")
    updated = storage.list_shipments()[0]

    assert archived_count == 0
    assert updated["delivered_at"] == "2026-06-05T09:00:00+00:00"
    assert updated["is_archived"] is False


def test_delivered_shipments_are_auto_archived_after_24_hours(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()
    _created, shipment = storage.add_shipment("075624238061", source="manual", carrier="GLS")

    with storage.get_connection() as db:
        db.execute(
            """
            UPDATE shipments
            SET status = 'leveret',
                status_code = 'DELIVERED',
                last_event_text = 'Din pakke er udleveret i PakkeShoppen.',
                delivered_at = '2026-06-05T10:00:00+00:00'
            WHERE id = ?
            """,
            (shipment["id"],),
        )

    assert storage.archive_due_delivered_shipments("2026-06-06T09:59:59+00:00") == 0
    assert storage.list_shipments()[0]["is_archived"] is False

    assert storage.archive_due_delivered_shipments("2026-06-06T10:00:00+00:00") == 1
    assert storage.list_shipments() == []

    archived = storage.list_shipments(include_archived=True)[0]
    assert archived["is_archived"] is True
    assert archived["archived_at"] == "2026-06-06T10:00:00+00:00"


def test_existing_delivered_shipments_with_old_event_are_archived(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()
    _created, shipment = storage.add_shipment("075624238061", source="manual", carrier="GLS")

    with storage.get_connection() as db:
        db.execute(
            """
            UPDATE shipments
            SET status = 'leveret',
                status_code = 'DELIVERED',
                last_event_at = '2026-06-05T09:00:00+00:00',
                last_event_text = 'Din pakke er udleveret i PakkeShoppen.'
            WHERE id = ?
            """,
            (shipment["id"],),
        )

    assert storage.archive_due_delivered_shipments("2026-06-06T09:00:00+00:00") == 1

    archived = storage.list_shipments(include_archived=True)[0]
    assert archived["delivered_at"] == "2026-06-05T09:00:00+00:00"
    assert archived["archived_at"] == "2026-06-06T09:00:00+00:00"


def test_gls_aliases_are_merged_into_best_tracking_number(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()

    created_short, short = storage.add_shipment(
        "7562423806",
        source="mail",
        carrier="GLS",
        mail_subject="Faktura: 650622",
        mail_from="mailservice@elextra.dk",
        mail_received_at="2026-05-28T11:01:06+02:00",
    )
    created_long, long = storage.add_shipment(
        "075624238061",
        source="mail",
        carrier="GLS",
        mail_subject="Du kan nu hente pakke 075624238061",
        mail_from="pakke-shop@pakkeshop.dk",
        mail_received_at="2026-05-29T08:55:41+00:00",
    )

    shipments = storage.list_shipments()

    assert created_short is True
    assert created_long is False
    assert short["id"] == long["id"]
    assert len(shipments) == 1
    assert shipments[0]["tracking_number"] == "075624238061"
    assert shipments[0]["mail_subject"] == "Du kan nu hente pakke 075624238061"
    assert shipments[0]["mail_received_at"] == "2026-05-29T08:55:41+00:00"


def test_gls_ready_mail_links_numeric_number_to_existing_reference_shipment(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()

    created_ref, reference = storage.add_shipment(
        "YMQHJ9AQ",
        label="Magnetz og Magnordic",
        source="mail",
        carrier="GLS",
        mail_subject="GLS pakke",
        mail_from="noreply@gls-denmark.com",
        mail_received_at="2026-05-28T17:26:20+02:00",
    )

    created_ready, updated = storage.add_shipment(
        "027624557628",
        label="Magnetz og Magnordic",
        source="mail",
        carrier="GLS",
        mail_subject="Din pakke er nu klar til afhentning",
        mail_from="pakke-shop@pakkeshop.dk",
        mail_received_at="2026-05-29T08:55:48+00:00",
        pickup_location="7-Eleven Odensevej Odensevej 102 4700 Naestved",
        pickup_code="090",
    )

    shipments = storage.list_shipments()

    assert created_ref is True
    assert created_ready is False
    assert updated["id"] == reference["id"]
    assert updated["tracking_number"] == "027624557628"
    assert updated["pickup_location"] == "7-Eleven Odensevej Odensevej 102 4700 Naestved"
    assert updated["pickup_code"] == "090"
    assert len(shipments) == 1


def test_gls_ready_mail_removes_archived_reference_duplicate_for_same_label(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()

    _created_ref, reference = storage.add_shipment(
        "YOXVB8CE",
        label="ELEXTRA.dk",
        source="mail",
        carrier="GLS",
        mail_subject="GLS pakke",
        mail_from="noreply@gls-denmark.com",
        mail_received_at="2026-05-28T19:19:00+02:00",
    )
    storage.set_shipment_archived(reference["id"], True)

    with storage.get_connection() as db:
        db.execute(
            """
            INSERT INTO shipments (
                tracking_number,
                label,
                label_source,
                carrier,
                status,
                source,
                tracking_url,
                mail_subject,
                mail_from,
                mail_received_at,
                created_at,
                updated_at,
                last_seen_at
            )
            VALUES (?, ?, 'mail', 'GLS', 'Saved', 'mail', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "075624238061",
                "ELEXTRA.dk",
                "https://gls-group.com/DK/da/find-pakke?match=075624238061",
                "Din pakke er nu klar til afhentning",
                "pakke-shop@pakkeshop.dk",
                "2026-05-29T08:55:41+00:00",
                "2026-06-03T20:00:00+00:00",
                "2026-06-03T20:00:00+00:00",
                "2026-06-03T20:00:00+00:00",
            ),
        )

    created, updated = storage.add_shipment(
        "075624238061",
        label="ELEXTRA.dk",
        source="mail",
        carrier="GLS",
        mail_subject="Din pakke er nu klar til afhentning",
        mail_from="pakke-shop@pakkeshop.dk",
        mail_received_at="2026-05-29T08:55:41+00:00",
        pickup_location="7-Eleven Odensevej Odensevej 102 4700 Naestved",
        pickup_code="844",
    )

    shipments = storage.list_shipments(include_archived=True)
    by_number = {item["tracking_number"]: item for item in shipments}

    assert created is False
    assert updated["tracking_number"] == "075624238061"
    assert "YOXVB8CE" not in by_number
    assert len(shipments) == 1


def test_init_db_dedupes_existing_gls_alias_rows(tmp_path, monkeypatch):
    db_path = tmp_path / "fjordparcel.db"
    monkeypatch.setattr(storage, "DATABASE_PATH", str(db_path))
    storage.init_db()

    storage.add_shipment(
        "7562423806",
        source="mail",
        carrier="GLS",
        mail_received_at="2026-05-28T11:01:06+02:00",
    )
    with storage.get_connection() as db:
        db.execute(
            """
            INSERT INTO shipments (
                tracking_number,
                carrier,
                source,
                tracking_url,
                mail_received_at,
                created_at,
                updated_at,
                last_seen_at
            )
            VALUES (?, 'GLS', 'mail', ?, ?, ?, ?, ?)
            """,
            (
                "075624238061",
                "https://gls-group.com/DK/da/find-pakke?match=075624238061",
                "2026-05-29T08:55:41+00:00",
                "2026-06-03T20:00:00+00:00",
                "2026-06-03T20:00:00+00:00",
                "2026-06-03T20:00:00+00:00",
            ),
        )

    storage.init_db()
    shipments = storage.list_shipments()

    assert len(shipments) == 1
    assert shipments[0]["tracking_number"] == "075624238061"
    assert shipments[0]["mail_received_at"] == "2026-05-29T08:55:41+00:00"


def test_carrier_postcodes_can_be_added_and_removed(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()

    storage.add_carrier_postcode("GLS", "9000")
    storage.add_carrier_postcode("GLS", " 9000 ")
    storage.add_carrier_postcode("GLS", "2100")

    assert storage.list_carrier_postcodes("GLS") == ["2100", "9000"]

    storage.remove_carrier_postcode("GLS", "2100")

    assert storage.list_carrier_postcodes("GLS") == ["9000"]


def test_mail_account_auto_scan_settings_are_per_account(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()

    assert storage.load_mail_account_settings("gmail", "user@gmail.com") == {
        "auto_scan_enabled": False,
        "auto_scan_minutes": 30,
    }

    storage.save_mail_account_settings(
        "gmail",
        "USER@gmail.com",
        {"auto_scan_enabled": "on", "auto_scan_minutes": "45"},
    )
    storage.save_mail_account_settings(
        "microsoft",
        "user@hotmail.com",
        {"auto_scan_minutes": "15"},
    )

    assert storage.load_mail_account_settings("gmail", "user@gmail.com") == {
        "auto_scan_enabled": True,
        "auto_scan_minutes": 45,
    }
    assert storage.load_mail_account_settings("microsoft", "user@hotmail.com") == {
        "auto_scan_enabled": False,
        "auto_scan_minutes": 15,
    }
    assert storage.list_enabled_mail_account_scans() == [
        {
            "provider": "gmail",
            "username": "user@gmail.com",
            "auto_scan_minutes": 45,
        }
    ]

    storage.delete_mail_account_settings("gmail", "user@gmail.com")

    assert storage.list_enabled_mail_account_scans() == []


def test_refresh_shipment_tracking_uses_saved_postcodes(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()
    storage.add_carrier_postcode("GLS", "9000")

    _created, shipment = storage.add_shipment("075624238061", source="manual", carrier="GLS")
    calls = {}

    def fake_fetch_tracking(number, carrier="", postal_codes=None, timeout=None):
        calls["number"] = number
        calls["carrier"] = carrier
        calls["postal_codes"] = postal_codes
        calls["timeout"] = timeout
        return TrackingLookupResult(
            carrier="GLS",
            tracking_number=number,
            status="leveret",
            status_code="DELIVERED",
            summary="Leveret med kvittering",
            last_event_at="2026-06-03T20:00:00",
            last_event_text="Pakken er leveret",
            events=[
                {
                    "description": "Pakken er leveret",
                    "status": "DELIVERED",
                    "date_iso": "2026-06-03T20:00:00",
                    "display_date": "03-06-2026",
                    "display_time": "20:00",
                    "location": "Aalborg",
                }
            ],
            tracking_url="https://gls-group.com/DK/da/find-pakke?match=075624238061",
            source="gls-rstt028",
        )

    monkeypatch.setattr(storage, "fetch_tracking", fake_fetch_tracking)

    updated = storage.refresh_shipment_tracking(shipment["id"])

    assert calls["number"] == "075624238061"
    assert calls["carrier"] == "GLS"
    assert calls["postal_codes"] == ["9000"]
    assert updated["status"] == "leveret"
    assert updated["status_code"] == "DELIVERED"
    assert updated["tracking_source"] == "gls-rstt028"
    assert updated["events"][0]["description"] == "Pakken er leveret"


def test_refresh_shipment_tracking_updates_tracking_number_from_provider(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()
    _created, shipment = storage.add_shipment("YMQHJ9AQ", source="mail", carrier="GLS")

    def fake_fetch_tracking(number, carrier="", postal_codes=None, timeout=None):
        return TrackingLookupResult(
            carrier="GLS",
            tracking_number="027624557628",
            status="leveret",
            status_code="DELIVERED",
            reference_number="YMQHJ9AQ",
            tracking_url="https://gls-group.com/DK/da/find-pakke?match=027624557628",
            source="gls-rstt028",
        )

    monkeypatch.setattr(storage, "fetch_tracking", fake_fetch_tracking)

    updated = storage.refresh_shipment_tracking(shipment["id"])

    assert updated["tracking_number"] == "027624557628"
    assert updated["tracking_reference"] == "YMQHJ9AQ"
    assert "match=027624557628" in updated["tracking_url"]


def test_refresh_shipment_tracking_keeps_gls_number_when_provider_returns_short_fragment(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()
    _created, shipment = storage.add_shipment("075624238061", source="mail", carrier="GLS")

    def fake_fetch_tracking(number, carrier="", postal_codes=None, timeout=None):
        return TrackingLookupResult(
            carrier="GLS",
            tracking_number="07562423",
            status="leveret",
            status_code="DELIVERED",
            tracking_url="https://gls-group.com/DK/da/find-pakke?match=07562423",
            source="gls-rstt028",
        )

    monkeypatch.setattr(storage, "fetch_tracking", fake_fetch_tracking)

    updated = storage.refresh_shipment_tracking(shipment["id"])

    assert updated["tracking_number"] == "075624238061"


def test_refresh_shipment_tracking_keeps_dao_pickup_location_from_mail(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "fjordparcel.db"))
    storage.init_db()
    _created, shipment = storage.add_shipment(
        "00057151273676436276",
        source="mail",
        carrier="DAO",
        pickup_location="7-Eleven Uno-X Odensevej Odensevej 102 4700 Næstved",
    )

    def fake_fetch_tracking(number, carrier="", postal_codes=None, timeout=None):
        return TrackingLookupResult(
            carrier="DAO",
            tracking_number=number,
            status="Klar til afhentning",
            last_event_text="Klar til afhentning",
            pickup_location="Hentested fra DAO tracking skal ignoreres",
            tracking_url=f"https://example.test/{number}",
            source="dao-test",
        )

    monkeypatch.setattr(storage, "fetch_tracking", fake_fetch_tracking)

    updated = storage.refresh_shipment_tracking(shipment["id"])

    assert updated["pickup_location"] == "7-Eleven Uno-X Odensevej Odensevej 102 4700 Næstved"
