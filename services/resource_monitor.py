from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


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
        self._system_lock = threading.Lock()
        self._system_cpu_prev: tuple[int, float] | None = None

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
                "system": self._empty_system("Docker er ikke tilgaengelig"),
                "overhead": self._overhead_summary(
                    self._empty_system("Docker er ikke tilgaengelig"),
                    self._empty_group("FjordHub"),
                    self._empty_capacity(),
                ),
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
                "system": self._empty_system("Kunne ikke hente Docker-containere"),
                "overhead": self._overhead_summary(
                    self._empty_system("Kunne ikke hente Docker-containere"),
                    self._empty_group("FjordHub"),
                    self._empty_capacity(),
                ),
                "hub": self._empty_group("FjordHub"),
                "core": self._empty_group("FjordHub core"),
                "apps": [],
            }

        capacity = self._capacity()
        system = self._system_summary(capacity)
        if system.get("available") and system.get("memory_limit"):
            capacity["memory_total"] = system["memory_limit"]
            capacity["memory_total_label"] = _format_bytes(system["memory_limit"])
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

        hub = self._group_summary("FjordHub", hub_containers, stats_by_id, capacity)
        core = self._group_summary("FjordHub core", core_containers, stats_by_id, capacity)

        return {
            "ok": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "capacity": capacity,
            "system": system,
            "overhead": self._overhead_summary(system, hub, capacity),
            "hub": hub,
            "core": core,
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

    def _system_summary(self, capacity: dict) -> dict:
        root = Path(os.environ.get("HOST_CGROUP_ROOT", "/host/sys/fs/cgroup"))
        if not root.exists():
            return self._empty_system("Cgroup er ikke monteret")

        memory_limit = self._read_cgroup_memory_limit(root)
        memory_usage_raw = self._read_cgroup_memory_usage(root)
        memory_cache = self._read_cgroup_memory_cache(root)
        memory_source = "cgroup"
        memory_usage = memory_usage_raw
        if memory_usage_raw is not None and memory_cache:
            memory_usage = max(memory_usage_raw - memory_cache, 0)

        proc_memory = self._read_proc_memory()
        if self._proc_memory_matches_limit(proc_memory, memory_limit):
            memory_usage = proc_memory["usage"]
            memory_limit = proc_memory["limit"]
            memory_source = "proc_meminfo"

        cpu_usage = self._read_cgroup_cpu_usage(root)
        if memory_usage is None and cpu_usage is None:
            return self._empty_system("Kunne ikke laese cgroup-tal")

        cpus = _safe_int(capacity.get("cpus"), 1) or 1
        now = time.monotonic()
        cpu_percent = 0.0
        if cpu_usage is not None:
            with self._system_lock:
                previous = self._system_cpu_prev
                self._system_cpu_prev = (cpu_usage, now)
            if previous:
                previous_usage, previous_time = previous
                elapsed = max(now - previous_time, 0.001)
                delta = max(cpu_usage - previous_usage, 0)
                cpu_percent = (delta / 1_000_000_000.0) / elapsed * 100.0

        if not memory_limit or memory_limit <= 0:
            memory_limit = _safe_int(capacity.get("memory_total"))
        memory_percent = (memory_usage / memory_limit * 100.0) if memory_usage and memory_limit else 0.0
        cpu_capacity_percent = min(100.0, cpu_percent / cpus) if cpus else min(100.0, cpu_percent)

        return {
            "available": True,
            "cpu_percent": round(cpu_percent, 2),
            "cpu_percent_label": f"{cpu_percent:.1f}%",
            "cpu_capacity_percent": round(cpu_capacity_percent, 2),
            "cpu_capacity_percent_label": f"{cpu_capacity_percent:.1f}%",
            "memory_usage": memory_usage or 0,
            "memory_usage_label": _format_bytes(memory_usage or 0),
            "memory_usage_raw": memory_usage_raw or 0,
            "memory_usage_raw_label": _format_bytes(memory_usage_raw or 0),
            "memory_cache": memory_cache or 0,
            "memory_cache_label": _format_bytes(memory_cache or 0),
            "memory_source": memory_source,
            "memory_limit": memory_limit or 0,
            "memory_limit_label": _format_bytes(memory_limit or 0) if memory_limit else "Ukendt",
            "memory_percent": round(memory_percent, 2),
            "memory_percent_label": f"{memory_percent:.1f}%",
            "message": "",
        }

    def _overhead_summary(self, system: dict, hub: dict, capacity: dict) -> dict:
        if not system.get("available"):
            return {
                "available": False,
                "cpu_percent": 0.0,
                "cpu_percent_label": "0.0%",
                "cpu_capacity_percent": 0.0,
                "cpu_capacity_percent_label": "0.0%",
                "memory_usage": 0,
                "memory_usage_label": "0 B",
                "memory_percent": 0.0,
                "memory_percent_label": "0.0%",
                "message": system.get("message") or "Ikke tilgaengelig",
            }

        cpus = _safe_int(capacity.get("cpus"), 1) or 1
        memory_total = _safe_int(capacity.get("memory_total"))
        memory_usage = max(_safe_int(system.get("memory_usage")) - _safe_int(hub.get("memory_usage")), 0)
        cpu_percent = max(_safe_float(system.get("cpu_percent")) - _safe_float(hub.get("cpu_percent")), 0.0)
        memory_percent = (memory_usage / memory_total * 100.0) if memory_total else 0.0
        cpu_capacity_percent = min(100.0, cpu_percent / cpus) if cpus else min(100.0, cpu_percent)
        return {
            "available": True,
            "cpu_percent": round(cpu_percent, 2),
            "cpu_percent_label": f"{cpu_percent:.1f}%",
            "cpu_capacity_percent": round(cpu_capacity_percent, 2),
            "cpu_capacity_percent_label": f"{cpu_capacity_percent:.1f}%",
            "memory_usage": memory_usage,
            "memory_usage_label": _format_bytes(memory_usage),
            "memory_percent": round(memory_percent, 2),
            "memory_percent_label": f"{memory_percent:.1f}%",
            "message": "",
        }

    def _empty_system(self, message: str) -> dict:
        return {
            "available": False,
            "cpu_percent": 0.0,
            "cpu_percent_label": "0.0%",
            "cpu_capacity_percent": 0.0,
            "cpu_capacity_percent_label": "0.0%",
            "memory_usage": 0,
            "memory_usage_label": "0 B",
            "memory_limit": 0,
            "memory_limit_label": "Ukendt",
            "memory_percent": 0.0,
            "memory_percent_label": "0.0%",
            "message": message,
        }

    def _read_cgroup_memory_usage(self, root: Path) -> int | None:
        for path in (root / "memory.current", root / "memory" / "memory.usage_in_bytes"):
            value = self._read_int_file(path)
            if value is not None:
                return value
        return None

    def _read_cgroup_memory_cache(self, root: Path) -> int:
        stats = self._read_cgroup_memory_stat(root)
        return (
            _safe_int(stats.get("inactive_file"))
            or _safe_int(stats.get("total_inactive_file"))
            or _safe_int(stats.get("cache"))
            or _safe_int(stats.get("total_cache"))
            or _safe_int(stats.get("file"))
        )

    def _read_cgroup_memory_stat(self, root: Path) -> dict[str, int]:
        for path in (root / "memory.stat", root / "memory" / "memory.stat"):
            if not path.exists():
                continue
            try:
                stats = {}
                for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    parts = line.split(None, 1)
                    if len(parts) == 2:
                        stats[parts[0]] = _safe_int(parts[1])
                return stats
            except Exception:
                return {}
        return {}

    def _read_proc_memory(self) -> dict[str, int] | None:
        try:
            stats = {}
            for line in Path("/proc/meminfo").read_text(encoding="utf-8", errors="ignore").splitlines():
                key, _, value = line.partition(":")
                if key:
                    stats[key] = _safe_int(value.strip().split()[0]) * 1024
            total = _safe_int(stats.get("MemTotal"))
            available = _safe_int(stats.get("MemAvailable"))
            if total > 0 and available >= 0:
                return {"limit": total, "usage": max(total - available, 0)}
        except Exception:
            return None
        return None

    def _proc_memory_matches_limit(self, proc_memory: dict[str, int] | None, memory_limit: int | None) -> bool:
        if not proc_memory:
            return False
        proc_limit = _safe_int(proc_memory.get("limit"))
        cgroup_limit = _safe_int(memory_limit)
        if proc_limit <= 0:
            return False
        if cgroup_limit <= 0:
            return proc_limit < 1 << 50
        ratio = proc_limit / cgroup_limit
        return 0.90 <= ratio <= 1.10

    def _read_cgroup_memory_limit(self, root: Path) -> int | None:
        for path in (root / "memory.max", root / "memory" / "memory.limit_in_bytes"):
            if not path.exists():
                continue
            raw = path.read_text(encoding="utf-8", errors="ignore").strip()
            if raw == "max":
                return None
            value = _safe_int(raw)
            # Ignore cgroup v1's "effectively unlimited" sentinel values.
            if value > 0 and value < 1 << 60:
                return value
        return None

    def _read_cgroup_cpu_usage(self, root: Path) -> int | None:
        cpu_stat = root / "cpu.stat"
        if cpu_stat.exists():
            try:
                for line in cpu_stat.read_text(encoding="utf-8", errors="ignore").splitlines():
                    key, _, value = line.partition(" ")
                    if key == "usage_usec":
                        return _safe_int(value) * 1000
            except Exception:
                return None

        return self._read_int_file(root / "cpuacct" / "cpuacct.usage")

    def _read_int_file(self, path: Path) -> int | None:
        try:
            if path.exists():
                return _safe_int(path.read_text(encoding="utf-8", errors="ignore").strip())
        except Exception:
            return None
        return None

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
