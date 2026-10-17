"""Cross-sign the managed bot device without replacing an existing identity."""
import base64
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile

import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


def b64(value):
    return base64.b64encode(value).decode('ascii').rstrip('=')


def unb64(value):
    return base64.b64decode(value + '=' * (-len(value) % 4), validate=True)


def canonical(value):
    return json.dumps({k:v for k,v in value.items() if k not in {'signatures','unsigned'}},
                      sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def public(key):
    return b64(key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw))


def sign(value, user, key, key_id=None):
    result = deepcopy(value)
    result.pop('unsigned', None)
    result.setdefault('signatures', {}).setdefault(user, {})['ed25519:' + (key_id or public(key))] = b64(key.sign(canonical(value)))
    return result


def verify(value, user, key):
    signature = value['signatures'][user]['ed25519:' + key]
    Ed25519PublicKey.from_public_bytes(unb64(key)).verify(unb64(signature), canonical(value))


def save(path, bundle):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.bot-identity-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(bundle, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def new_bundle(user, device_id, account):
    master, self_key, user_key = (Ed25519PrivateKey.generate() for _ in range(3))
    def description(key, usage):
        value = public(key)
        return {'user_id':user,'usage':[usage],'keys':{'ed25519:'+value:value}}
    master_key = description(master, 'master')
    master_key['signatures'] = {user:{'ed25519:'+device_id:account.sign(canonical(master_key).decode('utf-8'))}}
    # Master and user-signing private keys are not retained. The self-signing
    # key only signs this bot's own devices; it cannot sign another user's keys.
    return {'user_id':user, 'master_key':master_key,
            'self_signing_key':sign(description(self_key,'self_signing'),user,master),
            'user_signing_key':sign(description(user_key,'user_signing'),user,master),
            'self_signing_seed':b64(self_key.private_bytes(serialization.Encoding.Raw,
                                                        serialization.PrivateFormat.Raw, serialization.NoEncryption()))}


def ensure_identity(server, user, device_id, access_token, password, account, path, session_factory=requests.Session):
    def manual(message):
        return {'status':'manual_required','message':message}
    with session_factory() as session:
        session.trust_env = False
        def post(endpoint, body, challenge=False):
            response = session.post(server.rstrip('/') + '/_matrix/client/v3/' + endpoint,
                                    headers={'Authorization':'Bearer '+access_token}, json=body,
                                    timeout=(3,12), allow_redirects=False)
            if response.status_code == 401 and challenge:
                return response.status_code, response.json()
            if response.status_code != 200:
                raise RuntimeError('Matrix-identitet kunne ikke opdateres (HTTP '+str(response.status_code)+').')
            return response.status_code, response.json()
        def query():
            _, result = post('keys/query', {'device_keys':{user:[]}})
            if result.get('failures'):
                raise RuntimeError('Matrix kunne ikke hente botkontoens identitetsnøgler.')
            return result
        remote = query()
        device = remote.get('device_keys',{}).get(user,{}).get(device_id)
        local = account.identity_keys
        if (not device or device.get('user_id') != user or device.get('device_id') != device_id or
                device.get('keys',{}).get('ed25519:'+device_id) != local['ed25519'] or
                device.get('keys',{}).get('curve25519:'+device_id) != local['curve25519']):
            raise RuntimeError('Bottens publicerede enhedsnøgler matcher ikke dens lokale enhed.')
        # Confirm the device really signed its own published keys.
        signature = device.get('signatures',{}).get(user,{}).get('ed25519:'+device_id)
        Ed25519PublicKey.from_public_bytes(unb64(local['ed25519'])).verify(unb64(signature), canonical(device))
        path = Path(path)
        if path.exists():
            bundle = json.loads(path.read_text(encoding='utf-8'))
        else:
            if any(remote.get(name,{}).get(user) for name in ('master_keys','self_signing_keys','user_signing_keys')):
                return manual('Botkontoen har allerede en identitet. Den eksisterende identitet er ikke nulstillet.')
            bundle = new_bundle(user,device_id,account)
            save(path,bundle)  # Persist before publishing so an interrupted upload can be resumed.
        if bundle['user_id'] != user:
            return manual('De gemte identitetsnøgler tilhører en anden botkonto.')
        self_key = Ed25519PrivateKey.from_private_bytes(unb64(bundle['self_signing_seed']))
        master_public = next(iter(bundle['master_key']['keys'].values()))
        if bundle['self_signing_key']['keys'] != {'ed25519:'+public(self_key):public(self_key)}:
            raise RuntimeError('Bottens gemte signeringsnøgle matcher ikke dens identitet.')
        for name in ('self_signing_key','user_signing_key'):
            verify(bundle[name],user,master_public)
        def compatible(snapshot):
            for local_name, remote_name in (('master_key','master_keys'),('self_signing_key','self_signing_keys'),('user_signing_key','user_signing_keys')):
                existing = snapshot.get(remote_name,{}).get(user)
                if existing and any(existing.get(field) != bundle[local_name].get(field) for field in ('user_id','usage','keys')):
                    return False
            return True
        if not compatible(remote):
            return manual('Botkontoens identitet er ændret. Den nye identitet er ikke overskrevet.')
        if not all(remote.get(name,{}).get(user) for name in ('master_keys','self_signing_keys','user_signing_keys')):
            # Recheck immediately before any write; do not knowingly reset keys
            # created by another client while this process was preparing its bundle.
            if not compatible(query()):
                return manual('Botkontoens identitet blev ændret under klargøringen.')
            body = {name:bundle[name] for name in ('master_key','self_signing_key','user_signing_key')}
            status, challenge = post('keys/device_signing/upload',body,challenge=True)
            if status == 401:
                if not password or not any(flow.get('stages') == ['m.login.password'] for flow in challenge.get('flows',[])):
                    return manual('Matrix kræver en godkendelsesmetode, som botten ikke kan udføre automatisk.')
                if not compatible(query()):
                    return manual('Botkontoens identitet blev ændret før godkendelsen.')
                auth = {'type':'m.login.password','identifier':{'type':'m.id.user','user':user},'password':password}
                if challenge.get('session'):
                    auth['session'] = challenge['session']
                post('keys/device_signing/upload',{**body,'auth':auth})
        device = sign(device,user,self_key)
        _, result = post('keys/signatures/upload',{user:{device_id:device}})
        if result.get('failures'):
            raise RuntimeError('Matrix accepterede ikke bottens enhedssignatur.')
        final = query()
        if not compatible(final):
            return manual('Botkontoens identitet blev ændret under verificeringen.')
        if not all(final.get(name,{}).get(user) for name in ('master_keys','self_signing_keys','user_signing_keys')):
            raise RuntimeError('Matrix mangler den publicerede signeringskæde.')
        verify(final['self_signing_keys'][user],user,master_public)
        verify(final['user_signing_keys'][user],user,master_public)
        signed_device = final.get('device_keys',{}).get(user,{}).get(device_id,{})
        verify(signed_device,user,public(self_key))
        return {'status':'verified','message':'Bottens enhed er signeret af botkontoens egen identitet.'}
