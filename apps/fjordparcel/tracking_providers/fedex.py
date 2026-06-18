from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Optional
from urllib import error as urllib_error
from urllib import request as urllib_request

from .common import TrackingLookupResult, normalize_tracking_number

FEDEX_TRACKING_URL = "https://www.fedex.com/fedextrack/?trknbr={tracking_number}"
TRACK17_API_BASE = "https://api.17track.net/track/v2.2"
DEFAULT_TIMEOUT_SECONDS = int(str(os.getenv("FEDEX_TRACKING_TIMEOUT", "20") or "20"))


def _tracking_url(number: str) -> str:
    return FEDEX_TRACKING_URL.format(tracking_number=number)


def _get_api_key() -> str:
    try:
        from app_config import load_track17_settings
        return load_track17_settings().get("api_key", "")
    except Exception:
        return ""


def _api_request(endpoint: str, payload: list[Any], api_key: str, timeout: int) -> dict[str, Any]:
    url = f"{TRACK17_API_BASE}/{endpoint}"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib_request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "17token": api_key,
            "Content-Type": "application/json",
        },
    )
    with urllib_request.urlopen(req, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise RuntimeError("17TRACK API returnerede et uventet svarformat.")
    return result


def _text(value: Any) -> str:
    import html
    import re
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s+([.,:;!?])", r"\1", text)


def _parse_datetime(value: Any) -> tuple[str, str, str]:
    raw = _text(value)
    if not raw:
        return "", "", ""
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed.isoformat(timespec="seconds"), parsed.strftime("%d-%m-%Y"), parsed.strftime("%H:%M")
    except ValueError:
        return raw, raw[:10], ""


def _parse_event(event: dict[str, Any]) -> dict[str, Any]:
    date_iso, display_date, display_time = _parse_datetime(event.get("time_iso") or "")
    return {
        "description": _text(event.get("description") or ""),
        "status": _text(event.get("sub_status") or event.get("stage") or ""),
        "date_iso": date_iso,
        "display_date": display_date,
        "display_time": display_time,
        "location": _text(event.get("location") or ""),
    }


def _parse_response(data: dict[str, Any], number: str) -> TrackingLookupResult:
    accepted = (data.get("data") or {}).get("accepted") or []
    entry = next((item for item in accepted if isinstance(item, dict)), None)

    if not entry:
        return TrackingLookupResult(
            carrier="FedEx",
            tracking_number=number,
            status="Ikke fundet",
            tracking_url=_tracking_url(number),
            source="17track-api",
            error="17TRACK fandt ingen forsendelse på dette nummer.",
        )

    track_info = entry.get("track_info") if isinstance(entry.get("track_info"), dict) else {}
    latest_status = track_info.get("latest_status") if isinstance(track_info.get("latest_status"), dict) else {}
    latest_event_raw = track_info.get("latest_event") if isinstance(track_info.get("latest_event"), dict) else {}
    tracking = track_info.get("tracking") if isinstance(track_info.get("tracking"), dict) else {}
    providers = tracking.get("providers") if isinstance(tracking.get("providers"), list) else []
    provider = providers[0] if providers and isinstance(providers[0], dict) else {}
    raw_events = provider.get("events") if isinstance(provider.get("events"), list) else []

    events = [_parse_event(item) for item in raw_events if isinstance(item, dict)]
    events_desc = sorted(events, key=lambda item: item.get("date_iso") or "", reverse=True)
    if not events_desc and latest_event_raw:
        events_desc = [_parse_event(latest_event_raw)]

    latest = events_desc[0] if events_desc else {}
    status_code = _text(latest_status.get("status") or latest_status.get("sub_status") or "")
    last_text = (
        latest.get("description")
        or _text(latest_status.get("status") or "")
        or "Fundet hos 17TRACK"
    )

    misc = track_info.get("misc_info") if isinstance(track_info.get("misc_info"), dict) else {}
    provider_info = provider.get("provider") if isinstance(provider.get("provider"), dict) else {}
    service_type = _text(misc.get("service_type") or provider.get("service_type") or "")
    provider_name = _text(provider_info.get("name") or "")

    return TrackingLookupResult(
        carrier="FedEx",
        tracking_number=number,
        status=last_text,
        status_code=status_code,
        summary=service_type or provider_name,
        last_event_at=latest.get("date_iso") or "",
        last_event_text=last_text,
        last_event_location=latest.get("location") or "",
        events=events_desc,
        tracking_url=_tracking_url(number),
        source="17track-api",
        error="",
    )


def fetch_fedex_tracking(
    tracking_number: Any,
    postal_codes: Optional[list[str]] = None,
    timeout: Optional[int] = None,
) -> TrackingLookupResult:
    number = normalize_tracking_number(tracking_number)
    timeout_seconds = int(timeout or DEFAULT_TIMEOUT_SECONDS or 20)
    api_key = _get_api_key()

    if not api_key:
        return TrackingLookupResult(
            carrier="FedEx",
            tracking_number=number,
            status="Mangler API-nøgle",
            tracking_url=_tracking_url(number),
            source="17track-api",
            error="17TRACK API-nøgle mangler. Gå til Indstillinger → Fragtfirmaer → PostNord.",
        )

    try:
        _api_request(
            "register",
            [{"number": number, "auto_detection": True, "lang": "da"}],
            api_key,
            timeout_seconds,
        )
    except Exception:
        pass

    try:
        result = _api_request("gettrackinfo", [{"number": number}], api_key, timeout_seconds)
        return _parse_response(result, number)
    except urllib_error.HTTPError as exc:
        return TrackingLookupResult(
            carrier="FedEx",
            tracking_number=number,
            status="Fejl ved opdatering",
            tracking_url=_tracking_url(number),
            source="17track-api",
            error=f"17TRACK API svarede med HTTP {int(exc.code or 0)}",
        )
    except Exception as exc:
        return TrackingLookupResult(
            carrier="FedEx",
            tracking_number=number,
            status="Fejl ved opdatering",
            tracking_url=_tracking_url(number),
            source="17track-api",
            error=str(exc)[:260],
        )
