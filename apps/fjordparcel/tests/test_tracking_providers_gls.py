from tracking_providers import gls


def test_fetch_gls_returns_overview_when_no_postcodes(monkeypatch):
    overview_payload = {
        "tuStatus": [
            {
                "postalCode": "",
                "owners": [],
                "arrivalTime": {"name": "Leveret den:", "value": "29-05-2026  klokken 08:03"},
                "tuNo": "YOXVB8CE",
                "progressBar": {
                    "statusInfo": "DELIVERED",
                    "statusText": "leveret",
                    "statusBar": [
                        {
                            "status": "PREADVICE",
                            "imageStatus": "COMPLETE",
                            "imageText": "Information",
                            "statusText": "",
                        },
                        {
                            "status": "DELIVERED",
                            "imageStatus": "CURRENT",
                            "imageText": "Leveret",
                            "statusText": "Pakken er leveret",
                        },
                    ],
                },
            }
        ]
    }

    monkeypatch.setattr(gls, "_request_json", lambda _url, _timeout: overview_payload)

    result = gls.fetch_gls_tracking("075624238061", postal_codes=[])

    assert result.carrier == "GLS"
    assert result.status == "leveret"
    assert result.status_code == "DELIVERED"
    assert result.source == "gls-rstt029"
    assert result.reference_number == "YOXVB8CE"
    assert len(result.events) == 2
    assert result.last_event_text


def test_fetch_gls_tries_saved_postcodes_for_detail_events(monkeypatch):
    overview_payload = {
        "tuStatus": [
            {
                "postalCode": "",
                "owners": [{"tuOwnerCode": "OWNER1"}],
                "arrivalTime": {"name": "Leveret den:", "value": "29-05-2026  klokken 08:03"},
                "tuNo": "YOXVB8CE",
                "progressBar": {
                    "statusInfo": "INTRANSIT",
                    "statusText": "under levering",
                    "statusBar": [
                        {
                            "status": "INDELIVERY",
                            "imageStatus": "CURRENT",
                            "imageText": "Under levering",
                            "statusText": "Pakken er paa vej",
                        }
                    ],
                },
            }
        ]
    }
    details_payload = {
        "history": [
            {
                "evtDscr": "Pakken er afleveret",
                "date": "2026-05-29",
                "time": "08:03:41",
                "address": {
                    "city": "Aalborg",
                    "countryName": "Danmark",
                    "countryCode": "DK",
                },
            }
        ]
    }

    detail_urls = []

    def fake_request(url, _timeout):
        if "rstt029" in url:
            return overview_payload
        detail_urls.append(url)
        if "postalCode=9000" in url:
            return details_payload
        raise RuntimeError("Forkert postnr. Format")

    monkeypatch.setattr(gls, "_request_json", fake_request)

    result = gls.fetch_gls_tracking("075624238061", postal_codes=["9999", "9000"])

    assert result.source == "gls-rstt028"
    assert result.reference_number == "YOXVB8CE"
    assert result.events[0]["description"] == "Pakken er afleveret"
    assert result.events[0]["location"] == "Aalborg, Danmark"
    assert any("postalCode=9999" in url for url in detail_urls)
    assert any("postalCode=9000" in url for url in detail_urls)


def test_fetch_gls_returns_error_result_on_overview_failure(monkeypatch):
    monkeypatch.setattr(gls, "_request_json", lambda _url, _timeout: (_ for _ in ()).throw(RuntimeError("Adgang naegtet")))

    result = gls.fetch_gls_tracking("075624238061")

    assert result.status == "Fejl ved opdatering"
    assert "Adgang" in result.error


def test_fetch_gls_prefers_package_number_from_detail_payload(monkeypatch):
    overview_payload = {
        "tuStatus": [
            {
                "tuNo": "YMQHJ9AQ",
                "owners": [{"tuOwnerCode": "OWNER1"}],
                "progressBar": {
                    "statusInfo": "DELIVERED",
                    "statusText": "leveret",
                    "statusBar": [],
                },
            }
        ]
    }
    details_payload = {
        "consignmentInformation": [
            {"label": "Ref.nr.", "value": "YMQHJ9AQ"},
            {"label": "Dansk pakkenummer", "value": "027624557628"},
        ],
        "history": [
            {
                "evtDscr": "Pakken er afleveret",
                "date": "2026-05-29",
                "time": "08:03:41",
            }
        ],
    }

    def fake_request(url, _timeout):
        if "rstt029" in url:
            return overview_payload
        return details_payload

    monkeypatch.setattr(gls, "_request_json", fake_request)

    result = gls.fetch_gls_tracking("YMQHJ9AQ", postal_codes=["4100"])

    assert result.reference_number == "YMQHJ9AQ"
    assert result.tracking_number == "027624557628"
    assert "match=027624557628" in result.tracking_url
    assert result.source == "gls-rstt028"
