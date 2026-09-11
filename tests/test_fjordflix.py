import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.auth import AuthService
from services.installer import Installer
from services.install_state import InstallState
from services.nvidia_devices import render_compose_override, render_desktop_override, docker_desktop_gpu


class FjordFlixIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.manifest=json.loads((Path(__file__).parents[1]/'app_registry/fjordflix.json').read_text(encoding='utf-8'))

    def tearDown(self):
        self.temp.cleanup()

    def resolve(self, settings):
        with patch('services.installer.DATA_BASE',self.root),patch('services.installer._container_path_to_host_path',return_value=None):
            return Installer(InstallState(self.root))._resolve_env_values(self.manifest,settings)

    def test_cpu_uses_managed_compose_and_keeps_hub_identity(self):
        result=self.resolve({'FJORDHUB_API_KEY':'test-key','FJORDHUB_APP_ID':'fjordflix','FJORDHUB_URL':'http://hub:8080'})
        self.assertEqual(result['COMPOSE_FILE'],'docker-compose.yml')
        self.assertEqual(result['ENABLE_GPU_COMPOSE'],'0')
        self.assertEqual(result['FJORDHUB_API_KEY'],'test-key')
        self.assertEqual(result['APP_PORT'],'8097')
        self.assertEqual(result['MAX_TRANSCODES'],'2')

    def test_gpu_uses_app_service_and_shared_device(self):
        result=self.resolve({'ENABLE_GPU_COMPOSE':'1'})
        self.assertEqual(result['COMPOSE_FILE'],'docker-compose.yml:docker-compose.gpu.yml:docker-compose.fjordhub-gpu.yml')
        for service in (self.manifest['gpu_service'],'fjordlens-ai'):
            override=render_compose_override(service,['/dev/nvidia0','/dev/nvidiactl'])
            self.assertIn('/dev/nvidia0:/dev/nvidia0',override)
            self.assertIn(service+':',override)
        self.assertIn('devices: !reset []',render_desktop_override('app'))

    def test_desktop_runtime_detection(self):
        with patch('services.nvidia_devices.subprocess.run') as run:
            run.return_value.returncode=0
            run.return_value.stdout='Docker Desktop'
            self.assertTrue(docker_desktop_gpu())
            run.return_value.stdout='Ubuntu 24.04'
            self.assertFalse(docker_desktop_gpu())

    def test_roles_and_forced_password_are_central(self):
        auth=AuthService(self.root/'auth.db')
        uid=auth.create_user('viewer','sixsix',require_password_change=True)
        auth.set_user_app_access(uid,'fjordflix','user')
        self.assertTrue(auth.list_app_users('fjordflix')[0]['must_change_password'])
        auth.change_password(uid,'new-password')
        self.assertFalse(auth.list_app_users('fjordflix')[0]['must_change_password'])
        auth.update_app_user_role(uid,'fjordflix','admin')
        self.assertEqual(auth.authenticate_app_user('fjordflix','viewer','new-password')['role'],'admin')
        self.assertFalse(auth.get_by_id(uid).is_admin)
        auth.remove_user_app_access(uid,'fjordflix')
        self.assertIsNone(auth.authenticate_app_user('fjordflix','viewer','new-password'))
        self.assertEqual(auth.list_app_users('fjordflix'),[])
