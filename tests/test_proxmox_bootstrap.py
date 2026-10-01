import json
from pathlib import Path

from scripts import configure_proxmox as setup


def test_bootstrap_pins_host_and_delivers_only_forced_key(monkeypatch, tmp_path):
    real_path = Path
    def path(value):
        value = str(value)
        if value.startswith(('/root/', '/etc/', '/usr/local/', '/var/lib/')):
            return tmp_path / value.lstrip('/')
        return real_path(value)
    monkeypatch.setattr(setup, 'Path', path)
    monkeypatch.setattr(setup.os, 'geteuid', lambda: 0, raising=False)
    monkeypatch.setattr(setup.os, 'umask', lambda _: 0)
    path('/etc/pve').mkdir(parents=True)
    host = path('/etc/ssh/ssh_host_ed25519_key.pub')
    host.parent.mkdir(parents=True)
    host.write_text('ssh-ed25519 HOSTKEY host\n')
    authorized = path('/root/.ssh/authorized_keys')
    authorized.parent.mkdir(parents=True)
    authorized.write_text('ssh-ed25519 EXISTING administrator\n')
    monkeypatch.setattr('sys.argv', ['configure_proxmox.py','1000','--host','192.168.1.250'])
    calls, delivered, env = [], {}, []
    def run(args, input=None):
        calls.append(args)
        if args[0] == 'ssh-keygen':
            key = real_path(args[-1]); key.write_text('TEST PRIVATE KEY')
            key.with_suffix('.pub').write_text('ssh-ed25519 PUBLICKEY generated')
        if 'inspect' in args:
            return json.dumps([{'Source':'/opt/fjordhub/data','Destination':'/data','Type':'bind'}])
        if args[:2] == ['pct','push']:
            delivered[args[4]] = real_path(args[3]).read_text()
        if args[:4] == ['pveum','user','token','add']:
            return json.dumps({'full-tokenid':'test@pve!inventory','value':'test-only-token'})
        if input:
            env.append(json.loads(input))
        return ''
    monkeypatch.setattr(setup, 'run', run)
    setup.main()
    text = authorized.read_text()
    assert 'ssh-ed25519 EXISTING administrator' in text
    line = text.splitlines()[-1]
    assert line.startswith('restrict,command="/usr/bin/python3 ')
    assert 'storage.py 1000" ssh-ed25519 PUBLICKEY fjordhub-storage-1000' in line
    assert delivered['/opt/fjordhub/data/proxmox-agent/known_hosts'] == 'fjordhub-proxmox ssh-ed25519 HOSTKEY\n'
    assert env[0]['PROXMOX_VMID'] == '1000'
    assert env[0]['FJORDHUB_STORAGE_SSH_HOST'] == '192.168.1.250'
    acl = [args for args in calls if args[:3] == ['pveum','acl','modify']]
    assert len(acl) == 2 and all('PVEAuditor' in args for args in acl)
    assert not any(args[:2] == ['pct','reboot'] for args in calls)
    assert 'HostStorage' in calls[-1][-1]
