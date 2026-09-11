import subprocess
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

import app as hub
from services.nvidia_devices import probe_gpu
from services.installer import Installer


class GpuReuseTests(unittest.TestCase):
    def test_video_install_does_not_report_success_when_real_encoder_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'.git').mkdir()
            state=Mock()
            installer=Installer(state)
            process=Mock(stdout=[], returncode=0)
            with patch.object(installer, '_resolve_env_values', return_value={'ENABLE_GPU_COMPOSE':'1'}), \
                 patch('services.installer.probe_gpu', return_value={'ok':True}), \
                 patch('services.installer.discover_nvidia_devices', return_value=['/dev/nvidia0']), \
                 patch('services.installer.docker_desktop_gpu', return_value=False), \
                 patch('services.installer.subprocess.Popen', return_value=process), \
                 patch('services.installer.subprocess.run', side_effect=[
                     subprocess.CompletedProcess([],0,'Updated',''),
                     subprocess.CompletedProcess([],1,'','Cannot load libnvidia-encode.so.1')]) as run:
                installer._run({'id':'fjordflix','name':'FjordFlix','gpu_video':True,'gpu_service':'app'}, {}, root)
            self.assertIn('h264_nvenc',run.call_args.args[0])
            state.set_installed.assert_not_called()
            state.set_failed.assert_called_once()
            self.assertIn('libnvidia-encode',state.set_failed.call_args.args[1])

    def test_video_app_detects_missing_libraries_after_successful_gpu_test(self):
        with patch('services.nvidia_devices.discover_nvidia_devices', return_value=['/dev/nvidia0']), \
             patch('services.nvidia_devices.docker_desktop_gpu', return_value=False), \
             patch('services.nvidia_devices.subprocess.run', side_effect=[
                 subprocess.CompletedProcess([], 0, 'GPU ready', ''),
                 subprocess.CompletedProcess([], 1, '', '')]) as run:
            result = probe_gpu(require_video=True)
        self.assertFalse(result['ok'])
        self.assertEqual(result['stage'], 'video')
        self.assertIn('NVIDIA_DRIVER_CAPABILITIES=compute,utility,video', run.call_args.args[0])

    def test_video_app_ready_when_both_checks_pass(self):
        with patch('services.nvidia_devices.discover_nvidia_devices', return_value=[]), \
             patch('services.nvidia_devices.docker_desktop_gpu', return_value=True), \
             patch('services.nvidia_devices.subprocess.run', return_value=subprocess.CompletedProcess([], 0, 'ready', '')) as run:
            self.assertTrue(probe_gpu(require_video=True)['ok'])
        self.assertEqual(run.call_count, 2)

    def test_both_installers_stop_before_clone_when_gpu_unavailable(self):
        for app_id in ('fjordflix', 'fjordlens'):
            state = Mock()
            installer = Installer(state)
            with self.subTest(app=app_id), \
                 patch.object(installer, '_resolve_env_values', return_value={'ENABLE_GPU_COMPOSE': '1'}), \
                 patch('services.installer.probe_gpu', return_value={'ok': False, 'error': 'runtime missing'}), \
                 patch('services.installer.subprocess.run') as run:
                installer._run({'id': app_id}, {}, Path('unused-gpu-test'))
            state.set_failed.assert_called_once()
            run.assert_not_called()

    def test_ready_setup_never_installs_or_restarts_docker(self):
        with patch.object(hub, 'probe_gpu', return_value={'ok': True}), \
             patch.object(hub, '_gpu_setup_append'), \
             patch.object(hub, '_gpu_setup_finish') as finish, \
             patch.object(hub, '_gpu_setup_run_step') as mutate:
            hub._gpu_setup_worker()
        finish.assert_called_once_with(True)
        mutate.assert_not_called()

    def test_unavailable_test_does_not_trigger_installation(self):
        with patch.object(hub, 'probe_gpu', return_value={'ok': False, 'stage': 'test_error', 'error': 'timeout'}), \
             patch.object(hub, '_gpu_setup_append'), \
             patch.object(hub, '_gpu_setup_finish') as finish, \
             patch.object(hub, '_gpu_setup_run_step') as mutate:
            hub._gpu_setup_worker()
        finish.assert_called_once_with(False, 'timeout')
        mutate.assert_not_called()

    def test_missing_devices_require_host_setup(self):
        with patch('services.nvidia_devices.discover_nvidia_devices', return_value=[]), \
             patch('services.nvidia_devices.docker_desktop_gpu', return_value=False), \
             patch('services.nvidia_devices.subprocess.run') as run:
            result = probe_gpu()
        self.assertFalse(result['ok'])
        self.assertEqual(result['stage'], 'devices')
        run.assert_not_called()

    def test_linux_and_desktop_test_the_actual_runtime(self):
        for desktop in (False, True):
            with self.subTest(desktop=desktop), \
                 patch('services.nvidia_devices.discover_nvidia_devices', return_value=['/dev/nvidia0']), \
                 patch('services.nvidia_devices.docker_desktop_gpu', return_value=desktop), \
                 patch('services.nvidia_devices.subprocess.run', return_value=subprocess.CompletedProcess([], 0, 'GPU ready', '')) as run:
                self.assertTrue(probe_gpu()['ok'])
                command = run.call_args.args[0]
                self.assertIn('--gpus', command)
                self.assertEqual('--device' in command, not desktop)

    def test_runtime_failure_is_not_reported_as_ready(self):
        with patch('services.nvidia_devices.discover_nvidia_devices', return_value=['/dev/nvidia0']), \
             patch('services.nvidia_devices.docker_desktop_gpu', return_value=False), \
             patch('services.nvidia_devices.subprocess.run', return_value=subprocess.CompletedProcess([], 1, '', 'runtime missing')):
            result = probe_gpu()
        self.assertFalse(result['ok'])
        self.assertEqual(result['stage'], 'runtime')
