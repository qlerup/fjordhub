"""Real bundled Traefik -> Caddy -> Flix routing on isolated test ports."""
import sys
import os
import time
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import docker
import requests
from services import media_gateway as mg
from services.install_state import InstallState

real=docker.from_env()
client=SimpleNamespace(containers=real.containers,images=real.images,volumes=real.volumes)
qa='fjordhub-traefik-media-qa'
network=real.networks.create(qa)
proxy=None
create=client.containers.create
listing=client.containers.list
original=mg.caddyfile
proxy_image=os.environ.get('TRAEFIK_TEST_IMAGE','traefik:v3.3')
def isolated_create(*args,**kwargs):
    assert kwargs['ports']=={'443/tcp':443},kwargs['ports']
    kwargs['ports']={'443/tcp':('127.0.0.1',13444)}
    kwargs['network']=qa
    kwargs['labels']['traefik.docker.network']=qa
    return create(*args,**kwargs)
def containers():
    items=listing()
    for item in items:
        if item.id==proxy.id:
            item.attrs['NetworkSettings']['Ports']={'80/tcp':[{'HostPort':'80'}]}
    return items
try:
    client.images.pull(proxy_image)
    proxy=client.containers.run(proxy_image,name=qa+'-proxy',detach=True,network=qa,
        command=['--providers.docker=true','--providers.docker.exposedbydefault=false','--entrypoints.web.address=:80'],
        volumes={'/var/run/docker.sock':{'bind':'/var/run/docker.sock','mode':'ro'}},ports={'80/tcp':('127.0.0.1',13881)})
    app=client.containers.get('fjordflix-gateway-qa')
    mg.flix(app,'probe',('media.example.test','traefik-proof'))
    with tempfile.TemporaryDirectory() as tmp,patch.object(mg,'NAME',qa),patch.object(mg,'hub_traefik',side_effect=lambda c:c.id==proxy.id),patch.object(client.containers,'list',side_effect=containers),patch.object(client.containers,'create',side_effect=isolated_create),patch.object(mg,'caddyfile',side_effect=lambda host,up:original('http://'+host,up)):
        gateway=mg.MediaGateway(SimpleNamespace(client=client),InstallState(Path(tmp)))
        gateway.ensure_gateway(client,app,'media.example.test')
        for _ in range(15):
            response=requests.get('http://127.0.0.1:13881/media/connection-check',headers={'Host':'media.example.test'},timeout=5)
            if response.status_code==200: break
            time.sleep(1)
        assert response.status_code==200, (response.text,proxy.logs(tail=5).decode())
        assert response.json()=={'nonce':'traefik-proof'}
        assert requests.get('http://127.0.0.1:13881/api/admin',headers={'Host':'media.example.test'},timeout=5).status_code==404
        assert requests.get('http://127.0.0.1:13881/media/connection-check',headers={'Host':'unrelated.example.test'},timeout=5).status_code==404
        gateway.ensure_gateway(client,app,'media.example.test')
        assert client.containers.get(qa+'-proxy').id==proxy.id
        print('PASS: Traefik routes the selected hostname to Caddy; proof reaches Flix; admin and unrelated hosts blocked; proxy reused without restart. Public certificates are not requested.')
finally:
    for name in (qa,qa+'-proxy'):
        try: client.containers.get(name).remove(force=True)
        except docker.errors.NotFound: pass
    for suffix in ('-data','-config','-etc'):
        try: client.volumes.get(qa+suffix).remove()
        except docker.errors.NotFound: pass
    network.remove()
