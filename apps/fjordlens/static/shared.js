const els = {
  title: document.getElementById('shareTitle'),
  meta: document.getElementById('shareMeta'),
  status: document.getElementById('shareStatus'),
  blockedTypes: document.getElementById('shareBlockedTypes'),
  blockedTypesList: document.getElementById('shareBlockedTypesList'),
  shareUploadStatus: document.getElementById('shareUploadStatus'),
  shareUploadLabel: document.getElementById('shareUploadLabel'),
  shareUploadPct: document.getElementById('shareUploadPct'),
  shareUploadBar: document.getElementById('shareUploadBar'),
  authBox: document.getElementById('shareAuthBox'),
  authTitle: document.getElementById('authTitle'),
  authNameWrap: document.getElementById('authNameWrap'),
  authNameLabel: document.getElementById('authNameLabel'),
  authName: document.getElementById('authName'),
  authLabel: document.getElementById('authLabel'),
  authPassword: document.getElementById('authPassword'),
  authBtn: document.getElementById('authBtn'),
  uploadWrap: document.getElementById('uploadWrap'),
  pathBackTop: document.getElementById('sharePathBackTop'),
  uploadLabel: document.getElementById('uploadLabel'),
  fileInput: document.getElementById('shareFileInput'),
  uploadBtn: document.getElementById('uploadBtn'),
  deleteBtn: document.getElementById('deleteBtn'),
  moreBtn: document.getElementById('shareMoreBtn'),
  moreMenu: document.getElementById('shareMoreMenu'),
  moreSelectBtn: document.getElementById('shareMenuSelectBtn'),
  moreSelectAllBtn: document.getElementById('shareMenuSelectAllBtn'),
  moreClearBtn: document.getElementById('shareMenuClearBtn'),
  moreDeleteBtn: document.getElementById('shareMenuDeleteBtn'),
  grid: document.getElementById('shareGrid'),
  viewer: document.getElementById('shareViewer'),
  viewerImg: document.getElementById('shareViewerImg'),
  viewerVideo: document.getElementById('shareViewerVideo'),
  viewerClose: document.getElementById('shareViewerClose'),
  viewerPrev: document.getElementById('shareViewerPrev'),
  viewerNext: document.getElementById('shareViewerNext'),
  viewerTitle: document.getElementById('shareViewerTitle'),
  viewerMenuBtn: document.getElementById('shareViewerMenuBtn'),
  viewerMenu: document.getElementById('shareViewerMenu'),
  viewerOpenOrig: document.getElementById('shareViewerOpenOrig'),
  uploadPrepModal: document.getElementById('shareUploadPrepModal'),
  uploadPrepClose: document.getElementById('shareUploadPrepClose'),
  uploadPrepCancel: document.getElementById('shareUploadPrepCancel'),
  uploadPrepContinue: document.getElementById('shareUploadPrepContinue'),
  uploadWarnModal: document.getElementById('shareUploadWarnModal'),
  uploadWarnClose: document.getElementById('shareUploadWarnClose'),
};

const state = {
  token: String(window.SHARE_TOKEN || ''),
  info: null,
  items: [],
  selected: new Set(),
  selectionPulseId: 0,
  auth: { passwordRequired: false, nameRequired: false },
  selectMode: false,
  currentPath: '', // relative to share root (e.g. "sub/child")
  visible: [],    // items filtered to currentPath
  viewerIndex: -1,
  uploadAllowedExtensions: [],
};

const uploadProgress = {
  active: false,
  totalFiles: 0,
  totalBytes: 0,
  completedFiles: 0,
  completedBytes: 0,
  failedFiles: 0,
  currentFile: '',
  currentBytes: 0,
};

let uploadProgressHideTimer = null;
let lastResizeIsMobile = isMobileShareView();
let pendingShareFilePicker = null;
let shareUploadTransferHeartbeatTimer = null;

async function setShareUploadTransferState(active) {
  try {
    await fetch(`/api/share/${encodeURIComponent(state.token)}/upload/transfer-state`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ active: !!active }),
    });
  } catch {}
}

function startShareUploadTransferHeartbeat() {
  if (shareUploadTransferHeartbeatTimer) {
    window.clearInterval(shareUploadTransferHeartbeatTimer);
    shareUploadTransferHeartbeatTimer = null;
  }
  setShareUploadTransferState(true).catch(() => {});
  shareUploadTransferHeartbeatTimer = window.setInterval(() => {
    if (!uploadProgress.active) {
      stopShareUploadTransferHeartbeat().catch(() => {});
      return;
    }
    setShareUploadTransferState(true).catch(() => {});
  }, 15000);
}

async function stopShareUploadTransferHeartbeat() {
  if (shareUploadTransferHeartbeatTimer) {
    window.clearInterval(shareUploadTransferHeartbeatTimer);
    shareUploadTransferHeartbeatTimer = null;
  }
  await setShareUploadTransferState(false);
}

function clearUploadProgressHideTimer() {
  if (uploadProgressHideTimer) {
    window.clearTimeout(uploadProgressHideTimer);
    uploadProgressHideTimer = null;
  }
}

function setShareUploadStatusVisible(visible, tone = 'ok') {
  if (!els.shareUploadStatus) return;
  els.shareUploadStatus.classList.remove('err');
  if (tone === 'err') els.shareUploadStatus.classList.add('err');
  els.shareUploadStatus.classList.toggle('hidden', !visible);
}

function renderShareUploadStatus() {
  if (!els.shareUploadLabel || !els.shareUploadPct || !els.shareUploadBar) return;

  const totalFiles = Math.max(0, Number(uploadProgress.totalFiles || 0));
  if (totalFiles <= 0) {
    els.shareUploadLabel.textContent = 'Upload: 0/0';
    els.shareUploadPct.textContent = '0%';
    els.shareUploadBar.style.width = '0%';
    return;
  }

  const totalBytes = Math.max(0, Number(uploadProgress.totalBytes || 0));
  const completedFiles = Math.max(0, Number(uploadProgress.completedFiles || 0));
  const completedBytes = Math.max(0, Number(uploadProgress.completedBytes || 0));
  const currentBytes = Math.max(0, Number(uploadProgress.currentBytes || 0));
  const inProgress = !!uploadProgress.active && completedFiles < totalFiles;
  const currentIndex = inProgress ? Math.min(totalFiles, completedFiles + 1) : Math.min(totalFiles, completedFiles);

  let pct = 0;
  if (totalBytes > 0) {
    const combined = Math.max(0, Math.min(totalBytes, completedBytes + currentBytes));
    pct = Math.round((combined / totalBytes) * 100);
  } else {
    pct = Math.round((Math.max(0, Math.min(totalFiles, completedFiles)) / totalFiles) * 100);
  }
  pct = Math.max(0, Math.min(100, pct));

  let label = `${t('upload_run')}: ${currentIndex}/${totalFiles}`;
  if (inProgress && uploadProgress.currentFile) label += ` - ${uploadProgress.currentFile}`;
  if (!inProgress) {
    label = `Upload: ${Math.min(totalFiles, completedFiles)}/${totalFiles}`;
    if (uploadProgress.failedFiles > 0) label += ` (${uploadProgress.failedFiles} fejl)`;
  }

  els.shareUploadLabel.textContent = label;
  els.shareUploadPct.textContent = `${pct}%`;
  els.shareUploadBar.style.width = `${pct}%`;
}

function startShareUploadProgress(files) {
  const list = Array.isArray(files) ? files : [];
  clearUploadProgressHideTimer();
  uploadProgress.active = true;
  uploadProgress.totalFiles = list.length;
  uploadProgress.totalBytes = list.reduce((sum, f) => sum + Math.max(0, Number((f && f.size) || 0)), 0);
  uploadProgress.completedFiles = 0;
  uploadProgress.completedBytes = 0;
  uploadProgress.failedFiles = 0;
  uploadProgress.currentFile = '';
  uploadProgress.currentBytes = 0;
  setShareUploadStatusVisible(list.length > 0, 'ok');
  renderShareUploadStatus();
}

function markShareUploadCurrentFile(file) {
  uploadProgress.currentFile = String((file && file.name) || '');
  uploadProgress.currentBytes = 0;
  renderShareUploadStatus();
}

function updateShareUploadProgress(bytesUploaded, bytesTotal) {
  const uploaded = Math.max(0, Number(bytesUploaded || 0));
  const total = Math.max(0, Number(bytesTotal || 0));
  uploadProgress.currentBytes = (total > 0) ? Math.min(uploaded, total) : uploaded;
  renderShareUploadStatus();
}

function finishShareUploadFile(file, ok) {
  uploadProgress.completedFiles += 1;
  uploadProgress.completedBytes += Math.max(0, Number((file && file.size) || 0));
  uploadProgress.currentBytes = 0;
  uploadProgress.currentFile = '';
  if (!ok) uploadProgress.failedFiles += 1;
  renderShareUploadStatus();
}

function finishShareUploadProgress() {
  uploadProgress.active = false;
  renderShareUploadStatus();
  const hasErrors = uploadProgress.failedFiles > 0;
  setShareUploadStatusVisible(true, hasErrors ? 'err' : 'ok');
  clearUploadProgressHideTimer();
  uploadProgressHideTimer = window.setTimeout(() => {
    setShareUploadStatusVisible(false, 'ok');
  }, 5000);
}

function isMobileShareView() {
  try {
    return window.matchMedia('(max-width: 760px)').matches;
  } catch {
    return false;
  }
}

function openSharedItem(item) {
  const url = item && (item.original_url || item.download_url);
  if (url) window.open(url, '_blank', 'noopener');
}

function t(key) {
  const da = {
    title: 'Delt mappe',
    loading: 'Indl\u00e6ser...',
    auth_required: 'Adgang kr\u00e6ves',
    auth_title: 'Adgang kr\u00e6ves',
    auth_name_label: 'Dit navn',
    auth_name_placeholder: 'Skriv dit navn',
    auth_password_label: 'Indtast adgangskode',
    auth_password_placeholder: 'Adgangskode',
    auth_name_missing: 'Navn er p\u00e5kr\u00e6vet',
    auth_continue: 'Forts\u00e6t',
    upload_pick: 'Upload',
    perms_label: 'Tilladelser',
    perms_view: 'Se',
    perms_view_upload: 'Se og upload',
    perms_view_upload_delete: 'Se, upload og slet',
    upload_run: 'Upload',
    delete_selected: 'Slet valgte',
    no_files: 'Ingen filer valgt',
    upload_done: 'Upload fuldf\u00f8rt',
    upload_failed: 'Upload fejlede',
    postprocess_start_failed: 'Efterbehandling kunne ikke starte',
    blocked_file_types: 'Blokerede filtyper',
    blocked_file_types_none: 'Ingen blokerede filtyper',
    blocked_file_types_status: 'Blokeret filtype: {types}. Kun billeder og videoer uploades.',
    blocked_file_types_selected: 'Valgt og blokeret: {types}',
    blocked_file_types_configured: 'Blokeret fra whitelist: {types}',
    delete_done: 'Sletning fuldf\u00f8rt',
    delete_failed: 'Sletning fejlede',
    password_failed: 'Forkert adgangskode',
    back: 'Tilbage',
    open: '\u00c5bn',
    selected: 'valgt',
  };
  const en = {
    title: 'Shared folder',
    loading: 'Loading...',
    auth_required: 'Access required',
    auth_title: 'Access required',
    auth_name_label: 'Your name',
    auth_name_placeholder: 'Enter your name',
    auth_password_label: 'Enter password',
    auth_password_placeholder: 'Password',
    auth_name_missing: 'Name is required',
    auth_continue: 'Continue',
    upload_pick: 'Upload',
    perms_label: 'Permissions',
    perms_view: 'View',
    perms_view_upload: 'View and upload',
    perms_view_upload_delete: 'View, upload and delete',
    upload_run: 'Upload',
    delete_selected: 'Delete selected',
    no_files: 'No files selected',
    upload_done: 'Upload completed',
    upload_failed: 'Upload failed',
    postprocess_start_failed: 'Post-processing could not start',
    blocked_file_types: 'Blocked file types',
    blocked_file_types_none: 'No blocked file types',
    blocked_file_types_status: 'Blocked file type: {types}. Only photos and videos are uploaded.',
    blocked_file_types_selected: 'Selected and blocked: {types}',
    blocked_file_types_configured: 'Blocked from whitelist: {types}',
    delete_done: 'Delete completed',
    delete_failed: 'Delete failed',
    password_failed: 'Wrong password',
    back: 'Back',
    open: 'Open',
    selected: 'selected',
  };
  const lang = (document.documentElement.lang || 'da').toLowerCase().startsWith('en') ? en : da;
  return lang[key] || key;
}

async function startShareUploadPostprocess() {
  const res = await fetch(`/api/share/${encodeURIComponent(state.token)}/upload/postprocess`, {
    method: 'POST',
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || !data || data.ok === false) {
    throw new Error((data && data.error) || t('postprocess_start_failed'));
  }
  return data;
}

function showStatus(text, type = 'ok') {
  if (!els.status) return;
  els.status.textContent = text;
  els.status.classList.remove('hidden', 'ok', 'err');
  els.status.classList.add(type);
}

function hideStatus() {
  if (!els.status) return;
  els.status.classList.add('hidden');
}

function normalizeUploadFileExtension(value) {
  let raw = String(value || '').trim().toLowerCase();
  if (!raw) return '';
  raw = raw.split('?', 1)[0].split('#', 1)[0].replace(/\\/g, '/').trim();
  if (raw.includes('/')) raw = raw.split('/').pop() || '';
  let ext = raw.startsWith('.') ? raw : '';
  if (!ext) {
    const dot = raw.lastIndexOf('.');
    ext = dot >= 0 ? raw.slice(dot) : `.${raw}`;
  }
  return /^\.[a-z0-9]{1,16}$/.test(ext) ? ext : '';
}

function summarizeFileExtensions(files) {
  const counts = new Map();
  (Array.isArray(files) ? files : []).forEach((file) => {
    const ext = normalizeUploadFileExtension(file && file.name ? file.name : '') || 'uden filtype';
    counts.set(ext, (counts.get(ext) || 0) + 1);
  });
  return Array.from(counts.entries())
    .sort((a, b) => String(a[0]).localeCompare(String(b[0])))
    .map(([ext, count]) => count > 1 ? `${ext} (${count})` : ext)
    .join(', ');
}

function applyShareUploadFileTypes(data = {}) {
  const allowed = Array.isArray(data.upload_allowed_extensions)
    ? data.upload_allowed_extensions.map(normalizeUploadFileExtension).filter(Boolean)
    : [];
  state.uploadAllowedExtensions = Array.from(new Set(allowed)).sort();
  const accept = String(data.upload_accept || state.uploadAllowedExtensions.join(',')).trim();
  if (els.fileInput && accept) els.fileInput.accept = accept;
}

function splitShareFilesByAllowed(files) {
  const allowed = new Set(Array.isArray(state.uploadAllowedExtensions) ? state.uploadAllowedExtensions : []);
  if (!allowed.size) return { allowed: files, blocked: [] };
  const pass = [];
  const blocked = [];
  (Array.isArray(files) ? files : []).forEach((file) => {
    const ext = normalizeUploadFileExtension(file && file.name ? file.name : '');
    if (ext && allowed.has(ext)) pass.push(file);
    else blocked.push(file);
  });
  return { allowed: pass, blocked };
}

function renderShareBlockedTypes(blockedFiles = null) {
  if (!els.blockedTypes || !els.blockedTypesList) return;
  const selectedSummary = Array.isArray(blockedFiles) && blockedFiles.length ? summarizeFileExtensions(blockedFiles) : '';
  const configured = state.info && Array.isArray(state.info.upload_blocked_extensions)
    ? state.info.upload_blocked_extensions.map(normalizeUploadFileExtension).filter(Boolean).sort()
    : [];
  if (selectedSummary) {
    els.blockedTypesList.textContent = t('blocked_file_types_selected').replace('{types}', selectedSummary);
    els.blockedTypes.classList.remove('hidden');
    return;
  }
  if (configured.length) {
    els.blockedTypesList.textContent = t('blocked_file_types_configured').replace('{types}', configured.join(', '));
    els.blockedTypes.classList.remove('hidden');
    return;
  }
  els.blockedTypesList.textContent = t('blocked_file_types_none');
  els.blockedTypes.classList.add('hidden');
}

function canDeleteFromShare() {
  return !!(state.info && state.info.can_delete);
}

function closeShareMoreMenu() {
  if (!els.moreMenu) return;
  els.moreMenu.classList.remove('open');
  try {
    els.moreMenu.style.position = '';
    els.moreMenu.style.left = '';
    els.moreMenu.style.right = '';
    els.moreMenu.style.top = '';
    els.moreMenu.style.maxWidth = '';
  } catch {}
}

function openShareMoreMenu() {
  if (!els.moreMenu || !els.moreBtn) return;
  els.moreMenu.classList.add('open');
  try {
    const r = els.moreBtn.getBoundingClientRect();
    const vw = Math.max(window.innerWidth || 0, document.documentElement.clientWidth || 0);
    const width = 220;
    const pad = 8;
    let left = r.right - width;
    left = Math.max(pad, Math.min(left, vw - width - pad));
    const top = Math.max(pad, r.bottom + 8);
    els.moreMenu.style.position = 'fixed';
    els.moreMenu.style.left = `${left}px`;
    els.moreMenu.style.right = 'auto';
    els.moreMenu.style.top = `${top}px`;
    els.moreMenu.style.maxWidth = `${width}px`;
  } catch {}
}

function toggleShareMoreMenu() {
  if (!els.moreMenu) return;
  if (els.moreMenu.classList.contains('open')) closeShareMoreMenu();
  else openShareMoreMenu();
}

function closeShareViewerMenu() {
  if (els.viewerMenu) els.viewerMenu.classList.add('hidden');
}

function toggleShareViewerMenu() {
  if (!els.viewerMenu) return;
  els.viewerMenu.classList.toggle('hidden');
}

function setSelectMode(enabled, opts = {}) {
  const on = !!enabled && canDeleteFromShare();
  state.selectMode = on;
  if (!on || opts.clearSelection) {
    state.selected = new Set();
    state.selectionPulseId = 0;
  }
  updateDeleteButton();
  if (!opts.skipRender) renderGrid();
}

function syncSelectionToVisible() {
  if (!state.selected || !state.selected.size) return;
  const visibleIds = new Set((state.visible || []).map((it) => Number(it && it.id || 0)).filter((id) => id > 0));
  const next = new Set();
  state.selected.forEach((id) => { if (visibleIds.has(Number(id))) next.add(Number(id)); });
  state.selected = next;
  if (!state.selected.has(Number(state.selectionPulseId || 0))) state.selectionPulseId = 0;
}

function updateDeleteButton() {
  const canDelete = canDeleteFromShare();
  const count = state.selected.size;
  if (els.deleteBtn) {
    const showDelete = canDelete && state.selectMode;
    els.deleteBtn.style.display = showDelete ? '' : 'none';
    els.deleteBtn.disabled = count === 0;
    els.deleteBtn.textContent = count > 0 ? `${t('delete_selected')} (${count})` : t('delete_selected');
  }
  if (els.moreBtn) {
    els.moreBtn.style.display = canDelete ? '' : 'none';
  }
  if (els.moreSelectBtn) {
    els.moreSelectBtn.textContent = state.selectMode ? 'Afslut v\u00e6lg' : 'V\u00e6lg billeder';
  }
  if (els.moreSelectAllBtn) {
    const hasVisible = Array.isArray(state.visible) && state.visible.length > 0;
    els.moreSelectAllBtn.disabled = !(canDelete && state.selectMode && hasVisible);
  }
  if (els.moreClearBtn) {
    els.moreClearBtn.disabled = !(canDelete && state.selectMode && count > 0);
  }
  if (els.moreDeleteBtn) {
    els.moreDeleteBtn.disabled = !(canDelete && state.selectMode && count > 0);
    els.moreDeleteBtn.textContent = count > 0 ? `${t('delete_selected')} (${count})` : t('delete_selected');
  }
  if (els.pathBackTop) {
    const showBack = !!String(state.currentPath || '').trim();
    els.pathBackTop.style.display = showBack ? '' : 'none';
    els.pathBackTop.disabled = !!state.selectMode;
    els.pathBackTop.textContent = t('back');
  }
}

function isProbablyIosDevice() {
  try {
    const ua = String(navigator.userAgent || '');
    const platform = String(navigator.platform || '');
    return /iPad|iPhone|iPod/.test(ua) || (platform === 'MacIntel' && Number(navigator.maxTouchPoints || 0) > 1);
  } catch {
    return false;
  }
}

function shouldShowUploadPrepNotice() {
  return isProbablyIosDevice();
}

function closeUploadPrepModal() {
  pendingShareFilePicker = null;
  if (els.uploadPrepModal) els.uploadPrepModal.classList.add('hidden');
}

function showUploadPrepModal(onContinue) {
  if (!els.uploadPrepModal) {
    if (typeof onContinue === 'function') onContinue();
    return;
  }
  pendingShareFilePicker = (typeof onContinue === 'function') ? onContinue : null;
  els.uploadPrepModal.classList.remove('hidden');
  try { els.uploadPrepContinue && els.uploadPrepContinue.focus({ preventScroll: true }); } catch {}
}

function continueUploadPrepModal() {
  const fn = pendingShareFilePicker;
  pendingShareFilePicker = null;
  if (els.uploadPrepModal) els.uploadPrepModal.classList.add('hidden');
  if (typeof fn === 'function') fn();
}

function openShareFilePicker(skipPrepNotice = false) {
  if (!els.fileInput) return;
  if (!skipPrepNotice && shouldShowUploadPrepNotice()) {
    showUploadPrepModal(() => openShareFilePicker(true));
    return;
  }
  els.fileInput.value = '';
  try {
    if (typeof els.fileInput.showPicker === 'function') {
      els.fileInput.showPicker();
      return;
    }
    els.fileInput.click();
  } catch {
    showStatus('Kunne ikke åbne filvælger.', 'err');
  }
}

function showUploadWarningModal() {
  if (!els.uploadWarnModal) return;
  els.uploadWarnModal.classList.remove('hidden');
}

function closeUploadWarningModal() {
  if (!els.uploadWarnModal) return;
  els.uploadWarnModal.classList.add('hidden');
}

function renderGrid() {
  if (!els.grid) return;
  // Build folder cards and photo cards based on currentPath
  // If multiple folders are shared, treat a virtual root so we only show folders at top-level
  let root = '';
  try {
    const fps = (state.info && Array.isArray(state.info.folder_paths)) ? state.info.folder_paths : [];
    const count = Number((state.info && (state.info.folder_count != null ? state.info.folder_count : fps.length)) || 0);
    root = (count <= 1 && fps.length) ? String(fps[0] || '') : '';
  } catch { root = ''; }
  const norm = (rel) => {
    // Map uploads/originals|converted/<path>/<file> -> <path>
    let p = String(rel || '').replace(/\\/g, '/');
    if (p.startsWith('uploads/originals/')) p = p.slice('uploads/originals/'.length);
    else if (p.startsWith('uploads/converted/')) p = p.slice('uploads/converted/'.length);
    else if (p.startsWith('uploads/')) p = p.slice('uploads/'.length);
    const parts = p.split('/');
    parts.pop();
    return parts.join('/');
  };
  const relFromRoot = (folder) => {
    const f = String(folder || '').replace(/\\/g, '/');
    return f.startsWith(root + '/') ? f.slice((root + '/').length) : (f === root ? '' : f);
  };

  const items = Array.isArray(state.items) ? state.items : [];
  const byFolder = new Map(); // folderKey -> preview urls (max 4)
  const folderCounts = new Map(); // folderKey -> total items count
  const current = String(state.currentPath || '');
  const includeFolder = (f) => { if (!byFolder.has(f)) byFolder.set(f, []); };
  const incCount = (f) => { folderCounts.set(f, (folderCounts.get(f) || 0) + 1); };
  const immediateChild = (folder) => {
    const base = current ? `${root}/${current}` : root;
    const rel = relFromRoot(folder);
    if (!rel.startsWith(current ? current + '/' : '')) return null;
    const rest = current ? rel.slice(current.length + 1) : rel;
    if (!rest) return null;
    const seg = rest.split('/').filter(Boolean)[0] || null;
    return seg ? (current ? `${current}/${seg}` : seg) : null;
  };

  const directItems = [];
  for (const it of items) {
    const folder = norm(it.rel_path || '');
    const rel = relFromRoot(folder);
    if (rel === current) directItems.push(it);
    const child = immediateChild(folder);
    if (child) {
      includeFolder(child);
      incCount(child);
      try {
        const prev = byFolder.get(child);
        const url = String(it.thumb_url || it.view_url || it.original_url || it.download_url || '');
        if (url && prev.length < 4) prev.push(url);
      } catch {}
    }
  }

  // Render
  els.grid.innerHTML = '';
  // Upload tile (always visible when share allows upload)
  try {
    if (state.info && state.info.can_upload && !state.selectMode) {
      const up = document.createElement('article');
      up.className = 'photo-card upload-card';
      up.innerHTML = `<div class="card-thumb"><div class="upload-plus" aria-label="${t('upload_pick')}">+</div></div>`;
      const openPicker = () => {
        if (els.fileInput) {
          try { if (typeof els.fileInput.showPicker === 'function') { els.fileInput.showPicker(); return; } } catch {}
          try { els.fileInput.click(); } catch {}
        }
      };
      up.addEventListener('click', openPicker);
      els.grid.appendChild(up);
    }
  } catch {}

  // Folder cards
  const folderKeys = Array.from(byFolder.keys()).sort((a,b)=>a.localeCompare(b,'da-DK'));
  for (const fk of folderKeys) {
    const card = document.createElement('article');
    card.className = 'photo-card folder-card';
    const prev = byFolder.get(fk) || [];
    const shuffled = (a) => { const b = a.slice(); for (let i=b.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1)); [b[i],b[j]]=[b[j],b[i]];} return b; };
    const uniq = []; const seen = new Set(); for (const u of shuffled(prev)) { if (u && !seen.has(u)) { seen.add(u); uniq.push(u); } }
    const STORE_KEY = 'fl_folder_previews_v1';
    const loadStore = () => { try { return JSON.parse(localStorage.getItem(STORE_KEY) || '{}') || {}; } catch { return {}; } };
    const saveStore = (obj) => { try { localStorage.setItem(STORE_KEY, JSON.stringify(obj)); } catch {} };
    const store = loadStore();
    const stored = Array.isArray(store[fk]) ? store[fk] : null;
    const intersect = (want, avail) => want.filter(u => avail.includes(u));
    const desired = () => (uniq.length === 1 ? 1 : ((uniq.length === 2 || uniq.length === 3) ? 2 : 4));
    let variant = 'v4';
    let useUrls = [];
    const pickFresh = () => {
      if (uniq.length <= 0) return [];
      if (uniq.length === 1) { variant='v1'; return [uniq[0]]; }
      if (uniq.length === 2 || uniq.length === 3) { variant='v2'; return uniq.slice(0,2); }
      variant='v4'; return uniq.slice(0,4);
    };
    if (stored && stored.length) {
      const cand = intersect(stored, uniq);
      if (cand.length >= desired()) {
        useUrls = cand.slice(0, desired());
        variant = (useUrls.length === 1 ? 'v1' : (useUrls.length === 2 ? 'v2' : 'v4'));
      } else {
        useUrls = pickFresh();
        store[fk] = useUrls; saveStore(store);
      }
    } else {
      useUrls = pickFresh();
      store[fk] = useUrls; saveStore(store);
    }
    const thumbs = useUrls.map(u => `<img src="${u}" alt="">`).join("");
    const count = Number(folderCounts.get(fk) || 0);
    const title = (fk.split('/').pop() || fk);
    card.innerHTML = `
      <div class="card-thumb folder-mosaic"><div class="folder-grid ${variant}">${thumbs}</div></div>
      <div class="folder-name-overlay"><span class="folder-name"><span class="scroll">${title}</span></span><span class="folder-count">${count ? `${count} elementer` : ''}</span></div>
    `;
    // Hover marquee for long folder names (same logic as app.js)
    try {
      const nameEl = card.querySelector('.folder-name');
      const inner = nameEl ? nameEl.querySelector('.scroll') : null;
      if (nameEl && inner) {
        nameEl.setAttribute('title', String(title||''));
        const startMarquee = () => {
          try {
            const prev = inner.style.display;
            inner.style.display = 'inline-block';
            const delta = Math.max(0, inner.scrollWidth - nameEl.clientWidth);
            if (delta <= 4) return;
            nameEl.classList.add('marquee');
            let x = 0; let lastTs = 0; const speed = 60;
            const step = (ts) => {
              if (!nameEl.classList.contains('marquee')) return;
              if (!lastTs) { lastTs = ts; }
              const dt = Math.max(0, (ts - lastTs)/1000); lastTs = ts;
              x -= speed * dt; if (-x >= delta) x = 0;
              inner.style.transform = `translateX(${x}px)`;
              nameEl.__raf = window.requestAnimationFrame(step);
            };
            cancelMarquee();
            nameEl.__raf = window.requestAnimationFrame(step);
          } catch {}
        };
        const cancelMarquee = () => {
          try { if (nameEl.__raf) { window.cancelAnimationFrame(nameEl.__raf); nameEl.__raf = null; } } catch {}
          try { inner.style.transform = ''; } catch {}
          try { inner.style.display = ''; } catch {}
          nameEl.classList.remove('marquee');
        };
        const onEnter = () => startMarquee();
        const onLeave = () => cancelMarquee();
        card.addEventListener('mouseenter', onEnter);
        card.addEventListener('mouseleave', onLeave);
        card.addEventListener('mouseover', onEnter, { passive: true });
      }
    } catch {}
    card.addEventListener('click', () => {
      if (state.selectMode) return;
      state.currentPath = fk;
      renderGrid();
    });
    els.grid.appendChild(card);
  }

  // Photo cards
  state.visible = directItems.slice();
  syncSelectionToVisible();
  state.visible.forEach((item, idx) => {
    const photoId = Number(item && item.id ? item.id : 0);
    const isSelected = !!(state.selectMode && photoId > 0 && state.selected.has(photoId));
    const shouldAnimateSelection = !!(isSelected && photoId > 0 && Number(state.selectionPulseId || 0) === photoId);
    const card = document.createElement('article');
    card.className = `photo-card${isSelected ? ' selected' : ''}${shouldAnimateSelection ? ' just-selected' : ''}`;
    if (photoId > 0) card.setAttribute('data-photo-id', String(photoId));
    const thumb = item.thumb_url
      ? `<div class="card-thumb"><img loading="auto" decoding="async" src="${item.thumb_url}" alt=""></div>`
      : '<div class="card-thumb placeholder">No thumbnail</div>';
    const selectBadge = canDeleteFromShare() ? `<span class="photo-select-badge">${isSelected ? '&#10003;' : ''}</span>` : '';
    const uploader = String(item && item.uploaded_by ? item.uploaded_by : '').trim();
    const uploaderTag = uploader ? `<div class="uploader-badge" title="Uploadet af ${uploader}">${uploader}</div>` : '';
    card.innerHTML = `${thumb}${selectBadge}${uploaderTag}`;
    let longPressTimer = null;
    let longPressActivated = false;
    const startLongPress = () => {
      if (!canDeleteFromShare() || state.selectMode || photoId <= 0) return;
      longPressActivated = false;
      longPressTimer = window.setTimeout(() => {
        longPressActivated = true;
        setSelectMode(true, { skipRender: true });
        state.selectionPulseId = photoId;
        state.selected.add(photoId);
        renderGrid();
      }, 550);
    };
    const cancelLongPress = () => {
      if (!longPressTimer) return;
      window.clearTimeout(longPressTimer);
      longPressTimer = null;
    };
    card.addEventListener('mousedown', startLongPress);
    card.addEventListener('touchstart', startLongPress, { passive: true });
    ['mouseup', 'mouseleave', 'touchend', 'touchcancel'].forEach((ev) => card.addEventListener(ev, cancelLongPress));

    card.addEventListener('click', (ev) => {
      if (longPressActivated) {
        longPressActivated = false;
        ev.preventDefault();
        ev.stopPropagation();
        return;
      }
      if (state.selectMode && canDeleteFromShare()) {
        if (photoId > 0) {
          if (state.selected.has(photoId)) {
            state.selected.delete(photoId);
            if (Number(state.selectionPulseId || 0) === photoId) state.selectionPulseId = 0;
          } else {
            state.selected.add(photoId);
            state.selectionPulseId = photoId;
          }
        }
        updateDeleteButton();
        renderGrid();
        ev.preventDefault();
        ev.stopPropagation();
        return;
      }
      openShareViewer(idx);
    });
    els.grid.appendChild(card);
  });
  updateDeleteButton();
  state.selectionPulseId = 0;
}

function navigateShareBackPath() {
  if (state.selectMode) return;
  const current = String(state.currentPath || '').trim();
  if (!current) return;
  const parts = current.split('/').filter(Boolean);
  parts.pop();
  state.currentPath = parts.join('/');
  renderGrid();
}

// --- Simple viewer (popup) ---
function openShareViewer(index) {
  if (!els.viewer || !state.visible.length) return;
  const clamp = (i) => (i + state.visible.length) % state.visible.length;
  state.viewerIndex = clamp(index);
  const it = state.visible[state.viewerIndex];
  const mediaUrl = it && (it.original_url || it.view_url || it.download_url || it.thumb_url) || '';
  const isVideo = !!(it && it.is_video);

  if (els.viewerImg) {
    els.viewerImg.style.display = isVideo ? 'none' : 'block';
    if (!isVideo) els.viewerImg.src = mediaUrl;
    else els.viewerImg.removeAttribute('src');
  }
  if (els.viewerVideo) {
    els.viewerVideo.style.display = isVideo ? 'block' : 'none';
    try { els.viewerVideo.pause(); } catch {}
    if (isVideo) {
      els.viewerVideo.src = mediaUrl;
      try { els.viewerVideo.play().catch(() => {}); } catch {}
    } else {
      els.viewerVideo.removeAttribute('src');
    }
  }
  if (els.viewerTitle) els.viewerTitle.textContent = String(it && it.filename || '');
  if (els.viewerOpenOrig) {
    const dl = (it && (it.download_url || it.original_url || mediaUrl)) || '';
    els.viewerOpenOrig.href = dl;
  }
  closeShareMoreMenu();
  closeShareViewerMenu();
  els.viewer.classList.remove('hidden');
}
function closeShareViewer() {
  if (!els.viewer) return;
  els.viewer.classList.add('hidden');
  closeShareViewerMenu();
  if (els.viewerImg) els.viewerImg.removeAttribute('src');
  if (els.viewerVideo) {
    try { els.viewerVideo.pause(); } catch {}
    els.viewerVideo.removeAttribute('src');
  }
}
function navShareViewer(step) {
  if (!state.visible.length) return;
  openShareViewer(state.viewerIndex + step);
}

if (els.viewerClose) els.viewerClose.addEventListener('click', closeShareViewer);
if (els.viewerPrev) els.viewerPrev.addEventListener('click', () => navShareViewer(-1));
if (els.viewerNext) els.viewerNext.addEventListener('click', () => navShareViewer(1));
if (els.viewerMenuBtn) {
  els.viewerMenuBtn.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    toggleShareViewerMenu();
  });
}
if (els.viewer) {
  els.viewer.addEventListener('click', (e) => {
    const target = e.target;
    if (target === els.viewer) {
      closeShareViewer();
      return;
    }
    if (target && target.closest && (target.closest('#shareViewerMenu') || target.closest('#shareViewerMenuBtn'))) return;
    closeShareViewerMenu();
  });
}
document.addEventListener('keydown', (e) => {
  const viewerOpen = !!(els.viewer && !els.viewer.classList.contains('hidden'));
  if (!viewerOpen) {
    if (e.key === 'Escape') {
      closeShareMoreMenu();
      if (state.selectMode) setSelectMode(false, { clearSelection: true });
    }
    return;
  }
  if (e.key === 'Escape') closeShareViewer();
  if (e.key === 'ArrowLeft') navShareViewer(-1);
  if (e.key === 'ArrowRight') navShareViewer(1);
});

function applyAuthRequirements(data = {}) {
  const passwordRequired = !!data.password_required;
  const nameRequired = !!data.name_required;
  state.auth = { passwordRequired, nameRequired };
  if (els.authBox) els.authBox.classList.remove('hidden');
  if (els.authTitle) els.authTitle.textContent = t('auth_title');
  if (els.authNameLabel) els.authNameLabel.textContent = t('auth_name_label');
  if (els.authName) els.authName.placeholder = t('auth_name_placeholder');
  if (els.authLabel) els.authLabel.textContent = t('auth_password_label');
  if (els.authPassword) els.authPassword.placeholder = t('auth_password_placeholder');
  if (els.authNameWrap) els.authNameWrap.classList.toggle('hidden', !nameRequired);
  if (els.authPassword && els.authPassword.parentElement) {
    els.authPassword.parentElement.classList.toggle('hidden', !passwordRequired);
  }
}

async function loadInfo() {
  const res = await fetch(`/api/share/${encodeURIComponent(state.token)}/info`);
  const data = await res.json().catch(() => ({}));
  if (res.status === 401 && data && (data.password_required || data.name_required)) {
    applyAuthRequirements(data);
    if (els.meta) els.meta.textContent = t('auth_required');
    return false;
  }
  if (!res.ok || !data || !data.ok) {
    showStatus((data && data.error) || 'Share error', 'err');
    return false;
  }
  state.info = data;
  applyShareUploadFileTypes(data);
  renderShareBlockedTypes();
  if (els.authBox) els.authBox.classList.add('hidden');
  if (els.meta) {
    const perms = data.can_delete ? 'view+upload+delete' : (data.can_upload ? 'view+upload' : 'view');
    const permsText = data.can_delete ? t('perms_view_upload_delete') : (data.can_upload ? t('perms_view_upload') : t('perms_view'));
    const folderNames = Array.isArray(data.folder_paths) ? data.folder_paths.map(p => String(p||'').split('/').filter(Boolean).pop() || '').filter(Boolean) : [];
    const baseTitle = (folderNames.length === 1)
      ? folderNames[0]
      : (String(data.share_name || '').trim() || String(data.folder_label || '').replace(/^uploads\//,'').trim());
    els.meta.innerHTML = `<div class="meta-folder">${baseTitle}</div><div class="meta-perms">${t('perms_label')}: ${permsText}</div>`;
  }
  if (els.uploadWrap) els.uploadWrap.style.display = data.can_upload ? '' : 'none';
  if (els.uploadBtn) els.uploadBtn.style.display = data.can_upload ? '' : 'none';
  if (!data.can_delete) {
    state.selectMode = false;
    state.selected = new Set();
    state.selectionPulseId = 0;
  }
  updateDeleteButton();
  return true;
}

async function loadPhotos() {
  const res = await fetch(`/api/share/${encodeURIComponent(state.token)}/photos`);
  const data = await res.json().catch(() => ({}));
  if (res.status === 401 && data && (data.password_required || data.name_required)) {
    applyAuthRequirements(data);
    return;
  }
  if (!res.ok || !data || !data.ok) {
    showStatus((data && data.error) || 'Share error', 'err');
    return;
  }
  state.items = data.items || [];
  if (!state.selectMode) {
    state.selected = new Set();
    state.selectionPulseId = 0;
  }
  renderGrid();
}

async function runAuth() {
  const visitorName = String((els.authName && els.authName.value) || '').trim();
  const password = String((els.authPassword && els.authPassword.value) || '');
  if (state.auth.nameRequired && !visitorName) {
    showStatus(t('auth_name_missing'), 'err');
    return;
  }
  const res = await fetch(`/api/share/${encodeURIComponent(state.token)}/auth`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password, visitor_name: visitorName }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || !data || !data.ok) {
    showStatus((data && data.error) || t('password_failed'), 'err');
    return;
  }
  hideStatus();
  if (els.authPassword) els.authPassword.value = '';
  await boot();
}

async function runUpload(preselectedFiles = null) {
  const files = Array.isArray(preselectedFiles)
    ? preselectedFiles
    : ((els.fileInput && els.fileInput.files) ? Array.from(els.fileInput.files) : []);
  if (!files.length) { showStatus(t('no_files'), 'err'); return; }
  // Ensure we are authorized just before starting (handles expired session)
  try {
    const res = await fetch(`/api/share/${encodeURIComponent(state.token)}/info`, { cache: 'no-store' });
    const data = await res.json().catch(() => ({}));
    if (res.status === 401) {
      applyAuthRequirements(data || {});
      showStatus(t('auth_required'), 'err');
      return; // Wait for user to authorize
    }
    if (!res.ok || !data || !data.ok || !data.can_upload) {
      showStatus((data && data.error) || 'Upload ikke tilladt', 'err');
      return;
    }
    state.info = data;
    applyShareUploadFileTypes(data);
    renderShareBlockedTypes();
  } catch {}
  const split = splitShareFilesByAllowed(files);
  if (split.blocked.length) {
    const summary = summarizeFileExtensions(split.blocked);
    renderShareBlockedTypes(split.blocked);
    showStatus(t('blocked_file_types_status').replace('{types}', summary), 'err');
  }
  const uploadFiles = split.allowed;
  if (!uploadFiles.length) {
    if (els.fileInput) els.fileInput.value = '';
    return;
  }

  function hasTusClient(){ return !!(window.tus && typeof window.tus.Upload === 'function'); }
  async function uploadTus(file){
    return new Promise((resolve)=>{
      if (!hasTusClient()) { resolve({ ok:false, error:'TUS client unavailable' }); return; }
      const meta = {
        filename: String(file && file.name || 'file'),
        lastModified: String(Number(file && file.lastModified ? file.lastModified : 0)),
      };
      const upload = new window.tus.Upload(file, {
        endpoint: `/api/share/${encodeURIComponent(state.token)}/upload/tus`,
        metadata: meta,
        uploadDataDuringCreation: false,
        withCredentials: true,
        overridePatchMethod: true,
        chunkSize: 2 * 1024 * 1024,
        parallelUploads: 1,
        retryDelays: [0, 1000, 2500, 5000],
        removeFingerprintOnSuccess: true,
        onProgress(bytesUploaded, bytesTotal){
          const pct = bytesTotal > 0 ? Math.round((bytesUploaded/bytesTotal)*100) : 0;
          updateShareUploadProgress(bytesUploaded, bytesTotal);
          showStatus(`${t('upload_run')}: ${file.name} - ${pct}%`, 'ok');
        },
        onError(err){
          try {
            const resp = err && err.originalResponse;
            const status = resp && typeof resp.getStatus === 'function' ? Number(resp.getStatus()) : 0;
            if (status === 401) {
              showStatus(t('auth_required'), 'err');
              // Refresh share info to reveal auth box (password/name)
              loadInfo();
            }
          } catch {}
          resolve({ ok:false, error: (err && err.message) || 'Upload failed' });
        },
        onSuccess(){ resolve({ ok:true }); },
      });
      upload.findPreviousUploads().then((prev)=>{ if (Array.isArray(prev) && prev.length) upload.resumeFromPreviousUpload(prev[0]); upload.start(); }).catch(()=> upload.start());
    });
  }

  let saved=0, failed=0;
  if (!hasTusClient()) { showStatus('TUS klient mangler. Genindl\u00e6s siden.', 'err'); return; }
  showUploadWarningModal();
  startShareUploadProgress(uploadFiles);
  startShareUploadTransferHeartbeat();
  await setShareUploadTransferState(true);
  try {
    for (const f of uploadFiles){
      markShareUploadCurrentFile(f);
      const r = await uploadTus(f);
      const ok = !!(r && r.ok);
      finishShareUploadFile(f, ok);
      if (ok) saved+=1; else failed+=1;
    }
  } finally {
    await stopShareUploadTransferHeartbeat();
    finishShareUploadProgress();
    closeUploadWarningModal();
    if (els.fileInput) els.fileInput.value = '';
  }
  let postprocessError = '';
  if (saved > 0) {
    try {
      await startShareUploadPostprocess();
    } catch (err) {
      postprocessError = err && err.message ? String(err.message) : t('postprocess_start_failed');
    }
  }
  if (postprocessError) {
    showStatus(`${t('upload_done')} - ${t('postprocess_start_failed')}: ${postprocessError}`, 'err');
  } else if (failed>0){ showStatus(`${t('upload_done')} - ${saved} ok - ${failed} fejl`, 'err'); }
  else { showStatus(t('upload_done'), 'ok'); }
  await loadPhotos();
}

async function runDelete() {
  if (!canDeleteFromShare()) {
    showStatus('Sletning ikke tilladt', 'err');
    return;
  }
  const ids = Array.from(state.selected || []);
  if (!ids.length) {
    showStatus('Ingen billeder valgt', 'err');
    return;
  }
  if (!window.confirm(`Slet ${ids.length} billede(r)?`)) return;
  const res = await fetch(`/api/share/${encodeURIComponent(state.token)}/delete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ photo_ids: ids }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || !data || !data.ok) {
    showStatus((data && data.error) || t('delete_failed'), 'err');
    return;
  }
  showStatus(t('delete_done'), 'ok');
  state.selected = new Set();
  state.selectionPulseId = 0;
  if (state.selectMode) setSelectMode(false, { skipRender: true, clearSelection: true });
  await loadPhotos();
}

async function boot() {
  hideStatus();
  state.selectMode = false;
  state.selected = new Set();
  state.selectionPulseId = 0;
  closeShareMoreMenu();
  closeShareViewerMenu();
  closeUploadWarningModal();
  clearUploadProgressHideTimer();
  setShareUploadStatusVisible(false, 'ok');
  renderShareUploadStatus();
  if (els.title) els.title.textContent = t('title');
  if (els.meta) els.meta.textContent = t('loading');
  if (els.authTitle) els.authTitle.textContent = t('auth_title');
  if (els.authNameLabel) els.authNameLabel.textContent = t('auth_name_label');
  if (els.authName) els.authName.placeholder = t('auth_name_placeholder');
  if (els.authLabel) els.authLabel.textContent = t('auth_password_label');
  if (els.authPassword) els.authPassword.placeholder = t('auth_password_placeholder');
  if (els.authBtn) els.authBtn.textContent = t('auth_continue');
  if (els.uploadLabel) els.uploadLabel.textContent = t('upload_pick');
  // No separate upload button; auto-start on file pick
  if (els.deleteBtn) els.deleteBtn.textContent = t('delete_selected');
  if (els.moreSelectBtn) els.moreSelectBtn.textContent = 'V\u00e6lg billeder';
  if (els.moreSelectAllBtn) els.moreSelectAllBtn.textContent = 'V\u00e6lg alle';
  if (els.moreClearBtn) els.moreClearBtn.textContent = 'Fjern valgte';
  if (els.moreDeleteBtn) els.moreDeleteBtn.textContent = t('delete_selected');

  const ok = await loadInfo();
  if (!ok) return;
  await loadPhotos();
}

if (els.authBtn) els.authBtn.addEventListener('click', runAuth);
if (els.authPassword) {
  els.authPassword.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      runAuth();
    }
  });
}
if (els.authName) {
  els.authName.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      runAuth();
    }
  });
}
if (els.uploadWrap) {
  els.uploadWrap.addEventListener('click', (e) => {
    e.preventDefault();
    openShareFilePicker();
  });
}
if (els.fileInput) {
  els.fileInput.addEventListener('change', () => {
    const list = (els.fileInput && els.fileInput.files) ? els.fileInput.files : null;
    if (!list || !list.length) return;
    // Clone FileList immediately; iOS Safari can keep picker UI blocked while
    // the change handler runs. Defer heavy work one tick for smoother UX.
    const files = Array.from(list);
    showStatus(`${t('upload_run')}: forbereder ${files.length} filer...`, 'ok');
    window.setTimeout(() => {
      try {
        runUpload(files);
      } catch (e) {
        console.error(e);
      }
    }, 50);
    // Clear value so the same files can be picked again later
    els.fileInput.value = '';
  });
}
if (els.deleteBtn) els.deleteBtn.addEventListener('click', runDelete);
if (els.pathBackTop) {
  els.pathBackTop.addEventListener('click', (e) => {
    e.preventDefault();
    navigateShareBackPath();
  });
}
if (els.moreBtn) {
  ['pointerdown', 'touchstart'].forEach((ev) => {
    els.moreBtn.addEventListener(ev, (e) => { e.stopPropagation(); }, { passive: true });
  });
  els.moreBtn.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    toggleShareMoreMenu();
  });
}
if (els.moreMenu) {
  ['pointerdown', 'touchstart', 'click'].forEach((ev) => {
    els.moreMenu.addEventListener(ev, (e) => { e.stopPropagation(); }, { passive: true });
  });
}
if (els.moreSelectBtn) {
  els.moreSelectBtn.addEventListener('click', () => {
    setSelectMode(!state.selectMode, { clearSelection: !state.selectMode ? false : true });
    closeShareMoreMenu();
  });
}
if (els.moreSelectAllBtn) {
  els.moreSelectAllBtn.addEventListener('click', () => {
    if (!state.selectMode || !canDeleteFromShare()) return;
    state.selected = new Set((state.visible || []).map((it) => Number(it && it.id || 0)).filter((id) => id > 0));
    state.selectionPulseId = 0;
    renderGrid();
    closeShareMoreMenu();
  });
}
if (els.moreClearBtn) {
  els.moreClearBtn.addEventListener('click', () => {
    state.selected = new Set();
    state.selectionPulseId = 0;
    renderGrid();
    closeShareMoreMenu();
  });
}
if (els.moreDeleteBtn) {
  els.moreDeleteBtn.addEventListener('click', async () => {
    closeShareMoreMenu();
    await runDelete();
  });
}
if (els.uploadPrepClose) {
  els.uploadPrepClose.addEventListener('click', closeUploadPrepModal);
}
if (els.uploadPrepCancel) {
  els.uploadPrepCancel.addEventListener('click', closeUploadPrepModal);
}
if (els.uploadPrepContinue) {
  els.uploadPrepContinue.addEventListener('click', continueUploadPrepModal);
}
if (els.uploadPrepModal) {
  els.uploadPrepModal.addEventListener('click', (e) => {
    if (e.target === els.uploadPrepModal || (e.target && e.target.classList && e.target.classList.contains('modal-backdrop'))) {
      closeUploadPrepModal();
    }
  });
}
if (els.uploadWarnClose) {
  els.uploadWarnClose.addEventListener('click', closeUploadWarningModal);
}
if (els.uploadWarnModal) {
  els.uploadWarnModal.addEventListener('click', (e) => {
    if (e.target === els.uploadWarnModal) closeUploadWarningModal();
  });
}

document.addEventListener('pointerdown', (e) => {
  const t = e.target;
  if (!(t instanceof Node)) return;
  if (els.moreMenu && els.moreMenu.contains(t)) return;
  if (els.moreBtn && els.moreBtn.contains(t)) return;
  closeShareMoreMenu();
});

window.addEventListener('resize', () => {
  const mobileNow = isMobileShareView();
  if (mobileNow === lastResizeIsMobile) return;
  lastResizeIsMobile = mobileNow;
  updateDeleteButton();
});

boot();

