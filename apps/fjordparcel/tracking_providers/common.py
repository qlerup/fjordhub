from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TrackingLookupResult:
    carrier: str
    tracking_number: str
    status: str = ""
    status_code: str = ""
    summary: str = ""
    last_event_at: str = ""
    last_event_text: str = ""
    last_event_location: str = ""
    events: list[dict[str, Any]] = field(default_factory=list)
    pickup_location: str = ""
    tracking_url: str = ""
    reference_number: str = ""
    source: str = ""
    error: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "carrier": self.carrier,
            "tracking_number": self.tracking_number,
            "status": self.status,
            "status_code": self.status_code,
            "summary": self.summary,
            "last_event_at": self.last_event_at,
            "last_event_text": self.last_event_text,
            "last_event_location": self.last_event_location,
            "events": self.events,
            "pickup_location": self.pickup_location,
            "tracking_url": self.tracking_url,
            "reference_number": self.reference_number,
            "source": self.source,
            "error": self.error,
        }


def normalize_tracking_number(value: Any) -> str:
    raw = re.sub(r"[\s-]+", "", str(value or "").strip()).upper()
    if not raw:
        raise ValueError("Tracking number is required.")
    if len(raw) > 50:
        raise ValueError("Tracking number is too long.")
    return raw
