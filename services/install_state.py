import json
import threading
from datetime import datetime, timezone
from pathlib import Path


class InstallState:
    def __init__(self, data_dir: Path):
        self._file = data_dir / "install_state.json"
        self._lock = threading.Lock()
        self._state: dict = self._load()

    def get(self, app_id: str) -> dict:
        with self._lock:
            return dict(self._state.get(app_id, {}))

    def get_install_dir(self, app_id: str) -> str | None:
        with self._lock:
            return self._state.get(app_id, {}).get("install_dir")

    def set_installing(self, app_id: str, install_dir: str):
        self._update(app_id, {
            "state": "installing",
            "install_dir": install_dir,
            "log": [],
            "error": None,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
        })

    def append_log(self, app_id: str, line: str):
        with self._lock:
            self._state.setdefault(app_id, {}).setdefault("log", []).append(line)
            self._save()

    def set_installed(self, app_id: str):
        self._update(app_id, {
            "state": "installed",
            "finished_at": datetime.now(timezone.utc).isoformat(),
        })

    def clear(self, app_id: str):
        with self._lock:
            self._state.pop(app_id, None)
            self._save()

    def set_failed(self, app_id: str, error: str):
        self._update(app_id, {
            "state": "failed",
            "error": error,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        })

    def is_initialized(self, key: str) -> bool:
        with self._lock:
            state = self._state.get(key, {})
            return bool(state.get("initialized"))

    def mark_initialized(self, key: str, app_name: str, db_path: str, reason: str = "unknown"):
        if self.is_initialized(key):
            return
        self._update(key, {
            "app": app_name,
            "initialized": True,
            "initialized_at": datetime.now(timezone.utc).isoformat(),
            "reason": str(reason or "unknown"),
            "db_path": str(db_path or ""),
        })

    def _update(self, app_id: str, updates: dict):
        with self._lock:
            self._state.setdefault(app_id, {}).update(updates)
            self._save()

    def _load(self) -> dict:
        if self._file.exists():
            try:
                return json.loads(self._file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _save(self):
        self._file.write_text(
            json.dumps(self._state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
