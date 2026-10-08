"""Check the Docker host, not /dev inside FjordHub's management container."""
import os
import docker
from services.host_storage import HostStorage


def ensure_vpn_tun(log):
    client = docker.from_env(timeout=20)
    try:
        image = client.containers.get(os.environ['HOSTNAME']).attrs['Image']
        def probe():
            client.containers.run(image,
                command=['python', '-c', "import os; fd=os.open('/dev/net/tun',os.O_RDWR); os.close(fd)"],
                entrypoint=[], network_mode='none', devices=['/dev/net/tun:/dev/net/tun:rwm'],
                remove=True, read_only=True, cap_drop=['ALL'],
                security_opt=['no-new-privileges:true'])
        log('Kontrollerer VPN-adgang til TUN på Docker-værten…')
        try:
            probe()
        except docker.errors.DockerException:
            if not os.getenv('FJORDHUB_STORAGE_SSH_HOST'):
                raise RuntimeError('TUN mangler på Docker-værten. Aktivér FjordHubs Proxmox-forbindelse, så installationen kan sætte VPN-adgangen op automatisk.') from None
            log('Opsætter TUN automatisk på FjordHubs Proxmox-LXC…')
            result = HostStorage().ensure_vpn_tun()
            if result.get('ready') is not True:
                raise RuntimeError('Proxmox kunne ikke gøre VPN-adgangen klar.')
            probe()
        log('VPN-adgang er klar. TUN-test bestået i Docker.')
    finally:
        client.close()
