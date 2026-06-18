from __future__ import annotations

from typing import Any, Optional

from .common import TrackingLookupResult
from .bring import fetch_bring_tracking
from .dao import fetch_dao_tracking
from .fedex import fetch_fedex_tracking
from .gls import fetch_gls_tracking
from .postnord import fetch_postnord_tracking


def fetch_tracking(
    tracking_number: Any,
    carrier: str = "",
    postal_codes: Optional[list[str]] = None,
    timeout: Optional[int] = None,
) -> TrackingLookupResult:
    carrier_name = str(carrier or "").strip().lower()

    if carrier_name == "gls":
        return fetch_gls_tracking(tracking_number, postal_codes=postal_codes, timeout=timeout)
    if carrier_name == "dao":
        return fetch_dao_tracking(tracking_number, postal_codes=postal_codes, timeout=timeout)
    if carrier_name == "bring":
        return fetch_bring_tracking(tracking_number, postal_codes=postal_codes, timeout=timeout)
    if carrier_name == "postnord":
        return fetch_postnord_tracking(tracking_number, postal_codes=postal_codes, timeout=timeout)
    if carrier_name == "fedex":
        return fetch_fedex_tracking(tracking_number, postal_codes=postal_codes, timeout=timeout)

    raise ValueError(f"Tracking provider is not implemented yet for carrier: {carrier or 'Unknown'}")


__all__ = [
    "TrackingLookupResult",
    "fetch_tracking",
    "fetch_bring_tracking",
    "fetch_dao_tracking",
    "fetch_fedex_tracking",
    "fetch_gls_tracking",
    "fetch_postnord_tracking",
]
