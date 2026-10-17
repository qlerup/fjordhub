from copy import deepcopy
import json
import os
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from services.bot_identity import ensure_identity, public, b64, canonical, verify, new_bundle

USER='@bot:example.test'; DEVICE='BOTDEVICE'


class Server:
    def __init__(self, challenge=False):
        self.key=Ed25519PrivateKey.generate()
        self.account=SimpleNamespace(identity_keys={'ed25519':public(self.key),'curve25519':'curve-key'},
                                     sign=lambda value:b64(self.key.sign(value.encode())))
        device={'user_id':USER,'device_id':DEVICE,'algorithms':['m.olm.v1.curve25519-aes-sha2','m.megolm.v1.aes-sha2'],
                'keys':{'ed25519:'+DEVICE:public(self.key),'curve25519:'+DEVICE:'curve-key'}}
        device['signatures']={USER:{'ed25519:'+DEVICE:self.account.sign(canonical(device).decode())}}
        self.state={'device_keys':{USER:{DEVICE:device}}}
        self.calls=[];self.challenge=challenge;self.fail_signatures=False
        self.trust_env=True

    def __enter__(self):return self
    def __exit__(self,*args):return False
    def post(self,url,headers,json,**options):
        assert options['allow_redirects'] is False
        self.calls.append((url,deepcopy(json)))
        status=200;reply={}
        if url.endswith('/keys/query'):
            reply=deepcopy(self.state)
        elif url.endswith('/keys/device_signing/upload'):
            if self.challenge and 'auth' not in json:
                status=401;reply={'session':'uia-session','flows':[{'stages':['m.login.password']}]}
            else:
                if self.challenge:
                    assert json['auth']['session']=='uia-session'
                    assert json['auth']['password']=='bot-password'
                for singular,plural in [('master_key','master_keys'),('self_signing_key','self_signing_keys'),('user_signing_key','user_signing_keys')]:
                    self.state[plural]={USER:deepcopy(json[singular])}
        elif url.endswith('/keys/signatures/upload'):
            if self.fail_signatures:
                reply={'failures':{USER:{DEVICE:{'errcode':'M_INVALID_SIGNATURE'}}}}
            else:self.state['device_keys'][USER][DEVICE]=deepcopy(json[USER][DEVICE])
        else:raise AssertionError(url)
        return SimpleNamespace(status_code=status,json=lambda:reply)


def run(server,path):
    return ensure_identity('https://matrix.example.test',USER,DEVICE,'access-token','bot-password',server.account,path,session_factory=lambda:server)


@pytest.mark.parametrize('challenge',[False,True])
def test_cryptographically_valid_bootstrap_and_stable_restart(tmp_path,challenge):
    server=Server(challenge);path=tmp_path/'identity.json'
    assert run(server,path)['status']=='verified'
    saved=path.read_bytes();bundle=json.loads(saved)
    master=next(iter(bundle['master_key']['keys'].values()))
    self_key=next(iter(bundle['self_signing_key']['keys'].values()))
    verify(server.state['self_signing_keys'][USER],USER,master)
    verify(server.state['user_signing_keys'][USER],USER,master)
    verify(server.state['device_keys'][USER][DEVICE],USER,self_key)
    assert os.stat(path).st_mode & 0o777 == 0o600
    assert 'master_seed' not in bundle and 'user_signing_seed' not in bundle
    uploads=sum(url.endswith('/keys/device_signing/upload') for url,_ in server.calls)
    assert run(server,path)['status']=='verified'
    assert path.read_bytes()==saved
    assert sum(url.endswith('/keys/device_signing/upload') for url,_ in server.calls)==uploads
    assert server.trust_env is False


def test_existing_identity_is_never_reset_when_private_keys_are_missing(tmp_path):
    server=Server();other=new_bundle(USER,DEVICE,server.account)
    server.state['master_keys']={USER:other['master_key']}
    result=run(server,tmp_path/'identity.json')
    assert result['status']=='manual_required'
    assert all(url.endswith('/keys/query') for url,_ in server.calls)
    assert not (tmp_path/'identity.json').exists()


def test_changed_remote_identity_is_not_overwritten(tmp_path):
    server=Server();path=tmp_path/'identity.json';run(server,path)
    old=path.read_bytes()
    server.state['master_keys']={USER:new_bundle(USER,DEVICE,server.account)['master_key']}
    server.calls.clear()
    assert run(server,path)['status']=='manual_required'
    assert path.read_bytes()==old
    assert all(url.endswith('/keys/query') for url,_ in server.calls)


def test_mismatched_device_key_is_never_signed(tmp_path):
    server=Server();server.state['device_keys'][USER][DEVICE]['keys']['ed25519:'+DEVICE]='other'
    with pytest.raises(RuntimeError):run(server,tmp_path/'identity.json')
    assert all(url.endswith('/keys/query') for url,_ in server.calls)


def test_signature_rejection_is_not_reported_as_verified(tmp_path):
    server=Server();server.fail_signatures=True
    with pytest.raises(RuntimeError):run(server,tmp_path/'identity.json')


def test_corrupt_local_file_does_not_generate_new_identity(tmp_path):
    server=Server();path=tmp_path/'identity.json';path.write_text('invalid')
    with pytest.raises(ValueError):run(server,path)
    assert path.read_text()=='invalid'
    assert all(url.endswith('/keys/query') for url,_ in server.calls)


def test_interrupted_setup_reuses_saved_signatures_without_new_identity(tmp_path):
    server=Server();path=tmp_path/'identity.json';original=server.post
    fail=[True]
    def interrupted(url,**kw):
        if url.endswith('/keys/device_signing/upload') and fail[0]:
            fail[0]=False
            raise ConnectionError('offline')
        return original(url,**kw)
    server.post=interrupted
    with pytest.raises(ConnectionError):run(server,path)
    saved=path.read_bytes()
    assert run(server,path)['status']=='verified'
    assert path.read_bytes()==saved
    seed=json.loads(saved)['self_signing_seed']
    assert all(seed not in json.dumps(body) for _,body in server.calls)


def test_bot_startup_uploads_device_keys_then_verifies_its_persisted_account(monkeypatch,tmp_path):
    import asyncio
    from unittest.mock import AsyncMock
    from services import matrix_bot
    bot=matrix_bot.FjordBot.__new__(matrix_bot.FjordBot)
    account=object();calls=[]
    bot.client=SimpleNamespace(should_upload_keys=True,keys_upload=AsyncMock(),
                               user_id=USER,device_id=DEVICE,access_token='token',olm=SimpleNamespace(account=account))
    monkeypatch.setattr(matrix_bot,'ROOT',tmp_path)
    monkeypatch.setattr(matrix_bot,'read',lambda path:{'password':'private'})
    def check(*args):
        calls.append(args)
        return {'status':'verified','message':'ready'}
    monkeypatch.setattr(matrix_bot,'ensure_identity',check)
    asyncio.run(bot.verify_identity())
    bot.client.keys_upload.assert_awaited_once()
    assert calls[0][-1]==tmp_path/'cross-signing.json'
    assert calls[0][-2] is account
    assert bot.identity_state['status']=='verified'


def test_bot_image_bundle_includes_identity_support():
    import tarfile
    from unittest.mock import Mock
    from services.matrix_hub import MatrixHub
    client=Mock()
    def build(**kwargs):
        with tarfile.open(fileobj=kwargs['fileobj']) as archive:
            assert 'bot_identity.py' in archive.getnames()
            assert b'cryptography' in archive.extractfile('Dockerfile').read()
    client.images.build.side_effect=build
    MatrixHub._build_bot_image(client)
    client.images.build.assert_called_once()
