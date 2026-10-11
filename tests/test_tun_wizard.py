import json
from unittest.mock import Mock, patch

import pytest
import docker

from services import vpn_setup
from scripts import setup_vpn_tun as setup

IDENT='a'*64


def test_command_is_bound_to_exact_hub_without_guessing_addresses(monkeypatch):
    client=Mock();client.containers.get.return_value.attrs={'Id':IDENT}
    monkeypatch.setenv('HOSTNAME','hub');monkeypatch.delenv('FJORDHUB_STORAGE_SSH_HOST',raising=False)
    monkeypatch.setattr(vpn_setup.docker,'from_env',Mock(return_value=client))
    info=vpn_setup.wizard_setup()
    assert info['configured'] is False
    assert '--hub-container '+IDENT in info['command']
    assert '192.168.' not in info['command'] and '<CTID>' not in info['command']
    assert 'apt-get install -y --no-install-recommends git python3 ca-certificates' in info['command']
    assert 'set -euo pipefail' in info['command']
    assert info['command'].startswith("bash <<'FJORDHUB_TUN_SETUP'")
    client.close.assert_called_once()


def test_unavailable_identity_does_not_offer_a_guessed_command(monkeypatch):
    monkeypatch.setattr(vpn_setup.docker,'from_env',Mock(side_effect=RuntimeError('unavailable')))
    assert vpn_setup.wizard_setup()['command']==''


def test_detects_exact_container_and_route_to_its_lxc(monkeypatch):
    calls=[]
    def run(args):
        calls.append(args)
        if args==['pct','list']:return 'VMID Status Lock Name\n1000 running hub\n1001 running other\n1002 stopped stopped\n'
        if 'inspect' in args:
            if args[2]=='1001':raise ValueError('No match')
            return json.dumps([{'Id':IDENT,'Name':'/fjordhub','Mounts':[{'Type':'bind','Source':'/opt/custom-hub','Destination':'/fjordhub-src'}]}])
        if args[0]=='pct':return '[{"prefsrc":"192.168.1.14"}]'
        return '[{"prefsrc":"192.168.1.250"}]'
    monkeypatch.setattr(setup,'run',run)
    assert setup.discover(IDENT)=={'ctid':'1000','host':'192.168.1.250','directory':'/opt/custom-hub'}
    assert ['ip','-j','-4','route','get','192.168.1.14'] in calls
    assert not any('1002' in args for args in calls)


def test_different_container_is_never_configured(monkeypatch):
    monkeypatch.setattr(setup,'run',Mock(side_effect=['VMID Status Lock Name\n1000 running hub',
        json.dumps([{'Id':'b'*64,'Name':'/fjordhub'}])]))
    with pytest.raises(ValueError,match='ikke fundet entydigt'):setup.discover(IDENT)


def test_setup_persists_tun_before_bootstrap_and_verifies_docker(monkeypatch):
    from scripts import configure_proxmox
    from host_agent.storage import Agent
    monkeypatch.setattr(setup.os,'geteuid',lambda:0,raising=False)
    monkeypatch.setattr(setup.Path,'is_dir',lambda _:True)
    monkeypatch.setattr('sys.argv',['setup_vpn_tun.py','--hub-container',IDENT])
    target={'ctid':'1234','host':'192.168.1.250','directory':'/opt/custom-hub'}
    monkeypatch.setattr(setup,'discover',Mock(return_value=target))
    order=[]
    monkeypatch.setattr(Agent,'ensure_vpn_tun',lambda self:order.append('tun'))
    def bootstrap():
        import sys
        assert sys.argv==['configure_proxmox.py','1234','--host','192.168.1.250','--directory','/opt/custom-hub']
        order.append('bootstrap')
    monkeypatch.setattr(configure_proxmox,'main',bootstrap)
    monkeypatch.setattr(Agent,'__init__',lambda self,ctid:None)
    monkeypatch.setattr(setup,'run',lambda args:order.append('probe'))
    setup.main()
    assert order==['tun','bootstrap','probe']


def test_wizard_inserts_setup_step_only_for_fjordvpn(tmp_path):
    import app as hub
    from services.auth import AuthService
    auth=AuthService(tmp_path/'auth.db');auth.create_user('admin','test-password',role='admin')
    definition={'id':'fjordvpn','name':'FjordVPN','default_port':8098,'setup_steps':[]}
    with patch.object(hub,'_auth',auth),patch.object(hub,'_get_app',return_value=definition), \
         patch.object(vpn_setup,'wizard_setup',return_value={'configured':False,'command':'safe-fixture-command'}):
        with hub.app.test_client() as client:
            client.post('/login',data={'username':'admin','password':'test-password'})
            page=client.get('/apps/fjordvpn/wizard')
            assert page.status_code==200
            assert 'TUN netværksopsætning' in page.text and 'safe-fixture-command' in page.text
            definition['id']='fjordseed'
            page=client.get('/apps/fjordseed/wizard')
            assert 'tun-copy-btn' not in page.text


@pytest.mark.parametrize('missing',[False,True])
def test_checker_opens_device_without_repairing_host(monkeypatch,missing):
    monkeypatch.setenv('HOSTNAME','hub');monkeypatch.setenv('FJORDHUB_STORAGE_SSH_HOST','192.168.1.250')
    client=Mock();client.containers.get.return_value.attrs={'Image':'fixture'}
    if missing:client.containers.run.side_effect=docker.errors.DockerException('missing')
    monkeypatch.setattr(vpn_setup.docker,'from_env',Mock(return_value=client))
    monkeypatch.setattr(vpn_setup.HostStorage,'inventory',Mock(return_value={'available':True}))
    repair=Mock();monkeypatch.setattr(vpn_setup.HostStorage,'ensure_vpn_tun',repair)
    status=vpn_setup.check_vpn_tun()
    assert status['proxmox']=='connected'
    assert status['ready'] is not missing
    assert status['tun']==('unavailable' if missing else 'ready')
    assert client.containers.run.call_args.kwargs['network_mode']=='none'
    repair.assert_not_called();client.close.assert_called_once()


def test_checker_reports_unreachable_proxmox_separately_from_tun(monkeypatch):
    monkeypatch.setenv('HOSTNAME','hub');monkeypatch.setenv('FJORDHUB_STORAGE_SSH_HOST','192.168.1.250')
    client=Mock();client.containers.get.return_value.attrs={'Image':'fixture'}
    monkeypatch.setattr(vpn_setup.docker,'from_env',Mock(return_value=client))
    monkeypatch.setattr(vpn_setup.HostStorage,'inventory',Mock(side_effect=ValueError('secret details')))
    status=vpn_setup.check_vpn_tun()
    assert status['proxmox']=='unavailable' and status['ready'] is True
    assert 'secret' not in str(status)


def test_checker_cache_avoids_creating_a_probe_for_every_poll(monkeypatch):
    monkeypatch.setattr(vpn_setup,'_check_cache',{})
    timestamp=[100]
    monkeypatch.setattr(vpn_setup.time,'monotonic',lambda:timestamp[0])
    probe=Mock(return_value={'ready':True})
    monkeypatch.setattr(vpn_setup,'check_vpn_tun',probe)
    vpn_setup.cached_check_vpn_tun()['ready']=False
    assert vpn_setup.cached_check_vpn_tun()['ready'] is True
    probe.assert_called_once()
    timestamp[0]+=11;vpn_setup.cached_check_vpn_tun()
    assert probe.call_count==2


def test_checker_requires_administrator(tmp_path):
    import app as hub
    from services.auth import AuthService
    auth=AuthService(tmp_path/'auth.db')
    for name,role in [('admin','admin'),('reader','user')]:auth.create_user(name,'test-password',role=role)
    with patch.object(hub,'_auth',auth),patch.object(vpn_setup,'cached_check_vpn_tun',return_value={'ready':True}) as check:
        assert hub.app.test_client().get('/apps/fjordvpn/tun/check').status_code in (302,401)
        with hub.app.test_client() as client:
            client.post('/login',data={'username':'reader','password':'test-password'})
            assert client.get('/apps/fjordvpn/tun/check').status_code==403
        check.assert_not_called()
        with hub.app.test_client() as client:
            client.post('/login',data={'username':'admin','password':'test-password'})
            assert client.get('/apps/fjordvpn/tun/check').json['ready'] is True
        check.assert_called_once()
