"""Execute the wizard's generated shell with a fake pct; no host changes."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest


class NfsMountCommandsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        git_bash = Path('C:/Program Files/Git/bin/bash.exe')
        cls.bash = str(git_bash) if git_bash.exists() else shutil.which('bash')
        if not cls.bash or not shutil.which('node'):
            raise unittest.SkipTest('Requires Bash and Node.js')
        template = (Path(__file__).resolve().parents[1] / 'templates/wizard.html').read_text(encoding='utf-8')
        cls.function = template[template.index('function nfsLxcMountCommands('):template.index('function renderNfsCommands(')]

    def run_commands(self, config, target='/mnt/nas', fail_config=False):
        script = subprocess.check_output([
            'node', '-e', self.function + '\nconsole.log(nfsLxcMountCommands("100", ' + json.dumps(target) + ').join("\\n"));'
        ], text=True)
        fake = '''pct() {
  if [ "$1" = config ]; then
    [ "$FAIL_CONFIG" = 0 ] || return 1
    printf '%s\\n' "$PCT_CONFIG"
  else
    printf 'CALL'; printf ' <%s>' "$@"; printf '\\n'
  fi
}
export -f pct
'''
        env = dict(os.environ, PCT_CONFIG=config, FAIL_CONFIG='1' if fail_config else '0')
        return subprocess.run([self.bash], input=fake + script, text=True, capture_output=True, env=env)

    def test_occupied_slots_are_preserved(self):
        result = self.run_commands('mp0: /disk,mp=/data\nmp2: /other,mp=/other')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('CALL <set> <100> <-mp1> </mnt/nas,mp=/mnt/nas>', result.stdout)
        self.assertIn('CALL <reboot> <100>', result.stdout)

    def test_empty_config_uses_first_slot(self):
        self.assertIn('<-mp0>', self.run_commands('').stdout)

    def test_existing_mount_reused_even_after_free_slot(self):
        result = self.run_commands('mp3: /mnt/nas,mp=/mnt/nas,ro=1,backup=0')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('CALL', result.stdout)

    def test_conflicting_target_stops_without_changes(self):
        result = self.run_commands('mp0: /different,mp=/mnt/nas')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('CALL', result.stdout)

    def test_full_config_stops_without_changes(self):
        result = self.run_commands('\n'.join(f'mp{i}: /disk{i},mp=/data{i}' for i in range(256)))
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('CALL', result.stdout)

    def test_config_failure_stops_without_changes(self):
        result = self.run_commands('', fail_config=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('CALL', result.stdout)


if __name__ == '__main__':
    unittest.main()
