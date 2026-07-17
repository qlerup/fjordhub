import json
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from .remote_registry import fetch_json

CACHE_FILE = "packages_catalog_cache.json"
REFRESH_INTERVAL_SEC = 3600  # 1 hour
_ID_RE = re.compile(r"^[a-z0-9-]+$")
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def _normalize(entry) -> dict | None:
    """Validate a catalog entry; return a cleaned copy or None if unusable."""
    if not isinstance(entry, dict):
        return None
    package_id = str(entry.get("id") or "")
    version = str(entry.get("version") or "").strip()
    download_url = str(entry.get("download_url") or "").strip()
    sha256 = str(entry.get("sha256") or "").strip().lower()
    if not _ID_RE.match(package_id) or not version:
        return None
    if not download_url.startswith("https://") or not _SHA_RE.match(sha256):
        return None
    return {
        "id": package_id,
        "name": str(entry.get("name") or package_id),
        "tagline": str(entry.get("tagline") or ""),
        "description": str(entry.get("description") or ""),
        "accent": str(entry.get("accent") or "#3b82f6"),
        "icon": str(entry.get("icon") or "note"),
        "version": version,
        "download_url": download_url,
        "sha256": sha256,
    }


class PackageCatalog:
    """
    Fetches the package catalog (packages_catalog.json in FjordHub's GitHub
    repo) at runtime, so packages can be updated without redeploying the hub.
    Caches the last good catalog locally and falls back to the built-in
    definitions when nothing has ever been fetched.

    Catalog format:
      { "schema": "fjordhub-packages/v1",
        "packages": [ { "id", "name", "tagline", "description", "accent",
                        "icon", "version", "download_url", "sha256" } ] }
    """

    def __init__(self, data_dir: Path, catalog_url: str, fallback: list[dict] | None = None):
        self.catalog_url = str(catalog_url or "").strip()
        self.fallback = [dict(p) for p in (fallback or [])]
        self._cache_file = data_dir / CACHE_FILE
        self._lock = threading.Lock()
        self._packages: list[dict] = []
        self._last_refresh: datetime | None = None
        self._last_error: str | None = None

        data_dir.mkdir(parents=True, exist_ok=True)
        self._load_cache()
        if self.catalog_url:
            self._start_background_refresh()

    # ── Public API ──────────────────────────────────────────────────────────

    def get_packages(self) -> list[dict]:
        with self._lock:
            packages = [dict(p) for p in self._packages]
        return packages or [dict(p) for p in self.fallback]

    def refresh_if_stale(self, max_age_sec: int = 60) -> None:
        """Refresh synchronously when the catalog is older than max_age_sec.
        Used on store page loads so pushed package updates show up right away."""
        if not self.catalog_url:
            return
        with self._lock:
            last = self._last_refresh
        if last and (datetime.now(timezone.utc) - last).total_seconds() < max_age_sec:
            return
        self.refresh()

    def refresh(self) -> tuple[bool, str]:
        if not self.catalog_url:
            return False, "PACKAGES_URL er ikke konfigureret."
        try:
            data = fetch_json(self.catalog_url)
        except (requests.RequestException, ValueError) as e:
            with self._lock:
                self._last_error = f"Kunne ikke hente pakkekatalog: {e}"
            return False, self._last_error

        packages = []
        for entry in data.get("packages", []) if isinstance(data, dict) else []:
            cleaned = _normalize(entry)
            if cleaned:
                packages.append(cleaned)

        with self._lock:
            self._packages = packages
            self._last_refresh = datetime.now(timezone.utc)
            self._last_error = None
        self._save_cache(packages)
        return True, f"Hentet {len(packages)} pakker"

    def get_status(self) -> dict:
        with self._lock:
            return {
                "last_refresh": self._last_refresh.isoformat() if self._last_refresh else None,
                "package_count": len(self._packages),
                "error": self._last_error,
                "catalog_url": self.catalog_url,
            }

    # ── Internal ─────────────────────────────────────────────────────────────

    def _load_cache(self):
        if not self._cache_file.exists():
            return
        try:
            data = json.loads(self._cache_file.read_text(encoding="utf-8"))
            packages = [p for p in (_normalize(e) for e in data.get("packages", [])) if p]
            with self._lock:
                self._packages = packages
                ts = data.get("last_refresh")
                self._last_refresh = datetime.fromisoformat(ts) if ts else None
        except Exception:
            pass

    def _save_cache(self, packages: list[dict]):
        payload = {
            "last_refresh": datetime.now(timezone.utc).isoformat(),
            "packages": packages,
        }
        try:
            self._cache_file.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except OSError:
            pass

    def _start_background_refresh(self):
        def _loop():
            time.sleep(10)  # small delay so startup isn't slowed
            while True:
                self.refresh()
                time.sleep(REFRESH_INTERVAL_SEC)

        t = threading.Thread(target=_loop, daemon=True)
        t.start()
