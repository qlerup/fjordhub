"""Check the Docker host, not /dev inside FjordHub's management container."""
import os
import docker
import re
import threading
import time
from services.host_storage import HostStorage

_check_lock=threading.Lock()
_check_cache={}


def probe_tun(client,image):
    client.containers.run(image,
        command=['python','-c',"import os,stat; s=os.stat('/dev/net/tun'); assert stat.S_ISCHR(s.st_mode) and (os.major(s.st_rdev),os.minor(s.st_rdev))==(10,200); fd=os.open('/dev/net/tun',os.O_RDWR); os.close(fd)"],
        entrypoint=[],network_mode='none',devices=['/dev/net/tun:/dev/net/tun:rwm'],
        remove=True,read_only=True,cap_drop=['ALL'],security_opt=['no-new-privileges:true'])


def check_vpn_tun():
    """Read-only connection check and device open; never repairs the host."""
    status={'proxmox':'unconfigured','docker':'unavailable','tun':'unknown','ready':False}
    if os.getenv('FJORDHUB_STORAGE_SSH_HOST'):
        try:
            status['proxmox']='connected' if HostStorage().inventory().get('available') else 'unavailable'
        except Exception:
            status['proxmox']='unavailable'
    client=None
    try:
        client=docker.from_env(timeout=8)
        image=client.containers.get(os.environ['HOSTNAME']).attrs['Image']
        status['docker']='connected'
        try:
            probe_tun(client,image)
            status.update(tun='ready',ready=True)
        except docker.errors.DockerException:
            status['tun']='unavailable'
    except Exception:
        pass
    finally:
        if client is not None:client.close()
    if status['ready']:
        status['message']='Docker kan åbne TUN. VPN-adgangen er klar.'
    elif status['proxmox']=='connected':
        status['message']='Proxmox-forbindelsen virker. FjordVPN-installationen kan opsætte og montere TUN automatisk.'
    elif status['docker']=='unavailable':
        status['message']='Docker-forbindelsen kunne ikke kontrolleres. Kontrollér Docker og prøv igen.'
    else:
        status['message']='TUN er ikke tilgængelig i Docker. Kør opsætningskommandoen på Proxmox-værten og genindlæs guiden.'
    return status


def cached_check_vpn_tun():
    key=(os.getenv('HOSTNAME'),os.getenv('FJORDHUB_STORAGE_SSH_HOST'))
    with _check_lock:
        if _check_cache.get('key')==key and time.monotonic()-_check_cache.get('at',0)<10:
            return dict(_check_cache['status'])
        status=check_vpn_tun()
        _check_cache.update(key=key,at=time.monotonic(),status=status)
        return dict(status)


def wizard_setup():
    """Pin the host command to this Hub, without guessing its LXC ID or IP."""
    result={'configured':bool(os.getenv('FJORDHUB_STORAGE_SSH_HOST')),'command':''}
    client=None
    try:
        client=docker.from_env(timeout=5)
        ident=client.containers.get(os.environ['HOSTNAME']).attrs.get('Id')
        if isinstance(ident,str) and re.fullmatch('[a-f0-9]{64}',ident):
            result['command']=('setup_dir=$(mktemp -d /tmp/fjordhub-tun.XXXXXX)\n'
                'git clone --depth 1 https://github.com/qlerup/fjordhub.git "$setup_dir"\n'
                'python3 "$setup_dir/scripts/setup_vpn_tun.py" --hub-container '+ident)
    except Exception:
        pass
    finally:
        if client is not None:client.close()
    return result


def ensure_vpn_tun(log):
    client = docker.from_env(timeout=20)
    try:
        image = client.containers.get(os.environ['HOSTNAME']).attrs['Image']
        log('Kontrollerer VPN-adgang til TUN på Docker-værten…')
        if os.getenv('FJORDHUB_STORAGE_SSH_HOST'):
            # A working device may have been hotplugged manually. Persist the
            # exact LXC grant as well, so it remains available after reboot.
            log('Sikrer permanent TUN-adgang på FjordHubs Proxmox-LXC…')
            result = HostStorage().ensure_vpn_tun()
            if result.get('ready') is not True:
                raise RuntimeError('Proxmox kunne ikke gøre VPN-adgangen klar.')
        try:
            probe_tun(client,image)
        except docker.errors.DockerException:
            if not os.getenv('FJORDHUB_STORAGE_SSH_HOST'):
                raise RuntimeError('TUN mangler på Docker-værten. Aktivér FjordHubs Proxmox-forbindelse, så installationen kan sætte VPN-adgangen op automatisk.') from None
            raise RuntimeError('Proxmox har opsat TUN, men Docker kan ikke åbne enheden. Kontrollér LXC-adgangen på værten og prøv installationen igen.') from None
        log('VPN-adgang er klar. TUN-test bestået i Docker.')
    finally:
        client.close()
