import json
import subprocess
from pathlib import Path
from unittest.mock import Mock,patch

import pytest
from services.installer import Installer


def test_registry_offers_same_gpu_helper_and_dedicated_service():
    data=json.loads((Path(__file__).resolve().parents[1]/'app_registry/fjordseed.json').read_text(encoding='utf-8'))
    assert data['gpu_service']==data['gpu_video_service']=='converter'
    assert data['gpu_video'] and data['gpu_nvenc_check']
    gpu=next(step for step in data['setup_steps'] if step.get('gpu_helper'))
    assert gpu['fields'][0]['key']=='ENABLE_GPU_COMPOSE'


@pytest.mark.parametrize('exit_code',[0,1])
def test_seed_install_requires_real_nvenc_hevc_test(tmp_path,exit_code):
    (tmp_path/'.git').mkdir()
    state=Mock();installer=Installer(state)
    with patch.object(installer,'_resolve_env_values',return_value={'ENABLE_GPU_COMPOSE':'1'}), \
         patch('services.installer.probe_gpu',return_value={'ok':True}), \
         patch('services.installer.discover_nvidia_devices',return_value=['/dev/nvidia0','/dev/nvidiactl']), \
         patch('services.installer.docker_desktop_gpu',return_value=False), \
         patch('services.installer.subprocess.Popen',return_value=Mock(stdout=[],returncode=0)), \
         patch('services.installer.subprocess.run',side_effect=[
             subprocess.CompletedProcess([],0,'updated',''),subprocess.CompletedProcess([],0,'',''),
             subprocess.CompletedProcess([],exit_code,'','NVEncC failed' if exit_code else '')]) as run:
        installer._run({'id':'fjordseed','name':'FjordSeed','gpu_service':'converter','gpu_video':True,'gpu_nvenc_check':True},{},tmp_path)
    assert run.call_args.args[0][-1]=='--check-gpu'
    assert 'converter' in run.call_args.args[0]
    if exit_code:state.set_installed.assert_not_called();state.set_failed.assert_called_once()
    else:state.set_installed.assert_called_once_with('fjordseed');state.set_failed.assert_not_called()
