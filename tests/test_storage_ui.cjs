const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');
const section = (start, end) => source.slice(source.indexOf(start), source.indexOf(end, source.indexOf(start)));

function context() {
  const elements = {};
  const c = {elements, document: {getElementById(id) {
    return elements[id] ??= {value:'', hidden:false, elements:[], textContent:'', removeAttribute(name) {delete this[name];}};
  }}, _storagePools:[], _storageAccess:null, setTimeout, clearTimeout};
  vm.createContext(c);
  return c;
}

test('mounted NAS path can be selected without a Proxmox pool', () => {
  const c = context();
  c.document.getElementById('app-storage-target-type').value = 'path';
  vm.runInContext(section('function selectStoragePool()', 'async function loadProxmoxStorages('), c);
  vm.runInContext(section('function storageTargetSelection()', "document.getElementById('app-storage-target-type')?.addEventListener"), c);
  vm.runInContext('storageTargetSelection()', c);
  assert.equal(c.elements['app-storage-path-field'].hidden, false);
  assert.equal(c.elements['app-storage-pool-fields'].hidden, true);
  assert.equal(c.elements['app-storage-path'].required, true);
  assert.equal(c.elements['app-storage-pool'].required, false);
  assert.equal(c.elements['app-storage-folder'].required, false);
  c.elements['app-storage-target-type'].value = 'pool';
  vm.runInContext('storageTargetSelection()', c);
  assert.equal(c.elements['app-storage-path'].required, false);
  assert.equal(c.elements['app-storage-pool'].required, true);
});

test('progress displays transferred bytes and locks controls during migration', () => {
  const c = context();
  c.document.getElementById('app-storage-form').elements = [{disabled:false}];
  vm.runInContext(section('function renderStorageJob(', 'async function loadAppStorage('), c);
  vm.runInContext("renderStorageJob({running:true,message:'Kopierer',progress:{phase:'Kontrollerer filkopien',completed_bytes:150,total_bytes:300,copied_bytes:100,data_bytes:100}})", c);
  assert.equal(c.elements['app-storage-progress-bar'].value, 50);
  assert.equal(c.elements['app-storage-progress'].hidden, false);
  assert.equal(c.elements['app-storage-form'].elements[0].disabled, true);
  vm.runInContext("renderStorageJob({running:false,message:'Filerne er flyttet.'})", c);
  assert.equal(c.elements['app-storage-form'].elements[0].disabled, false);
  assert.equal(c.elements['app-storage-progress'].hidden, true);
});

test('status polling retries after a dropped connection without restarting migration', async () => {
  const c = context();
  c._settingsAppId = 'fjordlens'; c._storageGeneration = 2;
  c.fetch = async () => {throw new Error('offline');};
  const callbacks = [];
  c.setTimeout = fn => {callbacks.push(fn); return 1;};
  vm.runInContext(section('function pollAppStorage(', "document.getElementById('app-storage-mode')?.addEventListener"), c);
  vm.runInContext("pollAppStorage('fjordlens', 2)", c);
  await callbacks.shift()();
  assert.equal(callbacks.length, 1);
  assert.match(c.elements['app-storage-status'].textContent, /fortsætter på serveren/);
});
