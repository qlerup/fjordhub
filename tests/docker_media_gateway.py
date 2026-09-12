"""Disposable Docker integration: QA Flix on 8099; gateway on 13880/13443."""
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import docker
import requests
from types import SimpleNamespace
from services import media_gateway as mg
from services.install_state import InstallState

real=docker.from_env()
client=SimpleNamespace(containers=real.containers, images=real.images, volumes=real.volumes)
app=client.containers.get('fjordflix-gateway-qa')
qa='fjordhub-media-gateway-qa'
create=client.containers.create
def isolated_create(*args,**kwargs):
    kwargs['ports']={'80/tcp':('127.0.0.1',13880),'443/tcp':('127.0.0.1',13443)}
    return create(*args,**kwargs)
original=mg.caddyfile
try:
    with tempfile.TemporaryDirectory() as tmp, patch.object(mg,'NAME',qa), patch.object(client.containers,'create',side_effect=isolated_create), patch.object(mg,'caddyfile',side_effect=lambda host,up:original('http://'+host,up)):
        manager=type('Manager',(),{'client':client})()
        gateway=mg.MediaGateway(manager,InstallState(Path(tmp)))
        mg.flix(app,'probe',('media.example.test','docker-proof'))
        gateway.ensure_gateway(client,app,'media.example.test')
        import time
        time.sleep(2)
        response=requests.get('http://127.0.0.1:13880/media/connection-check',headers={'Host':'media.example.test'},timeout=5)
        assert response.status_code==200, response.text
        assert response.json()=={'nonce':'docker-proof'}
        assert requests.get('http://127.0.0.1:13880/api/admin',headers={'Host':'media.example.test'},timeout=5).status_code==404
        before=client.containers.get(qa).id
        gateway.ensure_gateway(client,app,'media.example.test')
        assert client.containers.get(qa).id==before
        assert mg.flix(app,'status')['media_url']==''
        mg.flix(app,'activate',('https://media.example.test','https://film.example.test'))
        assert mg.flix(app,'status')['media_url']=='https://media.example.test'
        print('PASS: real Caddy creation, persistent config, probe routing, blocked admin route, reuse/reload, app settings activation. Public TLS issuance is not exercised locally.')
finally:
    try: print(client.containers.get(qa).logs(tail=12).decode())
    except docker.errors.NotFound: pass
    try: client.containers.get(qa).remove(force=True)
    except docker.errors.NotFound: pass
    for suffix in ('-data','-config','-etc'):
        try: client.volumes.get(qa+suffix).remove()
        except docker.errors.NotFound: pass
