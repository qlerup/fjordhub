from __future__ import annotations

import html
import json
import os
import re
from datetime import datetime
from typing import Any, Optional
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from .common import TrackingLookupResult, normalize_tracking_number

BRING_TRACKING_URL = "https://bring.dk/t/{tracking_number}"
DEFAULT_TIMEOUT_SECONDS = int(str(os.getenv("BRING_TRACKING_TIMEOUT", "20") or "20"))


def _text(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s+([.,:;!?])", r"\1", text)


def _tracking_url(number: str) -> str:
    return BRING_TRACKING_URL.format(tracking_number=urllib_parse.quote(number, safe=""))


def _request_text(url: str, timeout: int) -> str:
    req = urllib_request.Request(
        url,
        method="GET",
        headers={
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "da-DK,da;q=0.9,en;q=0.7",
            "User-Agent": "fjordparcel-tracking/1.0",
        },
    )
    with urllib_request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _decode_react_payload(values: list[Any], root_index: int = 0) -> Any:
    def decode_ref(reference: int) -> Any:
        if reference < 0:
            return None
        return decode(values[reference])

    def decode(value: Any) -> Any:
        if isinstance(value, dict):
            out = {}
            for key, item in value.items():
                decoded_key = decode_ref(int(key[1:])) if key.startswith("_") and key[1:].isdigit() else key
                out[decoded_key] = decode_ref(item) if isinstance(item, int) else decode(item)
            return out
        if isinstance(value, list):
            if len(value) == 2 and value[0] == "P" and isinstance(value[1], int):
                return None
            return [decode_ref(item) if isinstance(item, int) else decode(item) for item in value]
        return value

    return decode(values[root_index])


def _loader_data_from_html(page: str) -> dict[str, Any]:
    for match in re.finditer(r"streamController\.enqueue\((\"(?:\\.|[^\"\\])*\")\)", page):
        try:
            encoded = json.loads(match.group(1)).strip()
        except json.JSONDecodeError:
            continue
        if not encoded.startswith("["):
            continue
        try:
            values = json.loads(encoded)
        except json.JSONDecodeError:
            continue
        if isinstance(values, list) and values:
            decoded = _decode_react_payload(values)
            if isinstance(decoded, dict) and decoded.get("loaderData"):
                return decoded["loaderData"]
    raise RuntimeError("Bring returned a tracking page without parcel data.")


def _parse_datetime(value: Any) -> tuple[str, str, str]:
    raw = _text(value)
    if not raw:
        return "", "", ""
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return raw, raw[:10], raw[11:19]
    return parsed.isoformat(timespec="seconds"), parsed.strftime("%d-%m-%Y"), parsed.strftime("%H:%M:%S")


def _parse_event(event: dict[str, Any]) -> dict[str, Any]:
    date_iso, display_date, display_time = _parse_datetime(event.get("dateIso"))
    location_parts = [_text(event.get("postalCode")), _text(event.get("city"))]
    return {
        "description": _text(event.get("deliveryLocationText") or event.get("description")),
        "status": _text(event.get("status")),
        "date_iso": date_iso,
        "display_date": display_date,
        "display_time": display_time,
        "location": " ".join(part for part in location_parts if part),
    }


def _find_consignment(loader_data: dict[str, Any]) -> dict[str, Any]:
    route = loader_data.get("routes/$sporing.$trackingNumber") or loader_data.get("routes/$trackingNumber") or {}
    if not isinstance(route, dict):
        return {}
    consignment = route.get("consignment")
    return consignment if isinstance(consignment, dict) else {}


def fetch_bring_tracking(
    tracking_number: Any,
    postal_codes: Optional[list[str]] = None,
    timeout: Optional[int] = None,
) -> TrackingLookupResult:
    number = normalize_tracking_number(tracking_number)
    timeout_seconds = int(timeout or DEFAULT_TIMEOUT_SECONDS or 20)

    try:
        page = _request_text(_tracking_url(number), timeout_seconds)
        loader_data = _loader_data_from_html(page)
    except urllib_error.HTTPError as exc:
        return TrackingLookupResult(
            carrier="Bring",
            tracking_number=number,
            status="Ikke fundet" if int(exc.code or 0) == 404 else "Fejl ved opdatering",
            tracking_url=_tracking_url(number),
            source="bring-tracking-page",
            error=f"Bring svarede med HTTP {int(exc.code or 0)}",
        )
    except Exception as exc:
        return TrackingLookupResult(
            carrier="Bring",
            tracking_number=number,
            status="Fejl ved opdatering",
            tracking_url=_tracking_url(number),
            source="bring-tracking-page",
            error=str(exc)[:260],
        )

    consignment = _find_consignment(loader_data)
    package_set = consignment.get("packageSet") if isinstance(consignment.get("packageSet"), list) else []
    package = next(
        (
            item
            for item in package_set
            if isinstance(item, dict) and normalize_tracking_number(item.get("packageNumber")) == number
        ),
        package_set[0] if package_set and isinstance(package_set[0], dict) else {},
    )
    if not package:
        return TrackingLookupResult(
            carrier="Bring",
            tracking_number=number,
            status="Ikke fundet",
            tracking_url=_tracking_url(number),
            source="bring-tracking-page",
            error="Bring fandt ingen forsendelse paa dette nummer.",
        )

    raw_events = package.get("eventSet") if isinstance(package.get("eventSet"), list) else []
    events = [_parse_event(event) for event in raw_events if isinstance(event, dict)]
    latest = events[0] if events else {}
    sender = _text(package.get("senderName") or consignment.get("senderName"))
    last_event_text = latest.get("description") or _text(package.get("statusDescription"))
    current_status = _text(package.get("currentStatus"))

    return TrackingLookupResult(
        carrier="Bring",
        tracking_number=number,
        status=last_event_text or current_status or "Fundet hos Bring",
        status_code=current_status or latest.get("status") or "",
        summary=sender,
        last_event_at=latest.get("date_iso") or "",
        last_event_text=last_event_text,
        last_event_location=latest.get("location") or "",
        events=events,
        tracking_url=_tracking_url(number),
        reference_number=_text(consignment.get("senderReference")),
        source="bring-tracking-page",
        error="",
    )
