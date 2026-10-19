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
  const customSelects = [];
  document.querySelectorAll('.cf-page dialog select').forEach(select => {
    const wrapper = element('div', '', 'cf-select');
    select.before(wrapper); wrapper.append(select); select.classList.add('cf-native-select');
    select.tabIndex = -1; select.setAttribute('aria-hidden', 'true');
    const trigger = element('button', '', 'cf-select-trigger'); trigger.type = 'button';
    trigger.id = select.id + '-trigger'; trigger.setAttribute('aria-haspopup', 'listbox'); trigger.setAttribute('aria-expanded', 'false');
    const label = document.querySelector('label[for="' + select.id + '"]');
    if (label) { label.id = select.id + '-label'; label.htmlFor = trigger.id; trigger.setAttribute('aria-labelledby', label.id + ' ' + trigger.id); }
    const list = element('div', '', 'cf-select-options'); list.id = select.id + '-options';
    list.setAttribute('role', 'listbox'); list.setAttribute('popover', 'manual');
    if (label) list.setAttribute('aria-labelledby', label.id);
    trigger.setAttribute('aria-controls', list.id); wrapper.append(trigger, list);
    const close = () => { list.hidePopover(); trigger.setAttribute('aria-expanded', 'false'); };
    const sync = () => {
      trigger.textContent = select.selectedOptions[0]?.textContent || 'Vælg …';
      trigger.disabled = select.matches(':disabled') || !select.options.length;
      if (trigger.disabled) close();
    };
    const choose = option => { select.value = option.value; select.dispatchEvent(new Event('change', {bubbles:true})); sync(); close(); trigger.focus(); };
    const open = (last = false) => {
      if (trigger.disabled) return;
      customSelects.forEach(item => item.close());
      const options = [...select.options].filter(o => !o.disabled && !o.hidden);
      list.replaceChildren(...options.map(option => {
        const item = element('button', option.textContent, 'cf-select-option'); item.type = 'button'; item.tabIndex = -1;
        item.setAttribute('role', 'option'); item.setAttribute('aria-selected', String(option.selected));
        item.onclick = () => choose(option); return item;
      }));
      const box = trigger.getBoundingClientRect();
      const below = innerHeight - box.bottom - 12, above = box.top - 12;
      const upward = below < 160 && above > below;
      list.style.width = box.width + 'px'; list.style.left = box.left + 'px';
      list.style.maxHeight = Math.min(240, upward ? above : below) + 'px';
      list.showPopover();
      list.style.top = (upward ? box.top - list.getBoundingClientRect().height - 5 : box.bottom + 5) + 'px';
      trigger.setAttribute('aria-expanded', 'true');
      const items = [...list.children];
      (items.find(i => i.getAttribute('aria-selected') === 'true') || (last ? items.at(-1) : items[0]))?.focus();
    };
    trigger.onclick = () => list.matches(':popover-open') ? close() : open();
    trigger.onkeydown = event => { if (['ArrowDown','ArrowUp','Home','End'].includes(event.key)) { event.preventDefault(); open(['ArrowUp','End'].includes(event.key)); } };
    let typed = '', typedAt = 0;
    list.onkeydown = event => {
      const items = [...list.children], index = items.indexOf(document.activeElement);
      if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); close(); trigger.focus(); }
      else if (event.key === 'Tab') close();
      else if (['ArrowDown','ArrowUp','Home','End'].includes(event.key)) {
        event.preventDefault();
        const next = event.key === 'Home' ? 0 : event.key === 'End' ? items.length - 1 : (index + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
        items[next]?.focus();
      } else if (event.key.length === 1 && !event.ctrlKey && !event.altKey && !event.metaKey && event.key !== ' ') {
        event.preventDefault(); typed = Date.now() - typedAt > 700 ? event.key : typed + event.key; typedAt = Date.now();
        items.find(i => i.textContent.toLocaleLowerCase().startsWith(typed.toLocaleLowerCase()))?.focus();
      }
    };
    select.addEventListener('change', sync);
    select.addEventListener('focus', () => trigger.focus());
    select.addEventListener('invalid', () => trigger.focus());
    new MutationObserver(sync).observe(select, {childList:true, subtree:true, attributes:true});
    document.addEventListener('pointerdown', event => { if (!wrapper.contains(event.target)) close(); });
    select.closest('dialog').addEventListener('close', close);
    select.closest('dialog').addEventListener('scroll', close);
    window.addEventListener('resize', close);
    customSelects.push({sync, close}); sync();
  });
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
    fillOriginFields('cf-create', {});
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
    customSelects.forEach(item => item.sync());
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
    let address;
    try { address = new URL(route.service); } catch { address = null; }
    $('cf-route-protocol').value = address?.protocol.replace(':','') || 'http';
    $('cf-route-host').value = address?.hostname || '';
    $('cf-route-port').value = address?.port || '';
    $('cf-route-service-path').value = address ? (address.pathname === '/' ? '' : address.pathname) + address.search : '';
    fillOriginFields('cf-route', route.originRequest || {});
    updateRoutePreview(); customSelects.forEach(item => item.sync());
    $('cf-route-editor').showModal();
  }
  function fillOriginFields(prefix, options) {
    $(prefix + '-tls').value = options.noTLSVerify === true ? 'skip' : options.noTLSVerify === false ? 'verify' : 'inherit';
    $(prefix + '-server-name').value = options.originServerName || '';
    $(prefix + '-host-header').value = options.httpHostHeader || '';
  }
  function readOriginFields(prefix) {
    const tls = $(prefix + '-tls').value;
    return {noTLSVerify:tls === 'inherit' ? null : tls === 'skip', originServerName:$(prefix + '-server-name').value.trim() || null, httpHostHeader:$(prefix + '-host-header').value.trim() || null};
  }
  function routeService() {
    let host = $('cf-route-host').value.trim();
    if (host.includes(':') && !host.startsWith('[')) host = '[' + host + ']';
    const port = $('cf-route-port').value, path = $('cf-route-service-path').value.trim();
    return $('cf-route-protocol').value + '://' + host + (port ? ':' + port : '') + (path && !path.startsWith('/') ? '/' : '') + path;
  }
  function updateRoutePreview() { $('cf-route-preview').textContent = 'Lokal service: ' + routeService(); }
  ['cf-route-protocol','cf-route-host','cf-route-port','cf-route-service-path'].forEach(id => { $(id).addEventListener('input',updateRoutePreview); $(id).addEventListener('change',updateRoutePreview); });
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
        if (r.service?.startsWith('https://') && r.originRequest?.noTLSVerify === true) section.append(element('p', 'No TLS Verify · certifikatkontrol er slået fra'));
        const dns = view.records.find(d => d.name === r.hostname && d.type === 'CNAME' && d.content.replace(/\.$/, '') === t.id + '.cfargotunnel.com');
        section.append(element('p', dns ? (dns.proxied ? 'DNS og tunnelregel tilknyttet' : 'CNAME findes, men proxy er slået fra') : 'Mangler tilhørende CNAME-post'));
        const actions = element('div', '', 'cf-actions');
        if (dns) actions.append(button('Rediger DNS-post', () => editRecord(dns)));
        if (!dns) actions.append(button('Ret DNS-tilknytning', () => editRecord({type:'CNAME',name:r.hostname,content:t.id+'.cfargotunnel.com',proxied:true})));
        if (!r.path) actions.append(button('Rediger tunneladresse', () => editRoute(t,r)), button('Slet tunnelregel', async () => {
          if (!confirm('Slet tunnelreglen for ' + r.hostname + '?\nDNS-posten bevares og kan slettes separat.')) return;
          await api(domainPath() + '/tunnels/' + t.id + '/routes', 'DELETE', {hostname:r.hostname,version:t.version}); await refresh();
        })); section.append(actions); item.append(section);
      }
      const linked = view.records.filter(d => d.type === 'CNAME' && d.content.replace(/\.$/, '') === t.id + '.cfargotunnel.com');
      const otherRecords = linked.filter(d => !routes.some(r => r.hostname === d.name));
      if (otherRecords.length) {
        const other = element('section', '', 'cf-tunnel-other-dns');
        other.append(element('h3', 'Øvrige DNS-tilknytninger'), element('p', 'Separate DNS-poster, som peger på tunnelen uden en synlig tunnelregel.'));
        const list = element('ul');
        for (const d of otherRecords) {
          const entry = element('li');
          entry.append(element('strong', d.name), element('span', t.config_src === 'cloudflare' && !t.error ? 'Ingen tunnelregel fundet' : 'Kontrollér tunnelreglen i den lokale opsætning'));
          list.append(entry);
        }
        other.append(list); item.append(other);
      }
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
      await api('domains/'+selectedDomain+'/addresses','POST',{kind:'tunnel',name:$('cf-record-name').value,tunnel_id:tunnel.id,version:tunnel.version,service,originRequest:readOriginFields('cf-create')});
      $('cf-editor').close(); $('cf-domains').value = selectedDomain; await refresh(); return;
    }
    const data = {type:$('cf-type').value,name:$('cf-record-name').value,ttl:Number($('cf-ttl').value),priority:Number($('cf-priority').value),proxied:$('cf-proxy').checked,comment:$('cf-comment').value};
    if($('cf-structured').checked) { try { data.data = JSON.parse($('cf-value').value); } catch { throw new Error('Værdien skal være gyldig JSON.'); } }
    else data.content = $('cf-value').value;
    await api('domains/'+selectedDomain+(recordId ? '/records/'+recordId : '/addresses'),recordId ? 'PATCH' : 'POST',{...data,kind:'dns'});
    $('cf-editor').close(); $('cf-domains').value = selectedDomain; await refresh();
  });
  $('cf-route-form').onsubmit = e => submitForm(e, async () => {
    await api(domainPath()+'/tunnels/'+routeTunnel.id+'/routes','POST',{hostname:$('cf-route-name').value,service:routeService(),version:routeTunnel.version,originRequest:readOriginFields('cf-route')});
    $('cf-route-editor').close(); await refresh();
  });
  api('settings').then(async r => { renderSettings(r); await refresh(); }).catch(e => status(e.message,true));
})();
