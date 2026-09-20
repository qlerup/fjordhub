import os
from pathlib import Path


FJORDLENS_MEMORY_DEFAULTS = {
    "FJORDLENS_MEMORY_GUARD": "1",
    "FJORDLENS_WEB_MEMORY_BOOT_LIMIT": "768m",
    "FJORDLENS_AI_MEMORY_BOOT_LIMIT": "2g",
    "FJORDLENS_CONVERT_MEMORY_BOOT_LIMIT": "512m",
    "FJORDLENS_UPDATER_MEMORY_BOOT_LIMIT": "128m",
}


def enable_fjordlens_memory_guard(install_dir: Path) -> None:
    """Migrate existing Hub installations; standalone Compose stays opt-out."""
    path = Path(install_dir) / ".env"
    original = path.read_text(encoding="utf-8") if path.exists() else ""
    keys = {line.split("=", 1)[0].strip() for line in original.splitlines() if "=" in line}
    missing = [f"{key}={value}" for key, value in FJORDLENS_MEMORY_DEFAULTS.items() if key not in keys]
    if missing:
        path.write_text(original.rstrip("\n") + "\n" + "\n".join(missing) + "\n", encoding="utf-8")


COMPOSE_ENV_PASSTHROUGH = (
    "PATH",
    "HOME",
    "DOCKER_HOST",
    "DOCKER_TLS_VERIFY",
    "DOCKER_CERT_PATH",
    "DOCKER_CONTEXT",
    "COMPOSE_PROFILES",
)


def build_compose_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    """Build a minimal environment for child app docker compose commands."""
    env = {
        key: value
        for key in COMPOSE_ENV_PASSTHROUGH
        if (value := os.environ.get(key))
    }
    if extra:
        env.update({str(key): str(value) for key, value in extra.items()})
    return env
