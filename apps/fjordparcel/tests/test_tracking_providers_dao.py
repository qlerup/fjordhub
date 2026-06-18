from tracking_providers import dao


def test_fetch_dao_tracking_reads_events(monkeypatch):
    payload = {
        "found": True,
        "parcel": {
            "barcode": "00057151273676436276",
            "events": [
                {
                    "date": {"day": "5. jun.", "year": "2026", "time": "07:55:52"},
                    "description": "Paa vej til daoSHOP",
                    "raw": {
                        "tidspunkt": "2026-06-05 07:55:52",
                        "haendelse": "23",
                        "beskrivelse": "Paa vej til daoSHOP",
                        "sted": "",
                    },
                },
                {
                    "date": {"day": "4. jun.", "year": "2026", "time": "13:22:10"},
                    "description": "Paa vej til terminal",
                    "raw": {
                        "tidspunkt": "2026-06-04 13:22:10",
                        "haendelse": "26",
                        "beskrivelse": "Paa vej til terminal",
                        "sted": "",
                    },
                },
            ],
            "latest_event": {
                "description": "Paa vej til daoSHOP",
                "raw": {"tidspunkt": "2026-06-05 07:55:52", "haendelse": "23"},
            },
            "pickup": {
                "name": "7-Eleven Uno-X Odensevej",
                "address": "Odensevej 102",
                "postnr": "4700",
                "city": "Næstved",
            },
        },
    }

    monkeypatch.setattr(dao, "_tracking_api_settings", lambda _timeout: ("https://dao.example/track", "nonce"))
    monkeypatch.setattr(dao, "_request_json", lambda _url, _timeout, headers=None: payload)

    result = dao.fetch_dao_tracking("00057151273676436276")

    assert result.carrier == "DAO"
    assert result.status == "Paa vej til daoSHOP"
    assert result.status_code == "23"
    assert result.summary == "7-Eleven Uno-X Odensevej, Næstved"
    assert result.pickup_location == ""
    assert result.last_event_at == "2026-06-05T07:55:52"
    assert len(result.events) == 2
    assert result.events[0]["display_date"] == "5. jun. 2026"


def test_fetch_dao_tracking_returns_not_found(monkeypatch):
    monkeypatch.setattr(dao, "_tracking_api_settings", lambda _timeout: ("https://dao.example/track", "nonce"))
    monkeypatch.setattr(dao, "_request_json", lambda _url, _timeout, headers=None: {"found": False})

    result = dao.fetch_dao_tracking("00057151273676436276")

    assert result.status == "Ikke fundet"
    assert "DAO fandt ingen" in result.error
