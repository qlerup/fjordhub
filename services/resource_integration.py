"""Explicit read-only projection of the Docker resource dashboard."""

METRICS = (
    "cpu_percent", "cpu_capacity_percent", "memory_usage", "memory_percent",
    "net_rx", "net_tx", "block_read", "block_write",
)
GROUP_FIELDS = (
    "id", "name", "container_count", "running_count", *METRICS,
    *(f"{key}_label" for key in METRICS),
)
CONTAINER_FIELDS = (
    "id", "name", "status", "cpu_percent", "memory_usage", "memory_limit",
    "net_rx", "net_tx", "block_read", "block_write",
    "memory_usage_label", "net_rx_label", "net_tx_label",
    "block_read_label", "block_write_label",
)


def _pick(value: dict, fields: tuple) -> dict:
    return {key: value[key] for key in fields if key in value}


def _group(value: dict) -> dict:
    result = _pick(value, GROUP_FIELDS)
    result["containers"] = []
    for container in value.get("containers", []):
        item = _pick(container, CONTAINER_FIELDS)
        # Docker exception text can contain internal connection details.
        item["error"] = "Container metrics unavailable" if container.get("error") else None
        result["containers"].append(item)
    return result


def docker_resource_payload(snapshot: dict) -> dict:
    result = {
        "ok": bool(snapshot.get("ok")),
        "generated_at": snapshot.get("generated_at"),
        "capacity": _pick(snapshot.get("capacity", {}),
                          ("cpus", "memory_total", "memory_total_label")),
        "hub": _group(snapshot.get("hub", {})),
        "core": _group(snapshot.get("core", {})),
        "apps": [_group(app) for app in snapshot.get("apps", [])],
    }
    if not result["ok"]:
        result["error"] = "Docker metrics unavailable"
    return result
