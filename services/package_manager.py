import hashlib
import io
import json
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

import requests


MAX_DOWNLOAD_BYTES = 5 * 1024 * 1024
MAX_EXTRACTED_BYTES = 15 * 1024 * 1024
REQUIRED_FILES = {"manifest.json", "body.html"}


class PackageError(RuntimeError):
    pass


class PackageManager:
    def __init__(self, data_dir: Path):
        self.root = data_dir / "packages"
        self.root.mkdir(parents=True, exist_ok=True)

    def install(self, definition: dict) -> dict:
        package_id = self._safe_id(definition.get("id"))
        url = str(definition.get("download_url") or "").strip()
        expected_sha = str(definition.get("sha256") or "").strip().lower()
        if not url.startswith("https://") or len(expected_sha) != 64:
            raise PackageError("Pakken har ikke en gyldig download eller checksum.")

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise PackageError(f"Pakken kunne ikke downloades: {exc}") from exc
        archive = response.content
        if len(archive) > MAX_DOWNLOAD_BYTES:
            raise PackageError("Pakken er større end den tilladte grænse.")
        if hashlib.sha256(archive).hexdigest() != expected_sha:
            raise PackageError("Pakkens checksum matcher ikke kataloget.")

        stage_parent = Path(tempfile.mkdtemp(prefix=f".{package_id}-", dir=self.root))
        stage = stage_parent / package_id
        stage.mkdir()
        try:
            self._extract(archive, stage)
            manifest = self._read_manifest(stage)
            if manifest.get("id") != package_id:
                raise PackageError("Pakkens manifest har et forkert id.")
            if str(manifest.get("version")) != str(definition.get("version")):
                raise PackageError("Pakkens version matcher ikke kataloget.")
            target = self.root / package_id
            old = self.root / f".{package_id}.old"
            if old.exists():
                shutil.rmtree(old)
            if target.exists():
                target.rename(old)
            stage.rename(target)
            if old.exists():
                shutil.rmtree(old)
            return manifest
        finally:
            if stage_parent.exists():
                shutil.rmtree(stage_parent, ignore_errors=True)

    def uninstall(self, package_id: str) -> None:
        target = self.root / self._safe_id(package_id)
        if target.exists():
            shutil.rmtree(target)

    def is_installed(self, package_id: str) -> bool:
        try:
            self._read_manifest(self.root / self._safe_id(package_id))
            return True
        except (PackageError, OSError):
            return False

    def installed_manifest(self, package_id: str) -> dict:
        return self._read_manifest(self.root / self._safe_id(package_id))

    def read_text(self, package_id: str, filename: str) -> str:
        if filename not in {"body.html", "app.js", "styles.css"}:
            raise PackageError("Ugyldig pakkefil.")
        path = self.root / self._safe_id(package_id) / filename
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise PackageError("Pakkefilen blev ikke fundet.") from exc

    def asset_path(self, package_id: str, filename: str) -> Path:
        package_dir = self.root / self._safe_id(package_id)
        candidate = (package_dir / filename).resolve()
        if package_dir.resolve() not in candidate.parents or not candidate.is_file():
            raise PackageError("Pakkefilen blev ikke fundet.")
        return candidate

    def _extract(self, archive: bytes, target: Path) -> None:
        try:
            with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
                total = 0
                names = set()
                for item in bundle.infolist():
                    path = PurePosixPath(item.filename)
                    if path.is_absolute() or ".." in path.parts or item.is_dir():
                        if item.is_dir():
                            continue
                        raise PackageError("Pakken indeholder en ugyldig filsti.")
                    total += item.file_size
                    if total > MAX_EXTRACTED_BYTES:
                        raise PackageError("Pakkens udpakkede størrelse er for stor.")
                    names.add(item.filename)
                    output = target.joinpath(*path.parts)
                    output.parent.mkdir(parents=True, exist_ok=True)
                    with bundle.open(item) as source, output.open("wb") as destination:
                        shutil.copyfileobj(source, destination)
                if not REQUIRED_FILES.issubset(names):
                    raise PackageError("Pakken mangler manifest.json eller body.html.")
        except zipfile.BadZipFile as exc:
            raise PackageError("Downloaden er ikke en gyldig FjordHub-pakke.") from exc

    @staticmethod
    def _safe_id(package_id) -> str:
        value = str(package_id or "")
        if not value or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-" for char in value):
            raise PackageError("Ugyldigt pakke-id.")
        return value

    @staticmethod
    def _read_manifest(package_dir: Path) -> dict:
        try:
            data = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise PackageError("Pakken er ikke korrekt installeret.") from exc
        if not isinstance(data, dict):
            raise PackageError("Pakkens manifest er ugyldigt.")
        return data
