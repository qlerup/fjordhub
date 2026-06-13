from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _format_bytes(value: int | float | None) -> str:
    size = _safe_float(value)
    units = ("B", "KB", "MB", "GB", "TB")
    for unit in units:
        if abs(size) < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return "0 B"


SIZE_RE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*([KMGTPE]?i?B|[kMGTPE]?B|B)\s*$")
SIZE_UNITS = {
    "B": 1,
    "KB": 1000,
    "kB": 1000,
    "MB": 1000 ** 2,
    "GB": 1000 ** 3,
    "TB": 1000 ** 4,
    "PB": 1000 ** 5,
    "EB": 1000 ** 6,
    "KiB": 1024,
    "MiB": 1024 ** 2,
    "GiB": 1024 ** 3,
    "TiB": 1024 ** 4,
    "PiB": 1024 ** 5,
    "EiB": 1024 ** 6,
}


def _parse_size(value: str) -> int:
    match = SIZE_RE.match(str(value or ""))
    if not match:
        return 0
    number, unit = match.groups()
    return int(float(number) * SIZE_UNITS.get(unit, 1))


def _parse_pair(value: str) -> tuple[int, int]:
    left, _, right = str(value or "").partition("/")
    return _parse_size(left), _parse_size(right)


def _parse_percent(value: str) -> float:
    return _safe_float(str(value or "").replace("%", "").strip())


def _container_name(container) -> str:
    return str(getattr(container, "name", "") or "").lstrip("/")


def _compose_project(container) -> str:
    labels = getattr(container, "labels", None) or {}
    return str(labels.get("com.docker.compose.project") or "")


def _compose_working_dir(container) -> str:
    labels = getattr(container, "labels", None) or {}
    return str(labels.get("com.docker.compose.project.working_dir") or "")


def _cpu_percent(stats: dict) -> float:
    cpu_stats = stats.get("cpu_stats") or {}
    precpu_stats = stats.get("precpu_stats") or {}
    cpu_usage = cpu_stats.get("cpu_usage") or {}
    precpu_usage = precpu_stats.get("cpu_usage") or {}

    cpu_delta = _safe_float(cpu_usage.get("total_usage")) - _safe_float(precpu_usage.get("total_usage"))
    system_delta = _safe_float(cpu_stats.get("system_cpu_usage")) - _safe_float(precpu_stats.get("system_cpu_usage"))
    online_cpus = _safe_int(cpu_stats.get("online_cpus"))
    if online_cpus <= 0:
        online_cpus = len(cpu_usage.get("percpu_usage") or []) or 1

    if cpu_delta <= 0 or system_delta <= 0:
        return 0.0
    return max(0.0, (cpu_delta / system_delta) * online_cpus * 100.0)


def _memory_usage(stats: dict) -> int:
    memory = stats.get("memory_stats") or {}
    usage = _safe_int(memory.get("usage"))
    details = memory.get("stats") or {}
    cache = (
        _safe_int(details.get("inactive_file"))
        or _safe_int(details.get("total_inactive_file"))
        or _safe_int(details.get("cache"))
    )
    if cache and usage > cache:
        return usage - cache
    return usage


def _memory_limit(stats: dict) -> int:
    memory = stats.get("memory_stats") or {}
    return _safe_int(memory.get("limit"))


def _network_totals(stats: dict) -> tuple[int, int]:
    rx = 0
    tx = 0
    for iface in (stats.get("networks") or {}).values():
        rx += _safe_int(iface.get("rx_bytes"))
        tx += _safe_int(iface.get("tx_bytes"))
    return rx, tx


def _block_io_totals(stats: dict) -> tuple[int, int]:
    read = 0
    write = 0
    for item in ((stats.get("blkio_stats") or {}).get("io_service_bytes_recursive") or []):
        op = str(item.get("op") or "").lower()
        value = _safe_int(item.get("value"))
        if op == "read":
            read += value
        elif op == "write":
            write += value
    return read, write


class ResourceMonitor:
    def __init__(self, docker_manager):
        self.docker_manager = docker_manager

    @property
    def client(self):
        return getattr(self.docker_manager, "client", None)

    def collect(self, apps: list[dict]) -> dict:
        if not self.client:
            return {
                "ok": False,
                "error": "Docker er ikke tilgaengelig",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "capacity": self._empty_capacity(),
                "hub": self._empty_group("FjordHub"),
                "core": self._empty_group("FjordHub core"),
                "apps": [],
            }

        try:
            containers = self.client.containers.list(all=True)
        except Exception as exc:
            return {
                "ok": False,
                "error": str(exc),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "capacity": self._empty_capacity(),
                "hub": self._empty_group("FjordHub"),
                "core": self._empty_group("FjordHub core"),
                "apps": [],
            }

        capacity = self._capacity()
        stats_by_id = self._stats_by_container(containers)

        app_groups = []
        used_container_ids: set[str] = set()
        for app_def in apps:
            matched = self._match_app_containers(app_def, containers)
            if not matched:
                continue
            for container in matched:
                used_container_ids.add(container.id)
            group = self._group_summary(
                str(app_def.get("name") or app_def.get("id") or "App"),
                matched,
                stats_by_id,
                capacity,
            )
            group.update({
                "id": app_def.get("id"),
                "accent": app_def.get("accent") or "#3b82f6",
                "icon_url": app_def.get("icon_url") or "",
            })
            app_groups.append(group)

        core_containers = self._core_containers(containers)
        for container in core_containers:
            used_container_ids.add(container.id)

        hub_containers = core_containers + [
            container for container in containers
            if container.id in used_container_ids and container not in core_containers
        ]

        return {
            "ok": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "capacity": capacity,
            "hub": self._group_summary("FjordHub", hub_containers, stats_by_id, capacity),
            "core": self._group_summary("FjordHub core", core_containers, stats_by_id, capacity),
            "apps": app_groups,
        }

    def _capacity(self) -> dict:
        try:
            info = self.client.info()
        except Exception:
            info = {}
        cpus = _safe_int(info.get("NCPU"), 1) or 1
        memory_total = _safe_int(info.get("MemTotal"))
        return {
            "cpus": cpus,
            "memory_total": memory_total,
            "memory_total_label": _format_bytes(memory_total) if memory_total else "Ukendt",
        }

    def _empty_capacity(self) -> dict:
        return {"cpus": 1, "memory_total": 0, "memory_total_label": "Ukendt"}

    def _stats_by_container(self, containers: list) -> dict[str, dict]:
        stats = {}
        for container in containers:
            if getattr(container, "status", "") != "running":
                stats[container.id] = self._container_snapshot(container, None)
                continue
            try:
                raw = container.stats(stream=False, decode=True)
            except Exception as exc:
                stats[container.id] = self._container_snapshot(container, None, str(exc))
                continue
            stats[container.id] = self._container_snapshot(container, raw)
        self._fill_from_docker_stats_cli(stats)
        return stats

    def _fill_from_docker_stats_cli(self, stats: dict[str, dict]) -> None:
        names_needing_stats = [
            item["name"]
            for item in stats.values()
            if item.get("status") == "running" and self._is_empty_stats(item)
        ]
        if not names_needing_stats:
            return

        try:
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "{{json .}}", *names_needing_stats],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except Exception:
            return
        if result.returncode != 0:
            return

        by_name = {item.get("name"): item for item in stats.values()}
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            name = str(row.get("Name") or row.get("Container") or "").lstrip("/")
            item = by_name.get(name)
            if not item:
                continue
            mem_usage, mem_limit = _parse_pair(row.get("MemUsage") or "")
            net_rx, net_tx = _parse_pair(row.get("NetIO") or "")
            block_read, block_write = _parse_pair(row.get("BlockIO") or "")
            item.update({
                "cpu_percent": round(_parse_percent(row.get("CPUPerc")), 2),
                "memory_usage": mem_usage,
                "memory_limit": mem_limit,
                "net_rx": net_rx,
                "net_tx": net_tx,
                "block_read": block_read,
                "block_write": block_write,
                "error": None,
            })

    def _is_empty_stats(self, item: dict) -> bool:
        return (
            _safe_float(item.get("cpu_percent")) == 0
            and _safe_int(item.get("memory_usage")) == 0
            and _safe_int(item.get("net_rx")) == 0
            and _safe_int(item.get("net_tx")) == 0
            and _safe_int(item.get("block_read")) == 0
            and _safe_int(item.get("block_write")) == 0
        )

    def _container_snapshot(self, container, raw: dict | None, error: str | None = None) -> dict:
        status = str(getattr(container, "status", "") or "unknown")
        if not raw:
            return {
                "id": container.id,
                "name": _container_name(container),
                "status": status,
                "cpu_percent": 0.0,
                "memory_usage": 0,
                "memory_limit": 0,
                "net_rx": 0,
                "net_tx": 0,
                "block_read": 0,
                "block_write": 0,
                "error": error,
            }

        net_rx, net_tx = _network_totals(raw)
        block_read, block_write = _block_io_totals(raw)
        return {
            "id": container.id,
            "name": _container_name(container),
            "status": status,
            "cpu_percent": round(_cpu_percent(raw), 2),
            "memory_usage": _memory_usage(raw),
            "memory_limit": _memory_limit(raw),
            "net_rx": net_rx,
            "net_tx": net_tx,
            "block_read": block_read,
            "block_write": block_write,
            "error": error,
        }

    def _group_summary(self, name: str, containers: list, stats_by_id: dict[str, dict], capacity: dict) -> dict:
        items = [stats_by_id.get(container.id) for container in containers]
        items = [item for item in items if item]
        memory_total = _safe_int(capacity.get("memory_total"))
        cpus = _safe_int(capacity.get("cpus"), 1) or 1

        cpu_percent = round(sum(_safe_float(item.get("cpu_percent")) for item in items), 2)
        memory_usage = sum(_safe_int(item.get("memory_usage")) for item in items)
        net_rx = sum(_safe_int(item.get("net_rx")) for item in items)
        net_tx = sum(_safe_int(item.get("net_tx")) for item in items)
        block_read = sum(_safe_int(item.get("block_read")) for item in items)
        block_write = sum(_safe_int(item.get("block_write")) for item in items)
        running = sum(1 for item in items if item.get("status") == "running")

        memory_percent = (memory_usage / memory_total * 100.0) if memory_total else 0.0
        cpu_capacity_percent = min(100.0, cpu_percent / cpus) if cpus else min(100.0, cpu_percent)

        return {
            "name": name,
            "container_count": len(items),
            "running_count": running,
            "cpu_percent": cpu_percent,
            "cpu_percent_label": f"{cpu_percent:.1f}%",
            "cpu_capacity_percent": round(cpu_capacity_percent, 2),
            "memory_usage": memory_usage,
            "memory_usage_label": _format_bytes(memory_usage),
            "memory_percent": round(memory_percent, 2),
            "memory_percent_label": f"{memory_percent:.1f}%",
            "net_rx": net_rx,
            "net_rx_label": _format_bytes(net_rx),
            "net_tx": net_tx,
            "net_tx_label": _format_bytes(net_tx),
            "block_read": block_read,
            "block_read_label": _format_bytes(block_read),
            "block_write": block_write,
            "block_write_label": _format_bytes(block_write),
            "containers": [
                {
                    **item,
                    "memory_usage_label": _format_bytes(item.get("memory_usage")),
                    "net_rx_label": _format_bytes(item.get("net_rx")),
                    "net_tx_label": _format_bytes(item.get("net_tx")),
                    "block_read_label": _format_bytes(item.get("block_read")),
                    "block_write_label": _format_bytes(item.get("block_write")),
                }
                for item in sorted(items, key=lambda item: item.get("name") or "")
            ],
        }

    def _empty_group(self, name: str) -> dict:
        return {
            "name": name,
            "container_count": 0,
            "running_count": 0,
            "cpu_percent": 0.0,
            "cpu_percent_label": "0.0%",
            "cpu_capacity_percent": 0.0,
            "memory_usage": 0,
            "memory_usage_label": "0 B",
            "memory_percent": 0.0,
            "memory_percent_label": "0.0%",
            "net_rx": 0,
            "net_rx_label": "0 B",
            "net_tx": 0,
            "net_tx_label": "0 B",
            "block_read": 0,
            "block_read_label": "0 B",
            "block_write": 0,
            "block_write_label": "0 B",
            "containers": [],
        }

    def _match_app_containers(self, app_def: dict, containers: list) -> list:
        app_id = str(app_def.get("id") or "")
        main_name = str(app_def.get("container_name") or "")
        install_dir = str(app_def.get("compose_dir") or "")
        matched = []
        for container in containers:
            name = _container_name(container)
            project = _compose_project(container)
            working_dir = _compose_working_dir(container)
            if main_name and name == main_name:
                matched.append(container)
            elif app_id and project == app_id:
                matched.append(container)
            elif install_dir and working_dir == install_dir:
                matched.append(container)
            elif app_id and (name == app_id or name.startswith(f"{app_id}-") or name.startswith(f"{app_id}_")):
                matched.append(container)
        return sorted({container.id: container for container in matched}.values(), key=_container_name)

    def _core_containers(self, containers: list) -> list:
        core_names = {"fjordhub", "fjordhub-traefik"}
        matched = []
        for container in containers:
            name = _container_name(container)
            project = _compose_project(container)
            if name in core_names or (project == "fjordhub" and name.startswith("fjordhub")):
                matched.append(container)
        return sorted({container.id: container for container in matched}.values(), key=_container_name)
