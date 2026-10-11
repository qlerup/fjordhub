"""Persistent local credentials shared only by the hub's control services."""
import os
import secrets
import tempfile
from pathlib import Path


_PLACEHOLDERS = {"dev-secret-change-me", "change-me-in-production", "changeme", "change-me"}


def _validate(value: str) -> str:
    if not value.strip() or value.strip().lower() in _PLACEHOLDERS:
        raise RuntimeError("Unsafe SECRET_KEY: configure a random secret before starting FjordHub")
    return value


def _persistent_secret(path: Path) -> str:
    """Publish a complete private file atomically, also across concurrent starts."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not path.exists():
        fd, temporary = tempfile.mkstemp(prefix=".secret-", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(secrets.token_hex(32))
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, path)
            except FileExistsError:
                pass  # Another worker published its complete key first.
        finally:
            os.unlink(temporary)
    value = path.read_text(encoding="utf-8").strip()
    if len(value) < 32 or value.lower() in _PLACEHOLDERS:
        raise RuntimeError("Invalid persisted control secret; restore it from a trusted backup")
    return value


def load_session_secret(data_dir: Path) -> str:
    configured = os.environ.get("SECRET_KEY", "")
    if configured:
        # Preserve existing keys byte-for-byte: SMTP encryption also uses this key.
        return _validate(configured)
    return _persistent_secret(Path(data_dir) / "security" / "session_key")


def load_updater_token(data_dir: Path) -> str:
    path = os.environ.get("FJORDHUB_UPDATER_TOKEN_FILE", "")
    return _persistent_secret(Path(path) if path else Path(data_dir) / "security" / "updater_token")
