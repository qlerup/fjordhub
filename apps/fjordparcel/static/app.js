function setScanProgress(progressBox, update) {
  const stage = progressBox.querySelector("[data-scan-stage]");
  const count = progressBox.querySelector("[data-scan-count]");
  const detail = progressBox.querySelector("[data-scan-detail]");
  const bar = progressBox.querySelector("[data-scan-bar]");

  if (update.stage) {
    stage.textContent = update.stage;
  }

  const scanned = Number(update.scanned || 0);
  const total = update.total === null || update.total === undefined ? null : Number(update.total);
  count.textContent = total ? `${scanned} / ${total} scannet` : `${scanned} scannet`;

  if (total && total > 0) {
    bar.style.width = `${Math.min(100, Math.round((scanned / total) * 100))}%`;
  } else if (update.state === "running") {
    bar.style.width = "18%";
  } else {
    bar.style.width = "0%";
  }

  if (update.state === "complete") {
    progressBox.classList.remove("scan-progress-error");
    progressBox.classList.add("scan-progress-success");
    bar.style.width = "100%";
    detail.textContent = `Fandt ${update.found || 0} trackingnumre. ${update.new_shipments || 0} nye pakker gemt. Opdaterer oversigten...`;
  } else if (update.state === "error") {
    progressBox.classList.remove("scan-progress-success");
    progressBox.classList.add("scan-progress-error");
    detail.textContent = update.error || "Scanningen mislykkedes.";
  } else {
    progressBox.classList.remove("scan-progress-success", "scan-progress-error");
    const accountText = update.account_label ? ` for ${update.account_label}` : "";
    detail.textContent = `FjordParcel scanner den valgte mailkonto${accountText} og checker mønstre for DAO, PostNord, Bring og GLS.`;
  }
}

function toggleShipmentDetails(row) {
  const details = row.parentElement.querySelector("[data-shipment-details]");
  if (!details) {
    return;
  }

  const isExpanded = row.getAttribute("aria-expanded") === "true";
  row.setAttribute("aria-expanded", String(!isExpanded));
  details.hidden = isExpanded;
}

function pollScanStatus(form, progressBox, jobId) {
  const statusTemplate = form.dataset.scanStatusUrlTemplate;
  const statusUrl = statusTemplate.replace("__JOB_ID__", jobId);

  const poll = async () => {
    const response = await fetch(statusUrl, {
      headers: { Accept: "application/json" },
    });
    const payload = await response.json();
    if (!payload.ok) {
      throw new Error(payload.error || "Could not read scan status.");
    }

    const job = payload.job;
    setScanProgress(progressBox, job);

    if (job.state === "complete") {
      window.setTimeout(() => window.location.reload(), 2200);
      return;
    }
    if (job.state === "error") {
      form.querySelector("button[type='submit']").disabled = false;
      return;
    }

    window.setTimeout(poll, 800);
  };

  poll().catch((error) => {
    setScanProgress(progressBox, {
      state: "error",
      stage: "Scan failed",
      error: error.message,
      scanned: 0,
      total: null,
    });
    form.querySelector("button[type='submit']").disabled = false;
  });
}

function bindShipmentInteractions(root = document) {
  root.querySelectorAll("[data-shipment-toggle]").forEach((row) => {
    if (row.dataset.shipmentToggleBound) {
      return;
    }
    row.dataset.shipmentToggleBound = "true";

    row.addEventListener("click", (event) => {
      if (event.target.closest("a, button, input, select, textarea, form, label")) {
        return;
      }
      toggleShipmentDetails(row);
    });

    row.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") {
        return;
      }
      if (event.target.closest("a, button, input, select, textarea, form, label")) {
        return;
      }
      event.preventDefault();
      toggleShipmentDetails(row);
    });
  });

  root.querySelectorAll("[data-rename-toggle]").forEach((button) => {
    if (button.dataset.renameToggleBound) {
      return;
    }
    button.dataset.renameToggleBound = "true";

    button.addEventListener("click", () => {
      const row = button.closest(".shipment-row");
      const form = row.querySelector(".rename-form");
      const input = form.querySelector("input[name='label']");
      form.hidden = !form.hidden;
      button.hidden = !form.hidden;
      if (!form.hidden) {
        input.focus();
        input.select();
      }
    });
  });

  root.querySelectorAll(".rename-form input[name='label']").forEach((input) => {
    if (input.dataset.renameEscapeBound) {
      return;
    }
    input.dataset.renameEscapeBound = "true";

    input.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") {
        return;
      }
      const form = input.closest(".rename-form");
      const row = input.closest(".shipment-row");
      const button = row.querySelector("[data-rename-toggle]");
      form.hidden = true;
      button.hidden = false;
      button.focus();
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  bindShipmentInteractions();

  document.querySelectorAll(".archive-switch").forEach((archiveSwitch) => {
    archiveSwitch.addEventListener("click", async (event) => {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
        return;
      }
      if (archiveSwitch.dataset.busy === "true") {
        event.preventDefault();
        return;
      }

      event.preventDefault();
      const href = archiveSwitch.href;
      const isOn = archiveSwitch.getAttribute("aria-checked") === "true";
      const nextIsOn = !isOn;
      const shouldReduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      const container = document.querySelector("[data-archived-container]");
      const archivedSection = container?.querySelector("[data-archived-section]");
      archiveSwitch.dataset.busy = "true";
      archiveSwitch.classList.toggle("is-on", nextIsOn);
      archiveSwitch.setAttribute("aria-checked", String(nextIsOn));

      const finish = () => {
        const nextUrl = new URL(window.location.href);
        if (nextIsOn) {
          nextUrl.searchParams.delete("archived");
          archiveSwitch.href = nextUrl.toString();
          archiveSwitch.setAttribute("aria-label", "Skjul arkiverede");
        } else {
          nextUrl.searchParams.set("archived", "1");
          archiveSwitch.href = nextUrl.toString();
          archiveSwitch.setAttribute("aria-label", "Vis arkiverede");
        }
        archiveSwitch.dataset.busy = "false";
      };

      if (!container) {
        window.location.href = href;
        return;
      }

      try {
        if (nextIsOn) {
          const response = await fetch(href, { headers: { Accept: "text/html" } });
          const html = await response.text();
          const documentFragment = new DOMParser().parseFromString(html, "text/html");
          const nextSection = documentFragment.querySelector("[data-archived-section]");
          container.classList.remove("is-open", "is-closing");
          container.replaceChildren();
          if (nextSection) {
            container.appendChild(nextSection);
            bindShipmentInteractions(container);
            window.requestAnimationFrame(() => {
              container.classList.add("is-open");
            });
          }
          window.history.pushState({}, "", href);
          finish();
          return;
        }

        if (archivedSection) {
          container.classList.add("is-closing");
          container.classList.remove("is-open");
          await new Promise((resolve) => window.setTimeout(resolve, shouldReduceMotion ? 0 : 420));
          container.replaceChildren();
          container.classList.remove("is-closing");
        }
        window.history.pushState({}, "", href);
        finish();
      } catch (_error) {
        window.location.href = href;
      }
    });
  });

  window.addEventListener("popstate", () => {
    window.location.reload();
  });

  const scanForm = document.querySelector("[data-scan-start-url]");
  if (!scanForm) {
    return;
  }

  scanForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const progressBox = scanForm.querySelector("[data-scan-progress]");
    const submitButton = scanForm.querySelector("button[type='submit']");
    progressBox.hidden = false;
    submitButton.disabled = true;
    setScanProgress(progressBox, {
      state: "running",
      stage: "Starter scanning",
      scanned: 0,
      total: null,
    });

    try {
      const response = await fetch(scanForm.dataset.scanStartUrl, {
        method: "POST",
        body: new FormData(scanForm),
        headers: {
          Accept: "application/json",
          "X-Requested-With": "fetch",
        },
      });
      const payload = await response.json();
      if (!payload.ok) {
        throw new Error(payload.error || "Could not start scan.");
      }
      pollScanStatus(scanForm, progressBox, payload.job_id);
    } catch (error) {
      setScanProgress(progressBox, {
        state: "error",
        stage: "Scan failed",
        error: error.message,
        scanned: 0,
        total: null,
      });
      submitButton.disabled = false;
    }
  });
});

// === In-app opdatering ===
(function () {
  var STATUS_POLL_MS = 2500;
  var BADGE_POLL_MS = 30000;
  var RECONNECT_MAX_MS = 20 * 60 * 1000;
  var RELOAD_DELAY_MS = 1800;
  var RECONNECT_KEY = 'fjordparcel.appUpdate.reconnect.v1';

  var statusPollTimer = null;
  var badgePollTimer = null;
  var choiceResolver = null;
  var reloadTimer = null;
  var appUpdateData = {};
  var reconnectUntil = 0;

  function g(id) { return document.getElementById(id); }

  function escHtml(s) {
    return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function fmtTs(iso) {
    if (!iso) return '';
    try {
      var d = new Date(iso);
      if (isNaN(d)) return iso;
      return d.toLocaleString('da-DK', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch (e) { return iso; }
  }

  function shortRev(v) {
    var s = String(v || '').trim();
    return s ? (s.length > 12 ? s.slice(0, 12) : s) : '-';
  }

  function showStatus(msg, kind) {
    var el = g('appUpdateStatus');
    if (!el) return;
    if (!msg) { el.style.display = 'none'; el.textContent = ''; return; }
    el.textContent = msg;
    el.style.display = 'block';
    el.style.background = kind === 'err' ? 'rgba(200,50,50,.12)' : 'rgba(50,150,80,.12)';
    el.style.color = kind === 'err' ? '#c03030' : '#1a6b35';
    el.style.border = '1px solid ' + (kind === 'err' ? 'rgba(200,50,50,.25)' : 'rgba(50,150,80,.25)');
  }

  function statusLabel(raw) {
    var s = String(raw || '').toLowerCase();
    if (s === 'idle') return 'Klar';
    if (s === 'available') return 'Opdatering klar';
    if (s === 'checking') return 'Tjekker';
    if (s === 'running') return 'Opdaterer';
    if (s === 'stopping') return 'Stopper';
    if (s === 'stopped') return 'Stoppet';
    if (s === 'success') return 'Fuldført';
    if (s === 'failed') return 'Fejlede';
    return raw || 'Klar';
  }

  function logLineLevel(line) {
    var s = String(line || '').toLowerCase();
    if (/\b(traceback|exception|error|failed|fatal)\b/.test(s) || s.includes('returncode=1')) return 'err';
    if (/\b(warn|warning|skipping|springer)\b/.test(s)) return 'warn';
    if (/\b(success|finished|done|healthy|started|built|klar)\b/.test(s)) return 'ok';
    if (/^\s*(=>|-->|->|\[\+\]|cached|\$|==>)/i.test(s)) return 'build';
    return 'info';
  }

  var LOG_COLORS = { err: '#e57373', warn: '#ffb74d', ok: '#81c784', build: '#64b5f6', info: '#ccc' };

  function renderLog(lines) {
    var el = g('appUpdateLog');
    if (!el) return;
    if (!Array.isArray(lines) || !lines.length) { el.style.display = 'none'; el.innerHTML = ''; return; }
    el.style.display = 'block';
    el.innerHTML = lines.map(function (line) {
      var level = logLineLevel(line);
      return '<span style="display:block;color:' + LOG_COLORS[level] + '">' + escHtml(line) + '</span>';
    }).join('');
    try { el.scrollTop = el.scrollHeight; } catch (e) {}
  }

  function markReconnect() {
    reconnectUntil = Date.now() + RECONNECT_MAX_MS;
    try { localStorage.setItem(RECONNECT_KEY, JSON.stringify({ until: reconnectUntil })); } catch (e) {}
  }

  function clearReconnect() {
    reconnectUntil = 0;
    try { localStorage.removeItem(RECONNECT_KEY); } catch (e) {}
  }

  function reconnectActive() {
    var now = Date.now();
    if (!reconnectUntil) {
      try {
        var raw = JSON.parse(localStorage.getItem(RECONNECT_KEY) || '{}') || {};
        reconnectUntil = Number(raw.until || 0);
      } catch (e) { reconnectUntil = 0; }
    }
    if (reconnectUntil > now) return true;
    if (reconnectUntil) clearReconnect();
    return false;
  }

  function scheduleReload() {
    if (reloadTimer) return;
    clearReconnect();
    showStatus('Opdatering fuldført. Genindlæser...', 'ok');
    reloadTimer = setTimeout(function () { try { window.location.reload(); } catch (e) {} }, RELOAD_DELAY_MS);
  }

  function shouldKeepPolling(data) {
    if (data && data.running) return true;
    if (reconnectActive()) return true;
    if (data && data.service_reachable === false) return true;
    var git = (data && data.git && typeof data.git === 'object') ? data.git : null;
    if (git && git.available === false) return true;
    return false;
  }

  function applySettingsUi(item) {
    var toggle = g('appUpdateAutoCheckToggle');
    var input = g('appUpdateIntervalInput');
    var meta = g('appUpdateAutoMeta');
    if (!item) return;
    var enabled = item.auto_check_enabled !== false;
    var interval = Math.max(5, Math.min(1440, Number(item.auto_check_interval_minutes || 30) || 30));
    if (toggle) toggle.checked = enabled;
    if (input && document.activeElement !== input) input.value = String(interval);
    if (input) input.disabled = !enabled;
    if (meta) {
      var next = String(item.next_auto_check_at || '').trim();
      var last = String(item.last_check_at || '').trim();
      if (!enabled) meta.textContent = 'Automatisk tjek er slaet fra.';
      else if (next) meta.textContent = 'Næste tjek: ' + fmtTs(next);
      else if (last) meta.textContent = 'Sidst tjekket: ' + fmtTs(last);
      else meta.textContent = '';
    }
  }

  function render(data) {
    if (!g('appUpdatePanel')) return;
    var prev = appUpdateData || {};
    var prevRunning = !!prev.running || String(prev.status || '').toLowerCase() === 'running';
    appUpdateData = data || {};
    var git = (data && data.git && typeof data.git === 'object') ? data.git : {};
    var running = !!data.running || String((data || {}).status || '').toLowerCase() === 'running';
    var statusRaw = String((data || {}).status || '').toLowerCase();
    var reconnecting = reconnectActive();
    var justFinished = statusRaw === 'success' && prevRunning && !running;
    var shouldReload = statusRaw === 'success' && (reconnecting || justFinished);
    var serviceOk = !data || data.service_reachable !== false;
    var hasGit = !!(git && Object.keys(git).length);
    var available = serviceOk && hasGit && git.available !== false;
    var hasUpdate = available && !!git.update_available;
    var current = shortRev(git.current_short || git.current_rev);
    var remote = shortRev(git.remote_short || git.remote_rev);
    var statusForLabel = (!running && hasUpdate) ? 'available' : ((data || {}).status || (running ? 'running' : 'idle'));

    var branchEl = g('appUpdateBranch'); if (branchEl) branchEl.textContent = String(git.branch || '-');
    var curEl = g('appUpdateCurrent'); if (curEl) curEl.textContent = current;
    var remEl = g('appUpdateRemote'); if (remEl) remEl.textContent = remote;
    var badge = g('appUpdateStateBadge');
    if (badge) { badge.textContent = statusLabel(statusForLabel); }

    applySettingsUi(data);
    renderLog(Array.isArray((data || {}).log) ? data.log : []);

    var checkBtn = g('appUpdateCheckBtn');
    var startBtn = g('appUpdateStartBtn');
    var forceStopBtn = g('appUpdateForceStopBtn');
    if (checkBtn) checkBtn.disabled = running || reconnecting || checkBtn.classList.contains('loading');
    if (startBtn) startBtn.disabled = running || reconnecting || !available || !!git.dirty || !!git.fetch_error || startBtn.classList.contains('loading');
    if (forceStopBtn) {
      forceStopBtn.hidden = !running;
      forceStopBtn.disabled = !running || !serviceOk || forceStopBtn.classList.contains('loading');
    }

    if (hasUpdate && !running) {
      clearReconnect();
      showStatus('Opdatering klar: ' + current + ' → ' + remote, 'ok');
    } else if (statusRaw === 'stopping') {
      showStatus('Stopper opdatering...', 'ok');
    } else if (statusRaw === 'stopped') {
      clearReconnect();
      showStatus('Opdatering blev stoppet.', 'err');
    } else if (statusRaw === 'success') {
      if (shouldReload) scheduleReload();
      else { clearReconnect(); showStatus('Opdatering fuldført.', 'ok'); }
    } else if (statusRaw === 'failed') {
      clearReconnect();
      showStatus('Opdatering fejlede.', 'err');
    } else if (reconnecting && serviceOk && available && !running) {
      scheduleReload();
    } else if (reconnecting) {
      showStatus('Opdatering kører. FjordParcel genstarter...', 'ok');
    } else if ((data || {}).error) {
      showStatus(String(data.error), 'err');
    } else if (!serviceOk || !available) {
      showStatus('Updater-service er ikke tilgaengelig.', 'err');
    } else if (git.fetch_error) {
      showStatus(String(git.fetch_error), 'err');
    } else if (git.dirty) {
      showStatus('Repoet har lokale tracked aendringer.', 'err');
    } else if (running) {
      showStatus('Opdatering kører...', 'ok');
    } else if (git.current_rev && git.remote_rev) {
      showStatus('Allerede nyeste version.', 'ok');
    }
  }

  function stopPolling() {
    if (statusPollTimer) { clearInterval(statusPollTimer); statusPollTimer = null; }
  }

  function startPolling() {
    if (!g('appUpdatePanel')) return;
    stopPolling();
    statusPollTimer = setInterval(function () {
      loadStatus({ silent: true }).then(function (data) {
        if (!shouldKeepPolling(data)) stopPolling();
      }).catch(function () {});
    }, STATUS_POLL_MS);
  }

  function loadStatus(opts) {
    opts = opts || {};
    if (!g('appUpdatePanel')) return Promise.resolve(null);
    return fetch('/api/app-update/status', { cache: 'no-store' })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        render(data || {});
        if (!opts.skipFollowPolling && shouldKeepPolling(data || {})) startPolling();
        return data;
      })
      .catch(function () {
        var reconnecting = reconnectActive();
        var prev = appUpdateData || {};
        var data = { ok: false, service_reachable: false, running: reconnecting,
          status: reconnecting ? 'running' : 'idle',
          git: (prev.git && typeof prev.git === 'object') ? prev.git : {},
          log: Array.isArray(prev.log) ? prev.log : [],
          error: reconnecting ? '' : (opts.silent ? '' : 'Updater-service er ikke tilgaengelig.') };
        render(data);
        if (!opts.skipFollowPolling && reconnecting && !statusPollTimer) startPolling();
        return data;
      });
  }

  function checkUpdate() {
    var btn = g('appUpdateCheckBtn');
    var orig = btn ? btn.textContent : 'Tjek';
    showStatus('Tjekker for opdatering...', 'ok');
    if (btn) { btn.disabled = true; btn.classList.add('loading'); btn.textContent = 'Tjekker...'; }
    fetch('/api/app-update/check', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
      .then(function (res) { return res.json(); })
      .then(function (data) { render(data || {}); })
      .catch(function () { render({ ok: false, service_reachable: false, error: 'Updater-service er ikke tilgaengelig.' }); })
      .finally(function () {
        if (btn) { btn.classList.remove('loading'); btn.textContent = orig; btn.disabled = false; }
        render(appUpdateData);
      });
  }

  function closeChoiceModal(choice) {
    var modal = g('appUpdateChoiceModal');
    if (modal) modal.style.display = 'none';
    if (choiceResolver) { var r = choiceResolver; choiceResolver = null; r(choice); }
  }

  function openChoiceModal() {
    var modal = g('appUpdateChoiceModal');
    if (!modal) return Promise.resolve(true);
    if (choiceResolver) closeChoiceModal(null);
    modal.style.display = 'flex';
    setTimeout(function () {
      var btn = g('appUpdateChoiceCleanupBtn') || g('appUpdateChoiceFastBtn');
      try { if (btn) btn.focus(); } catch (e) {}
    }, 0);
    return new Promise(function (resolve) { choiceResolver = resolve; });
  }

  function startUpdate() {
    openChoiceModal().then(function (cleanup) {
      if (cleanup === null) return;
      markReconnect();
      var btn = g('appUpdateStartBtn');
      var orig = btn ? btn.textContent : 'Opdater nu';
      showStatus('Starter opdatering...', 'ok');
      if (btn) { btn.disabled = true; btn.classList.add('loading'); btn.textContent = 'Starter...'; }
      fetch('/api/app-update/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cleanup: cleanup }),
      })
        .then(function (res) { return res.json().then(function (data) { return { ok: res.ok, data: data }; }); })
        .then(function (r) {
          render(r.data || {});
          if (!r.ok || !r.data || r.data.ok === false) { clearReconnect(); return; }
          startPolling();
        })
        .catch(function () {
          render({ ok: false, service_reachable: false, running: true, status: 'running', error: '' });
          startPolling();
        })
        .finally(function () {
          if (btn) { btn.classList.remove('loading'); btn.textContent = orig; btn.disabled = false; }
          render(appUpdateData);
        });
    });
  }

  function forceStopUpdate() {
    var btn = g('appUpdateForceStopBtn');
    if (!window.confirm('Force stop opdateringen nu?')) return;
    clearReconnect();
    showStatus('Stopper opdatering...', 'ok');
    if (btn) { btn.disabled = true; btn.classList.add('loading'); btn.textContent = 'Stopper...'; }
    fetch('/api/app-update/force-stop', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
      .then(function (res) { return res.json().then(function (data) { return { ok: res.ok, data: data }; }); })
      .then(function (r) {
        render(r.data || {});
        if (!r.ok || !r.data || r.data.ok === false) {
          showStatus((r.data && r.data.error) || 'Opdateringen kunne ikke stoppes.', 'err');
          return;
        }
        startPolling();
      })
      .catch(function () {
        showStatus('Updater-service er ikke tilgaengelig.', 'err');
      })
      .finally(function () {
        if (btn) { btn.classList.remove('loading'); btn.textContent = 'Force stop'; }
        loadStatus({ silent: true }).catch(function () {});
      });
  }

  function saveSettings() {
    var btn = g('appUpdateSettingsSaveBtn');
    var toggle = g('appUpdateAutoCheckToggle');
    var input = g('appUpdateIntervalInput');
    var enabled = !!(toggle && toggle.checked);
    var interval = Number(input ? input.value : 30);
    var orig = btn ? btn.textContent : 'Gem';
    if (btn) { btn.disabled = true; btn.classList.add('loading'); }
    fetch('/api/app-update/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ auto_check_enabled: enabled, auto_check_interval_minutes: Number.isFinite(interval) ? interval : 30 }),
    })
      .then(function (res) { return res.json().then(function (data) { return { ok: res.ok, data: data }; }); })
      .then(function (r) {
        if (!r.ok || !r.data || r.data.ok === false) {
          showStatus((r.data && r.data.error) || 'Indstillinger kunne ikke gemmes.', 'err');
          return;
        }
        var merged = Object.assign({}, appUpdateData, r.data);
        render(merged);
        showStatus('Indstillinger gemt.', 'ok');
      })
      .catch(function () { showStatus('Indstillinger kunne ikke gemmes.', 'err'); })
      .finally(function () {
        if (btn) { btn.disabled = false; btn.classList.remove('loading'); btn.textContent = orig; }
      });
  }

  function startBadgePolling() {
    if (!g('appUpdatePanel') || badgePollTimer) return;
    var tick = function () { loadStatus({ silent: true, skipFollowPolling: true }).catch(function () {}); };
    tick();
    badgePollTimer = setInterval(tick, BADGE_POLL_MS);
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (!g('appUpdatePanel')) return;

    loadStatus({}).then(function (data) {
      if (shouldKeepPolling(data)) startPolling();
    });
    startBadgePolling();

    var checkBtn = g('appUpdateCheckBtn');
    if (checkBtn) checkBtn.addEventListener('click', checkUpdate);

    var startBtn = g('appUpdateStartBtn');
    if (startBtn) startBtn.addEventListener('click', startUpdate);

    var forceStopBtn = g('appUpdateForceStopBtn');
    if (forceStopBtn) forceStopBtn.addEventListener('click', forceStopUpdate);

    var saveBtn = g('appUpdateSettingsSaveBtn');
    if (saveBtn) saveBtn.addEventListener('click', saveSettings);

    var cleanupBtn = g('appUpdateChoiceCleanupBtn');
    if (cleanupBtn) cleanupBtn.addEventListener('click', function () { closeChoiceModal(true); });

    var fastBtn = g('appUpdateChoiceFastBtn');
    if (fastBtn) fastBtn.addEventListener('click', function () { closeChoiceModal(false); });

    var closeBtn = g('appUpdateChoiceClose');
    if (closeBtn) closeBtn.addEventListener('click', function () { closeChoiceModal(null); });

    var backdrop = g('appUpdateChoiceBackdrop');
    if (backdrop) backdrop.addEventListener('click', function () { closeChoiceModal(null); });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && choiceResolver) closeChoiceModal(null);
    });

    var toggle = g('appUpdateAutoCheckToggle');
    if (toggle) {
      toggle.addEventListener('change', function () {
        var input = g('appUpdateIntervalInput');
        if (input) input.disabled = !toggle.checked;
      });
    }
  });

  function positionTabIndicator() {
    var indicator = document.getElementById('tab-indicator');
    if (!indicator) return;
    var bar = document.getElementById('tab-bar');
    var active = bar && bar.querySelector('.settings-switch-item.active');
    if (!active || !bar) return;
    var barRect = bar.getBoundingClientRect();
    var activeRect = active.getBoundingClientRect();
    indicator.style.width = activeRect.width + 'px';
    indicator.style.transform = 'translate(' + (activeRect.left - barRect.left - 6) + 'px, ' + (activeRect.top - barRect.top - 6) + 'px)';
  }

  document.addEventListener('DOMContentLoaded', function () {
    var indicator = document.getElementById('tab-indicator');
    if (!indicator) return;
    indicator.style.transition = 'none';
    requestAnimationFrame(function () {
      positionTabIndicator();
      requestAnimationFrame(function () { indicator.style.transition = ''; });
    });
  });

  window.addEventListener('resize', positionTabIndicator);
}());
