from tracking_providers import postnord


def test_build_request_payload_uses_number_and_sign():
    payload = postnord._build_request_payload("00073215400595127740", "abc-sign")

    assert payload["data"][0]["num"] == "00073215400595127740"
    assert payload["data"][0]["fc"] == 0
    assert payload["data"][0]["sc"] == 0
    assert payload["sign"] == "abc-sign"


def test_parse_tracking_response_maps_events_and_danish_text():
    payload = {
        "meta": {"code": 200, "message": "Ok"},
        "shipments": [
            {
                "code": 200,
                "number": "00073215400568030824",
                "shipment": {
                    "latest_status": {"status": "AvailableForPickup"},
                    "misc_info": {"service_type": "PostNord Service Point"},
                    "tracking": {
                        "providers": [
                            {
                                "provider": {"name": "PostNord Sweden"},
                                "events": [
                                    {
                                        "time_iso": "2026-06-08T11:56:40+02:00",
                                        "description": "E-mail notification has been sent to the recipient",
                                        "location": "Denmark",
                                        "sub_status": "AvailableForPickup_Other",
                                    },
                                    {
                                        "time_iso": "2026-06-06T09:22:10+02:00",
                                        "description": "The shipment item is under transportation",
                                        "location": "Denmark",
                                        "sub_status": "InTransit_Departure",
                                    },
                                ],
                            }
                        ]
                    },
                },
            }
        ],
    }

    result = postnord._parse_tracking_response(payload, "00073215400568030824")

    assert result.carrier == "PostNord"
    assert result.source == "17track-restapi"
    assert result.summary == "PostNord Service Point"
    assert result.status == "e-mail-meddelelse er sendt til modtageren"
    assert result.status_code == "AvailableForPickup"
    assert result.last_event_location == "Danmark"
    assert result.last_event_at == "2026-06-08T11:56:40+02:00"
    assert len(result.events) == 2
    assert result.events[0]["description"] == "e-mail-meddelelse er sendt til modtageren"
    assert result.events[1]["description"] == "forsendelsesvaren er under transport"


def test_parse_tracking_response_handles_sign_error():
    result = postnord._parse_tracking_response({"meta": {"code": -10, "message": ""}, "shipments": []}, "00073215400568030824")

    assert result.status == "Ikke fundet"
    assert "Forny sign" in result.error or "fornyelse" in result.error
