import os
import re
from pathlib import Path


_NUMBERED_GPU = re.compile(r"^nvidia\d+$")
_CAPABILITY_DEVICE = re.compile(r"^nvidia-cap\d+$")
_CORE_DEVICES = (
    "nvidiactl",
    "nvidia-uvm",
    "nvidia-uvm-tools",
    "nvidia-modeset",
)


def _natural_device_key(path: Path) -> tuple[int, int, str]:
    gpu_match = _NUMBERED_GPU.fullmatch(path.name)
    if gpu_match:
        return (0, int(path.name.removeprefix("nvidia")), path.name)
    if path.name in _CORE_DEVICES:
        return (1, _CORE_DEVICES.index(path.name), path.name)
    capability_match = _CAPABILITY_DEVICE.fullmatch(path.name)
    if capability_match:
        return (2, int(path.name.removeprefix("nvidia-cap")), path.name)
    return (3, 0, path.as_posix())


def nvidia_device_root() -> Path:
    explicit_root = str(os.environ.get("NVIDIA_DEVICE_ROOT", "")).strip()
    if explicit_root:
        return Path(explicit_root)

    host_proc_root = Path(os.environ.get("HOST_PROC_ROOT", "/host/proc"))
    host_device_root = host_proc_root / "1" / "root" / "dev"
    if host_device_root.is_dir():
        return host_device_root
    return Path("/dev")


def discover_nvidia_devices(device_root: Path | None = None) -> list[str]:
    root = device_root or nvidia_device_root()
    try:
        if not root.is_dir():
            return []
        root_entries = list(root.glob("nvidia*"))
    except OSError:
        return []

    devices = [path for path in root_entries if path.name in _CORE_DEVICES]
    devices.extend(path for path in root_entries if _NUMBERED_GPU.fullmatch(path.name))

    caps_root = root / "nvidia-caps"
    try:
        if caps_root.is_dir():
            devices.extend(
                path for path in caps_root.glob("nvidia-cap*")
                if _CAPABILITY_DEVICE.fullmatch(path.name)
            )
    except OSError:
        pass

    unique_devices = sorted(set(devices), key=_natural_device_key)
    return ["/dev/" + path.relative_to(root).as_posix() for path in unique_devices]


def render_compose_override(service_name: str, devices: list[str]) -> str:
    service = str(service_name or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", service):
        raise ValueError("Ugyldigt GPU-service-navn")
    if not devices:
        raise ValueError("Ingen NVIDIA-enheder fundet")

    lines = ["services:", f"  {service}:", "    devices:"]
    for device in devices:
        if not re.fullmatch(r"/dev/nvidia(?:\d+|ctl|-uvm|-uvm-tools|-modeset|-caps/nvidia-cap\d+)", device):
            raise ValueError(f"Ugyldig NVIDIA-enhed: {device}")
        lines.append(f'      - "{device}:{device}"')
    return "\n".join(lines) + "\n"
