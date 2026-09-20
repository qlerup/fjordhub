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
    # This helper is called only for a registered Hub installation. Repair the
    # old disabled/unlimited values as well as missing keys.
    lines = []
    for line in original.splitlines():
        key, sep, value = line.partition('=')
        key = key.strip()
        if sep and key in FJORDLENS_MEMORY_DEFAULTS and (key == 'FJORDLENS_MEMORY_GUARD' or value.strip().strip('\"\'') in {'', '0'}):
            line = f'{key}={FJORDLENS_MEMORY_DEFAULTS[key]}'
        lines.append(line)
    updated = '\n'.join(lines)
    keys = {line.split("=", 1)[0].strip() for line in lines if "=" in line}
    missing = [f"{key}={value}" for key, value in FJORDLENS_MEMORY_DEFAULTS.items() if key not in keys]
    updated = '\n'.join([updated.rstrip('\n'), *missing]).lstrip('\n') + '\n'
    if updated != original:
        temporary = path.with_name('.env.memory.tmp')
        temporary.write_text(updated, encoding='utf-8')
        temporary.replace(path)


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
