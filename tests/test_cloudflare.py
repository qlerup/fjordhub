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


def test_token_only_connection_detects_domain_and_replaces_token(service):
    zones=[{'name':'example.com','id':ZONE,'account':{'id':ACCOUNT}}]
    with patch.object(CloudflareAPI,'all',return_value=zones) as listing, \
         patch.object(CloudflareAPI,'call',return_value={'result':[]}):
        result=service.connect(None,'new-token')
    listing.assert_called_once_with('/zones')
    assert result=={'connected_domain':'example.com'}
    assert len(service.settings()['domains'])==1
    assert service.domain(1)[1].token=='new-token'
    assert 'new-token' not in str(result)


def test_multi_zone_token_requires_selection_without_saving_it(service):
    zones=[{'name':'example.com','id':ZONE,'account':{'id':ACCOUNT}},
           {'name':'other.dk','id':'d'*32,'account':{'id':ACCOUNT}}]
    before=service.settings()
    with patch.object(CloudflareAPI,'all',return_value=zones),patch.object(CloudflareAPI,'call') as call:
        result=service.connect(None,'multi-zone-token')
    assert result=={'selection_required':True,'choices':['example.com','other.dk']}
    call.assert_not_called()
    assert service.settings()==before and service.domain(1)[1].token==TOKEN
    with patch.object(CloudflareAPI,'all',return_value=zones), \
         patch.object(CloudflareAPI,'call',return_value={'result':[]}):
        assert service.connect('other.dk','multi-zone-token')=={'connected_domain':'other.dk'}
    assert len(service.settings()['domains'])==2


def test_discovery_with_no_zones_or_inaccessible_choice_preserves_existing_token(service):
    for name,zones in [(None,[]),('other.dk',[{'name':'example.com','id':ZONE,'account':{'id':ACCOUNT}}])]:
        with patch.object(CloudflareAPI,'all',return_value=zones),pytest.raises(CloudflareError):
            service.connect(name,'wrong-token')
    assert service.domain(1)[1].token==TOKEN


def test_api_accepts_token_without_domain(service):
    app=Flask(__name__);app.secret_key='synthetic-session'
    app.register_blueprint(create_cloudflare_blueprint(service))
    manager=LoginManager(app)
    class User(UserMixin):
        id='admin'
        is_admin=True
    manager.user_loader(lambda uid:User())
    app.before_request(check_csrf)
    client=app.test_client()
    with client.session_transaction() as session:
        session['_user_id']='admin';session['hub_csrf']='synthetic-csrf'
    zones=[{'name':'example.com','id':ZONE,'account':{'id':ACCOUNT}}]
    with patch.object(CloudflareAPI,'all',return_value=zones), \
         patch.object(CloudflareAPI,'call',return_value={'result':[]}):
        response=client.post('/api/cloudflare/domains',json={'token':TOKEN},headers={'X-CSRF-Token':'synthetic-csrf'})
    assert response.status_code==200 and response.json['connected_domain']=='example.com'
    assert TOKEN not in str(response.json)
    with patch.object(CloudflareAPI,'call',return_value={'result':{'id':RECORD}}):
        payload={'kind':'dns','type':'A','name':'new','content':'192.0.2.10','ttl':60}
        assert client.post('/api/cloudflare/domains/1/addresses',json=payload).status_code==403
        response=client.post('/api/cloudflare/domains/1/addresses',json=payload,headers={'X-CSRF-Token':'synthetic-csrf'})
        assert response.status_code==200 and response.json['record']['id']==RECORD


def test_named_connections_keep_separate_tokens_for_multiple_domains(service):
    for name,zone,token,label in [('example.com',ZONE,'private-token','Privat'),('other.dk','d'*32,'work-token','Arbejde')]:
        with patch.object(CloudflareAPI,'all',return_value=[{'name':name,'id':zone,'account':{'id':ACCOUNT}}]), \
             patch.object(CloudflareAPI,'call',return_value={'result':[]}):
            service.connect(None,token,label=label)
    domains={d['name']:d for d in service.settings()['domains']}
    assert domains['example.com']['label']=='Privat' and domains['other.dk']['label']=='Arbejde'
    assert service.domain(domains['example.com']['id'])[1].token=='private-token'
    assert service.domain(domains['other.dk']['id'])[1].token=='work-token'
    assert 'private-token' not in str(domains) and 'work-token' not in str(domains)


@pytest.mark.parametrize('label',['','  ','x'*81,'line\nbreak',True,{}])
def test_invalid_connection_name_is_rejected_before_provider_calls(service,label):
    with patch.object(CloudflareAPI,'all') as provider,pytest.raises(CloudflareError):
        service.connect(None,TOKEN,label=label)
    provider.assert_not_called()


def test_existing_database_is_migrated_without_losing_saved_tokens(tmp_path,service):
    path=tmp_path/'old-cloudflare.db'
    encrypted=service.cipher.encrypt(TOKEN.encode()).decode()
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE cloudflare_domains(id INTEGER PRIMARY KEY,name TEXT NOT NULL UNIQUE,zone_id TEXT NOT NULL,account_id TEXT NOT NULL,token TEXT NOT NULL)')
        db.execute('INSERT INTO cloudflare_domains VALUES(?,?,?,?,?)',(1,'example.com',ZONE,ACCOUNT,encrypted))
        db.execute('CREATE TABLE cloudflare_preferences(id INTEGER PRIMARY KEY,enabled INTEGER NOT NULL)')
        db.execute('INSERT INTO cloudflare_preferences VALUES(1,1)')
    migrated=CloudflareService(path,'unit-test-encryption-secret')
    assert migrated.settings()['domains'][0]['label']=='example.com'
    assert migrated.domain(1)[1].token==TOKEN
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT token FROM cloudflare_domains').fetchone()[0]==encrypted


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


def test_overview_returns_editable_origin_overrides_only_for_current_zone(service):
    original = config()
    original['config']['ingress'][0]['originRequest'].update(originServerName='server.example.com', httpHostHeader='app.example.com', caPool='/private/ca.pem')
    with patch.object(CloudflareAPI, 'all', side_effect=[[], [{'id':TUNNEL,'config_src':'cloudflare'}]]), \
         patch.object(CloudflareAPI, 'call', return_value={'result':original}):
        overview = service.overview(1)
    routes = overview['tunnels'][0]['routes']
    assert len(routes) == 1
    assert routes[0]['originRequest'] == {'noTLSVerify':True,'originServerName':'server.example.com','httpHostHeader':'app.example.com'}


def config():
    return {'version':7,'source':'cloudflare','config':{'originRequest':{'connectTimeout':30},'ingress':[
        {'hostname':'app.example.com','service':'http://old:8080','originRequest':{'noTLSVerify':True}},
        {'hostname':'elsewhere.dk','service':'http://private:80'},
        {'service':'http_status:404'},
    ]}}


def test_create_tunnel_address_creates_proxied_dns_and_preserves_other_routes(service):
    data={'kind':'tunnel','name':'new','tunnel_id':TUNNEL,'service':'http://192.168.1.20:8096','version':7}
    with patch.object(CloudflareAPI,'all',return_value=[]) as listing, \
         patch.object(CloudflareAPI,'call',side_effect=[{'result':config()},{'result':{'id':RECORD}}, {'result':config()},{'result':{}}]) as call:
        assert service.create_address(1,data)['id']==RECORD
    listing.assert_called_once_with(f'/zones/{ZONE}/dns_records',name='new.example.com')
    created=call.call_args_list[1].kwargs['json']
    assert created=={'type':'CNAME','name':'new.example.com','content':TUNNEL+'.cfargotunnel.com','proxied':True,'ttl':1}
    written=call.call_args.kwargs['json']['config']
    assert written['ingress'][-2]=={'hostname':'new.example.com','service':data['service']}
    assert written['ingress'][:-2]==config()['config']['ingress'][:-1]
    assert written['originRequest']==config()['config']['originRequest']


def test_create_tunnel_refuses_existing_dns_and_route_and_stale_version(service):
    base={'kind':'tunnel','name':'new','tunnel_id':TUNNEL,'service':'http://192.168.1.20:80','version':7}
    for data,existing in [(base,[{'id':RECORD}]),({**base,'name':'app'},[]),({**base,'version':6},[])]:
        with patch.object(CloudflareAPI,'all',return_value=existing), \
             patch.object(CloudflareAPI,'call',return_value={'result':config()}) as call, pytest.raises(CloudflareError):
            service.create_address(1,data)
        assert all(c.args[0]=='GET' for c in call.call_args_list)


@pytest.mark.parametrize('rollback_fails',[False,True])
def test_tunnel_failure_rolls_back_only_new_dns_or_reports_partial_state(service,rollback_fails):
    data={'kind':'tunnel','name':'new','tunnel_id':TUNNEL,'service':'http://192.168.1.20:80','version':7}
    replies=[{'result':config()},{'result':{'id':RECORD}},CloudflareError('Tunnel Edit mangler'),
             CloudflareError('DNS kunne ikke fjernes') if rollback_fails else {'result':{}}]
    with patch.object(CloudflareAPI,'all',return_value=[]),patch.object(CloudflareAPI,'call',side_effect=replies) as call,pytest.raises(CloudflareError) as error:
        service.create_address(1,data)
    assert call.call_args.args==('DELETE',f'/zones/{ZONE}/dns_records/{RECORD}')
    assert ('ikke fjernes' in str(error.value)) is rollback_fails


def test_create_normal_dns_uses_same_payload_validation(service):
    with patch.object(CloudflareAPI,'call',return_value={'result':{'id':RECORD}}) as call:
        service.create_address(1,{'kind':'dns','type':'A','name':'media','content':'192.0.2.10','ttl':60})
    assert call.call_args.args==('POST',f'/zones/{ZONE}/dns_records')
    assert call.call_args.kwargs['json']['name']=='media.example.com'


@pytest.mark.parametrize('address',[None,123,'http://192.168.1.20:99999','http://user:password@192.168.1.20','http://host with spaces:80'])
def test_invalid_tunnel_service_never_creates_dns(service,address):
    with patch.object(CloudflareAPI,'call') as call,pytest.raises(CloudflareError):
        service.create_address(1,{'kind':'tunnel','name':'new','tunnel_id':TUNNEL,'service':address,'version':7})
    call.assert_not_called()


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


@pytest.mark.parametrize('verify', [True, False, None])
def test_route_tls_overrides_preserve_other_options_and_routes(service, verify):
    original = config()
    original['config']['ingress'][0]['originRequest'].update(connectTimeout=12, originServerName='old.example.com')
    with patch.object(CloudflareAPI, 'call', side_effect=[{'result': copy.deepcopy(original)}, {'result': {}}]) as call:
        service.route(1, TUNNEL, {'hostname': 'app.example.com', 'service': 'https://192.0.2.5:3443', 'version': 7,
            'originRequest': {'noTLSVerify': verify, 'originServerName': None, 'httpHostHeader': 'app.example.com'}})
    written = call.call_args.kwargs['json']['config']
    assert written['ingress'][1:] == original['config']['ingress'][1:]
    assert written['originRequest'] == original['config']['originRequest']
    options = written['ingress'][0]['originRequest']
    assert options['connectTimeout'] == 12
    assert options['httpHostHeader'] == 'app.example.com'
    assert 'originServerName' not in options
    if verify is None:
        assert 'noTLSVerify' not in options
    else:
        assert options['noTLSVerify'] is verify


@pytest.mark.parametrize('overrides', [None, [], {'noTLSVerify': 'true'}, {'noTLSVerify': 1},
    {'httpHostHeader': 'bad\r\nHeader'}, {'httpHostHeader': 'bad\x00host'}, {'originServerName': 'https://host'}, {'unknown': True}])
def test_bad_origin_options_rejected_before_any_provider_write(service, overrides):
    data = {'kind': 'tunnel', 'name': 'new', 'tunnel_id': TUNNEL, 'hostname': 'new.example.com',
            'service': 'https://192.0.2.5:3443', 'version': 7, 'originRequest': overrides}
    with patch.object(CloudflareAPI, 'call') as call:
        with pytest.raises(CloudflareError):
            service.create_address(1, data)
        with pytest.raises(CloudflareError):
            service.route(1, TUNNEL, data)
    call.assert_not_called()


def test_create_address_sends_explicit_tls_options(service):
    options = {'noTLSVerify': True, 'originServerName': 'server.example.com', 'httpHostHeader': None}
    with patch.object(CloudflareAPI, 'all', return_value=[]), patch.object(CloudflareAPI, 'call',
        side_effect=[{'result':config()}, {'result':{'id':RECORD}}, {'result':config()}, {'result':{}}]) as call:
        service.create_address(1, {'kind':'tunnel','name':'new','tunnel_id':TUNNEL,
            'service':'https://192.0.2.5:3443','version':7,'originRequest':options})
    written = call.call_args.kwargs['json']['config']
    assert written['ingress'][-2]['originRequest'] == {'noTLSVerify': True, 'originServerName': 'server.example.com'}
    assert written['ingress'][:-2] == config()['config']['ingress'][:-1]


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
