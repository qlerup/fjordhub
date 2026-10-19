import copy
import sqlite3
from unittest.mock import Mock, patch

import pytest
from flask import Flask
from flask_login import LoginManager, UserMixin

from services.cloudflare import CloudflareAPI, CloudflareError, CloudflareService, hostname
from services.cloudflare_routes import create_cloudflare_blueprint
from services.web_security import check_csrf

ZONE = 'a' * 32
ACCOUNT = 'b' * 32
RECORD = 'c' * 32
TUNNEL = '11111111-2222-3333-4444-555555555555'
TOKEN = 'synthetic-cloudflare-token'


@pytest.fixture
def service(tmp_path):
    svc = CloudflareService(tmp_path / 'cloudflare.db', 'unit-test-encryption-secret')
    svc.enable(True)
    with patch.object(CloudflareAPI, 'all', return_value=[{'name':'example.com','id':ZONE,'account':{'id':ACCOUNT}}]), \
         patch.object(CloudflareAPI, 'call', return_value={'result':[]}):
        svc.connect('example.com', TOKEN)
    return svc


def test_tokens_encrypted_and_replace_persisted(service):
    settings = service.settings()
    assert settings['domains'][0]['name'] == 'example.com'
    assert TOKEN not in str(settings)
    with sqlite3.connect(service.db_path) as db:
        stored = db.execute('SELECT token FROM cloudflare_domains').fetchone()[0]
        assert stored != TOKEN
    assert service.domain(1)[1].token == TOKEN
    recreated = CloudflareService(service.db_path, 'unit-test-encryption-secret')
    assert recreated.domain(1)[1].token == TOKEN
    with patch.object(CloudflareAPI, 'all', return_value=[{'name':'example.com','id':ZONE,'account':{'id':ACCOUNT}}]), \
         patch.object(CloudflareAPI, 'call', return_value={'result':[]}):
        recreated.connect('example.com','replacement-token')
    assert len(recreated.settings()['domains']) == 1
    assert recreated.domain(1)[1].token == 'replacement-token'


def test_multiple_domains_and_disable(service):
    with patch.object(CloudflareAPI, 'all', return_value=[{'name':'other.dk','id':'d'*32,'account':{'id':ACCOUNT}}]), \
         patch.object(CloudflareAPI, 'call', return_value={'result':[]}):
        service.connect('other.dk', 'second-token')
    assert len(service.settings()['domains']) == 2
    assert service.domain(2)[1].token == 'second-token'
    service.enable(False)
    with patch.object(CloudflareAPI,'call') as call, pytest.raises(CloudflareError):
        service.delete_record(1,RECORD)
    call.assert_not_called()
    assert len(service.settings()['domains']) == 2
    service.disconnect(1)
    assert len(service.settings()['domains']) == 1


def test_pagination():
    api = CloudflareAPI(TOKEN)
    with patch.object(api, 'call', side_effect=[{'result':[1],'result_info':{'total_pages':2}}, {'result':[2],'result_info':{'total_pages':2}}]) as call:
        assert api.all('/zones', name='example.com') == [1,2]
        assert call.call_args_list[1].kwargs['params']['page'] == 2
        assert call.call_args_list[1].kwargs['params']['name'] == 'example.com'


@pytest.mark.parametrize('data', [
    {'type':'A','name':'evil.com','content':'1.2.3.4'},
    {'type':'A','name':'x','content':'::1'},
    {'type':'AAAA','name':'x','content':'1.2.3.4'},
    {'type':'A','name':'x','content':'1.2.3.4','ttl':True},
    {'type':'MX','name':'@','content':'mail.example.com','priority':-1},
    {'type':'TXT','name':'x','content':42},
    {'type':'CAA','name':'x','data':[]},
])
def test_invalid_records(service,data):
    with pytest.raises(CloudflareError):
        service.record_payload(data,'example.com')


def test_crud_scoped_to_zone(service):
    data = {'type':'A','name':'app','content':'1.2.3.4','ttl':300,'proxied':True}
    with patch.object(CloudflareAPI,'call', return_value={'result':{'type':'A'}}) as call:
        service.save_record(1,data)
        assert call.call_args.args == ('POST',f'/zones/{ZONE}/dns_records')
        assert call.call_args.kwargs['json']['ttl'] == 1
        assert call.call_args.kwargs['json']['name'] == 'app.example.com'
        service.save_record(1,data,RECORD)
        assert call.call_args.args[0] == 'PATCH'
        service.delete_record(1,RECORD)
        assert call.call_args.args == ('DELETE',f'/zones/{ZONE}/dns_records/{RECORD}')
    assert hostname('@','example.com') == 'example.com'
    assert service.record_payload({'type':'SRV','name':'_svc._tcp.example.com','data':{'port':443,'target':'x.example.com'}},'example.com')['data']['port'] == 443


def test_overview_dns_survives_tunnel_permission_failure(service):
    def all_results(self,path,**kwargs):
        if '/dns_records' in path:
            return [{'id':RECORD,'type':'A','name':'app.example.com'}]
        raise CloudflareError('Forbidden')
    with patch.object(CloudflareAPI,'all',all_results):
        result = service.overview(1)
    assert len(result['records']) == 1
    assert result['warnings']
    assert result['tunnels'] == []


def config():
    return {'version':7,'source':'cloudflare','config':{'originRequest':{'connectTimeout':30},'ingress':[
        {'hostname':'app.example.com','service':'http://old:8080','originRequest':{'noTLSVerify':True}},
        {'hostname':'elsewhere.dk','service':'http://private:80'},
        {'service':'http_status:404'},
    ]}}


def test_tunnel_update_preserves_all_other_configuration(service):
    original = config()
    with patch.object(CloudflareAPI,'call',side_effect=[original,{'result':{}}]) as call:
        # The API returns a wrapper around the configuration.
        call.side_effect = [{'result':copy.deepcopy(original)}, {'result':{}}]
        service.route(1,TUNNEL,{'hostname':'app.example.com','service':'http://new:8080','version':7})
        written = call.call_args.kwargs['json']['config']
    assert written['originRequest'] == original['config']['originRequest']
    assert written['ingress'][0]['originRequest'] == {'noTLSVerify':True}
    assert written['ingress'][0]['service'] == 'http://new:8080'
    assert written['ingress'][1:] == original['config']['ingress'][1:]


def test_tunnel_add_delete_and_stale_version(service):
    with patch.object(CloudflareAPI,'call',side_effect=[{'result':config()},{'result':{}}]) as call:
        service.route(1,TUNNEL,{'hostname':'new.example.com','service':'https://server:443','version':7})
        rules = call.call_args.kwargs['json']['config']['ingress']
        assert rules[-1] == {'service':'http_status:404'}
        assert rules[-2]['hostname'] == 'new.example.com'
    with patch.object(CloudflareAPI,'call',side_effect=[{'result':config()},{'result':{}}]) as call:
        service.route(1,TUNNEL,{'hostname':'app.example.com','version':7},delete=True)
        assert len(call.call_args.kwargs['json']['config']['ingress']) == 2
    with patch.object(CloudflareAPI,'call',return_value={'result':config()}) as call, pytest.raises(CloudflareError):
        service.route(1,TUNNEL,{'hostname':'new.example.com','service':'http://server:80','version':6})
    assert call.call_count == 1


def test_upstream_credentials_never_forwarded():
    response = Mock(ok=False,status_code=403)
    response.json.return_value = {'success':False,'errors':[{'code':9109,'message':TOKEN}]}
    with patch('services.cloudflare.requests.request',return_value=response) as call, pytest.raises(CloudflareError) as error:
        CloudflareAPI(TOKEN).call('GET','/zones')
    assert TOKEN not in str(error.value)
    assert call.call_args.kwargs['allow_redirects'] is False


def test_admin_and_csrf(service):
    app = Flask(__name__)
    app.secret_key = 'test-session'
    app.register_blueprint(create_cloudflare_blueprint(service))
    manager = LoginManager(app)
    class User(UserMixin):
        id = 'admin'
        is_admin = True
    @manager.user_loader
    def load(uid):
        user = User()
        user.is_admin = uid == 'admin'
        return user
    app.before_request(check_csrf)
    client = app.test_client()
    assert client.get('/api/cloudflare/settings').status_code == 403
    with client.session_transaction() as session:
        session['_user_id'] = 'normal'
    assert client.get('/api/cloudflare/settings').status_code == 403
    with client.session_transaction() as session:
        session['_user_id'] = 'admin'
        session['hub_csrf'] = 'valid-token'
    assert client.get('/api/cloudflare/settings').status_code == 200
    assert client.post('/api/cloudflare/settings',json={'enabled':False}).status_code == 403
    response = client.post('/api/cloudflare/settings',json={'enabled':False},headers={'X-CSRF-Token':'valid-token'})
    assert response.status_code == 200
    assert response.headers['Cache-Control'] == 'no-store'


def test_hub_integration_and_page(tmp_path, monkeypatch):
    import app as hub
    from services.auth import AuthService
    from services.install_state import InstallState
    auth = AuthService(tmp_path / 'auth.db')
    admin = auth.create_user('cloudflare-owner','long-secure-password',role='admin')
    reader = auth.create_user('cloudflare-reader','long-secure-password',role='user')
    monkeypatch.setattr(hub,'_auth',auth)
    monkeypatch.setattr(hub,'_install_state',InstallState(tmp_path))
    client = hub.app.test_client()
    assert client.get('/api/cloudflare/settings').status_code == 401
    with client.session_transaction() as session:
        session['_user_id'] = auth.get_by_id(reader).get_id()
        session['_fresh'] = True
    assert client.get('/api/cloudflare/settings').status_code == 403
    with client.session_transaction() as session:
        session['_user_id'] = auth.get_by_id(admin).get_id()
    assert client.get('/settings/cloudflare').status_code == 200
    assert b'Cloudflare' in client.get('/settings').data
    assert client.post('/api/cloudflare/settings',json={'enabled':True},headers={'X-CSRF-Token':'invalid'}).status_code == 403
