const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
function extract(name){const start=source.indexOf('function '+name+'(');return source.slice(start,source.indexOf('\n}\n',start)+3);}
const btn={style:{},dataset:{}},label={},dot={dataset:{}};
const row={style:{},querySelector:s=>({'.btn-update':btn,'.update-label':label,'.update-dot':dot}[s])};
const card={querySelector:s=>s==='.card-update-row'?row:{dataset:{status:'running'}}};
const context=vm.createContext({_updateStatusChecksInFlight:0,UPDATE_LABELS:{},INSTALLED_STATES:new Set(['running']),syncUpdateAllButton(){},hideUpdateRow(){throw Error('Unexpected hidden row');}});
vm.runInContext(extract('syncUpdateButtonLock')+'\n'+extract('applyUpdateStatus'),context);
context.applyUpdateStatus(card,{state:'failed',running:false});
assert.equal(btn.style.display,'');assert.equal(btn.disabled,false);assert.equal(btn.textContent,'Prøv igen');assert.equal(btn.dataset.updateAvailable,'0');
context.applyUpdateStatus(card,{state:'updating',running:true});assert.equal(btn.disabled,true);
context.applyUpdateStatus(card,{state:'update_available',running:false});assert.equal(btn.textContent,'Opdater');assert.equal(btn.dataset.updateRetry,'0');
context.applyUpdateStatus(card,{state:'up_to_date',running:false});assert.equal(btn.style.display,'none');
console.log('PASS failed retry, running lock, available update and up-to-date visibility');
