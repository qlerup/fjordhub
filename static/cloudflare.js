(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  let state = {domains: [], enabled: false}, view = null, recordId = null, routeTunnel = null, generation = 0;
  let createView = null, createGeneration = 0;
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
    const records = view.records.filter(r => [r.name,r.type,r.content,JSON.stringify(r.data || {})].join(' ').toLowerCase().includes(query))
      .sort((a,b) => a.name.localeCompare(b.name,'da') || a.type.localeCompare(b.type));
    const nodes = records.map(r => {
      const item = element('tr', '', 'cf-dns-row');
      const cell = className => { const td = element('td', '', className); item.append(td); return td; };
      const name = cell('cf-dns-name');
      const web = ['A','AAAA','CNAME','HTTPS'].includes(r.type) && /^[a-z0-9][a-z0-9.-]*[a-z0-9]$/i.test(r.name) && r.name.includes('.') && !r.name.includes('..');
      const title = element(web ? 'a' : 'strong', r.name, 'cf-dns-host');
      if (web) {title.href = 'https://' + r.name; title.target = '_blank'; title.rel = 'noopener noreferrer'; title.setAttribute('aria-label','Åbn ' + r.name);}
      name.append(title);
      if (r.comment) {
        const details = element('details', '', 'cf-dns-comment');
        details.append(element('summary','Kommentar'),element('p',r.comment)); name.append(details);
      }
      cell('cf-dns-type').append(element('span',r.type,'cf-type-badge'));
      const value = cell('cf-dns-content'), content = r.content || JSON.stringify(r.data || {});
      const code = element('code',content,'cf-dns-value'); code.title = content; value.append(code);
      if (r.type === 'CNAME' && r.content?.replace(/\.$/, '').endsWith('.cfargotunnel.com')) value.append(element('span','Cloudflare Tunnel','cf-dns-caption'));
      const proxy = cell('cf-dns-proxy');
      proxy.append(element('span',r.proxied ? 'Proxy aktiv' : 'Kun DNS', 'cf-proxy-badge' + (r.proxied ? ' is-proxied' : '')),
        element('span','TTL ' + (r.ttl === 1 ? 'automatisk' : r.ttl + ' sek.'),'cf-dns-caption'));
      const actions = cell('cf-dns-actions'), edit = button('Rediger', () => editRecord(r)), remove = button('Slet', async () => {
        if (!confirm('Slet DNS-posten ' + r.name + ' (' + r.type + ')?\nEn eventuel tunnelregel bevares.')) return;
        await api(domainPath() + '/records/' + r.id, 'DELETE'); await refresh();
      });
      edit.setAttribute('aria-label','Rediger ' + r.name); remove.setAttribute('aria-label','Slet ' + r.name);
      remove.classList.add('cf-remove'); actions.append(edit,remove); return item;
    });
    if (!nodes.length) {
      const row = element('tr'), cell = element('td','Ingen DNS-poster matcher.','cf-dns-empty'); cell.colSpan = 5; row.append(cell); nodes.push(row);
    }
    $('cf-records').replaceChildren(...nodes);
    $('cf-record-count').textContent = query ? records.length + ' af ' + view.records.length : String(records.length);
  }
  function editRecord(record = {}) {
    recordId = record.id || null;
    ++createGeneration; createView = view;
    $('cf-editor-title').textContent = recordId ? 'Rediger DNS-post' : 'Opret domæne';
    $('cf-address-save').textContent = recordId ? 'Gem DNS-post' : 'Opret domæne';
    $('cf-address-save').disabled = false;
    $('cf-create-options').hidden = Boolean(recordId);
    $('cf-create-kind').value = 'dns';
    $('cf-create-domain').replaceChildren(...state.domains.map(d => {const option = element('option',d.label && d.label !== d.name ? d.label + ' · ' + d.name : d.name); option.value = d.id; return option;}));
    $('cf-create-domain').value = $('cf-domains').value;
    $('cf-create-host').value = ''; $('cf-create-port').value = '8080'; $('cf-create-protocol').value = 'http';
    $('cf-record-form').querySelector('.cf-form-error').textContent = '';
    $('cf-type').value = record.type || 'A'; $('cf-type').disabled = Boolean(recordId);
    $('cf-record-name').value = record.name || '';
    const structured = Boolean(record.data && Object.keys(record.data).length && !['A','AAAA','CNAME','TXT','MX','NS','PTR'].includes(record.type));
    $('cf-structured').checked = structured;
    $('cf-value').value = structured ? JSON.stringify(record.data, null, 2) : (record.content || '');
    $('cf-ttl').value = record.ttl || 1; $('cf-priority').value = record.priority ?? 10;
    $('cf-proxy').checked = record.proxied || false; $('cf-comment').value = record.comment || '';
    createKindChanged(); typeChanged(); $('cf-editor').showModal();
  }
  function createKindChanged() {
    const tunnel = !recordId && $('cf-create-kind').value === 'tunnel';
    $('cf-tunnel-fields').hidden = !tunnel; $('cf-tunnel-fields').disabled = !tunnel;
    $('cf-dns-fields').hidden = tunnel; $('cf-dns-fields').disabled = tunnel;
    updateAddressPreview();
    const tunnels = (createView?.tunnels || []).filter(t => t.config_src === 'cloudflare' && !t.error && t.version != null);
    $('cf-create-tunnel').replaceChildren(...tunnels.map(t => {const option = element('option',t.name || t.id); option.value = t.id; return option;}));
    $('cf-create-tunnel-help').textContent = tunnels.length ? 'Vælg den tunnel, som kan nå den lokale service.' : 'Ingen redigerbare tunneler fundet. Tunnelen skal være styret hos Cloudflare og tokenet skal have Cloudflare Tunnel Edit.';
  }
  function updateAddressPreview() {
    const zone = state.domains.find(d => String(d.id) === $('cf-create-domain').value);
    const hint = $('cf-address-hint');
    hint.replaceChildren();
    if (!zone) return;
    let name = $('cf-record-name').value.trim().replace(/\.+$/, '').toLowerCase();
    if (!name) {
      hint.textContent = 'Skriv fx film eller et fuldt subdomæne under ' + zone.name + '.';
      return;
    }
    if (name === '@') name = zone.name;
    else if (!name.includes('.') && name !== zone.name) name += '.' + zone.name;
    hint.append('Adressen bliver: ', element('strong', name, 'cf-address-preview'));
    if (name !== zone.name && !name.endsWith('.' + zone.name)) hint.append(' · Skal høre til ' + zone.name + '.');
  }
  $('cf-record-name').oninput = updateAddressPreview;
  $('cf-create-kind').onchange = createKindChanged;
  $('cf-create-domain').onchange = async () => {
    const epoch = ++createGeneration; createView = null; createKindChanged();
    $('cf-address-save').disabled = true;
    try {
      const result = await api('domains/' + $('cf-create-domain').value);
      if (epoch !== createGeneration) return;
      createView = result; createKindChanged();
    } catch(e) { if(epoch === createGeneration) $('cf-record-form').querySelector('.cf-form-error').textContent = e.message; }
    finally { if(epoch === createGeneration) $('cf-address-save').disabled = false; }
  };
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
      const item = element('div', '', 'cf-item cf-tunnel-card');
      const heading = element('div','','cf-tunnel-heading');
      const states = {healthy:'Forbundet',inactive:'Inaktiv',down:'Offline',degraded:'Begrænset forbindelse'};
      heading.append(element('strong',t.name || 'Tunnel'),element('span',states[t.status] || t.status || 'Ukendt status','cf-tunnel-state'));
      item.append(heading,element('p',t.config_src === 'cloudflare' ? 'Styret hos Cloudflare' : 'Lokalt styret'));
      const technical = element('details','','cf-dns-comment');
      technical.append(element('summary','Tunnel-id og DNS-mål'),element('p',t.id + '.cfargotunnel.com')); item.append(technical);
      if (t.error) item.append(element('p', t.error));
      const routes = t.routes || [];
      for (const r of routes) {
        const section = element('div', '', 'cf-tunnel-route'); section.append(element('strong', r.hostname), element('p', r.service + (r.path ? ' · Sti: ' + r.path : '')));
        const dns = view.records.find(d => d.name === r.hostname && d.type === 'CNAME' && d.content.replace(/\.$/, '') === t.id + '.cfargotunnel.com');
        section.append(element('p', dns ? (dns.proxied ? 'DNS og tunnelregel tilknyttet' : 'CNAME findes, men proxy er slået fra') : 'Mangler tilhørende CNAME-post'));
        const actions = element('div', '', 'cf-actions');
        if (!dns) actions.append(button('Ret DNS-tilknytning', () => editRecord({type:'CNAME',name:r.hostname,content:t.id+'.cfargotunnel.com',proxied:true})));
        if (!r.path) actions.append(button('Rediger service', () => editRoute(t,r)), button('Slet tunnelregel', async () => {
          if (!confirm('Slet tunnelreglen for ' + r.hostname + '?\nDNS-posten bevares og kan slettes separat.')) return;
          await api(domainPath() + '/tunnels/' + t.id + '/routes', 'DELETE', {hostname:r.hostname,version:t.version}); await refresh();
        })); section.append(actions); item.append(section);
      }
      const linked = view.records.filter(d => d.type === 'CNAME' && d.content.replace(/\.$/, '') === t.id + '.cfargotunnel.com');
      for (const d of linked.filter(d => !routes.some(r => r.hostname === d.name))) item.append(element('p', d.name + (t.config_src === 'cloudflare' && !t.error ? ' · DNS findes, men tunnelregel mangler' : ' · DNS tilknyttet; kontrollér den lokale tunnelregel')));
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
    const selectedDomain = recordId ? $('cf-domains').value : $('cf-create-domain').value;
    if (!recordId && $('cf-create-kind').value === 'tunnel') {
      const tunnel = createView?.tunnels.find(t => t.id === $('cf-create-tunnel').value);
      if (!tunnel) throw new Error('Vælg en tilgængelig tunnel.');
      let host = $('cf-create-host').value.trim();
      if (host.includes(':') && !host.startsWith('[')) host = '[' + host + ']';
      const service = $('cf-create-protocol').value + '://' + host + ':' + $('cf-create-port').value;
      await api('domains/'+selectedDomain+'/addresses','POST',{kind:'tunnel',name:$('cf-record-name').value,tunnel_id:tunnel.id,version:tunnel.version,service});
      $('cf-editor').close(); $('cf-domains').value = selectedDomain; await refresh(); return;
    }
    const data = {type:$('cf-type').value,name:$('cf-record-name').value,ttl:Number($('cf-ttl').value),priority:Number($('cf-priority').value),proxied:$('cf-proxy').checked,comment:$('cf-comment').value};
    if($('cf-structured').checked) { try { data.data = JSON.parse($('cf-value').value); } catch { throw new Error('Værdien skal være gyldig JSON.'); } }
    else data.content = $('cf-value').value;
    await api('domains/'+selectedDomain+(recordId ? '/records/'+recordId : '/addresses'),recordId ? 'PATCH' : 'POST',{...data,kind:'dns'});
    $('cf-editor').close(); $('cf-domains').value = selectedDomain; await refresh();
  });
  $('cf-route-form').onsubmit = e => submitForm(e, async () => {
    await api(domainPath()+'/tunnels/'+routeTunnel.id+'/routes','POST',{hostname:$('cf-route-name').value,service:$('cf-route-service').value,version:routeTunnel.version});
    $('cf-route-editor').close(); await refresh();
  });
  api('settings').then(async r => { renderSettings(r); await refresh(); }).catch(e => status(e.message,true));
})();
