let _nfsPathFields = []; // [{key, label, recommended}, ...]
let _nfsLxcPrivileged = null;
let _nfsVmid = null;
let _nfsCheckGeneration = 0;

function _setNfsStatus(element, text, color) {
  element.textContent = text;
  element.style.color = color;
}

function _escapeHtml(text) {
  return String(text ?? '').replace(/[&<>"']/g, ch => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[ch]));
}

function _normalizeNfsField(field) {
  if (Array.isArray(field)) {
    const key = field[0] || '';
    const label = field[1] || key;
    return {
      key,
      label,
      recommended: key === 'UPLOADS_HOST_DIR' || /upload/i.test(label),
    };
  }
  const key = field?.key || '';
  const label = field?.label || key;
  return {
    key,
    label,
    recommended: field?.recommended === true || key === 'UPLOADS_HOST_DIR' || /upload/i.test(label),
  };
}

function onNfsTypeChange() {
  renderNfsCommands();
}

function openNfsHelper(fields) {
  _nfsPathFields = (fields || []).map(_normalizeNfsField).filter(field => (typeof wizardFieldActive !== 'function' || wizardFieldActive(field.key)));
  clearInterval(_nfsMountPollTimer);
  document.getElementById('nfs-mount-status').style.display = 'none';
  document.getElementById('nfs-done-btn').disabled = true;
  document.getElementById('nfs-fetch-result').style.display = 'none';
  document.getElementById('nfs-export-select').innerHTML = '<option value="">— Tryk Connect først —</option>';
  document.getElementById('nfs-field-selector').style.display = 'none';
  document.getElementById('nfs-field-list').innerHTML = '';
  _nfsSetConnected(false);
  const mountEl = document.getElementById('nfs-mount-root');
  if (mountEl && !mountEl.value) {
    const appSlug = (window.nfsHelperContext?.name || APP_NAME).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    mountEl.value = `/mnt/${appSlug}`;
  }
  renderNfsCommands();
  document.getElementById('nfs-modal').style.display = 'flex';
  const settings = document.getElementById('app-settings-modal');
  if (settings) settings.inert = true;
  document.getElementById('nfs-server-ip').focus();
  _detectLxcType();
}

async function _detectLxcType() {
  const el = document.getElementById('nfs-lxc-hint');
  try {
    const res  = await fetch('/api/lxc-type');
    const data = await res.json();
    const isDockerDesktop = data.runtime === 'docker_desktop' || data.wsl2 === true;
    const proxRadio = document.getElementById('nfs-type-proxmox');
    const proxLabel = document.getElementById('nfs-type-label-proxmox');
    const wslRadio = document.getElementById('nfs-type-wsl2');
    _nfsLxcPrivileged = data.privileged;
    _nfsVmid = data.vmid || null;
    const vmidRow = document.getElementById('nfs-vmid-row');
    const vmidInput = document.getElementById('nfs-vmid');
    if (isDockerDesktop) {
      _nfsLxcPrivileged = null;
      _nfsVmid = null;
      if (wslRadio) wslRadio.checked = true;
      if (proxRadio) proxRadio.disabled = true;
      if (proxLabel) {
        proxLabel.style.opacity = '.55';
        proxLabel.title = 'Automatisk Proxmox/LXC-mount er ikke tilgaengeligt paa Docker Desktop.';
      }
      if (vmidRow) vmidRow.style.display = 'none';
      if (el) el.innerHTML = 'Docker Desktop/WSL2 registreret - koer kommandoerne i <strong>WSL2-terminalen</strong>.';
      renderNfsCommands();
      return;
    }
    if (proxRadio) proxRadio.disabled = false;
    if (proxLabel) {
      proxLabel.style.opacity = '';
      proxLabel.title = '';
    }
    if (data.privileged === false) {
      if (vmidRow) vmidRow.style.display = '';
      if (vmidInput && !vmidInput.value && data.vmid) vmidInput.value = data.vmid;
    } else {
      if (vmidRow) vmidRow.style.display = 'none';
    }
    if (el) {
      if (data.privileged === true) {
        el.innerHTML = '▶ Kør kommandoerne i <strong>fjordhub-terminalen</strong> (privilegeret LXC)';
      } else if (data.privileged === false) {
        el.innerHTML = '▶ Kør kommandoerne på <strong>PVE-hosten</strong> (uprivilegeret LXC)';
      }
    }
    renderNfsCommands();
  } catch(_) {}
}

function closeNfsHelper() {
  _nfsCheckGeneration++;
  clearInterval(_nfsMountPollTimer);
  document.getElementById('nfs-modal').style.display = 'none';
  const settings = document.getElementById('app-settings-modal');
  if (settings) { settings.inert = false; document.getElementById('app-nfs-add')?.focus(); }
}

function _showNfsFieldSelector() {
  if (_nfsPathFields.length === 0) return;
  const list = document.getElementById('nfs-field-list');
  const recommendationEl = document.getElementById('nfs-recommendation');
  const hasRecommended = _nfsPathFields.some(field => field.recommended);
  const recommendedLabels = _nfsPathFields
    .filter(field => field.recommended)
    .map(field => field.label);
  if (recommendationEl) {
    if (recommendedLabels.length) {
      recommendationEl.style.display = '';
      recommendationEl.textContent = `Anbefalet: brug NFS til ${recommendedLabels.join(', ')}. Data og thumbnails anbefales normalt på lokal disk.`;
    } else {
      recommendationEl.style.display = 'none';
      recommendationEl.textContent = '';
    }
  }
  list.innerHTML = _nfsPathFields.map((field) => {
    const checked = hasRecommended ? field.recommended : true;
    const badge = field.recommended
      ? '<span style="font-size:.68rem;font-weight:700;color:#22c55e;border:1px solid rgba(34,197,94,.35);border-radius:999px;padding:2px 7px;white-space:nowrap;">Anbefalet til NAS/NFS</span>'
      : '';
    return `<label style="display:flex;align-items:center;gap:8px;margin-bottom:6px;cursor:pointer;font-size:.88rem;">
      <input type="checkbox" data-field-key="${_escapeHtml(field.key)}" ${checked ? 'checked' : ''}>
      <span style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
        <span>${_escapeHtml(field.label)}</span>
        ${badge}
      </span>
    </label>`;
  }).join('');
  document.getElementById('nfs-field-selector').style.display = '';
}

async function autoMountNfs() {
  const generation = _nfsCheckGeneration;
  const btn      = document.getElementById('nfs-auto-btn');
  const statusEl = document.getElementById('nfs-auto-status');
  const ip       = document.getElementById('nfs-server-ip')?.value.trim() || '';
  const path     = document.getElementById('nfs-export-select')?.value || '';
  const root     = document.getElementById('nfs-mount-root')?.value.trim() || '';
  const subdir   = document.getElementById('nfs-subdir')?.value.trim() || '';
  const options  = document.getElementById('nfs-options')?.value.trim() || 'vers=3,resvport,_netdev,nofail';

  if (!ip || !path || !root) return;
  btn.disabled = true;
  btn.textContent = '⏳ Monterer…';
  statusEl.innerHTML = '';

  try {
    const res  = await fetch('/api/mount-nfs', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({export: `${ip}:${path}`, mount_root: root, subdir, options}),
    });
    const data = await res.json();
    if (generation !== _nfsCheckGeneration) return;
    if (data.ok) {
      _setNfsStatus(statusEl, `✓ Mountet — ${data.path}`, '#22c55e');
      btn.textContent = '✓ Monteret';
      _onMountConfirmed();
    } else {
      _setNfsStatus(statusEl, `✗ ${data.error}`, '#ef4444');
      btn.disabled = false;
      btn.textContent = '⚡ Montér automatisk';
    }
  } catch(e) {
    statusEl.innerHTML = `<span style="color:#ef4444">✗ Netværksfejl</span>`;
    btn.disabled = false;
    btn.textContent = '⚡ Montér automatisk';
  }
}

function _onMountConfirmed() {
  _nfsCheckGeneration++;
  clearInterval(_nfsMountPollTimer);
  const statusEl = document.getElementById('nfs-mount-status');
  const doneBtn  = document.getElementById('nfs-done-btn');
  if (statusEl) statusEl.innerHTML = `<span style="color:#22c55e">✓ NFS mount bekræftet — klar til brug</span>`;
  _showNfsFieldSelector();
  if (doneBtn) { doneBtn.disabled = false; doneBtn.style.opacity = '1'; doneBtn.style.cursor = 'pointer'; }
}

function finishNfsHelper() {
  const root     = document.getElementById('nfs-mount-root')?.value.trim() || '';
  const subdir   = document.getElementById('nfs-subdir')?.value.trim() || '';
  const finalPath = subdir ? `${root.replace(/\/$/, '')}/${subdir}` : root;
  if (finalPath) {
    document.querySelectorAll('#nfs-field-list input[type=checkbox]:checked').forEach(cb => {
      const input = document.getElementById(`f-${cb.dataset.fieldKey}`);
      if (input) {
        input.value = finalPath;
        onFieldChange(cb.dataset.fieldKey, finalPath);
      }
    });
  }
  window.nfsHelperContext?.onComplete?.(finalPath);
  closeNfsHelper();
}

function nfsLxcMountCommands(vmid, root) {
  const quote = value => "'" + String(value).replace(/'/g, "'\"'\"'") + "'";
  return String.raw`bash <<'FJORDHUB_NFS_LXC'
set -euo pipefail
ctid=${quote(vmid)}
target=${quote(root.replace(/\/+$/, ''))}
config=$(pct config "$ctid")
slot=''
for i in $(seq 0 255); do
  line=$(printf '%s\n' "$config" | grep "^mp$i:" || true)
  [ -n "$line" ] || continue
  existing=$(printf '%s\n' "$line" | sed -n 's/.*,mp=\([^,]*\).*/\1/p')
  if [ "$existing" = "$target" ]; then
    source=$(printf '%s\n' "$line" | cut -d ' ' -f 2- | cut -d ',' -f 1)
    if [ "$source" = "$target" ]; then
      slot="mp$i"
      echo "Mount findes allerede paa $slot; eksisterende indstillinger bevares."
      if pct exec "$ctid" -- mountpoint -q "$target"; then
        echo 'Mountet er aktivt i LXC.'
        exit 0
      fi
      break
    fi
    echo "Mappen $target bruges allerede af et andet lager paa mp$i. Vaelg en anden mappesti."
    exit 1
  fi
done
if [ -z "$slot" ]; then
  for i in $(seq 0 255); do
    if ! printf '%s\n' "$config" | grep -q "^mp$i:"; then slot="mp$i"; break; fi
  done
  [ -n "$slot" ] || { echo 'Ingen ledige mountpladser i LXC.'; exit 1; }
  echo "Tilfoejer mount paa $slot"
  pct set "$ctid" "-$slot" "$target,mp=$target"
fi
# Afslut uploads foerst: denne LXC og dens apps lukkes ned og startes igen.
if pct status "$ctid" | grep -q 'status: running'; then
  pct shutdown "$ctid" --timeout 60
fi
pct start "$ctid"
pct exec "$ctid" -- mountpoint -q "$target" || { echo 'Mountet er stadig ikke aktivt i LXC. Kontroller mount og LXC-ID.'; exit 1; }
FJORDHUB_NFS_LXC`.split('\n');
}

function renderNfsCommands() {
  clearInterval(_nfsMountPollTimer);
  _nfsCheckGeneration++;
  if (document.getElementById('nfs-modal')?.style.display === 'none') return;
  document.getElementById('nfs-done-btn').disabled = true;
  document.getElementById('nfs-mount-status').style.display = 'none';
  const ip      = document.getElementById('nfs-server-ip')?.value.trim() || '';
  const path    = document.getElementById('nfs-export-select')?.value || '';
  const exp     = ip && path ? `${ip}:${path}` : '';
  const root    = document.getElementById('nfs-mount-root')?.value.trim() || '';
  const subdir  = document.getElementById('nfs-subdir')?.value.trim() || '';
  const options = document.getElementById('nfs-options')?.value.trim() || 'vers=3,resvport,_netdev,nofail';
  const block   = document.getElementById('nfs-code-block');

  if (!exp || !root) {
    block.innerHTML = '<span style="color:var(--text-muted)">Vælg NFS export og udfyld lokalt mount-punkt…</span>';
    return;
  }

  const setupType = document.querySelector('input[name="nfs-setup-type"]:checked')?.value || 'proxmox';
  const isWSL2 = setupType === 'wsl2';
  const s = isWSL2 ? 'sudo ' : '';

  const finalPath = subdir ? `${root.replace(/\/$/, '')}/${subdir}` : root;
  const c = text => ({comment: true, text});
  const linuxNfsInstallLines = [
    c('# 0. Installer NFS-klient (kun foerste gang)'),
    'if command -v apt-get >/dev/null 2>&1; then apt-get update && apt-get install -y nfs-common; elif command -v apk >/dev/null 2>&1; then apk add --no-cache nfs-utils util-linux; elif command -v dnf >/dev/null 2>&1; then dnf install -y nfs-utils; elif command -v yum >/dev/null 2>&1; then yum install -y nfs-utils; elif command -v zypper >/dev/null 2>&1; then zypper --non-interactive install nfs-client; else echo "Installer nfs-common/nfs-utils manuelt"; fi',
    '',
  ];

  const sections = [];

  if (isWSL2) {
    sections.push({
      location: 'WSL2-terminalen (skriv "wsl" i PowerShell)',
      lines: [
        c('# 0. Installér NFS-klient (kun første gang)'),
        'sudo apt install -y nfs-common',
        '',
        c('# 1. Opret mount-punkt'),
        `sudo mkdir -p ${root}`,
        '',
        c('# 2. Tilføj til /etc/fstab (vedvarende montering)'),
        `echo "${exp} ${root} nfs ${options} 0 0" | sudo tee -a /etc/fstab`,
        '',
        c('# 3. Montér nu'),
        'sudo mount -a',
        ...(subdir ? ['', c('# 4. Opret undermappe'), `sudo mkdir -p ${finalPath}`] : []),
        '',
        c(`# Base-sti til brug i wizard-felterne: ${finalPath}`),
      ],
    });
  } else if (_nfsLxcPrivileged === false) {
    const vmid = document.getElementById('nfs-vmid')?.value.trim() || _nfsVmid || '<VMID>';
    sections.push({
      location: 'PVE-hosten (root@pve)',
      lines: [
        ...linuxNfsInstallLines,
        c('# 1. Opret mount-punkt'),
        `mkdir -p ${root}`,
        '',
        c('# 2. Tilføj til /etc/fstab (vedvarende montering)'),
        `echo "${exp} ${root} nfs ${options} 0 0" | tee -a /etc/fstab`,
        '',
        c('# 3. Montér nu'),
        'mount -a',
        ...(subdir ? ['', c('# 4. Opret undermappe'), `mkdir -p ${finalPath}`] : []),
        '',
        c('# 5. Find ledig mountplads, tilføj bind-mount og genstart LXC'),
        ...nfsLxcMountCommands(vmid, root),
        '',
        c(`# Base-sti til brug i wizard-felterne: ${finalPath}`),
      ],
    });
  } else {
    const loc = _nfsLxcPrivileged === true ? 'fjordhub-terminalen (root@fjordhub)' : 'LXC-terminalen';
    sections.push({
      location: loc,
      lines: [
        ...linuxNfsInstallLines,
        c('# 1. Opret mount-punkt'),
        `mkdir -p ${root}`,
        '',
        c('# 2. Tilføj til /etc/fstab (vedvarende montering)'),
        `echo "${exp} ${root} nfs ${options} 0 0" | tee -a /etc/fstab`,
        '',
        c('# 3. Montér nu'),
        'mount -a',
        ...(subdir ? ['', c('# 4. Opret undermappe'), `mkdir -p ${finalPath}`] : []),
        '',
        c(`# Base-sti til brug i wizard-felterne: ${finalPath}`),
      ],
    });
  }

  if (_nfsLxcPrivileged === true && !isWSL2) {
    block.innerHTML =
      `<div class="nfs-code-section">
        <div class="nfs-section-header">
          <span class="nfs-block-location">📍 fjordhub-terminalen (root@fjordhub)</span>
        </div>
        <div style="padding:12px 0 4px;">
          <button type="button" class="btn btn-open" id="nfs-auto-btn" onclick="autoMountNfs()">⚡ Montér automatisk</button>
          <div id="nfs-auto-status" style="font-size:.8rem;margin-top:8px;"></div>
        </div>
      </div>`;
  } else {
    block.replaceChildren();
    sections.forEach(sec => {
      const section = document.createElement('div');
      section.className = 'nfs-code-section';
      const header = document.createElement('div');
      header.className = 'nfs-section-header';
      const location = document.createElement('span');
      location.className = 'nfs-block-location';
      location.textContent = `📍 ${sec.location}`;
      const copyButton = document.createElement('button');
      copyButton.type = 'button';
      copyButton.className = 'btn-nfs-copy-section';
      copyButton.textContent = 'Kopiér';
      copyButton.addEventListener('click', () => copySectionCommands(copyButton));
      header.append(location, copyButton);
      const code = document.createElement('div');
      code.className = 'nfs-code-block';
      sec.lines.forEach((line, index) => {
        if (index) code.append(document.createTextNode('\n'));
        if (line.comment) {
          const comment = document.createElement('span');
          comment.className = 'nfs-code-comment';
          comment.textContent = line.text;
          code.append(comment);
        } else {
          code.append(document.createTextNode(line));
        }
      });
      section.append(header, code);
      block.append(section);
    });
  }

  startMountPolling(root);
}

let _nfsMountPollTimer = null;

function startMountPolling(mountRoot) {
  const generation = ++_nfsCheckGeneration;
  clearInterval(_nfsMountPollTimer);
  if (!mountRoot) return;
  const statusEl = document.getElementById('nfs-mount-status');
  const doneBtn  = document.getElementById('nfs-done-btn');
  statusEl.style.display = '';
  statusEl.innerHTML = '<span style="color:var(--text-muted)">⏳ Afventer at mount er klar…</span>';
  doneBtn.disabled = true;
  doneBtn.style.opacity = '.35';
  doneBtn.style.cursor = 'not-allowed';
  let checking = false;
  const check = async () => {
    if (checking || generation !== _nfsCheckGeneration) return;
    checking = true;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    try {
      const ip = document.getElementById('nfs-server-ip').value.trim();
      const exportPath = document.getElementById('nfs-export-select').value;
      const res  = await fetch(`/api/verify-nfs-mount?path=${encodeURIComponent(mountRoot)}&export=${encodeURIComponent(`${ip}:${exportPath}`)}`, {signal: controller.signal, cache: 'no-store'});
      if (!res.ok) throw new Error(res.status === 401 ? 'Log ind i FjordHub igen.' : `Mountkontrollen svarede med HTTP ${res.status}.`);
      const data = await res.json();
      if (generation !== _nfsCheckGeneration) return;
      if (data.mounted) {
        clearInterval(_nfsMountPollTimer);
        _onMountConfirmed();
        if (_nfsLxcPrivileged === false) {
          const subdir = document.getElementById('nfs-subdir')?.value.trim() || '';
          if (subdir) {
            const finalPath = `${mountRoot.replace(/\/$/, '')}/${subdir}`;
            fetch('/api/mkdir', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({path: finalPath}),
            });
          }
        }
      } else {
        _setNfsStatus(statusEl, `Mountet er ikke klar: ${data.error || 'Kontrollér kommandoens output og LXC-ID.'} Kontrollerer igen automatisk.`, 'var(--text-muted)');
      }
    } catch(error) {
      if (generation === _nfsCheckGeneration) _setNfsStatus(statusEl, `Mountkontrollen kunne ikke gennemføres: ${error.name === 'AbortError' ? 'Serveren svarede ikke i tide.' : error.message} Kontrollerer igen automatisk.`, 'var(--text-muted)');
    } finally {
      clearTimeout(timeout);
      checking = false;
    }
  };
  check();
  _nfsMountPollTimer = setInterval(check, 5000);
}

function _nfsSetConnected(connected) {
  ['nfs-export-select', 'nfs-mount-root', 'nfs-subdir', 'nfs-options'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.disabled = !connected;
  });
}

async function fetchNfsExports() {
  const ip = document.getElementById('nfs-server-ip')?.value.trim() || '';
  const btn = document.getElementById('nfs-fetch-btn');
  const resultEl = document.getElementById('nfs-fetch-result');
  const sel = document.getElementById('nfs-export-select');
  if (!ip) return;
  btn.textContent = 'Forbinder…';
  btn.disabled = true;
  resultEl.style.display = 'none';
  _nfsSetConnected(false);
  sel.innerHTML = '<option value="">Henter…</option>';
  try {
    const res = await fetch(`/api/list-nfs-exports?host=${encodeURIComponent(ip)}`);
    const data = await res.json();
    resultEl.style.display = '';
    if (data.exports && data.exports.length > 0) {
      sel.replaceChildren(new Option('— Vælg export —', ''));
      data.exports.forEach(exportPath => sel.append(new Option(exportPath, exportPath)));
      _nfsSetConnected(true);
      _setNfsStatus(resultEl, `✓ Forbundet — ${data.exports.length} export(s) fundet`, '#22c55e');
    } else {
      sel.innerHTML = '<option value="">Ingen exports fundet</option>';
      _setNfsStatus(resultEl, `✗ ${data.error || 'Ingen exports på denne server'}`, '#ef4444');
    }
  } catch(e) {
    sel.innerHTML = '<option value="">Fejl ved hentning</option>';
    resultEl.style.display = '';
    _setNfsStatus(resultEl, `✗ Fejl: ${e.message}`, '#ef4444');
  } finally {
    btn.textContent = 'Connect';
    btn.disabled = false;
    renderNfsCommands();
  }
}

function _copyText(text, btn, label) {
  const confirm = () => {
    const orig = btn.textContent;
    btn.textContent = '✓ Kopieret!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = orig; btn.classList.remove('copied'); }, 2000);
  };
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(confirm).catch(() => _copyFallback(text, confirm));
  } else {
    _copyFallback(text, confirm);
  }
}

function copyNfsCommands() {
  const blocks = document.querySelectorAll('#nfs-code-block .nfs-code-block');
  const text = blocks.length
    ? Array.from(blocks).map(b => b.innerText).join('\n\n')
    : document.getElementById('nfs-code-block').innerText;
  _copyText(text, document.getElementById('nfs-copy-btn'));
}

function copySectionCommands(btn) {
  const codeBlock = btn.closest('.nfs-code-section').querySelector('.nfs-code-block');
  _copyText(codeBlock.textContent, btn);
}

function _copyFallback(text, onSuccess) {
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.cssText = 'position:fixed;top:-9999px;left:-9999px;opacity:0';
  document.body.appendChild(ta);
  ta.select();
  try { document.execCommand('copy'); onSuccess(); } catch(_) {}
  document.body.removeChild(ta);
}

document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && document.getElementById('nfs-modal')?.style.display === 'flex') {
    event.stopImmediatePropagation();
    closeNfsHelper();
  }
}, true);
