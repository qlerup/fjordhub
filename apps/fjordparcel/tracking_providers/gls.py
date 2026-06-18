from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from .common import TrackingLookupResult, normalize_tracking_number

GLS_OVERVIEW_API_URL = "https://gls-group.com/app/service/open/rest/DK/da/rstt029"
GLS_DETAILS_API_URL = "https://gls-group.com/app/service/open/rest/DK/da/rstt028/{tracking_number}"
GLS_TRACKING_URL = "https://gls-group.com/DK/da/find-pakke?match={tracking_number}"
DEFAULT_TIMEOUT_SECONDS = int(str(os.getenv("GLS_TRACKING_TIMEOUT", "20") or "20"))
DEFAULT_CALLER = "witt002"


def _text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _tracking_url(number: str) -> str:
    return GLS_TRACKING_URL.format(tracking_number=urllib_parse.quote(number, safe=""))


def _normalize_postal_codes(postal_codes: Optional[list[str]]) -> list[str]:
    seen = set()
    out = []
    for code in postal_codes or []:
        normalized = re.sub(r"[^0-9A-Za-z]", "", str(code or "").upper())
        if len(normalized) < 3 or len(normalized) > 10:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


def _overview_url(number: str) -> str:
    millis = int(datetime.now(timezone.utc).timestamp() * 1000)
    query = urllib_parse.urlencode(
        {
            "match": number,
            "type": "",
            "caller": DEFAULT_CALLER,
            "millis": millis,
        }
    )
    return f"{GLS_OVERVIEW_API_URL}?{query}"


def _details_url(number: str, postal_code: str, tu_owner_code: str = "") -> str:
    millis = int(datetime.now(timezone.utc).timestamp() * 1000)
    query = urllib_parse.urlencode(
        {
            "caller": DEFAULT_CALLER,
            "millis": millis,
            "tuOwnerCode": tu_owner_code,
            "postalCode": postal_code,
        }
    )
    encoded = urllib_parse.quote(number, safe="")
    return GLS_DETAILS_API_URL.format(tracking_number=encoded) + "?" + query


def _http_error_message(exc: urllib_error.HTTPError) -> str:
    try:
        raw = exc.read().decode("utf-8", errors="replace")
    except Exception:
        return ""

    raw_text = _text(raw)
    try:
        payload = json.loads(raw)
    except Exception:
        return raw_text[:260]

    if not isinstance(payload, dict):
        return raw_text[:260]

    message = _text(payload.get("exceptionText"))
    if message:
        return message[:260]

    field_errors = payload.get("fieldExceptions")
    if isinstance(field_errors, list):
        for item in field_errors:
            if not isinstance(item, dict):
                continue
            field_message = _text(item.get("exceptionText"))
            if field_message:
                return field_message[:260]

    return raw_text[:260]


def _request_json(url: str, timeout: int) -> dict[str, Any]:
    req = urllib_request.Request(
        url,
        method="GET",
        headers={
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "fjordparcel-tracking/1.0",
            "Referer": "https://gls-group.com/DK/da/find-pakke",
        },
    )
    try:
        with urllib_request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib_error.HTTPError as exc:
        message = _http_error_message(exc)
        code = int(exc.code or 0)
        raise RuntimeError(message or f"GLS API responded with HTTP {code}") from exc

    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON from GLS tracking endpoint: {str(exc)[:180]}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("Unexpected payload from GLS tracking endpoint")

    if payload.get("exceptionText"):
        raise RuntimeError(_text(payload.get("exceptionText"))[:260])

    return payload


def _parse_danish_datetime(value: Any) -> tuple[str, str, str]:
    text = _text(value)
    if not text:
        return "", "", ""

    match = re.search(r"(\d{1,2})[-./](\d{1,2})[-./](\d{4})(?:\s+klokken\s+(\d{1,2}):(\d{2}))?", text)
    if not match:
        return "", text, ""

    day = int(match.group(1))
    month = int(match.group(2))
    year = int(match.group(3))
    hour = int(match.group(4) or 0)
    minute = int(match.group(5) or 0)

    try:
        parsed = datetime(year, month, day, hour, minute)
    except ValueError:
        return "", text, ""

    date_display = f"{day:02d}-{month:02d}-{year:04d}"
    time_display = f"{hour:02d}:{minute:02d}" if match.group(4) else ""
    iso = parsed.isoformat(timespec="seconds")
    return iso, date_display, time_display


def _extract_owner_codes(status_row: dict[str, Any]) -> list[str]:
    owner_codes = [""]
    owners = status_row.get("owners")
    if isinstance(owners, list):
        for owner in owners:
            if not isinstance(owner, dict):
                continue
            for key in ("tuOwnerCode", "ownerCode", "code", "owner"):
                value = _text(owner.get(key))
                if value and value not in owner_codes:
                    owner_codes.append(value)

    tu_no = _text(status_row.get("tuNo"))
    if tu_no and tu_no not in owner_codes:
        owner_codes.append(tu_no)

    return owner_codes


def _normalize_event_datetime(date_value: Any, time_value: Any = "") -> tuple[str, str, str]:
    date_text = _text(date_value)
    time_text = _text(time_value)

    # ISO-like value with full timestamp
    if date_text and ("T" in date_text or re.match(r"^\d{4}[-./]\d{2}[-./]\d{2}$", date_text)):
        try:
            # Support YYYY-MM-DD or full ISO forms
            if "T" not in date_text:
                date_text = f"{date_text}T00:00:00"
            parsed = datetime.fromisoformat(date_text.replace("Z", "+00:00"))
            return parsed.isoformat(), parsed.date().isoformat(), parsed.strftime("%H:%M")
        except ValueError:
            pass

    if date_text:
        # Handle GLS detail quirk where date can be YY-MM-DD (year-month-day)
        m_ymd2 = re.match(r"^(\d{2})[-./](\d{1,2})[-./](\d{1,2})$", date_text)
        if m_ymd2:
            y2 = int(m_ymd2.group(1))
            mm = int(m_ymd2.group(2))
            dd = int(m_ymd2.group(3))
            if 0 <= y2 <= 99 and 1 <= mm <= 12 and 1 <= dd <= 31:
                year = 2000 + y2
                hour = 0
                minute = 0
                if time_text:
                    time_match = re.search(r"(\d{1,2}):(\d{2})", time_text)
                    if time_match:
                        hour = int(time_match.group(1))
                        minute = int(time_match.group(2))
                try:
                    parsed = datetime(year, mm, dd, hour, minute)
                    display_time = time_text if time_text else ""
                    return parsed.isoformat(timespec="seconds"), f"{dd:02d}-{mm:02d}-{year:04d}", display_time
                except ValueError:
                    pass

        match = re.search(r"(\d{1,2})[-./](\d{1,2})[-./](\d{2,4})", date_text)
        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            year = int(match.group(3))
            year = year + 2000 if year < 100 else year

            hour = 0
            minute = 0
            if time_text:
                time_match = re.search(r"(\d{1,2}):(\d{2})", time_text)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))

            try:
                parsed = datetime(year, month, day, hour, minute)
                display_time = time_text if time_text else ""
                return parsed.isoformat(timespec="seconds"), f"{day:02d}-{month:02d}-{year:04d}", display_time
            except ValueError:
                pass

    return "", date_text, time_text


def _location_text(value: Any) -> str:
    if isinstance(value, dict):
        city = _text(value.get("city"))
        country = _text(value.get("countryName") or value.get("country") or value.get("countryCode"))
        if city and country:
            return f"{city}, {country}"
        return city or country
    return _text(value)


def _gls_number_preference(value: str) -> int:
    number = re.sub(r"[^0-9]", "", _text(value))
    if not (10 <= len(number) <= 14):
        return -1
    if len(number) == 12 and number.startswith("0"):
        return 300
    if len(number) == 11 and number.startswith("0"):
        return 250
    if len(number) == 10 and not number.startswith("0"):
        return 200
    return 100 + len(number)


def _extract_gls_tracking_number(payload: Any, fallback_number: str = "") -> str:
    candidates: list[tuple[int, str, int]] = []
    seen = set()
    fallback_digits = re.sub(r"[^0-9]", "", _text(fallback_number))
    sequence = 0

    value_fields = (
        "value",
        "number",
        "no",
        "code",
        "id",
        "text",
        "tuNo",
        "parcelNumber",
        "parcelNo",
        "packageNumber",
    )

    def add_candidate(raw: Any, context: str = "") -> None:
        nonlocal sequence
        context_text = _text(context).lower()
        for match in re.findall(r"\d{10,14}", _text(raw)):
            pref = _gls_number_preference(match)
            if pref < 0:
                continue
            score = pref
            if "dansk" in context_text:
                score += 35
            if "pakke" in context_text or "parcel" in context_text:
                score += 25
            if "track" in context_text:
                score += 10
            if "ref" in context_text or "kunde" in context_text:
                score -= 60
            if fallback_digits and match == fallback_digits:
                score -= 15

            key = (match, score)
            if key in seen:
                continue
            seen.add(key)
            candidates.append((score, match, sequence))
            sequence += 1

    def walk(value: Any, parent_key: str = "") -> None:
        if isinstance(value, list):
            for item in value:
                walk(item, parent_key)
            return

        if not isinstance(value, dict):
            add_candidate(value, parent_key)
            return

        label = _text(
            value.get("label")
            or value.get("name")
            or value.get("title")
            or value.get("description")
            or value.get("key")
            or parent_key
        )
        for field in value_fields:
            if field in value:
                add_candidate(value.get(field), label)

        for key, nested in value.items():
            walk(nested, f"{label} {key}")

    walk(payload)
    if not candidates:
        return _text(fallback_number)

    best = sorted(candidates, key=lambda item: (-item[0], item[2]))[0]
    return best[1]


def _apply_tracking_number(result: TrackingLookupResult, tracking_number: str) -> TrackingLookupResult:
    number = _text(tracking_number) or result.tracking_number
    if number == result.tracking_number:
        return result
    return TrackingLookupResult(
        carrier=result.carrier,
        tracking_number=number,
        status=result.status,
        status_code=result.status_code,
        summary=result.summary,
        last_event_at=result.last_event_at,
        last_event_text=result.last_event_text,
        last_event_location=result.last_event_location,
        events=result.events,
        tracking_url=_tracking_url(number),
        reference_number=result.reference_number,
        source=result.source,
        error=result.error,
    )


def _extract_detail_events(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("history"), list):
        history_events = []
        for item in payload.get("history"):
            if not isinstance(item, dict):
                continue

            description = _text(item.get("evtDscr") or item.get("eventDescription") or item.get("description"))
            date_iso, display_date, display_time = _normalize_event_datetime(item.get("date"), item.get("time"))
            location = _location_text(item.get("address"))
            status = _text(item.get("status") or item.get("eventCode") or item.get("code"))

            if not description:
                continue

            history_events.append(
                {
                    "description": description,
                    "status": status,
                    "date_iso": date_iso,
                    "display_date": display_date,
                    "display_time": display_time,
                    "location": location,
                }
            )

        if history_events:
            return history_events[:30]

    events = []
    seen = set()

    def push(event: dict[str, Any]) -> None:
        key = (
            str(event.get("description") or ""),
            str(event.get("date_iso") or event.get("display_date") or ""),
            str(event.get("location") or ""),
        )
        if key in seen:
            return
        seen.add(key)
        events.append(event)

    def walk(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                walk(item)
            return

        if not isinstance(value, dict):
            return

        description = _text(
            value.get("eventText")
            or value.get("evtDscr")
            or value.get("eventDescription")
            or value.get("description")
            or value.get("statusText")
            or value.get("text")
            or value.get("event")
            or value.get("title")
            or value.get("name")
        )
        status = _text(value.get("status") or value.get("eventCode") or value.get("code"))
        location = _location_text(
            value.get("location")
            or value.get("city")
            or value.get("depot")
            or value.get("parcelShop")
            or value.get("zipCity")
            or value.get("address")
        )
        date_iso, display_date, display_time = _normalize_event_datetime(
            value.get("dateTime")
            or value.get("datetime")
            or value.get("eventDateTime")
            or value.get("eventDate")
            or value.get("date"),
            value.get("eventTime") or value.get("time"),
        )

        if description and (status or location or date_iso or display_date):
            push(
                {
                    "description": description,
                    "status": status,
                    "date_iso": date_iso,
                    "display_date": display_date,
                    "display_time": display_time,
                    "location": location,
                }
            )

        for nested_value in value.values():
            walk(nested_value)

    walk(payload)
    return events[:30]


def _status_events(status_bar: list[dict[str, Any]], current_iso: str, current_date: str, current_time: str) -> list[dict[str, Any]]:
    events = []
    for entry in status_bar:
        if not isinstance(entry, dict):
            continue

        status = _text(entry.get("status"))
        image_status = _text(entry.get("imageStatus")).upper()
        title = _text(entry.get("imageText") or status)
        detail = _text(entry.get("statusText"))
        description = title
        if detail and detail.lower() != title.lower():
            description = f"{title}: {detail}"

        date_iso = current_iso if image_status == "CURRENT" else ""
        display_date = current_date if image_status == "CURRENT" else ""
        display_time = current_time if image_status == "CURRENT" else ""

        events.append(
            {
                "description": description,
                "status": status,
                "date_iso": date_iso,
                "display_date": display_date,
                "display_time": display_time,
                "location": "",
            }
        )

    return events


def _parse_overview_payload(payload: dict[str, Any], number: str) -> tuple[TrackingLookupResult, dict[str, Any]]:
    raw_status_rows = payload.get("tuStatus")
    if not isinstance(raw_status_rows, list) or not raw_status_rows:
        return (
            TrackingLookupResult(
                carrier="GLS",
                tracking_number=number,
                status="Ikke fundet",
                tracking_url=_tracking_url(number),
                source="gls-rstt029",
                error="GLS fandt ingen forsendelse paa dette nummer.",
            ),
            {},
        )

    status_row = raw_status_rows[0] if isinstance(raw_status_rows[0], dict) else {}
    progress_bar = status_row.get("progressBar") if isinstance(status_row.get("progressBar"), dict) else {}
    arrival_time = status_row.get("arrivalTime") if isinstance(status_row.get("arrivalTime"), dict) else {}

    arrival_raw = _text(arrival_time.get("value"))
    arrival_iso, arrival_date, arrival_clock = _parse_danish_datetime(arrival_raw)

    status_text = _text(progress_bar.get("statusText")) or _text(progress_bar.get("statusInfo")) or "Fundet hos GLS"
    status_code = _text(progress_bar.get("statusInfo"))
    status_bar = progress_bar.get("statusBar") if isinstance(progress_bar.get("statusBar"), list) else []

    events = _status_events(status_bar, arrival_iso, arrival_date, arrival_clock)
    if not events and arrival_raw:
        events = [
            {
                "description": _text(arrival_time.get("name")) or status_text,
                "status": status_code,
                "date_iso": arrival_iso,
                "display_date": arrival_date,
                "display_time": arrival_clock,
                "location": "",
            }
        ]

    current_event = next(
        (
            event
            for event in events
            if _text(event.get("date_iso")) or _text(event.get("display_date"))
        ),
        events[-1] if events else {},
    )

    summary_parts = []
    reference_number = _text(status_row.get("tuNo"))
    if arrival_raw:
        summary_parts.append(arrival_raw)
    if reference_number:
        summary_parts.append(f"TU: {reference_number}")

    return (
        TrackingLookupResult(
            carrier="GLS",
            tracking_number=number,
            status=status_text,
            status_code=status_code,
            summary=" | ".join(summary_parts),
            last_event_at=_text(current_event.get("date_iso")),
            last_event_text=_text(current_event.get("description")) or status_text,
            last_event_location=_text(current_event.get("location")),
            events=events,
            tracking_url=_tracking_url(number),
            reference_number=reference_number,
            source="gls-rstt029",
            error="",
        ),
        status_row,
    )


def _is_retryable_detail_error(message: str) -> bool:
    normalized = _text(message).lower()
    normalized = normalized.replace("ae", "a").replace("oe", "o").replace("aa", "a")
    return any(
        item in normalized
        for item in (
            "forkert postnr",
            "postnr",
            "owner code is not valid",
            "adgang",
            "unable to retrieve proper sub session",
        )
    )


def _apply_detail_events(result: TrackingLookupResult, events: list[dict[str, Any]]) -> TrackingLookupResult:
    if not events:
        return result

    latest = events[0]
    return TrackingLookupResult(
        carrier=result.carrier,
        tracking_number=result.tracking_number,
        status=result.status,
        status_code=result.status_code,
        summary=result.summary,
        last_event_at=_text(latest.get("date_iso")) or result.last_event_at,
        last_event_text=_text(latest.get("description")) or result.last_event_text,
        last_event_location=_text(latest.get("location")) or result.last_event_location,
        events=events,
        tracking_url=result.tracking_url,
        reference_number=result.reference_number,
        source="gls-rstt028",
        error=result.error,
    )


def fetch_gls_tracking(
    tracking_number: Any,
    postal_codes: Optional[list[str]] = None,
    timeout: Optional[int] = None,
) -> TrackingLookupResult:
    number = normalize_tracking_number(tracking_number)
    timeout_seconds = int(timeout or DEFAULT_TIMEOUT_SECONDS or 20)

    try:
        overview_payload = _request_json(_overview_url(number), timeout_seconds)
        overview_result, status_row = _parse_overview_payload(overview_payload, number)
        overview_number = _extract_gls_tracking_number(status_row, fallback_number=number)
        overview_result = _apply_tracking_number(overview_result, overview_number)
    except Exception as exc:
        return TrackingLookupResult(
            carrier="GLS",
            tracking_number=number,
            status="Fejl ved opdatering",
            tracking_url=_tracking_url(number),
            source="gls-rstt029",
            error=str(exc)[:260],
        )

    normalized_postals = _normalize_postal_codes(postal_codes)
    if not normalized_postals:
        return overview_result

    owner_codes = _extract_owner_codes(status_row)
    last_detail_error = ""

    for owner_code in owner_codes:
        for postal_code in normalized_postals:
            try:
                detail_payload = _request_json(
                    _details_url(number, postal_code, owner_code),
                    timeout_seconds,
                )
            except Exception as exc:
                message = str(exc)
                if _is_retryable_detail_error(message):
                    last_detail_error = message
                    continue
                last_detail_error = message
                continue

            detail_events = _extract_detail_events(detail_payload)
            detail_number = _extract_gls_tracking_number(detail_payload, fallback_number=overview_result.tracking_number)
            resolved_result = _apply_tracking_number(overview_result, detail_number)
            if detail_events:
                return _apply_detail_events(resolved_result, detail_events)
            if resolved_result.tracking_number != overview_result.tracking_number:
                return resolved_result

    if last_detail_error and not overview_result.error:
        overview_result.error = f"Detaljer kunne ikke hentes med gemte postnumre: {last_detail_error[:180]}"

    return overview_result
