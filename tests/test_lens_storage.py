import json
import os
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from services.installer import Installer
from services.lens_storage import OVERRIDE, configure, write_override


def test_shared_discards_hidden_split_paths():
    values = {'UPLOADS_HOST_DIR': '/mnt/nas/photos', 'ORIGINALS_HOST_DIR': '/unused/a',
              'CONVERTED_HOST_DIR': '/unused/b'}
    configure(values)
    assert values['UPLOADS_HOST_DIR'] == '/mnt/nas/photos'
    assert 'ORIGINALS_HOST_DIR' not in values
    assert 'CONVERTED_HOST_DIR' not in values
    assert values['COMPOSE_FILE'] == 'docker-compose.yml'


def test_local_and_remote_manifest_storage_match():
    root = Path(__file__).parents[2]
    remote = root / 'fjordlens/fjordhub.json'
    if not remote.exists():
        pytest.skip('Requires FjordLens checkout')
    local = root / 'fjordhub/app_registry/fjordlens.json'
    def storage(path):
        return next(s for s in json.loads(path.read_text(encoding='utf-8'))['setup_steps'] if s['id'] == 'storage')
    assert storage(local) == storage(remote)


def test_split_preserves_gpu_and_mounts_both_services(tmp_path):
    values = {'FJORDLENS_STORAGE_MODE': 'split', 'ORIGINALS_HOST_DIR': '/mnt/nas/originals',
              'CONVERTED_HOST_DIR': '/mnt/ssd/converted', 'UPLOADS_HOST_DIR': '/unused',
              'COMPOSE_FILE': 'docker-compose.yml:docker-compose.gpu.yml'}
    configure(values)
    configure(values)
    assert 'UPLOADS_HOST_DIR' not in values
    assert values['COMPOSE_FILE'] == 'docker-compose.yml:docker-compose.gpu.yml:' + OVERRIDE
    write_override(tmp_path, values)
    services = json.loads((tmp_path / OVERRIDE).read_text())['services']
    for name in ('fjordlens', 'fjordlens-convert'):
        mounts = {v['target']: v['source'] for v in services[name]['volumes']}
        assert mounts['/uploads/originals'] == '${ORIGINALS_HOST_DIR}'
        assert mounts['/uploads/converted'] == '${CONVERTED_HOST_DIR}'
        assert mounts['/uploads'] == '${DATA_DIR}/uploads'


@pytest.mark.parametrize('path', ['', 'relative', '/mnt/nas', '/mnt/nas/originals', '/mnt/nas/originals/child'])
def test_split_rejects_missing_invalid_or_overlapping_paths(path):
    with pytest.raises(ValueError):
        configure({'FJORDLENS_STORAGE_MODE': 'split', 'ORIGINALS_HOST_DIR': '/mnt/nas/originals',
                   'CONVERTED_HOST_DIR': path})


@pytest.mark.parametrize('mode', ['shared', 'split'])
def test_real_manifest_installer_resolution(mode, tmp_path):
    definition = json.loads((Path(__file__).parents[1] / 'app_registry/fjordlens.json').read_text(encoding='utf-8'))
    with patch('services.installer.DATA_BASE', tmp_path), patch('services.installer._container_path_to_host_path', return_value=None):
        values = Installer(None)._resolve_env_values(definition, {'FJORDLENS_STORAGE_MODE': mode})
    assert (OVERRIDE in values['COMPOSE_FILE']) == (mode == 'split')
    assert ('UPLOADS_HOST_DIR' in values) == (mode == 'shared')
    assert ('ORIGINALS_HOST_DIR' in values) == (mode == 'split')


@pytest.mark.parametrize('gpu', [False, True])
def test_docker_compose_merges_real_lens_mounts(tmp_path, gpu):
    base = Path(__file__).parents[2] / 'fjordlens/docker-compose.yml'
    if not shutil.which('docker') or not base.exists():
        pytest.skip('Requires Docker Compose CLI and the FjordLens checkout')
    values = {'FJORDLENS_STORAGE_MODE': 'split', 'DATA_DIR': '/srv/lens/data',
              'ORIGINALS_HOST_DIR': '/mnt/nas/originals', 'CONVERTED_HOST_DIR': '/mnt/ssd/converted'}
    configure(values)
    write_override(tmp_path, values)
    args = ['docker', 'compose', '-f', str(base)]
    if gpu:
        args += ['-f', str(base.with_name('docker-compose.gpu.yml'))]
    args += ['-f', str(tmp_path / OVERRIDE), 'config', '--format', 'json']
    result = subprocess.run(args, env={**os.environ, **values}, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    config = json.loads(result.stdout)
    for name in ('fjordlens', 'fjordlens-convert'):
        mounts = {v['target']: v['source'] for v in config['services'][name]['volumes']}
        assert mounts['/uploads/originals'] == '/mnt/nas/originals'
        assert mounts['/uploads/converted'] == '/mnt/ssd/converted'
        assert mounts['/uploads'] == '/srv/lens/data/uploads'
