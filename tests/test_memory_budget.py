import json
import ast
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from flask import Flask, request, jsonify
from services.fjordlens_memory import budget_from_resources
from services.install_state import InstallState
from services.update_manager import UpdateManager

GIB = 1024**3


class MemoryBudgetTests(unittest.TestCase):
    def test_budget_endpoint_requires_fjordlens_key_and_registered_install(self):
        source = ast.parse((Path(__file__).resolve().parents[1]/'app.py').read_text(encoding='utf-8-sig'))
        node = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == 'api_fjordlens_memory_budget')
        node.decorator_list = []
        auth, install, monitor = Mock(), Mock(), Mock()
        env = dict(request=request, jsonify=jsonify, _auth=auth, _install_state=install,
                   resource_monitor=monitor, _apps_with_install_dirs=lambda: [])
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'app.py', 'exec'), env)
        app = Flask(__name__)
        with app.test_request_context(headers={'X-Hub-Key': 'test-key'}):
            auth.verify_hub_key.return_value = False
            self.assertEqual(env[node.name]()[1], 403)
            monitor.collect.assert_not_called()
            auth.verify_hub_key.assert_called_with('fjordlens', 'test-key')
            auth.verify_hub_key.return_value = True
            install.get_install_dir.return_value = None
            self.assertEqual(env[node.name]()[1], 404)
            install.get_install_dir.return_value = '/apps/fjordlens'
            monitor.collect.return_value = self.sample(2)
            monitor._system_summary.return_value = self.sample(3)['system']
            response = env[node.name]()
            self.assertEqual(response.get_json()['budget_bytes'], 5*GIB)
            # After AI startup, Docker working sets can exceed Proxmox's
            # cache-adjusted total. This must still return a fresh HTTP 200.
            snapshot = self.sample(0, own=3)
            snapshot['system']['memory_usage'] = 2*GIB
            monitor.collect.return_value = snapshot
            monitor._system_summary.return_value = dict(snapshot['system'])
            response = env[node.name]()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()['used_bytes'], 2*GIB)

    def sample(self, other, own=3):
        return dict(ok=True, system=dict(available=True, memory_limit=10*GIB, memory_usage=(other+own)*GIB),
                    apps=[dict(id='fjordlens', memory_usage=own*GIB, containers=[dict(error='')])])

    def test_budget_tracks_others_without_counting_lens_twice(self):
        for other, expected in [(2, 6), (3, 5), (1, 7)]:
            result = budget_from_resources(self.sample(other))
            self.assertEqual(result['budget_bytes'], expected*GIB)
        self.assertEqual(budget_from_resources(self.sample(2, own=5))['budget_bytes'], 6*GIB)

    def test_incomplete_or_inconsistent_measurements_fail_closed(self):
        for kind in ('unavailable', 'container_error', 'over_limit', 'negative', 'invalid_own'):
            sample = self.sample(2)
            if kind == 'unavailable':
                sample['system']['available'] = False
            elif kind == 'container_error':
                sample['apps'][0]['containers'][0]['error'] = 'Docker unavailable'
            elif kind == 'over_limit':
                sample['system']['memory_usage'] = 11*GIB
            elif kind == 'negative':
                sample['system']['memory_usage'] = -1
            else:
                sample['apps'][0]['memory_usage'] = -1
            with self.assertRaises(RuntimeError):
                budget_from_resources(sample)

    def test_docker_working_set_can_exceed_proxmox_usage(self):
        sample = self.sample(0, own=3)
        sample['system']['memory_usage'] = 2*GIB
        result = budget_from_resources(sample)
        self.assertTrue(result['ok'])
        self.assertEqual(result['used_bytes'], 2*GIB)
        self.assertEqual(result['total_bytes'], 10*GIB)
        self.assertEqual(result['other_bytes'], 0)
        self.assertEqual(result['budget_bytes'], 8*GIB)

    def test_up_to_date_installation_still_gets_activation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manager = UpdateManager(InstallState(root/'state.json'))
            with patch.object(manager, '_git_info', return_value={'ok': True, 'update_available': False}), \
                 patch.object(manager, 'fjordlens_memory_needs_activation', return_value=True), \
                 patch.object(manager, '_activate_fjordlens_memory') as activate:
                manager._run_update({'id': 'fjordlens'}, root)
            activate.assert_called_once_with(root)

    def test_other_apps_are_not_activated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manager = UpdateManager(InstallState(root/'state.json'))
            with patch.object(manager, '_git_info', return_value={'ok': True, 'update_available': False}), \
                 patch.object(manager, '_activate_fjordlens_memory') as activate:
                manager._run_update({'id': 'other'}, root)
            activate.assert_not_called()

    def test_activation_checks_real_limits_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'updater_service').mkdir()
            (root/'updater_service/memory_governor.py').write_text('HUB_MEMORY_PROTOCOL = 2')
            manager = UpdateManager(InstallState(root/'state.json'))
            containers = [dict(Name='/'+name, Config={'Labels': {'io.fjordlens.memory-managed': '1', 'io.fjordlens.memory-protocol': '2'}},
                               HostConfig={'Memory': GIB, 'MemorySwap': GIB})
                          for name in ('fjordlens', 'fjordlens-ai', 'fjordlens-convert', 'fjordlens-updater')]
            def result():
                return subprocess.CompletedProcess([], 0, stdout=json.dumps(containers))
            with patch.object(manager, '_run', side_effect=lambda *a, **kw: result()):
                self.assertFalse(manager.fjordlens_memory_needs_activation(root))
                containers[1]['HostConfig']['Memory'] = 0
                self.assertTrue(manager.fjordlens_memory_needs_activation(root))
                containers[1]['HostConfig']['Memory'] = GIB
                containers[3]['Config']['Labels']['io.fjordlens.memory-protocol'] = '1'
                self.assertTrue(manager.fjordlens_memory_needs_activation(root))
