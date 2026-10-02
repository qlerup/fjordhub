import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize('installed,candidate,install_exit,success,installs', [
    (True, '550.163.01-2', 0, True, False),
    (False, '550.163.01-2', 0, True, True),
    (False, '535.1-1', 0, False, False),
    (False, '550.163.01-2', 1, False, True),
])
def test_host_opencl_installs_only_matching_driver(tmp_path, installed, candidate, install_exit, success, installs):
    bash = 'C:/Program Files/Git/bin/bash.exe' if os.name == 'nt' else shutil.which('bash')
    if not bash or not Path(bash).is_file():
        pytest.skip('Bash needed for generated host-command tests')
    if installed:
        (tmp_path / 'libnvidia-opencl.so.550.163.01').touch()
    # Every privileged/external command is replaced with an in-process shell mock.
    mocks = f'''
nvidia-smi() {{ echo 550.163.01; }}
apt-cache() {{ echo 'nvidia-opencl-icd | {candidate} | test repository'; }}
apt-get() {{
  echo "$*" >> calls
  if [ "$1" = install ]; then
    [ {install_exit} = 0 ] || return 1
    touch libnvidia-opencl.so.550.163.01
  fi
}}
ldconfig() {{
  if [ "$1" = -p ] && [ -f libnvidia-opencl.so.550.163.01 ]; then
    echo "libnvidia-opencl.so.1 => $PWD/libnvidia-opencl.so.550.163.01"
  fi
  return 0
}}
'''
    script = Path(__file__).parents[1] / 'templates/partials/gpu_opencl.sh'
    result = subprocess.run([bash, '-s'], input=mocks + script.read_text(), cwd=tmp_path,
                            capture_output=True, text=True, timeout=10)
    assert (result.returncode == 0) == success, result.stdout + result.stderr
    calls = (tmp_path / 'calls').read_text() if (tmp_path / 'calls').exists() else ''
    assert ('install ' in calls) == installs
    if installs:
        assert '--no-remove --no-install-recommends nvidia-opencl-icd=550.163.01-2' in calls
