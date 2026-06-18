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

DAO_TRACKING_PAGE_URL = "https://dao.as/find-din-pakke/"
DAO_TRACKING_API_URL = "https://dao.as/wp-json/dao-wp/v1/track-parcel"
DEFAULT_TIMEOUT_SECONDS = int(str(os.getenv("DAO_TRACKING_TIMEOUT", "20") or "20"))


def _text(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s+([.,:;!?])", r"\1", text)


def _tracking_url(number: str) -> str:
    return f"{DAO_TRACKING_PAGE_URL}#q={urllib_parse.quote(number, safe='')}"


def _request_text(url: str, timeout: int, headers: Optional[dict[str, str]] = None) -> str:
    req = urllib_request.Request(
        url,
        method="GET",
        headers={
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "User-Agent": "fjordparcel-tracking/1.0",
            **(headers or {}),
        },
    )
    with urllib_request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _tracking_api_settings(timeout: int) -> tuple[str, str]:
    page = _request_text(DAO_TRACKING_PAGE_URL, timeout)
    endpoint_match = re.search(r'"endpoint"\s*:\s*"([^"]+)"', page)
    nonce_match = re.search(r'"nonce"\s*:\s*"([^"]+)"', page)
    endpoint = endpoint_match.group(1).replace("\\/", "/") if endpoint_match else DAO_TRACKING_API_URL
    nonce = nonce_match.group(1) if nonce_match else ""
    return endpoint, nonce


def _request_json(url: str, timeout: int, headers: Optional[dict[str, str]] = None) -> dict[str, Any]:
    try:
        raw = _request_text(url, timeout, headers=headers)
    except urllib_error.HTTPError as exc:
        try:
            raw_error = exc.read().decode("utf-8", errors="replace")
            payload = json.loads(raw_error or "{}")
            message = _text(payload.get("message")) if isinstance(payload, dict) else ""
        except Exception:
            message = ""
        raise RuntimeError(message or f"DAO API responded with HTTP {int(exc.code or 0)}") from exc

    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError("DAO returned an invalid tracking response.") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("DAO returned an unexpected tracking response.")
    return payload


def _parse_datetime(value: Any) -> tuple[str, str, str]:
    raw = _text(value)
    if not raw:
        return "", "", ""
    try:
        parsed = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return raw.replace(" ", "T", 1), raw[:10], raw[11:19]
    return parsed.isoformat(timespec="seconds"), parsed.strftime("%d-%m-%Y"), parsed.strftime("%H:%M:%S")


def _event_datetime(event: dict[str, Any]) -> tuple[str, str, str]:
    raw = event.get("raw") if isinstance(event.get("raw"), dict) else {}
    date_iso, display_date, display_time = _parse_datetime(raw.get("tidspunkt"))
    date_info = event.get("date") if isinstance(event.get("date"), dict) else {}
    if date_info:
        day = _text(date_info.get("day"))
        year = _text(date_info.get("year"))
        time = _text(date_info.get("time"))
        display_date = f"{day} {year}".strip() or display_date
        display_time = time or display_time
    return date_iso, display_date, display_time


def _parse_event(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("raw") if isinstance(event.get("raw"), dict) else {}
    date_iso, display_date, display_time = _event_datetime(event)
    return {
        "description": _text(event.get("description") or raw.get("beskrivelse")),
        "status": _text(raw.get("haendelse")),
        "date_iso": date_iso,
        "display_date": display_date,
        "display_time": display_time,
        "location": _text(raw.get("sted")),
    }


def fetch_dao_tracking(
    tracking_number: Any,
    postal_codes: Optional[list[str]] = None,
    timeout: Optional[int] = None,
) -> TrackingLookupResult:
    number = normalize_tracking_number(tracking_number)
    timeout_seconds = int(timeout or DEFAULT_TIMEOUT_SECONDS or 20)

    try:
        endpoint, nonce = _tracking_api_settings(timeout_seconds)
        query = urllib_parse.urlencode({"barcode": number, "lang": "DA"})
        headers = {
            "Accept": "application/json",
            "Referer": DAO_TRACKING_PAGE_URL,
        }
        if nonce:
            headers["X-WP-Nonce"] = nonce
        payload = _request_json(f"{endpoint}?{query}", timeout_seconds, headers=headers)
    except Exception as exc:
        return TrackingLookupResult(
            carrier="DAO",
            tracking_number=number,
            status="Fejl ved opdatering",
            tracking_url=_tracking_url(number),
            source="dao-track-parcel",
            error=str(exc)[:260],
        )

    if not payload.get("found") or not isinstance(payload.get("parcel"), dict):
        return TrackingLookupResult(
            carrier="DAO",
            tracking_number=number,
            status="Ikke fundet",
            tracking_url=_tracking_url(number),
            source="dao-track-parcel",
            error=_text(payload.get("message")) or "DAO fandt ingen forsendelse paa dette nummer.",
        )

    parcel = payload["parcel"]
    raw_events = parcel.get("events") if isinstance(parcel.get("events"), list) else []
    events = [_parse_event(event) for event in raw_events if isinstance(event, dict)]
    latest = events[0] if events else _parse_event(parcel.get("latest_event") or {})
    pickup = parcel.get("pickup") if isinstance(parcel.get("pickup"), dict) else {}
    summary = _text(pickup.get("name"))
    if pickup.get("city"):
        summary = f"{summary}, {_text(pickup.get('city'))}".strip(", ")

    return TrackingLookupResult(
        carrier="DAO",
        tracking_number=number,
        status=latest.get("description") or "Fundet hos DAO",
        status_code=latest.get("status") or "",
        summary=summary,
        last_event_at=latest.get("date_iso") or "",
        last_event_text=latest.get("description") or "",
        last_event_location=latest.get("location") or "",
        events=events,
        tracking_url=_tracking_url(number),
        source="dao-track-parcel",
        error="",
    )
