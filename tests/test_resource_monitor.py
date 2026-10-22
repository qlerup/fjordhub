import unittest
from types import SimpleNamespace
from unittest.mock import patch

from services.resource_monitor import ResourceMonitor, _cpu_percent


def _raw_stats() -> dict:
    return {
        "cpu_stats": {
            "cpu_usage": {"total_usage": 400_000_000},
            "system_cpu_usage": 20_000_000_000,
            "online_cpus": 4,
        },
        "precpu_stats": {
            "cpu_usage": {"total_usage": 200_000_000},
            "system_cpu_usage": 10_000_000_000,
        },
        "memory_stats": {
            "usage": 104_857_600,
            "limit": 1_073_741_824,
            "stats": {"inactive_file": 4_857_600},
        },
        "networks": {"eth0": {"rx_bytes": 1000, "tx_bytes": 2000}},
        "blkio_stats": {
            "io_service_bytes_recursive": [
                {"op": "read", "value": 10},
                {"op": "write", "value": 20},
            ]
        },
    }


class FakeContainer:
    """Efterligner docker-py 7.x: decode + stream=False kaster InvalidArgument."""

    def __init__(self, container_id: str = "abc123", name: str = "demo"):
        self.id = container_id
        self.name = name
        self.status = "running"
        self.labels = {}

    def stats(self, decode=None, stream=True, one_shot=None):
        if not stream and decode:
            raise ValueError(
                "decode is only available in conjunction with stream=True"
            )
        return _raw_stats()


class ResourceMonitorCpuTests(unittest.TestCase):
    def setUp(self):
        self.monitor = ResourceMonitor(SimpleNamespace(client=None))

    def test_cpu_percent_from_docker_deltas(self):
        # delta 0.2s CPU af 10s system pa 4 kerner = 8%
        self.assertAlmostEqual(_cpu_percent(_raw_stats()), 8.0)

    def test_container_stats_include_cpu_percent(self):
        container = FakeContainer()
        with patch.object(self.monitor, "_fill_from_docker_stats_cli") as cli_fallback:
            stats = self.monitor._stats_by_container([container])

        snapshot = stats[container.id]
        self.assertIsNone(snapshot["error"])
        self.assertEqual(snapshot["cpu_percent"], 8.0)
        self.assertEqual(snapshot["net_rx"], 1000)
        self.assertEqual(snapshot["block_write"], 20)
        cli_fallback.assert_called_once()

    def test_stopped_containers_get_empty_snapshot(self):
        container = FakeContainer()
        container.status = "exited"
        with patch.object(self.monitor, "_fill_from_docker_stats_cli"):
            stats = self.monitor._stats_by_container([container])
        self.assertEqual(stats[container.id]["cpu_percent"], 0.0)
        self.assertEqual(stats[container.id]["status"], "exited")


class ResourceMonitorVpnHealthTests(unittest.TestCase):
    def setUp(self):
        self.containers = [FakeContainer(str(i), name) for i, name in enumerate((
            'fjordvpn', 'fjordvpn-one-vpn', 'fjordvpn-one-relay',
            'fjordvpn-two-vpn', 'fjordvpn-two-relay'))]
        self.helper = FakeContainer('helper', 'fjordvpn-hub-vpn-image-1')
        self.helper.status = 'exited'
        self.helper.labels = {'com.docker.compose.project':'fjordvpn-hub',
                              'com.docker.compose.service':'vpn-image'}
        self.helper.attrs = {'State': {'ExitCode':0},
                             'Config': {'Entrypoint':['/bin/sh','-c','exit 0']}}
        self.containers.append(self.helper)
        self.monitor = ResourceMonitor(SimpleNamespace(client=SimpleNamespace(
            containers=SimpleNamespace(list=lambda **kwargs:self.containers))))

    def snapshot(self):
        stats = {c.id:self.monitor._container_snapshot(c, None) for c in self.containers}
        with patch.object(self.monitor,'_capacity',return_value={'cpus':4,'memory_total':1024}), patch.object(
                self.monitor,'_system_summary',return_value={'available':False}), patch.object(
                self.monitor,'_stats_by_container',return_value=stats):
            return self.monitor.collect([{'id':'fjordvpn','name':'FjordVPN','container_name':'fjordvpn'}])

    def test_successful_image_preparation_does_not_mark_app_offline(self):
        snapshot = self.snapshot()
        group = snapshot['apps'][0]
        self.assertEqual((group['running_count'],group['container_count']),(5,5))
        self.assertNotIn(self.helper.name,[c['name'] for c in group['containers']])
        self.assertEqual(snapshot['hub']['container_count'],5)

    def test_failed_or_unknown_preparation_still_reports_unhealthy(self):
        for state in ({'ExitCode':1},{},{'ExitCode':0,'OOMKilled':True},{'ExitCode':0,'Error':'failure'}):
            with self.subTest(state=state):
                self.helper.attrs['State']=state
                group=self.snapshot()['apps'][0]
                self.assertEqual((group['running_count'],group['container_count']),(5,6))

    def test_stopped_real_service_is_not_hidden_even_after_clean_exit(self):
        for container in self.containers[:5]:
            with self.subTest(container=container.name):
                container.status='exited'
                container.attrs={'State':{'ExitCode':0}}
                group=self.snapshot()['apps'][0]
                self.assertEqual((group['running_count'],group['container_count']),(4,5))
                container.status='running'

    def test_unrecognized_job_or_application_is_not_ignored(self):
        self.assertFalse(self.monitor._completed_vpn_image('other-app',self.helper))
        self.helper.attrs['Config']['Entrypoint']=['/gluetun-entrypoint']
        group=self.snapshot()['apps'][0]
        self.assertEqual((group['running_count'],group['container_count']),(5,6))


if __name__ == "__main__":
    unittest.main()
