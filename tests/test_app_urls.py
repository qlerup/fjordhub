import os
import tempfile
import unittest
from pathlib import Path

import app as fjordhub
from services.install_state import InstallState

FIB_TRIE = """\
Main:
  +-- 0.0.0.0/0 3 0 5
     +-- 10.10.0.0/24 2 0 2
        |-- 10.10.0.50
           /32 host LOCAL
        |-- 10.10.0.255
           /32 link BROADCAST
     +-- 172.18.0.0/16 2 0 2
        |-- 172.18.0.1
           /32 host LOCAL
     |-- 127.0.0.1
        /32 host LOCAL
"""

# Default route via 10.10.0.1 (0100000A little-endian) på eth0
ROUTE = """\
Iface\tDestination\tGateway\tFlags\tRefCnt\tUse\tMetric\tMask\tMTU\tWindow\tIRTT
eth0\t00000000\t0100000A\t0003\t0\t0\t0\t00000000\t0\t0\t0
eth0\t00000A0A\t00000000\t0001\t0\t0\t0\t00FFFFFF\t0\t0\t0
"""

# Sådan ser containerens egen netns ud: docker-bridge 172.18.0.x
CONTAINER_FIB_TRIE = """\
Main:
  +-- 0.0.0.0/0 3 0 5
     +-- 172.18.0.0/16 2 0 2
        |-- 172.18.0.5
           /32 host LOCAL
     |-- 127.0.0.1
        /32 host LOCAL
"""

# Default route via 172.18.0.1 (010012AC little-endian) på eth0
CONTAINER_ROUTE = """\
Iface\tDestination\tGateway\tFlags\tRefCnt\tUse\tMetric\tMask\tMTU\tWindow\tIRTT
eth0\t00000000\t010012AC\t0003\t0\t0\t0\t00000000\t0\t0\t0
"""


class AppUrlTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.previous_state = fjordhub._install_state
        fjordhub._install_state = InstallState(Path(self.tempdir.name))

    def tearDown(self):
        fjordhub._install_state = self.previous_state
        self.tempdir.cleanup()
        os.environ.pop("HOST_PROC_ROOT", None)
        os.environ.pop("HOST_LAN_IP", None)

    def _write_fake_proc(self, net_subdir="net", fib_trie=FIB_TRIE, route=ROUTE):
        proc_root = Path(self.tempdir.name) / "proc"
        net_dir = proc_root / net_subdir
        net_dir.mkdir(parents=True, exist_ok=True)
        (net_dir / "fib_trie").write_text(fib_trie, encoding="utf-8")
        (net_dir / "route").write_text(route, encoding="utf-8")
        os.environ["HOST_PROC_ROOT"] = str(proc_root)

    def test_normalizes_domains_and_private_addresses(self):
        self.assertEqual(
            fjordhub._normalize_external_url("photos.example.com"),
            "https://photos.example.com",
        )
        self.assertEqual(
            fjordhub._normalize_external_url("10.10.0.238:9080"),
            "http://10.10.0.238:9080",
        )

    def test_rejects_credentials_query_and_invalid_port(self):
        invalid = (
            "https://user:password@example.com",
            "https://example.com?token=secret",
            "https://example.com:99999",
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                fjordhub._normalize_external_url(value)

    def test_saved_url_is_authoritative(self):
        fjordhub._install_state.set_external_url("demo", "https://demo.example.com")
        with fjordhub.app.test_request_context("/", base_url="https://hub.example.com"):
            self.assertEqual(
                fjordhub._external_app_url({"id": "demo", "default_port": 8080}),
                "https://demo.example.com",
            )

    def test_fallback_uses_installed_app_port(self):
        install_dir = Path(self.tempdir.name) / "demo"
        install_dir.mkdir()
        (install_dir / ".env").write_text("APP_PORT=4321\n", encoding="utf-8")
        fjordhub._install_state.register("demo", str(install_dir))
        with fjordhub.app.test_request_context("/", base_url="http://10.10.0.10"):
            candidates = fjordhub._external_app_url_candidates({"id": "demo", "default_port": 8080})
        self.assertIn("http://10.10.0.10:4321", candidates)

    def test_host_lan_ip_prefers_gateway_subnet(self):
        self._write_fake_proc()
        self.assertEqual(fjordhub._host_lan_ip(), "10.10.0.50")

    def test_host_lan_ip_reads_host_netns_not_container(self):
        # /proc/net i containeren viser docker-bridgen (172.18.0.x);
        # hostens rigtige netværk ligger i <proc>/1/net og skal vinde
        self._write_fake_proc("net", CONTAINER_FIB_TRIE, CONTAINER_ROUTE)
        self._write_fake_proc("1/net", FIB_TRIE, ROUTE)
        self.assertEqual(fjordhub._host_lan_ip(), "10.10.0.50")

    def test_host_lan_ip_env_override(self):
        os.environ["HOST_LAN_IP"] = "10.10.0.99"
        self.assertEqual(fjordhub._host_lan_ip(), "10.10.0.99")

    def test_host_lan_ip_missing_proc_gives_empty(self):
        os.environ["HOST_PROC_ROOT"] = str(Path(self.tempdir.name) / "findes-ikke")
        self.assertEqual(fjordhub._host_lan_ip(), "")

    def test_fallback_url_uses_lan_ip_behind_tunnel_domain(self):
        self._write_fake_proc()
        with fjordhub.app.test_request_context("/", base_url="https://hub.example.dk"):
            self.assertEqual(
                fjordhub._fallback_app_url({"id": "demo", "default_port": 9090}),
                "http://10.10.0.50:9090",
            )
            candidates = fjordhub._external_app_url_candidates({"id": "demo", "default_port": 9090})
        self.assertEqual(candidates[0], "http://10.10.0.50:9090")

    def test_fallback_url_without_lan_ip_uses_request_host(self):
        os.environ["HOST_PROC_ROOT"] = str(Path(self.tempdir.name) / "findes-ikke")
        with fjordhub.app.test_request_context("/", base_url="http://10.10.0.10"):
            self.assertEqual(
                fjordhub._fallback_app_url({"id": "demo", "default_port": 9090}),
                "http://10.10.0.10:9090",
            )

    def test_dashboard_local_address_uses_installed_port(self):
        install_dir = Path(self.tempdir.name) / "demo"
        install_dir.mkdir()
        (install_dir / ".env").write_text("APP_PORT=4321\n", encoding="utf-8")
        fjordhub._install_state.register("demo", str(install_dir))
        os.environ["HOST_LAN_IP"] = "10.10.0.50"

        with fjordhub.app.test_request_context("/", base_url="https://hub.example.com"):
            local_url = fjordhub._fallback_app_url({"id": "demo", "default_port": 8080})

        self.assertEqual(local_url, "http://10.10.0.50:4321")


if __name__ == "__main__":
    unittest.main()
