"""Exercise copied shell code with fake package/git/python tools on Linux.

No real package installation, Git/network access, or Proxmox setup is performed.
Run on a Proxmox host with the generated command as JSON on stdin.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

command=json.load(sys.stdin)['command']
bash=shutil.which('bash')
assert bash and Path('/etc/pve').is_dir()
for scenario in ('missing_git','missing_python','already_installed','apt_failure','clone_failure'):
    with tempfile.TemporaryDirectory(prefix='fh-bootstrap-test-') as temporary:
        root=Path(temporary);bin_dir=root/'bin';bin_dir.mkdir();fixtures=root/'fixtures';fixtures.mkdir()
        log=root/'log'
        for name in ('bash','mktemp','rm','id'):
            (bin_dir/name).symlink_to(shutil.which(name))
        def script(path,text):
            path.write_text('#!/bin/sh\n'+text);path.chmod(0o755)
        script(fixtures/'git','echo git >> "$BOOTSTRAP_LOG"\n'
            'echo "dir=$5" >> "$BOOTSTRAP_LOG"\n'
            '[ "$SCENARIO" != clone_failure ] || exit 42\n'
            '/bin/mkdir -p "$5/scripts"\n: > "$5/scripts/setup_vpn_tun.py"\n')
        script(fixtures/'python3','echo python >> "$BOOTSTRAP_LOG"\n[ -f "$1" ]\n')
        script(bin_dir/'apt-get','echo "apt:$1" >> "$BOOTSTRAP_LOG"\n'
            '[ "$SCENARIO" != apt_failure ] || exit 42\n'
            'if [ "$1" = install ]; then\n'
            ' /bin/cp "$FIXTURES/git" "$TEST_BIN/git"\n'
            ' /bin/cp "$FIXTURES/python3" "$TEST_BIN/python3"\nfi\n')
        if scenario not in ('missing_git','apt_failure','clone_failure'):shutil.copy(fixtures/'git',bin_dir/'git')
        if scenario!='missing_python':shutil.copy(fixtures/'python3',bin_dir/'python3')
        env={**os.environ,'PATH':str(bin_dir),'SCENARIO':scenario,'BOOTSTRAP_LOG':str(log),
             'FIXTURES':str(fixtures),'TEST_BIN':str(bin_dir)}
        result=subprocess.run([bash,'-c',command],env=env,capture_output=True,text=True,timeout=20)
        entries=log.read_text().splitlines() if log.exists() else []
        if scenario in ('apt_failure','clone_failure'):
            assert result.returncode!=0 and 'python' not in entries
        else:
            assert result.returncode==0 and 'python' in entries
            if scenario=='already_installed':assert not any(e.startswith('apt:') for e in entries)
            else:assert 'apt:update' in entries and 'apt:install' in entries
        for entry in entries:
            if entry.startswith('dir='):assert not Path(entry[4:]).exists()
        print('PASS '+scenario+': correct dependencies, failure handling and temporary cleanup',flush=True)
