import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from services.nvidia_devices import discover_nvidia_devices, nvidia_device_root, render_compose_override


class NvidiaDeviceTests(unittest.TestCase):
    def test_discovers_single_gpu_and_optional_devices(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            for name in ("nvidia0", "nvidiactl", "nvidia-uvm", "nvidia-uvm-tools"):
                (root / name).touch()

            self.assertEqual(
                discover_nvidia_devices(root),
                [
                    "/dev/nvidia0",
                    "/dev/nvidiactl",
                    "/dev/nvidia-uvm",
                    "/dev/nvidia-uvm-tools",
                ],
            )

    def test_discovers_all_gpus_and_capability_devices(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            for name in ("nvidia0", "nvidia2", "nvidia10", "nvidiactl", "nvidia-modeset"):
                (root / name).touch()
            caps = root / "nvidia-caps"
            caps.mkdir()
            (caps / "nvidia-cap1").touch()
            (caps / "nvidia-cap2").touch()
            (caps / "ignored").touch()

            devices = discover_nvidia_devices(root)

            self.assertIn("/dev/nvidia0", devices)
            self.assertIn("/dev/nvidia2", devices)
            self.assertIn("/dev/nvidia10", devices)
            self.assertIn("/dev/nvidia-caps/nvidia-cap1", devices)
            self.assertIn("/dev/nvidia-caps/nvidia-cap2", devices)
            self.assertNotIn("/dev/nvidia1", devices)

    def test_returns_empty_for_missing_device_root(self):
        with tempfile.TemporaryDirectory() as tempdir:
            self.assertEqual(discover_nvidia_devices(Path(tempdir) / "missing"), [])

    def test_prefers_explicit_device_root(self):
        with patch.dict("os.environ", {"NVIDIA_DEVICE_ROOT": "/host/dev"}):
            self.assertEqual(nvidia_device_root(), Path("/host/dev"))

    def test_returns_empty_when_device_root_cannot_be_read(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with patch.object(Path, "glob", side_effect=PermissionError("denied")):
                self.assertEqual(discover_nvidia_devices(Path(tempdir)), [])

    def test_renders_all_detected_devices_for_gpu_service(self):
        override = render_compose_override(
            "fjordlens-ai",
            [
                "/dev/nvidia0",
                "/dev/nvidia1",
                "/dev/nvidiactl",
                "/dev/nvidia-caps/nvidia-cap1",
            ],
        )

        self.assertIn("fjordlens-ai:", override)
        self.assertIn('"/dev/nvidia0:/dev/nvidia0"', override)
        self.assertIn('"/dev/nvidia1:/dev/nvidia1"', override)
        self.assertIn('"/dev/nvidia-caps/nvidia-cap1:/dev/nvidia-caps/nvidia-cap1"', override)

    def test_rejects_empty_or_unsafe_override_values(self):
        with self.assertRaises(ValueError):
            render_compose_override("fjordlens-ai", [])
        with self.assertRaises(ValueError):
            render_compose_override("fjordlens-ai\nother", ["/dev/nvidia0"])
        with self.assertRaises(ValueError):
            render_compose_override("fjordlens-ai", ["/dev/null"])


if __name__ == "__main__":
    unittest.main()
