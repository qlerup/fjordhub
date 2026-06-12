import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

CACHE_FILE = "registry_cache.json"
REFRESH_INTERVAL_SEC = 3600  # 1 hour
REQUEST_TIMEOUT_SEC = 10


class RemoteRegistry:
    """
    Fetches the app registry from a remote URL (GitHub raw content) and
    caches it locally. Falls back to the cache when GitHub is unreachable.

    Registry format (registry.json in FjordHub's GitHub repo):
      { "schema": "fjordhub-registry/v1",
        "apps": [ { "id": "fjordlens",
                    "manifest_url": "https://raw.githubusercontent.com/..." } ] }

    Each manifest_url points to a fjordhub.json in the app's own repo.
    """

    def __init__(self, data_dir: Path, registry_url: str):
        self.data_dir = data_dir
        self.registry_url = registry_url
        self._cache_file = data_dir / CACHE_FILE
        self._lock = threading.Lock()
        self._apps: list[dict] = []
        self._last_refresh: datetime | None = None
        self._last_error: str | None = None

        data_dir.mkdir(parents=True, exist_ok=True)
        self._load_cache()
        self._start_background_refresh()

    # ── Public API ──────────────────────────────────────────────────────────

    def get_apps(self) -> list[dict]:
        with self._lock:
            return list(self._apps)

    def get_status(self) -> dict:
        with self._lock:
            return {
                "last_refresh": self._last_refresh.isoformat() if self._last_refresh else None,
                "last_refresh_ago": self._seconds_ago(self._last_refresh),
                "app_count": len(self._apps),
                "error": self._last_error,
                "registry_url": self.registry_url,
                "configured": not self.registry_url.startswith("https://raw.githubusercontent.com/OWNER/"),
            }

    def refresh(self) -> tuple[bool, str]:
        """Fetch registry + all app manifests from GitHub. Returns (ok, message)."""
        if self.registry_url.startswith("https://raw.githubusercontent.com/OWNER/"):
            return False, "REGISTRY_URL er ikke konfigureret. Sæt miljøvariablen."

        try:
            resp = requests.get(self.registry_url, timeout=REQUEST_TIMEOUT_SEC)
            resp.raise_for_status()
            registry = resp.json()
        except requests.RequestException as e:
            with self._lock:
                self._last_error = f"Kunne ikke hente registry: {e}"
            return False, self._last_error

        apps, errors = [], []

        for entry in registry.get("apps", []):
            manifest_url = entry.get("manifest_url", "").strip()
            if not manifest_url:
                continue
            try:
                m = requests.get(manifest_url, timeout=REQUEST_TIMEOUT_SEC)
                m.raise_for_status()
                app_data = m.json()
                app_data.setdefault("source_url", entry.get("source_url", ""))
                apps.append(app_data)
            except Exception as e:
                errors.append(f"{entry.get('id', '?')}: {e}")

        apps.sort(key=lambda a: a.get("sort_order", 99))

        with self._lock:
            self._apps = apps
            self._last_refresh = datetime.now(timezone.utc)
            self._last_error = ("; ".join(errors)) if errors else None

        self._save_cache(apps)

        msg = f"Hentet {len(apps)} apps"
        if errors:
            msg += f" ({len(errors)} fejl)"
        return True, msg

    # ── Internal ─────────────────────────────────────────────────────────────

    def _load_cache(self):
        if not self._cache_file.exists():
            return
        try:
            data = json.loads(self._cache_file.read_text(encoding="utf-8"))
            with self._lock:
                self._apps = data.get("apps", [])
                ts = data.get("last_refresh")
                self._last_refresh = datetime.fromisoformat(ts) if ts else None
        except Exception:
            pass

    def _save_cache(self, apps: list[dict]):
        payload = {
            "last_refresh": datetime.now(timezone.utc).isoformat(),
            "apps": apps,
        }
        self._cache_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _start_background_refresh(self):
        def _loop():
            time.sleep(10)  # small delay so startup isn't slowed
            while True:
                self.refresh()
                time.sleep(REFRESH_INTERVAL_SEC)

        t = threading.Thread(target=_loop, daemon=True)
        t.start()

    @staticmethod
    def _seconds_ago(dt: datetime | None) -> int | None:
        if dt is None:
            return None
        return int((datetime.now(timezone.utc) - dt).total_seconds())
