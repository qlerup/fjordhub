import os


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
