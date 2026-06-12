import json
from pathlib import Path


class AppRegistry:
    def __init__(self, registry_dir: Path):
        self.registry_dir = registry_dir

    def get_all(self) -> list[dict]:
        apps = []
        for f in sorted(self.registry_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                apps.append(data)
            except Exception:
                pass
        return apps

    def get(self, app_id: str) -> dict | None:
        for app in self.get_all():
            if app.get("id") == app_id:
                return app
        return None
