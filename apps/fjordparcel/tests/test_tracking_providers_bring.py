import json

from tracking_providers import bring


def _bring_loader_html():
    values = [
        {"_1": 2},
        "loaderData",
        {"_3": 4},
        "routes/$sporing.$trackingNumber",
        {"_5": 6, "_7": 8, "_9": 10},
        "_type",
        "SINGLE_CONSIGNMENT",
        "trackingNumber",
        "370722152477343049",
        "consignment",
        {"_11": 12, "_13": 14, "_15": 16},
        "consignmentId",
        "70722152601526613",
        "senderName",
        "MyTrendyPhone.dk",
        "packageSet",
        [17],
        {"_18": 19, "_20": 21, "_22": 23, "_24": 25},
        "packageNumber",
        "370722152477343049",
        "statusDescription",
        "Pakken kan afhentes paa <a href='#'>UnoX/7-Eleven Odensevej</a>.",
        "eventSet",
        [29, 35],
        "status",
        "description",
        "dateIso",
        "postalCode",
        "city",
        {
            "_24": 30,
            "_25": 31,
            "_26": 32,
            "_27": 33,
            "_28": 34,
        },
        "READY_FOR_PICKUP",
        "Pakken er ankommet til <a href='#'>UnoX/7-Eleven Odensevej</a>.",
        "2026-06-04T11:56:40+02:00",
        "",
        "Naestved",
        {
            "_24": 36,
            "_25": 37,
            "_26": 38,
            "_27": 39,
            "_28": 40,
        },
        "IN_TRANSIT",
        "Pakken er registreret hos os.",
        "2026-06-03T22:20:12+02:00",
        "2670",
        "Greve",
    ]
    encoded = json.dumps(values)
    return f"<script>window.__reactRouterContext.streamController.enqueue({json.dumps(encoded)});</script>"


def test_fetch_bring_tracking_reads_loader_events(monkeypatch):
    monkeypatch.setattr(bring, "_request_text", lambda _url, _timeout: _bring_loader_html())

    result = bring.fetch_bring_tracking("370722152477343049")

    assert result.carrier == "Bring"
    assert result.summary == "MyTrendyPhone.dk"
    assert result.status == "Pakken er ankommet til UnoX/7-Eleven Odensevej."
    assert result.status_code == "READY_FOR_PICKUP"
    assert result.last_event_text == "Pakken er ankommet til UnoX/7-Eleven Odensevej."
    assert result.last_event_at == "2026-06-04T11:56:40+02:00"
    assert result.events[0]["location"] == "Naestved"
    assert result.events[1]["location"] == "2670 Greve"
