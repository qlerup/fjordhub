"""Validate browser redirect targets supplied by unauthenticated callers."""
from urllib.parse import unquote, urlsplit


def safe_login_next(value: str | None) -> str:
    """Keep only unambiguous root-relative paths, otherwise use the dashboard.

    Inspect decoded forms as well as the actual value: proxies and browsers
    differ in how they normalize escaped separators. Return the original safe
    value so that query strings and escaped path components keep their meaning.
    """
    if not isinstance(value, str) or not value:
        return "/"
    candidate = value
    for _ in range(8):
        if (not candidate.startswith("/") or candidate.startswith("//")
                or "\\" in candidate
                or any(ord(char) < 32 or ord(char) == 127 for char in candidate)):
            return "/"
        try:
            parsed = urlsplit(candidate)
            if parsed.scheme or parsed.netloc:
                return "/"
            decoded = unquote(candidate, errors="strict")
        except (ValueError, UnicodeError):
            return "/"
        if decoded == candidate:
            return value
        candidate = decoded
    # Excessively nested encoding is ambiguous and never necessary here.
    return "/"
