from unittest.mock import Mock, patch
import pytest
import app as hub


@pytest.mark.parametrize('change', [
    {'mount_root':'/etc'}, {'mount_root':'/mnt/../etc'},
    {'subdir':'../other'}, {'options':'defaults\ninjected'},
    {'export':'nas:/share\ninjected'}, {'export':'nas:relative'},
])
def test_invalid_mount_cannot_start_host_command(change):
    payload = {'export':'nas:/media','mount_root':'/mnt/new-nas', **change}
    with hub.app.test_request_context('/api/mount-nfs',method='POST',json=payload), \
         patch.object(hub.subprocess,'run') as run:
        response, status = hub.api_mount_nfs.__wrapped__()
    assert status == 400
    assert response.json['ok'] is False
    run.assert_not_called()


@pytest.mark.parametrize('source,expected', [('nas:/media',True),('other:/media',False)])
def test_verification_requires_selected_export(source, expected):
    with hub.app.test_request_context('/api/verify-nfs-mount?path=/mnt/new-nas&export=nas:/media'), \
         patch.object(hub.subprocess,'run',return_value=Mock(returncode=0,stdout=f'nfs {source}')):
        response = hub.api_verify_nfs_mount.__wrapped__()
    assert response.json['mounted'] is expected


def test_verification_does_not_create_a_missing_host_directory():
    with hub.app.test_request_context('/api/verify-nfs-mount?path=/mnt/missing&export=nas:/media'), \
         patch.object(hub.subprocess,'run',return_value=Mock(returncode=125,stdout='',stderr='bind source path does not exist: /mnt/missing')) as run:
        response = hub.api_verify_nfs_mount.__wrapped__()
    assert not response.json['mounted']
    assert 'LXC-ID' in response.json['error']
    command = run.call_args.args[0]
    assert 'type=bind,source=/mnt/missing,target=/d,readonly' in command
    assert not any(arg.startswith('--volume=') for arg in command)


def test_verification_reports_docker_failure_and_timeout():
    with hub.app.test_request_context('/api/verify-nfs-mount?path=/mnt/nas'), \
         patch.object(hub.subprocess,'run',return_value=Mock(returncode=1,stdout='',stderr='Docker unavailable')):
        assert hub.api_verify_nfs_mount.__wrapped__().json['error'] == 'Docker unavailable'
    with hub.app.test_request_context('/api/verify-nfs-mount?path=/mnt/nas'), \
         patch.object(hub.subprocess,'run',side_effect=hub.subprocess.TimeoutExpired('docker',15)):
        assert hub.api_verify_nfs_mount.__wrapped__().json['error'] == 'Timeout'


def test_mount_failure_is_reported_without_success_path():
    with hub.app.test_request_context('/api/mount-nfs',method='POST',json={'export':'nas:/media','mount_root':'/mnt/new-nas'}), \
         patch.object(hub,'_nfs_runtime_info',return_value={'auto_mount_supported':True}), \
         patch.object(hub.subprocess,'run',return_value=Mock(returncode=44,stdout='',stderr='Mount point is already in use')):
        response = hub.api_mount_nfs.__wrapped__()
    assert response.json['ok'] is False
    assert 'already in use' in response.json['error']
    assert 'path' not in response.json


@pytest.mark.parametrize('mounted,configured,files,expected', [
    ('other:/share','',False,44), ('','other:/share',False,44),
    ('','',True,44), ('nas:/media','nas:/media',True,0), ('','',False,0),
])
def test_real_shell_guard_preserves_existing_storage(tmp_path, mounted, configured, files, expected):
    import shlex
    import shutil
    import subprocess
    from pathlib import Path
    bash = 'C:/Program Files/Git/bin/bash.exe' if Path('C:/Program Files/Git/bin/bash.exe').exists() else shutil.which('bash')
    if not bash:
        pytest.skip('Bash is required for the isolated host guard check')
    with hub.app.test_request_context('/api/mount-nfs',method='POST',json={'export':'nas:/media','mount_root':'/mnt/new-nas'}), \
         patch.object(hub,'_nfs_runtime_info',return_value={'auto_mount_supported':True}), \
         patch.object(hub.subprocess,'run',return_value=Mock(returncode=0,stdout='',stderr='')) as run:
        hub.api_mount_nfs.__wrapped__()
    script = shlex.split(run.call_args.args[0][-1])[-1]
    # Execute only the guard, against temporary mount tables and files.
    script = script[:script.index('if ! command -v mount.nfs')] + 'exit 0\n'
    target = tmp_path / 'target'; target.mkdir()
    sentinel = target / 'keep.txt'
    if files: sentinel.write_text('preserve me')
    mounts = tmp_path / 'mounts'; fstab = tmp_path / 'fstab'
    mounts.write_text(f'{mounted} {target.as_posix()} nfs rw 0 0\n' if mounted else '')
    fstab.write_text(f'{configured} {target.as_posix()} nfs defaults 0 0\n' if configured else '')
    before = fstab.read_bytes()
    script = script.replace('/mnt/new-nas',target.as_posix()).replace('/proc/mounts',shlex.quote(mounts.as_posix())).replace('/etc/fstab',shlex.quote(fstab.as_posix()))
    script_file = tmp_path / 'guard.sh'
    script_file.write_text(script, encoding='utf-8')
    result = subprocess.run([bash,script_file.as_posix()],capture_output=True,text=True,timeout=10)
    assert result.returncode == expected, result.stderr
    assert fstab.read_bytes() == before
    if files: assert sentinel.read_text() == 'preserve me'
