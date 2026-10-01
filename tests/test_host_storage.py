import contextlib
import json
import subprocess
import time
from pathlib import Path, PurePosixPath
from unittest.mock import Mock, patch

import pytest

from host_agent import storage
from services.host_storage import HostStorage


@pytest.fixture
def agent(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, 'ROOT', tmp_path)
    monkeypatch.setattr(storage.Agent, 'locked', lambda self: contextlib.nullcontext())
    return storage.Agent('1000')


def pool():
    return {'id': storage.pool_id('/mnt/media'), 'source':'/mnt/media', 'type':'fuse.mergerfs','allow_other':True}


def test_discovery_requires_real_media_mounts(monkeypatch):
    class HostPath(PurePosixPath):
        def is_dir(self): return True
        def resolve(self): return HostPath('/etc') if str(self) == '/mnt/link' else self
    monkeypatch.setattr(storage, 'Path', HostPath)
    monkeypatch.setattr(storage, 'MEDIA_ROOTS', tuple(map(HostPath, ['/mnt','/media','/srv'])))
    rows = [{'target': p, 'fstype': t, 'options': o} for p,t,o in [
        ('/mnt/media','fuse.mergerfs','rw,allow_other'),('/mnt/disk','ext4','rw'),
        ('/mnt/private','fuse.mergerfs','rw'),('/','ext4','rw'),('/mnt','ext4','rw'),
        ('/etc','ext4','rw'),('/mnt/link','ext4','rw'),('/mnt/device','devtmpfs','rw')]]
    monkeypatch.setattr(storage, 'run', lambda args: json.dumps({'filesystems':rows}))
    pools = storage.discover()
    assert [p['source'] for p in pools] == ['/mnt/disk','/mnt/media','/mnt/private']
    assert [p['allow_other'] for p in pools] == [True,True,False]


def test_connect_queues_one_fixed_ct_job_and_retry_does_not_reboot(agent, monkeypatch):
    monkeypatch.setattr(storage, 'discover', lambda: [pool()])
    monkeypatch.setattr(storage, 'config', lambda ctid: {'digest':'original'})
    commands = Mock(return_value='')
    monkeypatch.setattr(storage, 'run', commands)
    first = agent.connect(pool()['id'])
    assert first['state'] == 'queued'
    assert agent.connect(pool()['id'])['id'] == first['id']
    assert commands.call_count == 1
    args = commands.call_args.args[0]
    assert args[0] == 'systemd-run' and args[-3:] == ['--apply','1000',first['id']]
    with pytest.raises(ValueError): agent.connect('f'*20)
    agent.state_file.write_text(json.dumps({**first,'updated':time.time()-700}))
    with pytest.raises(ValueError, match='afbrudt'): agent.connect(pool()['id'])


def test_invalid_or_unmounted_source_never_starts_job(agent, monkeypatch):
    commands = Mock()
    monkeypatch.setattr(storage, 'run', commands)
    monkeypatch.setattr(storage, 'discover', lambda: [])
    for request in [{'action':'shell'}, {'action':'connect','path':'/etc'}, {'action':'connect','pool_id':'../etc'}, {'action':'connect','pool_id':'f'*20}]:
        with pytest.raises(ValueError): storage.dispatch(agent, request)
    monkeypatch.setattr(storage, 'discover', lambda: [{**pool(),'allow_other':False}])
    with pytest.raises(ValueError, match='allow_other'): agent.connect(pool()['id'])
    commands.assert_not_called()


def test_manual_write_grant_is_preserved_and_foreign_mount_refused():
    target = storage.target_for(pool()['id'])
    assert storage.matching_mount({'mp4':'/mnt/media,mp='+target+',ro=0'},pool()) == 'mp4'
    with pytest.raises(ValueError): storage.matching_mount({'mp4':'/mnt/other,mp='+target},pool())


def test_missing_host_mount_blocks_boot(monkeypatch):
    monkeypatch.setattr(storage, 'discover', lambda: [])
    monkeypatch.setattr(storage, 'config', lambda ctid: {'mp0':'/mnt/media,mp='+storage.target_for(pool()['id'])})
    with pytest.raises(ValueError, match='ikke monteret'): storage.verify_boot('1000')


def test_client_pins_host_and_rejects_wrong_container(monkeypatch):
    monkeypatch.setenv('FJORDHUB_STORAGE_SSH_HOST','192.168.1.250')
    monkeypatch.setenv('PROXMOX_VMID','1000')
    result = subprocess.CompletedProcess([],0,json.dumps({'ok':True,'ctid':'1000','pools':[],'job':{'state':'idle'}}),'')
    with patch('services.host_storage.subprocess.run', return_value=result) as run:
        assert HostStorage().inventory()['available']
        args = run.call_args.args[0]
        assert 'StrictHostKeyChecking=yes' in args and 'HostKeyAlias=fjordhub-proxmox' in args
        assert args[-1] == 'root@192.168.1.250'
        assert json.loads(run.call_args.kwargs['input']) == {'action':'inventory'}
        result.stdout = json.dumps({'ok':True,'ctid':'1010'})
        with pytest.raises(ValueError, match='anden LXC'): HostStorage().inventory()


def test_connect_endpoint_checks_identity_and_explicit_restart(monkeypatch):
    import app as hub
    auth = Mock()
    auth.verify_hub_key.side_effect = lambda app_id, key: key == 'test'
    auth.list_app_users.return_value = [{'id':7,'role':'admin'}]
    monkeypatch.setattr(hub, '_auth', auth)
    connect = Mock(return_value={'state':'queued'})
    monkeypatch.setattr(hub.HostStorage, 'connect', connect)
    client = hub.app.test_client()
    url = '/api/hub/apps/fjordflix/library/connect'
    data = {'app_id':'fjordflix','user_id':7,'pool_id':pool()['id'],'confirm_restart':True}
    assert client.post(url,json=data).status_code == 400
    assert client.post(url,json={**data,'user_id':8},headers={'X-Hub-Key':'test'}).status_code == 403
    assert client.post(url,json={**data,'confirm_restart':False},headers={'X-Hub-Key':'test'}).status_code == 400
    connect.assert_not_called()
    assert client.post(url,json=data,headers={'X-Hub-Key':'test'}).json['accepted']
    connect.assert_called_once_with(pool()['id'])


def test_worker_only_adds_read_only_mount_and_retains_backup(agent, monkeypatch, tmp_path):
    monkeypatch.setattr(storage, 'discover', lambda: [pool()])
    cfg = {'digest':'version', 'mp0':'/mnt/existing,mp=/mnt/existing,ro=0'}
    monkeypatch.setattr(storage, 'config', lambda ctid: dict(cfg))
    monkeypatch.setattr(storage, 'visible', lambda *args: True)
    boot = Mock()
    monkeypatch.setattr(storage, 'configure_boot', boot)
    original = tmp_path / 'original.conf'
    original.write_bytes(b'original CT configuration')
    real_path = Path
    monkeypatch.setattr(storage, 'Path', lambda value: original if str(value) == '/etc/pve/lxc/1000.conf' else real_path(value))
    commands = []
    def run(args, timeout=25):
        commands.append(args)
        if args[:2] == ['pct','set']:
            cfg['mp1'] = args[-1]
        return ''
    monkeypatch.setattr(storage, 'run', run)
    state = {'id':'a'*32,'pool_id':pool()['id'],'source':pool()['source'],
             'target':storage.target_for(pool()['id']),'state':'queued'}
    agent.save(state)
    agent.apply(state['id'])
    assert agent.state()['state'] == 'ready'
    mutation = next(args for args in commands if args[:2] == ['pct','set'])
    assert mutation == ['pct','set','1000','--digest','version','--mp1',
        '/mnt/media,mp='+state['target']+',ro=1,backup=0']
    assert cfg['mp0'] == '/mnt/existing,mp=/mnt/existing,ro=0'
    assert (agent.folder / (state['id']+'.conf')).read_bytes() == b'original CT configuration'
    boot.assert_called_once_with('1000',['/mnt/media'])
    assert ['pct','reboot','1000','--timeout','60'] in commands


def test_worker_failure_does_not_report_ready(agent, monkeypatch):
    monkeypatch.setattr(storage, 'discover', lambda: [])
    run = Mock()
    monkeypatch.setattr(storage, 'run', run)
    agent.save({'id':'a'*32,'pool_id':pool()['id'],'source':pool()['source'],'state':'queued'})
    agent.apply('a'*32)
    assert agent.state()['state'] == 'failed'
    run.assert_not_called()
