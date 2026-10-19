(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  let state = {domains: [], enabled: false}, view = null, recordId = null, routeTunnel = null, generation = 0;
  const status = (message, error = false) => { $('cf-status').textContent = message; $('cf-status').dataset.error = String(error); };
  async function api(path, method = 'GET', data) {
    const response = await fetch('/api/cloudflare/' + path, {method, headers: {'Content-Type': 'application/json'}, ...(data === undefined ? {} : {body: JSON.stringify(data)})});
    const result = await response.json();
    if (!response.ok || !result.ok) throw new Error(result.error || 'Forespørgslen mislykkedes.');
    return result;
  }
  function element(tag, value, className) { const node = document.createElement(tag); node.textContent = value; if (className) node.className = className; return node; }
  function button(label, action) { const b = element('button', label, 'btn-settings'); b.type = 'button'; b.onclick = () => run(b, action); return b; }
  async function run(control, action) {
    if (control.disabled) return;
    control.disabled = true;
    try { await action(); } catch (e) { status(e.message, true); } finally { control.disabled = false; }
  }
  const domainPath = () => 'domains/' + $('cf-domains').value;
  function renderSettings(result) {
    state = result;
    $('cf-enabled').checked = state.enabled;
    $('cf-enabled').disabled = false;
    $('cf-content').hidden = !state.enabled;
    const previous = $('cf-domains').value;
    $('cf-domains').replaceChildren(...state.domains.map(d => { const o = element('option', d.label && d.label !== d.name ? d.label + ' · ' + d.name : d.name); o.value = d.id; return o; }));
    if (state.domains.some(d => String(d.id) === previous)) $('cf-domains').value = previous;
    $('cf-empty').hidden = state.domains.length > 0;
    for (const id of ['cf-domains','cf-refresh','cf-disconnect']) $(id).disabled = !state.domains.length;
    $('cf-overview').hidden = true;
  }
  async function refresh() {
    const epoch = ++generation;
    view = null;
    $('cf-overview').hidden = true;
    if (!state.enabled || !$('cf-domains').value) return;
    const path = domainPath();
    status('Henter DNS-poster og tunneler …');
    const result = await api(path);
    if (epoch !== generation || path !== domainPath()) return;
    view = result;
    renderRecords(); renderTunnels();
    $('cf-overview').hidden = false;
    status(result.records.length + ' DNS-poster indlæst.');
  }
  function renderRecords() {
    const query = $('cf-search').value.toLowerCase();
    const records = view.records.filter(r => [r.name,r.type,r.content,JSON.stringify(r.data || {})].join(' ').toLowerCase().includes(query));
    const nodes = records.map(r => {
      const item = element('div', '', 'cf-item');
      item.append(element('strong', r.name), element('p', r.type + ' · ' + (r.proxied ? 'Proxy aktiv' : 'Kun DNS') + ' · TTL ' + (r.ttl === 1 ? 'automatisk' : r.ttl)));
      item.append(element('p', r.content || JSON.stringify(r.data)));
      if (r.type === 'CNAME' && r.content?.replace(/\.$/, '').endsWith('.cfargotunnel.com')) item.append(element('p', 'Cloudflare Tunnel'));
      if (r.comment) item.append(element('p', r.comment));
      const actions = element('div', '', 'cf-actions');
      actions.append(button('Rediger', () => editRecord(r)), button('Slet', async () => {
        if (!confirm('Slet DNS-posten ' + r.name + ' (' + r.type + ')?\nEn eventuel tunnelregel bevares.')) return;
        await api(domainPath() + '/records/' + r.id, 'DELETE'); await refresh();
      })); item.append(actions); return item;
    });
    $('cf-records').replaceChildren(...(nodes.length ? nodes : [element('p', 'Ingen DNS-poster matcher.') ]));
  }
  function editRecord(record = {}) {
    recordId = record.id || null;
    $('cf-editor-title').textContent = recordId ? 'Rediger DNS-post' : 'Opret DNS-post';
    $('cf-record-form').querySelector('.cf-form-error').textContent = '';
    $('cf-type').value = record.type || 'A'; $('cf-type').disabled = Boolean(recordId);
    $('cf-record-name').value = record.name || '';
    const structured = Boolean(record.data && Object.keys(record.data).length && !['A','AAAA','CNAME','TXT','MX','NS','PTR'].includes(record.type));
    $('cf-structured').checked = structured;
    $('cf-value').value = structured ? JSON.stringify(record.data, null, 2) : (record.content || '');
    $('cf-ttl').value = record.ttl || 1; $('cf-priority').value = record.priority ?? 10;
    $('cf-proxy').checked = record.proxied || false; $('cf-comment').value = record.comment || '';
    typeChanged(); $('cf-editor').showModal();
  }
  function typeChanged() {
    $('cf-proxy-field').hidden = !['A','AAAA','CNAME'].includes($('cf-type').value);
    $('cf-priority-field').hidden = !['MX','URI'].includes($('cf-type').value);
  }
  function editRoute(tunnel, route = {}) {
    routeTunnel = tunnel;
    $('cf-route-form').querySelector('.cf-form-error').textContent = '';
    $('cf-route-name').value = route.hostname || ''; $('cf-route-name').readOnly = Boolean(route.hostname);
    $('cf-route-service').value = route.service || '';
    $('cf-route-editor').showModal();
  }
  function renderTunnels() {
    $('cf-warnings').replaceChildren(...view.warnings.map(w => element('p', w)));
    const tunnels = view.tunnels.map(t => {
      const item = element('div', '', 'cf-item');
      item.append(element('strong', t.name || t.id), element('p', (t.status || 'Ukendt status') + ' · ' + (t.config_src === 'cloudflare' ? 'Styret hos Cloudflare' : 'Lokalt styret')));
      item.append(element('p', t.id + '.cfargotunnel.com'));
      if (t.error) item.append(element('p', t.error));
      const routes = t.routes || [];
      for (const r of routes) {
        const section = element('div', '', 'cf-item'); section.append(element('strong', r.hostname), element('p', r.service + (r.path ? ' · Sti: ' + r.path : '')));
        const dns = view.records.find(d => d.name === r.hostname && d.type === 'CNAME' && d.content.replace(/\.$/, '') === t.id + '.cfargotunnel.com');
        section.append(element('p', dns ? (dns.proxied ? 'DNS og tunnelregel tilknyttet' : 'CNAME findes, men proxy er slået fra') : 'Mangler tilhørende CNAME-post'));
        const actions = element('div', '', 'cf-actions');
        if (!dns) actions.append(button('Opret CNAME-post', () => editRecord({type:'CNAME',name:r.hostname,content:t.id+'.cfargotunnel.com',proxied:true})));
        if (!r.path) actions.append(button('Rediger service', () => editRoute(t,r)), button('Slet tunnelregel', async () => {
          if (!confirm('Slet tunnelreglen for ' + r.hostname + '?\nDNS-posten bevares og kan slettes separat.')) return;
          await api(domainPath() + '/tunnels/' + t.id + '/routes', 'DELETE', {hostname:r.hostname,version:t.version}); await refresh();
        })); section.append(actions); item.append(section);
      }
      const linked = view.records.filter(d => d.type === 'CNAME' && d.content.replace(/\.$/, '') === t.id + '.cfargotunnel.com');
      for (const d of linked.filter(d => !routes.some(r => r.hostname === d.name))) item.append(element('p', d.name + (t.config_src === 'cloudflare' && !t.error ? ' · DNS findes, men tunnelregel mangler' : ' · DNS tilknyttet; kontrollér den lokale tunnelregel')));
      if (t.config_src === 'cloudflare' && !t.error && t.version != null) item.append(button('Tilføj tunneladresse', () => editRoute(t)));
      return item;
    });
    $('cf-tunnels').replaceChildren(...(tunnels.length ? tunnels : [element('p', 'Ingen tilgængelige tunneler.') ]));
  }
  $('cf-enabled').onchange = () => run($('cf-enabled'), async () => {
    const enabled = $('cf-enabled').checked;
    try { renderSettings(await api('settings','POST',{enabled})); await refresh(); status(enabled ? 'Cloudflare-administration aktiveret.' : 'Cloudflare-administration deaktiveret.'); }
    catch(e) { $('cf-enabled').checked = state.enabled; throw e; }
  });
  function resetZoneChoice() {
    $('cf-zone-choice').hidden = true; $('cf-name').replaceChildren();
    $('cf-name').disabled = true; $('cf-name').required = false;
  }
  $('cf-token').oninput = resetZoneChoice;
  $('cf-connect').onsubmit = e => { e.preventDefault(); run(e.submitter, async () => {
    const payload = {token:$('cf-token').value,label:$('cf-token-label').value.trim()};
    if (!$('cf-zone-choice').hidden) payload.name = $('cf-name').value;
    $('cf-token').disabled = true;
    try {
      const result = await api('domains','POST',payload);
      if (result.selection_required) {
        $('cf-name').replaceChildren(...result.choices.map(name => {const option = element('option',name); option.value = name; return option;}));
        $('cf-name').disabled = false; $('cf-name').required = true; $('cf-zone-choice').hidden = false;
        status('Tokenet giver adgang til flere domæner. Vælg det domæne, du vil tilknytte.');
        $('cf-name').focus(); return;
      }
      renderSettings(result);
      const added = state.domains.find(d => d.name === result.connected_domain); if(added) $('cf-domains').value = added.id;
      $('cf-token').value = ''; $('cf-token-label').value = ''; resetZoneChoice(); await refresh();
    } finally { $('cf-token').disabled = false; }
  }); };
  $('cf-refresh').onclick = () => run($('cf-refresh'), refresh);
  $('cf-domains').onchange = () => refresh().catch(e => status(e.message,true));
  $('cf-disconnect').onclick = () => run($('cf-disconnect'), async () => {
    if (!confirm('Fjern domænets tilknytning fra FjordHub?\nDNS-poster og tunneler hos Cloudflare bevares.')) return;
    await api(domainPath(),'DELETE'); renderSettings(await api('settings')); await refresh();
  });
  $('cf-search').oninput = () => { if(view) renderRecords(); };
  $('cf-new').onclick = () => editRecord(); $('cf-type').onchange = typeChanged;
  document.querySelectorAll('[data-close]').forEach(b => b.onclick = () => b.closest('dialog').close());
  async function submitForm(event, action) {
    event.preventDefault(); const b = event.submitter; if(b.disabled) return; b.disabled = true;
    const error = event.target.querySelector('.cf-form-error'); error.textContent = '';
    try { await action(); } catch(e) { error.textContent = e.message; status(e.message, true); } finally { b.disabled = false; }
  }
  $('cf-record-form').onsubmit = e => submitForm(e, async () => {
    const data = {type:$('cf-type').value,name:$('cf-record-name').value,ttl:Number($('cf-ttl').value),priority:Number($('cf-priority').value),proxied:$('cf-proxy').checked,comment:$('cf-comment').value};
    if($('cf-structured').checked) { try { data.data = JSON.parse($('cf-value').value); } catch { throw new Error('Værdien skal være gyldig JSON.'); } }
    else data.content = $('cf-value').value;
    await api(domainPath()+'/records'+(recordId ? '/'+recordId : ''),recordId ? 'PATCH' : 'POST',data);
    $('cf-editor').close(); await refresh();
  });
  $('cf-route-form').onsubmit = e => submitForm(e, async () => {
    await api(domainPath()+'/tunnels/'+routeTunnel.id+'/routes','POST',{hostname:$('cf-route-name').value,service:$('cf-route-service').value,version:routeTunnel.version});
    $('cf-route-editor').close(); await refresh();
  });
  api('settings').then(async r => { renderSettings(r); await refresh(); }).catch(e => status(e.message,true));
})();
