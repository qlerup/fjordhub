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

  if (state === 'running') {
    open.href = getAppUrl(port);
    open.style.opacity = '';
    open.style.pointerEvents = '';
    btn.textContent    = 'Stop';
    btn.dataset.action = 'stop';
    btn.disabled       = false;
  } else if (state === 'not_installed') {
    const id = card.dataset.appId;
    open.href = '#';
    open.style.opacity = '0.4';
    open.style.pointerEvents = 'none';
    btn.textContent    = 'Installer';
    btn.dataset.action = 'install';
    btn.disabled       = false;
    btn.dataset.wizardUrl = `/apps/${id}/wizard`;
  } else {
    open.href = getAppUrl(port);
    open.style.opacity = '0.5';
    open.style.pointerEvents = '';
    btn.textContent    = 'Start';
    btn.dataset.action = 'start';
    btn.disabled       = false;
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
  } catch (_) {}
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

document.getElementById('app-grid')?.addEventListener('click', e => {
  const btn = e.target.closest('.btn-toggle');
  if (!btn || btn.disabled) return;
  const card   = btn.closest('.app-card');
  const action = btn.dataset.action;
  if (action === 'start' || action === 'stop') toggleApp(card, action);
  if (action === 'install') window.location.href = btn.dataset.wizardUrl;
});

// ── Boot ──────────────────────────────────────────────────────────────────

checkDockerHealth();
fetchStatuses();
tickRelativeTime();

setInterval(fetchStatuses,    8000);
setInterval(checkDockerHealth, 30000);
