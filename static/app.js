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

  dot.dataset.status = state;
  label.textContent  = STATUS_LABELS[state] ?? state;
  label.className    = 'status-label'
    + (state === 'running' ? ' running' : state === 'error' ? ' error' : '');
  uptime.textContent = (state === 'running' && status.uptime) ? status.uptime : '';

  const delBtn = card.querySelector('.btn-delete');

  if (state === 'running') {
    open.href = getAppUrl(port);
    open.style.opacity = '';
    open.style.pointerEvents = '';
    btn.textContent    = 'Stop';
    btn.dataset.action = 'stop';
    btn.disabled       = false;
    if (delBtn) delBtn.style.display = '';
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
    hideUpdateRow(card);
  } else {
    open.href = getAppUrl(port);
    open.style.opacity = '0.5';
    open.style.pointerEvents = '';
    btn.textContent    = 'Start';
    btn.dataset.action = 'start';
    btn.disabled       = false;
    if (delBtn) delBtn.style.display = '';
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
  if (!overlay) return;
  if (title)  title.textContent = `Opdaterer ${appName}…`;
  if (footer) { footer.textContent = ''; footer.className = 'terminal-footer'; }
  if (pre)    pre.innerHTML = '';
  overlay.classList.add('is-open');
}

function closeUpdateModal() {
  _terminalAppId = null;
  document.getElementById('update-log-modal')?.classList.remove('is-open');
}

function finishUpdateModal(state) {
  _terminalDone = true;
  const footer = document.getElementById('update-log-footer');
  const title  = document.getElementById('update-log-title');
  if (!footer) return;
  const ok = state === 'up_to_date' || state === 'updated';
  footer.textContent = ok ? '✓ Opdatering færdig' : '✗ Opdatering fejlede';
  footer.className   = 'terminal-footer ' + (ok ? 'ok' : 'err');
  if (title) title.textContent = title.textContent.replace('Opdaterer', ok ? 'Opdateret' : 'Fejl —');
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
  const btn = e.target.closest('.btn-toggle');
  if (!btn || btn.disabled) return;
  const card   = btn.closest('.app-card');
  const action = btn.dataset.action;
  if (action === 'start' || action === 'stop') toggleApp(card, action);
  if (action === 'install') window.location.href = btn.dataset.wizardUrl;
});

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

// ── Boot ──────────────────────────────────────────────────────────────────

document.getElementById('update-log-close')?.addEventListener('click', closeUpdateModal);
document.getElementById('update-log-modal')?.addEventListener('click', e => {
  if (e.target === e.currentTarget) closeUpdateModal();
});

checkDockerHealth();
fetchStatuses();
fetchUpdateStatuses();
tickRelativeTime();

setInterval(fetchStatuses,    8000);
setInterval(fetchUpdateStatuses, 60000);
setInterval(checkDockerHealth, 30000);
