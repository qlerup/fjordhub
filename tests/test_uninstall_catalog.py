"""Exercise the same lifecycle contract for every catalog app and legacy names."""
import json
import subprocess
import threading
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from services.install_state import InstallState
from services.installer import Installer
from services.uninstaller import remove_runtime
from services.update_manager import UpdateManager

CATALOG=[json.loads(p.read_text(encoding='utf-8')) for p in
         sorted((Path(__file__).resolve().parents[1]/'app_registry').glob('*.json'))]


@pytest.mark.parametrize('definition',CATALOG,ids=[a['id'] for a in CATALOG])
def test_every_catalog_app_removes_project_children_but_preserves_data(tmp_path,definition):
    project=definition['id']+'-test';main=definition['container_name']
    config={'name':project,'services':{'app':{'container_name':main}}}
    containers={main:project,main+'-helper':project,main+'-dynamic':project,'other-app':'foreign'}
    original=dict(containers)
    data=tmp_path/'data';data.mkdir();(data/'saved.db').write_bytes(b'precious data')
    (tmp_path/'.env').write_text('DATA_DIR=./data\n')
    calls=[]
    def run(args,**kwargs):
        calls.append(args)
        if args[:3]==['docker','compose','config']:
            output=json.dumps(config)
        elif args[:3]==['docker','compose','down']:
            assert '--remove-orphans' in args and '--volumes' not in args
            for name in list(containers):
                if containers[name]==project:del containers[name]
            output=''
        else:
            filter_value=args[args.index('--filter')+1]
            if filter_value.startswith('name='):
                name=filter_value.removeprefix('name=^/').removesuffix('$')
                output=('id '+containers[name]) if name in containers else ''
            else:
                output='\n'.join(name for name,p in containers.items() if p==project)
        return subprocess.CompletedProcess(args,0,output,'')
    with patch('services.uninstaller.subprocess.run',side_effect=run):
        remove_runtime(definition,tmp_path)
    assert containers=={'other-app':'foreign'}
    assert len(original)==4
    assert (data/'saved.db').read_bytes()==b'precious data'
    assert (tmp_path/'.env').read_text()=='DATA_DIR=./data\n'


def test_legacy_name_in_another_project_cannot_be_silently_forgotten(tmp_path):
    definition={'container_name':'fjord3d','legacy_container_names':['fjordshare']}
    config={'name':'new-project','services':{'app':{'container_name':'fjord3d'}}}
    results=[subprocess.CompletedProcess([],0,json.dumps(config),''),
             subprocess.CompletedProcess([],0,'',''),subprocess.CompletedProcess([],0,'old-id old-project','')]
    with patch('services.uninstaller.subprocess.run',side_effect=results) as run:
        with pytest.raises(RuntimeError,match='anden eller ukendt'):
            remove_runtime(definition,tmp_path)
    assert not any(call.args[0][:3]==['docker','compose','down'] for call in run.call_args_list)


def test_wrong_compose_directory_is_rejected_even_if_app_container_is_absent(tmp_path):
    config={'name':'another-project','services':{'app':{'container_name':'another-app'}}}
    with patch('services.uninstaller.subprocess.run',return_value=subprocess.CompletedProcess([],0,json.dumps(config),'')) as run:
        with pytest.raises(RuntimeError,match='forventede app'):
            remove_runtime({'container_name':'fjordvpn'},tmp_path)
    assert run.call_count==1


def test_shared_project_cannot_remove_another_catalog_app(tmp_path):
    config={'name':'shared','services':{'app':{'container_name':'fjordvpn'}}}
    values=[json.dumps(config),'id shared','fjordvpn\nfjordseed']
    with patch('services.uninstaller.subprocess.run',side_effect=[subprocess.CompletedProcess([],0,v,'') for v in values]) as run:
        with pytest.raises(RuntimeError,match='deles med en anden app'):
            remove_runtime({'container_name':'fjordvpn'},tmp_path,protected_containers={'fjordseed'})
    assert not any(call.args[0][:3]==['docker','compose','down'] for call in run.call_args_list)


def test_uninstall_is_blocked_for_entire_update_worker(tmp_path):
    state=InstallState(tmp_path);state.register('fjordvpn',str(tmp_path))
    installer=Installer(state);manager=UpdateManager(state,installer.reserve_operation)
    started=threading.Event();release=threading.Event();finished=threading.Event()
    def update(*args):
        started.set()
        assert release.wait(5)
        finished.set()
    previous_threads=set(threading.enumerate())
    with patch.object(manager,'_run_update',side_effect=update):
        assert manager.start_update({'id':'fjordvpn'})[1]==202
        assert started.wait(2)
        worker=next(t for t in threading.enumerate() if t not in previous_threads)
        try:
            with pytest.raises(RuntimeError,match='allerede'):
                with installer.reserve_operation('fjordvpn'):pass
            assert not installer.start_install({'id':'fjordvpn'},{})
        finally:release.set()
        assert finished.wait(2)
    worker.join(timeout=2)
    assert not installer._active_installs


def test_update_and_queued_batch_are_blocked_during_uninstall(tmp_path):
    state=InstallState(tmp_path);state.register('fjordvpn',str(tmp_path))
    installer=Installer(state);manager=UpdateManager(state,installer.reserve_operation)
    with installer.reserve_operation('fjordvpn'):
        assert manager.start_update({'id':'fjordvpn'})[1]==409
        with patch.object(manager,'get_status',return_value={'update_available':True}):
            payload,status=manager.start_all_updates([{'id':'fjordvpn'}])
        assert status==200 and payload['queued']==[] and payload['skipped']==['fjordvpn']
    assert not manager._reservations


def test_failed_update_thread_start_releases_shared_reservation(tmp_path):
    state=InstallState(tmp_path);state.register('fjordvpn',str(tmp_path))
    installer=Installer(state);manager=UpdateManager(state,installer.reserve_operation)
    with patch('services.update_manager.threading.Thread',side_effect=RuntimeError('thread failed')):
        with pytest.raises(RuntimeError):manager.start_update({'id':'fjordvpn'})
    assert not manager._reservations and not installer._active_installs


def test_finished_batch_does_not_release_a_new_update_reservation(tmp_path):
    state=InstallState(tmp_path);state.register('fjordvpn',str(tmp_path))
    installer=Installer(state);manager=UpdateManager(state,installer.reserve_operation)
    manager._reserve('fjordvpn');manager._batch_lock.acquire()
    def followup():
        manager._release('fjordvpn')
        manager._reserve('fjordvpn')
    future=Mock();future.result.side_effect=followup
    pool=Mock();pool.submit.return_value=future
    context=Mock();context.__enter__=Mock(return_value=pool);context.__exit__=Mock(return_value=False)
    try:
        with patch('services.update_manager.ThreadPoolExecutor',return_value=context):
            manager._run_all_updates([({'id':'fjordvpn'},tmp_path)])
        assert 'fjordvpn' in installer._active_installs
        assert 'fjordvpn' in manager._reservations
    finally:manager._release('fjordvpn')


def test_final_check_catches_recreated_container_with_new_project_label(tmp_path):
    config={'name':'original','services':{'app':{'container_name':'fjordvpn'}}}
    values=[json.dumps(config),'id original','','','new-id']
    with patch('services.uninstaller.subprocess.run',side_effect=[subprocess.CompletedProcess([],0,v,'') for v in values]):
        with pytest.raises(RuntimeError,match='findes stadig'):
            remove_runtime({'container_name':'fjordvpn'},tmp_path)


def test_leftover_network_is_not_reported_as_success(tmp_path):
    config={'name':'original','services':{'app':{'container_name':'fjordvpn'}}}
    values=[json.dumps(config),'id original','','','','remaining-network']
    with patch('services.uninstaller.subprocess.run',side_effect=[subprocess.CompletedProcess([],0,v,'') for v in values]):
        with pytest.raises(RuntimeError,match='netværk er stadig'):
            remove_runtime({'container_name':'fjordvpn'},tmp_path)


@pytest.mark.parametrize('action',['start','stop'])
def test_start_stop_cannot_race_with_uninstall(tmp_path,action):
    import app as hub
    from services.auth import AuthService
    auth=AuthService(tmp_path/'auth.db');auth.create_user('admin','test-password',role='admin')
    state=InstallState(tmp_path);installer=Installer(state)
    with patch.object(hub,'_auth',auth),patch.object(hub,'_installer',installer), \
         patch.object(hub,'_get_app',return_value={'id':'fjordvpn'}), \
         patch.object(hub.docker_mgr,action) as operation:
        with installer.reserve_operation('fjordvpn'),hub.app.test_client() as client:
            client.post('/login',data={'username':'admin','password':'test-password'})
            assert client.post('/apps/fjordvpn/'+action).status_code==409
        operation.assert_not_called()


def test_stale_start_click_cannot_recreate_uninstalled_app(tmp_path):
    import app as hub
    from services.auth import AuthService
    auth=AuthService(tmp_path/'auth.db');auth.create_user('admin','test-password',role='admin')
    with patch.object(hub,'_auth',auth),patch.object(hub,'_get_app',return_value={'id':'fjordvpn'}), \
         patch.object(hub.docker_mgr,'get_status',return_value={'state':'not_installed'}), \
         patch.object(hub.docker_mgr,'start') as start:
        with hub.app.test_client() as client:
            client.post('/login',data={'username':'admin','password':'test-password'})
            assert client.post('/apps/fjordvpn/start').status_code==409
        start.assert_not_called()
