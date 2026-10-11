import contextlib
import stat
from pathlib import Path
from unittest.mock import Mock
import docker
import pytest
from services import vpn_setup
from host_agent import storage
from services.installer import Installer
from services.install_state import InstallState


def test_installer_persists_proxmox_access_even_when_device_already_works(monkeypatch):
    client=Mock()
    client.containers.get.return_value.attrs={'Image':'hub-image'}
    monkeypatch.setenv('HOSTNAME','hub')
    monkeypatch.setenv('FJORDHUB_STORAGE_SSH_HOST','192.168.1.250')
    monkeypatch.setattr(vpn_setup.docker,'from_env',Mock(return_value=client))
    repair=Mock(return_value={'ready':True})
    monkeypatch.setattr(vpn_setup.HostStorage,'ensure_vpn_tun',repair)
    vpn_setup.ensure_vpn_tun(Mock())
    repair.assert_called_once()
    assert client.containers.run.call_count==1
    args=client.containers.run.call_args
    assert args.args==('hub-image',)
    assert args.kwargs['devices']==['/dev/net/tun:/dev/net/tun:rwm']
    assert args.kwargs['network_mode']=='none' and args.kwargs['cap_drop']==['ALL']
    client.close.assert_called_once()


def test_proxmox_setup_is_followed_by_real_docker_probe(monkeypatch):
    client=Mock()
    client.containers.get.return_value.attrs={'Image':'hub-image'}
    client.containers.run.side_effect=docker.errors.DockerException('still unavailable')
    monkeypatch.setenv('HOSTNAME','hub')
    monkeypatch.setenv('FJORDHUB_STORAGE_SSH_HOST','192.168.1.250')
    monkeypatch.setattr(vpn_setup.docker,'from_env',Mock(return_value=client))
    repair=Mock(return_value={'ready':True})
    monkeypatch.setattr(vpn_setup.HostStorage,'ensure_vpn_tun',repair)
    with pytest.raises(RuntimeError,match='Docker kan ikke åbne'):
        vpn_setup.ensure_vpn_tun(Mock())
    repair.assert_called_once()
    client.containers.run.assert_called_once()
    client.close.assert_called_once()


def test_standalone_docker_host_needs_no_proxmox_connection(monkeypatch):
    client=Mock();client.containers.get.return_value.attrs={'Image':'hub-image'}
    monkeypatch.setenv('HOSTNAME','hub')
    monkeypatch.delenv('FJORDHUB_STORAGE_SSH_HOST',raising=False)
    monkeypatch.setattr(vpn_setup.docker,'from_env',Mock(return_value=client))
    repair=Mock();monkeypatch.setattr(vpn_setup.HostStorage,'ensure_vpn_tun',repair)
    vpn_setup.ensure_vpn_tun(Mock())
    repair.assert_not_called()
    client.containers.run.assert_called_once()
    client.close.assert_called_once()


@pytest.mark.parametrize('result,message',[
    ({'ready':False},'Proxmox kunne ikke'),
    ({'ready':False,'restart_required':True},'LXC’en skal genstartes')])
def test_failed_host_setup_never_proceeds_to_docker_probe(monkeypatch,result,message):
    client=Mock();client.containers.get.return_value.attrs={'Image':'hub-image'}
    monkeypatch.setenv('HOSTNAME','hub')
    monkeypatch.setenv('FJORDHUB_STORAGE_SSH_HOST','192.168.1.250')
    monkeypatch.setattr(vpn_setup.docker,'from_env',Mock(return_value=client))
    monkeypatch.setattr(vpn_setup.HostStorage,'ensure_vpn_tun',Mock(return_value=result))
    with pytest.raises(RuntimeError,match=message):
        vpn_setup.ensure_vpn_tun(Mock())
    client.containers.run.assert_not_called()
    client.close.assert_called_once()


def test_missing_proxmox_access_fails_before_install(monkeypatch):
    client=Mock()
    client.containers.get.return_value.attrs={'Image':'hub-image'}
    client.containers.run.side_effect=docker.errors.DockerException('missing')
    monkeypatch.setenv('HOSTNAME','hub')
    monkeypatch.delenv('FJORDHUB_STORAGE_SSH_HOST',raising=False)
    monkeypatch.setattr(vpn_setup.docker,'from_env',Mock(return_value=client))
    with pytest.raises(RuntimeError,match='Proxmox-forbindelse'):vpn_setup.ensure_vpn_tun(Mock())


def test_vpn_installer_preflight_failure_never_starts_compose(tmp_path,monkeypatch):
    state=InstallState(tmp_path)
    installer=Installer(state)
    monkeypatch.setattr(installer,'_resolve_env_values',Mock(return_value={}))
    check=Mock(side_effect=RuntimeError('TUN not ready'))
    monkeypatch.setattr(vpn_setup,'ensure_vpn_tun',check)
    run=Mock()
    monkeypatch.setattr('services.installer.subprocess.run',run)
    installer._run({'id':'fjordvpn'}, {},tmp_path/'vpn')
    check.assert_called_once()
    run.assert_not_called()
    assert state.get('fjordvpn')['state']=='failed'


@pytest.mark.parametrize('hotplug_failed',[False,True,'missing','probe_failed'])
def test_fixed_host_action_persists_only_tun_and_hotplugs_without_restart(tmp_path,monkeypatch,hotplug_failed):
    monkeypatch.setattr(storage,'ROOT',tmp_path)
    monkeypatch.setattr(storage,'TUN_MODULES',tmp_path/'modules-load/tun.conf')
    monkeypatch.setattr(storage.Agent,'locked',lambda self:contextlib.nullcontext())
    agent=storage.Agent('1000')
    config=tmp_path/'ct.conf'
    original='hostname: hub\nlxc.cgroup2.devices.allow: c 195:* rwm\n'
    config.write_text(original)
    real_path=Path
    monkeypatch.setattr(storage,'Path',lambda v:config if str(v)=='/etc/pve/lxc/1000.conf' else real_path(v))
    calls=[]
    def run(args):
        calls.append(args)
        if 'inspect' in args:return 'sha256:'+'a'*64
        if args[0]=='pct' and 'run' in args and sum(c[0]=='pct' and 'run' in c for c in calls)==1:raise ValueError('missing')
        if args[0]=='lxc-device' and hotplug_failed=='missing':raise FileNotFoundError('missing lxc-device')
        if args[0]=='lxc-device' and hotplug_failed is True:raise ValueError('not allowed')
        if args[0]=='pct' and 'run' in args and hotplug_failed=='probe_failed':raise ValueError('device still inaccessible')
        return ''
    monkeypatch.setattr(storage,'run',run)
    result=storage.dispatch(agent,{'action':'vpn_tun'})
    assert result['ready'] is (not hotplug_failed)
    if hotplug_failed:assert result['restart_required'] is True
    assert config.read_text().startswith(original)
    assert config.read_text().count('c 10:200 rwm')==1
    assert ['lxc-device','-n','1000','add','/dev/net/tun'] in calls
    assert not any('reboot' in args or 'restart' in args for args in calls)
    assert list(agent.folder.glob('before-vpn-tun-*.conf'))[0].read_text()==original
    assert storage.dispatch(agent,{'action':'vpn_tun'})['changed'] is False
    assert storage.TUN_MODULES.read_text()=='tun\n'
    assert not any(args[:5]==['pct','exec','1000','--','python3'] for args in calls)
    for request in [{'action':'vpn_tun','ctid':'1013'}, {'action':'vpn_tun','pool_id':'x'}]:
        with pytest.raises(ValueError):storage.dispatch(agent,request)


@pytest.mark.parametrize('configured',[False,True])
def test_existing_tun_is_reused_and_only_missing_lxc_mount_is_added(tmp_path,monkeypatch,configured):
    monkeypatch.setattr(storage,'ROOT',tmp_path)
    monkeypatch.setattr(storage,'TUN_MODULES',tmp_path/'modules-load/tun.conf')
    monkeypatch.setattr(storage.Agent,'locked',lambda self:contextlib.nullcontext())
    agent=storage.Agent('1000');config=tmp_path/'ct.conf'
    existing='hostname: hub\n'
    if configured:existing+='lxc.mount.entry: /dev/net/tun dev/net/tun none bind,create=file\nlxc.cgroup2.devices.allow: c 10:200 rwm\n'
    config.write_text(existing)
    tun=Mock();tun.exists.return_value=True
    tun.stat.return_value=Mock(st_mode=stat.S_IFCHR,st_rdev=123)
    real_path=Path
    def path(value):
        if str(value)=='/dev/net/tun':return tun
        if str(value)=='/etc/pve/lxc/1000.conf':return config
        return real_path(value)
    monkeypatch.setattr(storage,'Path',path)
    monkeypatch.setattr(storage.os,'major',lambda _:10,raising=False)
    monkeypatch.setattr(storage.os,'minor',lambda _:200,raising=False)
    calls=[];monkeypatch.setattr(storage,'run',lambda args:calls.append(args) or ('sha256:'+'a'*64 if 'inspect' in args else ''))
    result=agent.ensure_vpn_tun()
    assert result['ready'] and result['changed'] is not configured
    assert not any(args[0] in ('modprobe','lxc-device') for args in calls)
    assert config.read_text().count('lxc.mount.entry: /dev/net/tun')==1
    assert config.read_text().count('c 10:200 rwm')==1
    if configured:assert config.read_text()==existing
    assert storage.TUN_MODULES.read_text()=='tun\n'
