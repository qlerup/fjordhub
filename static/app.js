'use strict';

const STATUS_LABELS = {
  running:       'Kører',
  exited:        'Stoppet',
  paused:        'Sat på pause',
  restarting:    'Genstarter…',
  not_installed: 'Ikke installeret',
  error:         'Fejl',
  unknown:       'Ukendt',
};

const UPDATE_LABELS = {
  update_available: 'Ny opdatering klar',
  up_to_date:       'Ingen opdatering',
  updating:         'Opdaterer...',
  failed:           'Opdatering fejlede',
  error:            'Kunne ikke tjekke',
  not_installed:    '',
};

const INSTALLED_STATES = new Set(['running', 'exited', 'paused', 'restarting', 'error']);

function getAppUrl(port) {
  return `${location.protocol}//${location.hostname}:${port}`;
}

// ── App status polling ────────────────────────────────────────────────────

function applyStatus(card, status) {
  const dot    = card.querySelector('.status-dot');
  const label  = card.querySelector('.status-label');
  const uptime = card.querySelector('.uptime-label');
  const btn    = card.querySelector('.btn-toggle');
  const open   = card.querySelector('.btn-open');
  const port   = parseInt(card.dataset.defaultPort, 10);
  const state  = status.state || 'unknown';
  const openUrl = status.external_url || status.fallback_url || getAppUrl(port);

  dot.dataset.status = state;
  label.textContent  = STATUS_LABELS[state] ?? state;
  label.className    = 'status-label'
    + (state === 'running' ? ' running' : state === 'error' ? ' error' : '');
  uptime.textContent = (state === 'running' && status.uptime) ? status.uptime : '';

  const delBtn  = card.querySelector('.btn-delete');
  const linkBtn = card.querySelector('.btn-link-hub');
  const settingsBtn = card.querySelector('.btn-app-settings');

  if (state === 'running') {
    open.href = openUrl;
    open.style.opacity = '';
    open.style.pointerEvents = '';
    btn.textContent    = 'Stop';
    btn.dataset.action = 'stop';
    btn.disabled       = false;
    if (delBtn) delBtn.style.display = '';
    if (settingsBtn) settingsBtn.style.display = '';
  } else if (state === 'not_installed') {
    const id = card.dataset.appId;
    open.href = '#';
    open.style.opacity = '0.4';
    open.style.pointerEvents = 'none';
    btn.textContent    = 'Installer';
    btn.dataset.action = 'install';
    btn.disabled       = false;
    btn.dataset.wizardUrl = `/apps/${id}/wizard`;
    if (delBtn) delBtn.style.display = 'none';
    if (linkBtn) linkBtn.style.display = 'none';
    if (settingsBtn) settingsBtn.style.display = 'none';
    hideUpdateRow(card);
    return;
  } else {
    open.href = openUrl;
    open.style.opacity = '0.5';
    open.style.pointerEvents = '';
    btn.textContent    = 'Start';
    btn.dataset.action = 'start';
    btn.disabled       = false;
    if (delBtn) delBtn.style.display = '';
    if (settingsBtn) settingsBtn.style.display = '';
  }

  if (linkBtn) {
    linkBtn.style.display = (status.hub_linked === false) ? '' : 'none';
  }
}

async function fetchStatuses() {
  try {
    const res = await fetch('/api/apps-status');
    if (!res.ok) return;
    const data = await res.json();
    document.querySelectorAll('.app-card').forEach(card => {
      const id = card.dataset.appId;
      if (data[id]) applyStatus(card, data[id]);
    });
    organizeAppSections(data);
  } catch (_) {}
}

function organizeAppSections(statuses) {
  const installedGrid = document.getElementById('installed-grid');
  const availableGrid = document.getElementById('available-grid');
  const installedSection = document.getElementById('installed-section');
  const availableSection = document.getElementById('available-section');
  const installedCount = document.getElementById('installed-count');
  const availableCount = document.getElementById('available-count');
  if (!installedGrid || !availableGrid) return;

  let installed = 0;
  let available = 0;
  const cards = Array.from(document.querySelectorAll('.app-card'))
    .sort((a, b) => Number(a.dataset.sortOrder || 0) - Number(b.dataset.sortOrder || 0));

  cards.forEach(card => {
    const state = statuses?.[card.dataset.appId]?.state || 'unknown';
    if (INSTALLED_STATES.has(state)) {
      installedGrid.appendChild(card);
      installed += 1;
    } else {
      availableGrid.appendChild(card);
      available += 1;
    }
  });

  if (installedSection) installedSection.style.display = installed ? '' : 'none';
  if (availableSection) availableSection.style.display = available ? '' : 'none';
  if (installedCount) installedCount.textContent = `${installed}`;
  if (availableCount) availableCount.textContent = `${available}`;
}

function hideUpdateRow(card) {
  const row = card.querySelector('.card-update-row');
  if (!row) return;
  row.style.display = 'none';
}

function applyUpdateStatus(card, status) {
  const row = card.querySelector('.card-update-row');
  if (!row) return;

  const state = status.state || 'error';
  if (state === 'not_installed') {
    hideUpdateRow(card);
    return;
  }

  const label = row.querySelector('.update-label');
  const dot = row.querySelector('.update-dot');
  const btn = row.querySelector('.btn-update');
  row.style.display = '';
  dot.dataset.updateStatus = state;
  label.textContent = status.label || UPDATE_LABELS[state] || state;

  const canUpdate = state === 'update_available';
  const isRunning = state === 'updating' || status.running;
  btn.style.display = canUpdate || isRunning ? '' : 'none';
  btn.disabled = isRunning;
  btn.textContent = isRunning ? 'Opdaterer...' : 'Opdater';
}

async function fetchUpdateStatuses() {
  try {
    const res = await fetch('/api/apps-updates');
    if (!res.ok) return;
    const data = await res.json();
    let hasRunningUpdate = false;
    document.querySelectorAll('.app-card').forEach(card => {
      const id = card.dataset.appId;
      if (data[id]) {
        applyUpdateStatus(card, data[id]);
        hasRunningUpdate ||= Boolean(data[id].running || data[id].state === 'updating');
      }
    });
    if (_terminalAppId && data[_terminalAppId]) {
      const s = data[_terminalAppId];
      if (s.log && s.log.length) renderUpdateLog(s.log);
      if (!s.running && !_terminalDone) finishUpdateModal(s.state);
    }
    if (hasRunningUpdate) setTimeout(fetchUpdateStatuses, 2500);
  } catch (_) {}
}

// ── Update terminal modal ─────────────────────────────────────────────────

let _terminalAppId = null;
let _terminalDone  = false;

const LOG_COLORS = {
  err:  '#f87171',
  warn: '#fbbf24',
  ok:   '#4ade80',
  cmd:  '#93c5fd',
  dim:  '#6b7280',
};

function logLineClass(line) {
  const l = line.toLowerCase();
  if (/error|fejl|failed|✗/.test(l)) return 'err';
  if (/warn/.test(l))                 return 'warn';
  if (/done|færdig|opdateret|success|✓/.test(l)) return 'ok';
  if (line.startsWith('$'))           return 'cmd';
  if (/^#\d+/.test(line.trim()))      return 'dim';
  return '';
}

function renderUpdateLog(lines) {
  const pre = document.getElementById('update-log-output');
  if (!pre) return;
  const atBottom = pre.scrollHeight - pre.scrollTop <= pre.clientHeight + 40;
  pre.innerHTML = '';
  for (const line of lines) {
    const span = document.createElement('span');
    span.textContent = line + '\n';
    const cls = logLineClass(line);
    if (cls) span.style.color = LOG_COLORS[cls];
    pre.appendChild(span);
  }
  if (atBottom) pre.scrollTop = pre.scrollHeight;
}

function openUpdateModal(appId, appName) {
  _terminalAppId = appId;
  _terminalDone  = false;
  const overlay = document.getElementById('update-log-modal');
  const title   = document.getElementById('update-log-title');
  const footer  = document.getElementById('update-log-footer');
  const pre     = document.getElementById('update-log-output');
  const doneBtn = document.getElementById('update-log-done');
  if (!overlay) return;
  if (title)  title.textContent = `Opdaterer ${appName}…`;
  if (footer) { footer.textContent = ''; footer.className = 'terminal-footer'; }
  if (pre)    pre.innerHTML = '';
  if (doneBtn) doneBtn.style.display = 'none';
  overlay.classList.add('is-open');
}

function openUtilityLogModal(titleText, lines = []) {
  _terminalAppId = null;
  _terminalDone = false;
  const overlay = document.getElementById('update-log-modal');
  const title   = document.getElementById('update-log-title');
  const footer  = document.getElementById('update-log-footer');
  const doneBtn = document.getElementById('update-log-done');
  if (!overlay) return;
  if (title) title.textContent = titleText;
  if (footer) { footer.textContent = ''; footer.className = 'terminal-footer'; }
  if (doneBtn) doneBtn.style.display = 'none';
  renderUpdateLog(lines);
  overlay.classList.add('is-open');
}

function finishUtilityLogModal(titleText, ok, lines, footerText) {
  _terminalDone = true;
  const title   = document.getElementById('update-log-title');
  const footer  = document.getElementById('update-log-footer');
  const doneBtn = document.getElementById('update-log-done');
  renderUpdateLog(lines || []);
  if (title) title.textContent = titleText;
  if (footer) {
    footer.textContent = footerText;
    footer.className = 'terminal-footer ' + (ok ? 'ok' : 'err');
  }
  if (doneBtn) doneBtn.style.display = '';
}

function closeUpdateModal() {
  _terminalAppId = null;
  document.getElementById('update-log-modal')?.classList.remove('is-open');
}

function finishUpdateModal(state) {
  _terminalDone = true;
  const footer  = document.getElementById('update-log-footer');
  const title   = document.getElementById('update-log-title');
  const doneBtn = document.getElementById('update-log-done');
  if (!footer) return;
  const ok = state === 'up_to_date' || state === 'updated';
  footer.textContent = ok ? '✓ Opdatering færdig' : '✗ Opdatering fejlede';
  footer.className   = 'terminal-footer ' + (ok ? 'ok' : 'err');
  if (title) title.textContent = title.textContent.replace('Opdaterer', ok ? 'Opdateret' : 'Fejl —');
  if (doneBtn) doneBtn.style.display = '';
}

// ── Docker health indicator ───────────────────────────────────────────────

async function checkDockerHealth() {
  const dot = document.getElementById('hub-docker-status');
  if (!dot) return;
  try {
    const res  = await fetch('/api/health');
    const data = await res.json();
    dot.className = 'topbar-status ' + (data.docker ? 'ok' : 'err');
    dot.title = data.docker ? 'Docker: forbundet' : 'Docker: ikke forbundet';
  } catch (_) {
    dot.className = 'topbar-status err';
    dot.title = 'Kunne ikke nå FjordHub API';
  }
}

// ── Registry refresh ──────────────────────────────────────────────────────

async function refreshRegistry() {
  const btn  = document.getElementById('refresh-btn');
  const icon = document.getElementById('refresh-icon');
  if (btn.disabled) return;

  btn.disabled = true;
  icon.classList.add('spinning');

  try {
    const res  = await fetch('/api/registry/refresh', { method: 'POST' });
    const data = await res.json();

    showToast(data.ok ? `✓ ${data.message}` : `✗ ${data.message}`, data.ok ? 'ok' : 'err');

    if (data.ok) {
      // Reload page to show any newly added apps
      setTimeout(() => location.reload(), 800);
    }
  } catch (_) {
    showToast('✗ Kunne ikke nå serveren', 'err');
  } finally {
    btn.disabled = false;
    icon.classList.remove('spinning');
  }
}

// ── "Last updated" relative time ──────────────────────────────────────────

async function cleanupDocker() {
  const btn = document.getElementById('cleanup-btn');
  const icon = document.getElementById('cleanup-icon');
  const label = document.getElementById('cleanup-label');
  if (!btn || btn.disabled) return;

  const confirmed = confirm(
    'Ryd ubrugte Docker-ting nu?\n\n' +
    'Dette fjerner build-cache, ubrugte images, stoppede containere og ubrugte networks.\n' +
    'Docker volumes og monterede data-mapper bevares.'
  );
  if (!confirmed) return;

  btn.disabled = true;
  if (icon) icon.classList.add('spinning');
  if (label) label.textContent = 'Rydder...';
  openUtilityLogModal('Docker oprydning', [
    'Starter Docker oprydning...',
    'Volumes og monterede data-mapper bevares.',
  ]);

  try {
    const res = await fetch('/api/docker-cleanup', { method: 'POST' });
    let data = {};
    try {
      data = await res.json();
    } catch (_) {
      data = { ok: false, message: 'Serveren svarede ikke med JSON.', log: [] };
    }
    const ok = Boolean(res.ok && data.ok);
    const lines = Array.isArray(data.log) && data.log.length
      ? data.log
      : [data.error || data.message || 'Docker oprydning fejlede.'];
    const message = data.message || (ok ? 'Docker oprydning faerdig.' : 'Docker oprydning fejlede.');
    finishUtilityLogModal(
      ok ? 'Docker oprydning faerdig' : 'Docker oprydning fejlede',
      ok,
      lines,
      message
    );
    showToast(ok ? `OK ${message}` : `Fejl: ${message}`, ok ? 'ok' : 'err');
    setTimeout(fetchStatuses, 1000);
  } catch (_) {
    const message = 'Kunne ikke naa serveren.';
    finishUtilityLogModal('Docker oprydning fejlede', false, [message], message);
    showToast(`Fejl: ${message}`, 'err');
  } finally {
    btn.disabled = false;
    if (icon) icon.classList.remove('spinning');
    if (label) label.textContent = 'Ryd op';
  }
}

function formatAgo(seconds) {
  if (seconds == null) return '';
  if (seconds < 60)   return 'opdateret for <1 min siden';
  if (seconds < 3600) return `opdateret for ${Math.floor(seconds / 60)} min siden`;
  if (seconds < 86400) return `opdateret for ${Math.floor(seconds / 3600)} t siden`;
  return `opdateret for ${Math.floor(seconds / 86400)} d siden`;
}

function tickRelativeTime() {
  const el = document.getElementById('reg-time');
  if (!el) return;
  let s = parseInt(el.dataset.seconds, 10);
  el.textContent = formatAgo(s);
  setInterval(() => { s += 5; el.textContent = formatAgo(s); }, 5000);
}

// ── Toast notification ────────────────────────────────────────────────────

let _toastTimer;
function showToast(msg, type = 'ok') {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.className   = `toast toast-${type} visible`;
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => { el.className = 'toast'; }, 3500);
}

// ── Start/stop via event delegation ──────────────────────────────────────

async function toggleApp(card, action) {
  const id  = card.dataset.appId;
  const btn = card.querySelector('.btn-toggle');
  btn.disabled    = true;
  btn.textContent = action === 'stop' ? 'Stopper…' : 'Starter…';
  try {
    const res  = await fetch(`/apps/${id}/${action}`, { method: 'POST' });
    const data = await res.json();
    if (!data.ok) showToast(`✗ ${data.message}`, 'err');
  } catch (_) {}
  setTimeout(fetchStatuses, 1500);
  setTimeout(fetchStatuses, 4500);
}

async function startUpdate(card) {
  const id = card.dataset.appId;
  const name = card.querySelector('.card-name')?.textContent || id;
  const btn = card.querySelector('.btn-update');
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Starter...';
  }
  try {
    const res = await fetch(`/apps/${id}/update/start`, { method: 'POST' });
    const data = await res.json();
    if (!data.ok && res.status !== 202) {
      showToast(`âœ— ${data.error || 'Kunne ikke starte opdatering'}`, 'err');
      if (btn) btn.disabled = false;
      return;
    }
    openUpdateModal(id, name);
    applyUpdateStatus(card, { ...data, state: 'updating', running: true, label: 'Opdaterer...' });
    setTimeout(fetchUpdateStatuses, 1200);
    setTimeout(fetchStatuses, 4500);
  } catch (_) {
    showToast('âœ— NetvÃ¦rksfejl', 'err');
    if (btn) btn.disabled = false;
  }
}

document.getElementById('app-sections')?.addEventListener('click', e => {
  const updateBtn = e.target.closest('.btn-update');
  if (updateBtn && !updateBtn.disabled) {
    startUpdate(updateBtn.closest('.app-card'));
    return;
  }
  const delBtn = e.target.closest('.btn-delete');
  if (delBtn && !delBtn.disabled) {
    confirmUninstall(delBtn.closest('.app-card'));
    return;
  }
  const settingsBtn = e.target.closest('.btn-app-settings');
  if (settingsBtn && !settingsBtn.disabled) {
    openAppSettings(settingsBtn.closest('.app-card'));
    return;
  }
  const linkBtn = e.target.closest('.btn-link-hub');
  if (linkBtn && !linkBtn.disabled) {
    linkHubIntegration(linkBtn.closest('.app-card'));
    return;
  }
  const btn = e.target.closest('.btn-toggle');
  if (!btn || btn.disabled) return;
  const card   = btn.closest('.app-card');
  const action = btn.dataset.action;
  if (action === 'start' || action === 'stop') toggleApp(card, action);
  if (action === 'install') window.location.href = btn.dataset.wizardUrl;
});

// ── Per-app settings ────────────────────────────────────────────────────────

let _settingsAppId = null;

function closeAppSettings() {
  _settingsAppId = null;
  document.getElementById('app-settings-modal')?.classList.remove('is-open');
}

async function openAppSettings(card) {
  const appId = card?.dataset.appId;
  if (!appId) return;
  _settingsAppId = appId;
  const modal = document.getElementById('app-settings-modal');
  const title = document.getElementById('app-settings-title');
  const input = document.getElementById('app-external-url');
  const status = document.getElementById('app-settings-status');
  const name = card.querySelector('.card-name')?.textContent || appId;
  if (title) title.textContent = `${name} · indstillinger`;
  if (input) input.value = '';
  if (status) { status.textContent = 'Henter indstillinger…'; status.className = 'app-settings-status'; }
  modal?.classList.add('is-open');
  try {
    const res = await fetch(`/api/apps/${encodeURIComponent(appId)}/settings`);
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || 'Kunne ikke hente indstillinger');
    if (input) { input.value = data.external_url || ''; input.focus(); }
    if (status) {
      status.textContent = data.external_url
        ? `Aktiv adresse: ${data.external_url}`
        : (data.fallback_url
            ? `Ingen adresse gemt — appen åbnes via ${data.fallback_url}.`
            : 'Ingen adresse gemt endnu. Indtast domænet som appen skal åbnes på.');
    }
  } catch (error) {
    if (status) { status.textContent = error.message || 'Kunne ikke hente indstillinger'; status.className = 'app-settings-status err'; }
  }
}

document.getElementById('app-settings-form')?.addEventListener('submit', async e => {
  e.preventDefault();
  if (!_settingsAppId) return;
  const input = document.getElementById('app-external-url');
  const status = document.getElementById('app-settings-status');
  const saveBtn = document.getElementById('app-settings-save');
  if (saveBtn) { saveBtn.disabled = true; saveBtn.textContent = 'Gemmer…'; }
  try {
    const res = await fetch(`/api/apps/${encodeURIComponent(_settingsAppId)}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ external_url: input?.value || '' }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || 'Kunne ikke gemme adressen');
    if (input) input.value = data.external_url || '';
    if (status) {
      status.textContent = data.reachable === false
        ? 'Adressen er gemt, men health-check kunne ikke nå den endnu.'
        : data.message;
      status.className = `app-settings-status ${data.reachable === false ? 'warn' : 'ok'}`;
    }
    showToast(`✓ ${data.message}`, 'ok');
    fetchStatuses();
    if (data.reachable !== false) setTimeout(closeAppSettings, 700);
  } catch (error) {
    if (status) { status.textContent = error.message || 'Kunne ikke gemme adressen'; status.className = 'app-settings-status err'; }
  } finally {
    if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = 'Gem adresse'; }
  }
});

document.getElementById('app-settings-close')?.addEventListener('click', closeAppSettings);
document.getElementById('app-settings-cancel')?.addEventListener('click', closeAppSettings);
document.getElementById('app-settings-modal')?.addEventListener('click', e => {
  if (e.target === e.currentTarget) closeAppSettings();
});

// ── Link FjordHub integration ────────────────────────────────────────────────

async function linkHubIntegration(card) {
  const id   = card.dataset.appId;
  const name = card.querySelector('.card-name')?.textContent || id;
  const linkBtn = card.querySelector('.btn-link-hub');
  if (!confirm(`Aktiver FjordHub-integration til ${name}?\n\nDette opdaterer appens konfiguration og genstarter containeren.`)) return;
  if (linkBtn) { linkBtn.disabled = true; linkBtn.textContent = 'Tilslutter…'; }
  try {
    const res  = await fetch(`/api/apps/${encodeURIComponent(id)}/link-hub`, { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      showToast(`✓ ${data.message}`, 'ok');
      if (linkBtn) linkBtn.style.display = 'none';
      setTimeout(fetchStatuses, 4000);
    } else {
      showToast(`✗ ${data.error || 'Tilslutning fejlede'}`, 'err');
      if (linkBtn) { linkBtn.disabled = false; linkBtn.textContent = 'Link FjordHub'; }
    }
  } catch (_) {
    showToast('✗ Netværksfejl', 'err');
    if (linkBtn) { linkBtn.disabled = false; linkBtn.textContent = 'Link FjordHub'; }
  }
}

// ── Uninstall ─────────────────────────────────────────────────────────────

async function confirmUninstall(card) {
  const id   = card.dataset.appId;
  const name = card.querySelector('.card-name')?.textContent || id;
  if (!confirm(`Afinstallér ${name}?\n\nDette stopper og fjerner containere, Docker images og app-filer.\nDine data-mapper berøres ikke.`)) return;

  const delBtn = card.querySelector('.btn-delete');
  const btn    = card.querySelector('.btn-toggle');
  if (delBtn) delBtn.disabled = true;
  if (btn)    btn.disabled    = true;

  try {
    const res  = await fetch(`/apps/${id}/uninstall`, { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      showToast(`✓ ${name} afinstalleret`, 'ok');
      setTimeout(fetchStatuses, 1500);
    } else {
      showToast(`✗ Fejl: ${(data.errors || []).join(', ')}`, 'err');
      if (delBtn) delBtn.disabled = false;
      if (btn)    btn.disabled    = false;
    }
  } catch (_) {
    showToast('✗ Netværksfejl', 'err');
    if (delBtn) delBtn.disabled = false;
    if (btn)    btn.disabled    = false;
  }
}

// ── SSO open ─────────────────────────────────────────────────────────────

document.getElementById('app-sections')?.addEventListener('click', e => {
  const openBtn = e.target.closest('.btn-open');
  if (!openBtn) return;
  const card  = openBtn.closest('.app-card');
  const appId = card?.dataset.appId;
  const href  = openBtn.getAttribute('href');
  if (!href || href === '#' || !appId) return;
  e.preventDefault();
  openWithSso(appId, href);
});

async function openWithSso(appId, appUrl) {
  const popup = window.open('about:blank', '_blank');
  if (popup) popup.opener = null;
  try {
    const res  = await fetch(`/apps/${encodeURIComponent(appId)}/sso-url`);
    const data = await res.json();
    if (data.ok && data.url) {
      if (popup) {
        popup.location.href = data.url;
      } else {
        window.location.href = data.url;
      }
      return;
    }
    if (popup) popup.close();
    if (data.error && data.error.includes('FjordHub-integration')) {
      showToast('✗ SSO kræver FjordHub-integration — klik "Link FjordHub" på app-kortet', 'err');
    } else {
      showToast(`✗ SSO fejlede: ${data.error || 'ukendt fejl'}`, 'err');
    }
  } catch (_) {
    if (popup) popup.close();
    showToast('✗ SSO fejlede: kunne ikke nå FjordHub', 'err');
  }
}

// ── Boot ──────────────────────────────────────────────────────────────────

document.getElementById('update-log-modal')?.addEventListener('click', e => {
  if (e.target === e.currentTarget && _terminalDone) closeUpdateModal();
});

checkDockerHealth();
fetchStatuses();
fetchUpdateStatuses();
tickRelativeTime();

setInterval(fetchStatuses,    8000);
setInterval(fetchUpdateStatuses, 60000);
setInterval(checkDockerHealth, 30000);
