import contextlib
from pathlib import Path
from unittest.mock import Mock
import docker
import pytest
from services import vpn_setup
from host_agent import storage
from services.installer import Installer
from services.install_state import InstallState


@pytest.mark.parametrize('missing',[False,True])
def test_installer_checks_docker_host_and_only_repairs_if_needed(monkeypatch,missing):
    client=Mock()
    client.containers.get.return_value.attrs={'Image':'hub-image'}
    if missing:client.containers.run.side_effect=[docker.errors.DockerException('missing tun'),b'']
    monkeypatch.setenv('HOSTNAME','hub')
    monkeypatch.setenv('FJORDHUB_STORAGE_SSH_HOST','192.168.1.250')
    monkeypatch.setattr(vpn_setup.docker,'from_env',Mock(return_value=client))
    repair=Mock(return_value={'ready':True})
    monkeypatch.setattr(vpn_setup.HostStorage,'ensure_vpn_tun',repair)
    vpn_setup.ensure_vpn_tun(Mock())
    assert repair.call_count==int(missing)
    assert client.containers.run.call_count==1+int(missing)
    args=client.containers.run.call_args
    assert args.args==('hub-image',)
    assert args.kwargs['devices']==['/dev/net/tun:/dev/net/tun:rwm']
    assert args.kwargs['network_mode']=='none' and args.kwargs['cap_drop']==['ALL']
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


def test_fixed_host_action_persists_only_tun_and_hotplugs_without_restart(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'ROOT',tmp_path)
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
        if args[0]=='pct' and sum(c[0]=='pct' for c in calls)==1:raise ValueError('missing')
        return ''
    monkeypatch.setattr(storage,'run',run)
    assert storage.dispatch(agent,{'action':'vpn_tun'})['ready']
    assert config.read_text().startswith(original)
    assert config.read_text().count('c 10:200 rwm')==1
    assert ['lxc-device','-n','1000','add','/dev/net/tun'] in calls
    assert not any('reboot' in args or 'restart' in args for args in calls)
    assert list(agent.folder.glob('before-vpn-tun-*.conf'))[0].read_text()==original
    assert storage.dispatch(agent,{'action':'vpn_tun'})['changed'] is False
    for request in [{'action':'vpn_tun','ctid':'1013'}, {'action':'vpn_tun','pool_id':'x'}]:
        with pytest.raises(ValueError):storage.dispatch(agent,request)
