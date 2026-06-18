from tracking import (
    build_tracking_url,
    classify_shipment_status,
    detect_carrier,
    extract_bring_mail_label,
    extract_dao_mail_event_text,
    extract_dao_mail_label,
    extract_gls_mail_label,
    extract_gls_mail_tracking_numbers,
    extract_gls_reference_numbers,
    extract_postnord_mail_label,
    extract_postnord_pickup_links,
    extract_postnord_pickup_page_details,
    extract_postnord_pincode,
    extract_pickup_code,
    extract_pickup_location,
    extract_tracking_numbers,
    is_gls_ready_mail,
    is_postnord_ready_mail,
    normalize_tracking_number,
)


def test_normalizes_common_spacing():
    assert normalize_tracking_number("1Z 999 AA1 012-345-6784") == "1Z999AA10123456784"


def test_extracts_ups_without_context():
    results = extract_tracking_numbers("Your code is 1Z999AA10123456784")

    assert results[0]["tracking_number"] == "1Z999AA10123456784"
    assert results[0]["carrier"] == "UPS"


def test_numeric_tracking_requires_delivery_context():
    assert extract_tracking_numbers("Invoice 123456789012 is ready") == []

    results = extract_tracking_numbers("Your DHL shipment tracking number is 1234567890")
    assert results[0]["tracking_number"] == "1234567890"
    assert results[0]["carrier"] == "DHL"


def test_detects_postnord_from_context():
    assert detect_carrier("1234567890123", "Din PostNord pakke er paa vej") == "PostNord"


def test_classifies_dao_udleveret_as_delivered():
    assert classify_shipment_status(carrier="DAO", last_event_text="Pakken er udleveret") == "delivered"


def test_extracts_dao_udleveret_event_from_mail_text():
    text = "dao har nyt om din pakke. Pakken er udleveret. Pakkenr.: 00057151273676436276"

    assert extract_dao_mail_event_text(text) == "Pakken er udleveret"


def test_generic_udleveret_is_not_delivered_for_bring_yet():
    assert classify_shipment_status(carrier="Bring", last_event_text="Pakken er udleveret") == "in_transit"


def test_extracts_dao_supported_formats_from_dao_mail():
    text = """
    dao giver dig besked om din pakke.
    Pakkenummer: 00057151270507652003
    E-label: 123456789
    """

    results = extract_tracking_numbers(text)

    assert [result["tracking_number"] for result in results] == [
        "00057151270507652003",
        "123456789",
    ]
    assert {result["carrier"] for result in results} == {"DAO"}


def test_extracts_distinctive_dao_number_without_carrier_context():
    results = extract_tracking_numbers(
        "Din pakke 00057151273676436276 fra bent Felvoe er klar til afhentning hos 7-Eleven."
    )

    assert results[0]["tracking_number"] == "00057151273676436276"
    assert results[0]["carrier"] == "DAO"


def test_extracts_postnord_s10_from_postnord_mail():
    results = extract_tracking_numbers("PostNord forsendelses-ID: RR123456789DK")

    assert results[0]["tracking_number"] == "RR123456789DK"
    assert results[0]["carrier"] == "PostNord"
    assert "postnord.dk" in results[0]["tracking_url"]


def test_extracts_postnord_number_and_label_from_received_mail():
    text = (
        "Hej, der er nyt om din PostNord-pakke.\n"
        "Vi har modtaget din pakke 00073215400568030824 fra Proshop a/s som har sendt den "
        "med udlevering til dig via en PostNord Pakkeshop eller en PostNord Pakkeboks."
    )

    results = extract_tracking_numbers(text)

    assert results[0]["tracking_number"] == "00073215400568030824"
    assert results[0]["carrier"] == "PostNord"
    assert extract_postnord_mail_label(text) == "Proshop a/s"


def test_extracts_postnord_ready_mail_details():
    text = (
        "Din PostNord-pakke er klar til afhentning\n\n"
        "Din pakke fra Proshop a/s er klar til afhentning i Pakkeshop "
        "7-Eleven , Odensevej 102, 4700 Naestved. Hent senest den 18.5. "
        "Vis din hentekode via https://l.postnord.com/Yj7b49l0G2E_ eller PostNord app."
    )

    assert extract_postnord_mail_label(text) == "Proshop a/s"
    assert extract_pickup_location(text, "PostNord") == "7-Eleven, Odensevej 102, 4700 Naestved"
    assert extract_postnord_pickup_links(text) == ["https://l.postnord.com/Yj7b49l0G2E_"]
    assert is_postnord_ready_mail(text) is True


def test_extracts_postnord_pickup_page_number():
    text = """
    Vis denne QR-kode, naar du skal hente din pakke
    08 24 13 14
    Pakkenummer
    00073215400568030824
    Leveret
    """

    assert extract_postnord_pickup_page_details(text) == {
        "tracking_number": "00073215400568030824",
        "pickup_code": "08241314",
    }


def test_extracts_postnord_pincode_from_mail():
    text = """
    Din pakke 00073215400568030824 fra Proshop a/s er klar til at blive hentet i
    Pakketaarnet ved Pakkeshop Bilka, Naestved Storcenter 1, 4700 Naestved.
    Naar du henter pakken skal du bruge pinkoden 84258172.
    """

    assert extract_postnord_pincode(text) == "84258172"


def test_extract_postnord_pincode_returns_none_when_absent():
    text = "Din pakke fra Proshop a/s er klar til afhentning i Pakkeshop 7-Eleven."

    assert extract_postnord_pincode(text) is None


def test_extracts_bring_numeric_formats_from_bring_mail():
    text = """
    Bring shipment number: 370733344455566677
    Bring parcel number: 70123456789012345
    """

    results = extract_tracking_numbers(text)

    assert [result["tracking_number"] for result in results] == [
        "370733344455566677",
        "70123456789012345",
    ]
    assert {result["carrier"] for result in results} == {"Bring"}


def test_extracts_gls_parcel_number_from_gls_mail():
    results = extract_tracking_numbers("GLS pakkenummer: 12345678901 er klar til afhentning")

    assert results[0]["tracking_number"] == "12345678901"
    assert results[0]["carrier"] == "GLS"
    assert "gls-group.com" in results[0]["tracking_url"]


def test_extracts_gls_merchant_label_from_shopping_mail():
    text = "Tak fordi du handlede hos ELEXTRA.dk. Din pakke er afsendt med GLS."

    assert extract_gls_mail_label(text) == "ELEXTRA.dk"


def test_extracts_gls_merchant_label_from_pakkeshop_mail():
    text = "Nu kan du godt begynde at glæde dig. Din pakke fra Magnetz og Magnordic er blevet leveret af GLS."

    assert extract_gls_mail_label(text) == "Magnetz og Magnordic"


def test_extracts_gls_merchant_label_from_html_mail():
    text = "Tak fordi du handlede hos <strong>ELEXTRA.dk</strong>. Din pakke er afsendt med GLS."

    assert extract_gls_mail_label(text) == "ELEXTRA.dk"


def test_extracts_gls_reference_from_tracking_link():
    text = """
    Tak fordi du handlede hos ELEXTRA.dk. Din pakke er afsendt med GLS.
    <a href="https://gls-group.com/DK/da/find-pakke?txtRefNo=YOXVB8CE&amp;foo=1">GLS Track & Trace</a>
    """

    assert extract_gls_reference_numbers(text) == ["YOXVB8CE"]


def test_detects_gls_ready_mail_by_required_phrases():
    text = (
        "Nu kan du godt begynde at glaede dig. Din pakke fra Magnetz og Magnordic "
        "er blevet leveret af din lokale GLS-chauffoer."
    )

    assert is_gls_ready_mail(text) is True


def test_extracts_gls_package_number_from_ready_mail():
    text = (
        "Nu kan du godt begynde at glaede dig. Din pakke fra Magnetz og Magnordic "
        "er blevet leveret af din lokale GLS-chauffoer. "
        "Dit pakkenummer er 027624557628."
    )

    assert extract_gls_mail_tracking_numbers(text) == ["027624557628"]


def test_extracts_full_gls_package_number_when_ready_mail_uses_spaces():
    text = (
        "Nu kan du godt begynde at glaede dig. Din pakke fra ELEXTRA.dk "
        "er blevet leveret af din lokale GLS-chauffoer. "
        "GLS pakkenummer: 0756 2423 8061 er klar til afhentning"
    )

    assert extract_gls_mail_tracking_numbers(text) == ["075624238061"]


def test_does_not_extract_gls_ready_number_without_required_delivery_phrase():
    text = "GLS: Dit pakkenummer er 027624557628 og pakken er klar til afhentning."

    assert extract_gls_mail_tracking_numbers(text) == []


def test_extracts_dao_sender_label_from_mail():
    text = """
    Hej Christian Glerup

    bent Foelvg har netop indleveret en pakke som nu er paa vej til dig.
    Pakkenr.: 00057151273676436276
    """

    assert extract_dao_mail_label(text) == "bent Foelvg"


def test_extracts_dao_sender_label_without_zero_width_spaces():
    text = "bent Felv\u00f8\u200b\u200b\u200b har netop indleveret en pakke som nu er paa vej til dig."

    assert extract_dao_mail_label(text) == "bent Felv\u00f8"


def test_extracts_danish_letters_from_mail_text():
    dao_text = "Søren Æblegård har netop indleveret en pakke som nu er på vej til dig. Pakkenr.: 00057151273676436276"
    postnord_text = "Din pakke fra Ærø Købmand er klar til afhentning i Pakkeshop 7-Eleven, Åvej 12, 4700 Næstved. Hent senest den 18.5."

    assert extract_dao_mail_label(dao_text) == "Søren Æblegård"
    assert extract_postnord_mail_label(postnord_text) == "Ærø Købmand"
    assert extract_pickup_location(postnord_text, "PostNord") == "7-Eleven, Åvej 12, 4700 Næstved"


def test_extracts_dao_sender_label_from_ready_mail():
    text = "Din pakke 00057151273676436276 fra bent Felvoe er klar til afhentning hos 7-Eleven."

    assert extract_dao_mail_label(text) == "bent Felvoe"


def test_extracts_pickup_code_from_dao_ready_mail():
    text = """
    Din pakke 00057151273676436276 fra bent Felvø er klar til afhentning hos:

    7-Eleven Uno-X Odensevej
    Odensevej 102
    4700 Næstved

    Åbningstider:
    Mandag: 06:00 - 22:00

    Brug afhentningskode 53828 når du henter pakken.
    """

    assert extract_pickup_code(text, "DAO") == "53828"


def test_extracts_bring_pickup_location():
    text = """
    Din pakke 370722152477343049 fra MyTrendyPhone kan nu hentes.
    Hentested: UnoX/7-Eleven Odensevej Odensevej 102, 4700 Naestved DK.
    Hentekode: KX83.
    Sporingsnummer: 370722152477343049
    """

    assert extract_pickup_location(text, "Bring") == "UnoX/7-Eleven Odensevej Odensevej 102, 4700 Naestved DK"


def test_extracts_dao_pickup_location():
    text = """
    Din pakke 00057151273676436276 fra bent Felvø er klar til afhentning hos:

    7-Eleven Uno-X Odensevej
    Odensevej 102
    4700 Næstved

    Åbningstider:
    Mandag: 06:00 - 22:00

    Brug afhentningskode 53828 når du henter pakken.
    """

    assert extract_pickup_location(text, "DAO") == "7-Eleven Uno-X Odensevej Odensevej 102 4700 Næstved"


def test_extracts_postnord_pakkeshop_location():
    text = "Din pakke fra Proshop a/s er klar til afhentning i Pakkeshop 7-Eleven, Odensevej 102, 4700 Naestved. Hent senest den 18.5."

    assert extract_pickup_location(text, "PostNord") == "7-Eleven, Odensevej 102, 4700 Naestved"


def test_extracts_postnord_pakketarnet_location():
    text = (
        "Din pakke 00073215400568030824 fra Proshop a/s er klar til at blive hentet i "
        "Pakketaarnet ved Pakkeshop Bilka, Naestved Storcenter 1, 4700 Naestved. "
        "Taarnet er udenfor til hoejre for indgangen."
    )

    assert extract_pickup_location(text, "PostNord") == "Pakketaarnet ved Pakkeshop Bilka, Naestved Storcenter 1, 4700 Naestved"


def test_extracts_gls_pickup_code():
    text = "GLS: Din pakke 075624238061 er klar. Når du henter din pakke, skal du oplyse hentekode 844."

    assert extract_pickup_code(text, "GLS") == "844"


def test_extracts_gls_pickup_location():
    text = """
    Den venter på dig i PakkeShoppen hos:

    7-Eleven Odensevej
    Odensevej 102
    4700 Naestved

    Dit pakkenummer er 027624557628.
    Naar du henter din pakke, skal du ogsaa oplyse hentekode 090.
    """

    assert extract_pickup_location(text, "GLS") == "7-Eleven Odensevej Odensevej 102 4700 Naestved"


def test_extracts_bring_sender_label_from_mail():
    text = "Din pakke fra MyTrendyPhone er snart hos os. Vi leverer den. https://bring.dk/t/370722152477343049"

    assert extract_bring_mail_label(text) == "MyTrendyPhone"


def test_extracts_bring_sender_label_from_ready_mail():
    text = "Din pakke 370722152477343049 fra MyTrendyPhone kan nu hentes."

    assert extract_bring_mail_label(text) == "MyTrendyPhone"


def test_removes_partial_gls_matches_from_same_mail():
    text = """
    GLS
    Du kan nu hente pakke 075624238061
    Link text: 07562423
    Pakkenummer: 075624238061
    """

    results = extract_tracking_numbers(text)

    assert [result["tracking_number"] for result in results] == ["075624238061"]


def test_collapses_gls_danish_package_aliases_from_same_mail():
    text = """
    GLS forsendelsesinformation
    Dansk pakkenummer 7562423806
    Dansk pakkenummer 07562423806
    Dansk pakkenummer 075624238061
    """

    results = extract_tracking_numbers(text)

    assert [result["tracking_number"] for result in results] == ["075624238061"]


def test_does_not_extract_short_numbers_without_carrier_context():
    assert extract_tracking_numbers("Order 123456789 was paid") == []


def test_builds_dao_tracking_url():
    assert build_tracking_url("00057151270507652003", "DAO") == (
        "https://dao.as/find-din-pakke/#q=00057151270507652003"
    )
