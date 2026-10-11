"""Run on a disposable Docker test host with new module sources on stdin.

Uses unique names/labels, synthetic data and no ports; never touches installed apps.
"""
import json
import subprocess
import sys
import tempfile
import types
import uuid
from pathlib import Path

payload=json.load(sys.stdin)
module=types.ModuleType('services.compose_env')
exec(payload['compose_env'],module.__dict__)
sys.modules['services']=types.ModuleType('services')
sys.modules['services.compose_env']=module
namespace={};exec(payload['uninstaller'],namespace)
remove_runtime=namespace['remove_runtime']
run_id='fh-uninstall-'+uuid.uuid4().hex[:10]
label='dk.fjordhub.uninstall-test='+run_id
image=subprocess.check_output(['docker','inspect','fjordhub','--format','{{.Image}}'],text=True).strip()

def run(args):
    result=subprocess.run(args,capture_output=True,text=True,timeout=90)
    if result.returncode:raise RuntimeError('Test command failed: '+args[0]+' '+args[1])
    return result.stdout.strip()

volumes=[]
projects=[]
try:
    with tempfile.TemporaryDirectory(prefix=run_id+'-') as directory:
        root=Path(directory)
        for app_id in payload['apps']:
            project=run_id+'-'+app_id
            folder=root/app_id;folder.mkdir();data=folder/'data';data.mkdir()
            saved=data/'saved.txt';saved.write_text('preserved')
            main=project+'-app';helper=project+'-helper';volume=project+'-data'
            volumes.append(volume)
            definition={'container_name':main}
            sleeper='import signal,time,sys; signal.signal(signal.SIGTERM,lambda *_:sys.exit(0)); time.sleep(600)'
            common={'image':image,'command':['python','-c',sleeper],
                    'mem_limit':'64m','labels':{'dk.fjordhub.uninstall-test':run_id},
                    'cap_drop':['ALL'],'security_opt':['no-new-privileges:true']}
            config={'name':project,'services':{
                'app':{**common,'container_name':main,'volumes':[str(data)+':/data',volume+':/persistent']},
                'helper':{**common,'container_name':helper}},
                'networks':{'default':{'internal':True,'labels':{'dk.fjordhub.uninstall-test':run_id}}},
                'volumes':{volume:{'name':volume,'labels':{'dk.fjordhub.uninstall-test':run_id}}}}
            (folder/'compose.yaml').write_text(json.dumps(config));projects.append(folder)
            run(['docker','compose','-f',str(folder/'compose.yaml'),'up','-d'])
            # A profile/worker outside the Compose file must be removed as an orphan.
            child=project+'-dynamic'
            run(['docker','run','-d','--name',child,'--network','none','--label',label,
                 '--label','com.docker.compose.project='+project,'--label','com.docker.compose.service=dynamic',
                 '--label','com.docker.compose.oneoff=False','--label','com.docker.compose.config-hash=fixture',
                 image,'python','-c',sleeper])
            remove_runtime(definition,folder,protected_containers={'fjordhub'})
            assert not run(['docker','ps','-a','--filter','label=com.docker.compose.project='+project,'--format','{{.ID}}'])
            assert not run(['docker','network','ls','--filter','label=com.docker.compose.project='+project,'--format','{{.ID}}'])
            run(['docker','volume','inspect',volume])
            assert saved.read_text()=='preserved' and (folder/'compose.yaml').exists()
            print('PASS '+app_id+': main, helper, dynamic orphan and network removed; data and volume preserved',flush=True)
finally:
    containers=run(['docker','ps','-aq','--filter','label='+label]).split()
    if containers:run(['docker','rm','-f',*containers])
    networks=run(['docker','network','ls','-q','--filter','label='+label]).split()
    if networks:run(['docker','network','rm',*networks])
    for volume in volumes:
        subprocess.run(['docker','volume','rm',volume],capture_output=True,text=True,timeout=20)
