const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
const text=fs.readFileSync(path.join(__dirname,'../templates/wizard.html'),'utf8');
const between=(a,b)=>text.slice(text.indexOf(a),text.indexOf(b,text.indexOf(a)));
test('reusing GPU runtime does not wait for a Docker restart',()=>{
  const c={localStorage:{removeItem(){}},setGpuAutoButtonRunning(){},setGpuAutoStatus(s){c.status=s;},_escapeHtml:s=>s,
    gpuSetupSeenRunning:true,waitForGpuTestReady(){c.waited=true;},runGpuPreflight(){c.tested=true;}};
  vm.runInNewContext(between('function renderGpuSetupState(', 'async function pollGpuSetupStatus(')+'\nrenderGpuSetupState({ok:true,restart_scheduled:false});',c);
  assert.equal(c.waited,undefined);assert.equal(c.tested,true);
  assert.ok(c.status.includes('Ingen Docker-genstart'));
});
test('scheduled restart still waits for readiness',()=>{
  const c={localStorage:{removeItem(){}},setGpuAutoButtonRunning(){},setGpuAutoStatus(){},_escapeHtml:s=>s,
    gpuSetupSeenRunning:true,waitForGpuTestReady(){c.waited=true;},runGpuPreflight(){c.tested=true;}};
  vm.runInNewContext(between('function renderGpuSetupState(', 'async function pollGpuSetupStatus(')+'\nrenderGpuSetupState({ok:true,restart_scheduled:true});',c);
  assert.equal(c.waited,true);assert.equal(c.tested,undefined);
});
test('full setup selection survives the asynchronous preflight response',async()=>{
  const elements={};
  const c={gpuFullSetup:true,APP_ID:'fjordflix',document:{getElementById(id){return elements[id]??={hidden:false,style:{}};}},
    _escapeHtml:s=>s,renderGpuVideoCommands(){},showFullGpuSetup(){c.restored=true;},
    fetch:async()=>({text:async()=>JSON.stringify({ok:true,hdr_warning:'OpenCL missing'})})};
  vm.createContext(c);
  vm.runInContext(between('let gpuPreflightRunning =', 'function useGpuSettings()'),c);
  await vm.runInContext('runGpuPreflight()',c);
  assert.equal(c.restored,true);
  assert.equal(elements['gpu-setup-instructions'].hidden,false);
  assert.ok(elements['gpu-test-result'].innerHTML.includes('ikke klar'));
});
