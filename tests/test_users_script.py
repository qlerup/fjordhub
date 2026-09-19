import json
import shutil
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader


@unittest.skipUnless(shutil.which('node'), 'Node.js is required for browser-script tests')
class UsersScriptTests(unittest.TestCase):
    def test_edit_buttons_and_validation_reopen(self):
        env = Environment(loader=FileSystemLoader(Path(__file__).resolve().parents[1] / 'templates'))
        template = env.get_template('users.html')
        users = [dict(id=1, username='admin', role='admin'), dict(id=2, username='member')]
        for reopen_id in (None, 1, 2):
            with self.subTest(reopen_id=reopen_id):
                context = template.new_context(dict(
                    users=users, current_user=SimpleNamespace(id=1),
                    edit_error=bool(reopen_id), edit_user_id=reopen_id,
                ))
                script = ''.join(template.blocks['scripts'](context)).split('<script>')[1].split('</script>')[0]
                harness = r'''
const assert = require('node:assert/strict');
const vm = require('node:vm');
const elements = new Map();
function element(id) {
  if (!elements.has(id)) {
    const classes = new Set();
    elements.set(id, {style: {}, value: '', dataset: {}, listeners: {},
      classList: {add: c => classes.add(c), remove: c => classes.delete(c), contains: c => classes.has(c)},
      addEventListener(type, fn) { this.listeners[type] = fn; }, focus() {}});
  }
  return elements.get(id);
}
const buttons = [1, 2].map(id => {const btn = element('button-' + id); btn.dataset.editUserId = String(id); return btn;});
const document = {getElementById: element, addEventListener() {},
  querySelectorAll: selector => selector === '[data-edit-user-id]' ? buttons : []};
vm.runInNewContext(SCRIPT, {document});
function check(id) {
  assert.equal(element('edit-modal').classList.contains('is-open'), true);
  assert.equal(element('edit-form').action, '/users/' + id + '/edit');
  assert.equal(element('edit-username').value, id === 1 ? 'admin' : 'member');
  assert.equal(element('edit-current-password-wrap').style.display, id === 1 ? '' : 'none');
  element('cancel-edit-modal').listeners.click();
  assert.equal(element('edit-modal').classList.contains('is-open'), false);
}
if (REOPEN) check(REOPEN);
for (const btn of buttons) {btn.listeners.click.call(btn); check(Number(btn.dataset.editUserId));}
'''
                harness = 'const SCRIPT = ' + json.dumps(script) + '; const REOPEN = ' + json.dumps(reopen_id) + ';\n' + harness
                result = subprocess.run(['node', '-e', harness], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
