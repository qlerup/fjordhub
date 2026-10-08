"""A failed build must deliver its final output to the dashboard poller."""
import tempfile
import json
import shutil
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from services.install_state import InstallState
from services.update_manager import UpdateManager


class UpdateTerminalLogTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node.js is required')
    def test_modal_shows_error_as_text(self):
        source = (Path(__file__).resolve().parents[1] / 'static/app.js').read_text(encoding='utf-8')
        function = source.split('function finishUpdateModal(', 1)[1].split('\n}\n', 1)[0]
        script = 'function finishUpdateModal(' + function + '\n}\n'
        harness = '''
const assert = require('node:assert/strict');
let _terminalDone = false;
const elements = {};
for (const id of ['update-log-footer', 'update-log-title', 'update-log-done']) {
  elements[id] = {textContent: 'Opdaterer FjordVPN', style: {}};
}
const document = {getElementById: id => elements[id]};
eval(SCRIPT);
finishUpdateModal('failed', 'registry <unavailable>');
assert(elements['update-log-footer'].textContent.includes('registry <unavailable>'));
assert.equal(elements['update-log-footer'].className, 'terminal-footer err');
assert.equal(_terminalDone, true);
finishUpdateModal('up_to_date', 'old error');
assert(!elements['update-log-footer'].textContent.includes('old error'));
'''
        result = subprocess.run(['node', '-e', 'const SCRIPT = ' + json.dumps(script) + ';\n' + harness],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = InstallState(self.root)
        self.state.register('fjordvpn', str(self.root))
        self.manager = UpdateManager(self.state)
        self.app = {'id': 'fjordvpn'}

    def test_final_build_error_survives_transition_from_running_to_cached(self):
        manager = self.manager
        manager._set_job('fjordvpn', {'running': True, 'state': 'updating', 'log': []})
        manager._append_job_log('fjordvpn', '#3 load metadata for python:3.13-alpine')
        running = manager.get_status(self.app)
        manager._append_job_log('fjordvpn', 'ERROR: failed to resolve source metadata')
        failure = {'running': False, 'state': 'failed', 'error': 'docker compose build fejlede'}
        manager._set_cache('fjordvpn', failure)
        manager._set_job('fjordvpn', failure)
        result = manager.get_all_statuses([self.app])['fjordvpn']
        self.assertEqual(result['state'], 'failed')
        self.assertFalse(result['running'])
        self.assertEqual(result['log'][-1], 'ERROR: failed to resolve source metadata')
        self.assertEqual(len(running['log']), 1)
        result['log'].clear()
        self.assertEqual(len(manager.get_log('fjordvpn')), 2)

    def test_success_delivers_final_line_and_refresh_preserves_log(self):
        manager = self.manager
        manager._set_job('fjordvpn', {'running': False, 'state': 'up_to_date', 'log': ['Opdatering færdig.']})
        manager._set_cache('fjordvpn', {'state': 'up_to_date', 'running': False})
        self.assertEqual(manager.get_status(self.app)['log'], ['Opdatering færdig.'])
        with patch.object(manager, '_git_info', return_value={'state': 'up_to_date'}):
            self.assertEqual(manager.get_status(self.app, fetch=True)['log'], ['Opdatering færdig.'])

    def test_real_update_failure_delivers_process_output_and_exception(self):
        manager = self.manager
        manager._set_job('fjordvpn', {'running': True, 'state': 'updating', 'log': []})
        info = dict(ok=True, dirty=False, update_available=True, branch='main',
                    current_rev='old', remote_rev='new')
        def command(app_id, args, **kwargs):
            if args[:3] == ['docker', 'compose', 'build']:
                manager._append_job_log(app_id, 'ERROR: registry unavailable')
                return 1
            return 0
        with patch.object(manager, '_git_info', return_value=info), \
             patch.object(manager, '_changed_paths', return_value=['app.py']), \
             patch.object(manager, '_compose_build_services_for_changes', return_value=['app']), \
             patch.object(manager, '_run_logged', side_effect=command):
            manager._run_update(self.app, self.root)
        result = manager.get_status(self.app)
        self.assertEqual(result['state'], 'failed')
        self.assertIn('ERROR: registry unavailable', result['log'])
        self.assertEqual(result['log'][-1], 'Fejl: docker compose build fejlede')
