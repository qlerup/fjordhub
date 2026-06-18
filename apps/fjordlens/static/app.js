const els = {
  grid: document.getElementById("galleryGrid"),
  topbar: document.getElementById("topbar"),
  searchShell: document.getElementById("searchShell"),
  searchToggleBtn: document.getElementById("searchToggleBtn"),
  search: document.getElementById("searchInput"),
  sort: document.getElementById("sortSelect"),
  timelineHeaderActions: document.getElementById("timelineHeaderActions"),
  scanBtn: document.getElementById("scanBtn"),
  rescanBtn: document.getElementById("rescanBtn"),
  rethumbBtn: document.getElementById("rethumbBtn"),
  fixThumbsBtn: document.getElementById("fixThumbsBtn"),
  stopAllProcessesBtn: document.getElementById("stopAllProcessesBtn"),
  clearIndexBtn: document.getElementById("clearIndexBtn"),
  factoryResetBtn: document.getElementById("factoryResetBtn"),
  appUpdateTitle: document.getElementById("appUpdateTitle"),
  appUpdateBranchLabel: document.getElementById("appUpdateBranchLabel"),
  appUpdateCurrentLabel: document.getElementById("appUpdateCurrentLabel"),
  appUpdateRemoteLabel: document.getElementById("appUpdateRemoteLabel"),
  appUpdateStateLabel: document.getElementById("appUpdateStateLabel"),
  appUpdateBranch: document.getElementById("appUpdateBranch"),
  appUpdateCurrent: document.getElementById("appUpdateCurrent"),
  appUpdateRemote: document.getElementById("appUpdateRemote"),
  appUpdateState: document.getElementById("appUpdateState"),
  appUpdateAutoCheckToggle: document.getElementById("appUpdateAutoCheckToggle"),
  appUpdateAutoCheckText: document.getElementById("appUpdateAutoCheckText"),
  appUpdateIntervalLabel: document.getElementById("appUpdateIntervalLabel"),
  appUpdateIntervalInput: document.getElementById("appUpdateIntervalInput"),
  appUpdateSettingsSaveBtn: document.getElementById("appUpdateSettingsSaveBtn"),
  appUpdateAutoMeta: document.getElementById("appUpdateAutoMeta"),
  appUpdateCheckBtn: document.getElementById("appUpdateCheckBtn"),
  appUpdateStartBtn: document.getElementById("appUpdateStartBtn"),
  appUpdateStatus: document.getElementById("appUpdateStatus"),
  appUpdateLog: document.getElementById("appUpdateLog"),
  appUpdateChoiceModal: document.getElementById("appUpdateChoiceModal"),
  appUpdateChoiceTitle: document.getElementById("appUpdateChoiceTitle"),
  appUpdateChoiceText: document.getElementById("appUpdateChoiceText"),
  appUpdateChoiceClose: document.getElementById("appUpdateChoiceClose"),
  appUpdateChoiceCleanupBtn: document.getElementById("appUpdateChoiceCleanupBtn"),
  appUpdateChoiceFastBtn: document.getElementById("appUpdateChoiceFastBtn"),
  aiIngestToggle: document.getElementById("aiIngestToggle"),
  aiIngestToggleText: document.getElementById("aiIngestToggleText"),
  aiPanelTitle: document.getElementById("aiPanelTitle"),
  aiEmbedTitle: document.getElementById("aiEmbedTitle"),
  aiEmbedDesc: document.getElementById("aiEmbedDesc"),
  aiDescTitle: document.getElementById("aiDescTitle"),
  aiDescDesc: document.getElementById("aiDescDesc"),
  aiDescModelLabel: document.getElementById("aiDescModelLabel"),
  aiDescribeToggle: document.getElementById("aiDescribeToggle"),
  aiDescribeToggleText: document.getElementById("aiDescribeToggleText"),
  aiDescribeForceStopBtn: document.getElementById("aiDescribeForceStopBtn"),
  aiDescribeRerunBtn: document.getElementById("aiDescribeRerunBtn"),
  aiDescribeClearBtn: document.getElementById("aiDescribeClearBtn"),
  aiDescribeLocalControls: document.getElementById("aiDescribeLocalControls"),
  aiDescribeModelRow: document.getElementById("aiDescribeModelRow"),
  aiDescExternalToggle: document.getElementById("aiDescExternalToggle"),
  aiDescExternalToggleText: document.getElementById("aiDescExternalToggleText"),
  aiDescExternalChooseBtn: document.getElementById("aiDescExternalChooseBtn"),
  aiDescExternalInfo: document.getElementById("aiDescExternalInfo"),
  hardwareUnloadQwenBtn: document.getElementById('hardwareUnloadQwenBtn'),
  hardwareStatus: document.getElementById('hardwareStatus'),
  aiDescribeModelSelect: document.getElementById("aiDescribeModelSelect"),
  aiDescribeStatus: document.getElementById("aiDescribeStatus"),
  aiDescribeRuntime: document.getElementById("aiDescribeRuntime"),
  aiFacesTitle: document.getElementById("aiFacesTitle"),
  aiFacesDesc: document.getElementById("aiFacesDesc"),
  aiEmbedRuntime: document.getElementById("aiEmbedRuntime"),
  aiFacesRuntime: document.getElementById("aiFacesRuntime"),
  aiStatus: document.getElementById("aiStatus"),
  facesToggle: document.getElementById("facesToggle"),
  facesToggleText: document.getElementById("facesToggleText"),
  facesStatus: document.getElementById("facesStatus"),
  aiIngestThrottleInput: document.getElementById("aiIngestThrottleInput"),
  facesThrottleInput: document.getElementById("facesThrottleInput"),
  aiPerfPresetLow: document.getElementById("aiPerfPresetLow"),
  aiPerfPresetNormal: document.getElementById("aiPerfPresetNormal"),
  aiPerfPresetFast: document.getElementById("aiPerfPresetFast"),
  aiPerfSaveBtn: document.getElementById("aiPerfSaveBtn"),
  aiPerfStatus: document.getElementById("aiPerfStatus"),
  uploadWorkflowTitle: document.getElementById("uploadWorkflowTitle"),
  uploadWorkflowDesc: document.getElementById("uploadWorkflowDesc"),
  uploadWorkflowModeGentle: document.getElementById("uploadWorkflowModeGentle"),
  uploadWorkflowModeAggressive: document.getElementById("uploadWorkflowModeAggressive"),
  uploadWorkflowGentleTitle: document.getElementById("uploadWorkflowGentleTitle"),
  uploadWorkflowGentleDesc: document.getElementById("uploadWorkflowGentleDesc"),
  uploadWorkflowAggressiveTitle: document.getElementById("uploadWorkflowAggressiveTitle"),
  uploadWorkflowAggressiveDesc: document.getElementById("uploadWorkflowAggressiveDesc"),
  uploadWorkflowExtraInfo: document.getElementById("uploadWorkflowExtraInfo"),
  uploadWorkflowSaveBtn: document.getElementById("uploadWorkflowSaveBtn"),
  uploadWorkflowStatus: document.getElementById("uploadWorkflowStatus"),
  fileTypesTitle: document.getElementById("fileTypesTitle"),
  fileTypesDesc: document.getElementById("fileTypesDesc"),
  fileTypeInput: document.getElementById("fileTypeInput"),
  fileTypeAddBtn: document.getElementById("fileTypeAddBtn"),
  fileTypeResetBtn: document.getElementById("fileTypeResetBtn"),
  fileTypeSaveBtn: document.getElementById("fileTypeSaveBtn"),
  fileTypeAllowedList: document.getElementById("fileTypeAllowedList"),
  fileTypeBlockedTitle: document.getElementById("fileTypeBlockedTitle"),
  fileTypeBlockedDesc: document.getElementById("fileTypeBlockedDesc"),
  fileTypeBlockedList: document.getElementById("fileTypeBlockedList"),
  fileTypeStatus: document.getElementById("fileTypeStatus"),
  heicConvertToggle: document.getElementById("heicConvertToggle"),
  heicKeepToggle: document.getElementById("heicKeepToggle"),
  heicStatus: document.getElementById("heicStatus"),
  rawConvertToggle: document.getElementById("rawConvertToggle"),
  rawKeepToggle: document.getElementById("rawKeepToggle"),
  rawStatus: document.getElementById("rawStatus"),
  movConvertToggle: document.getElementById("movConvertToggle"),
  movKeepToggle: document.getElementById("movKeepToggle"),
  movStatus: document.getElementById("movStatus"),
  movBulkConvertBtn: document.getElementById("movBulkConvertBtn"),
  rawBulkConvertBtn: document.getElementById("rawBulkConvertBtn"),
  heicBulkConvertBtn: document.getElementById("heicBulkConvertBtn"),
  mapperTools: document.getElementById("mapperTools"),
  mapperHeaderActions: document.getElementById("mapperHeaderActions"),
  mapperCurrentPath: document.getElementById("mapperCurrentPath"),
  mapperUpBtn: document.getElementById("mapperUpBtn"),
  mapperSearchShell: document.getElementById("mapperSearchShell"),
  mapperSearchToggleBtn: document.getElementById("mapperSearchToggleBtn"),
  mapperSearchInput: document.getElementById("mapperSearchInput"),
  mapperSortSelect: document.getElementById("mapperSortSelect"),
  mapperHeaderMenu: document.getElementById("mapperHeaderMenu"),
  mapperHeaderEditAction: document.getElementById("mapperHeaderEditAction"),
  mapperHeaderShareAction: document.getElementById("mapperHeaderShareAction"),
  mapperHeaderUploadAction: document.getElementById("mapperHeaderUploadAction"),
  mapperHeaderSortNewestAction: document.getElementById("mapperHeaderSortNewestAction"),
  mapperHeaderSortOldestAction: document.getElementById("mapperHeaderSortOldestAction"),
  mapperHeaderCreateAction: document.getElementById("mapperHeaderCreateAction"),
  mapperHeaderRenameAction: document.getElementById("mapperHeaderRenameAction"),
  mapperEditBtn: document.getElementById("mapperEditBtn"),
  mapperDeleteBtn: document.getElementById("mapperDeleteBtn"),
  mapperDownloadBtn: document.getElementById("mapperDownloadBtn"),
  mapperSelectAllBtn: document.getElementById("mapperSelectAllBtn"),
  mapperClearBtn: document.getElementById("mapperClearBtn"),
  mapperDownloadModal: document.getElementById('mapperDownloadModal'),
  mapperDownloadModalClose: document.getElementById('mapperDownloadModalClose'),
  downloadConvertedBtn: document.getElementById('downloadConvertedBtn'),
  downloadOriginalBtn: document.getElementById('downloadOriginalBtn'),
  mapperCancelBtn: document.getElementById("mapperCancelBtn"),
  mapperNavMenu: document.getElementById("mapperNavMenu"),
  mapperTreeNav: document.getElementById("mapperTreeNav"),
  mapperDropZone: document.getElementById("mapperDropZone"),
  mapperUploadInput: document.getElementById("mapperUploadInput"),
  iosUploadPrepModal: document.getElementById("iosUploadPrepModal"),
  iosUploadPrepClose: document.getElementById("iosUploadPrepClose"),
  iosUploadPrepCancel: document.getElementById("iosUploadPrepCancel"),
  iosUploadPrepContinue: document.getElementById("iosUploadPrepContinue"),
  stopScanBtn: null,
  status: document.getElementById("statusBar"),
  empty: document.getElementById("emptyState"),

  photoCount: document.getElementById("photoCount"),
  photoCountLabel: document.getElementById("photoCountLabel"),
  favoriteCount: document.getElementById("favoriteCount"),
  favoriteCountLabel: document.getElementById("favoriteCountLabel"),
  selectedCount: document.getElementById("selectedCount"),
  selectedCountLabel: document.getElementById("selectedCountLabel"),
  statPhotos: document.getElementById("statPhotos"),
  statFavorites: document.getElementById("statFavorites"),
  statSelected: document.getElementById("statSelected"),
  statHiddenToggle: document.getElementById("statHiddenToggle"),
  showHiddenToggle: document.getElementById("showHiddenToggle"),

  viewTitle: document.getElementById("viewTitle"),
  viewSubtitle: document.getElementById("viewSubtitle"),

  detailEmpty: document.getElementById("detailEmpty"),
  detailContent: document.getElementById("detailContent"),
  detailThumb: document.getElementById("detailThumb"),
  detailName: document.getElementById("detailName"),
  detailPath: document.getElementById("detailPath"),
  detailDate: document.getElementById("detailDate"),
  detailTime: document.getElementById("detailTime"),
  detailSize: document.getElementById("detailSize"),
  detailDims: document.getElementById("detailDims"),
  detailConvertedRow: document.getElementById("detailConvertedRow"),
  detailConverted: document.getElementById("detailConverted"),
  detailDevice: document.getElementById("detailDevice"),
  detailLens: document.getElementById("detailLens"),
  detailGps: document.getElementById("detailGps"),
  detailCountry: document.getElementById("detailCountry"),
  detailCity: document.getElementById("detailCity"),
  detailWeather: document.getElementById("detailWeather"),
  detailWeatherBtn: document.getElementById("detailWeatherBtn"),
  viWeather: document.getElementById("viWeather"),
  viWeatherBtn: document.getElementById("viWeatherBtn"),
  detailUploader: document.getElementById("detailUploader"),
  detailAiCaption: document.getElementById("detailAiCaption"),
  detailAiTags: document.getElementById("detailAiTags"),
  similarBtn: document.getElementById("similarBtn"),
  rawMeta: document.getElementById("rawMeta"),
  toggleRawBtn: document.getElementById("toggleRawBtn"),
  favoriteBtn: document.getElementById("favoriteBtn"),
  // logs
  logsBox: document.getElementById("liveLogs"),
  logsStart: document.getElementById("logsStart"),
  logsClear: document.getElementById("logsClear"),
  mainLogsBox: document.getElementById("mainLogs"),
  mainLogsStart: document.getElementById("mainLogsStart"),
  mainLogsClear: document.getElementById("mainLogsClear"),
  logsPanel: document.getElementById("logsPanel"),
  settingsPanel: document.getElementById("settingsPanel"),
  dnsPanelTitle: document.getElementById("dnsPanelTitle"),
  dnsPanelDesc: document.getElementById("dnsPanelDesc"),
  dnsDuckdnsBaseUrlLabel: document.getElementById("dnsDuckdnsBaseUrlLabel"),
  dnsDuckdnsBaseUrlInput: document.getElementById("dnsDuckdnsBaseUrlInput"),
  dnsSaveBtn: document.getElementById("dnsSaveBtn"),
  dnsStatus: document.getElementById("dnsStatus"),
  sharedLinksTitle: document.getElementById("sharedLinksTitle"),
  sharedLinksDesc: document.getElementById("sharedLinksDesc"),
  sharedLinksStatus: document.getElementById("sharedLinksStatus"),
  sharedLinksList: document.getElementById("sharedLinksList"),
  sharedEditModal: document.getElementById("sharedEditModal"),
  sharedEditModalTitle: document.getElementById("sharedEditModalTitle"),
  sharedEditModalClose: document.getElementById("sharedEditModalClose"),
  sharedEditModalCancel: document.getElementById("sharedEditModalCancel"),
  sharedEditModalSave: document.getElementById("sharedEditModalSave"),
  sharedEditNameLabel: document.getElementById("sharedEditNameLabel"),
  sharedEditNameInput: document.getElementById("sharedEditNameInput"),
  sharedEditFoldersLabel: document.getElementById("sharedEditFoldersLabel"),
  sharedEditFolders: document.getElementById("sharedEditFolders"),
  sharedEditExpireValueLabel: document.getElementById("sharedEditExpireValueLabel"),
  sharedEditExpireValue: document.getElementById("sharedEditExpireValue"),
  sharedEditExpireUnitLabel: document.getElementById("sharedEditExpireUnitLabel"),
  sharedEditExpireUnit: document.getElementById("sharedEditExpireUnit"),
  sharedEditNeverToggle: document.getElementById("sharedEditNeverToggle"),
  sharedEditNeverToggleText: document.getElementById("sharedEditNeverToggleText"),
  sharedEditPermissionLabel: document.getElementById("sharedEditPermissionLabel"),
  sharedEditPermission: document.getElementById("sharedEditPermission"),
  sharedEditDuckdnsToggle: document.getElementById("sharedEditDuckdnsToggle"),
  sharedEditDuckdnsToggleText: document.getElementById("sharedEditDuckdnsToggleText"),
  sharedEditPasswordToggle: document.getElementById("sharedEditPasswordToggle"),
  sharedEditPasswordToggleText: document.getElementById("sharedEditPasswordToggleText"),
  sharedEditPasswordWrap: document.getElementById("sharedEditPasswordWrap"),
  sharedEditPasswordLabel: document.getElementById("sharedEditPasswordLabel"),
  sharedEditPasswordInput: document.getElementById("sharedEditPasswordInput"),
  sharedEditRequireNameToggle: document.getElementById("sharedEditRequireNameToggle"),
  sharedEditRequireNameToggleText: document.getElementById("sharedEditRequireNameToggleText"),
  sharedEditError: document.getElementById("sharedEditError"),
  placesMapWrap: document.getElementById("placesMapWrap"),
  placesMapEl: document.getElementById("placesMap"),
  // duplicates
  dupesBtn: document.getElementById("dupesBtn"),
  dupesRun: document.getElementById("dupesRun"),
  dupeDist: document.getElementById("dupeDist"),
  dupeMin: document.getElementById("dupeMin"),
  dupeStatus: document.getElementById("dupeStatus"),
  dupeResults: document.getElementById("dupeResults"),
  // viewer
  viewer: document.getElementById("viewer"),
  viewerImg: document.getElementById("viewerImg"),
  viewerVideo: document.getElementById("viewerVideo"),
  viewerPrev: document.getElementById("viewerPrev"),
  viewerNext: document.getElementById("viewerNext"),
  viewerClose: document.getElementById("viewerClose"),
  viewerMenuBtn: document.getElementById("viewerMenuBtn"),
  viewerMenu: document.getElementById("viewerMenu"),
  viewerMenuInfoBtn: document.getElementById("viewerMenuInfoBtn"),
  viewerInfoMediaBtn: document.getElementById("viewerInfoMediaBtn"),
  viewerOpenOrig: document.getElementById("viewerOpenOrig"),
  similarModal: document.getElementById("similarModal"),
  similarModalClose: document.getElementById("similarModalClose"),
  similarModalTitle: document.getElementById("similarModalTitle"),
  similarDistanceForm: document.getElementById("similarDistanceForm"),
  similarMethodLabel: document.getElementById("similarMethodLabel"),
  similarMethodSelect: document.getElementById("similarMethodSelect"),
  similarAiMinLabel: document.getElementById("similarAiMinLabel"),
  similarAiMinInput: document.getElementById("similarAiMinInput"),
  similarPhashDistanceLabel: document.getElementById("similarPhashDistanceLabel"),
  similarPhashDistanceInput: document.getElementById("similarPhashDistanceInput"),
  similarDhashDistanceLabel: document.getElementById("similarDhashDistanceLabel"),
  similarDhashDistanceInput: document.getElementById("similarDhashDistanceInput"),
  similarAhashDistanceLabel: document.getElementById("similarAhashDistanceLabel"),
  similarAhashDistanceInput: document.getElementById("similarAhashDistanceInput"),
  similarDistanceApply: document.getElementById("similarDistanceApply"),
  similarSourcePanel: document.getElementById("similarSourcePanel"),
  similarSourceLabel: document.getElementById("similarSourceLabel"),
  similarSourcePreview: document.getElementById("similarSourcePreview"),
  similarModalStatus: document.getElementById("similarModalStatus"),
  similarModalGrid: document.getElementById("similarModalGrid"),
  menuBtn: document.getElementById("menuBtn"),
  drawerBackdrop: document.getElementById("drawerBackdrop"),
  mobileBottomNav: document.getElementById("mobileBottomNav"),
  mobileNavItems: document.querySelectorAll(".mobile-nav-item"),
  mobileUploadBar: document.getElementById("mobileUploadBar"),
  mobileUploadBarFill: document.getElementById("mobileUploadBarFill"),
  mobileUploadPct: document.getElementById("mobileUploadPct"),
  mobileUploadInfo: document.getElementById("mobileUploadInfo"),
  mobileUploadsBtn: document.getElementById("mobileUploadsBtn"),
  mobileUploadsBadge: document.getElementById("mobileUploadsBadge"),
  profileLink: document.getElementById("profileLink"),
  profileModal: document.getElementById("profileModal"),
  profileModalClose: document.getElementById("profileModalClose"),
  twofaModal: document.getElementById("twofaModal"),
  twofaModalClose: document.getElementById("twofaModalClose"),
  mapperCreateModal: document.getElementById("mapperCreateModal"),
  mapperCreateModalTitle: document.getElementById("mapperCreateModalTitle"),
  mapperCreateModalClose: document.getElementById("mapperCreateModalClose"),
  mapperCreateModalInput: document.getElementById("mapperCreateModalInput"),
  mapperCreateModalCancel: document.getElementById("mapperCreateModalCancel"),
  mapperCreateModalConfirm: document.getElementById("mapperCreateModalConfirm"),
  mapperShareModal: document.getElementById("mapperShareModal"),
  mapperShareModalTitle: document.getElementById("mapperShareModalTitle"),
  mapperShareModalClose: document.getElementById("mapperShareModalClose"),
  mapperShareModalCancel: document.getElementById("mapperShareModalCancel"),
  mapperShareModalConfirm: document.getElementById("mapperShareModalConfirm"),
  mapperShareNameLabel: document.getElementById("mapperShareNameLabel"),
  mapperShareNameInput: document.getElementById("mapperShareNameInput"),
  mapperShareFolderLabel: document.getElementById("mapperShareFolderLabel"),
  mapperShareFolderInput: document.getElementById("mapperShareFolderInput"),
  mapperShareExpireLabel: document.getElementById("mapperShareExpireLabel"),
  mapperShareExpireValue: document.getElementById("mapperShareExpireValue"),
  mapperShareExpireUnitLabel: document.getElementById("mapperShareExpireUnitLabel"),
  mapperShareExpireUnit: document.getElementById("mapperShareExpireUnit"),
  mapperSharePermissionLabel: document.getElementById("mapperSharePermissionLabel"),
  mapperSharePermission: document.getElementById("mapperSharePermission"),
  mapperShareDuckdnsToggle: document.getElementById("mapperShareDuckdnsToggle"),
  mapperShareDuckdnsToggleText: document.getElementById("mapperShareDuckdnsToggleText"),
  mapperSharePasswordToggle: document.getElementById("mapperSharePasswordToggle"),
  mapperSharePasswordToggleText: document.getElementById("mapperSharePasswordToggleText"),
  mapperShareRequireNameToggle: document.getElementById("mapperShareRequireNameToggle"),
  mapperShareRequireNameToggleText: document.getElementById("mapperShareRequireNameToggleText"),
  mapperSharePasswordWrap: document.getElementById("mapperSharePasswordWrap"),
  mapperSharePasswordLabel: document.getElementById("mapperSharePasswordLabel"),
  mapperSharePasswordInput: document.getElementById("mapperSharePasswordInput"),
  mapperShareResultWrap: document.getElementById("mapperShareResultWrap"),
  mapperShareResultLabel: document.getElementById("mapperShareResultLabel"),
  mapperShareResultInput: document.getElementById("mapperShareResultInput"),
  mapperShareCopyBtn: document.getElementById("mapperShareCopyBtn"),
  scanModal: document.getElementById("scanModal"),
  scanModalClose: document.getElementById("scanModalClose"),
  scanModalCancel: document.getElementById("scanModalCancel"),
  scanModalStart: document.getElementById("scanModalStart"),
  aiScopeModal: document.getElementById("aiScopeModal"),
  aiScopeModalTitle: document.getElementById("aiScopeModalTitle"),
  aiScopeModalText: document.getElementById("aiScopeModalText"),
  aiScopeModalClose: document.getElementById("aiScopeModalClose"),
  aiScopeModalCancel: document.getElementById("aiScopeModalCancel"),
  aiScopeModalNew: document.getElementById("aiScopeModalNew"),
  aiScopeModalAll: document.getElementById("aiScopeModalAll"),
  conversionScopeModal: document.getElementById("conversionScopeModal"),
  conversionScopeModalTitle: document.getElementById("conversionScopeModalTitle"),
  conversionScopeModalText: document.getElementById("conversionScopeModalText"),
  conversionScopeModalClose: document.getElementById("conversionScopeModalClose"),
  conversionScopeModalCancel: document.getElementById("conversionScopeModalCancel"),
  conversionScopeModalNew: document.getElementById("conversionScopeModalNew"),
  conversionScopeModalAll: document.getElementById("conversionScopeModalAll"),
  aiExternalModal: document.getElementById("aiExternalModal"),
  aiExternalModalTitle: document.getElementById("aiExternalModalTitle"),
  aiExternalModalText: document.getElementById("aiExternalModalText"),
  aiExternalModalClose: document.getElementById("aiExternalModalClose"),
  aiExternalModalCancel: document.getElementById("aiExternalModalCancel"),
  aiExternalModalSave: document.getElementById("aiExternalModalSave"),
  aiExternalFolders: document.getElementById("aiExternalFolders"),
  aiExternalTokenInput: document.getElementById("aiExternalTokenInput"),
  aiExternalCopyTokenBtn: document.getElementById("aiExternalCopyTokenBtn"),
  aiExternalLinksBtn: document.getElementById("aiExternalLinksBtn"),
  aiExternalRotateTokenBtn: document.getElementById("aiExternalRotateTokenBtn"),
  aiExternalModalStatus: document.getElementById("aiExternalModalStatus"),
  aiExternalLinksModal: document.getElementById("aiExternalLinksModal"),
  aiExternalLinksModalTitle: document.getElementById("aiExternalLinksModalTitle"),
  aiExternalLinksModalText: document.getElementById("aiExternalLinksModalText"),
  aiExternalLinksModalClose: document.getElementById("aiExternalLinksModalClose"),
  aiExternalLinksModalDone: document.getElementById("aiExternalLinksModalDone"),
  aiExternalLinksList: document.getElementById("aiExternalLinksList"),
  aiExternalLinksStatus: document.getElementById("aiExternalLinksStatus"),
  // date edit controls
  editDateBtn: document.getElementById('editDateBtn'),
  dateEditWrap: document.getElementById('dateEditWrap'),
  dateInput: document.getElementById('dateInput'),
  dateSaveBtn: document.getElementById('dateSaveBtn'),
  dateCancelBtn: document.getElementById('dateCancelBtn'),
  // gps edit controls
  editGpsBtn: document.getElementById('editGpsBtn'),
  gpsEditWrap: document.getElementById('gpsEditWrap'),
  gpsMapEl: document.getElementById('gpsMap'),
  gpsCoordText: document.getElementById('gpsCoordText'),
  gpsSaveBtn: document.getElementById('gpsSaveBtn'),
  gpsCancelBtn: document.getElementById('gpsCancelBtn'),
  gpsEarthBtn: document.getElementById('gpsEarthBtn'),
  gpsSearchInput: document.getElementById('gpsSearchInput'),
  gpsSearchList: document.getElementById('gpsSearchList'),
  // upload overlay
  uploadOverlay: document.getElementById("uploadOverlay"),
  uploadProgressBar: document.getElementById("uploadProgressBar"),
  uploadProgressText: document.getElementById("uploadProgressText"),
  uploadMonitor: document.getElementById("uploadMonitor"),
  uploadMonitorToggle: document.getElementById("uploadMonitorToggle"),
  uploadMonitorStop: document.getElementById("uploadMonitorStop"),
  uploadMonitorBar: document.getElementById("uploadMonitorBar"),
  uploadMonitorSummary: document.getElementById("uploadMonitorSummary"),
  uploadMonitorCurrent: document.getElementById("uploadMonitorCurrent"),
  uploadMonitorList: document.getElementById("uploadMonitorList"),
  uploadTopStatus: document.getElementById("uploadTopStatus"),
  uploadTopStatusLabel: document.getElementById("uploadTopStatusLabel"),
  uploadTopStatusBar: document.getElementById("uploadTopStatusBar"),
  uploadTopProcessRow: document.getElementById("uploadTopProcessRow"),
  downloadTopStatus: document.getElementById("downloadTopStatus"),
  downloadTopStatusLabel: document.getElementById("downloadTopStatusLabel"),
  downloadTopStatusBar: document.getElementById("downloadTopStatusBar"),
  downloadTopStatusCancel: document.getElementById("downloadTopStatusCancel"),
};

function ensureTimelineHeaderActions() {
  if (els.timelineHeaderActions) return els.timelineHeaderActions;
  const header = document.querySelector(".content-header");
  if (!header) return null;
  const node = document.createElement("div");
  node.id = "timelineHeaderActions";
  node.className = "timeline-header-actions";
  node.setAttribute("aria-label", "Tidslinje handlinger");
  const mapperActions = els.mapperHeaderActions || document.getElementById("mapperHeaderActions");
  if (mapperActions && mapperActions.parentElement === header) header.insertBefore(node, mapperActions);
  else header.appendChild(node);
  els.timelineHeaderActions = node;
  return node;
}

function placeGlobalSearchSortForView() {
  const topbar = els.topbar || document.getElementById("topbar") || document.querySelector(".topbar");
  if (!topbar || !els.searchShell || !els.sort) return;
  const timelineActions = ensureTimelineHeaderActions();
  const inHeaderBarView = !!(state && (state.view === "timeline" || state.view === "favorites" || state.view === "steder" || state.view === "kameraer"));
  const target = (inHeaderBarView && timelineActions) ? timelineActions : topbar;
  if (els.searchShell.parentElement !== target) target.appendChild(els.searchShell);
  if (els.sort.parentElement !== target) target.appendChild(els.sort);
}

function isSmallMobile() {
  try {
    return !!(window.matchMedia && window.matchMedia('(max-width: 760px)').matches);
  } catch (e) {
    return false;
  }
}

function ensureUploadOverlayRefs() {
  if (!els.uploadOverlay) els.uploadOverlay = document.getElementById("uploadOverlay");
  if (!els.uploadProgressBar) els.uploadProgressBar = document.getElementById("uploadProgressBar");
  if (!els.uploadProgressText) els.uploadProgressText = document.getElementById("uploadProgressText");
}

function ensureUploadMonitorRefs() {
  if (!els.uploadMonitor) els.uploadMonitor = document.getElementById("uploadMonitor");
  if (!els.uploadMonitorToggle) els.uploadMonitorToggle = document.getElementById("uploadMonitorToggle");
  if (!els.uploadMonitorStop) els.uploadMonitorStop = document.getElementById("uploadMonitorStop");
  if (!els.uploadMonitorBar) els.uploadMonitorBar = document.getElementById("uploadMonitorBar");
  if (!els.uploadMonitorSummary) els.uploadMonitorSummary = document.getElementById("uploadMonitorSummary");
  if (!els.uploadMonitorCurrent) els.uploadMonitorCurrent = document.getElementById("uploadMonitorCurrent");
  if (!els.uploadMonitorList) els.uploadMonitorList = document.getElementById("uploadMonitorList");
}

function ensureUploadTopStatusRefs() {
  if (!els.uploadTopStatus) els.uploadTopStatus = document.getElementById("uploadTopStatus");
  if (!els.uploadTopStatusLabel) els.uploadTopStatusLabel = document.getElementById("uploadTopStatusLabel");
  if (!els.uploadTopStatusBar) els.uploadTopStatusBar = document.getElementById("uploadTopStatusBar");
  if (!els.uploadTopProcessRow) els.uploadTopProcessRow = document.getElementById("uploadTopProcessRow");
}

function ensureDownloadTopStatusRefs() {
  if (!els.downloadTopStatus) els.downloadTopStatus = document.getElementById("downloadTopStatus");
  if (!els.downloadTopStatusLabel) els.downloadTopStatusLabel = document.getElementById("downloadTopStatusLabel");
  if (!els.downloadTopStatusBar) els.downloadTopStatusBar = document.getElementById("downloadTopStatusBar");
  if (!els.downloadTopStatusCancel) els.downloadTopStatusCancel = document.getElementById("downloadTopStatusCancel");
}

function setDownloadTopStatusCancelable(on = false) {
  ensureDownloadTopStatusRefs();
  if (els.downloadTopStatus) els.downloadTopStatus.classList.toggle('download-cancelable', !!on);
  if (els.downloadTopStatusCancel) {
    els.downloadTopStatusCancel.disabled = !on;
    els.downloadTopStatusCancel.title = tr('download_status_cancel_title');
    els.downloadTopStatusCancel.setAttribute('aria-label', tr('download_status_cancel_title'));
  }
}

// Generic top status helpers so we can reuse the same bar
function showTopStatusMessage(label, pct = null) {
  ensureUploadTopStatusRefs();
  if (!els.uploadTopStatus) return;
  els.uploadTopStatus.classList.remove('multi');
  els.uploadTopStatus.classList.remove('hidden');
  if (els.uploadTopProcessRow) {
    els.uploadTopProcessRow.classList.add('hidden');
    els.uploadTopProcessRow.innerHTML = '';
  }
  if (els.uploadTopStatusLabel) els.uploadTopStatusLabel.textContent = String(label || '');
  if (els.uploadTopStatusBar) {
    els.uploadTopStatusBar.classList.remove('indeterminate');
    const v = pct == null ? null : Math.max(0, Math.min(100, Number(pct || 0)));
    els.uploadTopStatusBar.style.width = (v == null) ? '0%' : `${v}%`;
  }
}

function hideTopStatusMessage() {
  ensureUploadTopStatusRefs();
  if (!els.uploadTopStatus) return;
  els.uploadTopStatus.classList.remove('multi');
  els.uploadTopStatus.classList.add('hidden');
  if (els.uploadTopStatusLabel) els.uploadTopStatusLabel.textContent = 'Upload: Klar';
  if (els.uploadTopStatusBar) {
    els.uploadTopStatusBar.classList.remove('indeterminate');
    els.uploadTopStatusBar.style.width = '0%';
  }
  if (els.uploadTopProcessRow) {
    els.uploadTopProcessRow.classList.add('hidden');
    els.uploadTopProcessRow.innerHTML = '';
  }
}

// Toggle indeterminate animation for the top status bar (no known percentage)
function setTopStatusIndeterminate(on = true) {
  ensureUploadTopStatusRefs();
  if (!els.uploadTopStatus || !els.uploadTopStatusBar) return;
  els.uploadTopStatus.classList.remove('hidden');
  els.uploadTopStatusBar.classList.toggle('indeterminate', !!on);
  if (!on) {
    els.uploadTopStatusBar.style.width = '0%';
  }
}

function _uploadProcessLabel(key) {
  const k = String(key || '').toLowerCase();
  if (k === 'metadata') return tr('upload_proc_metadata');
  if (k === 'thumbnails') return tr('upload_proc_thumbnails');
  if (k === 'faces') return tr('upload_proc_faces');
  if (k === 'embeddings') return tr('upload_proc_embeddings');
  if (k === 'descriptions') return tr('upload_proc_descriptions');
  return k || '-';
}

function clearUploadTopProcessStatus() {
  ensureUploadTopStatusRefs();
  if (!els.uploadTopStatus) return;
  els.uploadTopStatus.classList.remove('multi');
  if (els.uploadTopProcessRow) {
    els.uploadTopProcessRow.classList.add('hidden');
    els.uploadTopProcessRow.innerHTML = '';
  }
}

function renderUploadTopProcessStatus(processStatus) {
  ensureUploadTopStatusRefs();
  if (!els.uploadTopStatus || !els.uploadTopProcessRow || !processStatus || typeof processStatus !== 'object') {
    clearUploadTopProcessStatus();
    return false;
  }
  const order = ['metadata', 'thumbnails', 'faces', 'embeddings', 'descriptions'];
  const cards = [];
  for (const key of order) {
    const src = processStatus[key];
    if (!src || typeof src !== 'object') continue;
    const enabled = src.enabled !== false;
    const total = Math.max(0, Number(src.total || 0));
    const processed = Math.max(0, Number(src.processed || 0));
    const errors = Math.max(0, Number(src.errors || 0));
    const running = !!src.running;
    const inFlight = Math.max(0, Number(src.in_flight || 0));
    const queued = Math.max(0, Number(src.queued || Math.max(0, total - processed - inFlight)));
    const pct = total > 0 ? Math.max(0, Math.min(100, Math.round((processed / total) * 100))) : 0;
    if (!enabled) continue;
    if (key === 'metadata' && !running && errors <= 0 && (total <= 0 || processed >= total)) continue;
    const statusText = enabled ? `${processed}/${total}${errors ? ` · ${tr('status_errors_label')} ${errors}` : ''}` : tr('upload_proc_off');
    const queueText = enabled
      ? [
          tr('upload_proc_queue').replace('{count}', String(queued)),
          inFlight > 0 ? tr('upload_proc_running').replace('{count}', String(inFlight)) : '',
        ].filter(Boolean).join(' · ')
      : '';
    cards.push(
      `<div class="upload-top-proc ${enabled ? '' : 'off'} ${running ? 'run' : ''}" data-proc="${escapeHtml(key)}">` +
      `<div class="upload-top-proc-name">${escapeHtml(_uploadProcessLabel(key))}</div>` +
      `<div class="upload-top-proc-meta">${escapeHtml(statusText)}</div>` +
      `<div class="upload-top-proc-queue">${escapeHtml(queueText)}</div>` +
      `<div class="upload-top-proc-bar"><span style="width:${enabled ? pct : 0}%"></span></div>` +
      `</div>`
    );
  }
  if (!cards.length) {
    clearUploadTopProcessStatus();
    return false;
  }
  els.uploadTopStatus.classList.add('multi');
  els.uploadTopStatus.classList.remove('hidden');
  els.uploadTopProcessRow.innerHTML = cards.join('');
  els.uploadTopProcessRow.classList.remove('hidden');
  return true;
}

function summarizeUploadProcessStatus(processStatus) {
  if (!processStatus || typeof processStatus !== 'object') return '';
  const order = ['thumbnails', 'faces', 'embeddings', 'descriptions', 'metadata'];
  let fallback = '';
  for (const key of order) {
    const src = processStatus[key];
    if (!src || typeof src !== 'object' || src.enabled === false) continue;
    const total = Math.max(0, Number(src.total || 0));
    const processed = Math.max(0, Number(src.processed || 0));
    const running = !!src.running;
    const inFlight = Math.max(0, Number(src.in_flight || 0));
    const pct = total > 0 ? Math.max(0, Math.min(100, Math.round((processed / total) * 100))) : 0;
    const label = `${_uploadProcessLabel(key)} · ${processed}/${total} · ${pct}%${inFlight ? ` · kører: ${inFlight}` : ''}`;
    if (running) return label;
    if (!fallback && total > 0 && processed < total) fallback = label;
  }
  return fallback;
}

function showDownloadTopStatusMessage(label, pct = null) {
  ensureDownloadTopStatusRefs();
  if (!els.downloadTopStatus) return;
  els.downloadTopStatus.classList.remove('hidden');
  if (els.downloadTopStatusLabel) els.downloadTopStatusLabel.textContent = String(label || '');
  if (els.downloadTopStatusBar) {
    const v = pct == null ? null : Math.max(0, Math.min(100, Number(pct || 0)));
    els.downloadTopStatusBar.style.width = (v == null) ? '0%' : `${v}%`;
  }
}

function hideDownloadTopStatusMessage() {
  ensureDownloadTopStatusRefs();
  if (!els.downloadTopStatus) return;
  setDownloadTopStatusCancelable(false);
  els.downloadTopStatus.classList.add('hidden');
  if (els.downloadTopStatusLabel) els.downloadTopStatusLabel.textContent = tr('download_status_ready');
  if (els.downloadTopStatusBar) {
    els.downloadTopStatusBar.style.width = '0%';
    els.downloadTopStatusBar.classList.remove('indeterminate');
  }
}

function setDownloadTopStatusIndeterminate(on = true) {
  ensureDownloadTopStatusRefs();
  if (!els.downloadTopStatus || !els.downloadTopStatusBar) return;
  els.downloadTopStatus.classList.remove('hidden');
  els.downloadTopStatusBar.classList.toggle('indeterminate', !!on);
  if (!on) {
    els.downloadTopStatusBar.style.width = '0%';
  }
}

let uploadMonitorDomEventsBound = false;
function bindUploadMonitorDomEvents() {
  if (uploadMonitorDomEventsBound) return;
  document.addEventListener('click', (event) => {
    const toggleBtn = event && event.target && event.target.closest ? event.target.closest('#uploadMonitorToggle') : null;
    if (toggleBtn) {
      uploadUiState.collapsed = !uploadUiState.collapsed;
      showUploadMonitor();
      return;
    }

    const stopBtn = event && event.target && event.target.closest ? event.target.closest('#uploadMonitorStop') : null;
    if (stopBtn) {
      if (stopBtn.disabled) return;
      requestStopUpload();
    }
  });
  uploadMonitorDomEventsBound = true;
}

// Immediate emergency cleanup in case an overlay/backdrop was left in DOM
(function immediateCleanup(){
  try { document.querySelectorAll('.modal-backdrop[data-ephemeral="1"]').forEach(el=>{ el.classList.remove('active'); if (el.parentElement) el.parentElement.removeChild(el); }); } catch{}
  try { document.querySelectorAll('.upload-overlay').forEach(el=> el.classList.add('hidden')); } catch{}
})();
try { window.addEventListener('DOMContentLoaded', ()=>{
  try { document.querySelectorAll('.modal-backdrop[data-ephemeral="1"]').forEach(el=>{ el.classList.remove('active'); if (el.parentElement) el.parentElement.removeChild(el); }); } catch{}
  try { document.querySelectorAll('.upload-overlay').forEach(el=> el.classList.add('hidden')); } catch{}
  try { initThemeControls(); } catch{}
}); } catch{}

// People: toggle 'Vis skjulte'
try {
  if (els.showHiddenToggle) {
    els.showHiddenToggle.addEventListener('change', ()=>{
      state.showHiddenPeople = !!els.showHiddenToggle.checked;
      if (state.view === 'personer') loadPeople();
    });
  }
} catch {}

// Initialize globals from bootstrap element if not already present
(() => {
  try {
    if (!window.APP_PROFILE || !window.APP_ROLE || typeof window.APP_SCAN_ENABLED === 'undefined') {
      const el = document.getElementById('bootstrapData');
      if (el) {
        const p = el.getAttribute('data-profile') || '{}';
        const r = el.getAttribute('data-role') || '"user"';
        const s = el.getAttribute('data-scan-enabled') || 'false';
        if (!window.APP_PROFILE) window.APP_PROFILE = JSON.parse(p);
        if (!window.APP_ROLE) window.APP_ROLE = JSON.parse(r);
        if (typeof window.APP_SCAN_ENABLED === 'undefined') window.APP_SCAN_ENABLED = !!JSON.parse(s);
      }
    }
  } catch {}
})();

const APP_PROFILE = (window.APP_PROFILE && typeof window.APP_PROFILE === 'object') ? window.APP_PROFILE : {};
const SCAN_FEATURES_ENABLED = (typeof window.APP_SCAN_ENABLED === 'boolean') ? window.APP_SCAN_ENABLED : false;
const UI_LANGUAGES = new Set(['da', 'en']);

function applyScanFeatureVisibility() {
  try {
    // 'Scan bibliotek' er den eneste der skal skjules for alle, når scan-funktionen er slået fra
    if (!SCAN_FEATURES_ENABLED) {
      if (els.scanBtn) els.scanBtn.style.display = 'none';
      if (els.scanModal) els.scanModal.classList.add('hidden');
    }
    // De andre vedligeholdelsesknapper (rescan/rethumb/fix) forbliver synlige
  } catch {}
}
applyScanFeatureVisibility();

// THEME: System/Light/Dark with auto-detect and persistence
const THEME_STORE_KEY = 'fl_theme_mode'; // 'system' | 'light' | 'dark'
function getThemeMetaOverride(){ return document.querySelector('meta#theme-color-override'); }
function systemPrefersDark(){ try { return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches; } catch { return true; } }
function themeColors(){
  return {
    dark: '#0f1115',
    light: '#f5f6f8',
  };
}
function applyTheme(mode){
  const root = document.documentElement;
  const meta = getThemeMetaOverride();
  const colors = themeColors();
  // Normalize
  mode = (mode === 'light' || mode === 'dark') ? mode : 'system';
  if (mode === 'system') {
    root.removeAttribute('data-theme');
    const dark = systemPrefersDark();
    if (meta) meta.setAttribute('content', dark ? colors.dark : colors.light);
  } else {
    root.setAttribute('data-theme', mode);
    if (meta) meta.setAttribute('content', mode === 'dark' ? colors.dark : colors.light);
  }
  try { localStorage.setItem(THEME_STORE_KEY, mode); } catch {}
}
function initThemeControls(){
  // Apply saved preference immediately
  let saved = 'system';
  try {
    saved = (window.APP_PROFILE && typeof window.APP_PROFILE === 'object' && window.APP_PROFILE.theme_mode) || localStorage.getItem(THEME_STORE_KEY) || 'system';
  } catch {}
  applyTheme(saved);
  // Listen for system changes only when in system mode
  try {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    mq.addEventListener ? mq.addEventListener('change', ()=>{
      try { const mode = localStorage.getItem(THEME_STORE_KEY) || 'system'; if (mode === 'system') applyTheme('system'); } catch {}
    }) : mq.addListener && mq.addListener(()=>{
      try { const mode = localStorage.getItem(THEME_STORE_KEY) || 'system'; if (mode === 'system') applyTheme('system'); } catch {}
    });
  } catch {}
  // Settings select
  const sel = document.getElementById('themeSelect');
  if (sel) {
    try { sel.value = saved; } catch {}
    sel.addEventListener('change', ()=> applyTheme(sel.value));
  }
}

const I18N = {
  da: {
    nav_timeline: '📅 Tidlinje',
    nav_favorites: '⭐ Favoritter',
    nav_places: '📍 Steder',
    nav_cameras: '📸 Kameraer',
    nav_folders: '🗂️ Mapper',
    nav_photoframe: '🖼️ Photoframe',
    nav_people: '🙂 Personer',
    nav_settings: '⚙️ Indstillinger',
    profile_link: 'Profil',
    logout_link: 'Log ud',
    search_placeholder: 'Søg på dansk: strand, bil, skov, kamera, dato, filnavn...',
    tab_maint: 'Vedligeholdelse',
    tab_update: 'Opdatering',
    tab_ai: 'AI',
    tab_upload_workflow: 'Upload workflow',
    tab_file_types: 'Filtyper',
    tab_hardware: 'Hardware',
    tab_heic: 'Konvertering',
    tab_dns: 'DNS',
    tab_shared: 'Delte',
    tab_logs: 'Logs',
    tab_users: 'Brugere',
    tab_twofa: 'Min 2FA',
    profile_open_twofa: 'Administrer 2FA',
    tab_profile: 'Profil',
    tab_other: 'Andet',
    upload_workflow_title: 'Upload workflow',
    upload_workflow_desc: 'Vælg hvordan upload-efterbehandling kører.',
    upload_workflow_gentle_title: 'Skånsom',
    upload_workflow_gentle_desc: 'Kører én fase ad gangen for at skåne systemet.',
    upload_workflow_aggressive_title: 'Kraftig',
    upload_workflow_aggressive_desc: 'Kører faser parallelt. Ansigter behandles i batch på 10 filer.',
    upload_workflow_extra_info: 'Thumbnail runtime: {thumb_runtime} · Ansigtsbatch: {batch_size}',
    upload_workflow_save: 'Gem workflow',
    upload_workflow_saved: 'Upload workflow gemt.',
    upload_workflow_load_failed: 'Kunne ikke hente upload workflow.',
    upload_workflow_save_failed: 'Kunne ikke gemme upload workflow.',
    upload_workflow_running: 'Parallel behandling…',
    file_types_title: 'Upload filtyper',
    file_types_desc: 'Whitelist de filendelser, FjordLens må modtage. Ukendte typer uploades som filer uden medie-behandling.',
    file_types_add: 'Tilføj',
    file_types_reset: 'Nulstil',
    file_types_save: 'Gem filtyper',
    file_types_saved: 'Filtyper gemt.',
    file_types_load_failed: 'Kunne ikke hente filtyper.',
    file_types_save_failed: 'Kunne ikke gemme filtyper.',
    file_types_invalid: 'Skriv en filtype som .png.',
    file_types_unsupported: '{ext} kan tilføjes, men bliver ikke behandlet som billede eller video.',
    file_types_duplicate: '{ext} er allerede på listen.',
    file_types_allowed_empty: 'Ingen filtyper er tilladt.',
    file_types_blocked_title: 'Blokerede filtyper',
    file_types_blocked_desc: 'Standard mediefiltyper, der ikke er på whitelist.',
    file_types_blocked_empty: 'Ingen standard mediefiltyper er blokeret.',
    upload_blocked_file_types: 'Blokeret filtype: {types}. Kun whitelistede filtyper uploades.',
    upload_proc_metadata: 'Metadata',
    upload_proc_thumbnails: 'Thumbnails',
    upload_proc_faces: 'Ansigter',
    upload_proc_embeddings: 'Embeddings',
    upload_proc_descriptions: 'Beskrivelser',
    upload_proc_off: 'Slået fra',
    upload_proc_queue: 'i kø: {count}',
    upload_proc_running: 'kører: {count}',
    view_timeline_title: 'Tidlinje',
    view_timeline_sub: 'Dato-grupperet oversigt (år/måned)',
    view_favorites_title: 'Favoritter',
    view_favorites_sub: 'Markerede billeder',
    view_steder_title: 'Steder',
    view_steder_sub: 'Billeder med GPS/placeringsdata',
    view_kameraer_title: 'Kameraer',
    view_kameraer_sub: 'Filtreret på billeder med kameradata',
    view_mapper_title: 'Mapper',
    view_mapper_sub: 'Grupperet efter kilde-mappe',
    view_photoframe_title: 'Photoframe',
    view_photoframe_sub: 'Status på dine fotorammer',
    view_personer_title: 'Personer',
    view_personer_sub: '',
    view_settings_title: 'Indstillinger',
    view_settings_sub: 'Vedligeholdelse og administration',
    sort_date_desc: 'Nyeste først',
    sort_date_asc: 'Ældste først',
    sort_name_asc: 'Navn A-Å',
    sort_name_desc: 'Navn Å-A',
    sort_size_desc: 'Størst først',
    sort_size_asc: 'Mindst først',
    stat_photos: 'Billeder',
    stat_people: 'Personer',
    stat_favorites: 'Favoritter',
    stat_selected: 'Valgt',
    stat_show_hidden: 'Vis skjulte',
    empty_people: 'Ingen personer endnu. Upload billeder med ansigter eller kør ansigtsindeksering.',
    empty_no_photos: 'Ingen billeder endnu. Slip filer for at uploade eller scan biblioteket.',
    empty_no_matches: "Ingen billeder matcher filteret endnu. Prøv 'Scan bibliotek'.",
    empty_mapper_tree: 'Ingen mapper endnu.',
    photoframe_intro_title: 'Photoframe',
    photoframe_intro_sub: 'Overblik over fotorammer og om de er online.',
    photoframe_loading: 'Tjekker fotorammer...',
    photoframe_refresh: 'Opdater',
    photoframe_empty_title: 'Ingen fotorammer konfigureret endnu.',
    photoframe_empty_sub: 'Generer en token med \"Opret fotoramme\", indsæt den på rammen, og vent på første forbindelse.',
    photoframe_status_online: 'Online',
    photoframe_status_offline: 'Offline',
    photoframe_status_unknown: 'Ukendt',
    photoframe_last_checked: 'Sidst tjekket',
    photoframe_card_endpoint: 'Endpoint',
    photoframe_card_ip: 'IP',
    photoframe_card_local_ip: 'Lokal IP',
    photoframe_card_token: 'Token',
    photoframe_card_scope: 'Indhold',
    photoframe_scope_summary_all: 'Alle billeder',
    photoframe_scope_summary_folders: 'Mapper ({count})',
    photoframe_scope_summary_photos: 'Billeder ({count})',
    photoframe_card_last_seen: 'Sidst online',
    photoframe_card_setup: 'Opsætning',
    photoframe_setup_ready: 'Klar',
    photoframe_setup_pending: 'Mangler setup',
    photoframe_card_feed: 'Feed',
    photoframe_card_error: 'Fejl',
    photoframe_card_update: 'Opdatering',
    photoframe_card_sync: 'Synk',
    photoframe_card_version: 'Version',
    photoframe_card_video_prepare: 'Video klargøring',
    photoframe_video_prepare_processing: 'Klargør videoer',
    photoframe_video_prepare_pending: 'Afventer klargøring',
    photoframe_video_prepare_retrying: 'Starter klargøring',
    photoframe_video_prepare_ready: 'Klar',
    photoframe_video_prepare_progress: '{ready}/{total} klar - {queued} i kø - {waiting} mangler',
    photoframe_video_prepare_capped: '(udsnit)',
    photoframe_version_latest: 'Nyeste',
    photoframe_version_outdated: 'Skal opdateres',
    photoframe_version_unknown: 'Ukendt',
    photoframe_update_btn: 'Opdater enhed',
    photoframe_update_upload_btn: 'Upload zip',
    photoframe_update_upload_all_btn: 'Upload zip til alle',
    photoframe_update_confirm: 'Start baggrundsopdatering af {name}?',
    photoframe_update_upload_confirm: 'Start opdatering af {name} med zip-filen {file}?',
    photoframe_update_upload_all_confirm: 'Start opdatering af alle ({count}) med zip-filen {file}?',
    photoframe_update_queued: 'Opdatering sat i ko.',
    photoframe_update_upload_queued: 'Zip uploadet og opdatering sat i ko.',
    photoframe_update_upload_all_queued: 'Zip uploadet. {count} fotorammer sat i ko.',
    photoframe_update_failed: 'Kunne ikke starte opdatering.',
    photoframe_update_upload_failed: 'Kunne ikke uploade update-zip.',
    photoframe_update_upload_all_failed: 'Kunne ikke starte opdatering til alle.',
    photoframe_update_cancel_btn: 'Stop opdatering',
    photoframe_update_cancel_confirm: 'Stop opdatering for {name}?',
    photoframe_update_cancel_done: 'Opdatering stoppet.',
    photoframe_update_cancel_failed: 'Kunne ikke stoppe opdatering.',
    photoframe_restart_kiosk_btn: 'Genstart kiosk',
    photoframe_restart_kiosk_confirm: 'Genstarte kioskmode for {name}?',
    photoframe_restart_kiosk_queued: 'Kiosk-genstart sendt til enhed.',
    photoframe_restart_kiosk_failed: 'Kunne ikke sende kiosk-genstart.',
    photoframe_reset_device_btn: 'Nulstil',
    photoframe_reset_device_confirm: 'Nulstil {name}? Dette sletter indstillinger og cachede billeder/videoer.',
    photoframe_reset_device_queued: 'Nulstilling sendt til enhed.',
    photoframe_reset_device_failed: 'Kunne ikke sende nulstilling.',
    photoframe_open_settings_btn: 'Indstillinger',
    photoframe_open_settings_failed: 'Kunne ikke åbne indstillinger.',
    photoframe_open_settings_waiting: 'Forbinder til rammen...',
    photoframe_open_settings_ready: 'Rammen er klar. Åbner indstillinger...',
    photoframe_open_settings_popup_blocked: 'Browseren blokerede nyt vindue. Tillad popups for at åbne indstillinger.',
    photoframe_update_state_queued: 'Venter på enhed',
    photoframe_update_state_downloading: 'Henter pakke',
    photoframe_update_state_installing: 'Installerer',
    photoframe_update_state_restarting: 'Genstarter',
    photoframe_update_state_success: 'Opdateret',
    photoframe_update_state_failed: 'Fejlet',
    photoframe_sync_state_sending: 'Sender billeder',
    photoframe_sync_state_sent: 'Billeder sendt',
    photoframe_show_token_btn: 'Vis token',
    photoframe_preview_toggle_on: 'Preview til',
    photoframe_preview_toggle_off: 'Preview fra',
    photoframe_scope_btn: 'Indhold',
    photoframe_delete_btn: 'Slet',
    photoframe_delete_confirm: 'Slet token for {name}?',
    photoframe_delete_done: 'Token slettet.',
    photoframe_delete_failed: 'Kunne ikke slette token.',
    photoframe_show_token_title: 'Vis token',
    photoframe_show_token_for: 'Token for {name}',
    photoframe_show_token_loading: 'Henter token...',
    photoframe_show_token_unavailable: 'Token kan ikke vises for denne post.',
    photoframe_show_token_failed: 'Kunne ikke hente token.',
    photoframe_show_token_close: 'Luk',
    photoframe_scope_title: 'Vælg indhold',
    photoframe_scope_target: 'Adgang for {name}',
    photoframe_scope_mode_label: 'Hvad må rammen vise?',
    photoframe_scope_mode_all: 'Alle billeder',
    photoframe_scope_mode_folders: 'Kun valgte mapper',
    photoframe_scope_mode_photos: 'Kun valgte billeder',
    photoframe_scope_folders_label: 'Mapper',
    photoframe_scope_photos_label: 'Billeder',
    photoframe_scope_search_placeholder: 'Søg i billeder eller id',
    photoframe_scope_search_btn: 'Søg',
    photoframe_scope_select_mode: 'Vælg',
    photoframe_scope_done_mode: 'Færdig',
    photoframe_scope_select_visible: 'Vælg synlige',
    photoframe_scope_unselect_visible: 'Fravælg synlige',
    photoframe_scope_selected_count: '{count} valgt',
    photoframe_scope_folder_selected: 'Valgte billeder',
    photoframe_scope_folder_all: 'Alle mapper',
    photoframe_scope_hold_hint: 'Hold på et billede for at starte valg',
    photoframe_scope_empty_folders: 'Ingen mapper fundet.',
    photoframe_scope_empty_photos: 'Ingen billeder fundet.',
    photoframe_scope_save: 'Gem',
    photoframe_scope_saved: 'Adgang gemt.',
    photoframe_scope_saved_with_video_prepare: 'Adgang gemt. Video klargøring startet for {count} videoer.',
    photoframe_scope_save_failed: 'Kunne ikke gemme adgang.',
    photoframe_scope_load_failed: 'Kunne ikke hente adgangsdata.',
    photoframe_source_setting: 'Kilde: app-indstilling',
    photoframe_source_env: 'Kilde: miljøvariabel',
    photoframe_source_file: 'Kilde: konfig-fil',
    photoframe_source_tokens: 'Kilde: tokens',
    photoframe_source_none: 'Kilde: ingen',
    photoframe_create_btn: 'Opret fotoramme',
    photoframe_create_title: 'Opret fotoramme',
    photoframe_create_intro: 'Generer et nyt token/link til en fotoramme. Det er tokenet, du indsætter på rammen.',
    photoframe_create_name_label: 'Navn',
    photoframe_create_name_placeholder: 'Fx Stue-ramme',
    photoframe_create_url_label: 'Ramme URL',
    photoframe_create_url_placeholder: 'Fx http://10.0.0.71:5001',
    photoframe_create_location_label: 'Placering (valgfri)',
    photoframe_create_location_placeholder: 'Fx Stue',
    photoframe_create_note_label: 'Note (valgfri)',
    photoframe_create_note_placeholder: 'Valgfri note',
    photoframe_create_cancel: 'Annuller',
    photoframe_create_submit: 'Generer token',
    photoframe_create_submit_loading: 'Genererer...',
    photoframe_create_result_title: 'Token genereret',
    photoframe_create_token_help: 'Gem token nu. Det kan vises igen fra kortet.',
    photoframe_create_server_label: 'Server URL',
    photoframe_create_token_label: 'Device token',
    photoframe_create_feed_label: 'Feed URL',
    photoframe_create_copy: 'Kopier',
    photoframe_create_copy_ok: 'Kopieret til udklipsholder',
    photoframe_create_copy_failed: 'Kunne ikke kopiere automatisk.',
    photoframe_create_saved_ok: 'Fotoramme oprettet.',
    photoframe_create_name_required: 'Indtast navn på fotorammen.',
    photoframe_create_url_required: 'Indtast URL til fotorammen.',
    photoframe_create_failed: 'Kunne ikke oprette fotoramme.',
    no_thumb: 'Ingen thumbnail',
    settings_title: 'Indstillinger',
    settings_sub: 'Vedligeholdelse og logs',
    maint_title: 'Vedligeholdelse',
    app_update_title: 'FjordLens update',
    app_update_branch: 'Branch',
    app_update_current: 'Installeret',
    app_update_remote: 'Nyeste',
    app_update_state: 'Status',
    app_update_auto_check: 'Automatisk tjek',
    app_update_interval: 'Interval (minutter)',
    app_update_save_settings: 'Gem',
    app_update_settings_saved: 'Update-indstillinger gemt.',
    app_update_settings_failed: 'Kunne ikke gemme update-indstillinger.',
    app_update_next_check: 'Næste tjek: {time}',
    app_update_last_check: 'Sidst tjekket: {time}',
    app_update_auto_off: 'Automatisk tjek er slået fra.',
    app_update_check: 'Tjek',
    app_update_start: 'Opdater',
    app_update_checking: 'Tjekker for update...',
    app_update_starting: 'Starter update...',
    app_update_unavailable: 'Updater er ikke tilgængelig.',
    app_update_available: 'Update klar: {current} → {remote}',
    app_update_latest: 'Allerede nyeste version.',
    app_update_running: 'Update kører...',
    app_update_reconnecting: 'Update kører. FjordLens genstarter og forbinder igen automatisk...',
    app_update_reloading: 'Update færdig. Genindlæser siden...',
    app_update_success: 'Update færdig.',
    app_update_failed: 'Update fejlede.',
    app_update_dirty: 'Repoet har lokale tracked ændringer.',
    app_update_choice_title: 'Vælg update-type',
    app_update_choice_text: 'Ryd plads først, eller kør en hurtig update uden Docker oprydning.',
    app_update_choice_cleanup: 'Ryd plads og opdater',
    app_update_choice_fast: 'Hurtig opdatering',
    app_update_choice_close: 'Luk',
    app_update_status_idle: 'Klar',
    app_update_status_available: 'Update klar',
    app_update_status_checking: 'Tjekker',
    app_update_status_running: 'Kører',
    app_update_status_success: 'Færdig',
    app_update_status_failed: 'Fejlet',
    app_update_status_unknown: 'Ukendt',
    app_update_tab_badge: 'Ny',
    ai_panel_title: 'AI',
    ai_embed_title: 'AI-embeddings',
    ai_embed_desc: 'Starter eller stopper embedding-jobbet for billeder uden embedding.',
    ai_desc_title: 'AI beskrivelser',
    ai_desc_desc: 'Finder handlinger/scener (fx personer der svømmer) til bedre søgning.',
    ai_desc_model_label: 'Model',
    ai_desc_model_light: 'Light (hurtig)',
    ai_desc_model_qwen: 'Qwen (bedre kvalitet)',
    ai_desc_external_toggle: 'Ekstern behandling',
    ai_desc_external_choose: 'Vælg ekstern behandling',
    ai_desc_external_enabled: 'Ekstern behandling aktiv',
    ai_desc_external_disabled: 'Ekstern behandling slået fra',
    ai_desc_external_saved: 'Ekstern behandling gemt',
    ai_desc_external_save_failed: 'Kunne ikke gemme ekstern behandling',
    ai_desc_external_load_failed: 'Kunne ikke hente ekstern behandling',
    ai_desc_external_no_folders: 'Ingen mapper valgt',
    ai_desc_external_pending_label: 'venter',
    ai_desc_external_described_label: 'beskrevet',
    ai_desc_external_token_copied: 'Forbindelseslink kopieret',
    ai_desc_external_modal_title: 'Ekstern AI behandling',
    ai_desc_external_modal_text: 'Vælg mapperne som en ekstern PC må hente billeder fra og analysere. Kopiér forbindelseslinket og indsæt det i Windows-programmet.',
    ai_desc_external_token_label: 'Forbindelseslink',
    ai_desc_external_rotate: 'Nyt link',
    ai_desc_external_links: 'Vis links',
    ai_desc_external_links_title: 'Eksterne forbindelseslinks',
    ai_desc_external_links_text: 'Her kan du kopiere eller fjerne forbindelseslinks til ekstern AI behandling.',
    ai_desc_external_links_empty: 'Ingen forbindelseslinks endnu.',
    ai_desc_external_links_load_failed: 'Kunne ikke hente forbindelseslinks.',
    ai_desc_external_link_delete: 'Fjern',
    ai_desc_external_link_delete_confirm: 'Fjern dette forbindelseslink? PC’er der bruger linket kan ikke længere connecte.',
    ai_desc_external_link_deleted: 'Forbindelseslink fjernet.',
    ai_desc_external_link_delete_failed: 'Kunne ikke fjerne forbindelseslink.',
    ai_desc_external_current_link: 'Aktuelt link',
    ai_desc_external_created_label: 'Oprettet',
    ai_desc_external_save: 'Gem ekstern behandling',
    btn_rerun_ai_desc: 'Genkør alle',
    ai_desc_rerun_starting: 'Genkører beskrivelser for alle...',
    ai_desc_rerun_failed: 'Kunne ikke starte genkørsel',
    ai_desc_rerun_started: 'Genkørsel startet i baggrunden',
    btn_clear_ai_desc: 'Slet AI tags og beskrivelser',
    ai_desc_clear_confirm: 'Slet alle AI tags og AI beskrivelser fra alle billeder og videoer? Dette kan ikke fortrydes.',
    ai_desc_clear_starting: 'Sletter AI tags og beskrivelser...',
    ai_desc_clear_failed: 'Kunne ikke slette AI tags og beskrivelser.',
    ai_desc_clear_done: 'AI tags og beskrivelser slettet for {count} filer.',
    hw_unload_qwen_ok: 'Qwen er aflæst fra GPU (VRAM frigivet).',
    hw_unload_qwen_err: 'Kunne ikke aflæse Qwen fra GPU.',
    ai_faces_title: 'Ansigtsindeksering',
    ai_faces_desc: 'Scanner billeder for ansigter og opdaterer persondata.',
    dns_title: 'DNS',
    dns_desc: 'Opsæt ekstern base-URL til delte links (f.eks. https://photos.mitdomæne.dk).',
    dns_duckdns_base_url: 'Ekstern base-URL',
    dns_duckdns_placeholder: 'https://photos.eksempel.dk',
    dns_save: 'Gem DNS',
    dns_saved: 'DNS-indstillinger gemt.',
    dns_load_failed: 'Kunne ikke hente DNS-indstillinger.',
    dns_save_failed: 'Kunne ikke gemme DNS-indstillinger.',
    dns_shares_title: 'Aktive delinger',
    dns_shares_desc: 'Se aktive share-links, kopiér linket igen, tilbagekald dem eller forlæng udløb.',
    dns_shares_loading: 'Indlæser delinger…',
    dns_shares_empty: 'Ingen aktive delinger.',
    dns_shares_load_failed: 'Kunne ikke hente delinger.',
    dns_shares_col_folder: 'Navn',
    dns_shares_col_access: 'Adgang',
    dns_shares_col_expires: 'Udløber',
    dns_shares_col_last_used: 'Sidst brugt',
    dns_shares_col_link: 'Link',
    dns_shares_col_actions: 'Handlinger',
    dns_shares_never: 'Aldrig',
    dns_shares_revoke: 'Tilbagekald',
    dns_shares_deactivate: 'Deaktiver',
    dns_shares_activate: 'Aktiver',
    dns_shares_extend: 'Forlæng',
    dns_shares_copy: 'Kopiér',
    dns_shares_copy_ok: 'Share-link kopieret.',
    dns_shares_copy_failed: 'Kunne ikke kopiere share-link.',
    dns_shares_link_unavailable: 'Link ikke tilgængeligt (opret nyt for gammel deling).',
    dns_shares_revoke_confirm: 'Tilbagekald dette share-link?',
    dns_shares_revoke_ok: 'Share-link tilbagekaldt.',
    dns_shares_revoke_failed: 'Kunne ikke tilbagekalde share-link.',
    dns_shares_deactivate_confirm: 'Deaktiver dette share-link?',
    dns_shares_deactivate_ok: 'Share-link deaktiveret.',
    dns_shares_activate_prompt: 'Aktivér link i antal dage (0 eller tom = aldrig):',
    dns_shares_activate_ok: 'Share-link aktiveret.',
    dns_shares_activate_failed: 'Kunne ikke aktivere share-link.',
    dns_shares_delete: 'Slet',
    dns_shares_delete_confirm: 'Slet dette share-link permanent?',
    dns_shares_delete_ok: 'Share-link slettet.',
    dns_shares_delete_failed: 'Kunne ikke slette share-link.',
    dns_shares_edit: 'Rediger',
    dns_shares_edit_title: 'Rediger deling',
    dns_shares_edit_name_label: 'Navn',
    dns_shares_edit_folders_label: 'Mapper',
    dns_shares_edit_no_folders: 'Ingen mapper fundet.',
    dns_shares_edit_expire_value: 'Gyldig i',
    dns_shares_edit_expire_unit: 'Enhed',
    dns_shares_edit_never: 'Udløber aldrig',
    dns_shares_edit_permission: 'Adgang',
    dns_shares_edit_password_toggle: 'Kodebeskyt link',
    dns_shares_edit_password_label: 'Adgangskode',
    dns_shares_edit_password_placeholder: 'Tom = behold nuværende kode',
    dns_shares_edit_require_name: 'Kræv navn ved åbning',
    dns_shares_edit_save: 'Gem ændringer',
    dns_shares_edit_saving: 'Gemmer...',
    dns_shares_edit_saved: 'Deling opdateret.',
    dns_shares_edit_failed: 'Kunne ikke opdatere deling.',
    dns_shares_edit_select_folder: 'Vælg mindst én mappe.',
    dns_shares_edit_load_folders_failed: 'Kunne ikke hente mapper til redigering.',
    dns_shares_edit_invalid_expiry: 'Ugyldig udløbsværdi.',
    dns_shares_extend_prompt: 'Forlæng med antal dage (0 eller tom = aldrig):',
    dns_shares_extend_ok: 'Share-link forlænget.',
    dns_shares_extend_failed: 'Kunne ikke forlænge share-link.',
    btn_scan_library: 'Scan bibliotek',
    btn_stop_scan: 'Stop scan',
    btn_rescan_metadata: 'Rescan metadata',
    btn_rebuild_thumbs: 'Genbyg thumbnails',
    btn_fix_missing_thumbs: 'Ret manglende thumbnails',
    btn_stop_all_processes: 'Stop alle processer',
    btn_reset_index: 'Nulstil indeks',
    btn_factory_reset: 'Fabriksnulstil',
    btn_start_ai: 'Start AI',
    btn_stop_ai: 'Stop AI',
    btn_start_ai_desc: 'Start beskrivelser',
    btn_stop_ai_desc: 'Stop beskrivelser',
    btn_force_stop_qwen: 'Afbryd Qwen',
    btn_start_faces: 'Start ansigter',
    btn_stop_faces: 'Stop ansigter',
    btn_index_faces: 'Indekser ansigter',
    status_faces_prefix: 'Ansigter',
    status_ai_prefix: 'AI',
    status_ai_desc_prefix: 'Beskrivelser',
    status_embedded_label: 'embedded',
    status_library_label: 'bibliotek',
    status_missing_label: 'mangler',
    status_faces_found_label: 'ansigter',
    status_described_label: 'beskrevet',
    status_processed_label: 'behandlet',
    status_stopped: 'stoppet',
    status_running: 'kører',
    status_stopping: 'stopper',
    status_runtime_label: 'Runtime',
    status_runtime_gpu: 'GPU',
    status_runtime_cpu: 'CPU',
    status_runtime_unknown: 'ukendt',
    status_dash: '—',
    upload_new_folder_placeholder: 'Ny mappe (fx ferie eller 2026/rejse)',
    upload_create_folder: 'Opret mappe',
    logs_label: 'Logs:',
    btn_stop: 'Stop',
    btn_start: 'Start',
    btn_clear: 'Ryd',
    mapper_current_folder: 'Aktuel mappe',
    mapper_root_folder: 'uploads (rodmappe)',
    mapper_drop_here: 'Slip filer eller mapper her for at uploade til',
    mapper_up: 'Tilbage',
    mapper_done: 'Færdig',
    mapper_edit: '⋮',
    mapper_edit_title: 'Flere indstillinger',
    mapper_done_title: 'Luk flere indstillinger',
    mapper_menu_edit: 'Vælg',
    mapper_menu_done: 'Luk redigering',
    mapper_menu_share: 'Del',
    mapper_menu_upload: 'Upload',
    mapper_menu_create: 'Opret mappe',
    mapper_menu_rename: 'Omd\u00f8b mappe',
    mapper_create_modal_title: 'Opret mappe',
    mapper_create_pending: 'Opretter...',
    mapper_rename_modal_title: 'Omd\u00f8b mappe',
    mapper_rename_action: 'Gem nyt navn',
    mapper_rename_pending: 'Omd\u00f8ber...',
    mapper_rename_placeholder: 'Nyt mappenavn',
    mapper_rename_select_one: 'V\u00e6lg pr\u00e6cis \u00e9n mappe at omd\u00f8be.',
    mapper_rename_root_block: 'Rodmappen kan ikke omd\u00f8bes.',
    mapper_rename_name_required: 'Skriv nyt mappenavn f\u00f8rst.',
    mapper_rename_same_name: 'Det nye navn skal v\u00e6re anderledes.',
    mapper_rename_failed: 'Kunne ikke omd\u00f8be mappe',
    mapper_rename_error: 'Fejl ved omd\u00f8bning af mappe.',
    mapper_rename_success: 'Mappe omd\u00f8bt',
    mapper_delete_selected: 'Slet valgte',
    mapper_download: 'Download',
    mapper_download_converted: 'Download konverterede',
    mapper_download_original: 'Download originale',
    download_status_ready: 'Download: Klar',
    download_status_preparing: 'Download: Forbereder...',
    download_status_fetching_one: 'Downloader billede...',
    download_status_zipping: 'Pakker ZIP på server...',
    download_status_receiving: 'Henter fil... {pct}%',
    download_status_done: 'Download klar',
    download_status_failed: 'Download fejlede',
    download_status_cancel_title: 'Stop download',
    download_status_cancelled: 'Download annulleret',
    download_status_already_running: 'Der kører allerede en download.',
    mapper_select_all: 'Vælg alle',
    mapper_clear_selection: 'Fjern valgte',
    mapper_cancel: 'Annuller',
    mapper_create_name_required: 'Skriv mappenavn først.',
    mapper_create_failed: 'Kunne ikke oprette mappe',
    mapper_create_error: 'Fejl ved oprettelse af mappe.',
    mapper_created_status: 'Mappe oprettet',
    mapper_select_delete_none: 'Vælg mindst én mappe at slette.',
    mapper_select_download_none: 'Vælg mindst ét billede at downloade.',
    mapper_delete_confirm: 'Slet {count} mappe(r) inkl. alt indhold? Dette kan ikke fortrydes.',
    mapper_delete_pending: 'Sletter...',
    mapper_delete_failed: 'Kunne ikke slette mapper',
    mapper_delete_error: 'Fejl ved sletning af mapper.',
    mapper_delete_success: 'Slettet {count} mappe(r) og {removed} indekserede filer.',
    mapper_share_title: 'Del mapper',
    mapper_share_generate: 'Generer link',
    mapper_share_generating: 'Genererer...',
    mapper_share_name_label: 'Navn',
    mapper_share_name_placeholder: 'F.eks. Familie sommer 2026',
    mapper_share_folder_label: 'Valgte mapper',
    mapper_share_expire_label: 'Gyldig i',
    mapper_share_expire_unit_label: 'Enhed',
    mapper_share_expire_days: 'Dage',
    mapper_share_expire_hours: 'Timer',
    mapper_share_permission_label: 'Adgang',
    mapper_share_perm_view: 'Se',
    mapper_share_perm_upload: 'Se og uploade',
    mapper_share_perm_manage: 'Se, uploade og slette',
    mapper_share_duckdns_toggle: 'Brug ekstern base-URL',
    mapper_share_duckdns_not_configured: 'Ekstern base-URL er ikke konfigureret under DNS.',
    mapper_share_password_toggle: 'Kodebeskyt link',
    mapper_share_require_name_toggle: 'Kræv navn ved åbning',
    mapper_share_password_label: 'Adgangskode',
    mapper_share_password_placeholder: 'Mindst 4 tegn',
    mapper_share_result_label: 'Share-link',
    mapper_share_copy: 'Kopiér',
    mapper_share_select_one: 'Vælg mindst én mappe først.',
    mapper_share_create_failed: 'Kunne ikke oprette share-link',
    mapper_share_created: 'Share-link oprettet.',
    mapper_share_copy_ok: 'Share-link kopieret.',
    mapper_share_copy_fail: 'Kunne ikke kopiere link automatisk.',
    profile_title: 'Profil',
    profile_close: 'Luk',
    profile_username: 'Brugernavn',
    profile_password_new_optional: 'Nyt password (valgfrit)',
    profile_password_repeat: 'Gentag nyt password',
    profile_password_repeat_placeholder: 'Gentag password',
    profile_password_unchanged_placeholder: 'Tom = uændret',
    profile_ui_lang: 'UI-sprog',
    profile_search_lang: 'Søgesprog',
    profile_theme: 'Tema',
    theme_auto: 'Auto',
    theme_light: 'Lys',
    theme_dark: 'Mørk',
    profile_save: 'Gem profil',
    profile_saved: 'Profil opdateret',
    status_errors_label: 'fejl',
    status_error_prefix: 'Fejl:',
    status_ready_scan: "Klar. Tryk 'Scan bibliotek' for at indeksere dine billeder.",
    scan_modal_title: 'Scan bibliotek',
    scan_modal_text: 'Vil du starte en fuld scanning af biblioteket nu?',
    scan_modal_close: 'Luk',
    scan_modal_cancel: 'Annuller',
    scan_modal_start: 'Start scan',
    ai_scope_title_ai: 'Start AI-embeddings',
    ai_scope_title_desc: 'Start AI beskrivelser',
    ai_scope_title_desc_model: 'Skift model for AI beskrivelser',
    ai_scope_title_faces: 'Start ansigtsindeksering',
    ai_scope_text: 'Vil du køre på alle eksisterende filer, eller kun på nye uploads fremover?',
    ai_scope_all: 'Alle eksisterende',
    ai_scope_new: 'Kun nye uploads fremover',
    ai_scope_cancel: 'Annuller',
    conversion_scope_title_heic: 'Start HEIC-konvertering',
    conversion_scope_title_raw: 'Start RAW/DNG-konvertering',
    conversion_scope_title_mov: 'Start MOV-konvertering',
    conversion_scope_text: 'Vil du konvertere alle eksisterende filer nu, eller kun nye uploads fremover?',
    conversion_scope_all: 'Alle eksisterende',
    conversion_scope_new: 'Kun nye uploads fremover',
    conversion_scope_cancel: 'Annuller',
    users_loading: 'Indlæser…',
    users_load_error: 'Kan ikke hente brugere.',
    users_panel_title: 'Brugere',
    users_add_user: 'Tilføj bruger',
    users_no_users: 'Ingen brugere',
    users_col_id: 'ID',
    users_col_username: 'Brugernavn',
    users_col_role: 'Rolle',
    users_col_language: 'Sprog (UI/Søgning)',
    users_col_2fa: '2FA',
    users_btn_folders: 'Mapper',
    users_btn_edit: 'Rediger',
    users_btn_delete: 'Slet',
    users_create_title: 'Tilføj bruger',
    users_edit_title: 'Rediger bruger',
    users_folders_title: 'Mappeadgang',
    users_folders_hint: 'Vælg mapper brugeren må se. Hvis du vælger en undermappe, vises overmapper automatisk kun som sti.',
    users_save_access: 'Gem adgang',
    users_label_username: 'Brugernavn',
    users_label_password: 'Adgangskode',
    users_label_new_password_optional: 'Nyt password (valgfrit)',
    users_label_role: 'Rolle',
    users_label_ui_language: 'UI-sprog',
    users_label_search_language: 'Søgesprog',
    users_role_user: 'Bruger',
    users_role_manager: 'Manager',
    users_role_admin: 'Admin',
    users_enable_2fa_start: 'Aktivér 2FA fra start',
    users_close: 'Luk',
    users_cancel: 'Annuller',
    users_create: 'Opret',
    users_save: 'Gem',
    users_acl_none_found: 'Ingen mapper fundet endnu.',
    users_acl_all_folders: 'Alle mapper (ingen begrænsning)',
    users_acl_selected_suffix: 'valgte mapper',
    users_acl_user_prefix: 'Bruger',
    users_status_acl_save_failed: 'Kunne ikke gemme mappeadgang:',
    users_status_acl_saved: 'Mappeadgang gemt',
    users_confirm_delete: 'Slet bruger',
    users_status_delete_failed: 'Kunne ikke slette:',
    users_status_deleted: 'Bruger slettet',
    users_status_username_required: 'Brugernavn må ikke være tomt.',
    users_status_update_failed: 'Kunne ikke gemme bruger:',
    users_status_updated: 'Bruger opdateret',
    users_status_username_password_required: 'Udfyld brugernavn og adgangskode.',
    users_status_create_failed: 'Kunne ikke oprette:',
    users_status_created: 'Bruger oprettet',
    users_login_log_title: 'Login-log',
    users_login_log_empty: 'Ingen login-forsøg endnu.',
    users_login_col_time: 'Tidspunkt',
    users_login_col_user: 'Bruger',
    users_login_col_status: 'Status',
    users_login_col_reason: 'Hændelse',
    users_login_col_ip: 'IP',
    users_login_col_country: 'Land',
    users_login_col_device: 'Enhed',
    users_login_status_ok: 'OK',
    users_login_status_fail: 'Fejl',
    users_login_unknown: 'Ukendt',
    users_select_all: 'Markér alle',
    users_clear_all: 'Fjern alle markeringer',
    mapper_tree_expand: 'Fold mappe ud',
    mapper_tree_collapse: 'Fold mappe sammen',
    upload_failed_generic: 'Upload fejlede',
    upload_mapper_only: 'Upload er kun aktiv i Mapper-sektionen.',
    person_rename_save_failed: 'Kunne ikke gemme navn',
    person_rename_merged: 'Person flettet til',
    person_name_updated: 'Navn opdateret',
    person_rename_merge_error: 'Fejl ved navngivning/merge',
    person_unknown_cannot_rename: 'Ukendte kan ikke omdøbes',
    person_rename_title: 'Navngiv / merge person',
    person_rename_new_placeholder: 'Opret ny person',
    person_rename_save: 'Gem',
    person_rename_none: 'Ingen eksisterende navne endnu',
    person_unknown: 'Ukendt',
    person_maybe_name: 'Måske {name}?',
    person_count_suffix: 'billede(r)',
    person_hidden_badge: 'Skjult',
    person_btn_accept_maybe: 'Ja',
    person_btn_rename: 'Navngiv',
    person_btn_hide: 'Skjul',
    person_btn_unhide: 'Vis',
    person_hide_confirm: 'Skjul denne person fra listen?',
    person_hide_failed: 'Kunne ikke skjule',
    person_hidden_ok: 'Person skjult',
    person_hide_error: 'Fejl ved skjul',
    person_unhide_failed: 'Kunne ikke gendanne',
    person_unhidden_ok: 'Person vist igen',
    person_unhide_error: 'Fejl ved gendannelse',
    people_match_btn: 'Match scan (ukendte → kendte)',
    people_match_running: 'Scanner…',
    people_match_failed: 'Match scan fejlede',
    people_match_done: 'Match scan færdig: {matched} matchet ud af {scanned}',
    users_panel_render_error: 'Fejl',
    twofa_loading: 'Indlæser…',
    twofa_load_failed: 'Kan ikke hente 2FA-status.',
    twofa_remember_days: 'Husk dage',
    twofa_onetime_code: 'Engangskode',
    twofa_code_placeholder: '6-cifret kode',
    twofa_disable: 'Deaktivér',
    twofa_enable: 'Aktivér',
    twofa_regen: 'Forny QR / nøgle',
    twofa_save_btn: 'Gem',
    twofa_status_label: 'Status',
    twofa_status_enabled: 'Aktiveret',
    twofa_status_disabled: 'Deaktiveret',
    twofa_error_prefix: '2FA-fejl:',
    twofa_updated: '2FA opdateret',
    scan_done_or_stopped: 'Scan færdig eller stoppet.',
    scan_stop_failed: 'Kunne ikke stoppe scan.',
    scan_stopping: 'Stopper scan...',
    scan_stop_error: 'Fejl ved stop scan.',
    scan_failed: 'Scan fejlede',
    scan_started_hint: "Scan startet... klik 'Stop scan' for at afbryde.",
    scan_error_prefix: 'Fejl under scan:',
    rescan_starting: 'Rescanner metadata for eksisterende billeder...',
    rescan_failed: 'Rescan fejlede',
    rescan_error: 'Fejl ved rescan.',
    rescan_done_prefix: 'Rescan færdig. Gennemgået',
    rethumb_starting: 'Genbygger thumbnails (kan tage lidt tid)...',
    rethumb_failed: 'Genbyg thumbnails fejlede',
    rethumb_error: 'Fejl ved genbyg thumbnails.',
    rethumb_done_prefix: 'Genbyg thumbnails færdig. Behandlet',
    stop_all_processes_confirm: 'Stop alle igangværende processer? Aktive enkeltkald stopper først ved næste sikre punkt.',
    stop_all_processes_stopping: 'Stopper alle processer...',
    stop_all_processes_done: 'Stop sendt til alle processer.',
    stop_all_processes_failed: 'Kunne ikke stoppe alle processer.',
    stop_all_processes_error: 'Fejl ved stop af processer.',
    clear_confirm: 'Nulstil indeks? Dette sletter data, thumbnails og konverterede kopier i FjordLens (ikke dine originale billeder). Fortsæt?',
    clear_starting: 'Sletter indeks og thumbnails...',
    clear_failed: 'Fejl ved nulstilling:',
    clear_unknown: 'ukendt',
    clear_error: 'Fejl ved nulstilling.',
    clear_done_prefix: 'Indeks nulstillet. Slettet',
    factory_confirm: 'Fabriksnulstil? Dette sletter alt INDHOLD: indeksering, personer/ansigter, thumbnails, konverterede kopier, uploads og midlertidige filer. Brugere og indstillinger bevares. Originale billeder røres ikke. Fortsæt?',
    factory_starting: 'Udfører fabriksnulstilling af indhold…',
    factory_failed: 'Fabriksnulstilling fejlede:',
    factory_error: 'Fejl ved fabriksnulstilling.',
    factory_done: 'Fabriksnulstilling gennemført. Indhold slettet – brugere bevaret.',
    file_picker_open_failed: 'Kunne ikke åbne filvælger.',
    ai_starting: 'Starter AI-indeksering (embeddings)...',
    ai_start_failed: 'Kunne ikke starte AI-indeksering.',
    ai_enabled_new_uploads: 'AI aktiveret for nye uploads fremover.',
    ai_started_bg: 'AI-indeksering er startet i baggrunden.',
    ai_start_error: 'Fejl ved start af AI-indeksering.',
    ai_stop_failed: 'Kunne ikke stoppe AI-indeksering.',
    ai_stopped: 'AI-indeksering stoppet.',
    ai_stop_error: 'Fejl ved stop af AI-indeksering.',
    ai_desc_starting: 'Starter AI-beskrivelser…',
    ai_desc_start_failed: 'Kunne ikke starte AI-beskrivelser.',
    ai_desc_enabled_new_uploads: 'AI-beskrivelser aktiveret for nye uploads fremover.',
    ai_desc_started_bg: 'AI-beskrivelser er startet i baggrunden.',
    ai_desc_start_error: 'Fejl ved start af AI-beskrivelser.',
    ai_desc_model_changed_new: 'Beskrivelsesmodel ændret for nye uploads fremover.',
    ai_desc_model_changed_all: 'Beskrivelsesmodel ændret. Genkører på alle eksisterende filer i baggrunden.',
    ai_desc_model_change_failed: 'Kunne ikke ændre beskrivelsesmodel.',
    ai_desc_stop_failed: 'Kunne ikke stoppe AI-beskrivelser.',
    ai_desc_stopped: 'AI-beskrivelser stoppet.',
    ai_desc_stop_error: 'Fejl ved stop af AI-beskrivelser.',
    ai_desc_force_stopping: 'Afbryder Qwen...',
    ai_desc_force_failed: 'Kunne ikke afbryde Qwen.',
    ai_desc_force_error: 'Fejl ved afbrydelse af Qwen.',
    status_model_label: 'Model',
    faces_starting: 'Starter ansigtsindeksering…',
    faces_start_failed: 'Kunne ikke starte ansigtsindeksering',
    faces_enabled_new_uploads: 'Ansigtsindeksering aktiveret for nye uploads fremover.',
    faces_started_bg: 'Ansigtsindeksering kører i baggrunden.',
    faces_start_error: 'Fejl ved start af ansigtsindeksering',
    faces_stop_failed: 'Kunne ikke stoppe ansigtsindeksering.',
    faces_stopped: 'Ansigtsindeksering stoppet.',
    faces_stop_error: 'Fejl ved stop af ansigtsindeksering.',
    date_update_failed: 'Kunne ikke opdatere dato',
    date_updated: 'Dato opdateret',
    update_error: 'Fejl ved opdatering',
    gps_update_failed: 'Kunne ikke opdatere GPS',
    gps_updated: 'GPS opdateret',
    weather_fetching: 'Henter vejr...',
    weather_fetch_failed: 'Vejret kan ikke hentes',
    weather_ready_to_fetch: 'Klar til hentning',
    weather_missing_inputs: 'Kræver GPS/by og dato',
    weather_updated: 'Vejrdata gemt',
    weather_no_rain: 'Ingen regn',
    weather_wind: 'Vind',
    similar_fetch_failed: 'Kunne ikke hente lignende',
    similar_fetch_error: 'Fejl ved hentning af lignende',
    similar_view_title: 'Lignende billeder',
    similar_view_subtitle: 'Fundet via billed-embedding',
    similar_modal_title: 'Lignende billeder',
    similar_modal_loading: 'Finder lignende billeder...',
    similar_modal_empty: 'Ingen lignende billeder fundet med nuværende metode og indstillinger.',
    similar_modal_count: 'Fundet {count} lignende billeder (grænser: pHash {phash}, dHash {dhash}, aHash {ahash}).',
    similar_modal_count_ai: 'Fundet {count} lignende billeder med AI-embedding (AI min {aiMin}%).',
    similar_modal_count_hybrid: 'Fundet {count} lignende billeder med Hash + AI (AI min {aiMin}%, grænser: pHash {phash}, dHash {dhash}, aHash {ahash}).',
    similar_source_label: 'Matcher fra',
    similar_method_label: 'Metode',
    similar_method_hash: 'Hash',
    similar_method_ai: 'AI',
    similar_method_hybrid: 'Hash + AI',
    similar_ai_min_label: 'AI min',
    similar_phash_label: 'pHash',
    similar_dhash_label: 'dHash',
    similar_ahash_label: 'aHash',
    similar_distance_find: 'Find',
    raw_meta_show: 'Vis rå metadata (JSON)',
    raw_meta_hide: 'Skjul rå metadata (JSON)',
  },
  en: {
    nav_timeline: '📅 Timeline',
    nav_favorites: '⭐ Favorites',
    nav_places: '📍 Places',
    nav_cameras: '📸 Cameras',
    nav_folders: '🗂️ Folders',
    nav_photoframe: '🖼️ Photoframe',
    nav_people: '🙂 People',
    nav_settings: '⚙️ Settings',
    profile_link: 'Profile',
    logout_link: 'Log out',
    search_placeholder: 'Search in English: beach, car, forest, camera, date, filename...',
    tab_maint: 'Maintenance',
    tab_update: 'Update',
    tab_ai: 'AI',
    tab_upload_workflow: 'Upload workflow',
    tab_file_types: 'File types',
    tab_hardware: 'Hardware',
    tab_heic: 'Conversion',
    tab_dns: 'DNS',
    tab_shared: 'Shared',
    tab_logs: 'Logs',
    tab_users: 'Users',
    tab_twofa: 'My 2FA',
    profile_open_twofa: 'Manage 2FA',
    tab_profile: 'Profile',
    tab_other: 'Other',
    upload_workflow_title: 'Upload workflow',
    upload_workflow_desc: 'Choose how upload post-processing runs.',
    upload_workflow_gentle_title: 'Gentle',
    upload_workflow_gentle_desc: 'Runs one phase at a time to keep system load low.',
    upload_workflow_aggressive_title: 'Power mode',
    upload_workflow_aggressive_desc: 'Runs phases in parallel. Faces are processed in batches of 10 files.',
    upload_workflow_extra_info: 'Thumbnail runtime: {thumb_runtime} · Face batch: {batch_size}',
    upload_workflow_save: 'Save workflow',
    upload_workflow_saved: 'Upload workflow saved.',
    upload_workflow_load_failed: 'Could not load upload workflow.',
    upload_workflow_save_failed: 'Could not save upload workflow.',
    upload_workflow_running: 'Parallel processing…',
    file_types_title: 'Upload file types',
    file_types_desc: 'Whitelist the file extensions FjordLens may receive. Unknown types upload as files without media processing.',
    file_types_add: 'Add',
    file_types_reset: 'Reset',
    file_types_save: 'Save file types',
    file_types_saved: 'File types saved.',
    file_types_load_failed: 'Could not load file types.',
    file_types_save_failed: 'Could not save file types.',
    file_types_invalid: 'Enter a file type like .png.',
    file_types_unsupported: '{ext} can be added, but will not be processed as an image or video.',
    file_types_duplicate: '{ext} is already on the list.',
    file_types_allowed_empty: 'No file types are allowed.',
    file_types_blocked_title: 'Blocked file types',
    file_types_blocked_desc: 'Default media file types that are not on the whitelist.',
    file_types_blocked_empty: 'No default media file types are blocked.',
    upload_blocked_file_types: 'Blocked file type: {types}. Only whitelisted file types are uploaded.',
    upload_proc_metadata: 'Metadata',
    upload_proc_thumbnails: 'Thumbnails',
    upload_proc_faces: 'Faces',
    upload_proc_embeddings: 'Embeddings',
    upload_proc_descriptions: 'Descriptions',
    upload_proc_off: 'Disabled',
    upload_proc_queue: 'queued: {count}',
    upload_proc_running: 'running: {count}',
    view_timeline_title: 'Timeline',
    view_timeline_sub: 'Date grouped overview (year/month)',
    view_favorites_title: 'Favorites',
    view_favorites_sub: 'Starred photos',
    view_steder_title: 'Places',
    view_steder_sub: 'Photos with location metadata',
    view_kameraer_title: 'Cameras',
    view_kameraer_sub: 'Filtered by available camera metadata',
    view_mapper_title: 'Folders',
    view_mapper_sub: 'Grouped by source folder',
    view_photoframe_title: 'Photoframe',
    view_photoframe_sub: 'Status for your photo frames',
    view_personer_title: 'People',
    view_personer_sub: '',
    view_settings_title: 'Settings',
    view_settings_sub: 'Maintenance and administration',
    sort_date_desc: 'Newest first',
    sort_date_asc: 'Oldest first',
    sort_name_asc: 'Name A-Z',
    sort_name_desc: 'Name Z-A',
    sort_size_desc: 'Largest first',
    sort_size_asc: 'Smallest first',
    stat_photos: 'Photos',
    stat_people: 'People',
    stat_favorites: 'Favorites',
    stat_selected: 'Selected',
    stat_show_hidden: 'Show hidden',
    empty_people: 'No people yet. Upload photos with faces or run face indexing.',
    empty_no_photos: 'No photos yet. Drop files to upload or scan the library.',
    empty_no_matches: "No photos match the current filters yet. Try 'Scan library'.",
    empty_mapper_tree: 'No folders yet.',
    photoframe_intro_title: 'Photoframe',
    photoframe_intro_sub: 'Overview of your photo frames and whether they are online.',
    photoframe_loading: 'Checking photo frames...',
    photoframe_refresh: 'Refresh',
    photoframe_empty_title: 'No photo frames configured yet.',
    photoframe_empty_sub: 'Generate a token with \"Create frame\", paste it on the frame, and wait for first connection.',
    photoframe_status_online: 'Online',
    photoframe_status_offline: 'Offline',
    photoframe_status_unknown: 'Unknown',
    photoframe_last_checked: 'Last checked',
    photoframe_card_endpoint: 'Endpoint',
    photoframe_card_ip: 'IP',
    photoframe_card_local_ip: 'Local IP',
    photoframe_card_token: 'Token',
    photoframe_card_scope: 'Content',
    photoframe_scope_summary_all: 'All photos',
    photoframe_scope_summary_folders: 'Folders ({count})',
    photoframe_scope_summary_photos: 'Photos ({count})',
    photoframe_card_last_seen: 'Last online',
    photoframe_card_setup: 'Setup',
    photoframe_setup_ready: 'Ready',
    photoframe_setup_pending: 'Setup needed',
    photoframe_card_feed: 'Feed',
    photoframe_card_error: 'Error',
    photoframe_card_update: 'Update',
    photoframe_card_sync: 'Sync',
    photoframe_card_version: 'Version',
    photoframe_card_video_prepare: 'Video prepare',
    photoframe_video_prepare_processing: 'Preparing videos',
    photoframe_video_prepare_pending: 'Waiting to prepare',
    photoframe_video_prepare_retrying: 'Starting prepare',
    photoframe_video_prepare_ready: 'Ready',
    photoframe_video_prepare_progress: '{ready}/{total} ready - {queued} queued - {waiting} missing',
    photoframe_video_prepare_capped: '(sample)',
    photoframe_version_latest: 'Latest',
    photoframe_version_outdated: 'Needs update',
    photoframe_version_unknown: 'Unknown',
    photoframe_update_btn: 'Update device',
    photoframe_update_upload_btn: 'Upload zip',
    photoframe_update_upload_all_btn: 'Upload zip to all',
    photoframe_update_confirm: 'Start background update for {name}?',
    photoframe_update_upload_confirm: 'Start update for {name} using zip file {file}?',
    photoframe_update_upload_all_confirm: 'Start update for all ({count}) using zip file {file}?',
    photoframe_update_queued: 'Update queued.',
    photoframe_update_upload_queued: 'Zip uploaded and update queued.',
    photoframe_update_upload_all_queued: 'Zip uploaded. {count} frames queued.',
    photoframe_update_failed: 'Could not start update.',
    photoframe_update_upload_failed: 'Could not upload update zip.',
    photoframe_update_upload_all_failed: 'Could not start update for all.',
    photoframe_update_cancel_btn: 'Stop update',
    photoframe_update_cancel_confirm: 'Stop update for {name}?',
    photoframe_update_cancel_done: 'Update stopped.',
    photoframe_update_cancel_failed: 'Could not stop update.',
    photoframe_restart_kiosk_btn: 'Restart kiosk',
    photoframe_restart_kiosk_confirm: 'Restart kiosk mode for {name}?',
    photoframe_restart_kiosk_queued: 'Kiosk restart queued for device.',
    photoframe_restart_kiosk_failed: 'Could not queue kiosk restart.',
    photoframe_reset_device_btn: 'Reset',
    photoframe_reset_device_confirm: 'Reset {name}? This deletes settings and cached photos/videos.',
    photoframe_reset_device_queued: 'Device reset queued.',
    photoframe_reset_device_failed: 'Could not queue device reset.',
    photoframe_open_settings_btn: 'Settings',
    photoframe_open_settings_failed: 'Could not open settings.',
    photoframe_open_settings_waiting: 'Connecting to the frame...',
    photoframe_open_settings_ready: 'Frame is ready. Opening settings...',
    photoframe_open_settings_popup_blocked: 'Browser blocked a new window. Allow popups to open settings.',
    photoframe_update_state_queued: 'Waiting for device',
    photoframe_update_state_downloading: 'Downloading',
    photoframe_update_state_installing: 'Installing',
    photoframe_update_state_restarting: 'Restarting',
    photoframe_update_state_success: 'Updated',
    photoframe_update_state_failed: 'Failed',
    photoframe_sync_state_sending: 'Sending photos',
    photoframe_sync_state_sent: 'Photos sent',
    photoframe_show_token_btn: 'Show token',
    photoframe_preview_toggle_on: 'Preview on',
    photoframe_preview_toggle_off: 'Preview off',
    photoframe_scope_btn: 'Content',
    photoframe_delete_btn: 'Delete',
    photoframe_delete_confirm: 'Delete token for {name}?',
    photoframe_delete_done: 'Token deleted.',
    photoframe_delete_failed: 'Could not delete token.',
    photoframe_show_token_title: 'Show token',
    photoframe_show_token_for: 'Token for {name}',
    photoframe_show_token_loading: 'Loading token...',
    photoframe_show_token_unavailable: 'Token is not available for this record.',
    photoframe_show_token_failed: 'Could not fetch token.',
    photoframe_show_token_close: 'Close',
    photoframe_scope_title: 'Choose content',
    photoframe_scope_target: 'Access for {name}',
    photoframe_scope_mode_label: 'What may this frame display?',
    photoframe_scope_mode_all: 'All photos',
    photoframe_scope_mode_folders: 'Only selected folders',
    photoframe_scope_mode_photos: 'Only selected photos',
    photoframe_scope_folders_label: 'Folders',
    photoframe_scope_photos_label: 'Photos',
    photoframe_scope_search_placeholder: 'Search photos or id',
    photoframe_scope_search_btn: 'Search',
    photoframe_scope_select_mode: 'Select',
    photoframe_scope_done_mode: 'Done',
    photoframe_scope_select_visible: 'Select visible',
    photoframe_scope_unselect_visible: 'Unselect visible',
    photoframe_scope_selected_count: '{count} selected',
    photoframe_scope_folder_selected: 'Selected photos',
    photoframe_scope_folder_all: 'All folders',
    photoframe_scope_hold_hint: 'Long-press an image to start selecting',
    photoframe_scope_empty_folders: 'No folders found.',
    photoframe_scope_empty_photos: 'No photos found.',
    photoframe_scope_save: 'Save',
    photoframe_scope_saved: 'Access saved.',
    photoframe_scope_saved_with_video_prepare: 'Access saved. Video preparation started for {count} videos.',
    photoframe_scope_save_failed: 'Could not save access.',
    photoframe_scope_load_failed: 'Could not load access data.',
    photoframe_source_setting: 'Source: app setting',
    photoframe_source_env: 'Source: environment variable',
    photoframe_source_file: 'Source: config file',
    photoframe_source_tokens: 'Source: tokens',
    photoframe_source_none: 'Source: none',
    photoframe_create_btn: 'Create frame',
    photoframe_create_title: 'Create photo frame',
    photoframe_create_intro: 'Generate a new token/link for a photo frame. This is the token you paste on the frame.',
    photoframe_create_name_label: 'Name',
    photoframe_create_name_placeholder: 'Example: Living room frame',
    photoframe_create_url_label: 'Frame URL',
    photoframe_create_url_placeholder: 'Example: http://10.0.0.71:5001',
    photoframe_create_location_label: 'Location (optional)',
    photoframe_create_location_placeholder: 'Example: Living room',
    photoframe_create_note_label: 'Note (optional)',
    photoframe_create_note_placeholder: 'Optional note',
    photoframe_create_cancel: 'Cancel',
    photoframe_create_submit: 'Generate token',
    photoframe_create_submit_loading: 'Generating...',
    photoframe_create_result_title: 'Token generated',
    photoframe_create_token_help: 'Save the token now. You can view it again from the frame card.',
    photoframe_create_server_label: 'Server URL',
    photoframe_create_token_label: 'Device token',
    photoframe_create_feed_label: 'Feed URL',
    photoframe_create_copy: 'Copy',
    photoframe_create_copy_ok: 'Copied to clipboard',
    photoframe_create_copy_failed: 'Could not copy automatically.',
    photoframe_create_saved_ok: 'Photo frame created.',
    photoframe_create_name_required: 'Enter a frame name.',
    photoframe_create_url_required: 'Enter the frame URL.',
    photoframe_create_failed: 'Could not create photo frame.',
    no_thumb: 'No thumbnail',
    settings_title: 'Settings',
    settings_sub: 'Maintenance and logs',
    maint_title: 'Maintenance',
    app_update_title: 'FjordLens update',
    app_update_branch: 'Branch',
    app_update_current: 'Installed',
    app_update_remote: 'Latest',
    app_update_state: 'Status',
    app_update_auto_check: 'Automatic check',
    app_update_interval: 'Interval (minutes)',
    app_update_save_settings: 'Save',
    app_update_settings_saved: 'Update settings saved.',
    app_update_settings_failed: 'Could not save update settings.',
    app_update_next_check: 'Next check: {time}',
    app_update_last_check: 'Last checked: {time}',
    app_update_auto_off: 'Automatic check is off.',
    app_update_check: 'Check',
    app_update_start: 'Update',
    app_update_checking: 'Checking for update...',
    app_update_starting: 'Starting update...',
    app_update_unavailable: 'Updater is not available.',
    app_update_available: 'Update ready: {current} → {remote}',
    app_update_latest: 'Already on the latest version.',
    app_update_running: 'Update is running...',
    app_update_reconnecting: 'Update is running. FjordLens is restarting and will reconnect automatically...',
    app_update_reloading: 'Update finished. Reloading the page...',
    app_update_success: 'Update finished.',
    app_update_failed: 'Update failed.',
    app_update_dirty: 'Repository has local tracked changes.',
    app_update_choice_title: 'Choose update type',
    app_update_choice_text: 'Free up space first, or run a quick update without Docker cleanup.',
    app_update_choice_cleanup: 'Free space and update',
    app_update_choice_fast: 'Quick update',
    app_update_choice_close: 'Close',
    app_update_status_idle: 'Ready',
    app_update_status_available: 'Update ready',
    app_update_status_checking: 'Checking',
    app_update_status_running: 'Running',
    app_update_status_success: 'Done',
    app_update_status_failed: 'Failed',
    app_update_status_unknown: 'Unknown',
    app_update_tab_badge: 'New',
    ai_panel_title: 'AI',
    ai_embed_title: 'AI embeddings',
    ai_embed_desc: 'Starts or stops the embeddings job for photos without embeddings.',
    ai_desc_title: 'AI descriptions',
    ai_desc_desc: 'Finds actions/scenes (for example people swimming) for better search.',
    ai_desc_model_label: 'Model',
    ai_desc_model_light: 'Light (fast)',
    ai_desc_model_qwen: 'Qwen (better quality)',
    ai_desc_external_toggle: 'External processing',
    ai_desc_external_choose: 'Choose external processing',
    ai_desc_external_enabled: 'External processing active',
    ai_desc_external_disabled: 'External processing disabled',
    ai_desc_external_saved: 'External processing saved',
    ai_desc_external_save_failed: 'Could not save external processing',
    ai_desc_external_load_failed: 'Could not load external processing',
    ai_desc_external_no_folders: 'No folders selected',
    ai_desc_external_pending_label: 'pending',
    ai_desc_external_described_label: 'described',
    ai_desc_external_token_copied: 'Connection link copied',
    ai_desc_external_modal_title: 'External AI processing',
    ai_desc_external_modal_text: 'Choose the folders an external PC may fetch images from and analyze. Copy the connection link and paste it in the Windows app.',
    ai_desc_external_token_label: 'Connection link',
    ai_desc_external_rotate: 'New link',
    ai_desc_external_links: 'Show links',
    ai_desc_external_links_title: 'External connection links',
    ai_desc_external_links_text: 'Copy or remove connection links for external AI processing here.',
    ai_desc_external_links_empty: 'No connection links yet.',
    ai_desc_external_links_load_failed: 'Could not load connection links.',
    ai_desc_external_link_delete: 'Remove',
    ai_desc_external_link_delete_confirm: 'Remove this connection link? PCs using the link will no longer be able to connect.',
    ai_desc_external_link_deleted: 'Connection link removed.',
    ai_desc_external_link_delete_failed: 'Could not remove connection link.',
    ai_desc_external_current_link: 'Current link',
    ai_desc_external_created_label: 'Created',
    ai_desc_external_save: 'Save external processing',
    btn_rerun_ai_desc: 'Rerun all',
    ai_desc_rerun_starting: 'Rerunning descriptions for all...',
    ai_desc_rerun_failed: 'Failed to start rerun',
    ai_desc_rerun_started: 'Rerun started in background',
    btn_clear_ai_desc: 'Delete AI tags and descriptions',
    ai_desc_clear_confirm: 'Delete all AI tags and AI descriptions from all photos and videos? This cannot be undone.',
    ai_desc_clear_starting: 'Deleting AI tags and descriptions...',
    ai_desc_clear_failed: 'Could not delete AI tags and descriptions.',
    ai_desc_clear_done: 'AI tags and descriptions deleted for {count} files.',
    hw_unload_qwen_ok: 'Qwen unloaded from GPU (VRAM freed).',
    hw_unload_qwen_err: 'Failed to unload Qwen from GPU.',
    ai_faces_title: 'Face indexing',
    ai_faces_desc: 'Scans photos for faces and updates people data.',
    dns_title: 'DNS',
    dns_desc: 'Configure external base URL for shared links (e.g. https://photos.example.com).',
    dns_duckdns_base_url: 'External base URL',
    dns_duckdns_placeholder: 'https://photos.example.com',
    dns_save: 'Save DNS',
    dns_saved: 'DNS settings saved.',
    dns_load_failed: 'Could not load DNS settings.',
    dns_save_failed: 'Could not save DNS settings.',
    dns_shares_title: 'Active shares',
    dns_shares_desc: 'View active share links, copy links again, revoke them, or extend expiry.',
    dns_shares_loading: 'Loading shares…',
    dns_shares_empty: 'No active shares.',
    dns_shares_load_failed: 'Could not load shares.',
    dns_shares_col_folder: 'Name',
    dns_shares_col_access: 'Access',
    dns_shares_col_expires: 'Expires',
    dns_shares_col_last_used: 'Last used',
    dns_shares_col_link: 'Link',
    dns_shares_col_actions: 'Actions',
    dns_shares_never: 'Never',
    dns_shares_revoke: 'Revoke',
    dns_shares_deactivate: 'Deactivate',
    dns_shares_activate: 'Activate',
    dns_shares_extend: 'Extend',
    dns_shares_copy: 'Copy',
    dns_shares_copy_ok: 'Share link copied.',
    dns_shares_copy_failed: 'Could not copy share link.',
    dns_shares_link_unavailable: 'Link unavailable (recreate share for older entry).',
    dns_shares_revoke_confirm: 'Revoke this share link?',
    dns_shares_revoke_ok: 'Share link revoked.',
    dns_shares_revoke_failed: 'Could not revoke share link.',
    dns_shares_deactivate_confirm: 'Deactivate this share link?',
    dns_shares_deactivate_ok: 'Share link deactivated.',
    dns_shares_activate_prompt: 'Activate link for number of days (0 or empty = never):',
    dns_shares_activate_ok: 'Share link activated.',
    dns_shares_activate_failed: 'Could not activate share link.',
    dns_shares_delete: 'Delete',
    dns_shares_delete_confirm: 'Delete this share link permanently?',
    dns_shares_delete_ok: 'Share link deleted.',
    dns_shares_delete_failed: 'Could not delete share link.',
    dns_shares_edit: 'Edit',
    dns_shares_edit_title: 'Edit share',
    dns_shares_edit_name_label: 'Name',
    dns_shares_edit_folders_label: 'Folders',
    dns_shares_edit_no_folders: 'No folders found.',
    dns_shares_edit_expire_value: 'Valid for',
    dns_shares_edit_expire_unit: 'Unit',
    dns_shares_edit_never: 'Never expires',
    dns_shares_edit_permission: 'Access',
    dns_shares_edit_password_toggle: 'Protect link with password',
    dns_shares_edit_password_label: 'Password',
    dns_shares_edit_password_placeholder: 'Empty = keep current password',
    dns_shares_edit_require_name: 'Require visitor name',
    dns_shares_edit_save: 'Save changes',
    dns_shares_edit_saving: 'Saving...',
    dns_shares_edit_saved: 'Share updated.',
    dns_shares_edit_failed: 'Could not update share.',
    dns_shares_edit_select_folder: 'Select at least one folder.',
    dns_shares_edit_load_folders_failed: 'Could not load folders for editing.',
    dns_shares_edit_invalid_expiry: 'Invalid expiry value.',
    dns_shares_extend_prompt: 'Extend by number of days (0 or empty = never):',
    dns_shares_extend_ok: 'Share link extended.',
    dns_shares_extend_failed: 'Could not extend share link.',
    btn_scan_library: 'Scan library',
    btn_stop_scan: 'Stop scan',
    btn_rescan_metadata: 'Rescan metadata',
    btn_rebuild_thumbs: 'Rebuild thumbnails',
    btn_fix_missing_thumbs: 'Fix missing thumbnails',
    btn_stop_all_processes: 'Stop all processes',
    btn_reset_index: 'Reset index',
    btn_factory_reset: 'Factory reset',
    btn_start_ai: 'Start AI',
    btn_stop_ai: 'Stop AI',
    btn_start_ai_desc: 'Start descriptions',
    btn_stop_ai_desc: 'Stop descriptions',
    btn_force_stop_qwen: 'Abort Qwen',
    btn_start_faces: 'Start faces',
    btn_stop_faces: 'Stop faces',
    btn_index_faces: 'Index faces',
    status_faces_prefix: 'Faces',
    status_ai_prefix: 'AI',
    status_ai_desc_prefix: 'Descriptions',
    status_embedded_label: 'embedded',
    status_library_label: 'library',
    status_missing_label: 'missing',
    status_faces_found_label: 'faces',
    status_described_label: 'described',
    status_processed_label: 'processed',
    status_stopped: 'stopped',
    status_running: 'running',
    status_stopping: 'stopping',
    status_runtime_label: 'Runtime',
    status_runtime_gpu: 'GPU',
    status_runtime_cpu: 'CPU',
    status_runtime_unknown: 'unknown',
    status_dash: '—',
    upload_new_folder_placeholder: 'New folder (e.g. holiday or 2026/trip)',
    upload_create_folder: 'Create folder',
    logs_label: 'Logs:',
    btn_stop: 'Stop',
    btn_start: 'Start',
    btn_clear: 'Clear',
    mapper_current_folder: 'Current folder',
    mapper_root_folder: 'uploads (root)',
    mapper_drop_here: 'Drop files or folders here to upload to',
    mapper_up: 'Back',
    mapper_done: 'Done',
    mapper_edit: '⋮',
    mapper_edit_title: 'More options',
    mapper_done_title: 'Close more options',
    mapper_menu_edit: 'Select',
    mapper_menu_done: 'Close editing',
    mapper_menu_share: 'Share',
    mapper_menu_upload: 'Upload',
    mapper_menu_create: 'Create folder',
    mapper_menu_rename: 'Rename folder',
    mapper_create_modal_title: 'Create folder',
    mapper_create_pending: 'Creating...',
    mapper_rename_modal_title: 'Rename folder',
    mapper_rename_action: 'Save new name',
    mapper_rename_pending: 'Renaming...',
    mapper_rename_placeholder: 'New folder name',
    mapper_rename_select_one: 'Select exactly one folder to rename.',
    mapper_rename_root_block: 'The root folder cannot be renamed.',
    mapper_rename_name_required: 'Enter a new folder name first.',
    mapper_rename_same_name: 'The new name must be different.',
    mapper_rename_failed: 'Could not rename folder',
    mapper_rename_error: 'Error while renaming folder.',
    mapper_rename_success: 'Folder renamed',
    mapper_delete_selected: 'Delete selected',
    mapper_download: 'Download',
    mapper_download_converted: 'Download converted',
    mapper_download_original: 'Download originals',
    download_status_ready: 'Download: Ready',
    download_status_preparing: 'Download: Preparing...',
    download_status_fetching_one: 'Downloading image...',
    download_status_zipping: 'Creating ZIP on server...',
    download_status_receiving: 'Receiving file... {pct}%',
    download_status_done: 'Download complete',
    download_status_failed: 'Download failed',
    download_status_cancel_title: 'Stop download',
    download_status_cancelled: 'Download cancelled',
    download_status_already_running: 'A download is already running.',
    mapper_select_all: 'Select all',
    mapper_clear_selection: 'Clear selection',
    mapper_cancel: 'Cancel',
    mapper_create_name_required: 'Enter a folder name first.',
    mapper_create_failed: 'Could not create folder',
    mapper_create_error: 'Error while creating folder.',
    mapper_created_status: 'Folder created',
    mapper_select_delete_none: 'Select at least one folder to delete.',
    mapper_select_download_none: 'Select at least one photo to download.',
    mapper_delete_confirm: 'Delete {count} folder(s) including all content? This cannot be undone.',
    mapper_delete_pending: 'Deleting...',
    mapper_delete_failed: 'Could not delete folders',
    mapper_delete_error: 'Error while deleting folders.',
    mapper_delete_success: 'Deleted {count} folder(s) and {removed} indexed files.',
    mapper_share_title: 'Share folders',
    mapper_share_generate: 'Generate link',
    mapper_share_generating: 'Generating...',
    mapper_share_name_label: 'Name',
    mapper_share_name_placeholder: 'For example Family Summer 2026',
    mapper_share_folder_label: 'Selected folders',
    mapper_share_expire_label: 'Valid for',
    mapper_share_expire_unit_label: 'Unit',
    mapper_share_expire_days: 'Days',
    mapper_share_expire_hours: 'Hours',
    mapper_share_permission_label: 'Access',
    mapper_share_perm_view: 'View',
    mapper_share_perm_upload: 'View and upload',
    mapper_share_perm_manage: 'View, upload and delete',
    mapper_share_duckdns_toggle: 'Use DuckDNS link',
    mapper_share_duckdns_not_configured: 'DuckDNS is not configured in the DNS tab.',
    mapper_share_password_toggle: 'Protect link with password',
    mapper_share_require_name_toggle: 'Require visitor name',
    mapper_share_password_label: 'Password',
    mapper_share_password_placeholder: 'At least 4 characters',
    mapper_share_result_label: 'Share link',
    mapper_share_copy: 'Copy',
    mapper_share_select_one: 'Select at least one folder first.',
    mapper_share_create_failed: 'Could not create share link',
    mapper_share_created: 'Share link created.',
    mapper_share_copy_ok: 'Share link copied.',
    mapper_share_copy_fail: 'Could not copy link automatically.',
    profile_title: 'Profile',
    profile_close: 'Close',
    profile_username: 'Username',
    profile_password_new_optional: 'New password (optional)',
    profile_password_repeat: 'Repeat new password',
    profile_password_repeat_placeholder: 'Repeat password',
    profile_password_unchanged_placeholder: 'Empty = unchanged',
    profile_ui_lang: 'UI language',
    profile_search_lang: 'Search language',
    profile_theme: 'Theme',
    theme_auto: 'Auto',
    theme_light: 'Light',
    theme_dark: 'Dark',
    profile_save: 'Save profile',
    profile_saved: 'Profile updated',
    status_errors_label: 'failures',
    status_error_prefix: 'Error:',
    status_ready_scan: "Ready. Press 'Scan library' to index your photos.",
    scan_modal_title: 'Scan library',
    scan_modal_text: 'Do you want to start a full library scan now?',
    scan_modal_close: 'Close',
    scan_modal_cancel: 'Cancel',
    scan_modal_start: 'Start scan',
    ai_scope_title_ai: 'Start AI embeddings',
    ai_scope_title_desc: 'Start AI descriptions',
    ai_scope_title_desc_model: 'Change AI description model',
    ai_scope_title_faces: 'Start face indexing',
    ai_scope_text: 'Do you want to run on all existing files, or only on new uploads from now on?',
    ai_scope_all: 'All existing',
    ai_scope_new: 'Only new uploads from now on',
    ai_scope_cancel: 'Cancel',
    conversion_scope_title_heic: 'Start HEIC conversion',
    conversion_scope_title_raw: 'Start RAW/DNG conversion',
    conversion_scope_title_mov: 'Start MOV conversion',
    conversion_scope_text: 'Do you want to convert all existing files now, or only new uploads from now on?',
    conversion_scope_all: 'All existing',
    conversion_scope_new: 'Only new uploads from now on',
    conversion_scope_cancel: 'Cancel',
    users_loading: 'Loading…',
    users_load_error: 'Could not load users.',
    users_panel_title: 'Users',
    users_add_user: 'Add user',
    users_no_users: 'No users',
    users_col_id: 'ID',
    users_col_username: 'Username',
    users_col_role: 'Role',
    users_col_language: 'Language (UI/Search)',
    users_col_2fa: '2FA',
    users_btn_folders: 'Folders',
    users_btn_edit: 'Edit',
    users_btn_delete: 'Delete',
    users_create_title: 'Add user',
    users_edit_title: 'Edit user',
    users_folders_title: 'Folder access',
    users_folders_hint: 'Select folders the user can access. If you select a subfolder, parent folders are shown only as path containers.',
    users_save_access: 'Save access',
    users_label_username: 'Username',
    users_label_password: 'Password',
    users_label_new_password_optional: 'New password (optional)',
    users_label_role: 'Role',
    users_label_ui_language: 'UI language',
    users_label_search_language: 'Search language',
    users_role_user: 'User',
    users_role_manager: 'Manager',
    users_role_admin: 'Admin',
    users_enable_2fa_start: 'Enable 2FA on creation',
    users_close: 'Close',
    users_cancel: 'Cancel',
    users_create: 'Create',
    users_save: 'Save',
    users_acl_none_found: 'No folders found yet.',
    users_acl_all_folders: 'All folders (no restriction)',
    users_acl_selected_suffix: 'selected folders',
    users_acl_user_prefix: 'User',
    users_status_acl_save_failed: 'Could not save folder access:',
    users_status_acl_saved: 'Folder access saved',
    users_confirm_delete: 'Delete user',
    users_status_delete_failed: 'Could not delete:',
    users_status_deleted: 'User deleted',
    users_status_username_required: 'Username cannot be empty.',
    users_status_update_failed: 'Could not save user:',
    users_status_updated: 'User updated',
    users_status_username_password_required: 'Fill in username and password.',
    users_status_create_failed: 'Could not create:',
    users_status_created: 'User created',
    users_login_log_title: 'Login log',
    users_login_log_empty: 'No login attempts yet.',
    users_login_col_time: 'Time',
    users_login_col_user: 'User',
    users_login_col_status: 'Status',
    users_login_col_reason: 'Event',
    users_login_col_ip: 'IP',
    users_login_col_country: 'Country',
    users_login_col_device: 'Device',
    users_login_status_ok: 'OK',
    users_login_status_fail: 'Failed',
    users_login_unknown: 'Unknown',
    users_select_all: 'Select all',
    users_clear_all: 'Clear all selections',
    mapper_tree_expand: 'Expand folder',
    mapper_tree_collapse: 'Collapse folder',
    upload_failed_generic: 'Upload failed',
    upload_mapper_only: 'Upload is only active in the Folders section.',
    person_rename_save_failed: 'Could not save name',
    person_rename_merged: 'Person merged to',
    person_name_updated: 'Name updated',
    person_rename_merge_error: 'Error while renaming/merging',
    person_unknown_cannot_rename: 'Unknown people cannot be renamed',
    person_rename_title: 'Rename / merge person',
    person_rename_new_placeholder: 'Create new person',
    person_rename_save: 'Save',
    person_rename_none: 'No existing names yet',
    person_unknown: 'Unknown',
    person_maybe_name: 'Maybe {name}?',
    person_count_suffix: 'photo(s)',
    person_hidden_badge: 'Hidden',
    person_btn_accept_maybe: 'Yes',
    person_btn_rename: 'Rename',
    person_btn_hide: 'Hide',
    person_btn_unhide: 'Show',
    person_hide_confirm: 'Hide this person from the list?',
    person_hide_failed: 'Could not hide',
    person_hidden_ok: 'Person hidden',
    person_hide_error: 'Error while hiding',
    person_unhide_failed: 'Could not restore',
    person_unhidden_ok: 'Person shown again',
    person_unhide_error: 'Error while restoring',
    people_match_btn: 'Match scan (unknown → known)',
    people_match_running: 'Scanning…',
    people_match_failed: 'Match scan failed',
    people_match_done: 'Match scan done: {matched} matched of {scanned}',
    users_panel_render_error: 'Error',
    twofa_loading: 'Loading…',
    twofa_load_failed: 'Could not load 2FA status.',
    twofa_remember_days: 'Remember days',
    twofa_onetime_code: 'One-time code',
    twofa_code_placeholder: '6-digit code',
    twofa_disable: 'Disable',
    twofa_enable: 'Enable',
    twofa_regen: 'Renew QR / key',
    twofa_save_btn: 'Save',
    twofa_status_label: 'Status',
    twofa_status_enabled: 'Enabled',
    twofa_status_disabled: 'Disabled',
    twofa_error_prefix: '2FA error:',
    twofa_updated: '2FA updated',
    scan_done_or_stopped: 'Scan finished or stopped.',
    scan_stop_failed: 'Could not stop scan.',
    scan_stopping: 'Stopping scan...',
    scan_stop_error: 'Error while stopping scan.',
    scan_failed: 'Scan failed',
    scan_started_hint: "Scan started... click 'Stop scan' to cancel.",
    scan_error_prefix: 'Scan error:',
    rescan_starting: 'Rescanning metadata for existing photos...',
    rescan_failed: 'Rescan failed',
    rescan_error: 'Error while rescanning.',
    rescan_done_prefix: 'Rescan completed. Scanned',
    rethumb_starting: 'Rebuilding thumbnails (may take a while)...',
    rethumb_failed: 'Rebuild thumbnails failed',
    rethumb_error: 'Error while rebuilding thumbnails.',
    rethumb_done_prefix: 'Thumbnail rebuild completed. Processed',
    stop_all_processes_confirm: 'Stop all running processes? Active single calls stop at the next safe point.',
    stop_all_processes_stopping: 'Stopping all processes...',
    stop_all_processes_done: 'Stop sent to all processes.',
    stop_all_processes_failed: 'Could not stop all processes.',
    stop_all_processes_error: 'Error while stopping processes.',
    clear_confirm: 'Reset index? This deletes FjordLens data, thumbnails and converted copies (not your original photos). Continue?',
    clear_starting: 'Deleting index and thumbnails...',
    clear_failed: 'Reset failed:',
    clear_unknown: 'unknown',
    clear_error: 'Error while resetting index.',
    clear_done_prefix: 'Index reset. Removed',
    factory_confirm: 'Factory reset? This deletes all CONTENT: indexing, people/faces, thumbnails, converted copies, uploads and temp files. Users and settings are kept. Original photos are not touched. Continue?',
    factory_starting: 'Performing content-only factory reset…',
    factory_failed: 'Factory reset failed:',
    factory_error: 'Error during factory reset.',
    factory_done: 'Factory reset complete. Content cleared; users kept.',
    file_picker_open_failed: 'Could not open file picker.',
    ai_starting: 'Starting AI indexing (embeddings)...',
    ai_start_failed: 'Could not start AI indexing.',
    ai_enabled_new_uploads: 'AI enabled for new uploads from now on.',
    ai_started_bg: 'AI indexing started in the background.',
    ai_start_error: 'Error while starting AI indexing.',
    ai_stop_failed: 'Could not stop AI indexing.',
    ai_stopped: 'AI indexing stopped.',
    ai_stop_error: 'Error while stopping AI indexing.',
    ai_desc_starting: 'Starting AI descriptions…',
    ai_desc_start_failed: 'Could not start AI descriptions.',
    ai_desc_enabled_new_uploads: 'AI descriptions enabled for new uploads from now on.',
    ai_desc_started_bg: 'AI descriptions started in the background.',
    ai_desc_start_error: 'Error while starting AI descriptions.',
    ai_desc_model_changed_new: 'Description model changed for new uploads from now on.',
    ai_desc_model_changed_all: 'Description model changed. Reprocessing all existing files in the background.',
    ai_desc_model_change_failed: 'Could not change description model.',
    ai_desc_stop_failed: 'Could not stop AI descriptions.',
    ai_desc_stopped: 'AI descriptions stopped.',
    ai_desc_stop_error: 'Error while stopping AI descriptions.',
    ai_desc_force_stopping: 'Aborting Qwen...',
    ai_desc_force_failed: 'Could not abort Qwen.',
    ai_desc_force_error: 'Error while aborting Qwen.',
    status_model_label: 'Model',
    faces_starting: 'Starting face indexing…',
    faces_start_failed: 'Could not start face indexing',
    faces_enabled_new_uploads: 'Face indexing enabled for new uploads from now on.',
    faces_started_bg: 'Face indexing is running in the background.',
    faces_start_error: 'Error while starting face indexing',
    faces_stop_failed: 'Could not stop face indexing.',
    faces_stopped: 'Face indexing stopped.',
    faces_stop_error: 'Error while stopping face indexing.',
    date_update_failed: 'Could not update date',
    date_updated: 'Date updated',
    update_error: 'Update error',
    gps_update_failed: 'Could not update GPS',
    gps_updated: 'GPS updated',
    weather_fetching: 'Fetching weather...',
    weather_fetch_failed: 'Weather could not be fetched',
    weather_ready_to_fetch: 'Ready to fetch',
    weather_missing_inputs: 'Requires GPS/city and date',
    weather_updated: 'Weather saved',
    weather_no_rain: 'No rain',
    weather_wind: 'Wind',
    similar_fetch_failed: 'Could not load similar photos',
    similar_fetch_error: 'Error while loading similar photos',
    similar_view_title: 'Similar photos',
    similar_view_subtitle: 'Found via image embedding',
    similar_modal_title: 'Similar photos',
    similar_modal_loading: 'Finding similar photos...',
    similar_modal_empty: 'No similar photos found with the current method and settings.',
    similar_modal_count: 'Found {count} similar photos (limits: pHash {phash}, dHash {dhash}, aHash {ahash}).',
    similar_modal_count_ai: 'Found {count} similar photos with AI embeddings (AI min {aiMin}%).',
    similar_modal_count_hybrid: 'Found {count} similar photos with Hash + AI (AI min {aiMin}%, limits: pHash {phash}, dHash {dhash}, aHash {ahash}).',
    similar_source_label: 'Matching from',
    similar_method_label: 'Method',
    similar_method_hash: 'Hash',
    similar_method_ai: 'AI',
    similar_method_hybrid: 'Hash + AI',
    similar_ai_min_label: 'AI min',
    similar_phash_label: 'pHash',
    similar_dhash_label: 'dHash',
    similar_ahash_label: 'aHash',
    similar_distance_find: 'Find',
    raw_meta_show: 'Show raw metadata (JSON)',
    raw_meta_hide: 'Hide raw metadata (JSON)',
  },
};

const APP_VIEW_KEYS = new Set(['timeline', 'favorites', 'steder', 'kameraer', 'mapper', 'photoframe', 'personer', 'settings']);
const SETTINGS_TAB_KEYS = new Set(['maint', 'update', 'ai', 'upload_workflow', 'file_types', 'hardware', 'dns', 'heic', 'shared', 'logs', 'users', 'profile', 'other']);

function _normalizeSettingsTab(tab) {
  const raw = String(tab || '').trim().toLowerCase();
  if (!raw) return '';
  return SETTINGS_TAB_KEYS.has(raw) ? raw : '';
}

function resolveUiLanguage(lang) {
  return UI_LANGUAGES.has(lang) ? lang : 'da';
}

// --- Utilities: dynamic script loader (for MapLibre) ---
let _maplibrePromise = null;
function loadScriptOnce(url){
  return new Promise((resolve, reject)=>{
    try {
      const prev = Array.from(document.getElementsByTagName('script')).some(s=> s && s.src === url);
      if (prev) { resolve(true); return; }
      const el = document.createElement('script');
      el.src = url; el.async = true; el.defer = true; el.crossOrigin = 'anonymous';
      el.onload = ()=> resolve(true);
      el.onerror = ()=> reject(new Error('Script load failed: '+url));
      document.head.appendChild(el);
    } catch (e){ reject(e); }
  });
}
async function ensureMaplibre(){
  if (typeof window.maplibregl !== 'undefined') return true;
  if (!_maplibrePromise){
    _maplibrePromise = loadScriptOnce('https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js')
      .catch(()=> false);
  }
  try { const ok = await _maplibrePromise; return !!(ok && window.maplibregl); } catch { return false; }
}

function tr(key) {
  const lang = resolveUiLanguage(state.uiLanguage || 'da');
  const dict = I18N[lang] || I18N.da;
  if (Object.prototype.hasOwnProperty.call(dict, key)) return dict[key];
  if (Object.prototype.hasOwnProperty.call(I18N.da, key)) return I18N.da[key];
  return key;
}

function normalizeAiDescribeModel(value) {
  const raw = String(value || '').trim().toLowerCase();
  if (raw === 'qwen' || raw === 'qwen-vl' || raw === 'qwen_vl' || raw === 'qwen2.5-vl' || raw === 'qwen2_5_vl') {
    return 'qwen';
  }
  return 'light';
}

function updateAiDescribeModelSelect() {
  if (!els.aiDescribeModelSelect) return;
  const current = normalizeAiDescribeModel(state.aiDescribeModel || 'light');
  els.aiDescribeModelSelect.value = current;
}

function updateAiToggleButton() {
  if (!els.aiIngestToggle) return;
  const enabled = !!state.aiAutoEnabled || !!state.aiRunning;
  els.aiIngestToggle.checked = enabled;
  if (els.aiIngestToggleText) {
    els.aiIngestToggleText.textContent = enabled ? tr('btn_stop_ai') : tr('btn_start_ai');
  }
  updateSimilarMethodAvailability();
}

function updateAiDescribeToggleButton() {
  const externalEnabled = !!state.aiDescExternalEnabled;
  if (els.aiDescribeLocalControls) els.aiDescribeLocalControls.classList.toggle('hidden', externalEnabled);
  if (els.aiDescribeModelRow) els.aiDescribeModelRow.classList.toggle('hidden', externalEnabled);
  if (els.aiDescExternalToggle) els.aiDescExternalToggle.checked = externalEnabled;
  if (els.aiDescExternalToggleText) els.aiDescExternalToggleText.textContent = tr('ai_desc_external_toggle');
  if (els.aiDescExternalChooseBtn) {
    els.aiDescExternalChooseBtn.classList.toggle('hidden', !externalEnabled);
    els.aiDescExternalChooseBtn.textContent = tr('ai_desc_external_choose');
  }
  if (els.aiDescExternalInfo) {
    els.aiDescExternalInfo.classList.toggle('hidden', !externalEnabled);
    if (externalEnabled) {
      const folders = Array.isArray(state.aiDescExternalFolders) ? state.aiDescExternalFolders.length : 0;
      const pending = Number(state.aiDescExternalPending || 0);
      const described = Number(state.aiDescExternalDescribed || 0);
      const total = Number(state.aiDescExternalTotal || 0);
      const folderText = folders ? `${folders} mapper` : tr('ai_desc_external_no_folders');
      els.aiDescExternalInfo.textContent = `${tr('ai_desc_external_enabled')} · ${folderText} · ${tr('ai_desc_external_pending_label')} ${pending} · ${tr('ai_desc_external_described_label')} ${described}/${total}`;
    }
  }
  if (!els.aiDescribeToggle) return;
  if (externalEnabled) {
    els.aiDescribeToggle.checked = false;
    els.aiDescribeToggle.disabled = true;
  } else {
    els.aiDescribeToggle.disabled = false;
  }
  const enabled = !!state.aiDescribeAutoEnabled || !!state.aiDescribeRunning;
  if (!externalEnabled) els.aiDescribeToggle.checked = enabled;
  if (els.aiDescribeToggleText) {
    els.aiDescribeToggleText.textContent = enabled ? tr('btn_stop_ai_desc') : tr('btn_start_ai_desc');
  }
  if (els.aiDescribeForceStopBtn) {
    const showForce = !externalEnabled && !!state.aiDescribeRunning && normalizeAiDescribeModel(state.aiDescribeModel) === 'qwen';
    els.aiDescribeForceStopBtn.classList.toggle('hidden', !showForce);
    els.aiDescribeForceStopBtn.disabled = !showForce || !!state.aiDescribeForceStopPending;
  }
  if (els.aiDescribeRerunBtn) {
    els.aiDescribeRerunBtn.textContent = tr('btn_rerun_ai_desc');
    els.aiDescribeRerunBtn.disabled = externalEnabled || !!state.aiDescribeRunning || !!state.aiDescribeStopping;
  }
  if (els.aiDescribeClearBtn) {
    els.aiDescribeClearBtn.textContent = tr('btn_clear_ai_desc');
    els.aiDescribeClearBtn.disabled = !!state.aiDescribeRunning || !!state.aiDescribeStopping;
  }
}

function updateFacesToggleButton() {
  if (!els.facesToggle) return;
  const enabled = !!state.facesAutoEnabled || !!state.facesRunning;
  els.facesToggle.checked = enabled;
  if (els.facesToggleText) {
    els.facesToggleText.textContent = enabled ? tr('btn_stop_faces') : tr('btn_start_faces');
  }
}

function formatRuntimeDevice(value) {
  const raw = String(value || '').trim().toLowerCase();
  if (!raw || raw === 'unknown') return tr('status_runtime_unknown');
  if (raw === 'external') return tr('ai_desc_external_toggle');
  if (raw === 'gpu' || raw === 'cuda' || raw.startsWith('cuda')) return tr('status_runtime_gpu');
  if (raw === 'cpu') return tr('status_runtime_cpu');
  return raw.toUpperCase();
}

function updateRuntimeIndicator(el, value) {
  if (!el) return;
  el.textContent = `${tr('status_runtime_label')}: ${formatRuntimeDevice(value)}`;
}

function navLabels() {
  return {
    timeline: [tr('view_timeline_title'), tr('view_timeline_sub')],
    favorites: [tr('view_favorites_title'), tr('view_favorites_sub')],
    steder: [tr('view_steder_title'), tr('view_steder_sub')],
    kameraer: [tr('view_kameraer_title'), tr('view_kameraer_sub')],
    // Remove subtitle for mapper view
    mapper: [tr('view_mapper_title'), ''],
    photoframe: [tr('view_photoframe_title'), tr('view_photoframe_sub')],
    personer: [tr('view_personer_title'), tr('view_personer_sub')],
    settings: [tr('view_settings_title'), tr('view_settings_sub')],
  };
}

let state = {
  selectedId: null,
  items: [],
  view: "timeline",
  sort: "date_desc",
  q: "",
  scanning: false,
  selectedIndex: -1,
  viewerItems: null,
  similarModalItems: [],
  similarSourceId: 0,
  similarSourceItem: null,
  similarSourceFolder: '',
  similarSourceCoverageFolder: '',
  similarSourceFolderCoverageKnown: false,
  similarSourceFolderEmbedded: 0,
  similarSourceFolderTotal: 0,
  similarSourceFolderMissing: 0,
  similarMethodTouchedInModal: false,
  similarAutoSelectAiPending: false,
  similarMethod: 'hybrid',
  similarAiMin: 88,
  similarHashDistances: { phash: 9, dhash: 12, ahash: 12 },
  folder: null,
  // logs
  // Default off; enable only for authorized users
  logsRunning: false,
  logsAfter: 0,
  // people view state
  people: [],
  _peopleCache: { key: '', items: [], ts: 0 },
  personView: { mode: 'list', personId: null, personName: null },
  showHiddenPeople: false,
  mapperPath: "",
  mapperFolders: [],
  mapperSort: "date_desc",
  settingsTab: '',
  mapperEditMode: false,
  mapperSelectedFolders: new Set(),
  mapperSelectedPhotoIds: new Set(),
  mapperFolderModalMode: "create",
  mapperRenameTargetPath: "",
  mapperTreeOpen: false,
  mapperTreeExpanded: new Set([""]),
  // Paging for large folders (timeline and mapper views)
  photosPageOffset: 0,
  photosPageLimit: 300,
  mapperPageRows: 5,
  photosHasMore: false,
  photosLoading: false,
  currentUser: {
    id: APP_PROFILE.id || null,
    username: APP_PROFILE.username || '',
    role: APP_PROFILE.role || 'user',
  },
  uiLanguage: resolveUiLanguage(APP_PROFILE.ui_language || 'da'),
  searchLanguage: resolveUiLanguage(APP_PROFILE.search_language || 'da'),
  aiRunning: false,
  aiAutoEnabled: false,
  aiCoverageEmbedded: 0,
  aiCoverageTotal: 0,
  aiCoverageMissing: 0,
  aiRuntime: 'unknown',
  aiDescribeRunning: false,
  aiDescribeStopping: false,
  aiDescribeForceStopPending: false,
  aiDescribeAutoEnabled: false,
  aiDescribeRuntime: 'unknown',
  aiDescribeModel: 'light',
  aiDescribePendingModel: null,
  aiDescExternalEnabled: false,
  aiDescExternalFolders: [],
  aiDescExternalAvailableFolders: [],
  aiDescExternalToken: '',
  aiDescExternalConnectionUrl: '',
  aiDescExternalLinks: [],
  aiDescExternalPending: 0,
  aiDescExternalDescribed: 0,
  aiDescExternalTotal: 0,
  facesRunning: false,
  facesAutoEnabled: false,
  facesRuntime: 'unknown',
  aiScopePendingFeature: null,
  conversionScopePendingType: null,
  photoframeItems: [],
  photoframeLoading: false,
  photoframeError: '',
  photoframeCheckedAt: '',
  photoframeSource: 'none',
  photoframeConfigPath: '',
  photoframeLatestVersion: '',
  photoframeLatestVersionAt: '',
  photoframePreviewHiddenById: {},
  shareDuckdnsConfigured: false,
  shareDuckdnsEffectiveBaseUrl: '',
  sharedLinks: [],
  sharedEditShareId: 0,
  sharedFolderOptions: [],
  uploadWorkflowMode: 'gentle',
  uploadWorkflowBatchSize: 10,
  uploadWorkflowThumbnailsUseGpu: false,
  uploadFileTypes: null,
  uploadFileTypesLoaded: false,
  uploadFileTypesLoading: null,
  appUpdate: null,
  appUpdateReconnectUntil: 0,
};

const PHOTOFRAME_STATUS_POLL_MS = 7000;
let photoframeStatusPollTimer = null;
const APP_UPDATE_STATUS_POLL_MS = 2500;
const APP_UPDATE_BADGE_POLL_MS = 30000;
const APP_UPDATE_RECONNECT_MAX_MS = 20 * 60 * 1000;
const APP_UPDATE_RELOAD_DELAY_MS = 1800;
const APP_UPDATE_RECONNECT_KEY = 'fjordlens.appUpdate.reconnect.v1';
let appUpdateStatusPollTimer = null;
let appUpdateBadgePollTimer = null;
let appUpdateChoiceResolver = null;
let appUpdateReloadTimer = null;

const MAPPER_TREE_UI_STATE_KEY = 'fjordlens.mapperTreeUi.v1';
const PHOTOFRAME_PREVIEW_UI_STATE_KEY = 'fjordlens.photoframePreviewHiddenById.v1';

function _loadPhotoframePreviewUiState() {
  try {
    const raw = localStorage.getItem(PHOTOFRAME_PREVIEW_UI_STATE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return;
    const clean = {};
    Object.entries(parsed).forEach(([k, v]) => {
      const id = String(k || '').trim();
      if (!id) return;
      if (v === true) clean[id] = true;
    });
    state.photoframePreviewHiddenById = clean;
  } catch {}
}

function _savePhotoframePreviewUiState() {
  try {
    const source = (state && state.photoframePreviewHiddenById && typeof state.photoframePreviewHiddenById === 'object')
      ? state.photoframePreviewHiddenById
      : {};
    const clean = {};
    Object.entries(source).forEach(([k, v]) => {
      const id = String(k || '').trim();
      if (!id) return;
      if (v === true) clean[id] = true;
    });
    localStorage.setItem(PHOTOFRAME_PREVIEW_UI_STATE_KEY, JSON.stringify(clean));
  } catch {}
}

function _loadMapperTreeUiState() {
  try {
    const raw = localStorage.getItem(MAPPER_TREE_UI_STATE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object') {
      state.mapperTreeOpen = !!parsed.open;
      const expanded = Array.isArray(parsed.expanded) ? parsed.expanded : [];
      const cleaned = expanded
        .map(v => _normalizeMapperPath(v))
        .filter(v => v === '' || !!v);
      state.mapperTreeExpanded = new Set(['', ...cleaned]);
    }
  } catch {}
}

function _saveMapperTreeUiState() {
  try {
    const expanded = Array.from(state.mapperTreeExpanded || []).map(v => _normalizeMapperPath(v));
    localStorage.setItem(MAPPER_TREE_UI_STATE_KEY, JSON.stringify({
      open: !!state.mapperTreeOpen,
      expanded: Array.from(new Set(['', ...expanded])),
    }));
  } catch {}
}

_loadMapperTreeUiState();
_loadPhotoframePreviewUiState();

function _expandMapperAncestors(path) {
  const parts = String(path || '').split('/').filter(Boolean);
  let acc = '';
  state.mapperTreeExpanded.add('');
  for (const part of parts) {
    acc = acc ? `${acc}/${part}` : part;
    state.mapperTreeExpanded.add(acc);
  }
  _saveMapperTreeUiState();
}

function _buildMapperTree(paths) {
  const nodes = new Map();
  nodes.set('', { path: '', name: 'uploads', children: new Set() });
  for (const rawPath of (paths || [])) {
    const safePath = _normalizeMapperPath(rawPath);
    if (!safePath) continue;
    const parts = safePath.split('/').filter(Boolean);
    let parent = '';
    let acc = '';
    for (const part of parts) {
      acc = acc ? `${acc}/${part}` : part;
      if (!nodes.has(acc)) nodes.set(acc, { path: acc, name: part, children: new Set() });
      if (!nodes.has(parent)) nodes.set(parent, { path: parent, name: parent || 'uploads', children: new Set() });
      nodes.get(parent).children.add(acc);
      parent = acc;
    }
  }
  return nodes;
}

function renderMapperTree() {
  if (!els.mapperTreeNav) return;
  if (state.view !== 'mapper' || !state.mapperTreeOpen) {
    if (els.mapperNavMenu) els.mapperNavMenu.classList.add('hidden');
    els.mapperTreeNav.classList.add('hidden');
    return;
  }

  if (els.mapperNavMenu) els.mapperNavMenu.classList.remove('hidden');

  const tree = _buildMapperTree(state.mapperFolders || []);
  _expandMapperAncestors(state.mapperPath || '');
  const root = tree.get('');
  const rootChildren = root ? Array.from(root.children) : [];

  els.mapperTreeNav.classList.remove('hidden');
  if (!rootChildren.length) {
    els.mapperTreeNav.innerHTML = `<div class="mini-label">${escapeHtml(tr('empty_mapper_tree'))}</div>`;
    return;
  }
  els.mapperTreeNav.innerHTML = '';

  const renderNode = (path, depth = 0) => {
    const node = tree.get(path);
    if (!node) return;

    const children = Array.from(node.children || []).sort((a, b) => {
      const an = (tree.get(a)?.name || a).toLocaleLowerCase('da-DK');
      const bn = (tree.get(b)?.name || b).toLocaleLowerCase('da-DK');
      return an.localeCompare(bn, 'da-DK');
    });
    const hasChildren = children.length > 0;
    const isExpanded = state.mapperTreeExpanded.has(path) || String(state.mapperPath || '').startsWith(path ? `${path}/` : '');

    const row = document.createElement('div');
    row.className = 'mapper-tree-item';
    row.style.paddingLeft = `${depth * 14}px`;

    const caret = document.createElement('button');
    caret.className = 'mapper-tree-caret';
    caret.type = 'button';
    caret.textContent = hasChildren ? (isExpanded ? '▾' : '▸') : '';
    caret.disabled = !hasChildren;
    if (!hasChildren) caret.style.visibility = 'hidden';
    if (hasChildren) {
      caret.title = isExpanded ? tr('mapper_tree_collapse') : tr('mapper_tree_expand');
      caret.setAttribute('aria-label', isExpanded ? tr('mapper_tree_collapse') : tr('mapper_tree_expand'));
      caret.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (state.mapperTreeExpanded.has(path)) state.mapperTreeExpanded.delete(path);
        else state.mapperTreeExpanded.add(path);
        _saveMapperTreeUiState();
        renderMapperTree();
      });
    }
    row.appendChild(caret);

    const link = document.createElement('button');
    link.className = 'mapper-tree-link' + (String(state.mapperPath || '') === path ? ' active' : '');
    link.type = 'button';
    link.textContent = node.name;
    link.addEventListener('click', async () => {
      state.mapperPath = path;
      state.folder = path || null;
      _expandMapperAncestors(path);
      renderMapperContext(path);
      await loadMapperTools(path);
      await loadPhotos();
    });
    row.appendChild(link);
    els.mapperTreeNav.appendChild(row);

    if (hasChildren && isExpanded) {
      for (const ch of children) renderNode(ch, depth + 1);
    }
  };

  for (const ch of rootChildren.sort((a, b) => {
    const an = (tree.get(a)?.name || a).toLocaleLowerCase('da-DK');
    const bn = (tree.get(b)?.name || b).toLocaleLowerCase('da-DK');
    return an.localeCompare(bn, 'da-DK');
  })) {
    renderNode(ch, 0);
  }
}

function _normalizeMapperPath(path) {
  const raw = String(path || '').replace(/\\/g, '/').trim();
  if (!raw) return '';
  const cleaned = raw
    .split('/')
    .map(s => s.trim())
    .filter(s => s && s !== '.' && s !== '..')
    .join('/');
  if (!cleaned) return '';
  if (cleaned === 'uploads') return '';
  if (cleaned.startsWith('uploads/')) return cleaned.slice('uploads/'.length);
  return cleaned;
}

function _normalizeMapperSort(sort) {
  return String(sort || '').trim().toLowerCase() === 'date_asc' ? 'date_asc' : 'date_desc';
}

function _readRouteStateFromUrl() {
  try {
    const url = new URL(window.location.href);
    const viewRaw = String(url.searchParams.get('view') || '').trim().toLowerCase();
    const view = APP_VIEW_KEYS.has(viewRaw) ? viewRaw : null;
    const mapperPath = _normalizeMapperPath(url.searchParams.get('mappe') || url.searchParams.get('folder') || '');
    const settingsTab = _normalizeSettingsTab(url.searchParams.get('tab') || url.searchParams.get('settings_tab') || '');
    return { view, mapperPath, settingsTab };
  } catch {
    return { view: null, mapperPath: '', settingsTab: '' };
  }
}

function _activeSettingsTabFromUi() {
  try {
    const activeBtn = document.querySelector('#settingsPanel .tab-btn.active');
    const tab = activeBtn ? activeBtn.getAttribute('data-tab') : '';
    return _normalizeSettingsTab(tab);
  } catch {
    return '';
  }
}

function _syncRouteStateToUrl() {
  try {
    const url = new URL(window.location.href);
    if (state.view && state.view !== 'timeline') {
      url.searchParams.set('view', state.view);
    } else {
      url.searchParams.delete('view');
    }
    if (state.view === 'mapper' && state.mapperPath) {
      url.searchParams.set('mappe', state.mapperPath);
    } else {
      url.searchParams.delete('mappe');
      url.searchParams.delete('folder');
    }
    if (state.view === 'settings') {
      const activeSettingsTab = _activeSettingsTabFromUi() || _normalizeSettingsTab(state.settingsTab);
      if (activeSettingsTab) {
        state.settingsTab = activeSettingsTab;
        url.searchParams.set('tab', activeSettingsTab);
      } else {
        url.searchParams.delete('tab');
      }
    } else {
      url.searchParams.delete('tab');
      url.searchParams.delete('settings_tab');
    }
    const next = `${url.pathname}${url.search}${url.hash}`;
    const cur = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    if (next !== cur) {
      window.history.replaceState({ view: state.view, mappe: state.mapperPath || '', tab: state.settingsTab || '' }, '', next);
    }
  } catch {}
}

// mark initial view for CSS targeting
document.body.classList.add("view-timeline");

// Map state for "Steder"
let placesMap = null;
let placesSourceReady = false;
const weatherFetches = new Set();

function showStatus(text, type = "ok") {
  els.status.textContent = text;
  els.status.classList.remove("hidden", "ok", "err");
  els.status.classList.add(type);
}
function hideStatus() {
  els.status.classList.add("hidden");
}

function fmtBytes(bytes) {
  if (bytes == null) return "-";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let val = Number(bytes);
  let idx = 0;
  while (val >= 1024 && idx < units.length - 1) {
    val /= 1024;
    idx++;
  }
  return `${val.toFixed(val >= 10 || idx === 0 ? 0 : 1)} ${units[idx]}`;
}

function fmtDims(w, h) {
  if (!w || !h) return "-";
  return `${w} × ${h}`;
}

function escapeHtml(s) {
  if (s === null || s === undefined) return '';
  return String(s).replace(/[&<>"'`]/g, (ch) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
    '`': '&#96;'
  })[ch]);
}

function fmtDate(s) {
  if (!s) return "-";
  try {
    const locale = (state.uiLanguage === 'en') ? 'en-GB' : 'da-DK';
    return new Date(s).toLocaleString(locale);
  } catch {
    return s;
  }
}

function _pad2(n) {
  return String(Number(n) || 0).padStart(2, '0');
}

function fmtDateParts(s) {
  if (!s) return { date: '-', time: '-' };
  try {
    const d = new Date(s);
    if (Number.isNaN(d.getTime())) return { date: '-', time: '-' };
    const date = `${_pad2(d.getDate())}-${_pad2(d.getMonth() + 1)}-${d.getFullYear()}`;
    const time = `${_pad2(d.getHours())}:${_pad2(d.getMinutes())}:${_pad2(d.getSeconds())}`;
    return { date, time };
  } catch {
    return { date: '-', time: '-' };
  }
}

function _repairMojibakeText(value) {
  const txt = String(value || '');
  if (!/[ÃÂ]/.test(txt) || typeof TextDecoder === 'undefined') return txt;
  try {
    const bytes = Uint8Array.from(Array.from(txt).map((ch) => ch.charCodeAt(0) & 255));
    const fixed = new TextDecoder('utf-8').decode(bytes);
    return fixed || txt;
  } catch {
    return txt;
  }
}

function _splitTagParts(value) {
  return _repairMojibakeText(value).split(/[,;|]|\s+[–—-]\s+/g);
}

function _cleanUiTag(value) {
  return _repairMojibakeText(value)
    .trim()
    .toLowerCase()
    .replace(/^[\s"'`\[\]{}()]+|[\s"'`\[\]{}()]+$/g, '')
    .replace(/\s+/g, ' ');
}

function _normalizeTagList(raw) {
  const addParts = (arr, value) => {
    _splitTagParts(value).forEach((part) => {
      const tag = _cleanUiTag(part);
      if (tag && tag.length <= 40) arr.push(tag);
    });
  };
  if (Array.isArray(raw)) {
    const out = [];
    raw.forEach((v) => addParts(out, v));
    return out;
  }
  if (raw == null) return [];
  if (typeof raw === 'string') {
    const txt = raw.trim();
    if (!txt) return [];
    try {
      const parsed = JSON.parse(txt);
      if (Array.isArray(parsed)) {
        const out = [];
        parsed.forEach((v) => addParts(out, v));
        return out;
      }
    } catch {}
    const out = [];
    addParts(out, txt);
    return out;
  }
  return [];
}

function _collectItemTags(item) {
  const primary = _normalizeTagList(item && item.ai_tags);
  const secondary = _normalizeTagList(item && item.ai_desc_tags);
  const seen = new Set();
  const out = [];
  primary.concat(secondary).forEach((tag) => {
    const key = tag.normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
    if (seen.has(key)) return;
    seen.add(key);
    out.push(tag);
  });
  return out;
}

function _formatAiAnalysisText(item) {
  const caption = _repairMojibakeText(item && item.ai_desc_caption ? item.ai_desc_caption : '').trim();
  const tags = _collectItemTags(item);
  if (caption && tags.length) return `${caption} · ${tags.join(", ")}`;
  if (tags.length) return tags.join(", ");
  return caption || "-";
}

function _formatAiCaptionText(item) {
  return _repairMojibakeText(item && item.ai_desc_caption ? item.ai_desc_caption : '').trim() || "-";
}

function _formatAiTagsText(item) {
  const tags = _collectItemTags(item);
  return tags.length ? tags.join(", ") : "-";
}

function _extractFileExt(value) {
  const raw = String(value || '').trim();
  if (!raw) return '';
  const clean = raw.split('#')[0].split('?')[0];
  const leaf = clean.split('/').pop() || clean;
  const dot = leaf.lastIndexOf('.');
  if (dot < 0 || dot >= (leaf.length - 1)) return '';
  return leaf.slice(dot + 1).trim().replace(/[^a-zA-Z0-9]/g, '').toUpperCase();
}

function _getItemConversionInfo(item) {
  const rel = String(item && item.rel_path ? item.rel_path : '').replace(/\\/g, '/').trim();
  const metadata = (item && item.metadata_json && typeof item.metadata_json === 'object') ? item.metadata_json : {};
  const conversion = (metadata && metadata.conversion && typeof metadata.conversion === 'object') ? metadata.conversion : {};

  let toExt = _extractFileExt(item && (item.ext || item.filename || rel));
  const toExtMeta = _extractFileExt(conversion.to_ext || metadata.converted_to_ext || item && item.converted_to_ext);
  if (!toExt && toExtMeta) toExt = toExtMeta;

  let fromExt = _extractFileExt(conversion.from_ext || metadata.converted_from_ext || item && item.converted_from_ext);
  if (!fromExt) {
    const fromRel = conversion.from_rel_path || metadata.converted_from_rel || item && item.converted_from_rel;
    fromExt = _extractFileExt(fromRel);
  }

  let converted = !!(item && (item.converted === true || item.is_converted === true));
  if (!converted && rel) {
    const rl = rel.toLowerCase();
    converted = rl.startsWith('uploads/converted/') || rl.startsWith('converted/') || rl.includes('/converted/');
  }
  if (!converted && fromExt && toExt && fromExt !== toExt) converted = true;

  if (!converted) return { converted: false, label: '' };
  const fromLabel = fromExt || 'Ukendt';
  const toLabel = toExt || 'Ukendt';
  return { converted: true, label: `${fromLabel} -> ${toLabel}` };
}

function _itemWeather(item) {
  const metadata = (item && item.metadata_json && typeof item.metadata_json === 'object') ? item.metadata_json : {};
  const weather = metadata && metadata.weather && typeof metadata.weather === 'object' ? metadata.weather : null;
  return weather;
}

function _weatherFetchFailed(item) {
  const metadata = (item && item.metadata_json && typeof item.metadata_json === 'object') ? item.metadata_json : {};
  const value = metadata ? metadata.weather_fetch_failed : null;
  return value === true || value === 1 || value === '1' || value === 'true' || value === 'True';
}

function _markItemWeatherFetchFailed(item) {
  if (!item || typeof item !== 'object') return item;
  const metadata = (item.metadata_json && typeof item.metadata_json === 'object') ? item.metadata_json : {};
  delete metadata.weather;
  metadata.weather_fetch_failed = true;
  item.metadata_json = metadata;
  return item;
}

function _numOrNull(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function canFetchWeather(item) {
  if (!item) return false;
  const lat = _numOrNull(item.gps_lat);
  const lon = _numOrNull(item.gps_lon);
  const metadata = (item.metadata_json && typeof item.metadata_json === 'object') ? item.metadata_json : {};
  const geo = (metadata.geo && typeof metadata.geo === 'object') ? metadata.geo : {};
  const city = String(geo.city || metadata.city || '').trim();
  const captured = String(item.captured_at || item.modified_fs || item.created_fs || '').trim();
  return !!captured && ((lat != null && lon != null) || !!city);
}

function formatWeatherSummary(item) {
  const weather = _itemWeather(item);
  if (!weather) return '';
  const lang = resolveUiLanguage(state.uiLanguage || 'da');
  const temp = _numOrNull(weather.temperature_2m);
  const precipitation = _numOrNull(weather.precipitation);
  const wind = _numOrNull(weather.wind_speed_10m);
  const label = String((lang === 'en' ? weather.weather_label_en : weather.weather_label_da) || weather.weather_label_da || weather.weather_label_en || '').trim();
  const tempUnit = String(weather.temperature_2m_unit || '°C');
  const precipUnit = String(weather.precipitation_unit || 'mm');
  const windUnit = String(weather.wind_speed_10m_unit || 'm/s');
  const parts = [];
  if (temp != null) parts.push(`${temp.toFixed(Math.abs(temp) >= 10 ? 0 : 1)} ${tempUnit}`);
  if (label) parts.push(label);
  if (precipitation != null) {
    parts.push(precipitation > 0 ? `${precipitation.toFixed(precipitation >= 10 ? 0 : 1)} ${precipUnit}` : tr('weather_no_rain'));
  }
  if (wind != null) parts.push(`${tr('weather_wind')} ${wind.toFixed(wind >= 10 ? 0 : 1)} ${windUnit}`);
  return parts.length ? parts.join(' · ') : '';
}

function setWeatherEl(text, button, item, { fetching = false } = {}) {
  const canFetch = canFetchWeather(item);
  const hasWeather = !!_itemWeather(item);
  const summary = formatWeatherSummary(item);
  const hasFetchFailure = _weatherFetchFailed(item);
  const value = fetching
    ? tr('weather_fetching')
    : (summary || (hasFetchFailure ? tr('weather_fetch_failed') : (canFetch ? tr('weather_ready_to_fetch') : tr('weather_missing_inputs'))));
  if (text) {
    text.textContent = value;
    const weather = _itemWeather(item);
    const observed = weather && weather.observed_at ? ` · ${weather.observed_at}` : '';
    const source = weather && weather.source ? ` · ${weather.source}` : '';
    text.title = weather ? `${value}${observed}${source}` : value;
  }
  if (button) {
    button.classList.toggle('hidden', !canFetch);
    button.disabled = !canFetch || fetching;
    button.title = hasWeather ? 'Opdater vejr' : 'Hent vejr';
  }
}

function renderWeatherInfo(item, opts = {}) {
  setWeatherEl(els.detailWeather, els.detailWeatherBtn, item, opts);
  setWeatherEl(els.viWeather, els.viWeatherBtn, item, opts);
}

async function fetchWeatherForItem(item, { force = false, silent = false } = {}) {
  const id = Number(item && item.id ? item.id : 0);
  if (!id || !canFetchWeather(item)) return;
  const key = `${id}:${force ? 'force' : 'manual'}`;
  if (weatherFetches.has(key)) return;
  weatherFetches.add(key);
  renderWeatherInfo(item, { fetching: true });
  try {
    const res = await fetch(`/api/photos/${encodeURIComponent(id)}/weather`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ force: !!force }),
    });
    const data = await res.json().catch(() => null);
    if (!res.ok || !data || !data.ok) {
      const idx = state.items.findIndex(i => Number(i.id) === id);
      let failedItem = item;
      if (idx >= 0) {
        failedItem = _markItemWeatherFetchFailed(state.items[idx]);
        state.items[idx] = failedItem;
      } else {
        failedItem = _markItemWeatherFetchFailed(item);
      }
      if (!silent) showStatus((data && data.error) || tr('weather_fetch_failed'), 'err');
      if (Number(state.selectedId || 0) === id) {
        renderWeatherInfo(failedItem);
        if (els.rawMeta) els.rawMeta.textContent = JSON.stringify((failedItem && failedItem.metadata_json) || {}, null, 2);
      }
      try {
        const viewerItems = getViewerItems();
        const viewerItem = viewerItems[state.selectedIndex];
        if (viewerItem && Number(viewerItem.id) === id) {
          viewerItems[state.selectedIndex] = failedItem;
          renderWeatherInfo(failedItem);
        }
      } catch {}
      return;
    }
    const next = data.item;
    if (next && next.id) {
      const idx = state.items.findIndex(i => Number(i.id) === Number(next.id));
      if (idx >= 0) state.items[idx] = next;
      if (Number(state.selectedId || 0) === Number(next.id)) {
        renderWeatherInfo(next);
        if (els.rawMeta) els.rawMeta.textContent = JSON.stringify(next.metadata_json || {}, null, 2);
      }
      try {
        const viewerItems = getViewerItems();
        const viewerItem = viewerItems[state.selectedIndex];
        if (viewerItem && Number(viewerItem.id) === Number(next.id)) {
          viewerItems[state.selectedIndex] = next;
          renderWeatherInfo(next);
        }
      } catch {}
      if (!silent || force) showStatus(tr('weather_updated'), 'ok');
    }
  } catch (e) {
    const idx = state.items.findIndex(i => Number(i.id) === id);
    let failedItem = item;
    if (idx >= 0) {
      failedItem = _markItemWeatherFetchFailed(state.items[idx]);
      state.items[idx] = failedItem;
    } else {
      failedItem = _markItemWeatherFetchFailed(item);
    }
    if (Number(state.selectedId || 0) === id) {
      renderWeatherInfo(failedItem);
      if (els.rawMeta) els.rawMeta.textContent = JSON.stringify((failedItem && failedItem.metadata_json) || {}, null, 2);
    }
    try {
      const viewerItems = getViewerItems();
      const viewerItem = viewerItems[state.selectedIndex];
      if (viewerItem && Number(viewerItem.id) === id) {
        viewerItems[state.selectedIndex] = failedItem;
        renderWeatherInfo(failedItem);
      }
    } catch {}
    if (!silent) showStatus(tr('weather_fetch_failed'), 'err');
  } finally {
    weatherFetches.delete(key);
  }
}

function renderStats() {
  const inPeople = (state.view === 'personer');
  if (els.photoCountLabel) els.photoCountLabel.textContent = inPeople ? tr('stat_people') : tr('stat_photos');
  if (els.favoriteCountLabel) els.favoriteCountLabel.textContent = tr('stat_favorites');
  if (els.selectedCountLabel) els.selectedCountLabel.textContent = tr('stat_selected');
  const showHiddenLabel = document.querySelector('label[for="showHiddenToggle"]');
  if (showHiddenLabel) showHiddenLabel.textContent = tr('stat_show_hidden');
  if (els.statFavorites) els.statFavorites.style.display = inPeople ? 'none' : '';
  if (els.statSelected) els.statSelected.style.display = inPeople ? 'none' : '';

  if (inPeople) {
    if (els.photoCount) els.photoCount.textContent = Array.isArray(state.people) ? state.people.length : 0;
  } else {
    if (els.photoCount) els.photoCount.textContent = state.items.length;
    if (els.favoriteCount) els.favoriteCount.textContent = state.items.filter(i => i.favorite).length;
    if (els.selectedCount) els.selectedCount.textContent = state.selectedId ? "1" : "0";
  }
}

function photoframeSourceLabel(source) {
  if (source === 'setting') return tr('photoframe_source_setting');
  if (source === 'env') return tr('photoframe_source_env');
  if (source === 'file') return tr('photoframe_source_file');
  if (source === 'tokens') return tr('photoframe_source_tokens');
  return tr('photoframe_source_none');
}

function photoframeScopeSummary(item) {
  const mode = String(item && item.scope_mode ? item.scope_mode : 'all').trim().toLowerCase();
  const folderCount = Number(item && item.allowed_folder_count ? item.allowed_folder_count : 0) || 0;
  const photoCount = Number(item && item.allowed_photo_count ? item.allowed_photo_count : 0) || 0;
  if (mode === 'folders') return tr('photoframe_scope_summary_folders').replace('{count}', String(folderCount));
  if (mode === 'photos') return tr('photoframe_scope_summary_photos').replace('{count}', String(photoCount));
  return tr('photoframe_scope_summary_all');
}

function photoframeUpdateStatusUi(item) {
  const status = String(item && item.update_status ? item.update_status : '').trim().toLowerCase();
  let message = String(item && item.update_message ? item.update_message : '').trim();
  if (message.toLowerCase() === 'venter paa enheden') {
    message = 'Venter p\u00e5 enheden';
  }
  const requestedRaw = String(item && item.update_requested_at ? item.update_requested_at : '').trim();
  const requestedLabel = requestedRaw ? fmtDate(requestedRaw) : '';
  const versionText = String(item && item.update_version ? item.update_version : '').trim();
  if (!status) return null;

  let text = '';
  let cls = 'idle';
  let icon = '\u21bb';
  if (status === 'queued') {
    text = tr('photoframe_update_state_queued');
    cls = 'busy';
  } else if (status === 'downloading') {
    text = tr('photoframe_update_state_downloading');
    cls = 'busy';
  } else if (status === 'installing') {
    text = tr('photoframe_update_state_installing');
    cls = 'busy';
  } else if (status === 'restarting') {
    text = tr('photoframe_update_state_restarting');
    cls = 'busy';
  } else if (status === 'success') {
    text = tr('photoframe_update_state_success');
    cls = 'ok';
    icon = '\u2713';
  } else if (status === 'failed') {
    text = tr('photoframe_update_state_failed');
    cls = 'err';
    icon = '!';
  } else {
    return null;
  }

  let extra = message || '';
  if (!extra && requestedLabel) extra = requestedLabel;
  if (versionText) {
    extra = extra ? `${extra} - ${versionText}` : versionText;
  }
  const fullText = extra ? `${text} (${extra})` : text;
  return { status, cls, icon, text: fullText };
}

function photoframeContentSyncUi(item) {
  const status = String(item && item.content_sync_status ? item.content_sync_status : '').trim().toLowerCase();
  const count = Number(item && item.content_sync_count ? item.content_sync_count : 0) || 0;
  const sentAtRaw = String(item && item.content_sync_sent_at ? item.content_sync_sent_at : '').trim();
  const ackAtRaw = String(item && item.content_sync_acked_at ? item.content_sync_acked_at : '').trim();
  if (!status) return null;

  if (status === 'sending') {
    let text = tr('photoframe_sync_state_sending');
    if (count > 0) text = `${text} (${count})`;
    if (sentAtRaw) text = `${text} - ${fmtDate(sentAtRaw)}`;
    return { cls: 'busy', icon: '\u21bb', text };
  }
  if (status === 'sent') {
    let text = tr('photoframe_sync_state_sent');
    if (count > 0) text = `${text} (${count})`;
    if (ackAtRaw) text = `${text} - ${fmtDate(ackAtRaw)}`;
    return { cls: 'ok', icon: '\u2713', text };
  }
  return null;
}

function photoframeVersionUi(item) {
  const latestVersion = String(state.photoframeLatestVersion || '').trim();
  const deviceVersion = String(item && item.device_version ? item.device_version : '').trim();
  let status = String(item && item.version_status ? item.version_status : '').trim().toLowerCase();
  if (!latestVersion) status = 'unknown';
  if (!['latest', 'outdated', 'unknown'].includes(status)) status = 'unknown';

  let statusText = tr('photoframe_version_unknown');
  let cls = 'unknown';
  if (status === 'latest') {
    statusText = tr('photoframe_version_latest');
    cls = 'latest';
  } else if (status === 'outdated') {
    statusText = tr('photoframe_version_outdated');
    cls = 'outdated';
  }

  const deviceText = deviceVersion || '-';
  const targetText = latestVersion || '-';
  const text = `${statusText} (${deviceText} -> ${targetText})`;
  return { status, cls, text };
}

function photoframeVideoPrepareUi(item) {
  const total = Number(item && item.video_prepare_total ? item.video_prepare_total : 0) || 0;
  const ready = Number(item && item.video_prepare_ready ? item.video_prepare_ready : 0) || 0;
  const queued = Number(item && item.video_prepare_queued ? item.video_prepare_queued : 0) || 0;
  const requeued = Number(item && item.video_prepare_requeued ? item.video_prepare_requeued : 0) || 0;
  const waiting = Number(item && item.video_prepare_waiting ? item.video_prepare_waiting : 0) || 0;
  const capped = !!(item && item.video_prepare_capped);
  if (total <= 0) return null;

  const queuedVisible = Math.max(0, queued, requeued);
  const pctRaw = Number(item && item.video_prepare_pct ? item.video_prepare_pct : 0);
  const pct = Math.max(0, Math.min(100, Number.isFinite(pctRaw) ? Math.round(pctRaw) : Math.round((ready / Math.max(1, total)) * 100)));
  let cls = 'busy';
  let icon = '\u21bb';
  let stateText = tr('photoframe_video_prepare_processing');
  if (ready >= total) {
    cls = 'ok';
    icon = '\u2713';
    stateText = tr('photoframe_video_prepare_ready');
  } else if (queuedVisible <= 0) {
    cls = 'pending';
    icon = '\u2026';
    stateText = tr('photoframe_video_prepare_pending');
  } else if (queued <= 0 && requeued > 0) {
    cls = 'busy';
    icon = '\u21bb';
    stateText = tr('photoframe_video_prepare_retrying');
  }

  let detail = tr('photoframe_video_prepare_progress')
    .replace('{ready}', String(Math.max(0, ready)))
    .replace('{total}', String(Math.max(0, total)))
    .replace('{queued}', String(Math.max(0, queuedVisible)))
    .replace('{waiting}', String(Math.max(0, waiting)));
  if (capped) detail = `${detail} ${tr('photoframe_video_prepare_capped')}`;
  const text = `${stateText} (${pct}%)`;
  return { cls, icon, text, detail, pct };
}

const PHOTOFRAME_PREVIEW_SYNC_ROWS = 5;

function syncPhotoframePreviewHeights() {
  const cards = Array.from(document.querySelectorAll('.photoframe-card'));
  if (!cards.length) return;
  let isMobile = false;
  try {
    isMobile = !!window.matchMedia('(max-width: 760px)').matches;
  } catch (_) {
    isMobile = false;
  }

  cards.forEach((card) => {
    const preview = card.querySelector('.photoframe-preview');
    if (!(preview instanceof HTMLElement)) return;

    if (isMobile) {
      preview.style.height = '';
      preview.style.minHeight = '';
      preview.style.maxHeight = '';
      return;
    }

    const rows = Array.from(card.querySelectorAll('.photoframe-meta .photoframe-row')).slice(0, PHOTOFRAME_PREVIEW_SYNC_ROWS);
    if (rows.length < PHOTOFRAME_PREVIEW_SYNC_ROWS) {
      preview.style.height = '';
      preview.style.minHeight = '';
      preview.style.maxHeight = '';
      return;
    }

    let totalHeight = 0;
    for (let i = 0; i < rows.length; i += 1) {
      const row = rows[i];
      if (!(row instanceof HTMLElement)) continue;
      const rowRect = row.getBoundingClientRect();
      totalHeight += rowRect.height;
      if (i < (rows.length - 1)) {
        const nextRow = rows[i + 1];
        if (nextRow instanceof HTMLElement) {
          const nextRect = nextRow.getBoundingClientRect();
          totalHeight += Math.max(0, nextRect.top - rowRect.bottom);
        }
      }
    }

    const targetPx = Math.max(120, Math.round(totalHeight));
    const targetCss = `${targetPx}px`;
    preview.style.height = targetCss;
    preview.style.minHeight = targetCss;
    preview.style.maxHeight = targetCss;
  });
}

function renderPhotoframePanel() {
  if (!els.grid) return;
  const items = Array.isArray(state.photoframeItems) ? state.photoframeItems : [];
  const hasFrames = items.length > 0;
  const canCreateFrame = String((state.currentUser && state.currentUser.role) || '').toLowerCase() === 'admin';
  const checkedText = state.photoframeCheckedAt ? fmtDate(state.photoframeCheckedAt) : '-';
  const pathText = String(state.photoframeConfigPath || '/data/photoframes.json');

  const cardsHtml = items.map((item) => {
    const online = !!item.online;
    const statusLabel = online ? tr('photoframe_status_online') : tr('photoframe_status_offline');
    const statusClass = online ? 'online' : 'offline';
    const frameId = String(item.id || '').trim();
    const frameName = String(item.name || 'Photoframe').trim();
    const previewHiddenMap = (state.photoframePreviewHiddenById && typeof state.photoframePreviewHiddenById === 'object')
      ? state.photoframePreviewHiddenById
      : {};
    const previewVisible = !previewHiddenMap[frameId];
    const previewToggleLabel = previewVisible
      ? tr('photoframe_preview_toggle_off')
      : tr('photoframe_preview_toggle_on');
    const settingsProxyUrl = String(item.settings_proxy_url || '').trim() || (frameId ? `/api/photoframes/${encodeURIComponent(frameId)}/settings-proxy` : '');
    const ipText = String(item.net_ip || item.ip || '').trim() || '-';
    const localIpText = String(item.local_ip || '').trim() || '-';
    const tokenHint = String(item.token_hint || '').trim();
    const tokenText = tokenHint ? `***${tokenHint}` : '-';
    const scopeText = photoframeScopeSummary(item);
    const noteText = String(item.note || '').trim();
    const locationText = String(item.location || '').trim();
    const errText = String(item.error || '').trim();
    const checkedItemText = String(item.checked_at || state.photoframeCheckedAt || '').trim();
    const checkedLabel = checkedItemText ? fmtDate(checkedItemText) : checkedText;
    const lastSeenRaw = String(item.last_seen_at || '').trim();
    const lastSeenLabel = lastSeenRaw ? fmtDate(lastSeenRaw) : '-';
    const versionUi = photoframeVersionUi(item);
    const updateUi = photoframeUpdateStatusUi(item);
    const contentSyncUi = photoframeContentSyncUi(item);
    const updateBusy = !!(updateUi && ['queued', 'downloading', 'installing', 'restarting'].includes(updateUi.status));
    const previewThumbUrl = String(item.preview_thumb_url || '').trim();
    const previewUpdatedRaw = String(item.preview_updated_at || '').trim();
    const previewUpdatedLabel = previewUpdatedRaw ? fmtDate(previewUpdatedRaw) : '';
    const previewVersionSeed = String(
      previewUpdatedRaw || item.preview_photo_id || checkedItemText || state.photoframeCheckedAt || ''
    ).trim();
    const previewThumbSrc = previewThumbUrl
      ? `${previewThumbUrl}${previewThumbUrl.includes('?') ? '&' : '?'}v=${encodeURIComponent(previewVersionSeed || '0')}`
      : '';
    return `
      <article class="photoframe-card ${online ? 'is-online' : 'is-offline'}">
        <div class="photoframe-card-head">
          <h3 class="photoframe-card-title">${escapeHtml(frameName)}</h3>
          <span class="photoframe-badge ${statusClass}">
            <span class="dot" aria-hidden="true"></span>
            ${escapeHtml(statusLabel)}
          </span>
        </div>
        <div class="photoframe-card-body${previewVisible ? '' : ' no-preview'}">
          <div class="photoframe-card-main">
            ${locationText ? `<div class="mini-label">${escapeHtml(locationText)}</div>` : ''}
            <div class="photoframe-meta">
              <div class="photoframe-row photoframe-row-token"><span>${escapeHtml(tr('photoframe_card_token'))}</span><strong class="photoframe-token-value">${escapeHtml(tokenText)}</strong></div>
              <div class="photoframe-row"><span>${escapeHtml(tr('photoframe_card_scope'))}</span><strong>${escapeHtml(scopeText)}</strong></div>
              <div class="photoframe-row"><span>${escapeHtml(tr('photoframe_card_ip'))}</span><strong>${escapeHtml(ipText)}</strong></div>
              <div class="photoframe-row"><span>${escapeHtml(tr('photoframe_card_local_ip'))}</span><strong>${escapeHtml(localIpText)}</strong></div>
              <div class="photoframe-row"><span>${escapeHtml(tr('photoframe_card_last_seen'))}</span><strong>${escapeHtml(lastSeenLabel)}</strong></div>
              <div class="photoframe-row"><span>${escapeHtml(tr('photoframe_last_checked'))}</span><strong>${escapeHtml(checkedLabel)}</strong></div>
              <div class="photoframe-row photoframe-version-row">
                <span>${escapeHtml(tr('photoframe_card_version'))}</span>
                <strong>
                  <span class="photoframe-version-pill ${escapeHtml(versionUi.cls)}">${escapeHtml(versionUi.text)}</span>
                </strong>
              </div>
              ${updateUi ? `
                <div class="photoframe-row photoframe-update-row">
                  <span>${escapeHtml(tr('photoframe_card_update'))}</span>
                  <strong>
                    <span class="photoframe-update-pill ${escapeHtml(updateUi.cls)}">
                      <span class="icon" aria-hidden="true">${escapeHtml(updateUi.icon)}</span>
                      ${escapeHtml(updateUi.text)}
                    </span>
                  </strong>
                </div>
              ` : ''}
              ${contentSyncUi ? `
                <div class="photoframe-row photoframe-update-row">
                  <span>${escapeHtml(tr('photoframe_card_sync'))}</span>
                  <strong>
                    <span class="photoframe-update-pill ${escapeHtml(contentSyncUi.cls)}">
                      <span class="icon" aria-hidden="true">${escapeHtml(contentSyncUi.icon)}</span>
                      ${escapeHtml(contentSyncUi.text)}
                    </span>
                  </strong>
                </div>
              ` : ''}
              ${errText ? `<div class="photoframe-row"><span>${escapeHtml(tr('photoframe_card_error'))}</span><strong>${escapeHtml(errText)}</strong></div>` : ''}
            </div>
            ${noteText ? `<div class="mini-label">${escapeHtml(noteText)}</div>` : ''}
            ${canCreateFrame ? `
              <div class="photoframe-card-actions">
                <button
                  class="btn small"
                  type="button"
                  data-photoframe-action="open-settings"
                  data-frame-id="${escapeHtml(frameId)}"
                  data-settings-url="${escapeHtml(settingsProxyUrl)}"
                >${escapeHtml(tr('photoframe_open_settings_btn'))}</button>
                <button
                  class="btn small"
                  type="button"
                  data-photoframe-action="scope"
                  data-frame-id="${escapeHtml(frameId)}"
                  data-frame-name="${escapeHtml(frameName)}"
                >${escapeHtml(tr('photoframe_scope_btn'))}</button>
                <button
                  class="btn small"
                  type="button"
                  data-photoframe-action="trigger-update-upload"
                  data-frame-id="${escapeHtml(frameId)}"
                  data-frame-name="${escapeHtml(frameName)}"
                  ${updateBusy ? ' disabled' : ''}
                >${escapeHtml(tr('photoframe_update_upload_btn'))}</button>
                <button
                  class="btn small"
                  type="button"
                  data-photoframe-action="restart-kiosk"
                  data-frame-id="${escapeHtml(frameId)}"
                  data-frame-name="${escapeHtml(frameName)}"
                  ${updateBusy ? ' disabled' : ''}
                >${escapeHtml(tr('photoframe_restart_kiosk_btn'))}</button>
                <button
                  class="btn small danger"
                  type="button"
                  data-photoframe-action="reset-device"
                  data-frame-id="${escapeHtml(frameId)}"
                  data-frame-name="${escapeHtml(frameName)}"
                  ${updateBusy ? ' disabled' : ''}
                >${escapeHtml(tr('photoframe_reset_device_btn'))}</button>
                ${updateBusy ? `
                  <button
                    class="btn small danger"
                    type="button"
                    data-photoframe-action="cancel-update"
                    data-frame-id="${escapeHtml(frameId)}"
                    data-frame-name="${escapeHtml(frameName)}"
                  >${escapeHtml(tr('photoframe_update_cancel_btn'))}</button>
                ` : ''}
                <button
                  class="btn small"
                  type="button"
                  data-photoframe-action="show-token"
                  data-frame-id="${escapeHtml(frameId)}"
                  data-frame-name="${escapeHtml(frameName)}"
                >${escapeHtml(tr('photoframe_show_token_btn'))}</button>
                <button
                  class="btn small"
                  type="button"
                  data-photoframe-action="toggle-preview"
                  data-frame-id="${escapeHtml(frameId)}"
                >${escapeHtml(previewToggleLabel)}</button>
                <button
                  class="btn small"
                  type="button"
                  data-photoframe-action="delete-token"
                  data-frame-id="${escapeHtml(frameId)}"
                  data-frame-name="${escapeHtml(frameName)}"
                >${escapeHtml(tr('photoframe_delete_btn'))}</button>
              </div>
            ` : ''}
          </div>
          ${previewVisible ? `
            <aside class="photoframe-preview" aria-label="Preview">
              ${previewThumbSrc
                ? `<img src="${escapeHtml(previewThumbSrc)}" alt="${escapeHtml(frameName)}" loading="lazy" decoding="async">`
                : `<div class="photoframe-preview-empty">${escapeHtml(tr('no_thumb'))}</div>`
              }
              ${previewUpdatedLabel ? `<div class="photoframe-preview-meta">${escapeHtml(previewUpdatedLabel)}</div>` : ''}
            </aside>
          ` : ''}
        </div>
      </article>
    `;
  }).join('');

  const loadingBlock = (state.photoframeLoading && !items.length)
    ? `<div class="panel"><div class="mini-label">${escapeHtml(tr('photoframe_loading'))}</div></div>`
    : '';
  const emptyBlock = (!state.photoframeLoading && !items.length)
    ? `<div class="panel">
         <h3 style="margin:0 0 8px;">${escapeHtml(tr('photoframe_empty_title'))}</h3>
         <p class="mini-label" style="margin:0 0 8px;">${escapeHtml(tr('photoframe_empty_sub').replace('{path}', pathText))}</p>
       </div>`
    : '';
  const errorBlock = state.photoframeError
    ? `<div class="status err">${escapeHtml(state.photoframeError)}</div>`
    : '';

  const contentHeader = document.querySelector('.content-header');
  if (contentHeader) {
    let headerActions = document.getElementById('photoframeHeaderActions');
    if (!headerActions) {
      headerActions = document.createElement('div');
      headerActions.id = 'photoframeHeaderActions';
      headerActions.className = 'photoframe-header-actions';
      contentHeader.appendChild(headerActions);
    }
    headerActions.innerHTML = `
      ${canCreateFrame ? `<button id="photoframeCreateBtn" class="btn small" type="button">${escapeHtml(tr('photoframe_create_btn'))}</button>` : ''}
      ${canCreateFrame ? `
        <button
          id="photoframeUploadAllBtn"
          class="btn small"
          type="button"
          ${(!hasFrames || state.photoframeLoading) ? ' disabled' : ''}
        >${escapeHtml(tr('photoframe_update_upload_all_btn'))}</button>
      ` : ''}
      <button
        id="photoframeRefreshBtn"
        class="btn small photoframe-refresh-btn"
        type="button"
        aria-label="${escapeHtml(tr('photoframe_refresh'))}"
        title="${escapeHtml(tr('photoframe_refresh'))}"
        ${state.photoframeLoading ? ' disabled' : ''}
      ><span aria-hidden="true">&#x21bb;</span></button>
    `;
  }

  els.grid.innerHTML = `
    <section class="photoframe-wrap">
      ${errorBlock}
      ${loadingBlock}
      ${emptyBlock}
      <div class="photoframe-grid">${cardsHtml}</div>
    </section>
    <div id="photoframeCreateModal" class="hidden photoframe-modal" style="position:fixed;inset:0;background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;z-index:10000;">
      <div class="photoframe-modal-card" style="width:560px;max-width:92vw;background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
          <h3 style="margin:0;">${escapeHtml(tr('photoframe_create_title'))}</h3>
          <button id="photoframeCreateCloseBtn" class="btn">${escapeHtml(tr('scan_modal_close'))}</button>
        </div>
        <p class="mini-label" style="margin:0 0 14px;line-height:1.5;">${escapeHtml(tr('photoframe_create_intro'))}</p>
        <div class="actions" style="justify-content:flex-end;gap:8px;">
          <button id="photoframeCreateCancelBtn" class="btn">${escapeHtml(tr('photoframe_create_cancel'))}</button>
          <button id="photoframeCreateSubmitBtn" class="btn primary">${escapeHtml(tr('photoframe_create_submit'))}</button>
        </div>
        <div id="photoframeCreateError" class="mini-label hidden" style="color:#ff6b6b;margin-top:8px;"></div>
        <div id="photoframeCreateResultWrap" class="hidden" style="margin-top:12px;border:1px solid var(--border);border-radius:10px;background:var(--panel-2);padding:10px;">
          <div class="mini-label" style="margin-bottom:8px;font-weight:700;">${escapeHtml(tr('photoframe_create_result_title'))}</div>
          <div class="form-row" style="margin-bottom:0;">
            <label for="photoframeCreateToken">${escapeHtml(tr('photoframe_create_token_label'))}</label>
            <div class="toolbar photoframe-token-field" style="gap:8px;align-items:stretch;">
              <input id="photoframeCreateToken" class="mapper-input" type="text" readonly style="min-width:0;width:100%;">
              <button id="photoframeCreateCopyTokenBtn" class="btn" type="button">${escapeHtml(tr('photoframe_create_copy'))}</button>
            </div>
          </div>
          <div class="mini-label" style="margin-top:8px;">${escapeHtml(tr('photoframe_create_token_help'))}</div>
        </div>
      </div>
    </div>
    <div id="photoframeShowTokenModal" class="hidden photoframe-modal" style="position:fixed;inset:0;background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;z-index:10001;">
      <div class="photoframe-modal-card" style="width:560px;max-width:92vw;background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
          <h3 id="photoframeShowTokenTitle" style="margin:0;">${escapeHtml(tr('photoframe_show_token_title'))}</h3>
          <button id="photoframeShowTokenCloseBtn" class="btn">${escapeHtml(tr('photoframe_show_token_close'))}</button>
        </div>
        <div class="form-row" style="margin-bottom:0;">
          <label for="photoframeShowTokenInput">${escapeHtml(tr('photoframe_create_token_label'))}</label>
          <div class="toolbar photoframe-token-field" style="gap:8px;align-items:stretch;">
            <input id="photoframeShowTokenInput" class="mapper-input" type="text" readonly style="min-width:0;width:100%;">
            <button id="photoframeShowTokenCopyBtn" class="btn" type="button">${escapeHtml(tr('photoframe_create_copy'))}</button>
          </div>
        </div>
        <div id="photoframeShowTokenError" class="mini-label hidden" style="color:#ff6b6b;margin-top:8px;"></div>
      </div>
    </div>
    <div id="photoframeScopeModal" class="hidden" style="position:fixed;inset:0;background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;z-index:10002;">
      <div style="width:980px;max-width:96vw;background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px;max-height:90vh;overflow:auto;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
          <h3 style="margin:0;">${escapeHtml(tr('photoframe_scope_title'))}</h3>
          <button id="photoframeScopeCloseBtn" class="btn">${escapeHtml(tr('scan_modal_close'))}</button>
        </div>
        <div id="photoframeScopeTarget" class="mini-label" style="margin-bottom:10px;"></div>
        <div class="form-row">
          <label for="photoframeScopeMode">${escapeHtml(tr('photoframe_scope_mode_label'))}</label>
          <select id="photoframeScopeMode" class="select">
            <option value="all">${escapeHtml(tr('photoframe_scope_mode_all'))}</option>
            <option value="folders">${escapeHtml(tr('photoframe_scope_mode_folders'))}</option>
            <option value="photos">${escapeHtml(tr('photoframe_scope_mode_photos'))}</option>
          </select>
        </div>
        <div id="photoframeScopeFoldersWrap" class="hidden">
          <div class="mini-label" style="margin-bottom:6px;">${escapeHtml(tr('photoframe_scope_folders_label'))}</div>
          <div id="photoframeScopeFoldersList" class="photoframe-scope-list"></div>
        </div>
        <div id="photoframeScopePhotosWrap" class="hidden">
          <div class="photoframe-scope-toolbar-row">
            <button id="photoframeScopeSelectModeBtn" class="btn small" type="button">${escapeHtml(tr('photoframe_scope_select_mode'))}</button>
            <button id="photoframeScopeSelectVisibleBtn" class="btn small" type="button">${escapeHtml(tr('photoframe_scope_select_visible'))}</button>
            <button id="photoframeScopeClearVisibleBtn" class="btn small" type="button">${escapeHtml(tr('photoframe_scope_unselect_visible'))}</button>
            <div id="photoframeScopeSelectedCount" class="mini-label">${escapeHtml(tr('photoframe_scope_selected_count').replace('{count}', '0'))}</div>
          </div>
          <div class="mini-label photoframe-scope-hint">${escapeHtml(tr('photoframe_scope_hold_hint'))}</div>
          <div class="photoframe-scope-browser">
            <aside class="photoframe-scope-folders-pane">
              <div class="mini-label" style="margin-bottom:6px;">${escapeHtml(tr('photoframe_scope_folders_label'))}</div>
              <div id="photoframeScopeFolderNav" class="photoframe-scope-folder-nav"></div>
            </aside>
            <section class="photoframe-scope-photos-pane">
              <div class="toolbar" style="gap:8px;align-items:stretch;margin-bottom:8px;">
                <input id="photoframeScopePhotoSearch" class="mapper-input" type="text" placeholder="${escapeHtml(tr('photoframe_scope_search_placeholder'))}" style="min-width:0;width:100%;">
                <button id="photoframeScopePhotoSearchBtn" class="btn small" type="button">${escapeHtml(tr('photoframe_scope_search_btn'))}</button>
              </div>
              <div id="photoframeScopePhotosList" class="photoframe-scope-thumb-grid"></div>
            </section>
          </div>
        </div>
        <div id="photoframeScopeError" class="mini-label hidden" style="color:#ff6b6b;margin-top:8px;"></div>
        <div class="actions" style="justify-content:flex-end;gap:8px;margin-top:12px;">
          <button id="photoframeScopeCancelBtn" class="btn">${escapeHtml(tr('scan_modal_cancel'))}</button>
          <button id="photoframeScopeSaveBtn" class="btn primary">${escapeHtml(tr('photoframe_scope_save'))}</button>
        </div>
      </div>
    </div>
  `;

  try {
    window.requestAnimationFrame(() => syncPhotoframePreviewHeights());
  } catch (_) {
    syncPhotoframePreviewHeights();
  }
  els.grid.querySelectorAll('.photoframe-preview img').forEach((img) => {
    if (!img.complete) {
      img.addEventListener('load', syncPhotoframePreviewHeights, { once: true });
      img.addEventListener('error', syncPhotoframePreviewHeights, { once: true });
    }
  });

  const refreshBtn = document.getElementById('photoframeRefreshBtn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', async () => {
      await loadPhotoframeStatus();
    });
  }

  const createBtn = document.getElementById('photoframeCreateBtn');
  const uploadAllBtn = document.getElementById('photoframeUploadAllBtn');
  const createModal = document.getElementById('photoframeCreateModal');
  const createCloseBtn = document.getElementById('photoframeCreateCloseBtn');
  const createCancelBtn = document.getElementById('photoframeCreateCancelBtn');
  const createSubmitBtn = document.getElementById('photoframeCreateSubmitBtn');
  const createErrorEl = document.getElementById('photoframeCreateError');
  const resultWrap = document.getElementById('photoframeCreateResultWrap');
  const tokenInput = document.getElementById('photoframeCreateToken');
  const copyTokenBtn = document.getElementById('photoframeCreateCopyTokenBtn');
  const showTokenModal = document.getElementById('photoframeShowTokenModal');
  const showTokenTitle = document.getElementById('photoframeShowTokenTitle');
  const showTokenCloseBtn = document.getElementById('photoframeShowTokenCloseBtn');
  const showTokenInput = document.getElementById('photoframeShowTokenInput');
  const showTokenCopyBtn = document.getElementById('photoframeShowTokenCopyBtn');
  const showTokenErrorEl = document.getElementById('photoframeShowTokenError');
  const scopeModal = document.getElementById('photoframeScopeModal');
  const scopeCloseBtn = document.getElementById('photoframeScopeCloseBtn');
  const scopeCancelBtn = document.getElementById('photoframeScopeCancelBtn');
  const scopeSaveBtn = document.getElementById('photoframeScopeSaveBtn');
  const scopeTargetEl = document.getElementById('photoframeScopeTarget');
  const scopeModeSel = document.getElementById('photoframeScopeMode');
  const scopeFoldersWrap = document.getElementById('photoframeScopeFoldersWrap');
  const scopeFoldersList = document.getElementById('photoframeScopeFoldersList');
  const scopePhotosWrap = document.getElementById('photoframeScopePhotosWrap');
  const scopeFolderNav = document.getElementById('photoframeScopeFolderNav');
  const scopePhotosList = document.getElementById('photoframeScopePhotosList');
  const scopePhotoSearchInput = document.getElementById('photoframeScopePhotoSearch');
  const scopePhotoSearchBtn = document.getElementById('photoframeScopePhotoSearchBtn');
  const scopeSelectModeBtn = document.getElementById('photoframeScopeSelectModeBtn');
  const scopeSelectVisibleBtn = document.getElementById('photoframeScopeSelectVisibleBtn');
  const scopeClearVisibleBtn = document.getElementById('photoframeScopeClearVisibleBtn');
  const scopeSelectedCountEl = document.getElementById('photoframeScopeSelectedCount');
  const scopeErrorEl = document.getElementById('photoframeScopeError');

  let shouldRefreshOnClose = false;
  let scopeFrameId = '';
  let scopeFrameName = '';
  let scopeMode = 'all';
  let scopeFoldersSelected = new Set();
  let scopePhotosSelected = new Set();
  let scopeFolderOptions = [];
  let scopePhotoOptions = [];
  let scopePhotoFolderPath = '';
  let scopePhotoSelectMode = false;
  let scopePhotoDragSession = null;
  let scopePhotoDragSuppressClickUntil = 0;
  const SCOPE_SELECTED_FOLDER_KEY = '__selected__';
  let scopePhotoQueryText = '';
  let scopeSelectedBucketIds = new Set();

  const showCreateError = (text) => {
    if (!createErrorEl) return;
    const msg = String(text || '').trim();
    if (!msg) {
      createErrorEl.textContent = '';
      createErrorEl.classList.add('hidden');
      return;
    }
    createErrorEl.textContent = msg;
    createErrorEl.classList.remove('hidden');
  };

  const copyText = async (value) => {
    const txt = String(value || '').trim();
    if (!txt) return;
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(txt);
      } else {
        const temp = document.createElement('input');
        temp.value = txt;
        document.body.appendChild(temp);
        temp.select();
        document.execCommand('copy');
        document.body.removeChild(temp);
      }
      showStatus(tr('photoframe_create_copy_ok'), 'ok');
    } catch (_) {
      showStatus(tr('photoframe_create_copy_failed'), 'err');
    }
  };

  const showTokenError = (text) => {
    if (!showTokenErrorEl) return;
    const msg = String(text || '').trim();
    if (!msg) {
      showTokenErrorEl.textContent = '';
      showTokenErrorEl.classList.add('hidden');
      return;
    }
    showTokenErrorEl.textContent = msg;
    showTokenErrorEl.classList.remove('hidden');
  };

  const closeShowTokenModal = () => {
    if (!showTokenModal) return;
    showTokenModal.classList.add('hidden');
  };

  const showScopeError = (text) => {
    if (!scopeErrorEl) return;
    const msg = String(text || '').trim();
    if (!msg) {
      scopeErrorEl.textContent = '';
      scopeErrorEl.classList.add('hidden');
      return;
    }
    scopeErrorEl.textContent = msg;
    scopeErrorEl.classList.remove('hidden');
  };

  const closeScopeModal = () => {
    if (!scopeModal) return;
    setScopePhotoSelectMode(false);
    scopeModal.classList.add('hidden');
  };

  const updateScopeModeVisibility = () => {
    const mode = String(scopeMode || (scopeModeSel && scopeModeSel.value) || 'all').trim().toLowerCase();
    if (scopeFoldersWrap) scopeFoldersWrap.classList.toggle('hidden', mode !== 'folders');
    if (scopePhotosWrap) scopePhotosWrap.classList.toggle('hidden', mode !== 'photos');
    const inPhotosMode = mode === 'photos';
    if (scopeSelectModeBtn) scopeSelectModeBtn.disabled = !inPhotosMode;
    if (scopeSelectVisibleBtn) scopeSelectVisibleBtn.disabled = !inPhotosMode;
    if (scopeClearVisibleBtn) scopeClearVisibleBtn.disabled = !inPhotosMode;
    if (mode !== 'photos') {
      setScopePhotoSelectMode(false);
    }
  };

  const updateScopeSelectedCount = () => {
    if (!scopeSelectedCountEl) return;
    const count = scopePhotosSelected ? scopePhotosSelected.size : 0;
    scopeSelectedCountEl.textContent = tr('photoframe_scope_selected_count').replace('{count}', String(count));
  };

  const stopScopePhotoDragSelection = () => {
    document.removeEventListener('pointermove', onScopePhotoDragPointerMove);
    document.removeEventListener('pointerup', onScopePhotoDragPointerUp);
    document.removeEventListener('pointercancel', onScopePhotoDragPointerUp);
    scopePhotoDragSession = null;
  };

  const setScopePhotoSelection = (photoId, shouldSelect, cardEl = null) => {
    const pid = Number(photoId || 0) || 0;
    if (!pid) return;
    if (shouldSelect) {
      scopePhotosSelected.add(pid);
      scopeSelectedBucketIds.add(pid);
    } else {
      scopePhotosSelected.delete(pid);
    }
    const card = cardEl || (scopePhotosList ? scopePhotosList.querySelector(`[data-photoframe-scope-photo-card="${pid}"]`) : null);
    if (card) card.classList.toggle('selected', !!shouldSelect);
    updateScopeSelectedCount();
  };

  const setScopePhotoSelectMode = (enabled) => {
    scopePhotoSelectMode = !!enabled;
    if (!scopePhotoSelectMode) stopScopePhotoDragSelection();
    if (scopePhotosWrap) scopePhotosWrap.classList.toggle('photoframe-scope-select-mode', scopePhotoSelectMode);
    if (scopeSelectModeBtn) {
      scopeSelectModeBtn.textContent = scopePhotoSelectMode ? tr('photoframe_scope_done_mode') : tr('photoframe_scope_select_mode');
      scopeSelectModeBtn.classList.toggle('primary', scopePhotoSelectMode);
    }
  };

  const setScopeVisibleSelection = (shouldSelect) => {
    if (!scopePhotosList) return;
    const nextState = !!shouldSelect;
    let touched = false;
    scopePhotosList.querySelectorAll('[data-photoframe-scope-photo-card]').forEach((card) => {
      const pid = Number(card.getAttribute('data-photoframe-scope-photo-card') || 0) || 0;
      if (!pid) return;
      const current = scopePhotosSelected.has(pid);
      if (current === nextState) return;
      touched = true;
      if (nextState) {
        scopePhotosSelected.add(pid);
        scopeSelectedBucketIds.add(pid);
      }
      else scopePhotosSelected.delete(pid);
      card.classList.toggle('selected', nextState);
    });
    if (touched) updateScopeSelectedCount();
  };

  const startScopePhotoDragSelection = (ev, card, forceSelect = null) => {
    if (!scopePhotoSelectMode) return;
    if (!ev || !card) return;
    try { ev.preventDefault(); } catch {}
    const pid = Number(card.getAttribute('data-photoframe-scope-photo-card') || 0) || 0;
    if (!pid) return;
    const actionSelect = (forceSelect === null) ? !scopePhotosSelected.has(pid) : !!forceSelect;
    stopScopePhotoDragSelection();
    scopePhotoDragSession = {
      pointerId: Number(ev.pointerId),
      actionSelect,
      touched: new Set(),
    };
    setScopePhotoSelection(pid, actionSelect, card);
    scopePhotoDragSession.touched.add(pid);
    document.addEventListener('pointermove', onScopePhotoDragPointerMove, { passive: false });
    document.addEventListener('pointerup', onScopePhotoDragPointerUp, { passive: true });
    document.addEventListener('pointercancel', onScopePhotoDragPointerUp, { passive: true });
  };

  function onScopePhotoDragPointerMove(ev) {
    const session = scopePhotoDragSession;
    if (!session) return;
    if (Number(ev.pointerId) !== Number(session.pointerId)) return;
    const node = document.elementFromPoint(Number(ev.clientX || 0), Number(ev.clientY || 0));
    const card = (node && node.closest) ? node.closest('[data-photoframe-scope-photo-card]') : null;
    if (!card) return;
    const pid = Number(card.getAttribute('data-photoframe-scope-photo-card') || 0) || 0;
    if (!pid || session.touched.has(pid)) return;
    session.touched.add(pid);
    setScopePhotoSelection(pid, !!session.actionSelect, card);
    try { ev.preventDefault(); } catch {}
  }

  function onScopePhotoDragPointerUp(ev) {
    const session = scopePhotoDragSession;
    if (!session) return;
    if (ev && ev.pointerId != null && Number(ev.pointerId) !== Number(session.pointerId)) return;
    scopePhotoDragSuppressClickUntil = Date.now() + 220;
    stopScopePhotoDragSelection();
  }

  const renderScopeFolderNav = () => {
    if (!scopeFolderNav) return;
    const folderOpts = Array.isArray(scopeFolderOptions) ? scopeFolderOptions : [];
    const opts = [SCOPE_SELECTED_FOLDER_KEY, ...folderOpts];
    scopeFolderNav.innerHTML = opts.map((path) => {
      const p = String(path || '').trim();
      const active = p === scopePhotoFolderPath ? ' active' : '';
      const isSelectedBucket = p === SCOPE_SELECTED_FOLDER_KEY;
      const label = isSelectedBucket ? tr('photoframe_scope_folder_selected') : (p.split('/').filter(Boolean).pop() || p);
      const labelSafe = escapeHtml(label);
      const pathSafe = escapeHtml(p);
      const sub = (!isSelectedBucket && p)
        ? `<div class="photoframe-scope-folder-line is-sub mini-label" title="${pathSafe}">
             <span class="photoframe-scope-folder-marquee-text">${pathSafe}</span>
           </div>`
        : '';
      return `<button type="button" class="photoframe-scope-folder-item${active}" data-photoframe-scope-folder-nav="${escapeHtml(p)}">
        <div class="photoframe-scope-folder-line is-title" title="${labelSafe}">
          <span class="photoframe-scope-folder-marquee-text">${labelSafe}</span>
        </div>
        ${sub}
      </button>`;
    }).join('');
    const setupScopeFolderMarquees = () => {
      scopeFolderNav.querySelectorAll('.photoframe-scope-folder-line').forEach((line) => {
        const textEl = line.querySelector('.photoframe-scope-folder-marquee-text');
        if (!textEl) return;
        line.classList.remove('is-overflow');
        line.style.removeProperty('--scroll-distance');
        line.style.removeProperty('--scroll-duration');
        const overflow = Math.ceil(textEl.scrollWidth - line.clientWidth);
        if (overflow <= 2) return;
        const distance = overflow + 20;
        const duration = Math.max(3, Math.min(18, distance / 42));
        line.style.setProperty('--scroll-distance', `${distance}px`);
        line.style.setProperty('--scroll-duration', `${duration.toFixed(2)}s`);
        line.classList.add('is-overflow');
      });
    };
    setupScopeFolderMarquees();
    requestAnimationFrame(setupScopeFolderMarquees);
    scopeFolderNav.querySelectorAll('[data-photoframe-scope-folder-nav]').forEach((el) => {
      el.addEventListener('click', async () => {
        const nextPath = String(el.getAttribute('data-photoframe-scope-folder-nav') || '').trim();
        if (nextPath === scopePhotoFolderPath) return;
        scopePhotoFolderPath = nextPath;
        renderScopeFolderNav();
        showScopeError('');
        try {
          await loadScopePhotos(String((scopePhotoSearchInput && scopePhotoSearchInput.value) || ''));
          renderScopePhotos();
        } catch (e) {
          showScopeError(String((e && e.message) || tr('photoframe_scope_load_failed')));
        }
      });
    });
  };

  const renderScopeFolders = () => {
    if (!scopeFoldersList) return;
    if (!Array.isArray(scopeFolderOptions) || !scopeFolderOptions.length) {
      scopeFoldersList.innerHTML = `<div class="mini-label">${escapeHtml(tr('photoframe_scope_empty_folders'))}</div>`;
      return;
    }
    scopeFoldersList.innerHTML = scopeFolderOptions.map((path, idx) => {
      const p = String(path || '').trim();
      if (!p) return '';
      const checked = scopeFoldersSelected.has(p) ? ' checked' : '';
      const id = `pfScopeFolder_${idx}`;
      return `<label style="display:flex;gap:8px;align-items:flex-start;padding:3px 0;">
        <input id="${id}" type="checkbox" data-photoframe-scope-folder="${escapeHtml(p)}"${checked}>
        <span style="word-break:break-all;">${escapeHtml(p)}</span>
      </label>`;
    }).join('');
    scopeFoldersList.querySelectorAll('input[data-photoframe-scope-folder]').forEach((el) => {
      el.addEventListener('change', () => {
        const p = String(el.getAttribute('data-photoframe-scope-folder') || '').trim();
        if (!p) return;
        if (el.checked) scopeFoldersSelected.add(p);
        else scopeFoldersSelected.delete(p);
      });
    });
  };

  const renderScopePhotos = () => {
    if (!scopePhotosList) return;
    const selectedOnly = String(scopePhotoFolderPath || '').trim() === SCOPE_SELECTED_FOLDER_KEY;
    const q = String(scopePhotoQueryText || '').trim().toLowerCase();
    let photoItems = Array.isArray(scopePhotoOptions)
      ? scopePhotoOptions.filter((it) => {
          const rel = String(it && it.rel_path ? it.rel_path : '').toLowerCase();
          const extRaw = String((it && (it.ext || rel)) || '').toLowerCase();
          const isVideo = !!(it && it.is_video) || ['.mp4', '.m4v', '.mov', '.avi', '.mkv', '.webm', '.3gp'].some((ext) => extRaw.endsWith(ext));
          return !isVideo;
        })
      : [];
    if (selectedOnly) {
      photoItems = photoItems.filter((it) => {
        const pid = Number(it && it.id ? it.id : 0) || 0;
        return !!pid && scopeSelectedBucketIds.has(pid);
      });
    }
    if (q) {
      photoItems = photoItems.filter((it) => {
        const pid = Number(it && it.id ? it.id : 0) || 0;
        const rel = String(it && it.rel_path ? it.rel_path : '').toLowerCase();
        const label = String(it && it.label ? it.label : '').toLowerCase();
        return String(pid).includes(q) || rel.includes(q) || label.includes(q);
      });
    }
    if (!photoItems.length) {
      scopePhotosList.innerHTML = `<div class="mini-label">${escapeHtml(tr('photoframe_scope_empty_photos'))}</div>`;
      updateScopeSelectedCount();
      return;
    }
    scopePhotosList.innerHTML = photoItems.map((it) => {
      const pid = Number(it && it.id ? it.id : 0) || 0;
      if (!pid) return '';
      const selected = scopePhotosSelected.has(pid);
      const rel = String(it && it.rel_path ? it.rel_path : '').trim();
      const label = String(it && it.label ? it.label : `Photo #${pid}`).trim();
      const thumb = String(it && it.thumb_url ? it.thumb_url : '').trim();
      const extRaw = String((it && (it.ext || rel || label)) || '').toLowerCase();
      const isGif = !!(it && it.is_gif) || extRaw.endsWith('.gif');
      const mediaBadge = isGif ? `<div class="gif-badge" aria-label="GIF" title="GIF">GIF</div>` : '';
      return `
        <article class="photoframe-scope-photo-card${selected ? ' selected' : ''}" data-photoframe-scope-photo-card="${pid}">
          <div class="photoframe-scope-photo-thumb">
            ${thumb ? `<img class="photoframe-scope-photo-img" loading="lazy" decoding="async" src="${escapeHtml(thumb)}" alt="" data-photoframe-scope-thumb="1">` : ''}
            <div class="photoframe-scope-photo-placeholder${thumb ? ' hidden' : ''}">${escapeHtml(tr('no_thumb'))}</div>
            ${mediaBadge}
            <span class="photoframe-scope-select-badge">&#10003;</span>
          </div>
          <div class="photoframe-scope-photo-body">
            <h4 class="photoframe-scope-photo-title">#${pid} - ${escapeHtml(label || `Photo #${pid}`)}</h4>
            <div class="photoframe-scope-photo-meta">
              <span>${escapeHtml(rel || '-')}</span>
            </div>
          </div>
        </article>
      `;
    }).join('');

    scopePhotosList.querySelectorAll('img[data-photoframe-scope-thumb]').forEach((img) => {
      img.addEventListener('error', () => {
        img.classList.add('hidden');
        const wrap = img.closest('.photoframe-scope-photo-thumb');
        const ph = wrap ? wrap.querySelector('.photoframe-scope-photo-placeholder') : null;
        if (ph) ph.classList.remove('hidden');
      });
      img.addEventListener('load', () => {
        const wrap = img.closest('.photoframe-scope-photo-thumb');
        const ph = wrap ? wrap.querySelector('.photoframe-scope-photo-placeholder') : null;
        if (ph) ph.classList.add('hidden');
        img.classList.remove('hidden');
      });
    });

    scopePhotosList.querySelectorAll('[data-photoframe-scope-photo-card]').forEach((card) => {
      const pid = Number(card.getAttribute('data-photoframe-scope-photo-card') || 0) || 0;
      if (!pid) return;
      let lpTimer = null;
      let lpActivated = false;
      let lpStartX = 0;
      let lpStartY = 0;
      const lpThreshold = 520;
      const cancelLongPress = () => {
        if (lpTimer) {
          clearTimeout(lpTimer);
          lpTimer = null;
        }
      };

      card.addEventListener('pointerdown', (ev) => {
        if (ev.button != null && Number(ev.button) !== 0) return;
        if (scopePhotoSelectMode) {
          const pointerType = String((ev && ev.pointerType) || '').toLowerCase();
          const isTouchLike = pointerType === 'touch' || pointerType === 'pen' || !pointerType;
          if (!isTouchLike) startScopePhotoDragSelection(ev, card, null);
          return;
        }
        lpActivated = false;
        lpStartX = Number(ev.clientX || 0);
        lpStartY = Number(ev.clientY || 0);
        lpTimer = window.setTimeout(() => {
          lpActivated = true;
          setScopePhotoSelectMode(true);
          setScopePhotoSelection(pid, true, card);
          startScopePhotoDragSelection(ev, card, true);
        }, lpThreshold);
      });

      card.addEventListener('pointermove', (ev) => {
        if (!lpTimer) return;
        const dx = Number(ev.clientX || 0) - lpStartX;
        const dy = Number(ev.clientY || 0) - lpStartY;
        if (Math.hypot(dx, dy) > 10) cancelLongPress();
      });

      ['pointerup', 'pointercancel', 'pointerleave'].forEach((evtName) => {
        card.addEventListener(evtName, cancelLongPress);
      });

      card.addEventListener('click', (ev) => {
        if (Date.now() < scopePhotoDragSuppressClickUntil) {
          ev.preventDefault();
          ev.stopPropagation();
          return;
        }
        if (lpActivated) {
          lpActivated = false;
          ev.preventDefault();
          ev.stopPropagation();
          return;
        }
        if (!scopePhotoSelectMode) return;
        setScopePhotoSelection(pid, !scopePhotosSelected.has(pid), card);
        ev.preventDefault();
        ev.stopPropagation();
      });
    });
    updateScopeSelectedCount();
  };

  const loadScopeFolders = async () => {
    if (Array.isArray(scopeFolderOptions) && scopeFolderOptions.length) return;
    const res = await fetch('/api/photoframes/available-folders');
    let data = null;
    try {
      const ct = String(res.headers.get('content-type') || '');
      data = ct.includes('application/json') ? await res.json() : null;
    } catch (_) {
      data = null;
    }
    if (!res.ok || !data || !data.ok) {
      throw new Error((data && data.error) ? String(data.error) : tr('photoframe_scope_load_failed'));
    }
    scopeFolderOptions = Array.isArray(data.items) ? data.items.map((v) => String(v || '').trim()).filter(Boolean) : [];
  };

  const loadScopePhotos = async (queryText = '') => {
    scopePhotoQueryText = String(queryText || '').trim();
    const qs = new URLSearchParams();
    qs.set('limit', '220');
    const selectedOnly = String(scopePhotoFolderPath || '').trim() === SCOPE_SELECTED_FOLDER_KEY;
    if (selectedOnly) {
      const ids = Array.from(scopeSelectedBucketIds || [])
        .map((v) => Number(v))
        .filter((v) => Number.isFinite(v) && v > 0)
        .slice(0, 900);
      if (!ids.length) {
        scopePhotoOptions = [];
        return;
      }
      qs.set('ids', ids.join(','));
    } else {
      if (scopePhotoQueryText) qs.set('q', scopePhotoQueryText);
      if (String(scopePhotoFolderPath || '').trim()) qs.set('folder', String(scopePhotoFolderPath || '').trim());
    }
    const res = await fetch(`/api/photoframes/available-photos?${qs.toString()}`);
    let data = null;
    try {
      const ct = String(res.headers.get('content-type') || '');
      data = ct.includes('application/json') ? await res.json() : null;
    } catch (_) {
      data = null;
    }
    if (!res.ok || !data || !data.ok) {
      throw new Error((data && data.error) ? String(data.error) : tr('photoframe_scope_load_failed'));
    }
    const rawItems = Array.isArray(data.items) ? data.items : [];
    scopePhotoOptions = rawItems.filter((it) => {
      const rel = String(it && it.rel_path ? it.rel_path : '').toLowerCase();
      const extRaw = String((it && (it.ext || rel)) || '').toLowerCase();
      const isVideo = !!(it && it.is_video) || ['.mp4', '.m4v', '.mov', '.avi', '.mkv', '.webm', '.3gp'].some((ext) => extRaw.endsWith(ext));
      return !isVideo;
    });
  };

  const openScopeModal = async (frameId, frameName) => {
    if (!scopeModal) return;
    scopeFrameId = String(frameId || '').trim();
    scopeFrameName = String(frameName || '').trim() || 'Photoframe';
    if (!scopeFrameId) return;
    scopeMode = 'all';
    scopeFoldersSelected = new Set();
    scopePhotosSelected = new Set();
    scopeFolderOptions = [];
    scopePhotoOptions = [];
    scopePhotoFolderPath = SCOPE_SELECTED_FOLDER_KEY;
    scopePhotoQueryText = '';
    scopeSelectedBucketIds = new Set();
    scopePhotoDragSuppressClickUntil = 0;
    setScopePhotoSelectMode(false);
    showScopeError('');
    if (scopePhotoSearchInput) scopePhotoSearchInput.value = '';
    if (scopeTargetEl) scopeTargetEl.textContent = tr('photoframe_scope_target').replace('{name}', scopeFrameName);
    if (scopeModeSel) scopeModeSel.value = 'all';
    renderScopeFolderNav();
    renderScopePhotos();
    updateScopeSelectedCount();
    updateScopeModeVisibility();
    scopeModal.classList.remove('hidden');

    try {
      const res = await fetch(`/api/photoframes/${encodeURIComponent(scopeFrameId)}/scope`);
      let data = null;
      try {
        const ct = String(res.headers.get('content-type') || '');
        data = ct.includes('application/json') ? await res.json() : null;
      } catch (_) {
        data = null;
      }
      if (!res.ok || !data || !data.ok) {
        throw new Error((data && data.error) ? String(data.error) : tr('photoframe_scope_load_failed'));
      }
      scopeMode = String(data.scope_mode || 'all').trim().toLowerCase();
      if (!['all', 'folders', 'photos'].includes(scopeMode)) scopeMode = 'all';
      const folders = Array.isArray(data.allowed_folders) ? data.allowed_folders : [];
      const photoIds = Array.isArray(data.allowed_photo_ids) ? data.allowed_photo_ids : [];
      scopeFoldersSelected = new Set(folders.map((v) => String(v || '').trim()).filter(Boolean));
      scopePhotosSelected = new Set(photoIds.map((v) => Number(v || 0)).filter((v) => Number.isFinite(v) && v > 0));
      scopeSelectedBucketIds = new Set(scopePhotosSelected);
      if (scopeModeSel) scopeModeSel.value = scopeMode;
      updateScopeSelectedCount();
      updateScopeModeVisibility();
      await loadScopeFolders();
      renderScopeFolderNav();
      if (scopeMode === 'folders') {
        renderScopeFolders();
      } else if (scopeMode === 'photos') {
        await loadScopePhotos('');
        renderScopePhotos();
      }
    } catch (e) {
      showScopeError(String((e && e.message) || tr('photoframe_scope_load_failed')));
    }
  };

  const openShowTokenModal = async (frameId, frameName) => {
    if (!showTokenModal) return;
    const id = String(frameId || '').trim();
    if (!id) return;
    const name = String(frameName || '').trim() || 'Photoframe';
    if (showTokenTitle) {
      showTokenTitle.textContent = tr('photoframe_show_token_for').replace('{name}', name);
    }
    if (showTokenInput) showTokenInput.value = tr('photoframe_show_token_loading');
    if (showTokenCopyBtn) showTokenCopyBtn.disabled = true;
    showTokenError('');
    showTokenModal.classList.remove('hidden');

    try {
      const res = await fetch(`/api/photoframes/${encodeURIComponent(id)}/token`);
      let data = null;
      try {
        const ct = String(res.headers.get('content-type') || '');
        data = ct.includes('application/json') ? await res.json() : null;
      } catch (_) {
        data = null;
      }
      if (!res.ok || !data || !data.ok) {
        const message = (data && data.error) ? String(data.error) : tr('photoframe_show_token_failed');
        throw new Error(message);
      }
      const tokenValue = String(data.token || '').trim();
      if (!tokenValue) throw new Error(tr('photoframe_show_token_unavailable'));
      if (showTokenInput) showTokenInput.value = tokenValue;
      if (showTokenCopyBtn) showTokenCopyBtn.disabled = false;
    } catch (e) {
      if (showTokenInput) showTokenInput.value = '';
      showTokenError(String((e && e.message) || tr('photoframe_show_token_failed')));
    }
  };

  const openCreateModal = () => {
    if (!createModal) return;
    shouldRefreshOnClose = false;
    showCreateError('');
    if (resultWrap) resultWrap.classList.add('hidden');
    if (tokenInput) tokenInput.value = '';
    createModal.classList.remove('hidden');
    if (createSubmitBtn) {
      setTimeout(() => {
        try { createSubmitBtn.focus(); } catch {}
      }, 0);
    }
  };

  const closeCreateModal = async () => {
    if (!createModal) return;
    createModal.classList.add('hidden');
    if (shouldRefreshOnClose) await loadPhotoframeStatus();
  };

  if (createBtn) {
    createBtn.addEventListener('click', openCreateModal);
  }
  if (uploadAllBtn) {
    uploadAllBtn.addEventListener('click', async () => {
      const totalCount = Array.isArray(state.photoframeItems) ? state.photoframeItems.length : 0;
      if (totalCount <= 0) return;

      const file = await pickPhotoframeUpdateZip();
      if (!file) return;
      const question = tr('photoframe_update_upload_all_confirm')
        .replace('{count}', String(totalCount))
        .replace('{file}', String(file.name || 'update.zip'));
      if (!window.confirm(question)) return;

      uploadAllBtn.disabled = true;
      uploadAllBtn.classList.add('loading');
      try {
        const formData = new FormData();
        formData.append('package_zip', file, String(file.name || 'update.zip'));
        const res = await fetch('/api/photoframes/update-all', {
          method: 'POST',
          body: formData,
        });
        let data = null;
        try {
          const ct = String(res.headers.get('content-type') || '');
          data = ct.includes('application/json') ? await res.json() : null;
        } catch (_) {
          data = null;
        }
        if (!res.ok || !data || !data.ok) {
          const message = (data && data.error) ? String(data.error) : tr('photoframe_update_upload_all_failed');
          throw new Error(message);
        }
        const queuedCount = Number(data && data.queued_count);
        const safeCount = Number.isFinite(queuedCount) && queuedCount >= 0 ? queuedCount : totalCount;
        showStatus(
          tr('photoframe_update_upload_all_queued').replace('{count}', String(safeCount)),
          'ok'
        );
        await loadPhotoframeStatus();
      } catch (e) {
        showStatus(String((e && e.message) || tr('photoframe_update_upload_all_failed')), 'err');
      } finally {
        uploadAllBtn.disabled = false;
        uploadAllBtn.classList.remove('loading');
      }
    });
  }
  if (createCloseBtn) createCloseBtn.addEventListener('click', closeCreateModal);
  if (createCancelBtn) createCancelBtn.addEventListener('click', closeCreateModal);
  if (createModal) {
    createModal.addEventListener('click', (e) => {
      if (e.target === createModal) closeCreateModal();
    });
    createModal.addEventListener('keydown', async (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        await closeCreateModal();
      }
    });
  }
  if (copyTokenBtn) copyTokenBtn.addEventListener('click', async () => copyText(tokenInput ? tokenInput.value : ''));
  if (showTokenCloseBtn) showTokenCloseBtn.addEventListener('click', closeShowTokenModal);
  if (showTokenModal) {
    showTokenModal.addEventListener('click', (e) => {
      if (e.target === showTokenModal) closeShowTokenModal();
    });
    showTokenModal.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        closeShowTokenModal();
      }
    });
  }
  if (showTokenCopyBtn) showTokenCopyBtn.addEventListener('click', async () => copyText(showTokenInput ? showTokenInput.value : ''));
  if (scopeCloseBtn) scopeCloseBtn.addEventListener('click', closeScopeModal);
  if (scopeCancelBtn) scopeCancelBtn.addEventListener('click', closeScopeModal);
  if (scopeModal) {
    scopeModal.addEventListener('click', (e) => {
      if (e.target === scopeModal) closeScopeModal();
    });
    scopeModal.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        closeScopeModal();
      }
    });
  }
  if (scopeModeSel) {
    scopeModeSel.addEventListener('change', async () => {
      scopeMode = String(scopeModeSel.value || 'all').trim().toLowerCase();
      updateScopeModeVisibility();
      showScopeError('');
      try {
        if (scopeMode === 'folders') {
          await loadScopeFolders();
          renderScopeFolders();
        } else if (scopeMode === 'photos') {
          await loadScopeFolders();
          renderScopeFolderNav();
          await loadScopePhotos(String((scopePhotoSearchInput && scopePhotoSearchInput.value) || ''));
          renderScopePhotos();
        }
      } catch (e) {
        showScopeError(String((e && e.message) || tr('photoframe_scope_load_failed')));
      }
    });
  }
  if (scopeSelectModeBtn) {
    scopeSelectModeBtn.addEventListener('click', () => {
      if (String(scopeMode || '').trim().toLowerCase() !== 'photos') return;
      setScopePhotoSelectMode(!scopePhotoSelectMode);
    });
  }
  if (scopeSelectVisibleBtn) {
    scopeSelectVisibleBtn.addEventListener('click', () => {
      if (String(scopeMode || '').trim().toLowerCase() !== 'photos') return;
      setScopeVisibleSelection(true);
    });
  }
  if (scopeClearVisibleBtn) {
    scopeClearVisibleBtn.addEventListener('click', () => {
      if (String(scopeMode || '').trim().toLowerCase() !== 'photos') return;
      setScopeVisibleSelection(false);
    });
  }
  if (scopePhotoSearchBtn) {
    scopePhotoSearchBtn.addEventListener('click', async () => {
      showScopeError('');
      try {
        await loadScopePhotos(String((scopePhotoSearchInput && scopePhotoSearchInput.value) || ''));
        renderScopePhotos();
      } catch (e) {
        showScopeError(String((e && e.message) || tr('photoframe_scope_load_failed')));
      }
    });
  }
  if (scopePhotoSearchInput) {
    scopePhotoSearchInput.addEventListener('keydown', async (e) => {
      if (e.key !== 'Enter') return;
      e.preventDefault();
      showScopeError('');
      try {
        await loadScopePhotos(String(scopePhotoSearchInput.value || ''));
        renderScopePhotos();
      } catch (err) {
        showScopeError(String((err && err.message) || tr('photoframe_scope_load_failed')));
      }
    });
  }
  if (scopeSaveBtn) {
    scopeSaveBtn.addEventListener('click', async () => {
      if (!scopeFrameId) return;
      scopeSaveBtn.disabled = true;
      scopeSaveBtn.classList.add('loading');
      showScopeError('');
      try {
        const payload = {
          scope_mode: String(scopeModeSel && scopeModeSel.value ? scopeModeSel.value : scopeMode || 'all').trim().toLowerCase(),
          allowed_folders: Array.from(scopeFoldersSelected),
          allowed_photo_ids: Array.from(scopePhotosSelected).map((v) => Number(v)).filter((v) => Number.isFinite(v) && v > 0),
        };
        const res = await fetch(`/api/photoframes/${encodeURIComponent(scopeFrameId)}/scope`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        let data = null;
        try {
          const ct = String(res.headers.get('content-type') || '');
          data = ct.includes('application/json') ? await res.json() : null;
        } catch (_) {
          data = null;
        }
        if (!res.ok || !data || !data.ok) {
          throw new Error((data && data.error) ? String(data.error) : tr('photoframe_scope_save_failed'));
        }
        showStatus(tr('photoframe_scope_saved'), 'ok');
        closeScopeModal();
        await loadPhotoframeStatus();
      } catch (e) {
        showScopeError(String((e && e.message) || tr('photoframe_scope_save_failed')));
      } finally {
        scopeSaveBtn.disabled = false;
        scopeSaveBtn.classList.remove('loading');
      }
    });
  }

  const pickPhotoframeUpdateZip = () => new Promise((resolve) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.zip,application/zip,application/x-zip-compressed';
    input.style.position = 'fixed';
    input.style.left = '-10000px';
    input.style.top = '-10000px';
    const cleanup = () => {
      try {
        input.remove();
      } catch (_) {}
    };
    input.addEventListener('change', () => {
      const file = (input.files && input.files.length) ? input.files[0] : null;
      cleanup();
      resolve(file || null);
    }, { once: true });
    input.addEventListener('cancel', () => {
      cleanup();
      resolve(null);
    }, { once: true });
    document.body.appendChild(input);
    input.click();
  });

  document.querySelectorAll('[data-photoframe-action="scope"]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const frameId = String(btn.getAttribute('data-frame-id') || '').trim();
      const frameName = String(btn.getAttribute('data-frame-name') || '').trim();
      await openScopeModal(frameId, frameName);
    });
  });
  document.querySelectorAll('[data-photoframe-action="open-settings"]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const frameId = String(btn.getAttribute('data-frame-id') || '').trim();
      const settingsUrl = String(btn.getAttribute('data-settings-url') || '').trim();
      if (!settingsUrl || !frameId) {
        showStatus(tr('photoframe_open_settings_failed'), 'err');
        return;
      }

      const preOpened = window.open('', '_blank');
      if (!preOpened) {
        showStatus(tr('photoframe_open_settings_popup_blocked'), 'err');
        return;
      }

      try {
        const doc = preOpened.document;
        if (doc) {
          doc.title = tr('photoframe_open_settings_btn');
          doc.body.innerHTML = `<div style="font-family:Arial,Helvetica,sans-serif;padding:24px;color:#e6edf3;background:#0d1117;min-height:100vh;">${escapeHtml(tr('photoframe_open_settings_waiting'))}</div>`;
        }
      } catch (_) {}

      btn.disabled = true;
      btn.classList.add('loading');
      try {
        showStatus(tr('photoframe_open_settings_waiting'), 'ok');
        const prepareUrl = `/api/photoframes/${encodeURIComponent(frameId)}/settings-ready`;
        const res = await fetch(prepareUrl, { method: 'POST' });
        let data = null;
        try {
          const ct = String(res.headers.get('content-type') || '');
          data = ct.includes('application/json') ? await res.json() : null;
        } catch (_) {
          data = null;
        }
        const fallbackUrl = String((data && data.settings_url) || '').trim();
        if (!res.ok || !data || !data.ok) {
          if (fallbackUrl) {
            preOpened.location.href = fallbackUrl;
            const msg = (data && data.error) ? String(data.error) : tr('photoframe_open_settings_ready');
            showStatus(msg, 'ok');
            return;
          }
          const msg = (data && data.error) ? String(data.error) : tr('photoframe_open_settings_failed');
          throw new Error(msg);
        }

        const targetUrl = fallbackUrl || settingsUrl;
        preOpened.location.href = targetUrl;
        showStatus(tr('photoframe_open_settings_ready'), 'ok');
      } catch (e) {
        try {
          const doc = preOpened.document;
          if (doc) {
            doc.title = tr('photoframe_open_settings_failed');
            doc.body.innerHTML = `<div style="font-family:Arial,Helvetica,sans-serif;padding:24px;color:#f8d7da;background:#2a0f12;min-height:100vh;">${escapeHtml(String((e && e.message) || tr('photoframe_open_settings_failed')))}</div>`;
          }
        } catch (_) {}
        showStatus(String((e && e.message) || tr('photoframe_open_settings_failed')), 'err');
      } finally {
        btn.disabled = false;
        btn.classList.remove('loading');
      }
    });
  });
  document.querySelectorAll('[data-photoframe-action="show-token"]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const frameId = String(btn.getAttribute('data-frame-id') || '').trim();
      const frameName = String(btn.getAttribute('data-frame-name') || '').trim();
      await openShowTokenModal(frameId, frameName);
    });
  });
  document.querySelectorAll('[data-photoframe-action="toggle-preview"]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const frameId = String(btn.getAttribute('data-frame-id') || '').trim();
      if (!frameId) return;
      const map = (state.photoframePreviewHiddenById && typeof state.photoframePreviewHiddenById === 'object')
        ? { ...state.photoframePreviewHiddenById }
        : {};
      const currentlyHidden = !!map[frameId];
      if (currentlyHidden) delete map[frameId];
      else map[frameId] = true;
      state.photoframePreviewHiddenById = map;
      _savePhotoframePreviewUiState();
      if (state.view === 'photoframe') renderGrid();
    });
  });
  document.querySelectorAll('[data-photoframe-action="trigger-update-upload"]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const frameId = String(btn.getAttribute('data-frame-id') || '').trim();
      const frameName = String(btn.getAttribute('data-frame-name') || 'Photoframe').trim();
      if (!frameId) return;

      const file = await pickPhotoframeUpdateZip();
      if (!file) return;
      const question = tr('photoframe_update_upload_confirm')
        .replace('{name}', frameName || 'Photoframe')
        .replace('{file}', String(file.name || 'update.zip'));
      if (!window.confirm(question)) return;

      btn.disabled = true;
      btn.classList.add('loading');
      try {
        const formData = new FormData();
        formData.append('package_zip', file, String(file.name || 'update.zip'));
        const res = await fetch(`/api/photoframes/${encodeURIComponent(frameId)}/update`, {
          method: 'POST',
          body: formData,
        });
        let data = null;
        try {
          const ct = String(res.headers.get('content-type') || '');
          data = ct.includes('application/json') ? await res.json() : null;
        } catch (_) {
          data = null;
        }
        if (!res.ok || !data || !data.ok) {
          const message = (data && data.error) ? String(data.error) : tr('photoframe_update_upload_failed');
          throw new Error(message);
        }
        showStatus(tr('photoframe_update_upload_queued'), 'ok');
        await loadPhotoframeStatus();
      } catch (e) {
        showStatus(String((e && e.message) || tr('photoframe_update_upload_failed')), 'err');
      } finally {
        btn.disabled = false;
        btn.classList.remove('loading');
      }
    });
  });
  document.querySelectorAll('[data-photoframe-action="restart-kiosk"]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const frameId = String(btn.getAttribute('data-frame-id') || '').trim();
      const frameName = String(btn.getAttribute('data-frame-name') || 'Photoframe').trim();
      if (!frameId) return;

      const question = tr('photoframe_restart_kiosk_confirm')
        .replace('{name}', frameName || 'Photoframe');
      if (!window.confirm(question)) return;

      btn.disabled = true;
      btn.classList.add('loading');
      try {
        const res = await fetch(`/api/photoframes/${encodeURIComponent(frameId)}/restart`, {
          method: 'POST',
        });
        let data = null;
        try {
          const ct = String(res.headers.get('content-type') || '');
          data = ct.includes('application/json') ? await res.json() : null;
        } catch (_) {
          data = null;
        }
        if (!res.ok || !data || !data.ok) {
          const message = (data && data.error) ? String(data.error) : tr('photoframe_restart_kiosk_failed');
          throw new Error(message);
        }
        showStatus(tr('photoframe_restart_kiosk_queued'), 'ok');
        await loadPhotoframeStatus();
      } catch (e) {
        showStatus(String((e && e.message) || tr('photoframe_restart_kiosk_failed')), 'err');
      } finally {
        btn.disabled = false;
        btn.classList.remove('loading');
      }
    });
  });
  document.querySelectorAll('[data-photoframe-action="reset-device"]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const frameId = String(btn.getAttribute('data-frame-id') || '').trim();
      const frameName = String(btn.getAttribute('data-frame-name') || 'Photoframe').trim();
      if (!frameId) return;

      const question = tr('photoframe_reset_device_confirm')
        .replace('{name}', frameName || 'Photoframe');
      if (!window.confirm(question)) return;

      btn.disabled = true;
      btn.classList.add('loading');
      try {
        const res = await fetch(`/api/photoframes/${encodeURIComponent(frameId)}/reset`, {
          method: 'POST',
        });
        let data = null;
        try {
          const ct = String(res.headers.get('content-type') || '');
          data = ct.includes('application/json') ? await res.json() : null;
        } catch (_) {
          data = null;
        }
        if (!res.ok || !data || !data.ok) {
          const message = (data && data.error) ? String(data.error) : tr('photoframe_reset_device_failed');
          throw new Error(message);
        }
        showStatus(tr('photoframe_reset_device_queued'), 'ok');
        await loadPhotoframeStatus();
      } catch (e) {
        showStatus(String((e && e.message) || tr('photoframe_reset_device_failed')), 'err');
      } finally {
        btn.disabled = false;
        btn.classList.remove('loading');
      }
    });
  });
  document.querySelectorAll('[data-photoframe-action="cancel-update"]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const frameId = String(btn.getAttribute('data-frame-id') || '').trim();
      const frameName = String(btn.getAttribute('data-frame-name') || 'Photoframe').trim();
      if (!frameId) return;

      const question = tr('photoframe_update_cancel_confirm')
        .replace('{name}', frameName || 'Photoframe');
      if (!window.confirm(question)) return;

      btn.disabled = true;
      btn.classList.add('loading');
      try {
        const res = await fetch(`/api/photoframes/${encodeURIComponent(frameId)}/update/cancel`, {
          method: 'POST',
        });
        let data = null;
        try {
          const ct = String(res.headers.get('content-type') || '');
          data = ct.includes('application/json') ? await res.json() : null;
        } catch (_) {
          data = null;
        }
        if (!res.ok || !data || !data.ok) {
          const message = (data && data.error) ? String(data.error) : tr('photoframe_update_cancel_failed');
          throw new Error(message);
        }
        showStatus(tr('photoframe_update_cancel_done'), 'ok');
        await loadPhotoframeStatus();
      } catch (e) {
        showStatus(String((e && e.message) || tr('photoframe_update_cancel_failed')), 'err');
      } finally {
        btn.disabled = false;
        btn.classList.remove('loading');
      }
    });
  });
  document.querySelectorAll('[data-photoframe-action="delete-token"]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const frameId = String(btn.getAttribute('data-frame-id') || '').trim();
      const frameName = String(btn.getAttribute('data-frame-name') || 'Photoframe').trim();
      if (!frameId) return;
      const question = tr('photoframe_delete_confirm').replace('{name}', frameName || 'Photoframe');
      if (!window.confirm(question)) return;

      btn.disabled = true;
      try {
        const res = await fetch(`/api/photoframes/${encodeURIComponent(frameId)}`, { method: 'DELETE' });
        let data = null;
        try {
          const ct = String(res.headers.get('content-type') || '');
          data = ct.includes('application/json') ? await res.json() : null;
        } catch (_) {
          data = null;
        }
        if (!res.ok || !data || !data.ok) {
          const message = (data && data.error) ? String(data.error) : tr('photoframe_delete_failed');
          throw new Error(message);
        }
        showStatus(tr('photoframe_delete_done'), 'ok');
        await loadPhotoframeStatus();
      } catch (e) {
        showStatus(String((e && e.message) || tr('photoframe_delete_failed')), 'err');
      } finally {
        btn.disabled = false;
      }
    });
  });

  if (createSubmitBtn) {
    createSubmitBtn.addEventListener('click', async () => {
      showCreateError('');
      createSubmitBtn.disabled = true;
      createSubmitBtn.classList.add('loading');
      createSubmitBtn.textContent = tr('photoframe_create_submit_loading');
      try {
        const res = await fetch('/api/photoframes', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({}),
        });
        let data = null;
        try {
          const ct = String(res.headers.get('content-type') || '');
          data = ct.includes('application/json') ? await res.json() : null;
        } catch (_) {
          data = null;
        }
        if (!res.ok || !data || !data.ok) {
          const message = (data && data.error) ? String(data.error) : tr('photoframe_create_failed');
          showCreateError(message);
          return;
        }

        const tokenValue = String(data.token || '').trim();
        if (tokenInput) tokenInput.value = tokenValue;
        if (resultWrap) resultWrap.classList.remove('hidden');
        shouldRefreshOnClose = true;
        showStatus(tr('photoframe_create_saved_ok'), 'ok');
      } catch (e) {
        const msg = String((e && e.message) || '').trim() || tr('photoframe_create_failed');
        showCreateError(msg);
      } finally {
        createSubmitBtn.disabled = false;
        createSubmitBtn.classList.remove('loading');
        createSubmitBtn.textContent = tr('photoframe_create_submit');
      }
    });
  }
}

function renderEmpty(message) {
  els.empty.innerHTML = `<div>${message}</div>`;
  els.empty.classList.remove("hidden");
}

function hideEmpty() {
  els.empty.classList.add("hidden");
}

function setDetail(item) {
  if (!item) {
    els.detailEmpty.classList.remove("hidden");
    els.detailContent.classList.add("hidden");
    return;
  }

  els.detailEmpty.classList.add("hidden");
  els.detailContent.classList.remove("hidden");

  if (item.thumb_url) {
    els.detailThumb.src = item.thumb_url;
    els.detailThumb.style.display = "block";
  } else {
    els.detailThumb.removeAttribute("src");
    els.detailThumb.style.display = "none";
  }

  els.detailName.textContent = item.filename || "-";
  els.detailPath.textContent = item.rel_path || "-";
  const capturedDisplay = item.captured_at || item.modified_fs || item.created_fs;
  const capturedParts = fmtDateParts(capturedDisplay);
  els.detailDate.textContent = capturedParts.date;
  if (els.detailTime) els.detailTime.textContent = capturedParts.time;
  // Prefill date editor
  try {
    const iso = (item.captured_at || item.modified_fs || item.created_fs || '').toString();
    if (els.dateInput && iso) {
      const d = new Date(iso);
      const y = d.getFullYear();
      const m = String(d.getMonth()+1).padStart(2,'0');
      const da = String(d.getDate()).padStart(2,'0');
      const hh = String(d.getHours()).padStart(2,'0');
      const mm = String(d.getMinutes()).padStart(2,'0');
      els.dateInput.value = `${y}-${m}-${da}T${hh}:${mm}`;
    }
  } catch {}
  els.detailSize.textContent = fmtBytes(item.file_size);
  els.detailDims.textContent = fmtDims(item.width, item.height);
  els.detailDevice.textContent = (item.device_label || [item.camera_make, item.camera_model].filter(Boolean).join(" ") ) || "-";
  els.detailLens.textContent = (item.lens_label || item.lens_model) || "-";
  try {
    const uploadedBy = String(item && item.uploaded_by ? item.uploaded_by : '').trim();
    if (els.detailUploader) els.detailUploader.textContent = uploadedBy || '-';
  } catch {}
  if (item.gps_lat != null && item.gps_lon != null) {
    els.detailGps.textContent = `${Number(item.gps_lat).toFixed(5)}, ${Number(item.gps_lon).toFixed(5)}`;
  } else {
    els.detailGps.textContent = item.gps_name || "-";
  }
  const aiCaptionText = _formatAiCaptionText(item);
  const aiTagsText = _formatAiTagsText(item);
  if (els.detailAiCaption) {
    els.detailAiCaption.textContent = aiCaptionText;
    els.detailAiCaption.title = aiCaptionText === "-" ? "" : aiCaptionText;
  }
  els.detailAiTags.textContent = aiTagsText;
  els.detailAiTags.title = aiTagsText === "-" ? "" : aiTagsText;
  const conversion = _getItemConversionInfo(item);
  if (els.detailConvertedRow) els.detailConvertedRow.classList.toggle('hidden', !conversion.converted);
  if (els.detailConverted) els.detailConverted.textContent = conversion.converted ? conversion.label : '-';
  const geo = (item.metadata_json && item.metadata_json.geo) ? item.metadata_json.geo : {};
  els.detailCountry.textContent = geo.country || "-";
  els.detailCity.textContent = geo.city || "-";
  renderWeatherInfo(item);
  els.rawMeta.textContent = JSON.stringify(item.metadata_json || {}, null, 2);
  els.favoriteBtn.textContent = item.favorite ? "★" : "☆";

  // Click on thumbnail in detail opens viewer
  els.detailThumb.onclick = () => {
    const idx = state.items.findIndex(i => i.id === item.id);
    if (idx >= 0) {
      state.viewerItems = null;
      openViewer(idx);
    }
  };
}

function getSizeLabel(w, h) {
  if (!w || !h) return "";
  const area = w * h;
  if (area >= 2500 * 2500) return "XL";
  if (area >= 1200 * 1200) return "M";
  if (area >= 600 * 600) return "SM";
  return "XS";
}

function cardHTML(item) {
  const extRaw = String((item && (item.ext || item.filename || item.rel_path)) || '').toLowerCase();
  const isGif = extRaw.endsWith('.gif');
  const selectBadge = `<span class="photo-select-badge">✓</span>`;
  const thumb = item.thumb_url
    ? `<div class="card-thumb"><img loading="lazy" decoding="async" src="${item.thumb_url}" alt="">${selectBadge}</div>`
    : `<div class="card-thumb placeholder">${item.is_video ? '🎬 Video' : (isGif ? 'GIF' : escapeHtml(tr('no_thumb')))}${selectBadge}</div>`;
  const videoOverlay = item.is_video
    ? `<div class="video-badge" aria-label="Video" title="Video"><span class="video-badge-icon" aria-hidden="true"></span></div>`
    : "";
  const gifOverlay = (!item.is_video && isGif)
    ? `<div class="gif-badge" aria-label="GIF" title="GIF">GIF</div>`
    : "";
  const uploadedByRaw = String(item && item.uploaded_by ? item.uploaded_by : '').trim();
  const uploadedBy = uploadedByRaw ? escapeHtml(uploadedByRaw) : '';
  const uploaderTag = uploadedBy
    ? `<div class="uploader-badge" title="Uploadet af ${uploadedBy}">👤 ${uploadedBy}</div>`
    : "";

  // Gridkort uden extra tekst/metadata – kun selve billedet
  return `${thumb}${videoOverlay}${gifOverlay}${uploaderTag}`;
}

// Render a large People list in small chunks to avoid UI jank/crashes
function appendPeopleInChunks(people, chunkSize = 48) {
  if (!els.grid) return;
  let index = 0;
  // Queue for sequential image loading (1 at a time)
  const pendingImgs = [];
  let imgLoading = false;

  function _ensureImgStyles(img) {
    try {
      if (!img) return;
      // Guarantee correct cover/crop immediately
      img.style.width = '100%';
      img.style.height = '100%';
      img.style.objectFit = 'cover';
      img.style.objectPosition = 'center center';
      img.style.display = 'block';
    } catch {}
  }

  const currentEpoch = peopleRenderEpoch;
  function loadNextImg() {
    if (!pendingImgs.length) { imgLoading = false; return; }
    imgLoading = true;
    const img = pendingImgs.shift();
    if (!img) { loadNextImg(); return; }
    const src = img.getAttribute('data-src');
    if (!src) { loadNextImg(); return; }
    const pollFaceReady = (imgEl) => {
      try {
        const attrFid = String((imgEl && imgEl.getAttribute('data-face-id')) || '').trim();
        const u = String((imgEl && (imgEl.currentSrc || imgEl.src)) || '').trim();
        const m = u.match(/\/api\/face-thumb\/(\d+)/) || String(imgEl.getAttribute('data-src') || '').match(/\/api\/face-thumb\/(\d+)/);
        const fid = attrFid || (m && m[1]) || '';
        if (!fid) return;
        let tries = 0;
        const maxTries = 120;
        const startTick = () => {
          if (currentEpoch !== peopleRenderEpoch) return; // view changed
          if (!document.body.contains(imgEl)) return; // removed from DOM
          if (activeFacePolls >= MAX_ACTIVE_FACE_POLLS) { setTimeout(startTick, 120); return; }
          activeFacePolls += 1;
          tick();
        };
        const tick = async () => {
          tries += 1;
          try {
            const r = await fetch(`/api/face-thumb/status/${fid}`);
            const d = await r.json();
            if (r.ok && d && d.ok && d.ready && d.url) {
              imgEl.src = d.url; // swap in the cropped face
              activeFacePolls = Math.max(0, activeFacePolls - 1);
              return;
            }
          } catch {}
          if (tries < maxTries && currentEpoch === peopleRenderEpoch && document.body.contains(imgEl)) {
            const delay = Math.min(2000, 180 + tries * 120);
            setTimeout(tick, delay);
          } else {
            activeFacePolls = Math.max(0, activeFacePolls - 1);
          }
        };
        // Start almost immediately so crop appears fast
        setTimeout(startTick, 120);
      } catch {}
    };

    const cleanup = () => {
      img.removeEventListener('load', onload);
      img.removeEventListener('error', onerror);
      img.removeEventListener('abort', onerror);
    };
    const onload = () => {
      // Kick quick face-ready polling so crop swaps in ASAP
      pollFaceReady(img);
      cleanup();
      loadNextImg();
    };
    const onerror = () => {
      // Even if the first fetch failed, try polling face-ready and retry later
      pollFaceReady(img);
      const retries = Number(img.getAttribute('data-retries') || '0');
      if (retries < 3) {
        img.setAttribute('data-retries', String(retries + 1));
        // push back for a later retry
        setTimeout(() => { pendingImgs.push(img); if (!imgLoading) loadNextImg(); }, 400);
      }
      cleanup();
      loadNextImg();
    };
    img.addEventListener('load', onload, { once: true });
    img.addEventListener('error', onerror, { once: true });
    img.addEventListener('abort', onerror, { once: true });
    // Defer a tiny bit to allow layout to settle
    (window.requestIdleCallback || window.requestAnimationFrame)(() => {
      _ensureImgStyles(img);
      // Force a reflow so object-fit takes effect immediately on some browsers
      try { void img.offsetWidth; } catch {}
      img.setAttribute('src', src);
      img.removeAttribute('data-src');
    });
  }

  function enqueueImgsFrom(node) {
    // Find any newly added images with data-src
    const imgs = node.querySelectorAll('img[data-src]');
    imgs.forEach((im) => pendingImgs.push(im));
    if (!imgLoading) loadNextImg();
  }
  function step() {
    const end = Math.min(index + chunkSize, people.length);
    const frag = document.createDocumentFragment();
    for (; index < end; index += 1) {
      const p = people[index];
      const card = document.createElement('article');
      card.className = 'photo-card';
      card.setAttribute('data-person-id', String(p.id));
      const maybeName = String(p.maybe_person_name || '').trim();
      const hasMaybeName = !!maybeName;
      const maybeScoreVal = Number(p.maybe_score);
      const maybeScorePct = Number.isFinite(maybeScoreVal) ? Math.round(maybeScoreVal * 100) : null;
      const titleText = hasMaybeName
        ? tr('person_maybe_name').replace('{name}', maybeName)
        : String(p.name || tr('person_unknown'));
      const faceMatch = String(p.thumb_url || '').match(/\/api\/face-thumb\/(\d+)/);
      const faceAttr = faceMatch ? ` data-face-id="${faceMatch[1]}"` : '';
      const imgHtml = p.thumb_url
        ? `<img data-src="${p.thumb_url}"${faceAttr} alt="${escapeHtml(p.name || '')}" loading="lazy" decoding="async" style="width:100%;height:100%;object-fit:cover;object-position:center center;display:block;">`
        : `<div class="card-thumb placeholder">🙂</div>`;
      const maybePill = hasMaybeName
        ? `<span class="pill person-maybe-pill">${escapeHtml(maybeScorePct === null ? '~' : `~${maybeScorePct}%`)}</span>`
        : '';
      card.innerHTML = `
        <div class="card-thumb">${imgHtml}</div>
        <div class="card-body">
          <h4 class="card-title ${hasMaybeName ? 'person-maybe-title' : ''}">${escapeHtml(titleText)}</h4>
          <div class="card-meta"><span>${p.count||0} ${escapeHtml(tr('person_count_suffix'))}</span></div>
          <div class="pills">${maybePill}${p.hidden ? `<span class="pill">${escapeHtml(tr('person_hidden_badge'))}</span>` : ''}</div>
          <div class="actions" style="margin-top:6px;display:flex;gap:6px;">
            ${hasMaybeName && p.id !== 'unknown' ? `<button class="btn tiny primary" data-act="accept-maybe">${escapeHtml(tr('person_btn_accept_maybe'))}</button>` : ''}
            <button class="btn tiny" data-act="rename">${escapeHtml(tr('person_btn_rename'))}</button>
            ${p.id==='unknown' ? '' : `<button class="btn tiny ${p.hidden?'':'danger'}" data-act="${p.hidden?'unhide':'hide'}">${escapeHtml(p.hidden ? tr('person_btn_unhide') : tr('person_btn_hide'))}</button>`}
          </div>
        </div>
      `;
      card.querySelectorAll('img').forEach((el) => { el.setAttribute('draggable', 'false'); });
      card.addEventListener('click', (e)=>{
        if (e.target && e.target.closest('[data-act]')) return;
        if (p.id === 'unknown') loadPersonPhotos('unknown', tr('person_unknown'));
        else loadPersonPhotos(p.id, p.name);
      });
      const acceptMaybeBtn = card.querySelector('[data-act="accept-maybe"]');
      if (acceptMaybeBtn) acceptMaybeBtn.addEventListener('click', async (e)=>{
        e.preventDefault(); e.stopPropagation();
        if (!hasMaybeName) return;
        await renameOrMergePerson(p.id, maybeName);
      });
      const renBtn = card.querySelector('[data-act="rename"]');
      if (renBtn) renBtn.addEventListener('click', async (e)=>{ e.preventDefault(); e.stopPropagation(); openPersonRenameMenu(e.currentTarget, p); });
      const hideBtn = card.querySelector('[data-act="hide"]');
      if (hideBtn) hideBtn.addEventListener('click', async (e)=>{
        e.preventDefault(); e.stopPropagation();
        if (!confirm(tr('person_hide_confirm'))) return;
        try {
          const r = await fetch(`/api/people/${p.id}/hide`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ hidden: true })});
          const d = await r.json();
          if (!r.ok || !d.ok) { showStatus(d.error || tr('person_hide_failed'), 'err'); return; }
          showStatus(tr('person_hidden_ok'), 'ok');
          // Fjern kortet med det samme for en snappy oplevelse
          const node = document.querySelector(`.photo-card[data-person-id="${Number(p.id)}"]`);
          if (node && node.parentElement) node.parentElement.removeChild(node);
        } catch { showStatus(tr('person_hide_error'), 'err'); }
      });
      const unhideBtn = card.querySelector('[data-act="unhide"]');
      if (unhideBtn) unhideBtn.addEventListener('click', async (e)=>{
        e.preventDefault(); e.stopPropagation();
        try {
          const r = await fetch(`/api/people/${p.id}/hide`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ hidden: false })});
          const d = await r.json();
          if (!r.ok || !d.ok) { showStatus(d.error || tr('person_unhide_failed'), 'err'); return; }
          showStatus(tr('person_unhidden_ok'), 'ok');
          const cardEl = e.currentTarget.closest('.photo-card');
          if (cardEl) {
            const pillWrap = cardEl.querySelector('.pills');
            if (pillWrap) pillWrap.innerHTML = '';
            const btn = cardEl.querySelector('[data-act="unhide"]');
            if (btn) { btn.setAttribute('data-act','hide'); btn.classList.remove('danger'); btn.textContent = tr('person_btn_hide'); }
          }
        } catch { showStatus(tr('person_unhide_error'), 'err'); }
      });
      frag.appendChild(card);
    }
    els.grid.appendChild(frag);
    enqueueImgsFrom(els.grid);
    if (index < people.length) {
      // Yield to browser to paint and handle input, then continue
      (window.requestIdleCallback || window.requestAnimationFrame)(step);
    }
  }
  step();
}

let photoLoadMoreObserver = null;

function estimateMapperPageLimit() {
  try {
    const gridWidth = Math.max(0, (els.grid && els.grid.clientWidth) || window.innerWidth || 0);
    const rootStyle = getComputedStyle(document.documentElement);
    const gridStyle = els.grid ? getComputedStyle(els.grid) : null;
    const tileWidth = parseFloat(rootStyle.getPropertyValue('--folder-tile')) || 230;
    const gap = gridStyle ? (parseFloat(gridStyle.columnGap || gridStyle.gap) || 12) : 12;
    const cols = Math.max(1, Math.floor((gridWidth + gap) / (tileWidth + gap)));
    const rows = Math.max(1, Number(state.mapperPageRows || 5));
    return Math.max(cols * rows, cols);
  } catch {
    return 30;
  }
}

function appendPhotoLoadMoreButton(id, expectedView) {
  try {
    if (photoLoadMoreObserver) photoLoadMoreObserver.disconnect();
  } catch {}
  if (!els.grid) return;
  const old = document.getElementById(id);
  if (old && old.parentNode) old.parentNode.removeChild(old);
  if (!state.photosHasMore) return;
  const btn = document.createElement('button');
  btn.id = id;
  btn.className = 'btn';
  btn.style.margin = '16px auto';
  btn.style.display = 'block';
  btn.textContent = 'Indlæs flere…';
  const loadMore = async () => {
    if (state.photosLoading || state.view !== expectedView || !state.photosHasMore) return;
    btn.disabled = true;
    btn.classList.add('loading');
    try {
      await loadPhotos(true);
    } finally {
      btn.disabled = false;
      btn.classList.remove('loading');
    }
  };
  btn.addEventListener('click', loadMore);
  els.grid.appendChild(btn);
  if ('IntersectionObserver' in window) {
    photoLoadMoreObserver = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) loadMore();
    }, { rootMargin: '700px 0px' });
    photoLoadMoreObserver.observe(btn);
  }
}

function renderGrid() {
  // Toggle fixed-width columns for folder view
  if (els.grid) els.grid.classList.toggle("folders-view", state.view === "mapper");
  if (els.mapperTools) els.mapperTools.classList.add("hidden");
  // Always hide special panels first
  if (els.settingsPanel) els.settingsPanel.classList.add("hidden");
  if (els.placesMapWrap) els.placesMapWrap.classList.add("hidden");
  // Handle Settings view
  if (state.view === "settings") {
    els.grid.innerHTML = "";
    if (els.settingsPanel) els.settingsPanel.classList.remove("hidden");
    const activeBtn = document.querySelector('#settingsPanel .tab-btn.active');
    const activeTab = activeBtn ? activeBtn.getAttribute('data-tab') : null;
    if (activeTab) {
      document.querySelectorAll('#settingsPanel .tab-panel').forEach(p => {
        p.classList.toggle('hidden', p.dataset.tabpanel !== activeTab);
      });
    }
    return;
  }
  // Handle Photoframe view (placeholder for upcoming Pi integration)
  if (state.view === "photoframe") {
    if (els.searchShell) els.searchShell.style.display = 'none';
    if (els.sort) els.sort.style.display = 'none';
    const peopleBtn = document.getElementById('peopleMatchScanBtn');
    if (peopleBtn) peopleBtn.style.display = 'none';
    if (els.statHiddenToggle) els.statHiddenToggle.style.display = 'none';
    els.grid.classList.remove('timeline-wrap');
    // Let photoframe panel take full width; card layout is handled by .photoframe-grid.
    els.grid.classList.remove('gallery-grid');
    renderPhotoframePanel();
    hideEmpty();
    setDetail(null);
    renderStats();
    return;
  }
  // Handle Places (Steder) view: show map with clusters
  if (state.view === "steder") {
    if (els.placesMapWrap) els.placesMapWrap.classList.remove("hidden");
    els.grid.innerHTML = ""; // hide gallery
    initOrUpdatePlacesMap();
    return;
  }
  // Handle People (Personer) view
  if (state.view === 'personer') {
    if (els.statHiddenToggle) {
      els.statHiddenToggle.style.display = '';
      if (els.showHiddenToggle) els.showHiddenToggle.checked = !!state.showHiddenPeople;
    }
    els.grid.innerHTML = '';
      els.grid.classList.remove('timeline-wrap');
      els.grid.classList.add('gallery-grid');
    // Hide global search in People view and place Match-scan in the content header (next to where search normally sits)
    (function ensurePeopleHeaderActions(){
      if (els.searchShell) els.searchShell.style.display = 'none';
      // Remove any topbar button if we previously added it
      const oldTop = document.getElementById('peopleMatchScanTopBtn');
      if (oldTop && oldTop.parentNode) { try { oldTop.parentNode.removeChild(oldTop); } catch {} }

      const header = document.querySelector('.content-header');
      if (!header) return;
      let actions = document.getElementById('peopleHeaderActions');
      if (!actions) {
        actions = document.createElement('div');
        actions.id = 'peopleHeaderActions';
        actions.style.display = 'flex';
        actions.style.alignItems = 'center';
        actions.style.gap = '8px';
        actions.style.marginLeft = 'auto';
        header.appendChild(actions);
      }
      let btn = document.getElementById('peopleMatchScanBtn');
      if (!btn) {
        btn = document.createElement('button');
        btn.id = 'peopleMatchScanBtn';
        btn.className = 'btn';
        btn.textContent = tr('people_match_btn');
        btn.addEventListener('click', ()=> matchUnknownFaces(1000));
        actions.appendChild(btn);
      } else {
        btn.textContent = tr('people_match_btn');
        btn.style.display = '';
      }
    })();
    const people = state.personView.mode === 'list' ? (state.people || []) : [];
    if (state.personView.mode === 'list') {
      if (!people.length) {
        renderEmpty(tr('empty_people'));
        renderStats();
        setDetail(null);
        return;
      }
      hideEmpty();
      // New people render epoch: cancel any leftover polling from previous view
      peopleRenderEpoch += 1;
      activeFacePolls = 0;
      // Render in chunks to avoid main-thread spikes when many people exist
      appendPeopleInChunks(people);
      renderStats();
      return;
    } else if (state.personView.mode === 'photos') {
      hideEmpty();
      // Ensure the container is not a gallery grid so inner grid can span full width
      els.grid.classList.remove('gallery-grid');
      const head = document.createElement('div');
      head.className = 'timeline-header';
      head.style.cursor = 'pointer';
      head.textContent = `← ${state.personView.personName || 'Person'}`;
      head.addEventListener('click', ()=>{ state.personView = { mode:'list', personId:null, personName:null }; loadPeople(); });
      els.grid.appendChild(head);
      const wrap = document.createElement('div');
      wrap.className = 'timeline-grid';
      els.grid.appendChild(wrap);
      (state.items||[]).forEach(it => appendCardTo(it, wrap));
      renderStats();
      return;
    }
  }
  // Hide hidden-toggle outside People view
  if (state.view !== 'personer' && els.statHiddenToggle) {
    els.statHiddenToggle.style.display = 'none';
  }
  if (state.view !== 'personer') {
    // Show global search again in other views and hide the match-scan btn in header
    if (els.searchShell) els.searchShell.style.display = '';
    if (els.sort) els.sort.style.display = '';
    const hdrBtn = document.getElementById('peopleMatchScanBtn');
    if (hdrBtn) hdrBtn.style.display = 'none';
  }
  // Timeline view: group by year-month headers
  if (state.view === "timeline") {
    els.grid.innerHTML = "";
    // Ensure vertical stacking container (not the gallery grid)
    els.grid.classList.remove('gallery-grid');
    els.grid.classList.add('timeline-wrap');
    hideEmpty();
    const items = state.items.slice();
    if (!items.length) {
      renderEmpty(tr('empty_no_photos'));
      renderStats();
      setDetail(null);
      return;
    }
    const groups = new Map(); // key: YYYY-MM label
    for (const it of items) {
      const d = new Date(it.captured_at || it.modified_fs || it.created_fs || Date.now());
      const y = d.getFullYear();
      const m = d.toLocaleString((state.uiLanguage === 'en') ? 'en-GB' : 'da-DK', { month: "long" });
      const key = `${y}-${String(d.getMonth()+1).padStart(2,'0')}`;
      const label = `${m} ${y}`;
      if (!groups.has(key)) groups.set(key, { label, arr: [] });
      groups.get(key).arr.push(it);
    }
    // Sort groups according to selection (date_desc or date_asc)
    const asc = state.sort === 'date_asc';
    const ordered = Array.from(groups.entries()).sort((a,b)=> {
      if (a[0] === b[0]) return 0;
      return asc ? (a[0] > b[0] ? 1 : -1) : (a[0] < b[0] ? 1 : -1);
    });
    for (const [, grp] of ordered) {
      const h = document.createElement('div');
      h.className = 'timeline-header';
      h.textContent = grp.label;
      const wrap = document.createElement('div');
      wrap.className = 'timeline-grid';
      els.grid.appendChild(h);
      els.grid.appendChild(wrap);
      grp.arr.forEach(it => appendCardTo(it, wrap));
    }
    appendPhotoLoadMoreButton('timelineLoadMoreBtn', 'timeline');
    if (!state.items.some(i => i.id === state.selectedId)) {
      state.selectedId = null; setDetail(null);
    }
    renderStats();
    return;
  }

  // Default views (mapper, etc.)
  els.grid.innerHTML = "";
  if (state.view === "mapper" && els.mapperTools) {
    els.mapperTools.classList.remove("hidden");
  }
  // Restore gallery grid layout for non-timeline views
  els.grid.classList.add('gallery-grid');
  els.grid.classList.remove('timeline-wrap');
  if (!state.items.length && state.view !== "mapper") {
    const msg = state.view === "personer"
      ? tr('empty_people')
      : tr('empty_no_matches');
    renderEmpty(msg);
    renderStats();
    setDetail(null);
    return;
  }
  hideEmpty();

  const items = state.items.slice();
  if (state.view === "mapper") {
    const current = String(state.mapperPath || "");

    // Build child folder list purely from the folder index (fast) — do not scan items
    const childSet = new Set();
    for (const f of (state.mapperFolders || [])) {
      const child = mapperImmediateChildFolder(String(f || ''), current);
      if (child) childSet.add(child);
    }
    const sorted = Array.from(childSet.values()).sort((a, b) => a.localeCompare(b, 'da-DK'));
    if (!sorted.length && !items.length) {
      renderEmpty(tr('empty_no_photos'));
      renderStats();
      setDetail(null);
      return;
    }
    for (const folderPath of sorted) {
      const title = folderPath.split('/').filter(Boolean).pop() || folderPath;
      appendFolderCard(folderPath, [], {
        title,
        onOpen: async () => {
          state.mapperPath = folderPath;
          state.folder = folderPath;
          await loadMapperTools(folderPath);
          await loadPhotos();
        },
      });
    }
    items.forEach(item => appendCard(item));
    appendPhotoLoadMoreButton('mapperLoadMoreBtn', 'mapper');
  } else {
    items.forEach(item => appendCard(item));
  }

  if (!state.items.some(i => i.id === state.selectedId)) {
    state.selectedId = null;
    setDetail(null);
  }
  renderStats();
}

function appendCardTo(item, container) {
  const card = document.createElement("article");
  const isMapperSelected = !!(state.view === 'mapper' && state.mapperSelectedPhotoIds && state.mapperSelectedPhotoIds.has(item.id));
  card.className = "photo-card" + (state.selectedId === item.id ? " active" : "") + (isMapperSelected ? " selected" : "");
  try {
    const photoId = Number(item && item.id);
    if (Number.isFinite(photoId) && photoId > 0) card.setAttribute('data-photo-id', String(photoId));
  } catch {}
  card.innerHTML = cardHTML(item);
  card.querySelectorAll('img').forEach((img) => {
    img.setAttribute('draggable', 'false');
  });
  // Note: photo cards have no folder-name marquee

  // Add Info icon overlay (top-left, on red dot) on mouseover
  const thumb = card.querySelector('.card-thumb');
  // Hide info overlay in mapper selection mode
  const allowInfoOverlay = !(state && state.view === 'mapper' && state.mapperEditMode);
  if (thumb && allowInfoOverlay) {
    // Create info icon
    const infoIcon = document.createElement('div');
    infoIcon.className = 'info-icon-overlay';
    infoIcon.title = 'Info';
    infoIcon.innerHTML = '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="10" cy="10" r="10" fill="#fff"/><text x="10" y="15" text-anchor="middle" font-size="13" fill="#333" font-family="Arial" font-weight="bold">i</text></svg>';
    infoIcon.style.position = 'absolute';
    infoIcon.style.left = '6px';
    infoIcon.style.top = '6px';
    infoIcon.style.zIndex = '3';
    infoIcon.style.cursor = 'pointer';
    infoIcon.style.opacity = '0';
    infoIcon.style.transition = 'opacity 0.15s';
    // Show icon on hover
    card.addEventListener('mouseenter', () => { infoIcon.style.opacity = '1'; });
    card.addEventListener('mouseleave', () => { infoIcon.style.opacity = '0'; });
    // Place icon above the red dot (assume red dot is at 0,0 or adjust as needed)
    thumb.style.position = 'relative';
    thumb.appendChild(infoIcon);
    // Clicking the icon opens the sidebar (detail panel)
    infoIcon.addEventListener('click', (ev) => {
      ev.stopPropagation();
      try { document.body.classList.add('detail-open'); } catch {}
      state.selectedId = item.id;
      setDetail(item);
      // Optionally scroll sidebar into view if needed
      if (els.detailContent) els.detailContent.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
  }
  // If viewing 'Ukendte' person folder, overlay detected face boxes on the thumbnail
  try {
    if (state.personView && state.personView.personId === 'unknown' && item && Array.isArray(item.faces) && item.faces.length) {
      const thumb = card.querySelector('.card-thumb');
      const img = thumb && thumb.querySelector('img');
      if (thumb && img) {
        thumb.style.position = 'relative';
        img.style.objectFit = 'contain';
        img.style.background = '#0d1016';
        const faces = item.faces.slice(0, 2);
        const draw = () => {
          try {
            const cw = thumb.clientWidth; const ch = thumb.clientHeight;
            const iw = img.naturalWidth || (item.width||1); const ih = img.naturalHeight || (item.height||1);
            const scale = Math.min(cw/iw, ch/ih);
            const dw = iw*scale; const dh = ih*scale;
            const offX = (cw - dw)/2; const offY = (ch - dh)/2;
            faces.forEach(fc => {
              const box = document.createElement('div');
              box.style.position = 'absolute';
              box.style.left = `${offX + (fc.x*dw)}px`;
              box.style.top = `${offY + (fc.y*dh)}px`;
              box.style.width = `${fc.w*dw}px`;
              box.style.height = `${fc.h*dh}px`;
              box.style.border = '2px solid #e33';
              box.style.boxShadow = '0 0 0 1px rgba(0,0,0,0.4) inset';
              box.style.pointerEvents = 'none';
              thumb.appendChild(box);
            });
          } catch {}
        };
        if (img.complete) draw(); else img.addEventListener('load', draw, { once: true });
      }
    }
  } catch {}
  card.addEventListener('pointerdown', (ev) => {
    _startMapperDragSelect(ev, card);
  });
  // Single-click opens viewer directly (unless clicking info icon or in select/edit mode)
  card.addEventListener("click", (ev) => {
    // If click was on info icon, ignore (handled above)
    if (ev.target && ev.target.closest && ev.target.closest('.info-icon-overlay')) return;
    if (_consumeMapperDragSelectClickSuppression()) {
      ev.preventDefault();
      ev.stopPropagation();
      return;
    }
    // When in selection mode (mapper edit), clicking should toggle selection instead of opening
    try {
      if (state && state.view === 'mapper' && state.mapperEditMode) {
        if (!state.mapperSelectedPhotoIds) state.mapperSelectedPhotoIds = new Set();
        const isSel = state.mapperSelectedPhotoIds.has(item.id);
        if (isSel) state.mapperSelectedPhotoIds.delete(item.id); else state.mapperSelectedPhotoIds.add(item.id);
        card.classList.toggle('selected', !isSel);
        try { renderMapperContext(state.mapperPath || ''); } catch {}
        ev.preventDefault();
        ev.stopPropagation();
        return;
      }
    } catch {}
    try { document.body.classList.remove('detail-open'); } catch {}
    state.selectedId = item.id;
    const idx = state.items.findIndex(i => i.id === item.id);
    if (idx >= 0) {
      state.viewerItems = null;
      openViewer(idx);
    }
  });
  (container || els.grid).appendChild(card);
}

function appendCard(item){ return appendCardTo(item, els.grid); }

function bindFolderNameMarquee(card, fullText) {
  try {
    if (!card || !window.matchMedia || !window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
    const nameEl = card.querySelector('.folder-name');
    const inner = nameEl ? nameEl.querySelector('.scroll') : null;
    if (!nameEl || !inner) return;
    const full = String(fullText || inner.textContent || '');
    nameEl.setAttribute('title', full);

    const stop = () => {
      try {
        nameEl.classList.remove('marquee-run');
        nameEl.classList.remove('marquee');
        nameEl.style.removeProperty('--fl-shift');
        inner.style.transform = '';
      } catch {}
    };
    const start = () => {
      try {
        const prev = inner.style.display;
        inner.style.display = 'inline-block';
        const delta = Math.max(0, inner.scrollWidth - nameEl.clientWidth);
        inner.style.display = prev;
        if (delta <= 4) {
          stop();
          return;
        }
        nameEl.style.setProperty('--fl-shift', `-${Math.ceil(delta)}px`);
        nameEl.classList.add('marquee');
        // Restart animation cleanly each hover.
        nameEl.classList.remove('marquee-run');
        void nameEl.offsetWidth;
        nameEl.classList.add('marquee-run');
      } catch {
        stop();
      }
    };

    card.addEventListener('mouseenter', start);
    card.addEventListener('mouseleave', stop);
  } catch {}
}

const FOLDER_PREVIEW_STORE_KEY = 'fl_folder_previews_v1';

function invalidateStoredFolderPreviews(folders) {
  const list = Array.isArray(folders) ? folders : [];
  if (!list.length) return;
  // Keep the last good preview visible; the async server refresh replaces it.
}

function mapperImmediateChildFolder(folderPath, parentPath) {
  const f = String(folderPath || '');
  const p = String(parentPath || '');
  if (!f) return null;
  if (!p) {
    const seg = f.split('/').filter(Boolean)[0] || null;
    return seg || null;
  }
  if (f === p || !f.startsWith(p + '/')) return null;
  const rest = f.slice(p.length + 1);
  const seg = rest.split('/').filter(Boolean)[0] || null;
  return seg ? `${p}/${seg}` : null;
}

async function prefetchMapperFolderPreviewsForCurrentPath() {
  if (state.view !== 'mapper') return;
  const current = String(state.mapperPath || '');
  const childSet = new Set();
  for (const f of (state.mapperFolders || [])) {
    const child = mapperImmediateChildFolder(String(f || ''), current);
    if (child) childSet.add(child);
  }
  const folders = Array.from(childSet.values()).sort((a, b) => a.localeCompare(b, 'da-DK'));
  if (!folders.length) return;
  try {
    const res = await fetch(`/api/folder-previews?folders=${encodeURIComponent(folders.join(','))}`);
    const data = await res.json().catch(() => ({}));
    const items = data && data.items && typeof data.items === 'object' ? data.items : {};
    const store = JSON.parse(localStorage.getItem(FOLDER_PREVIEW_STORE_KEY) || '{}') || {};
    let changed = false;
    for (const folder of folders) {
      const urls = Array.isArray(items[folder])
        ? items[folder].map((u) => String(u || '').trim()).filter(Boolean).slice(0, 4)
        : [];
      if (!urls.length) continue;
      store[folder] = urls;
      changed = true;
    }
    if (changed) localStorage.setItem(FOLDER_PREVIEW_STORE_KEY, JSON.stringify(store));
  } catch {}
}

function appendFolderCard(folder, arr, opts = {}) {
  const card = document.createElement("article");
  const isSelected = !!(state.mapperEditMode && state.mapperSelectedFolders && state.mapperSelectedFolders.has(folder));
  card.className = "photo-card folder-card" + (isSelected ? " selected" : "");
  try { card.setAttribute('data-folder', folder); } catch {}
  // Randomize and select unique preview URLs (prefer folder's own items; arr includes subtree)
  const shuffled = (list) => {
    const a = list.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  };
  const toUrl = (p) => p && (p.thumb_url || p.view_url || p.original_url || p.download_url);
  const normFolder = (rel) => {
    let f = String(rel || '');
    f = f.includes('/') ? f.split('/').slice(0, -1).join('/') : '';
    if (f === 'uploads') f = '';
    else if (f.startsWith('uploads/')) f = f.slice('uploads/'.length);
    if (f.startsWith('converted/')) f = f.slice('converted/'.length);
    if (f.startsWith('originals/')) f = f.slice('originals/'.length);
    return f;
  };
  const ownFirst = []; // items whose immediate folder equals this tile
  const descLater = []; // deeper descendants
  for (const it of arr) {
    const u = toUrl(it);
    if (!u) continue;
    const f = normFolder(String(it.rel_path || ''));
    if (f === folder) ownFirst.push({u}); else descLater.push({u});
  }
  // Deduplicate and randomize within priority buckets
  const collect = (list) => {
    const seen = new Set();
    const out = [];
    for (const x of shuffled(list)) { if (x.u && !seen.has(x.u)) { seen.add(x.u); out.push(x.u); } }
    return out;
  };
  const uniqUrls = collect(ownFirst).concat(collect(descLater));

  // Persist selection per folder in localStorage so it stays after refresh
  const loadStore = () => { try { return JSON.parse(localStorage.getItem(FOLDER_PREVIEW_STORE_KEY) || '{}') || {}; } catch { return {}; } };
  const saveStore = (obj) => { try { localStorage.setItem(FOLDER_PREVIEW_STORE_KEY, JSON.stringify(obj)); } catch {} };
  const store = loadStore();
  const stored = Array.isArray(store[folder]) ? store[folder] : null;
  const intersect = (want, avail) => want.filter(u => avail.includes(u));

  // Decide variant: 1 image → full; 2 or 3 images → 2 tall columns; 4+ → 2×2 grid
  let variant = 'v4';
  let useUrls = [];
  const pickFresh = () => {
    if (uniqUrls.length <= 0) return [];
    if (uniqUrls.length === 1) { variant = 'v1'; return [uniqUrls[0]]; }
    if (uniqUrls.length === 2 || uniqUrls.length === 3) { variant = 'v2'; return uniqUrls.slice(0,2); }
    variant = 'v4'; return uniqUrls.slice(0,4);
  };
  const desired = () => {
    if (uniqUrls.length <= 0 && stored && stored.length) {
      return stored.length >= 4 ? 4 : (stored.length >= 2 ? 2 : 1);
    }
    return uniqUrls.length === 1 ? 1 : ((uniqUrls.length === 2 || uniqUrls.length === 3) ? 2 : 4);
  };
  if (stored && stored.length) {
    const candidates = uniqUrls.length ? intersect(stored, uniqUrls) : stored;
    if (candidates.length >= desired()) {
      useUrls = candidates.slice(0, desired());
      variant = (useUrls.length === 1 ? 'v1' : (useUrls.length === 2 ? 'v2' : 'v4'));
    } else {
      useUrls = pickFresh();
      if (useUrls.length) {
        store[folder] = useUrls;
        saveStore(store);
      }
    }
  } else {
    useUrls = pickFresh();
    if (useUrls.length) {
      store[folder] = useUrls;
      saveStore(store);
    }
  }
  const cells = useUrls.map(u => `<img src="${escapeHtml(u)}" alt="">`).join("");
  const title = opts.title || folder;
  const selBadge = state.mapperEditMode ? `<span class="folder-select-badge">${isSelected ? '✓' : ''}</span>` : '';
  const folderTitle = escapeHtml(title || '');
  const hasExplicitCount = (opts && Object.prototype.hasOwnProperty.call(opts, 'count'));
  const countVal = hasExplicitCount ? Number(opts.count || 0) : (Array.isArray(arr) ? arr.length : 0);
  const countLabel = countVal > 0 ? `${countVal} ${countVal === 1 ? 'element' : 'elementer'}` : '';
  const overlay = `<div class="folder-name-overlay"><span class="folder-name"><span class="scroll">${folderTitle}</span></span>${countLabel ? `<span class="folder-count">${escapeHtml(countLabel)}</span>` : ''}</div>`;
  const thumbHtml = (useUrls && useUrls.length)
    ? `<div class="card-thumb folder-mosaic"><div class="folder-grid ${variant}">${cells}</div>${selBadge}${overlay}</div>`
    : `<div class="card-thumb placeholder">${escapeHtml('Ingen billeder')}${overlay}</div>`;
  card.innerHTML = `
    ${thumbHtml}
    <div class="card-body">
      <h4 class="card-title">${folderTitle}</h4>
      <div class="card-meta">
        ${countVal > 0 ? `<span>${countVal} ${countVal === 1 ? 'element' : 'elementer'}</span>` : ''}
        <span>Mapper</span>
      </div>
      </div>`;
  bindFolderNameMarquee(card, title || folder || '');
  card.querySelectorAll('img').forEach((img) => {
    img.setAttribute('draggable', 'false');
  });
  // --- Hold-to-select (long press) for Mapper ---
  let _lpTimer = null;
  let _lpActivated = false;
  const _lpTriggerMs = 550;
  const _lpStart = () => {
    if (state.mapperEditMode) return; // already selecting
    _lpActivated = false;
    _lpTimer = window.setTimeout(() => {
      _lpActivated = true;
      try { setMapperEditMode(true); } catch {}
      toggleMapperFolderSelection(folder);
    }, _lpTriggerMs);
  };
  const _lpCancel = () => { if (_lpTimer) { clearTimeout(_lpTimer); _lpTimer = null; } };
  card.addEventListener('mousedown', _lpStart);
  card.addEventListener('touchstart', _lpStart, { passive: true });
  ['mouseup','mouseleave','touchend','touchcancel'].forEach(ev => card.addEventListener(ev, _lpCancel));
  card.addEventListener("click", (ev) => {
    if (_lpActivated) { _lpActivated = false; return; }
    if (_consumeMapperDragSelectClickSuppression()) {
      try { ev.preventDefault(); ev.stopPropagation(); } catch {}
      return;
    }
    if (state.mapperEditMode) {
      toggleMapperFolderSelection(folder);
      return;
    }
    if (typeof opts.onOpen === 'function') {
      Promise.resolve(opts.onOpen()).catch((e) => {
        const errMsg = String((e && e.message) || e || '').trim();
        if (errMsg) showStatus(`Kunne ikke åbne mappe: ${errMsg}`, 'err');
      });
      return;
    }
    state.view = "timeline";
    state.folder = folder === "(root)" ? "" : folder;
    document.querySelectorAll(".nav-item").forEach(btn => btn.classList.remove("active"));
    loadPhotos();
  });
  els.grid.appendChild(card);

  // After initial render, try to load persisted selection from server; else persist our pick
  (async () => {
    try {
      const res = await fetch(`/api/folder-previews?folders=${encodeURIComponent(folder)}`);
      const data = await res.json();
      const saved = data && data.items ? data.items[folder] : null;
      const variantForCount = (count) => (count === 1 ? 'v1' : (count === 2 ? 'v2' : 'v4'));
      const normalizePreviewSet = (urls) => {
        const raw = (Array.isArray(urls) ? urls : []).map((u) => String(u || '').trim()).filter(Boolean).slice(0, 4);
        if (raw.length >= 4) return raw.slice(0, 4);
        if (raw.length >= 2) return raw.slice(0, 2);
        return raw.slice(0, 1);
      };
      let grid = card.querySelector('.folder-grid');
      const updateGrid = (urls, v) => {
        const nextUrls = normalizePreviewSet(urls);
        if (!nextUrls.length) return;
        const nextVariant = v || variantForCount(nextUrls.length);
        let thumb = card.querySelector('.card-thumb');
        grid = card.querySelector('.folder-grid');
        if (!grid) {
          if (!thumb) return;
          thumb.className = 'card-thumb folder-mosaic';
          thumb.innerHTML = `<div class="folder-grid ${nextVariant}"></div>${selBadge}${overlay}`;
          bindFolderNameMarquee(card, title || folder || '');
          grid = card.querySelector('.folder-grid');
        }
        if (!grid) return;
        grid.classList.remove('v1','v2','v4');
        grid.classList.add(nextVariant);
        grid.innerHTML = nextUrls.map(u => `<img src="${escapeHtml(u)}" alt="">`).join("");
        card.querySelectorAll('img').forEach((img) => {
          img.setAttribute('draggable', 'false');
        });
      };
      const persistPreviews = async (urls) => {
        if (!Array.isArray(urls) || !urls.length) return;
        try {
          await fetch('/api/folder-previews', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folder, previews: urls }),
          });
        } catch {}
      };
      // Determine desired preview count based on available unique URLs
      // If we didn't compute uniqUrls (arr empty), accept saved previews as-is
      const desiredCount = (uniqUrls.length === 1) ? 1 : ((uniqUrls.length === 2 || uniqUrls.length === 3) ? 2 : 4);
      const desiredVariant = (desiredCount === 1 ? 'v1' : (desiredCount === 2 ? 'v2' : 'v4'));
      if (Array.isArray(saved) && saved.length) {
        // When uniqUrls is empty (we skipped client-side scan), trust server-saved picks
        const normalizedSaved = uniqUrls.length ? normalizePreviewSet(saved.filter((u) => uniqUrls.includes(u)).slice(0, desiredCount)) : normalizePreviewSet(saved);
        if (normalizedSaved.length) {
          const latestStore = loadStore();
          latestStore[folder] = normalizedSaved;
          saveStore(latestStore);
        }
        if (!uniqUrls.length) {
          updateGrid(normalizedSaved, variantForCount(normalizedSaved.length));
          return;
        }
        if (normalizedSaved.length < desiredCount) {
          const fresh = uniqUrls.slice(0, desiredCount);
          if (fresh.length) {
            const latestStore = loadStore();
            latestStore[folder] = fresh;
            saveStore(latestStore);
            updateGrid(fresh, desiredVariant);
            await persistPreviews(fresh);
          }
        } else {
          const savedVariant = (normalizedSaved.length === 1 ? 'v1' : (normalizedSaved.length === 2 ? 'v2' : 'v4'));
          // Only update if different from what we rendered
          const same = Array.isArray(useUrls) && useUrls.length === normalizedSaved.length && useUrls.every((u,i)=>u===normalizedSaved[i]);
          if (!same) updateGrid(normalizedSaved, savedVariant);
          const changed = uniqUrls.length > 0 && (normalizedSaved.length !== saved.length || normalizedSaved.some((u, i) => u !== saved[i]));
          if (changed) await persistPreviews(normalizedSaved);
        }
      } else if (useUrls && useUrls.length) {
        await persistPreviews(useUrls);
      }
    } catch {}
  })();
}

let personRenameMenuEl = null;

function closePersonRenameMenu() {
  if (personRenameMenuEl && personRenameMenuEl.parentElement) {
    personRenameMenuEl.parentElement.removeChild(personRenameMenuEl);
  }
  personRenameMenuEl = null;
}

async function renameOrMergePerson(pid, name) {
  const nv = String(name || '').trim();
  if (!nv) return;
  try {
    const r = await fetch(`/api/people/${pid}/rename`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: nv }),
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok || !d.ok) {
      showStatus(d.error || tr('person_rename_save_failed'), 'err');
      return;
    }
    if (d.merged) showStatus(`${tr('person_rename_merged')} '${d.name || nv}'`, 'ok');
    else showStatus(tr('person_name_updated'), 'ok');
    // Trigger training so future matches improve for this person
    try {
      const targetId = Number(d.to_id || pid);
      if (Number.isFinite(targetId)) {
        fetch(`/api/people/${targetId}/train`, { method: 'POST' }).catch(()=>{});
      }
    } catch {}
    // Light in-place UI update to avoid re-rendering all images
    try {
      if (d.merged) {
        const fromId = Number(d.from_id || pid);
        const fromEl = document.querySelector(`.photo-card[data-person-id="${fromId}"]`);
        if (fromEl && fromEl.parentElement) fromEl.parentElement.removeChild(fromEl);
        const toId = Number(d.to_id);
        if (Number.isFinite(toId)) {
          const toEl = document.querySelector(`.photo-card[data-person-id="${toId}"]`);
          const title = toEl && toEl.querySelector('.card-title');
          if (title) title.textContent = String(d.name || nv);
        }
      } else {
        const el = document.querySelector(`.photo-card[data-person-id="${Number(pid)}"] .card-title`);
        if (el) el.textContent = nv;
      }
    } catch {}
    // Optionally kick off a quick unknown-face re-match pass (non-blocking)
    fetch('/api/faces/match-unknown', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ limit: 1000 }) })
      .then(r=>r.json().catch(()=>({}))).then((d2)=>{ if (d2 && d2.ok && d2.matched>0) showStatus(`Matchede ${d2.matched} ukendte ansigt(er).`, 'ok'); }).catch(()=>{});
    // Force fresh people list so newly created names are available immediately in rename suggestions.
    state._peopleCache = { key: '', items: [], ts: 0 };
    await loadPeople(false);
    closePersonRenameMenu();
  } catch {
    showStatus(tr('person_rename_merge_error'), 'err');
  }
}

async function matchUnknownFaces(limit = 1000) {
  const btn = document.getElementById('peopleMatchScanBtn');
  const orig = btn ? btn.textContent : tr('people_match_btn');
  try {
    if (btn) { btn.disabled = true; btn.classList.add('loading'); btn.textContent = tr('people_match_running'); }
    // Show top status in the header with indeterminate progress
    showTopStatusMessage(tr('people_match_running'));
    setTopStatusIndeterminate(true);
    const res = await fetch('/api/faces/match-unknown', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ limit: Number(limit) || 1000 }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || !data.ok) {
      showStatus((data && data.error) || tr('people_match_failed'), 'err');
      setTopStatusIndeterminate(false);
      hideTopStatusMessage();
      return;
    }
    const msg = (tr('people_match_done') || '').replace('{matched}', String(data.matched || 0)).replace('{scanned}', String(data.scanned || 0));
    showStatus(msg, 'ok');
    // Show brief result in top bar then hide
    if (els.uploadTopStatusLabel) els.uploadTopStatusLabel.textContent = msg;
    setTopStatusIndeterminate(false);
    setTimeout(hideTopStatusMessage, 2500);
    await loadPeople();
  } catch {
    showStatus(tr('people_match_failed'), 'err');
    setTopStatusIndeterminate(false);
    hideTopStatusMessage();
  } finally {
    if (btn) { btn.disabled = false; btn.classList.remove('loading'); btn.textContent = orig || tr('people_match_btn'); }
  }
}

function openPersonRenameMenu(anchorBtn, person) {
  closePersonRenameMenu();
  if (!anchorBtn || !person || person.id === 'unknown') {
    if (person && person.id === 'unknown') showStatus(tr('person_unknown_cannot_rename'), 'err');
    return;
  }

  const menu = document.createElement('div');
  menu.className = 'person-rename-menu';
  menu.innerHTML = `
    <div class="person-rename-head">${escapeHtml(tr('person_rename_title'))}</div>
    <div class="person-rename-create-row">
      <input type="text" class="person-rename-input" placeholder="${escapeHtml(tr('person_rename_new_placeholder'))}" value="" />
      <button type="button" class="btn tiny primary" data-act="create">${escapeHtml(tr('person_rename_save'))}</button>
    </div>
    <div class="person-rename-divider"></div>
    <div class="person-rename-list"></div>
  `;

  const listEl = menu.querySelector('.person-rename-list');
  // Exclude auto-generated unknown buckets like "Ukendt-10" from merge targets
  const _isAutoUnknown = (nm) => {
    const s = String(nm || '').trim().toLowerCase();
    return /^ukendt(?:-|\b)/.test(s) || /^unknown(?:-|\b)/.test(s);
  };
  const existing = (Array.isArray(state.people) ? state.people : [])
    .filter((it) => it && it.id !== 'unknown' && Number(it.id) !== Number(person.id)
      && String(it.name || '').trim() && !_isAutoUnknown(it.name))
    .sort((a, b) => String(a.name || '').localeCompare(String(b.name || ''), 'da-DK'));

  if (!existing.length) {
    listEl.innerHTML = `<div class="person-rename-empty">${escapeHtml(tr('person_rename_none'))}</div>`;
  } else {
    existing.forEach((it) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'person-rename-option';
      btn.textContent = String(it.name || tr('person_unknown'));
      btn.addEventListener('click', async () => {
        await renameOrMergePerson(person.id, String(it.name || ''));
      });
      listEl.appendChild(btn);
    });
  }

  const input = menu.querySelector('.person-rename-input');
  const createBtn = menu.querySelector('[data-act="create"]');
  let createBusy = false;
  const createNow = async () => {
    if (createBusy) return;
    const val = String(input && input.value ? input.value : '').trim();
    if (!val) {
      input && input.focus();
      return;
    }
    createBusy = true;
    const originalLabel = createBtn ? String(createBtn.textContent || '') : '';
    try {
      if (createBtn) {
        createBtn.disabled = true;
        createBtn.classList.add('loading');
      }
      await renameOrMergePerson(person.id, val);
    } finally {
      createBusy = false;
      if (createBtn && createBtn.isConnected) {
        createBtn.disabled = false;
        createBtn.classList.remove('loading');
        if (originalLabel) createBtn.textContent = originalLabel;
      }
    }
  };
  createBtn && createBtn.addEventListener('click', createNow);
  input && input.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      await createNow();
    }
    if (e.key === 'Escape') {
      e.preventDefault();
      closePersonRenameMenu();
    }
  });

  document.body.appendChild(menu);
  const rect = anchorBtn.getBoundingClientRect();
  const top = Math.min(window.innerHeight - 12, rect.bottom + 6 + window.scrollY);
  const left = Math.min(window.innerWidth - 12, rect.left + window.scrollX);
  menu.style.top = `${top}px`;
  menu.style.left = `${left}px`;
  personRenameMenuEl = menu;
  if (input) {
    try { input.focus(); } catch {}
  }

  window.setTimeout(() => {
    const onDocClick = (ev) => {
      const target = ev.target;
      if (!personRenameMenuEl) {
        document.removeEventListener('click', onDocClick, true);
        return;
      }
      if (target && (personRenameMenuEl.contains(target) || anchorBtn.contains(target))) return;
      closePersonRenameMenu();
      document.removeEventListener('click', onDocClick, true);
    };
    document.addEventListener('click', onDocClick, true);
  }, 0);
}

function appendPersonCard(p) {
  const card = document.createElement('article');
  card.className = 'photo-card';
  const img = p.thumb_url ? `<img src="${p.thumb_url}" alt="${p.name}" loading="lazy" decoding="async">` : `<div class="card-thumb placeholder">🙂</div>`;
  card.innerHTML = `
    <div class="card-thumb">${img}</div>
    <div class="card-body">
      <h4 class="card-title">${escapeHtml(p.name || tr('person_unknown'))}</h4>
      <div class="card-meta"><span>${p.count||0} ${escapeHtml(tr('person_count_suffix'))}</span></div>
      <div class="pills">${p.hidden ? `<span class="pill">${escapeHtml(tr('person_hidden_badge'))}</span>` : ''}</div>
      <div class="actions" style="margin-top:6px;display:flex;gap:6px;">
        <button class="btn tiny" data-act="rename">${escapeHtml(tr('person_btn_rename'))}</button>
        ${p.id==='unknown' ? '' : `<button class="btn tiny ${p.hidden?'':'danger'}" data-act="${p.hidden?'unhide':'hide'}">${escapeHtml(p.hidden ? tr('person_btn_unhide') : tr('person_btn_hide'))}</button>`}
      </div>
    </div>
  `;
  card.querySelectorAll('img').forEach((el) => {
    el.setAttribute('draggable', 'false');
  });
  // Klik på hele kortet åbner personens billeder (undtagen når man klikker på en knap)
  card.addEventListener('click', (e)=>{
    if (e.target && e.target.closest('[data-act]')) return;
    if (p.id === 'unknown') loadPersonPhotos('unknown', tr('person_unknown'));
    else loadPersonPhotos(p.id, p.name);
  });
  card.querySelector('[data-act="rename"]').addEventListener('click', async (e)=>{
    e.preventDefault();
    e.stopPropagation();
    openPersonRenameMenu(e.currentTarget, p);
  });
  const hideBtn = card.querySelector('[data-act="hide"]');
  if (hideBtn) {
    hideBtn.addEventListener('click', async ()=>{
      if (!confirm(tr('person_hide_confirm'))) return;
      try {
        const r = await fetch(`/api/people/${p.id}/hide`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ hidden: true })});
        const d = await r.json();
        if (!r.ok || !d.ok) { showStatus(d.error || tr('person_hide_failed'), 'err'); return; }
        showStatus(tr('person_hidden_ok'), 'ok');
        await loadPeople(false);
      } catch { showStatus(tr('person_hide_error'), 'err'); }
    });
  }
  const unhideBtn = card.querySelector('[data-act="unhide"]');
  if (unhideBtn) {
    unhideBtn.addEventListener('click', async ()=>{
      try {
        const r = await fetch(`/api/people/${p.id}/hide`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ hidden: false })});
        const d = await r.json();
        if (!r.ok || !d.ok) { showStatus(d.error || tr('person_unhide_failed'), 'err'); return; }
        showStatus(tr('person_unhidden_ok'), 'ok');
        await loadPeople(false);
      } catch { showStatus(tr('person_unhide_error'), 'err'); }
    });
  }
  els.grid.appendChild(card);
}

// Viewer controls
let viewerTransitionRunning = false;
let viewerPendingStep = 0;

function cleanupViewerMediaAnimation() {
  [els.viewerImg, els.viewerVideo].forEach((node) => {
    if (!node) return;
    node.style.transition = '';
    node.style.transform = '';
    node.style.opacity = '';
    node.style.willChange = '';
  });
}

function getViewerItems() {
  if (Array.isArray(state.viewerItems) && state.viewerItems.length) return state.viewerItems;
  return Array.isArray(state.items) ? state.items : [];
}

function openViewerWithItems(items, index = 0) {
  if (!Array.isArray(items) || !items.length) return;
  state.viewerItems = items.slice();
  const idx = Math.max(0, Math.min(items.length - 1, Number(index) || 0));
  openViewer(idx);
}

function _resolveSelectedPhotoIdForSimilar() {
  const sid = Number(state.selectedId || 0);
  if (Number.isFinite(sid) && sid > 0) return sid;
  const items = getViewerItems();
  const current = items[state.selectedIndex];
  const pid = Number(current && current.id || 0);
  return (Number.isFinite(pid) && pid > 0) ? pid : 0;
}

function getActiveViewerMediaElement() {
  if (els.viewerVideo && els.viewerVideo.style.display !== 'none') return els.viewerVideo;
  if (els.viewerImg && els.viewerImg.style.display !== 'none') return els.viewerImg;
  return els.viewerImg || els.viewerVideo || null;
}

function getViewerMediaAnchorRect() {
  const mediaEl = getActiveViewerMediaElement();
  if (!mediaEl) return null;
  try {
    const w = Number(mediaEl.offsetWidth || mediaEl.clientWidth || 0);
    const h = Number(mediaEl.offsetHeight || mediaEl.clientHeight || 0);
    if (w > 0 && h > 0 && els.viewer) {
      const viewerRect = els.viewer.getBoundingClientRect();
      const left = Number(viewerRect.left || 0) + Number(mediaEl.offsetLeft || 0);
      const top = Number(viewerRect.top || 0) + Number(mediaEl.offsetTop || 0);
      return { left, top, right: left + w, bottom: top + h, width: w, height: h };
    }
  } catch {}
  try {
    const r = mediaEl.getBoundingClientRect();
    if (r && Number.isFinite(r.left) && r.width > 0 && r.height > 0) return r;
  } catch {}
  return null;
}

function scheduleViewerInfoPosition() {
  if (!els.viewer || els.viewer.classList.contains('hidden')) return;
  try {
    requestAnimationFrame(() => {
      try { positionViewerInfoPanel(); positionViewerInfoTrigger(); } catch {}
    });
  } catch {}
}

  function updateViewerLandscapeClass(fallbackItem = null) {
    if (!els.viewer) return;

    let width = 0;
    let height = 0;
    if (els.viewerVideo && els.viewerVideo.style.display !== 'none') {
      width = Number(els.viewerVideo.videoWidth || 0);
      height = Number(els.viewerVideo.videoHeight || 0);
    } else if (els.viewerImg && els.viewerImg.style.display !== 'none') {
      width = Number(els.viewerImg.naturalWidth || 0);
      height = Number(els.viewerImg.naturalHeight || 0);
    }

    if (!(width > 0 && height > 0) && fallbackItem) {
      width = Number(fallbackItem.width || 0);
      height = Number(fallbackItem.height || 0);
    }

    if (!(width > 0 && height > 0)) {
      const active = getActiveViewerMediaElement();
      if (active) {
        width = Number(active.clientWidth || active.offsetWidth || 0);
        height = Number(active.clientHeight || active.offsetHeight || 0);
      }
    }

    const isLandscape = width > 0 && height > 0 && width > (height * 1.05);
    els.viewer.classList.toggle('viewer-landscape', isLandscape);
    scheduleViewerInfoPosition();
  }

function viewerInfoOpenTransform(offsetX = 0) {
  const x = Math.round(Number(offsetX) || 0);
  if (!x) return 'translateX(100%)';
  return `translateX(calc(100% ${x >= 0 ? '+' : '-'} ${Math.abs(x)}px))`;
}

function beginViewerInfoSlideOut(offsetX, duration) {
  if (!viPanel || !isViewerInfoPanelOpen() || isMobileViewerLayout()) return false;
  try {
    positionViewerInfoPanel();
    viPanel.style.willChange = 'transform, opacity';
    viPanel.style.transition = `transform ${duration}ms ease, opacity ${duration}ms ease`;
    viPanel.style.transform = viewerInfoOpenTransform(offsetX);
    viPanel.style.opacity = '0';
    return true;
  } catch {
    return false;
  }
}

function prepareViewerInfoSlideIn(offsetX) {
  if (!viPanel || !isViewerInfoPanelOpen() || isMobileViewerLayout()) return false;
  try {
    positionViewerInfoPanel();
    viPanel.style.willChange = 'transform, opacity';
    viPanel.style.transition = 'none';
    viPanel.style.transform = viewerInfoOpenTransform(offsetX);
    viPanel.style.opacity = '0';
    return true;
  } catch {
    return false;
  }
}

function runViewerInfoSlideIn(duration) {
  if (!viPanel || !isViewerInfoPanelOpen() || isMobileViewerLayout()) return;
  viPanel.style.transition = `transform ${duration}ms ease, opacity ${duration}ms ease`;
  viPanel.style.transform = viewerInfoOpenTransform(0);
  viPanel.style.opacity = '1';
}

function finishViewerInfoSlideAnimation() {
  if (!viPanel) return;
  try {
    if (isViewerInfoPanelOpen() && !isMobileViewerLayout()) {
      viPanel.style.transition = '';
      viPanel.style.transform = '';
      viPanel.style.opacity = '';
      viPanel.style.willChange = '';
      positionViewerInfoPanel();
    }
  } catch {}
}

function beginViewerInfoButtonSlideOut(offsetX, duration) {
  if (!viMediaBtn || !els.viewer || els.viewer.classList.contains('hidden')) return false;
  try {
    positionViewerInfoTrigger();
    viMediaBtn.style.willChange = 'transform, opacity';
    viMediaBtn.style.transition = `transform ${duration}ms ease, opacity ${duration}ms ease`;
    viMediaBtn.style.transform = `translateX(${Math.round(Number(offsetX) || 0)}px)`;
    viMediaBtn.style.opacity = '0';
    return true;
  } catch {
    return false;
  }
}

function prepareViewerInfoButtonSlideIn(offsetX) {
  if (!viMediaBtn || !els.viewer || els.viewer.classList.contains('hidden')) return false;
  try {
    positionViewerInfoTrigger();
    viMediaBtn.style.willChange = 'transform, opacity';
    viMediaBtn.style.transition = 'none';
    viMediaBtn.style.transform = `translateX(${Math.round(Number(offsetX) || 0)}px)`;
    viMediaBtn.style.opacity = '0';
    return true;
  } catch {
    return false;
  }
}

function runViewerInfoButtonSlideIn(duration) {
  if (!viMediaBtn || !els.viewer || els.viewer.classList.contains('hidden')) return;
  viMediaBtn.style.transition = `transform ${duration}ms ease, opacity ${duration}ms ease`;
  viMediaBtn.style.transform = 'translateX(0)';
  viMediaBtn.style.opacity = '1';
}

function finishViewerInfoButtonSlideAnimation() {
  if (!viMediaBtn) return;
  try {
    viMediaBtn.style.transition = '';
    viMediaBtn.style.transform = '';
    viMediaBtn.style.opacity = '';
    viMediaBtn.style.willChange = '';
    positionViewerInfoTrigger();
  } catch {}
}

function animateViewerSlideTransition(step, applyUpdate) {
  if (!els.viewer || els.viewer.classList.contains('hidden')) {
    applyUpdate();
    return;
  }
  const fromEl = getActiveViewerMediaElement();
  if (!fromEl) {
    applyUpdate();
    return;
  }

  const duration = 180;
  const distance = Math.min(Math.round(window.innerWidth * 0.22), 160);
  const outX = step > 0 ? -distance : distance;
  const inStartX = step > 0 ? distance : -distance;
  const animateInfoPanel = beginViewerInfoSlideOut(outX, duration);
  const animateInfoButton = beginViewerInfoButtonSlideOut(outX, duration);

  fromEl.style.willChange = 'transform, opacity';
  fromEl.style.transition = `transform ${duration}ms ease, opacity ${duration}ms ease`;
  fromEl.style.transform = `translateX(${outX}px)`;
  fromEl.style.opacity = '0';

  window.setTimeout(() => {
    applyUpdate();
    const infoPanelIn = animateInfoPanel && prepareViewerInfoSlideIn(inStartX);
    const infoButtonIn = animateInfoButton && prepareViewerInfoButtonSlideIn(inStartX);
    const toEl = getActiveViewerMediaElement();
    if (!toEl) {
      cleanupViewerMediaAnimation();
      finishViewerInfoSlideAnimation();
      finishViewerInfoButtonSlideAnimation();
      scheduleViewerInfoPosition();
      viewerTransitionRunning = false;
      return;
    }

    toEl.style.willChange = 'transform, opacity';
    toEl.style.transition = 'none';
    toEl.style.transform = `translateX(${inStartX}px)`;
    toEl.style.opacity = '0';

    requestAnimationFrame(() => {
      toEl.style.transition = `transform ${duration}ms ease, opacity ${duration}ms ease`;
      toEl.style.transform = 'translateX(0)';
      toEl.style.opacity = '1';
      if (infoPanelIn) runViewerInfoSlideIn(duration);
      if (infoButtonIn) runViewerInfoButtonSlideIn(duration);
    });

    window.setTimeout(() => {
      cleanupViewerMediaAnimation();
      finishViewerInfoSlideAnimation();
      finishViewerInfoButtonSlideAnimation();
      scheduleViewerInfoPosition();
      viewerTransitionRunning = false;
      if (viewerPendingStep !== 0) {
        const pending = viewerPendingStep;
        viewerPendingStep = 0;
        nextViewer(pending);
      }
    }, duration + 30);
  }, duration);
}

function openViewer(index) {
  const items = getViewerItems();
  state.selectedIndex = index;
  const it = items[index];
  if (!it || !it.original_url) return;
  try {
    const pid = Number(it.id || 0);
    if (Number.isFinite(pid) && pid > 0) state.selectedId = pid;
  } catch {}
  if (!els.viewer) return;
  els.viewer.classList.remove('viewer-landscape');
  // Toggle media elements
  if (els.viewerImg) {
    els.viewerImg.setAttribute('draggable', 'false');
    els.viewerImg.onload = () => {
      try { positionViewerInfoPanel(); positionViewerInfoTrigger(); } catch {}
      updateViewerLandscapeClass(it);
    };
    els.viewerImg.style.display = it.is_video ? 'none' : 'block';
    if (!it.is_video) {
      // Show a fast placeholder immediately, then swap to full viewable when ready
      if (it.thumb_url) {
        els.viewerImg.src = it.thumb_url;
      } else {
        els.viewerImg.removeAttribute('src');
      }
      const hi = new Image();
      try { hi.decoding = 'async'; } catch {}
      try { hi.fetchPriority = 'high'; } catch {}
      hi.onload = async () => {
        try { if (hi.decode) await hi.decode().catch(()=>{}); } catch {}
        // Only swap if the viewer still shows this item
        const currentItems = getViewerItems();
        const current = currentItems[state.selectedIndex];
        if (current && Number(current.id || 0) === Number(it.id || 0)) {
          els.viewerImg.src = it.original_url || it.thumb_url || '';
          try { positionViewerInfoPanel(); positionViewerInfoTrigger(); } catch {}
        }
      };
      hi.src = it.original_url || it.thumb_url || '';
    }
    if (it.is_video) els.viewerImg.removeAttribute('src');
  }
  if (els.viewerVideo) {
    els.viewerVideo.setAttribute('draggable', 'false');
    els.viewerVideo.onloadedmetadata = () => {
      try { positionViewerInfoPanel(); positionViewerInfoTrigger(); } catch {}
      updateViewerLandscapeClass(it);
    };
    els.viewerVideo.style.display = it.is_video ? 'block' : 'none';
    try { els.viewerVideo.pause(); } catch(_) {}
    if (it.is_video) {
      els.viewerVideo.src = it.original_url;
      try { els.viewerVideo.play().catch(()=>{}); } catch(_) {}
    } else {
      els.viewerVideo.removeAttribute('src');
    }
  }
  updateViewerLandscapeClass(it);
  els.viewer.classList.remove("hidden");
  try {
    requestAnimationFrame(() => {
      positionViewerInfoPanel();
      positionViewerInfoTrigger();
    });
  } catch {}
  // Preload neighbors for snappier next/prev navigation
  try {
    const idxs = [index - 1, index + 1];
    for (const j of idxs) {
      const nx = items[j];
      if (!nx || nx.is_video || !nx.original_url) continue;
      const pre = new Image();
      try { pre.decoding = 'async'; } catch {}
      pre.src = nx.original_url;
    }
  } catch {}
  // Populate slide-out info with the current item's metadata
  try {
    const title = (it.filename || it.rel_path || "-");
    const dateParts = fmtDateParts(it.captured_at || it.modified_fs || it.created_fs);
    const dims = it.width && it.height ? `${it.width} × ${it.height}` : "-";
    const dev = it.device_label || [it.camera_make, it.camera_model].filter(Boolean).join(" ");
    const lens = it.lens_label || it.lens_model || "-";
    const gps = (it.gps_lat!=null && it.gps_lon!=null) ? `${Number(it.gps_lat).toFixed(5)}, ${Number(it.gps_lon).toFixed(5)}` : (it.gps_name || "-");
    const uploader = String(it && it.uploaded_by ? it.uploaded_by : '').trim();
    const caption = _formatAiCaptionText(it);
    const tags = _formatAiTagsText(it);
    const conversion = _getItemConversionInfo(it);
    const dl = (it.download_url || it.original_url || '#');
    const q = (id) => document.getElementById(id);
    const setText = (id, value) => {
      const el = q(id);
      if (el) el.textContent = String(value == null ? '-' : value);
    };
    setText('viTitle', title);
    setText('viDate', dateParts.date);
    setText('viTime', dateParts.time);
    setText('viSize', fmtBytes(it.file_size));
    setText('viDims', dims);
    setText('viDevice', dev || '-');
    setText('viLens', lens);
    setText('viGps', gps);
    setText('viUploader', uploader || '—');
    setText('viCaption', caption);
    setText('viTags', tags);
    try { const viCaption = q('viCaption'); if (viCaption) viCaption.title = caption === '-' ? '' : caption; } catch {}
    try { const viTags = q('viTags'); if (viTags) viTags.title = tags; } catch {}
    const convRow = q('viConvertedRow');
    if (convRow) convRow.classList.toggle('hidden', !conversion.converted);
    setText('viConverted', conversion.converted ? conversion.label : '—');
    try {
      const geo = (it.metadata_json && it.metadata_json.geo) ? it.metadata_json.geo : {};
      setText('viCountry', geo.country || '-');
      setText('viCity', geo.city || '-');
    } catch {}
    renderWeatherInfo(it);
    const viDL = q('viDownload'); if (viDL) viDL.href = dl;
    try { const fbtn = q('viFavoriteBtn'); if (fbtn) fbtn.textContent = it.favorite ? '★' : '☆'; } catch {}
  } catch {}

  // Keep panel + info icon anchored to the active media.
  try { positionViewerInfoPanel(); positionViewerInfoTrigger(); } catch {}
  if (els.viewerOpenOrig) {
    const dl = (it.download_url || it.original_url || '');
    els.viewerOpenOrig.href = dl;
    els.viewerOpenOrig.download = it.filename || '';
    els.viewerOpenOrig.style.display = 'inline-block';
  }
}
function closeViewer() {
  if (!els.viewer) return;
  els.viewer.classList.add("hidden");
  els.viewer.classList.remove('viewer-landscape');
  if (els.viewerImg) els.viewerImg.removeAttribute("src");
  if (els.viewerVideo) { try { els.viewerVideo.pause(); } catch(_) {} els.viewerVideo.removeAttribute('src'); }
}
function nextViewer(step=1) {
  if (state.selectedIndex < 0) return;
  if (viewerTransitionRunning) {
    viewerPendingStep = step;
    return;
  }
  const items = getViewerItems();
  const n = items.length;
  if (!n) return;
  const targetIndex = (state.selectedIndex + step + n) % n;
  const it = items[targetIndex];
  if (!it || !it.original_url) return;
  viewerTransitionRunning = true;
  state.selectedIndex = targetIndex;
  animateViewerSlideTransition(step, () => openViewer(state.selectedIndex));
}

function stopPhotoframeStatusPolling() {
  if (photoframeStatusPollTimer) {
    clearInterval(photoframeStatusPollTimer);
    photoframeStatusPollTimer = null;
  }
}

function isPhotoframeModalOpen() {
  if (state.view !== 'photoframe') return false;
  const ids = ['photoframeCreateModal', 'photoframeShowTokenModal', 'photoframeScopeModal'];
  for (const id of ids) {
    const modal = document.getElementById(id);
    if (modal && !modal.classList.contains('hidden')) return true;
  }
  return false;
}

function startPhotoframeStatusPolling() {
  stopPhotoframeStatusPolling();
  photoframeStatusPollTimer = setInterval(async () => {
    if (state.view !== 'photoframe' || state.photoframeLoading || isPhotoframeModalOpen()) return;
    try {
      await loadPhotoframeStatus();
    } catch {}
  }, PHOTOFRAME_STATUS_POLL_MS);
}

async function loadPhotoframeStatus() {
  if (state.photoframeLoading) return;
  state.photoframeLoading = true;
  state.photoframeError = '';
  if (state.view === 'photoframe' && !isPhotoframeModalOpen()) renderGrid();

  try {
    const res = await fetch('/api/photoframes/status');
    let data = null;
    try {
      const ct = String(res.headers.get('content-type') || '');
      data = ct.includes('application/json') ? await res.json() : null;
    } catch (_) {
      data = null;
    }
    if (!res.ok || !data || !data.ok) {
      const errTxt = (data && data.error) ? String(data.error) : tr('photoframe_status_unknown');
      throw new Error(errTxt);
    }
    state.photoframeItems = Array.isArray(data.items) ? data.items : [];
    state.photoframeCheckedAt = String(data.checked_at || new Date().toISOString());
    state.photoframeSource = String(data.source || 'none');
    state.photoframeConfigPath = String(data.config_path || '');
    state.photoframeLatestVersion = String(data.latest_version || '').trim();
    state.photoframeLatestVersionAt = String(data.latest_version_at || '').trim();
  } catch (e) {
    state.photoframeError = `${tr('photoframe_card_error')}: ${String((e && e.message) || e || tr('photoframe_status_unknown'))}`;
    state.photoframeItems = [];
    state.photoframeCheckedAt = new Date().toISOString();
    state.photoframeLatestVersion = '';
    state.photoframeLatestVersionAt = '';
  } finally {
    state.photoframeLoading = false;
    if (state.view === 'photoframe' && !isPhotoframeModalOpen()) renderGrid();
  }
}

async function loadPhotos(append = false) {
  if (state.view === 'photoframe') {
    state.items = [];
    const labels = navLabels();
    const [title, subtitle] = labels[state.view] || ["FjordLens", ""];
    if (els.viewTitle) els.viewTitle.textContent = title;
    if (els.viewSubtitle) els.viewSubtitle.textContent = subtitle;
    renderGrid();
    return;
  }

  // Timeline and Mapper support paging. Mapper only fetches direct photos in the
  // current folder; child folder previews are loaded separately and cheaply.
  const pagedView = (state.view === 'timeline' || state.view === 'mapper');
  if (!append) {
    state.photosPageOffset = 0;
    state.photosHasMore = false;
  }
  const qs = new URLSearchParams({
    q: state.q,
    view: state.view,
    sort: state.view === 'mapper' ? _normalizeMapperSort(state.mapperSort) : state.sort,
    folder: state.view === 'mapper' ? (state.mapperPath || "") : (state.folder || ""),
    search_lang: state.searchLanguage || 'da',
  });
  if (state.view === 'mapper') {
    qs.set('direct', '1');
    qs.set('offset', String(state.photosPageOffset || 0));
    qs.set('limit', String(estimateMapperPageLimit()));
  } else if (state.view === 'timeline') {
    qs.set('offset', String(state.photosPageOffset || 0));
    qs.set('limit', String(state.photosPageLimit || 300));
  }

  state.photosLoading = true;
  const res = await fetch(`/api/photos?${qs.toString()}`);
  let data;
  try {
    const ct = String(res.headers.get('content-type') || '');
    data = ct.includes('application/json') ? await res.json() : null;
  } catch (_) {
    data = null;
  }
  if (!data) {
    const text = await res.text().catch(()=> '');
    console.warn('photos non-JSON svar', { status: res.status, text: text?.slice(0, 200) });
    showStatus('Kunne ikke hente billeder (server svarede ikke med JSON).', 'err');
    if (!append) state.items = []; // keep existing on append failure
  } else {
    const incoming = Array.isArray(data.items) ? data.items : [];
    if (append) state.items = (state.items || []).concat(incoming);
    else state.items = incoming;
    state.photosHasMore = !!data.has_more;
    if (pagedView) {
      const used = incoming.length;
      const nextOffset = Number(data.next_offset);
      state.photosPageOffset = Number.isFinite(nextOffset) && nextOffset >= 0
        ? nextOffset
        : ((state.photosPageOffset || 0) + used);
    }
    if (data && data.error) {
      const errMsg = String(data.error || '').trim();
      if (errMsg) showStatus(`Kunne ikke hente billeder: ${errMsg}`, 'err');
    }
    if (!append && state.view === 'mapper') {
      handleMapperDiskSyncStatus(data.disk_sync);
    }
  }
  state.photosLoading = false;

  const labels = navLabels();
  const [title, subtitle] = labels[state.view] || ["FjordLens", ""];
  els.viewTitle.textContent = title;
  els.viewSubtitle.textContent = subtitle;

  if (!append && state.view === 'mapper') {
    await prefetchMapperFolderPreviewsForCurrentPath();
  }
  renderGrid();
}

async function loadPeople(useCache = true) {
  closePersonRenameMenu();
  try {
    const cacheKey = state.showHiddenPeople ? 'hidden:1' : 'hidden:0';
    const now = Date.now();
    if (useCache && state._peopleCache && state._peopleCache.key === cacheKey && (now - (state._peopleCache.ts || 0) < 60000)) {
      state.people = Array.isArray(state._peopleCache.items) ? state._peopleCache.items : [];
    } else {
      const url = state.showHiddenPeople ? '/api/people?include_hidden=1' : '/api/people';
      const res = await fetch(url);
      const data = await res.json();
      state.people = data.items || [];
      state._peopleCache = { key: cacheKey, items: state.people.slice(), ts: now };
    }
  } catch { state.people = []; }
  // Update headings for People view
  const labels = navLabels();
  const [title, subtitle] = labels['personer'] || ["Personer", ""];
  if (els.viewTitle) els.viewTitle.textContent = title;
  if (els.viewSubtitle) els.viewSubtitle.textContent = subtitle;
  renderGrid();
}

async function loadPersonPhotos(pid, name) {
  try {
    const url = (pid === 'unknown') ? '/api/people/unknown/photos-faces' : `/api/people/${pid}/photos`;
    const res = await fetch(url);
    const data = await res.json();
    state.items = data.items || [];
    state.personView = { mode: 'photos', personId: pid, personName: name };
  } catch { state.items = []; }
  renderGrid();
}

async function fetchUploadDestinationConfig(destination = null) {
  let url = '/api/settings/upload-destination';
  if (destination) url += `?destination=${encodeURIComponent(destination)}`;
  const res = await fetch(url);
  let data;
  try {
    const ct = String(res.headers.get('content-type') || '');
    data = ct.includes('application/json') ? await res.json() : null;
  } catch (_) {
    data = null;
  }
  if (!data) {
    // Fald tilbage: undgå at crashe hvis backend sender HTML (fx login/fejlside)
    const text = await res.text().catch(()=> '');
    console.warn('upload-destination non-JSON svar', { status: res.status, text: text?.slice(0, 200) });
    data = { ok: false, error: 'invalid_json', note: 'non-json', status: res.status };
  }
  return { res, data };
}

const uploadUiState = {
  totalFiles: 0,
  totalBytes: 0,
  processedFiles: 0,
  processedBytes: 0,
  failedFiles: 0,
  currentFileName: '',
  currentPhaseLabel: '',
  currentLoaded: 0,
  currentTotal: 0,
  workflowMode: 'gentle',
  processStatus: null,
  collapsed: false,
  transferStartedAt: 0,
  transferStartBytes: 0,
  transferLastSampleAt: 0,
  transferLastSampleBytes: 0,
  transferRateBps: 0,
  transferSamples: [],
  transferEtaSeconds: 0,
  transferLastEtaAt: 0,
};

let uploadOverlayHideTimer = null;
let uploadMonitorHideTimer = null;
let mobileUploadsHideTimer = null;

function scheduleUploadMonitorAutoHide(delayMs = 10000) {
  try {
    if (!els.uploadMonitor) return;
    if (uploadMonitorHideTimer) { window.clearTimeout(uploadMonitorHideTimer); uploadMonitorHideTimer = null; }
    uploadMonitorHideTimer = window.setTimeout(() => {
      try {
        els.uploadMonitor.style.transition = 'opacity .35s ease';
        els.uploadMonitor.style.opacity = '0';
        window.setTimeout(()=>{
          try {
            els.uploadMonitor.classList.add('hidden');
            els.uploadMonitor.style.opacity = '';
            els.uploadMonitor.style.transition = '';
          } catch {}
        }, 380);
      } catch {}
      uploadMonitorHideTimer = null;
    }, Math.max(0, Number(delayMs || 0)));
  } catch {}
}
let activeTusUpload = null;
let uploadStopRequested = false;
let uploadWasStopped = false;
let uploadTransferActive = false;
let uploadLiveRefreshBusy = false;
let uploadLiveRefreshAt = 0;
let uploadImmediateRevealDone = false;
let uploadQueuePumpRunning = false;
let uploadBatchSeq = 0;
let uploadSessionSavedTotal = 0;
let uploadTransferHeartbeatTimer = null;
let directUploadPostprocessPollActive = false;
let directUploadPostprocessUiActive = false;
let mapperDiskSyncWatcherTimer = null;
let mapperDiskSyncWatcherBusy = false;

async function setUploadTransferState(active) {
  try {
    await fetch('/api/upload/transfer-state', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ active: !!active }),
    });
  } catch {}
}

function startUploadTransferHeartbeat() {
  if (uploadTransferHeartbeatTimer) {
    window.clearInterval(uploadTransferHeartbeatTimer);
    uploadTransferHeartbeatTimer = null;
  }
  setUploadTransferState(true).catch(() => {});
  uploadTransferHeartbeatTimer = window.setInterval(() => {
    if (!uploadQueuePumpRunning && !isUploadRunning()) {
      stopUploadTransferHeartbeat().catch(() => {});
      return;
    }
    setUploadTransferState(true).catch(() => {});
  }, 15000);
}

async function stopUploadTransferHeartbeat() {
  if (uploadTransferHeartbeatTimer) {
    window.clearInterval(uploadTransferHeartbeatTimer);
    uploadTransferHeartbeatTimer = null;
  }
  await setUploadTransferState(false);
}
const uploadQueue = [];
const uploadMonitorItemsByKey = new Map();
const UPLOAD_RESUME_DRAFT_KEY = 'fjordlens.upload.resumeDraft.v1';
const UPLOAD_RESUME_DRAFT_TTL_MS = 12 * 60 * 60 * 1000;
// People view: guard timers and concurrency for face-crop polling
let peopleRenderEpoch = 0;
let activeFacePolls = 0;
const MAX_ACTIVE_FACE_POLLS = 6;

function _uploadFileSignature(file) {
  return [
    String(file && file.name ? file.name : ''),
    String(Number(file && file.size ? file.size : 0)),
    String(Number(file && file.lastModified ? file.lastModified : 0)),
  ].join('|');
}

function _normalizeUploadDraft(raw) {
  if (!raw || typeof raw !== 'object') return null;
  const now = Date.now();
  const createdAt = Number(raw.createdAt || 0);
  const updatedAt = Number(raw.updatedAt || createdAt || now);
  if (!createdAt || (now - updatedAt) > UPLOAD_RESUME_DRAFT_TTL_MS) return null;
  const pending = Array.isArray(raw.pending)
    ? raw.pending.map((v) => String(v || '').trim()).filter(Boolean)
    : [];
  if (!pending.length) return null;
  return {
    destination: String(raw.destination || ''),
    subdir: String(raw.subdir || ''),
    pending,
    createdAt,
    updatedAt,
  };
}

function _readUploadResumeDraft() {
  try {
    const raw = window.localStorage.getItem(UPLOAD_RESUME_DRAFT_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    const normalized = _normalizeUploadDraft(parsed);
    if (!normalized) {
      window.localStorage.removeItem(UPLOAD_RESUME_DRAFT_KEY);
      return null;
    }
    return normalized;
  } catch {
    return null;
  }
}

function _writeUploadResumeDraft(draft) {
  const normalized = _normalizeUploadDraft(draft);
  if (!normalized) {
    try { window.localStorage.removeItem(UPLOAD_RESUME_DRAFT_KEY); } catch {}
    return;
  }
  try {
    window.localStorage.setItem(UPLOAD_RESUME_DRAFT_KEY, JSON.stringify(normalized));
  } catch {}
}

function _clearUploadResumeDraft() {
  try { window.localStorage.removeItem(UPLOAD_RESUME_DRAFT_KEY); } catch {}
}

function _queueUploadDraftFiles(files, destination = '', subdir = '') {
  const existing = _readUploadResumeDraft();
  const sameTarget = !!existing
    && String(existing.destination || '') === String(destination || '')
    && String(existing.subdir || '') === String(subdir || '');
  const pending = sameTarget ? Array.from(existing.pending || []) : [];
  const set = new Set(pending);
  for (const file of (files || [])) {
    set.add(_uploadFileSignature(file));
  }
  _writeUploadResumeDraft({
    destination: String(destination || ''),
    subdir: String(subdir || ''),
    pending: Array.from(set),
    createdAt: sameTarget && existing ? Number(existing.createdAt || Date.now()) : Date.now(),
    updatedAt: Date.now(),
  });
}

function _markUploadDraftFileDone(file) {
  const draft = _readUploadResumeDraft();
  if (!draft) return;
  const sig = _uploadFileSignature(file);
  const pending = (draft.pending || []).filter((v) => v !== sig);
  if (!pending.length) {
    _clearUploadResumeDraft();
    return;
  }
  _writeUploadResumeDraft({
    destination: draft.destination,
    subdir: draft.subdir,
    pending,
    createdAt: Number(draft.createdAt || Date.now()),
    updatedAt: Date.now(),
  });
}

function _announceUploadResumeDraftIfNeeded() {
  const draft = _readUploadResumeDraft();
  if (!draft || !(draft.pending || []).length) return;
  const pathTxt = String(draft.subdir || '').trim() || 'root';
  showStatus(
    `Upload kan genoptages: vælg de samme ${draft.pending.length} fil(er) igen (${pathTxt}) for at fortsætte via TUS.`,
    'ok'
  );
}

function _maybeAnnounceAutoResumeForBatch(files, destination = '', subdir = '') {
  const draft = _readUploadResumeDraft();
  if (!draft) return;
  if (String(draft.destination || '') !== String(destination || '')) return;
  if (String(draft.subdir || '') !== String(subdir || '')) return;
  const pending = new Set((draft.pending || []).map((v) => String(v || '').trim()).filter(Boolean));
  if (!pending.size) return;
  let matched = 0;
  for (const file of (files || [])) {
    if (pending.has(_uploadFileSignature(file))) matched += 1;
  }
  if (matched > 0) {
    showStatus(`Genoptager upload via TUS for ${matched} fil(er)…`, 'ok');
  }
}

function shouldWarnOnPageLeaveDuringUpload() {
  if (isUploadRunning() || uploadQueuePumpRunning) return true;
  const draft = _readUploadResumeDraft();
  return !!(draft && Array.isArray(draft.pending) && draft.pending.length > 0);
}

window.addEventListener('beforeunload', (event) => {
  if (!shouldWarnOnPageLeaveDuringUpload()) return;
  // Browsers ignore custom text, but setting returnValue triggers a confirmation dialog.
  event.preventDefault();
  event.returnValue = '';
});

async function maybeRefreshPhotosDuringPostprocess(force = false) {
  // Do not refresh the grid during raw upload transfer to avoid showing
  // any new/partial items before metadata/thumb phases begin.
  if (!force && isUploadRunning()) return;
  if (!(state.view === 'mapper' || state.view === 'timeline')) return;
  if (uploadLiveRefreshBusy) return;
  const now = Date.now();
  if (!force && (now - uploadLiveRefreshAt) < 2500) return;
  uploadLiveRefreshBusy = true;
  uploadLiveRefreshAt = now;
  try {
    await loadPhotos();
  } catch {}
  uploadLiveRefreshBusy = false;
}

function _syncCount(value) {
  const n = Number(value || 0);
  return Number.isFinite(n) ? Math.max(0, n) : 0;
}

function applyDirectPostprocessStatusToUploadUi(status) {
  if (isUploadRunning() || uploadQueuePumpRunning || uploadPostprocessResumeActive) return;
  const src = (status && typeof status === 'object') ? status : {};
  const stageTotal = _syncCount(src.stage_total);
  const stageDone = _syncCount(src.stage_processed);
  const overallTotal = _syncCount(src.overall_total);
  const overallDone = _syncCount(src.overall_processed);
  const pending = _syncCount(src.pending);
  const total = overallTotal || stageTotal || overallDone || stageDone || pending || 0;
  const done = Math.min(total || overallDone || stageDone || 0, overallDone || stageDone || 0);
  uploadUiState.totalFiles = Math.max(Number(uploadUiState.totalFiles || 0), total || done || 0);
  uploadUiState.processedFiles = Math.max(0, Math.min(uploadUiState.totalFiles || done || 0, done));
  uploadUiState.totalBytes = 0;
  uploadUiState.processedBytes = 0;
  uploadUiState.failedFiles = 0;
  uploadUiState.workflowMode = String(src.workflow_mode || uploadUiState.workflowMode || 'gentle').toLowerCase();
  uploadUiState.processStatus = (src.process_status && typeof src.process_status === 'object') ? src.process_status : null;
  const useParallel = uploadUiState.workflowMode === 'aggressive' && !!uploadUiState.processStatus;
  uploadUiState.currentPhaseLabel = useParallel ? tr('tab_upload_workflow') : postprocessPhaseLabel(src.phase);
  uploadUiState.currentFileName = useParallel ? tr('upload_workflow_running') : (shortRelName(src.current_rel) || 'Arbejder…');
  uploadUiState.currentLoaded = uploadUiState.processedFiles;
  uploadUiState.currentTotal = uploadUiState.totalFiles;
  directUploadPostprocessUiActive = true;
  renderUploadMonitor();
}

function clearDirectPostprocessUploadUi() {
  if (!directUploadPostprocessUiActive) return;
  directUploadPostprocessUiActive = false;
  uploadUiState.totalFiles = 0;
  uploadUiState.totalBytes = 0;
  uploadUiState.processedFiles = 0;
  uploadUiState.processedBytes = 0;
  uploadUiState.failedFiles = 0;
  uploadUiState.currentFileName = '';
  uploadUiState.currentPhaseLabel = '';
  uploadUiState.currentLoaded = 0;
  uploadUiState.currentTotal = 0;
  uploadUiState.workflowMode = 'gentle';
  uploadUiState.processStatus = null;
  renderUploadMonitor();
}

async function pollDirectUploadPostprocessStatus(forceShow = false) {
  if (directUploadPostprocessPollActive) return;
  directUploadPostprocessPollActive = true;
  try {
    let sawRunning = false;
    const deadline = Date.now() + (24 * 60 * 60 * 1000);
    while (Date.now() < deadline) {
      const res = await fetch('/api/upload/direct-postprocess/status');
      let status = {};
      try { status = await res.json(); } catch {}
      if (!res.ok || !status || !status.ok) return;

      const pending = _syncCount(status.pending);
      if (status.running || pending > 0) {
        sawRunning = true;
        applyDirectPostprocessStatusToUploadUi(status);
        await maybeRefreshPhotosDuringPostprocess(false);
        await new Promise((resolve) => window.setTimeout(resolve, uploadPostprocessPollDelayMs(status)));
        continue;
      }

      if (sawRunning || forceShow) {
        clearDirectPostprocessUploadUi();
        await maybeRefreshPhotosDuringPostprocess(true);
      }
      return;
    }
  } catch {
    return;
  } finally {
    directUploadPostprocessPollActive = false;
  }
}

function handleMapperDiskSyncStatus(sync) {
  if (state.view !== 'mapper' || !sync || typeof sync !== 'object') return;
  const queued = _syncCount(sync.postprocess_queued);
  const unsettled = _syncCount(sync.unsettled);
  if (Array.isArray(sync.preview_folders) && sync.preview_folders.length) invalidateStoredFolderPreviews(sync.preview_folders);
  if (queued > 0 || sync.skipped === 'running') {
    pollDirectUploadPostprocessStatus(queued > 0).catch(() => {});
  }
  if (unsettled > 0) {
    window.setTimeout(() => {
      if (state.view === 'mapper' && !state.photosLoading) {
        loadPhotos().catch(() => {});
      }
    }, 1800);
  }
}

async function checkMapperDiskSyncNow() {
  if (mapperDiskSyncWatcherBusy) return;
  if (state.view !== 'mapper') return;
  if (state.photosLoading || isUploadRunning() || uploadQueuePumpRunning) return;
  mapperDiskSyncWatcherBusy = true;
  try {
    const qs = new URLSearchParams({
      folder: state.mapperPath || '',
      direct: '1',
    });
    const res = await fetch(`/api/upload/folder-sync/status?${qs.toString()}`, { cache: 'no-store' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || !data.ok) return;
    const sync = data.disk_sync || {};
    handleMapperDiskSyncStatus(sync);
    const post = (data.postprocess && typeof data.postprocess === 'object') ? data.postprocess : {};
    if (post.running || _syncCount(post.pending) > 0) {
      pollDirectUploadPostprocessStatus(false).catch(() => {});
    }
    const changed = _syncCount(sync.indexed) + _syncCount(sync.missing_removed) + _syncCount(sync.missing_thumbs_removed);
    if (changed > 0) {
      await loadPhotos();
      try { await loadMapperTools(state.mapperPath || ''); } catch {}
    }
  } catch {
    return;
  } finally {
    mapperDiskSyncWatcherBusy = false;
  }
}

function startMapperDiskSyncWatcher() {
  if (mapperDiskSyncWatcherTimer) return;
  mapperDiskSyncWatcherTimer = window.setInterval(() => {
    checkMapperDiskSyncNow().catch(() => {});
  }, 2200);
}

function hideUploadOverlay() {
  ensureUploadOverlayRefs();
  if (!els.uploadOverlay) return;
  els.uploadOverlay.classList.remove('active', 'upload-ready', 'upload-blocked');
  els.uploadOverlay.classList.add('hidden');
}

function isUploadRunning() {
  return !!uploadTransferActive;
}

function isUploadPostprocessPhase() {
  const phaseKey = String(uploadUiState.currentPhaseLabel || '').toLowerCase();
  return !!phaseKey && phaseKey !== 'uploader';
}

function hasRawUploadWorkQueued() {
  const total = Math.max(0, Number(uploadUiState.totalFiles || 0));
  const processed = Math.max(0, Number(uploadUiState.processedFiles || 0));
  return total > 0 && processed < total;
}

function shouldShowRawUploadMonitor() {
  if (isUploadPostprocessPhase()) return false;
  return isUploadRunning() || uploadQueuePumpRunning || uploadQueue.length > 0 || hasRawUploadWorkQueued();
}

function resetUploadUiState() {
  uploadUiState.totalFiles = 0;
  uploadUiState.totalBytes = 0;
  uploadUiState.processedFiles = 0;
  uploadUiState.processedBytes = 0;
  uploadUiState.failedFiles = 0;
  uploadUiState.currentFileName = '';
  uploadUiState.currentPhaseLabel = '';
  uploadUiState.currentLoaded = 0;
  uploadUiState.currentTotal = 0;
  uploadUiState.workflowMode = 'gentle';
  uploadUiState.processStatus = null;
  uploadUiState.transferStartedAt = 0;
  uploadUiState.transferStartBytes = 0;
  uploadUiState.transferLastSampleAt = 0;
  uploadUiState.transferLastSampleBytes = 0;
  uploadUiState.transferRateBps = 0;
  uploadUiState.transferSamples = [];
  uploadUiState.transferEtaSeconds = 0;
  uploadUiState.transferLastEtaAt = 0;
  uploadMonitorItemsByKey.clear();
}

function formatUploadEta(seconds) {
  const total = Math.max(0, Math.ceil(Number(seconds || 0)));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function updateUploadTransferEstimate(uploadedBytes) {
  const now = Date.now();
  const uploaded = Math.max(0, Number(uploadedBytes || 0));
  if (!uploadUiState.transferStartedAt) {
    uploadUiState.transferStartedAt = now;
    uploadUiState.transferStartBytes = uploaded;
    uploadUiState.transferLastSampleAt = now;
    uploadUiState.transferLastSampleBytes = uploaded;
    uploadUiState.transferRateBps = 0;
    uploadUiState.transferSamples = [{ at: now, bytes: uploaded }];
    uploadUiState.transferEtaSeconds = 0;
    uploadUiState.transferLastEtaAt = 0;
    return;
  }
  const lastAt = Number(uploadUiState.transferLastSampleAt || 0);
  const lastBytes = Number(uploadUiState.transferLastSampleBytes || 0);
  if (uploaded < lastBytes) {
    uploadUiState.transferStartedAt = now;
    uploadUiState.transferStartBytes = uploaded;
    uploadUiState.transferLastSampleAt = now;
    uploadUiState.transferLastSampleBytes = uploaded;
    uploadUiState.transferRateBps = 0;
    uploadUiState.transferSamples = [{ at: now, bytes: uploaded }];
    uploadUiState.transferEtaSeconds = 0;
    uploadUiState.transferLastEtaAt = 0;
    return;
  }
  const elapsedMs = Math.max(0, now - lastAt);
  const deltaBytes = uploaded - lastBytes;
  if (elapsedMs < 900 || deltaBytes <= 0) return;
  const instantRate = deltaBytes / (elapsedMs / 1000);
  const samples = Array.isArray(uploadUiState.transferSamples) ? uploadUiState.transferSamples : [];
  samples.push({ at: now, bytes: uploaded });
  const sampleWindowMs = 18000;
  while (samples.length > 2 && (now - Number(samples[0].at || 0)) > sampleWindowMs) {
    samples.shift();
  }
  uploadUiState.transferSamples = samples;
  const firstWindowSample = samples[0] || { at: now, bytes: uploaded };
  const windowElapsedMs = Math.max(0, now - Number(firstWindowSample.at || now));
  const windowBytes = Math.max(0, uploaded - Number(firstWindowSample.bytes || 0));
  const windowRate = windowElapsedMs >= 2500 && windowBytes > 0
    ? windowBytes / (windowElapsedMs / 1000)
    : 0;
  const sessionElapsedMs = Math.max(0, now - Number(uploadUiState.transferStartedAt || now));
  const sessionBytes = Math.max(0, uploaded - Number(uploadUiState.transferStartBytes || 0));
  const sessionRate = sessionElapsedMs >= 2500 && sessionBytes > 0
    ? sessionBytes / (sessionElapsedMs / 1000)
    : 0;
  let measuredRate = instantRate;
  if (windowRate > 0 && sessionRate > 0) {
    measuredRate = (windowRate * 0.58) + (sessionRate * 0.42);
  } else if (windowRate > 0) {
    measuredRate = windowRate;
  } else if (sessionRate > 0) {
    measuredRate = sessionRate;
  }
  const currentRate = Number(uploadUiState.transferRateBps || 0);
  uploadUiState.transferRateBps = currentRate > 0
    ? ((currentRate * 0.84) + (measuredRate * 0.16))
    : measuredRate;
  uploadUiState.transferLastSampleAt = now;
  uploadUiState.transferLastSampleBytes = uploaded;
}

function uploadEtaLabel(uploadedBytes) {
  if (!isUploadRunning() || uploadStopRequested) return '';
  const now = Date.now();
  const total = Math.max(0, Number(uploadUiState.totalBytes || 0));
  const uploaded = Math.max(0, Number(uploadedBytes || 0));
  const remaining = Math.max(0, total - uploaded);
  if (!total || !remaining) return '';
  const rate = Math.max(0, Number(uploadUiState.transferRateBps || 0));
  const sampleCount = Array.isArray(uploadUiState.transferSamples) ? uploadUiState.transferSamples.length : 0;
  const estimateAgeMs = Math.max(0, now - Number(uploadUiState.transferStartedAt || now));
  if (rate < 1024 || sampleCount < 2 || estimateAgeMs < 2500) return 'tid tilbage: beregner...';
  let etaSeconds = remaining / rate;
  const previousEta = Math.max(0, Number(uploadUiState.transferEtaSeconds || 0));
  const previousAt = Number(uploadUiState.transferLastEtaAt || 0);
  if (previousEta > 0 && previousAt > 0) {
    const elapsedSeconds = Math.max(0, (now - previousAt) / 1000);
    const expectedEta = Math.max(0, previousEta - elapsedSeconds);
    const etaDelta = etaSeconds - expectedEta;
    const etaWeight = etaDelta > 0 ? 0.18 : 0.28;
    etaSeconds = expectedEta + (etaDelta * etaWeight);
  }
  uploadUiState.transferEtaSeconds = etaSeconds;
  uploadUiState.transferLastEtaAt = now;
  return `tid tilbage: ${formatUploadEta(etaSeconds)}`;
}

function setUploadStopButtonState() {
  ensureUploadMonitorRefs();
  if (!els.uploadMonitorStop) return;
  const running = isUploadRunning();
  els.uploadMonitorStop.disabled = !running || uploadStopRequested;
  els.uploadMonitorStop.textContent = uploadStopRequested ? 'Stopper…' : 'Stop upload';
}

function _uploadItemKey(name, index = null) {
  const safeName = String(name || '').trim() || '(ukendt fil)';
  return index === null || index === undefined
    ? safeName
    : `${safeName}::${String(index)}`;
}

function _setUploadMonitorItemProgress(key, pct) {
  const ref = uploadMonitorItemsByKey.get(String(key || ''));
  if (!ref || !ref.progressBar) return;
  const value = Math.max(0, Math.min(100, Number(pct || 0)));
  ref.progressBar.style.width = `${value}%`;
}

function updateUploadMonitorItem(key, ok, detail = '', progressPct = null) {
  const ref = uploadMonitorItemsByKey.get(String(key || ''));
  if (!ref || !ref.statusEl) return;
  ref.statusEl.classList.remove('ok', 'err', 'work');
  ref.statusEl.classList.add(ok === null ? 'work' : (ok ? 'ok' : 'err'));
  ref.statusEl.textContent = String(detail || (ok === null ? 'Arbejder…' : (ok ? 'OK' : 'Fejl')));
  if (progressPct !== null && progressPct !== undefined) {
    _setUploadMonitorItemProgress(key, progressPct);
  }
}

function requestStopUpload() {
  if (!isUploadRunning() || uploadStopRequested) return;
  uploadStopRequested = true;
  uploadWasStopped = true;
  uploadUiState.currentFileName = 'Stopper upload…';
  try {
    if (activeTusUpload && typeof activeTusUpload.abort === 'function') {
      activeTusUpload.abort();
    }
  } catch {}
  setUploadStopButtonState();
  renderUploadMonitor();
}

function renderUploadMonitor() {
  ensureUploadTopStatusRefs();
  ensureUploadMonitorRefs();
  const transferLoaded = uploadTransferActive ? uploadUiState.currentLoaded : 0;
  const processedVisualBytes = Math.min(uploadUiState.totalBytes, uploadUiState.processedBytes + transferLoaded);
  const overallPct = uploadUiState.totalBytes > 0
    ? Math.max(0, Math.min(100, Math.round((processedVisualBytes / uploadUiState.totalBytes) * 100)))
    : 0;
  const isPostprocess = isUploadPostprocessPhase();
  const showRawUploadMonitor = shouldShowRawUploadMonitor();
  const workflowMode = String(uploadUiState.workflowMode || 'gentle').toLowerCase();
  const useMultiTopStatus = isPostprocess && workflowMode === 'aggressive' && !!uploadUiState.processStatus;
  const stagePct = uploadUiState.currentTotal > 0
    ? Math.max(0, Math.min(100, Math.round((uploadUiState.currentLoaded / uploadUiState.currentTotal) * 100)))
    : 0;
  const stageTxt = uploadUiState.currentTotal > 0
    ? `${uploadUiState.currentLoaded}/${uploadUiState.currentTotal}`
    : 'venter…';
  const processStatusSummary = isPostprocess ? summarizeUploadProcessStatus(uploadUiState.processStatus) : '';
  const postprocessLabel = isPostprocess
    ? (processStatusSummary || `${String(uploadUiState.currentPhaseLabel || 'Efterbehandler')} · ${stageTxt} · ${stagePct}%`)
    : '';
  if (isUploadRunning() && !isPostprocess) {
    updateUploadTransferEstimate(processedVisualBytes);
  }
  const etaTxt = !isPostprocess ? uploadEtaLabel(processedVisualBytes) : '';

  if (els.uploadTopStatus) {
    const hasTopStatus = isUploadRunning() || isPostprocess || !!String(uploadUiState.currentFileName || '').trim();
    if (hasTopStatus) {
      if (useMultiTopStatus && renderUploadTopProcessStatus(uploadUiState.processStatus)) {
        if (els.uploadTopStatusLabel) els.uploadTopStatusLabel.textContent = '';
        if (els.uploadTopStatusBar) els.uploadTopStatusBar.style.width = '0%';
      } else {
        clearUploadTopProcessStatus();
        const activePct = isPostprocess ? stagePct : overallPct;
        const visibleProcessed = Math.max(0, Math.min(uploadUiState.totalFiles, uploadUiState.processedFiles));
        const phaseLabel = directUploadPostprocessUiActive
          ? `Baggrund · ${uploadUiState.currentPhaseLabel}`
          : uploadUiState.currentPhaseLabel;
        const topLabel = isPostprocess
          ? `${phaseLabel} · ${stageTxt} · ${activePct}%`
          : `Uploader · ${visibleProcessed}/${uploadUiState.totalFiles} · ${activePct}%${etaTxt ? ` · ${etaTxt.replace('tid tilbage: ', '')}` : ''}`;
        els.uploadTopStatus.classList.remove('hidden');
        if (els.uploadTopStatusLabel) els.uploadTopStatusLabel.textContent = topLabel;
        if (els.uploadTopStatusBar) els.uploadTopStatusBar.style.width = `${activePct}%`;
      }
    } else {
      clearUploadTopProcessStatus();
      els.uploadTopStatus.classList.add('hidden');
      if (els.uploadTopStatusBar) els.uploadTopStatusBar.style.width = '0%';
      if (els.uploadTopStatusLabel) els.uploadTopStatusLabel.textContent = 'Upload: Klar';
    }
  }

  // Update compact mobile status bar and badge
  try {
    const remaining = Math.max(0, Number(uploadUiState.totalFiles || 0) - Number(uploadUiState.processedFiles || 0));
    const showMini = (isUploadRunning() || (!isPostprocess && remaining > 0));
    if (els.mobileUploadBar) {
      els.mobileUploadBar.classList.toggle('hidden', !showMini);
      if (els.mobileUploadBarFill) {
        const activePct = isPostprocess ? stagePct : overallPct;
        els.mobileUploadBarFill.style.width = `${activePct}%`;
        if (els.mobileUploadPct) els.mobileUploadPct.textContent = `${activePct}%`;
        if (els.mobileUploadInfo) {
          const visibleProcessed = Math.max(0, Math.min(uploadUiState.totalFiles, uploadUiState.processedFiles));
          els.mobileUploadInfo.textContent = `${visibleProcessed}/${uploadUiState.totalFiles || 0}`;
        }
      }
    }
    // Button visibility: show while active, then linger 10s after done
    const showBtnNow = showMini; // active upload or postprocess
    if (els.mobileUploadsBtn && els.mobileBottomNav) {
      if (showBtnNow) {
        if (mobileUploadsHideTimer) { window.clearTimeout(mobileUploadsHideTimer); mobileUploadsHideTimer = null; }
        if (els.mobileUploadsBtn.classList.contains('hidden')) { els.mobileUploadsBtn.classList.remove('hidden'); void els.mobileUploadsBtn.offsetWidth; }
        els.mobileBottomNav.classList.add('with-uploads');
      } else {
        if (!mobileUploadsHideTimer) {
          mobileUploadsHideTimer = window.setTimeout(() => {
            try { els.mobileBottomNav.classList.remove('with-uploads'); } catch {}
            // After slide-out transition, fully hide to remove from a11y/tab order
            window.setTimeout(() => { try { els.mobileUploadsBtn.classList.add('hidden'); } catch {} }, 300);
            mobileUploadsHideTimer = null;
          }, 10000);
        }
      }
    }
    if (els.mobileUploadsBadge) {
      const badgeCount = Math.max(0, remaining);
      if (badgeCount > 0) {
        els.mobileUploadsBadge.textContent = String(badgeCount);
        els.mobileUploadsBadge.classList.remove('hidden');
      } else {
        els.mobileUploadsBadge.classList.add('hidden');
        els.mobileUploadsBadge.textContent = '0';
      }
    }
  } catch {}

  if (!els.uploadMonitor) return;
  if (!showRawUploadMonitor) {
    els.uploadMonitor.classList.add('hidden');
    try {
      els.uploadMonitor.style.opacity = '';
      els.uploadMonitor.style.transition = '';
    } catch {}
    if (uploadMonitorHideTimer) {
      window.clearTimeout(uploadMonitorHideTimer);
      uploadMonitorHideTimer = null;
    }
    return;
  }
  setUploadStopButtonState();

  if (els.uploadMonitorBar) els.uploadMonitorBar.style.width = `${overallPct}%`;
  if (els.uploadMonitorSummary) {
    const failedTxt = uploadUiState.failedFiles ? ` · fejl: ${uploadUiState.failedFiles}` : '';
    els.uploadMonitorSummary.textContent = isPostprocess
      ? `${postprocessLabel}${failedTxt}`
      : `${uploadUiState.processedFiles}/${uploadUiState.totalFiles} filer · ${fmtBytes(processedVisualBytes)}/${fmtBytes(uploadUiState.totalBytes)} · ${overallPct}%${etaTxt ? ` · ${etaTxt}` : ''}${failedTxt}`;
  }
  if (els.uploadMonitorCurrent) {
    if (isPostprocess) {
      const currentName = String(uploadUiState.currentFileName || '').trim();
      els.uploadMonitorCurrent.textContent = currentName
        ? `${String(uploadUiState.currentPhaseLabel || 'Efterbehandler')}: ${currentName}`
        : 'Efterbehandling i gang';
    } else if (uploadUiState.currentFileName) {
      const filePct = uploadUiState.currentTotal > 0
        ? Math.max(0, Math.min(100, Math.round((uploadUiState.currentLoaded / uploadUiState.currentTotal) * 100)))
        : 0;
      const phasePrefix = String(uploadUiState.currentPhaseLabel || '').trim() || 'Uploader';
      els.uploadMonitorCurrent.textContent = `${phasePrefix}: ${uploadUiState.currentFileName} (${filePct}%)`;
    } else {
      els.uploadMonitorCurrent.textContent = uploadUiState.totalFiles
        ? 'Upload fuldført'
        : 'Ingen aktiv upload';
    }
  }

  // Auto-hide monitor:
  // - Hide the upload monitor after raw transfer is done; postprocess keeps
  //   showing progress in the top status area.
  // - Else fallback to old behavior (hide 10s after everything done)
  try {
    const transferDone = !isUploadRunning() && uploadUiState.totalFiles > 0;
    if (transferDone) {
      if (!uploadMonitorHideTimer) {
        const delay = 10000; // always wait 10s after transfer completes
        uploadMonitorHideTimer = window.setTimeout(() => {
          if (!els.uploadMonitor) { uploadMonitorHideTimer = null; return; }
          try {
            els.uploadMonitor.style.transition = 'opacity .35s ease';
            els.uploadMonitor.style.opacity = '0';
            window.setTimeout(()=>{
              try {
                els.uploadMonitor.classList.add('hidden');
                els.uploadMonitor.style.opacity = '';
                els.uploadMonitor.style.transition = '';
              } catch {}
            }, 380);
          } catch {}
          uploadMonitorHideTimer = null;
        }, delay);
      }
    } else {
      if (uploadMonitorHideTimer) { window.clearTimeout(uploadMonitorHideTimer); uploadMonitorHideTimer = null; }
    }
  } catch {}
}

function showUploadMonitor() {
  ensureUploadMonitorRefs();
  if (!shouldShowRawUploadMonitor()) return;
  bindUploadMonitorDomEvents();
  if (els.uploadMonitor) {
    els.uploadMonitor.classList.remove('hidden');
    try { els.uploadMonitor.style.opacity = '1'; els.uploadMonitor.style.transition=''; } catch {}
  }
  if (uploadMonitorHideTimer) { window.clearTimeout(uploadMonitorHideTimer); uploadMonitorHideTimer = null; }
  const collapsed = !!uploadUiState.collapsed;
  if (els.uploadMonitor) els.uploadMonitor.classList.toggle('collapsed', collapsed);
  if (els.uploadMonitorToggle) {
    els.uploadMonitorToggle.textContent = collapsed ? 'Vis detaljer' : 'Minimer';
  }
  setUploadStopButtonState();
}

function addUploadMonitorItem(name, ok, detail = '', key = null, progressPct = null) {
  ensureUploadMonitorRefs();
  if (!els.uploadMonitorList) return;
  const li = document.createElement('li');
  li.className = 'upload-monitor-item';
  const safeName = String(name || '').trim() || '(ukendt fil)';
  const itemKey = String(key || _uploadItemKey(safeName));
  const statusClass = ok ? 'ok' : 'err';
  const statusText = ok ? 'OK' : 'Fejl';
  li.innerHTML = `
    <div class="upload-monitor-item-top">
      <span class="upload-monitor-item-name" title="${escapeHtml(safeName)}">${escapeHtml(safeName)}</span>
      <span class="upload-monitor-item-status ${statusClass}">${escapeHtml(detail || statusText)}</span>
    </div>
    <div class="upload-monitor-item-progress"><span class="upload-monitor-item-progress-bar" style="width:${Math.max(0, Math.min(100, Number(progressPct || 0)))}%"></span></div>
  `;
  els.uploadMonitorList.insertBefore(li, els.uploadMonitorList.firstChild || null);
  uploadMonitorItemsByKey.set(itemKey, {
    el: li,
    statusEl: li.querySelector('.upload-monitor-item-status'),
    progressBar: li.querySelector('.upload-monitor-item-progress-bar'),
  });
  while (els.uploadMonitorList.children.length > 8) {
    const last = els.uploadMonitorList.lastChild;
    if (!last) break;
    uploadMonitorItemsByKey.forEach((value, k) => {
      if (value && value.el === last) uploadMonitorItemsByKey.delete(k);
    });
    els.uploadMonitorList.removeChild(last);
  }
}

function uploadSingleFile(file, options = {}, onProgress = null) {
  return new Promise((resolve) => {
    const fd = new FormData();
    const safeName = String(file && file.name ? file.name : 'fil');
    fd.append('files', file, safeName);
    fd.append('meta', JSON.stringify([{ name: safeName, lastModified: Number(file && file.lastModified ? file.lastModified : 0) }]));
    const destination = (options && options.destination) ? String(options.destination) : '';
    const subdir = (options && Object.prototype.hasOwnProperty.call(options, 'subdir')) ? String(options.subdir || '') : null;
    if (destination) fd.append('destination', destination);
    if (subdir !== null) fd.append('subdir', subdir);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/upload');
    xhr.onload = () => {
      let payload = {};
      try { payload = JSON.parse(xhr.responseText || '{}'); } catch {}
      const saved = Array.isArray(payload.saved) ? payload.saved.length : 0;
      const errors = Array.isArray(payload.errors) ? payload.errors : [];
      const ok = xhr.status >= 200 && xhr.status < 300 && payload && payload.ok !== false && !(saved <= 0 && errors.length > 0);
      const firstError = errors[0];
      const errorMsg = (payload && payload.error) || (typeof firstError === 'string' ? firstError : (firstError && (firstError.error || firstError.name))) || '';
      resolve({ ok, saved, errorMsg });
    };
    xhr.onerror = () => resolve({ ok: false, saved: 0, errorMsg: 'Netværksfejl' });
    xhr.upload.onprogress = (evt) => {
      if (typeof onProgress === 'function') {
        onProgress(Number(evt && evt.loaded ? evt.loaded : 0), Number(evt && evt.total ? evt.total : 0));
      }
    };
    xhr.send(fd);
  });
}

function hasTusClient() {
  return !!(window.tus && typeof window.tus.Upload === 'function');
}

function postprocessPhaseLabel(phase) {
  const key = String(phase || '').toLowerCase();
  if (key === 'converting') return 'Konverterer RAW/HEIC/MOV';
  if (key === 'metadata') return 'Metadata';
  if (key === 'thumbnails') return 'Thumbnails';
  if (key === 'faces') return 'Ansigtsgenkendelse';
  if (key === 'embeddings') return 'AI embeddings';
  if (key === 'descriptions') return 'AI beskrivelser';
  if (key === 'parallel') return tr('tab_upload_workflow');
  if (key === 'starting') return 'Starter efterbehandling';
  if (key === 'done') return 'Efterbehandling færdig';
  if (key === 'error') return 'Efterbehandling fejl';
  return 'Efterbehandler';
}

function shortRelName(relPath) {
  const rel = String(relPath || '').trim();
  if (!rel) return '';
  const parts = rel.split('/').filter(Boolean);
  return parts.length ? parts[parts.length - 1] : rel;
}

function uploadPostprocessPollDelayMs(statusLike = null) {
  const status = (statusLike && typeof statusLike === 'object') ? statusLike : {};
  const mode = String((status.workflow_mode || uploadUiState.workflowMode || 'gentle')).toLowerCase();
  const phase = String(status.phase || '').toLowerCase();
  const proc = (status.process_status && typeof status.process_status === 'object') ? status.process_status : null;
  if (mode === 'aggressive' && (phase === 'parallel' || phase === 'faces' || !!proc)) {
    return 250;
  }
  return 900;
}

async function runUploadPostprocess(onProgress = null) {
  const startRes = await fetch('/api/upload/postprocess', { method: 'POST' });
  let startData = {};
  try { startData = await startRes.json(); } catch {}
  if (!startRes.ok || !startData.ok) {
    const msg = (startData && startData.error) ? String(startData.error) : 'Efterbehandling fejlede';
    throw new Error(msg);
  }

  if (!startData.running) {
    return startData.result || {
      ok: true,
      received: 0,
      indexed: 0,
      index_errors: 0,
      faces_enabled: false,
      faces_done: 0,
      faces_errors: 0,
      ai_enabled: false,
      ai_done: 0,
      ai_errors: 0,
      ai_desc_enabled: false,
      ai_desc_done: 0,
      ai_desc_errors: 0,
    };
  }

  const deadline = Date.now() + (24 * 60 * 60 * 1000);
  while (Date.now() < deadline) {
    const statusRes = await fetch('/api/upload/postprocess/status');
    let statusData = {};
    try { statusData = await statusRes.json(); } catch {}
    if (!statusRes.ok || !statusData.ok) {
      const msg = (statusData && statusData.error) ? String(statusData.error) : 'Efterbehandling status fejlede';
      throw new Error(msg);
    }
    if (statusData.running && typeof onProgress === 'function') {
      onProgress(statusData);
    }
    if (!statusData.running) {
      if (statusData.error) throw new Error(String(statusData.error));
      return statusData.result || {
        ok: true,
        received: 0,
        indexed: 0,
        index_errors: 0,
        faces_enabled: false,
        faces_done: 0,
        faces_errors: 0,
        ai_enabled: false,
        ai_done: 0,
        ai_errors: 0,
        ai_desc_enabled: false,
        ai_desc_done: 0,
        ai_desc_errors: 0,
      };
    }
    await new Promise((resolve) => window.setTimeout(resolve, uploadPostprocessPollDelayMs(statusData)));
  }

  throw new Error('Efterbehandling timeout');
}

let uploadPostprocessResumeActive = false;
async function resumeUploadPostprocessAfterRefresh() {
  if (uploadPostprocessResumeActive) return;
  if (uploadQueuePumpRunning || isUploadRunning()) return;
  uploadPostprocessResumeActive = true;
  try {
    const readStatus = async () => {
      const res = await fetch('/api/upload/postprocess/status');
      let data = {};
      try { data = await res.json(); } catch {}
      if (!res.ok || !data || !data.ok) return null;
      return data;
    };

    let status = await readStatus();
    if (!status) return;

    // If a refresh happened before postprocess started, kick it off automatically.
    if (!status.running && (Number(status.pending || 0) > 0 || Number(status.recoverable_pending || 0) > 0)) {
      try {
        const startRes = await fetch('/api/upload/postprocess', { method: 'POST' });
        let startData = {};
        try { startData = await startRes.json(); } catch {}
        if (!startRes.ok || !startData || !startData.ok) return;
      } catch {
        return;
      }
      status = await readStatus();
      if (!status) return;
    }

    if (!status.running) return;

    uploadUiState.collapsed = false;

    while (status && status.running && !uploadQueuePumpRunning && !isUploadRunning()) {
      const stageTotal = Number(status.stage_total || 0);
      const stageProcessed = Number(status.stage_processed || 0);
      if (stageTotal > 0) uploadUiState.totalFiles = Math.max(uploadUiState.totalFiles, stageTotal);
      if (stageProcessed > 0) uploadUiState.processedFiles = Math.max(uploadUiState.processedFiles, stageProcessed);
      uploadUiState.workflowMode = String(status.workflow_mode || uploadUiState.workflowMode || 'gentle').toLowerCase();
      uploadUiState.processStatus = (status.process_status && typeof status.process_status === 'object') ? status.process_status : null;
      const useParallel = uploadUiState.workflowMode === 'aggressive' && !!uploadUiState.processStatus;
      uploadUiState.currentPhaseLabel = useParallel ? tr('tab_upload_workflow') : postprocessPhaseLabel(status.phase);
      uploadUiState.currentFileName = useParallel ? tr('upload_workflow_running') : (shortRelName(status.current_rel) || 'Arbejder…');
      uploadUiState.currentLoaded = stageProcessed;
      uploadUiState.currentTotal = stageTotal;
      renderUploadMonitor();

      const phase = String(status.phase || '').toLowerCase();
      const proc = (status.process_status && typeof status.process_status === 'object') ? status.process_status : null;
      const parallelRefresh = (phase === 'parallel') && !!proc;
      if (phase === 'metadata' || phase === 'thumbnails' || phase === 'faces' || parallelRefresh) {
        // Refresh during 'faces' too to reveal any thumbnails that finished
        // right at the phase boundary.
        maybeRefreshPhotosDuringPostprocess(false);
      }

      await new Promise((resolve) => window.setTimeout(resolve, uploadPostprocessPollDelayMs(status)));
      status = await readStatus();
    }

    uploadUiState.currentFileName = '';
    uploadUiState.currentPhaseLabel = '';
    uploadUiState.currentLoaded = 0;
    uploadUiState.currentTotal = 0;
    uploadUiState.workflowMode = 'gentle';
    uploadUiState.processStatus = null;
    renderUploadMonitor();

    await maybeRefreshPhotosDuringPostprocess(true);
    if (state.view === 'mapper') loadMapperTools();
  } finally {
    uploadPostprocessResumeActive = false;
  }
}

function uploadSingleFileTus(file, options = {}, onProgress = null) {
  return new Promise((resolve) => {
    let settled = false;
    const done = (payload) => {
      if (settled) return;
      settled = true;
      if (activeTusUpload && activeTusUpload.__fjordlens_file === file) {
        activeTusUpload = null;
      }
      resolve(payload);
    };

    if (uploadStopRequested) {
      done({ ok: false, aborted: true, saved: 0, errorMsg: 'Stoppet af bruger' });
      return;
    }

    if (!hasTusClient()) {
      done({ ok: false, saved: 0, errorMsg: 'TUS client unavailable' });
      return;
    }
    const safeName = String(file && file.name ? file.name : 'fil');
    const destination = (options && options.destination) ? String(options.destination) : '';
    const subdir = (options && Object.prototype.hasOwnProperty.call(options, 'subdir')) ? String(options.subdir || '') : '';
    const metadata = {
      filename: safeName,
      destination,
      subdir,
      lastModified: String(Number(file && file.lastModified ? file.lastModified : 0)),
    };

    const upload = new window.tus.Upload(file, {
      endpoint: '/api/upload/tus',
      metadata,
      uploadDataDuringCreation: false,
      overridePatchMethod: true,
      chunkSize: 2 * 1024 * 1024,
      parallelUploads: 1,
      retryDelays: [0, 1000, 2500, 5000],
      removeFingerprintOnSuccess: true,
      onShouldRetry(error, retryAttempt, options) {
        try {
          const status = Number(error && error.originalResponse && error.originalResponse.getStatus && error.originalResponse.getStatus());
          if ([502, 503, 504].includes(status)) return true;
        } catch {}
        return window.tus.defaultOptions.onShouldRetry(error, retryAttempt, options);
      },
      onProgress(bytesUploaded, bytesTotal) {
        if (typeof onProgress === 'function') onProgress(Number(bytesUploaded || 0), Number(bytesTotal || 0));
      },
      onError(error) {
        if (uploadStopRequested) {
          done({ ok: false, aborted: true, saved: 0, errorMsg: 'Stoppet af bruger' });
          return;
        }
        const message = (error && error.message) ? String(error.message) : 'Upload fejl';
        done({ ok: false, saved: 0, errorMsg: message });
      },
      onSuccess() {
        done({ ok: true, saved: 1, errorMsg: '' });
      },
    });

    upload.__fjordlens_file = file;
    activeTusUpload = upload;
    setUploadStopButtonState();

    upload.findPreviousUploads().then((previousUploads) => {
      if (uploadStopRequested) {
        done({ ok: false, aborted: true, saved: 0, errorMsg: 'Stoppet af bruger' });
        return;
      }
      if (Array.isArray(previousUploads) && previousUploads.length > 0) {
        upload.resumeFromPreviousUpload(previousUploads[0]);
      }
      upload.start();
    }).catch(() => {
      if (uploadStopRequested) {
        done({ ok: false, aborted: true, saved: 0, errorMsg: 'Stoppet af bruger' });
        return;
      }
      upload.start();
    });
  });
}

async function uploadSingleFileTusWithAutoResume(file, options = {}, onProgress = null, onAttempt = null) {
  const maxAttempts = 3;
  let last = null;
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    if (typeof onAttempt === 'function') {
      try { onAttempt(attempt, maxAttempts); } catch {}
    }
    const result = await uploadSingleFileTus(file, options, onProgress);
    last = result;
    if (!result || result.ok || result.aborted) return result;
    if (attempt >= maxAttempts) break;
    await new Promise((resolve) => window.setTimeout(resolve, 900 * attempt));
  }
  return last || { ok: false, saved: 0, errorMsg: 'Upload fejl' };
}

async function uploadFiles(fileList, options = {}) {
  ensureUploadOverlayRefs();
  ensureUploadMonitorRefs();
  const selectedFiles = Array.from(fileList || []).filter(f => !!f && f.name);
  if (!selectedFiles.length) return { ok: false, queued: 0 };
  await ensureUploadFileTypeSettingsLoaded();
  const split = filterUploadFilesByAllowed(selectedFiles);
  const files = split.allowed;
  if (!files.length) {
    if (split.blocked.length) showBlockedUploadFiles(split.blocked);
    return { ok: false, queued: 0 };
  }
  const destination = (options && options.destination) ? String(options.destination) : '';
  const subdir = (options && Object.prototype.hasOwnProperty.call(options, 'subdir')) ? String(options.subdir || '') : null;
  const totalSize = files.reduce((s,f)=>s+ (f.size||0), 0);

  _maybeAnnounceAutoResumeForBatch(files, destination, subdir || '');
  _queueUploadDraftFiles(files, destination, subdir || '');

  if (!uploadQueuePumpRunning && !isUploadRunning()) {
    resetUploadUiState();
    uploadStopRequested = false;
    uploadWasStopped = false;
    activeTusUpload = null;
    uploadSessionSavedTotal = 0;
    uploadImmediateRevealDone = false;
    uploadUiState.collapsed = false;
    if (els.uploadMonitorList) els.uploadMonitorList.innerHTML = '';

    if (els.uploadOverlay) {
      const titleEl = document.querySelector('#uploadOverlay .upload-title');
      if (titleEl) titleEl.textContent = 'Starter upload…';
      els.uploadOverlay.classList.remove('hidden');
      els.uploadOverlay.classList.add('active', 'upload-ready');
      if (uploadOverlayHideTimer) {
        window.clearTimeout(uploadOverlayHideTimer);
        uploadOverlayHideTimer = null;
      }
      uploadOverlayHideTimer = window.setTimeout(() => {
        hideUploadOverlay();
        uploadOverlayHideTimer = null;
      }, 900);
    }
    if (els.uploadProgressBar) els.uploadProgressBar.style.width = '100%';
  }
  if (split.blocked.length) showBlockedUploadFiles(split.blocked);

  uploadUiState.totalFiles += files.length;
  uploadUiState.totalBytes += totalSize;
  if (els.uploadProgressText) {
    const queuedCount = Math.max(0, uploadUiState.totalFiles - uploadUiState.processedFiles);
    els.uploadProgressText.textContent = `${queuedCount} filer i kø · ${fmtBytes(uploadUiState.totalBytes)}`;
  }
  renderUploadMonitor();
  if (!isSmallMobile()) showUploadMonitor();

  const batchId = ++uploadBatchSeq;
  const batchPromise = new Promise((resolve) => {
    uploadQueue.push({ batchId, files, destination, subdir, resolve });
  });

  if (!uploadQueuePumpRunning) {
    const runQueue = async () => {
      let post = null;
      try {
        uploadQueuePumpRunning = true;
        startUploadTransferHeartbeat();
        await setUploadTransferState(true);
        let finished = false;
        while (!finished) {
          uploadTransferActive = true;
          setUploadStopButtonState();

          while (uploadQueue.length && !uploadStopRequested) {
            const batch = uploadQueue.shift();
            if (!batch) continue;
            let batchSaved = 0;
            let batchFailed = 0;

            for (let fileIndex = 0; fileIndex < batch.files.length; fileIndex += 1) {
              const file = batch.files[fileIndex];
              const itemKey = _uploadItemKey(file.name, `${batch.batchId}-${fileIndex}`);
              if (uploadStopRequested) break;

              uploadUiState.currentPhaseLabel = 'Uploader';
              uploadUiState.currentFileName = file.name || 'fil';
              uploadUiState.currentLoaded = 0;
              uploadUiState.currentTotal = Number(file.size || 0);
              addUploadMonitorItem(file.name, null, 'Uploader… 0%', itemKey, 0);
              renderUploadMonitor();

              if (!hasTusClient()) {
                throw new Error('TUS client mangler i browseren');
              }
              let result;
              const useTus = hasTusClient() && Number(file && file.size || 0) > (1024 * 1024); // >1MB → TUS
              if (useTus) {
                result = await uploadSingleFileTusWithAutoResume(
                  file,
                  { destination: batch.destination, subdir: batch.subdir },
                  (loaded, total) => {
                    uploadUiState.currentLoaded = Number(loaded || 0);
                    uploadUiState.currentTotal = Number(total || file.size || 0);
                    const pct = Number(total || file.size || 0) > 0
                      ? Math.max(0, Math.min(100, Math.round((Number(loaded || 0) / Number(total || file.size || 0)) * 100)))
                      : 0;
                    updateUploadMonitorItem(itemKey, null, `Uploader… ${pct}%`, pct);
                    renderUploadMonitor();
                  },
                  (attempt, maxAttempts) => {
                    if (attempt <= 1) return;
                    updateUploadMonitorItem(itemKey, null, `Genoptager upload… (${attempt}/${maxAttempts})`, null);
                    renderUploadMonitor();
                  }
                );
              } else {
                result = await uploadSingleFile(
                  file,
                  { destination: batch.destination, subdir: batch.subdir },
                  (loaded, total) => {
                    uploadUiState.currentLoaded = Number(loaded || 0);
                    uploadUiState.currentTotal = Number(total || file.size || 0);
                    const pct = Number(total || file.size || 0) > 0
                      ? Math.max(0, Math.min(100, Math.round((Number(loaded || 0) / Number(total || file.size || 0)) * 100)))
                      : 0;
                    updateUploadMonitorItem(itemKey, null, `Uploader… ${pct}%`, pct);
                    renderUploadMonitor();
                  }
                );
              }

              if (result && result.aborted) {
                updateUploadMonitorItem(itemKey, false, 'Stoppet', 0);
                renderUploadMonitor();
                break;
              }

              uploadUiState.processedFiles += 1;
              uploadUiState.processedBytes += Number(file.size || uploadUiState.currentTotal || 0);
              uploadUiState.currentLoaded = 0;
              uploadUiState.currentTotal = 0;

              if (result.ok) {
                const saved = Number(result.saved || 0) || 1;
                batchSaved += saved;
                uploadSessionSavedTotal += saved;
                _markUploadDraftFileDone(file);
                updateUploadMonitorItem(itemKey, true, `Uploadet · ${fmtBytes(file.size || 0)}`, 100);
                // Do not refresh grid during raw upload; wait until metadata/thumbnails phase
                // so the flow is strictly: upload -> metadata -> thumbnails -> faces/AI.
                // Refreshes now happen from the postprocess progress callback below.
              } else {
                batchFailed += 1;
                uploadUiState.failedFiles += 1;
                updateUploadMonitorItem(itemKey, false, result.errorMsg || 'Fejl', 0);
              }

              renderUploadMonitor();
            }

            try { batch.resolve({ ok: !uploadStopRequested, saved: batchSaved, failed: batchFailed, stopped: !!uploadStopRequested }); } catch {}
          }

          uploadTransferActive = false;
          setUploadStopButtonState();

          if (uploadStopRequested) {
            while (uploadQueue.length) {
              const skipped = uploadQueue.shift();
              if (!skipped) continue;
              try { skipped.resolve({ ok: false, saved: 0, failed: skipped.files.length, stopped: true }); } catch {}
            }
            finished = true;
            break;
          }

          const queueQuietUntil = Date.now() + 700;
          while (!uploadStopRequested && !uploadQueue.length && Date.now() < queueQuietUntil) {
            await new Promise((resolve) => window.setTimeout(resolve, 70));
          }
          if (uploadStopRequested) {
            finished = true;
            break;
          }
          if (uploadQueue.length) {
            continue;
          }

          if (uploadUiState.processedFiles <= 0) {
            finished = true;
            break;
          }

          await stopUploadTransferHeartbeat();
          uploadUiState.currentPhaseLabel = 'Efterbehandler';
          uploadUiState.currentFileName = 'Klargør…';
          uploadUiState.currentLoaded = 0;
          uploadUiState.currentTotal = 0;
          renderUploadMonitor();

          try {
            post = await runUploadPostprocess((status) => {
              uploadUiState.workflowMode = String(status.workflow_mode || uploadUiState.workflowMode || 'gentle').toLowerCase();
              uploadUiState.processStatus = (status.process_status && typeof status.process_status === 'object') ? status.process_status : null;
              const useParallel = uploadUiState.workflowMode === 'aggressive' && !!uploadUiState.processStatus;
              uploadUiState.currentPhaseLabel = useParallel ? tr('tab_upload_workflow') : postprocessPhaseLabel(status.phase);
              const n = shortRelName(status.current_rel);
              uploadUiState.currentFileName = useParallel ? tr('upload_workflow_running') : (n || 'Arbejder…');
              uploadUiState.currentLoaded = Number(status.stage_processed || 0);
              uploadUiState.currentTotal = Number(status.stage_total || 0);
              const phase = String(status.phase || '').toLowerCase();
              const proc = (status.process_status && typeof status.process_status === 'object') ? status.process_status : null;
              const parallelRefresh = (phase === 'parallel') && !!proc;
              if (['metadata','thumbnails','faces'].includes(phase) || parallelRefresh) {
                maybeRefreshPhotosDuringPostprocess(false);
              }
              renderUploadMonitor();
            });
          } catch (postErr) {
            console.error(postErr);
            showStatus(`Upload færdig, men efterbehandling fejlede: ${postErr && postErr.message ? postErr.message : 'ukendt fejl'}`, 'err');
          }

          if (uploadQueue.length) {
            post = null;
            continue;
          }

          finished = true;
        }

        uploadUiState.currentFileName = '';
        uploadUiState.currentPhaseLabel = '';
        uploadUiState.currentLoaded = 0;
        uploadUiState.currentTotal = 0;
        uploadUiState.workflowMode = 'gentle';
        uploadUiState.processStatus = null;
        renderUploadMonitor();
        // Ensure the monitor auto-hides after uploads are fully done
        scheduleUploadMonitorAutoHide(10000);

        if (post) {
          const thumbsDone = Math.max(0, Number(post.indexed || 0) - Number(post.thumb_errors || 0));
          const postParts = [
            `thumbs: ${thumbsDone}${Number(post.thumb_errors || 0) ? ` (fejl: ${Number(post.thumb_errors || 0)})` : ''}`,
            `${Number(post.heic_converted || 0) ? `konverteret: ${Number(post.heic_converted || 0)}` : ''}`,
            `ansigter: ${Number(post.faces_done || 0)}${Number(post.faces_errors || 0) ? ` (fejl: ${Number(post.faces_errors || 0)})` : ''}`,
            `embeddings: ${Number(post.ai_done || 0)}${Number(post.ai_errors || 0) ? ` (fejl: ${Number(post.ai_errors || 0)})` : ''}`,
            `beskrivelser: ${Number(post.ai_desc_done || 0)}${Number(post.ai_desc_errors || 0) ? ` (fejl: ${Number(post.ai_desc_errors || 0)})` : ''}`,
          ];
          showStatus(
            `${uploadWasStopped ? 'Upload stoppet' : 'Upload færdig'}: ${uploadSessionSavedTotal} fil(er)${uploadUiState.failedFiles ? `, fejl: ${uploadUiState.failedFiles}` : ''} · ${postParts.filter(Boolean).join(' · ')}`,
            (uploadUiState.failedFiles || Number(post.index_errors || 0) || Number(post.faces_errors || 0) || Number(post.ai_errors || 0) || Number(post.ai_desc_errors || 0)) ? 'err' : 'ok'
          );
        } else {
          showStatus(
            `${uploadWasStopped ? 'Upload stoppet' : 'Upload færdig'}: ${uploadSessionSavedTotal} fil(er)${uploadUiState.failedFiles ? `, fejl: ${uploadUiState.failedFiles}` : ''}`,
            uploadUiState.failedFiles ? 'err' : 'ok'
          );
        }

        await maybeRefreshPhotosDuringPostprocess(true);
        if (state.view === 'mapper') {
          loadMapperTools();
        }
      } catch (e) {
        console.error(e);
        showStatus(tr('upload_failed_generic'), 'err');
      } finally {
        activeTusUpload = null;
        uploadStopRequested = false;
        uploadTransferActive = false;
        uploadQueuePumpRunning = false;
        await stopUploadTransferHeartbeat();
        const draft = _readUploadResumeDraft();
        if (draft && !(draft.pending || []).length) {
          _clearUploadResumeDraft();
        }
        if (uploadOverlayHideTimer) {
          window.clearTimeout(uploadOverlayHideTimer);
          uploadOverlayHideTimer = null;
        }
        hideUploadOverlay();
        // Efter afsluttet upload: opdater kun UI og bevar evt. auto-hide timer
        renderUploadMonitor();
      }
    };
    runQueue();
  }

  return batchPromise;
}

function renderMapperContext(path = '') {
  const p = String(path || '');
  const selFolders = state.mapperSelectedFolders ? state.mapperSelectedFolders.size : 0;
  const selPhotos = state.mapperSelectedPhotoIds ? state.mapperSelectedPhotoIds.size : 0;
  const selectedCount = selFolders + selPhotos;
  if (els.mapperCurrentPath) {
    els.mapperCurrentPath.textContent = `${tr('mapper_current_folder')}: ${p ? `uploads/${p}` : tr('mapper_root_folder')}`;
    // On mobile, hide the current-path label while in selection mode to make room for buttons
    try {
      const isMobile = window.matchMedia('(max-width: 760px)').matches;
      els.mapperCurrentPath.classList.toggle('hidden', !!state.mapperEditMode && isMobile);
    } catch {}
  }
  if (els.mapperDropZone) {
    els.mapperDropZone.textContent = `${tr('mapper_drop_here')}: ${p || tr('mapper_root_folder')}`;
    els.mapperDropZone.classList.toggle('hidden', !!state.mapperEditMode);
  }
  if (els.mapperUpBtn) {
    els.mapperUpBtn.textContent = tr('mapper_up');
    els.mapperUpBtn.disabled = !p;
  }
  if (els.mapperEditBtn) {
    els.mapperEditBtn.textContent = tr('mapper_edit');
    const mapperEditTitle = tr('mapper_edit_title');
    els.mapperEditBtn.title = mapperEditTitle;
    els.mapperEditBtn.setAttribute('aria-label', mapperEditTitle);
  }
  if (els.mapperHeaderEditAction) {
    els.mapperHeaderEditAction.textContent = state.mapperEditMode
      ? (selectedCount > 0 ? `${tr('mapper_delete_selected')} (${selectedCount})` : tr('mapper_menu_done'))
      : tr('mapper_menu_edit');
  }
  if (els.mapperHeaderShareAction) {
    els.mapperHeaderShareAction.textContent = tr('mapper_menu_share');
    // Sharing operates on folders only
    const canShare = !!state.mapperEditMode && selFolders >= 1;
    els.mapperHeaderShareAction.disabled = !canShare;
    els.mapperHeaderShareAction.title = canShare ? tr('mapper_menu_share') : tr('mapper_share_select_one');
  }
  if (els.mapperHeaderCreateAction) {
    els.mapperHeaderCreateAction.textContent = tr('mapper_menu_create');
    els.mapperHeaderCreateAction.disabled = !!state.mapperEditMode;
    els.mapperHeaderCreateAction.title = state.mapperEditMode ? tr('mapper_done_title') : tr('mapper_menu_create');
  }
  if (els.mapperHeaderUploadAction) {
    els.mapperHeaderUploadAction.textContent = tr('mapper_menu_upload');
    els.mapperHeaderUploadAction.disabled = !!state.mapperEditMode;
    els.mapperHeaderUploadAction.title = state.mapperEditMode ? tr('mapper_done_title') : tr('mapper_menu_upload');
  }
  const mapperSortMode = _normalizeMapperSort(state.mapperSort);
  if (els.mapperHeaderSortNewestAction) {
    const isActive = mapperSortMode === 'date_desc';
    els.mapperHeaderSortNewestAction.textContent = tr('sort_date_desc');
    els.mapperHeaderSortNewestAction.disabled = !!state.mapperEditMode || isActive;
    els.mapperHeaderSortNewestAction.classList.toggle('is-active-sort', isActive);
    els.mapperHeaderSortNewestAction.title = tr('sort_date_desc');
  }
  if (els.mapperHeaderSortOldestAction) {
    const isActive = mapperSortMode === 'date_asc';
    els.mapperHeaderSortOldestAction.textContent = tr('sort_date_asc');
    els.mapperHeaderSortOldestAction.disabled = !!state.mapperEditMode || isActive;
    els.mapperHeaderSortOldestAction.classList.toggle('is-active-sort', isActive);
    els.mapperHeaderSortOldestAction.title = tr('sort_date_asc');
  }
  if (els.mapperHeaderRenameAction) {
    const canRenameInEdit = !!state.mapperEditMode && selFolders === 1 && selPhotos === 0;
    const canRenameCurrent = !state.mapperEditMode && !!p;
    const canRename = canRenameInEdit || canRenameCurrent;
    els.mapperHeaderRenameAction.textContent = tr('mapper_menu_rename');
    els.mapperHeaderRenameAction.disabled = !canRename;
    if (state.mapperEditMode) {
      els.mapperHeaderRenameAction.title = canRename ? tr('mapper_menu_rename') : tr('mapper_rename_select_one');
    } else {
      els.mapperHeaderRenameAction.title = canRename ? tr('mapper_menu_rename') : tr('mapper_rename_root_block');
    }
  }
  if (els.mapperDeleteBtn) {
    const show = !!state.mapperEditMode;
    const canDelete = show && selectedCount > 0;
    els.mapperDeleteBtn.classList.toggle('hidden', !show);
    els.mapperDeleteBtn.disabled = !canDelete;
    els.mapperDeleteBtn.textContent = canDelete
      ? `${tr('mapper_delete_selected')} (${selectedCount})`
      : tr('mapper_delete_selected');
  }
  if (els.mapperDownloadBtn) {
    const show = !!state.mapperEditMode;
    const canDownload = show && (selPhotos > 0);
    els.mapperDownloadBtn.classList.toggle('hidden', !show);
    els.mapperDownloadBtn.disabled = !canDownload;
    els.mapperDownloadBtn.textContent = tr('mapper_download');
  }
  if (els.mapperSelectAllBtn) {
    const show = !!state.mapperEditMode;
    els.mapperSelectAllBtn.classList.toggle('hidden', !show);
    els.mapperSelectAllBtn.textContent = tr('mapper_select_all');
    // Enable when there are any selectable items visible
    try {
      const hasTargets = !!document.querySelector('.gallery-grid .folder-card, .gallery-grid .photo-card:not(.folder-card):not(.upload-card)');
      els.mapperSelectAllBtn.disabled = !hasTargets;
    } catch { els.mapperSelectAllBtn.disabled = false; }
  }
  if (els.mapperClearBtn) {
    const show = !!state.mapperEditMode;
    els.mapperClearBtn.classList.toggle('hidden', !show);
    els.mapperClearBtn.textContent = tr('mapper_clear_selection');
    els.mapperClearBtn.disabled = !(selectedCount > 0);
  }
  if (els.mapperCancelBtn) {
    const show = !!state.mapperEditMode;
    els.mapperCancelBtn.classList.toggle('hidden', !show);
    els.mapperCancelBtn.textContent = tr('mapper_cancel');
  }
  renderMapperTree();
}

function openDownloadModal(){
  if (!els.mapperDownloadModal) return;
  els.mapperDownloadModal.classList.remove('hidden');
}
function closeDownloadModal(){ if (els.mapperDownloadModal) els.mapperDownloadModal.classList.add('hidden'); }

let _downloadStatusTimer = null;
let _activeDownloadController = null;
let _downloadInProgress = false;
function _scheduleDownloadStatusHide(ms = 4200) {
  try { if (_downloadStatusTimer) clearTimeout(_downloadStatusTimer); } catch {}
  _downloadStatusTimer = setTimeout(() => {
    hideDownloadTopStatusMessage();
    _downloadStatusTimer = null;
  }, Math.max(0, Number(ms || 0)));
}

function cancelActiveMapperDownload() {
  if (!_activeDownloadController || !_downloadInProgress) return false;
  try { _activeDownloadController.abort(); } catch {}
  return true;
}

function _formatByteSize(bytes) {
  const n = Number(bytes || 0);
  if (!Number.isFinite(n) || n <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let value = n;
  let idx = 0;
  while (value >= 1024 && idx < units.length - 1) {
    value /= 1024;
    idx += 1;
  }
  const decimals = (value >= 100 || idx === 0) ? 0 : 1;
  return `${value.toFixed(decimals)} ${units[idx]}`;
}

function _extractFilenameFromDisposition(disposition, fallbackName) {
  const raw = String(disposition || '').trim();
  if (!raw) return String(fallbackName || 'download.bin');
  const star = raw.match(/filename\*=([^;]+)/i);
  if (star && star[1]) {
    let value = String(star[1]).trim().replace(/^UTF-8''/i, '');
    value = value.replace(/^"(.*)"$/, '$1');
    try {
      return decodeURIComponent(value) || String(fallbackName || 'download.bin');
    } catch {
      return value || String(fallbackName || 'download.bin');
    }
  }
  const plain = raw.match(/filename="?([^";]+)"?/i);
  if (plain && plain[1]) return String(plain[1]).trim();
  return String(fallbackName || 'download.bin');
}

function _downloadFileFromBlob(blob, filename) {
  const a = document.createElement('a');
  const url = URL.createObjectURL(blob);
  a.href = url;
  a.download = String(filename || 'download.bin');
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    URL.revokeObjectURL(url);
    a.remove();
  }, 1000);
}

async function _extractDownloadErrorMessage(res) {
  const fallback = `${tr('download_status_failed')} (HTTP ${Number(res && res.status || 0) || '?'})`;
  if (!res) return fallback;
  try {
    const ct = String(res.headers && res.headers.get && res.headers.get('content-type') || '').toLowerCase();
    if (ct.includes('application/json')) {
      const payload = await res.json().catch(() => null);
      const msg = payload && (payload.error || payload.message);
      return String(msg || fallback);
    }
    const txt = await res.text().catch(() => '');
    const cleaned = String(txt || '').trim();
    return cleaned || fallback;
  } catch {
    return fallback;
  }
}

async function _fetchBlobWithProgress(url, options, onProgress) {
  const res = await fetch(url, options);
  if (!res.ok) return { ok: false, res };
  const totalRaw = Number(res.headers.get('content-length') || 0);
  const total = Number.isFinite(totalRaw) && totalRaw > 0 ? totalRaw : 0;
  if (!res.body || typeof res.body.getReader !== 'function') {
    const blob = await res.blob();
    if (typeof onProgress === 'function') onProgress(blob.size, total || blob.size, 100, true);
    return { ok: true, res, blob };
  }
  const reader = res.body.getReader();
  const chunks = [];
  let received = 0;
  while (true) {
    const chunk = await reader.read();
    if (chunk.done) break;
    if (chunk.value && chunk.value.byteLength) {
      chunks.push(chunk.value);
      received += chunk.value.byteLength;
      const pct = total > 0 ? Math.max(0, Math.min(100, Math.round((received / total) * 100))) : null;
      if (typeof onProgress === 'function') onProgress(received, total, pct, total > 0);
    }
  }
  const blob = new Blob(chunks, { type: res.headers.get('content-type') || 'application/octet-stream' });
  if (typeof onProgress === 'function' && total <= 0) onProgress(received, Math.max(received, 1), 100, true);
  return { ok: true, res, blob };
}

async function runMapperDownload(mode){
  const ids = Array.from(state.mapperSelectedPhotoIds || []);
  if (!ids.length) { showStatus(tr('mapper_select_download_none'), 'err'); return; }
  if (_downloadInProgress) {
    showStatus(tr('download_status_already_running'), 'err');
    return;
  }
  try { if (_downloadStatusTimer) clearTimeout(_downloadStatusTimer); } catch {}
  _downloadInProgress = true;
  _activeDownloadController = new AbortController();
  const isSingle = ids.length === 1;
  const fallbackName = isSingle ? `photo_${ids[0]}` : `fjordlens_download_${ids.length}.zip`;
  showDownloadTopStatusMessage(tr('download_status_preparing'));
  setDownloadTopStatusIndeterminate(true);
  setDownloadTopStatusCancelable(true);
  try {
    const url = isSingle
      ? `/api/photos/download/${encodeURIComponent(ids[0])}?mode=${encodeURIComponent(mode)}`
      : '/api/photos/download-zip';
    const init = isSingle
      ? { method: 'GET', signal: _activeDownloadController.signal }
      : {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ photo_ids: ids, mode }),
          signal: _activeDownloadController.signal,
        };
    showDownloadTopStatusMessage(tr(isSingle ? 'download_status_fetching_one' : 'download_status_zipping'));
    const result = await _fetchBlobWithProgress(url, init, (received, total, pct, hasPct) => {
      if (hasPct && pct != null) {
        setDownloadTopStatusIndeterminate(false);
        showDownloadTopStatusMessage(tr('download_status_receiving').replace('{pct}', String(pct)), pct);
        return;
      }
      const labelKey = isSingle ? 'download_status_fetching_one' : 'download_status_zipping';
      showDownloadTopStatusMessage(`${tr(labelKey)} (${_formatByteSize(received)})`);
    });
    if (!result.ok) {
      setDownloadTopStatusIndeterminate(false);
      const msg = await _extractDownloadErrorMessage(result.res);
      showDownloadTopStatusMessage(`${tr('download_status_failed')}: ${msg}`);
      showStatus(msg, 'err');
      _scheduleDownloadStatusHide(7000);
      return;
    }
    const fileName = _extractFilenameFromDisposition(result.res.headers.get('content-disposition'), fallbackName);
    _downloadFileFromBlob(result.blob, fileName);
    setDownloadTopStatusIndeterminate(false);
    showDownloadTopStatusMessage(`${tr('download_status_done')}: ${fileName}`, 100);
    _scheduleDownloadStatusHide();
  } catch (err) {
    setDownloadTopStatusIndeterminate(false);
    const isAbort = !!(err && (err.name === 'AbortError' || String(err.message || '').toLowerCase().includes('aborted')));
    if (isAbort) {
      const msg = tr('download_status_cancelled');
      showDownloadTopStatusMessage(msg);
      showStatus(msg, 'ok');
      _scheduleDownloadStatusHide(2600);
      return;
    }
    const msg = `${tr('download_status_failed')}${err && err.message ? `: ${String(err.message)}` : ''}`;
    showDownloadTopStatusMessage(msg);
    showStatus(msg, 'err');
    _scheduleDownloadStatusHide(7000);
  } finally {
    _downloadInProgress = false;
    _activeDownloadController = null;
    setDownloadTopStatusCancelable(false);
  }
}

function showDnsStatus(message, kind = 'ok') {
  if (!els.dnsStatus) return;
  const msg = String(message || '').trim();
  if (!msg) {
    els.dnsStatus.classList.add('hidden');
    els.dnsStatus.textContent = '';
    els.dnsStatus.classList.remove('ok', 'err');
    return;
  }
  els.dnsStatus.textContent = msg;
  els.dnsStatus.classList.remove('hidden');
  els.dnsStatus.classList.toggle('ok', kind === 'ok');
  els.dnsStatus.classList.toggle('err', kind !== 'ok');
}

function showSharedStatus(message, kind = 'ok') {
  if (!els.sharedLinksStatus) return;
  const msg = String(message || '').trim();
  if (!msg) {
    els.sharedLinksStatus.classList.add('hidden');
    els.sharedLinksStatus.textContent = '';
    els.sharedLinksStatus.classList.remove('ok', 'err');
    return;
  }
  els.sharedLinksStatus.textContent = msg;
  els.sharedLinksStatus.classList.remove('hidden');
  els.sharedLinksStatus.classList.toggle('ok', kind === 'ok');
  els.sharedLinksStatus.classList.toggle('err', kind !== 'ok');
}

function _fmtDnsShareTime(isoValue) {
  const raw = String(isoValue || '').trim();
  if (!raw) return tr('dns_shares_never');
  const dt = new Date(raw);
  if (!Number.isFinite(dt.getTime())) return raw;
  try {
    return dt.toLocaleString();
  } catch {
    return raw;
  }
}

async function _copySharedLink(link) {
  const value = String(link || '').trim();
  if (!value) {
    showSharedStatus(tr('dns_shares_link_unavailable'), 'err');
    return;
  }
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(value);
    } else {
      const temp = document.createElement('textarea');
      temp.value = value;
      document.body.appendChild(temp);
      temp.select();
      document.execCommand('copy');
      document.body.removeChild(temp);
    }
    showSharedStatus(tr('dns_shares_copy_ok'), 'ok');
  } catch {
    showSharedStatus(tr('dns_shares_copy_failed'), 'err');
  }
}

function renderDnsSharesList() {
  if (!els.sharedLinksList) return;
  const items = Array.isArray(state.sharedLinks) ? state.sharedLinks : [];
  if (!items.length) {
    els.sharedLinksList.innerHTML = `<div class="mini-label">${escapeHtml(tr('dns_shares_empty'))}</div>`;
    return;
  }
  const rows = items.map((item) => {
    const permission = String(item.permission || 'view');
    const permissionLabel = permission === 'manage'
      ? tr('mapper_share_perm_manage')
      : (permission === 'upload' ? tr('mapper_share_perm_upload') : tr('mapper_share_perm_view'));
    const folder = String(item.share_name || '').trim() || `uploads/${String(item.folder_path || '')}`;
    const link = String(item.link || '');
    const linkCell = link
      ? `<div class="mini-label" style="max-width:420px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${escapeHtml(link)}">${escapeHtml(link)}</div>`
      : `<span class="mini-label">${escapeHtml(tr('dns_shares_link_unavailable'))}</span>`;
    const isActive = !!item.active;
    const actionBtn = isActive
      ? `<button class="btn danger small" data-share-revoke="${Number(item.id || 0)}">${escapeHtml(tr('dns_shares_deactivate'))}</button>`
      : `<button class="btn small" data-share-activate="${Number(item.id || 0)}">${escapeHtml(tr('dns_shares_activate'))}</button>`;
    const editBtn = `<button class="btn small" data-share-edit="${Number(item.id || 0)}">${escapeHtml(tr('dns_shares_edit'))}</button>`;
    const deleteBtn = `<button class="btn danger small" data-share-delete="${Number(item.id || 0)}">${escapeHtml(tr('dns_shares_delete'))}</button>`;
    const extendBtn = isActive
      ? `<button class="btn small" data-share-extend="${Number(item.id || 0)}">${escapeHtml(tr('dns_shares_extend'))}</button>`
      : '';
    const qrBtn = `<button class="btn small" data-share-qr="${Number(item.id || 0)}">QR</button>`;
    return `
      <tr>
        <td>${escapeHtml(folder)}</td>
        <td>${escapeHtml(permissionLabel)}</td>
        <td>${escapeHtml(_fmtDnsShareTime(item.expires_at))}</td>
        <td>${escapeHtml(_fmtDnsShareTime(item.last_used_at))}</td>
        <td>${linkCell}</td>
        <td style="text-align:right;">
          <div class="dns-share-actions">
            <button class="btn small" data-share-copy="${Number(item.id || 0)}">${escapeHtml(tr('dns_shares_copy'))}</button>
            ${qrBtn}
            ${editBtn}
            ${extendBtn}
            ${actionBtn}
            ${deleteBtn}
          </div>
        </td>
      </tr>
    `;
  }).join('');

  els.sharedLinksList.innerHTML = `
    <div class="data-table">
      <table>
        <thead>
          <tr>
            <th>${escapeHtml(tr('dns_shares_col_folder'))}</th>
            <th>${escapeHtml(tr('dns_shares_col_access'))}</th>
            <th>${escapeHtml(tr('dns_shares_col_expires'))}</th>
            <th>${escapeHtml(tr('dns_shares_col_last_used'))}</th>
            <th>${escapeHtml(tr('dns_shares_col_link'))}</th>
            <th style="text-align:right;">${escapeHtml(tr('dns_shares_col_actions'))}</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

async function loadDnsShares() {
  if (!els.sharedLinksList) return;
  showSharedStatus('');
  els.sharedLinksList.innerHTML = `<div class="mini-label">${escapeHtml(tr('dns_shares_loading'))}</div>`;
  try {
    const res = await fetch('/api/admin/shares?include_inactive=1');
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || !data.ok) {
      state.sharedLinks = [];
      els.sharedLinksList.innerHTML = `<div class="mini-label">${escapeHtml((data && data.error) || tr('dns_shares_load_failed'))}</div>`;
      return;
    }
    state.sharedLinks = Array.isArray(data.items) ? data.items : [];
    renderDnsSharesList();
  } catch {
    state.sharedLinks = [];
    els.sharedLinksList.innerHTML = `<div class="mini-label">${escapeHtml(tr('dns_shares_load_failed'))}</div>`;
  }
}

function showSharedEditError(message = '') {
  if (!els.sharedEditError) return;
  const msg = String(message || '').trim();
  if (!msg) {
    els.sharedEditError.classList.add('hidden');
    els.sharedEditError.textContent = '';
    return;
  }
  els.sharedEditError.textContent = msg;
  els.sharedEditError.classList.remove('hidden');
}

function _collectShareFoldersFromItem(item) {
  const list = [];
  const paths = Array.isArray(item && item.folder_paths) ? item.folder_paths : [];
  paths.forEach((value) => {
    const fp = String(value || '').trim();
    if (fp && !list.includes(fp)) list.push(fp);
  });
  const fallback = String((item && item.folder_path) || '').trim();
  if (fallback && !list.includes(fallback)) list.push(fallback);
  return list;
}

function _deriveEditExpiryState(expiresAtRaw) {
  const raw = String(expiresAtRaw || '').trim();
  if (!raw) return { never: true, value: '0', unit: 'days' };
  const dt = new Date(raw);
  if (!Number.isFinite(dt.getTime())) return { never: false, value: '7', unit: 'days' };
  const diffMs = dt.getTime() - Date.now();
  if (!Number.isFinite(diffMs) || diffMs <= 0) return { never: false, value: '1', unit: 'days' };
  const hours = Math.max(1, Math.ceil(diffMs / (1000 * 60 * 60)));
  if (hours <= 48) return { never: false, value: String(hours), unit: 'hours' };
  return { never: false, value: String(Math.max(1, Math.ceil(hours / 24))), unit: 'days' };
}

function _syncSharedEditNeverToggle() {
  const never = !!(els.sharedEditNeverToggle && els.sharedEditNeverToggle.checked);
  if (els.sharedEditExpireValue) {
    els.sharedEditExpireValue.disabled = never;
    if (never) {
      els.sharedEditExpireValue.value = '0';
    } else {
      const raw = String(els.sharedEditExpireValue.value || '').trim();
      const val = Number(raw);
      if (!raw || !Number.isFinite(val) || val <= 0) els.sharedEditExpireValue.value = '7';
    }
  }
  if (els.sharedEditExpireUnit) els.sharedEditExpireUnit.disabled = never;
}

function _syncSharedEditPasswordToggle() {
  const enabled = !!(els.sharedEditPasswordToggle && els.sharedEditPasswordToggle.checked);
  if (els.sharedEditPasswordWrap) els.sharedEditPasswordWrap.classList.toggle('hidden', !enabled);
  if (!enabled && els.sharedEditPasswordInput) els.sharedEditPasswordInput.value = '';
}

function closeSharedEditModal() {
  if (!els.sharedEditModal) return;
  els.sharedEditModal.classList.add('hidden');
  state.sharedEditShareId = 0;
  showSharedEditError('');
}

async function loadSharedFolderOptions(force = false) {
  if (!force && Array.isArray(state.sharedFolderOptions) && state.sharedFolderOptions.length) {
    return state.sharedFolderOptions.slice();
  }
  const { res, data } = await fetchUploadDestinationConfig('uploads');
  if (!res.ok || !data || !data.ok) {
    throw new Error((data && data.error) || tr('dns_shares_edit_load_folders_failed'));
  }
  const folders = Array.isArray(data.folders)
    ? data.folders.map((v) => String(v || '').trim()).filter((v) => !!v)
    : [];
  const cleaned = folders.filter((value) => {
    const parts = String(value || '')
      .split('/')
      .map((seg) => String(seg || '').trim().toLowerCase())
      .filter(Boolean);
    return !parts.includes('@eadir');
  });
  state.sharedFolderOptions = Array.from(new Set(cleaned));
  return state.sharedFolderOptions.slice();
}

function _renderSharedEditFolders(allFolders, selectedFolders) {
  if (!els.sharedEditFolders) return;
  const selectedSet = new Set((Array.isArray(selectedFolders) ? selectedFolders : []).map((v) => String(v || '').trim()).filter(Boolean));
  const rows = Array.isArray(allFolders) ? allFolders : [];
  if (!rows.length) {
    els.sharedEditFolders.innerHTML = `<div class="mini-label">${escapeHtml(tr('dns_shares_edit_no_folders'))}</div>`;
    return;
  }
  els.sharedEditFolders.innerHTML = '';
  rows.forEach((folderPath) => {
    const fp = String(folderPath || '').trim();
    if (!fp) return;
    const row = document.createElement('label');
    row.className = 'toolbar';
    row.style.justifyContent = 'flex-start';
    row.style.gap = '10px';
    row.style.margin = '0 0 8px';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.setAttribute('data-folder-path', fp);
    cb.checked = selectedSet.has(fp);
    const text = document.createElement('span');
    text.className = 'mini-label';
    text.textContent = `uploads/${fp}`;
    row.appendChild(cb);
    row.appendChild(text);
    els.sharedEditFolders.appendChild(row);
  });
}

async function openSharedEditModal(shareId) {
  if (!els.sharedEditModal) return;
  const sid = Number(shareId || 0) || 0;
  if (!sid) return;
  const item = Array.isArray(state.sharedLinks) ? state.sharedLinks.find((s) => Number(s.id || 0) === sid) : null;
  if (!item) {
    showSharedStatus(tr('dns_shares_edit_failed'), 'err');
    return;
  }
  showSharedEditError('');
  state.sharedEditShareId = sid;

  try {
    await loadSharedFolderOptions(true);
  } catch (err) {
    showSharedStatus((err && err.message) || tr('dns_shares_edit_load_folders_failed'), 'err');
    return;
  }
  await refreshShareDuckdnsConfig();
  applyUiLanguage();

  const selectedFolders = _collectShareFoldersFromItem(item);
  const options = Array.from(new Set([...(state.sharedFolderOptions || []), ...selectedFolders]))
    .sort((a, b) => String(a || '').localeCompare(String(b || ''), 'da-DK'));
  _renderSharedEditFolders(options, selectedFolders);

  if (els.sharedEditNameInput) {
    const name = String(item.share_name || '').trim();
    const fallback = selectedFolders.length === 1 ? `uploads/${selectedFolders[0]}` : `${selectedFolders.length} mapper`;
    els.sharedEditNameInput.value = name || fallback;
  }
  const expiry = _deriveEditExpiryState(item.expires_at);
  if (els.sharedEditNeverToggle) els.sharedEditNeverToggle.checked = !!expiry.never;
  if (els.sharedEditExpireValue) els.sharedEditExpireValue.value = String(expiry.value || '7');
  if (els.sharedEditExpireUnit) els.sharedEditExpireUnit.value = expiry.unit || 'days';
  _syncSharedEditNeverToggle();

  if (els.sharedEditPermission) els.sharedEditPermission.value = String(item.permission || 'view');
  if (els.sharedEditDuckdnsToggle) {
    const duckdnsEnabled = !!state.shareDuckdnsConfigured;
    els.sharedEditDuckdnsToggle.checked = duckdnsEnabled ? !!item.use_duckdns : false;
    els.sharedEditDuckdnsToggle.disabled = !duckdnsEnabled;
    els.sharedEditDuckdnsToggle.title = duckdnsEnabled ? '' : tr('mapper_share_duckdns_not_configured');
  }
  if (els.sharedEditPasswordToggle) els.sharedEditPasswordToggle.checked = !!item.password_enabled;
  if (els.sharedEditPasswordInput) els.sharedEditPasswordInput.value = '';
  _syncSharedEditPasswordToggle();

  if (els.sharedEditRequireNameToggle) els.sharedEditRequireNameToggle.checked = !!item.require_visitor_name;
  if (els.sharedEditModalSave) {
    els.sharedEditModalSave.disabled = false;
    els.sharedEditModalSave.classList.remove('loading');
    els.sharedEditModalSave.textContent = tr('dns_shares_edit_save');
  }
  els.sharedEditModal.classList.remove('hidden');
}

async function saveSharedEditModal() {
  const shareId = Number(state.sharedEditShareId || 0) || 0;
  if (!shareId) return;
  const folders = [];
  if (els.sharedEditFolders) {
    const checks = Array.from(els.sharedEditFolders.querySelectorAll('input[data-folder-path]:checked'));
    checks.forEach((cb) => {
      const fp = String(cb.getAttribute('data-folder-path') || '').trim();
      if (fp && !folders.includes(fp)) folders.push(fp);
    });
  }
  if (!folders.length) {
    showSharedEditError(tr('dns_shares_edit_select_folder'));
    return;
  }

  let expiresValue = 0;
  const neverExpires = !!(els.sharedEditNeverToggle && els.sharedEditNeverToggle.checked);
  if (!neverExpires) {
    const raw = String((els.sharedEditExpireValue && els.sharedEditExpireValue.value) || '').trim();
    if (!raw) {
      expiresValue = 0;
    } else {
      const parsed = Number(raw);
      if (!Number.isFinite(parsed) || parsed < 0) {
        showSharedEditError(tr('dns_shares_edit_invalid_expiry'));
        return;
      }
      expiresValue = Math.floor(parsed);
    }
  }

  const shareName = String((els.sharedEditNameInput && els.sharedEditNameInput.value) || '').trim();
  const permission = String((els.sharedEditPermission && els.sharedEditPermission.value) || 'view');
  const useDuckdns = !!(els.sharedEditDuckdnsToggle && els.sharedEditDuckdnsToggle.checked);
  const requireVisitorName = !!(els.sharedEditRequireNameToggle && els.sharedEditRequireNameToggle.checked);
  const passwordEnabled = !!(els.sharedEditPasswordToggle && els.sharedEditPasswordToggle.checked);
  const password = String((els.sharedEditPasswordInput && els.sharedEditPasswordInput.value) || '');
  if (passwordEnabled && password && password.length < 4) {
    showSharedEditError(tr('mapper_share_password_placeholder'));
    return;
  }

  const saveBtn = els.sharedEditModalSave;
  const original = saveBtn ? saveBtn.textContent : tr('dns_shares_edit_save');
  showSharedEditError('');
  try {
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.classList.add('loading');
      saveBtn.textContent = tr('dns_shares_edit_saving');
    }
    const res = await fetch(`/api/admin/shares/${encodeURIComponent(String(shareId))}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        share_name: shareName,
        folder_paths: folders,
        permission,
        expires_value: neverExpires ? 0 : expiresValue,
        expires_unit: String((els.sharedEditExpireUnit && els.sharedEditExpireUnit.value) || 'days'),
        use_duckdns: useDuckdns,
        require_visitor_name: requireVisitorName,
        password_enabled: passwordEnabled,
        password,
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || !data.ok) {
      showSharedEditError((data && data.error) || tr('dns_shares_edit_failed'));
      return;
    }
    closeSharedEditModal();
    showSharedStatus(tr('dns_shares_edit_saved'), 'ok');
    await loadDnsShares();
  } catch {
    showSharedEditError(tr('dns_shares_edit_failed'));
  } finally {
    if (saveBtn) {
      saveBtn.classList.remove('loading');
      saveBtn.disabled = false;
      saveBtn.textContent = original || tr('dns_shares_edit_save');
    }
  }
}

async function revokeDnsShare(shareId) {
  if (!shareId) return;
  if (!window.confirm(tr('dns_shares_deactivate_confirm'))) return;
  try {
    const res = await fetch(`/api/admin/shares/${encodeURIComponent(String(shareId))}/revoke`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || !data.ok) {
      showSharedStatus((data && data.error) || tr('dns_shares_revoke_failed'), 'err');
      return;
    }
    showSharedStatus(tr('dns_shares_deactivate_ok'), 'ok');
    await loadDnsShares();
  } catch {
    showSharedStatus(tr('dns_shares_revoke_failed'), 'err');
  }
}

async function activateDnsShare(shareId) {
  if (!shareId) return;
  const raw = window.prompt(tr('dns_shares_activate_prompt'), '7');
  if (raw === null) return;
  const value = String(raw || '').trim();
  let days = 0;
  if (value) {
    const parsed = Number(value);
    if (!Number.isFinite(parsed) || parsed < 0) {
      showSharedStatus(tr('dns_shares_activate_failed'), 'err');
      return;
    }
    days = Math.floor(parsed);
  }
  try {
    const res = await fetch(`/api/admin/shares/${encodeURIComponent(String(shareId))}/activate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ expires_value: days, expires_unit: 'days' }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || !data.ok) {
      showSharedStatus((data && data.error) || tr('dns_shares_activate_failed'), 'err');
      return;
    }
    showSharedStatus(tr('dns_shares_activate_ok'), 'ok');
    await loadDnsShares();
  } catch {
    showSharedStatus(tr('dns_shares_activate_failed'), 'err');
  }
}

async function deleteDnsShare(shareId) {
  if (!shareId) return;
  if (!window.confirm(tr('dns_shares_delete_confirm'))) return;
  try {
    const res = await fetch(`/api/admin/shares/${encodeURIComponent(String(shareId))}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || !data.ok) {
      showSharedStatus((data && data.error) || tr('dns_shares_delete_failed'), 'err');
      return;
    }
    showSharedStatus(tr('dns_shares_delete_ok'), 'ok');
    await loadDnsShares();
  } catch {
    showSharedStatus(tr('dns_shares_delete_failed'), 'err');
  }
}

async function _downloadQrForLink(link, filename = 'share-qr.png') {
  const value = String(link || '').trim();
  if (!value) return;
  try {
    const res = await fetch(`/api/qr?text=${encodeURIComponent(value)}&box=6&border=2`, { cache: 'no-store' });
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch {}
}

async function extendDnsShare(shareId) {
  if (!shareId) return;
  const raw = window.prompt(tr('dns_shares_extend_prompt'), '7');
  if (raw === null) return;
  const value = String(raw || '').trim();
  let days = 0;
  if (value) {
    const parsed = Number(value);
    if (!Number.isFinite(parsed) || parsed < 0) {
      showSharedStatus(tr('dns_shares_extend_failed'), 'err');
      return;
    }
    days = Math.floor(parsed);
  }
  try {
    const res = await fetch(`/api/admin/shares/${encodeURIComponent(String(shareId))}/extend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ expires_value: days, expires_unit: 'days' }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || !data.ok) {
      showSharedStatus((data && data.error) || tr('dns_shares_extend_failed'), 'err');
      return;
    }
    showSharedStatus(tr('dns_shares_extend_ok'), 'ok');
    await loadDnsShares();
  } catch {
    showSharedStatus(tr('dns_shares_extend_failed'), 'err');
  }
}

async function loadDnsSettings() {
  if (!els.dnsDuckdnsBaseUrlInput) return;
  showDnsStatus('');
  try {
    const res = await fetch('/api/settings/dns');
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || !data.ok) {
      showDnsStatus((data && data.error) || tr('dns_load_failed'), 'err');
      return;
    }
    els.dnsDuckdnsBaseUrlInput.value = String(data.duckdns_base_url || '');
  } catch {
    showDnsStatus(tr('dns_load_failed'), 'err');
  }
}

async function saveDnsSettings() {
  if (!els.dnsDuckdnsBaseUrlInput) return;
  const saveBtn = els.dnsSaveBtn;
  const original = saveBtn ? saveBtn.textContent : tr('dns_save');
  showDnsStatus('');
  try {
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.classList.add('loading');
    }
    const res = await fetch('/api/settings/dns', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        duckdns_base_url: String((els.dnsDuckdnsBaseUrlInput.value || '')).trim(),
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || !data.ok) {
      showDnsStatus((data && data.error) || tr('dns_save_failed'), 'err');
      return;
    }
    els.dnsDuckdnsBaseUrlInput.value = String(data.duckdns_base_url || '');
    showDnsStatus(tr('dns_saved'), 'ok');
  } catch {
    showDnsStatus(tr('dns_save_failed'), 'err');
  } finally {
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.classList.remove('loading');
      saveBtn.textContent = original || tr('dns_save');
    }
  }
}

function showAiPerfStatus(message, kind = 'ok') {
  if (!els.aiPerfStatus) return;
  const msg = String(message || '').trim();
  if (!msg) {
    els.aiPerfStatus.classList.add('hidden');
    els.aiPerfStatus.textContent = '';
    els.aiPerfStatus.classList.remove('ok', 'err');
    return;
  }
  els.aiPerfStatus.textContent = msg;
  els.aiPerfStatus.classList.remove('hidden');
  els.aiPerfStatus.classList.toggle('ok', kind === 'ok');
  els.aiPerfStatus.classList.toggle('err', kind !== 'ok');
}

async function loadAiPerformanceSettings() {
  if (!els.aiIngestThrottleInput || !els.facesThrottleInput) return;
  showAiPerfStatus('');
  try {
    const res = await fetch('/api/settings/ai-performance');
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || !data.ok) {
      showAiPerfStatus((data && data.error) || 'Kunne ikke hente AI-ydelse.', 'err');
      return;
    }
    els.aiIngestThrottleInput.value = String(data.ai_ingest_throttle_sec ?? '0.04');
    els.facesThrottleInput.value = String(data.faces_index_throttle_sec ?? '0.06');
  } catch {
    showAiPerfStatus('Kunne ikke hente AI-ydelse.', 'err');
  }
}

async function saveAiPerformanceSettings() {
  if (!els.aiIngestThrottleInput || !els.facesThrottleInput) return;
  const saveBtn = els.aiPerfSaveBtn;
  const original = saveBtn ? saveBtn.textContent : 'Gem ydelse';
  showAiPerfStatus('');
  try {
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.classList.add('loading');
    }
    const aiValue = Number(els.aiIngestThrottleInput.value);
    const facesValue = Number(els.facesThrottleInput.value);
    const res = await fetch('/api/settings/ai-performance', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ai_ingest_throttle_sec: Number.isFinite(aiValue) ? aiValue : 0,
        faces_index_throttle_sec: Number.isFinite(facesValue) ? facesValue : 0,
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || !data.ok) {
      showAiPerfStatus((data && data.error) || 'Kunne ikke gemme AI-ydelse.', 'err');
      return;
    }
    els.aiIngestThrottleInput.value = String(data.ai_ingest_throttle_sec ?? els.aiIngestThrottleInput.value);
    els.facesThrottleInput.value = String(data.faces_index_throttle_sec ?? els.facesThrottleInput.value);
    showAiPerfStatus('AI-ydelse gemt (gælder med det samme).', 'ok');
  } catch {
    showAiPerfStatus('Kunne ikke gemme AI-ydelse.', 'err');
  } finally {
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.classList.remove('loading');
      saveBtn.textContent = original || 'Gem ydelse';
    }
  }
}

function applyAiPerfPreset(kind) {
  if (!els.aiIngestThrottleInput || !els.facesThrottleInput) return;
  const presets = {
    low: { ai: 0.12, faces: 0.16 },
    normal: { ai: 0.04, faces: 0.06 },
    fast: { ai: 0.00, faces: 0.00 },
  };
  const p = presets[kind] || presets.normal;
  els.aiIngestThrottleInput.value = p.ai.toFixed(2);
  els.facesThrottleInput.value = p.faces.toFixed(2);
}

function showUploadWorkflowStatus(message, kind = 'ok') {
  if (!els.uploadWorkflowStatus) return;
  const msg = String(message || '').trim();
  if (!msg) {
    els.uploadWorkflowStatus.classList.add('hidden');
    els.uploadWorkflowStatus.textContent = '';
    els.uploadWorkflowStatus.classList.remove('ok', 'err');
    return;
  }
  els.uploadWorkflowStatus.textContent = msg;
  els.uploadWorkflowStatus.classList.remove('hidden');
  els.uploadWorkflowStatus.classList.toggle('ok', kind === 'ok');
  els.uploadWorkflowStatus.classList.toggle('err', kind !== 'ok');
}

function _applyUploadWorkflowData(data) {
  if (!data || typeof data !== 'object') return;
  const mode = String(data.mode || 'gentle').toLowerCase() === 'aggressive' ? 'aggressive' : 'gentle';
  state.uploadWorkflowMode = mode;
  state.uploadWorkflowBatchSize = Number(data.batch_size || 10) || 10;
  state.uploadWorkflowThumbnailsUseGpu = !!data.thumbnails_use_gpu;
  if (els.uploadWorkflowModeGentle) els.uploadWorkflowModeGentle.checked = mode === 'gentle';
  if (els.uploadWorkflowModeAggressive) els.uploadWorkflowModeAggressive.checked = mode === 'aggressive';
  if (els.uploadWorkflowExtraInfo) {
    const runtimeText = state.uploadWorkflowThumbnailsUseGpu ? tr('status_runtime_gpu') : tr('status_runtime_cpu');
    els.uploadWorkflowExtraInfo.textContent = tr('upload_workflow_extra_info')
      .replace('{thumb_runtime}', runtimeText)
      .replace('{batch_size}', String(state.uploadWorkflowBatchSize || 10));
  }
}

async function loadUploadWorkflowSettings() {
  if (!els.uploadWorkflowModeGentle || !els.uploadWorkflowModeAggressive) return;
  showUploadWorkflowStatus('');
  try {
    const res = await fetch('/api/settings/upload-workflow');
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || !data.ok) {
      showUploadWorkflowStatus((data && data.error) || tr('upload_workflow_load_failed'), 'err');
      return;
    }
    _applyUploadWorkflowData(data);
  } catch {
    showUploadWorkflowStatus(tr('upload_workflow_load_failed'), 'err');
  }
}

async function saveUploadWorkflowSettings() {
  if (!els.uploadWorkflowModeGentle || !els.uploadWorkflowModeAggressive) return;
  const saveBtn = els.uploadWorkflowSaveBtn;
  const original = saveBtn ? saveBtn.textContent : tr('upload_workflow_save');
  showUploadWorkflowStatus('');
  try {
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.classList.add('loading');
    }
    const mode = (els.uploadWorkflowModeAggressive && els.uploadWorkflowModeAggressive.checked) ? 'aggressive' : 'gentle';
    const res = await fetch('/api/settings/upload-workflow', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || !data.ok) {
      showUploadWorkflowStatus((data && data.error) || tr('upload_workflow_save_failed'), 'err');
      return;
    }
    _applyUploadWorkflowData(data);
    showUploadWorkflowStatus(tr('upload_workflow_saved'), 'ok');
  } catch {
    showUploadWorkflowStatus(tr('upload_workflow_save_failed'), 'err');
  } finally {
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.classList.remove('loading');
      saveBtn.textContent = original || tr('upload_workflow_save');
    }
  }
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

function _summarizeFileExtensions(files) {
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

function showFileTypeStatus(message, kind = 'ok') {
  if (!els.fileTypeStatus) return;
  const msg = String(message || '').trim();
  if (!msg) {
    els.fileTypeStatus.classList.add('hidden');
    els.fileTypeStatus.textContent = '';
    els.fileTypeStatus.classList.remove('ok', 'err');
    return;
  }
  els.fileTypeStatus.textContent = msg;
  els.fileTypeStatus.classList.remove('hidden');
  els.fileTypeStatus.classList.toggle('ok', kind === 'ok');
  els.fileTypeStatus.classList.toggle('err', kind !== 'ok');
}

function updateUploadAcceptFromFileTypes() {
  const data = state.uploadFileTypes || {};
  const accept = String(data.upload_accept || '').trim();
  if (els.mapperUploadInput && accept) els.mapperUploadInput.accept = accept;
}

function renderUploadFileTypeSettings() {
  const data = state.uploadFileTypes || {};
  const allowed = Array.isArray(data.allowed_extensions) ? data.allowed_extensions.slice().sort() : [];
  const blocked = Array.isArray(data.blocked_extensions) ? data.blocked_extensions.slice().sort() : [];
  const customSet = new Set(Array.isArray(data.custom_extensions) ? data.custom_extensions : []);
  if (els.fileTypeAllowedList) {
    if (!allowed.length) {
      els.fileTypeAllowedList.innerHTML = `<div class="mini-label">${escapeHtml(tr('file_types_allowed_empty'))}</div>`;
    } else {
      els.fileTypeAllowedList.innerHTML = allowed.map((ext) => {
        const chipClass = customSet.has(ext) ? 'file-type-chip custom' : 'file-type-chip';
        return `<span class="${chipClass}">` +
        `<span>${escapeHtml(ext)}</span>` +
        `<button type="button" data-file-type-remove="${escapeHtml(ext)}" aria-label="Fjern ${escapeHtml(ext)}">&times;</button>` +
        `</span>`;
      }).join('');
    }
  }
  if (els.fileTypeBlockedList) {
    if (!blocked.length) {
      els.fileTypeBlockedList.innerHTML = `<div class="mini-label">${escapeHtml(tr('file_types_blocked_empty'))}</div>`;
    } else {
      els.fileTypeBlockedList.innerHTML = blocked.map((ext) => (
        `<span class="file-type-chip muted">${escapeHtml(ext)}</span>`
      )).join('');
    }
  }
  updateUploadAcceptFromFileTypes();
}

function _applyUploadFileTypesData(data) {
  if (!data || typeof data !== 'object') return;
  const allowed = Array.isArray(data.allowed_extensions) ? data.allowed_extensions.map(normalizeUploadFileExtension).filter(Boolean) : [];
  const supported = Array.isArray(data.supported_extensions) ? data.supported_extensions.map(normalizeUploadFileExtension).filter(Boolean) : [];
  const defaults = Array.isArray(data.default_extensions) ? data.default_extensions.map(normalizeUploadFileExtension).filter(Boolean) : supported.slice();
  const supportedSet = new Set(supported);
  const custom = Array.isArray(data.custom_extensions) ? data.custom_extensions.map(normalizeUploadFileExtension).filter(Boolean) : allowed.filter((ext) => !supportedSet.has(ext));
  const allowedSet = new Set(allowed);
  const blocked = Array.isArray(data.blocked_extensions)
    ? data.blocked_extensions.map(normalizeUploadFileExtension).filter(Boolean)
    : supported.filter((ext) => !allowedSet.has(ext));
  state.uploadFileTypes = {
    allowed_extensions: Array.from(new Set(allowed)).sort(),
    supported_extensions: Array.from(new Set(supported)).sort(),
    default_extensions: Array.from(new Set(defaults)).sort(),
    custom_extensions: Array.from(new Set(custom)).sort(),
    blocked_extensions: Array.from(new Set(blocked)).sort(),
    upload_accept: String(data.upload_accept || allowed.join(',')).trim(),
  };
  state.uploadFileTypesLoaded = true;
  renderUploadFileTypeSettings();
}

async function loadUploadFileTypeSettings(options = {}) {
  const silent = !!(options && options.silent);
  if (!silent) showFileTypeStatus('');
  try {
    const res = await fetch('/api/settings/upload-file-types');
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || !data.ok) {
      if (!silent) showFileTypeStatus((data && data.error) || tr('file_types_load_failed'), 'err');
      return false;
    }
    _applyUploadFileTypesData(data);
    return true;
  } catch {
    if (!silent) showFileTypeStatus(tr('file_types_load_failed'), 'err');
    return false;
  }
}

async function ensureUploadFileTypeSettingsLoaded() {
  if (state.uploadFileTypesLoaded && state.uploadFileTypes) return true;
  if (state.uploadFileTypesLoading) return state.uploadFileTypesLoading;
  state.uploadFileTypesLoading = loadUploadFileTypeSettings({ silent: true }).finally(() => {
    state.uploadFileTypesLoading = null;
  });
  return state.uploadFileTypesLoading;
}

function updateUploadFileTypeBlockedFromAllowed() {
  const data = state.uploadFileTypes || {};
  const supported = Array.isArray(data.supported_extensions) ? data.supported_extensions : [];
  const allowedSet = new Set(Array.isArray(data.allowed_extensions) ? data.allowed_extensions : []);
  data.blocked_extensions = supported.filter((ext) => !allowedSet.has(ext)).sort();
  data.custom_extensions = (Array.isArray(data.allowed_extensions) ? data.allowed_extensions : []).filter((ext) => !supported.includes(ext)).sort();
  data.upload_accept = (Array.isArray(data.allowed_extensions) ? data.allowed_extensions : []).join(',');
}

function addUploadFileTypeFromInput() {
  if (!els.fileTypeInput) return;
  const ext = normalizeUploadFileExtension(els.fileTypeInput.value);
  if (!ext) {
    showFileTypeStatus(tr('file_types_invalid'), 'err');
    return;
  }
  const data = state.uploadFileTypes || {};
  const supported = new Set(Array.isArray(data.supported_extensions) ? data.supported_extensions : []);
  const allowed = new Set(Array.isArray(data.allowed_extensions) ? data.allowed_extensions : []);
  if (allowed.has(ext)) {
    showFileTypeStatus(tr('file_types_duplicate').replace('{ext}', ext), 'err');
    return;
  }
  allowed.add(ext);
  state.uploadFileTypes = {
    ...data,
    allowed_extensions: Array.from(allowed).sort(),
  };
  updateUploadFileTypeBlockedFromAllowed();
  els.fileTypeInput.value = '';
  showFileTypeStatus(supported.size && !supported.has(ext) ? tr('file_types_unsupported').replace('{ext}', ext) : '', 'ok');
  renderUploadFileTypeSettings();
}

async function saveUploadFileTypeSettings() {
  const data = state.uploadFileTypes || {};
  const allowed = Array.isArray(data.allowed_extensions) ? data.allowed_extensions.slice().sort() : [];
  const saveBtn = els.fileTypeSaveBtn;
  const original = saveBtn ? saveBtn.textContent : tr('file_types_save');
  if (!allowed.length) {
    showFileTypeStatus(tr('file_types_allowed_empty'), 'err');
    return;
  }
  showFileTypeStatus('');
  try {
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.classList.add('loading');
    }
    const res = await fetch('/api/settings/upload-file-types', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ allowed_extensions: allowed }),
    });
    const payload = await res.json().catch(() => ({}));
    if (!res.ok || !payload || !payload.ok) {
      showFileTypeStatus((payload && payload.error) || tr('file_types_save_failed'), 'err');
      return;
    }
    _applyUploadFileTypesData(payload);
    showFileTypeStatus(tr('file_types_saved'), 'ok');
  } catch {
    showFileTypeStatus(tr('file_types_save_failed'), 'err');
  } finally {
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.classList.remove('loading');
      saveBtn.textContent = original || tr('file_types_save');
    }
  }
}

function filterUploadFilesByAllowed(files) {
  const data = state.uploadFileTypes || {};
  const allowed = new Set(Array.isArray(data.allowed_extensions) ? data.allowed_extensions : []);
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

function showBlockedUploadFiles(blockedFiles) {
  const summary = _summarizeFileExtensions(blockedFiles);
  if (!summary) return;
  showStatus(tr('upload_blocked_file_types').replace('{types}', summary), 'err');
  try {
    ensureUploadMonitorRefs();
    if (els.uploadMonitor) {
      showUploadMonitor();
      const list = Array.isArray(blockedFiles) ? blockedFiles.slice(0, 8) : [];
      list.forEach((file, idx) => {
        addUploadMonitorItem(file && file.name ? file.name : 'fil', false, 'Blokeret filtype', `blocked-${Date.now()}-${idx}`, 0);
      });
      if (els.uploadMonitorSummary) els.uploadMonitorSummary.textContent = `Blokeret: ${blockedFiles.length} fil(er)`;
      if (els.uploadMonitorCurrent) els.uploadMonitorCurrent.textContent = tr('upload_blocked_file_types').replace('{types}', summary);
      scheduleUploadMonitorAutoHide(10000);
    }
  } catch {}
}

function showAppUpdateStatus(message, kind = 'ok') {
  if (!els.appUpdateStatus) return;
  const msg = String(message || '').trim();
  if (!msg) {
    els.appUpdateStatus.classList.add('hidden');
    els.appUpdateStatus.textContent = '';
    els.appUpdateStatus.classList.remove('ok', 'err');
    return;
  }
  els.appUpdateStatus.textContent = msg;
  els.appUpdateStatus.classList.remove('hidden');
  els.appUpdateStatus.classList.toggle('ok', kind === 'ok');
  els.appUpdateStatus.classList.toggle('err', kind !== 'ok');
}

function appUpdateStatusLabel(value) {
  const raw = String(value || '').trim().toLowerCase();
  if (raw === 'idle') return tr('app_update_status_idle');
  if (raw === 'available') return tr('app_update_status_available');
  if (raw === 'checking') return tr('app_update_status_checking');
  if (raw === 'running') return tr('app_update_status_running');
  if (raw === 'success') return tr('app_update_status_success');
  if (raw === 'failed') return tr('app_update_status_failed');
  return tr('app_update_status_unknown');
}

function appUpdateShortRev(value) {
  const raw = String(value || '').trim();
  if (!raw) return '-';
  return raw.length > 12 ? raw.slice(0, 12) : raw;
}

function renderAppUpdateTabBadge(item = null) {
  const updateState = (item && typeof item === 'object') ? item : (state.appUpdate || {});
  const git = (updateState && updateState.git && typeof updateState.git === 'object') ? updateState.git : {};
  const serviceReachable = updateState.service_reachable !== false;
  const hasGit = !!(git && Object.keys(git).length);
  const available = serviceReachable && hasGit && git.available !== false;
  const autoEnabled = updateState.auto_check_enabled !== false;
  const hasUpdate = !!(available && git.update_available);
  const showBadge = autoEnabled && hasUpdate;

  const tabBtn = document.querySelector('#settingsPanel .tab-btn[data-tab="update"]');
  if (tabBtn) {
    tabBtn.classList.toggle('has-update-badge', showBadge);
    if (showBadge) tabBtn.setAttribute('data-update-badge', tr('app_update_tab_badge'));
    else tabBtn.removeAttribute('data-update-badge');
  }

  const updateOpt = document.querySelector('#settingsTabSelect option[value="update"]');
  if (updateOpt) {
    const base = tr('tab_update');
    updateOpt.textContent = showBadge ? `${base} • ${tr('app_update_tab_badge')}` : base;
  }

  const settingsBadgeText = tr('app_update_tab_badge');
  document.querySelectorAll('.nav-item[data-view="settings"], .mobile-nav-item[data-view="settings"]').forEach((btn) => {
    btn.classList.toggle('has-update-badge', showBadge);
    if (showBadge) {
      btn.setAttribute('data-update-badge', settingsBadgeText);
      btn.setAttribute('title', tr('app_update_status_available'));
    } else {
      btn.removeAttribute('data-update-badge');
      btn.removeAttribute('title');
    }
  });
}

function applyAppUpdateSettingsUi(item = {}) {
  if (!els.appUpdateAutoCheckToggle && !els.appUpdateIntervalInput) return;
  const enabled = item.auto_check_enabled !== false;
  const interval = Math.max(5, Math.min(1440, Number(item.auto_check_interval_minutes || 30) || 30));
  if (els.appUpdateAutoCheckToggle) els.appUpdateAutoCheckToggle.checked = enabled;
  if (els.appUpdateIntervalInput && document.activeElement !== els.appUpdateIntervalInput) {
    els.appUpdateIntervalInput.value = String(interval);
  }
  if (els.appUpdateIntervalInput) els.appUpdateIntervalInput.disabled = !enabled;
  if (els.appUpdateAutoMeta) {
    const next = String(item.next_auto_check_at || '').trim();
    const last = String(item.last_check_at || '').trim();
    if (!enabled) {
      els.appUpdateAutoMeta.textContent = tr('app_update_auto_off');
    } else if (next) {
      els.appUpdateAutoMeta.textContent = tr('app_update_next_check').replace('{time}', fmtDate(next));
    } else if (last) {
      els.appUpdateAutoMeta.textContent = tr('app_update_last_check').replace('{time}', fmtDate(last));
    } else {
      els.appUpdateAutoMeta.textContent = '';
    }
  }
}

function markAppUpdateReconnect() {
  const until = Date.now() + APP_UPDATE_RECONNECT_MAX_MS;
  state.appUpdateReconnectUntil = until;
  try {
    localStorage.setItem(APP_UPDATE_RECONNECT_KEY, JSON.stringify({ until }));
  } catch {}
}

function clearAppUpdateReconnect() {
  state.appUpdateReconnectUntil = 0;
  try { localStorage.removeItem(APP_UPDATE_RECONNECT_KEY); } catch {}
}

function appUpdateReconnectActive() {
  const nowMs = Date.now();
  let until = Number(state.appUpdateReconnectUntil || 0);
  if (!until) {
    try {
      const raw = JSON.parse(localStorage.getItem(APP_UPDATE_RECONNECT_KEY) || '{}') || {};
      until = Number(raw.until || 0);
      if (until) state.appUpdateReconnectUntil = until;
    } catch {
      until = 0;
    }
  }
  if (until > nowMs) return true;
  if (until) clearAppUpdateReconnect();
  return false;
}

function scheduleAppUpdatePageReload() {
  if (appUpdateReloadTimer) return;
  showAppUpdateStatus(tr('app_update_reloading'), 'ok');
  clearAppUpdateReconnect();
  appUpdateReloadTimer = setTimeout(() => {
    try { window.location.reload(); } catch {}
  }, APP_UPDATE_RELOAD_DELAY_MS);
}

function shouldKeepAppUpdatePolling(data = null) {
  if (data && data.running) return true;
  if (appUpdateReconnectActive()) return true;
  if (data && data.service_reachable === false) return true;
  const git = (data && data.git && typeof data.git === 'object') ? data.git : null;
  if (git && git.available === false) return true;
  return false;
}

function appUpdateLogLineLevel(line) {
  const s = String(line || '').toLowerCase();
  if (/\b(traceback|exception|error|failed|fatal)\b/.test(s) || s.includes('returncode=1')) return 'err';
  if (/\b(warn|warning|skipping|springer|unavailable)\b/.test(s) || s.includes('ikke tilg')) return 'warn';
  if (/\b(success|finished|done|healthy|started|built|klar)\b/.test(s) || /\b20\d\b/.test(s)) return 'ok';
  if (/^\s*(=>|-->|->|\[\+\]|cached|\$|==>)/i.test(s)) return 'build';
  return 'info';
}

function highlightAppUpdateLogText(rawLine) {
  let raw = String(rawLine || '');
  let prefix = '';
  const serviceMatch = raw.match(/^(\s*)([a-z0-9_.-]+)(\s+\|)(.*)$/i);
  if (serviceMatch) {
    prefix =
      escapeHtml(serviceMatch[1]) +
      `<span class="app-log-service">${escapeHtml(serviceMatch[2])}</span>` +
      `<span class="app-log-pipe">${escapeHtml(serviceMatch[3])}</span>`;
    raw = serviceMatch[4];
  }

  const tokenRe = /(https?:\/\/[^\s"]+)|(\b\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?\b)|(\b[1-5]\d\d\b)|(\b(?:INFO|WARN|WARNING|ERROR|Traceback|Exception|FINISHED|DONE|OK|Built|Started|Healthy|success|failed|FAILED|CACHED)\b:?|==>|=>|-->|->|\[\+\]|\$)/g;
  let html = '';
  let last = 0;
  let m;
  while ((m = tokenRe.exec(raw)) !== null) {
    html += escapeHtml(raw.slice(last, m.index));
    const token = m[0];
    let cls = 'app-log-accent';
    if (m[1]) cls = 'app-log-url';
    else if (m[2]) cls = 'app-log-ip';
    else if (m[3]) {
      const code = Number(token);
      cls = code >= 500 ? 'app-log-err' : (code >= 400 ? 'app-log-warn' : (code >= 300 ? 'app-log-warn' : 'app-log-ok'));
    } else if (/\b(error|traceback|exception|failed)\b/i.test(token)) cls = 'app-log-err';
    else if (/\b(warn|warning)\b/i.test(token)) cls = 'app-log-warn';
    else if (/\b(info)\b/i.test(token)) cls = 'app-log-info-token';
    else if (/\b(ok|finished|done|built|started|healthy|success|cached)\b/i.test(token)) cls = 'app-log-ok';
    else if (/^(==>|=>|-->|->|\[\+\]|\$)$/.test(token)) cls = 'app-log-build';
    html += `<span class="${cls}">${escapeHtml(token)}</span>`;
    last = tokenRe.lastIndex;
  }
  html += escapeHtml(raw.slice(last));
  return prefix + html;
}

function renderAppUpdateLog(logLines) {
  if (!els.appUpdateLog) return;
  const lines = Array.isArray(logLines) ? logLines : [];
  const hasText = lines.some((line) => String(line || '').trim());
  els.appUpdateLog.classList.toggle('hidden', !hasText);
  if (!hasText) {
    els.appUpdateLog.textContent = '';
    return;
  }
  els.appUpdateLog.innerHTML = lines.map((line) => {
    const level = appUpdateLogLineLevel(line);
    const body = highlightAppUpdateLogText(line) || '&nbsp;';
    return `<span class="app-log-line app-log-line-${level}">${body}</span>`;
  }).join('');
  try { els.appUpdateLog.scrollTop = els.appUpdateLog.scrollHeight; } catch {}
}

function renderAppUpdate(data = null) {
  if (!els.appUpdateTitle) return;
  const previousItem = (state.appUpdate && typeof state.appUpdate === 'object') ? state.appUpdate : {};
  const previousStatusRaw = String(previousItem.status || '').toLowerCase();
  const previousRunning = !!previousItem.running || previousStatusRaw === 'running';

  const item = data || state.appUpdate || {};
  state.appUpdate = item;
  const git = (item && item.git && typeof item.git === 'object') ? item.git : {};
  const running = !!item.running || String(item.status || '').toLowerCase() === 'running';
  const statusRaw = String(item.status || '').toLowerCase();
  const reconnecting = appUpdateReconnectActive();
  const justFinishedFromRunning = statusRaw === 'success' && previousRunning && !running;
  const shouldReloadOnSuccess = statusRaw === 'success' && (reconnecting || justFinishedFromRunning);
  const serviceReachable = item.service_reachable !== false;
  const hasGit = !!(git && Object.keys(git).length);
  const available = serviceReachable && hasGit && git.available !== false;
  const hasUpdateAvailable = available && !!git.update_available;
  const current = appUpdateShortRev(git.current_short || git.current_rev);
  const remote = appUpdateShortRev(git.remote_short || git.remote_rev);
  const statusForLabel = (!running && hasUpdateAvailable)
    ? 'available'
    : (item.status || (running ? 'running' : 'idle'));

  if (els.appUpdateBranch) els.appUpdateBranch.textContent = String(git.branch || '-');
  if (els.appUpdateCurrent) els.appUpdateCurrent.textContent = current;
  if (els.appUpdateRemote) els.appUpdateRemote.textContent = remote;
  if (els.appUpdateState) els.appUpdateState.textContent = appUpdateStatusLabel(statusForLabel);
  applyAppUpdateSettingsUi(item);
  renderAppUpdateTabBadge(item);

  const logLines = Array.isArray(item.log) ? item.log : [];
  renderAppUpdateLog(logLines);

  if (els.appUpdateCheckBtn) {
    els.appUpdateCheckBtn.disabled = running || reconnecting || els.appUpdateCheckBtn.classList.contains('loading');
  }
  if (els.appUpdateStartBtn) {
    els.appUpdateStartBtn.disabled = running || reconnecting || !available || !!git.dirty || !!git.fetch_error || els.appUpdateStartBtn.classList.contains('loading');
  }

  if (hasUpdateAvailable && !running) {
    clearAppUpdateReconnect();
    showAppUpdateStatus(
      tr('app_update_available').replace('{current}', current).replace('{remote}', remote),
      'ok'
    );
  } else if (statusRaw === 'success') {
    if (shouldReloadOnSuccess) {
      scheduleAppUpdatePageReload();
    } else {
      clearAppUpdateReconnect();
      showAppUpdateStatus(tr('app_update_success'), 'ok');
    }
  } else if (statusRaw === 'failed') {
    clearAppUpdateReconnect();
    showAppUpdateStatus(tr('app_update_failed'), 'err');
  } else if (reconnecting && serviceReachable && available && !running) {
    scheduleAppUpdatePageReload();
  } else if (reconnecting && (!serviceReachable || !available || running)) {
    showAppUpdateStatus(tr('app_update_reconnecting'), 'ok');
  } else if (item.error) {
    showAppUpdateStatus(String(item.error), 'err');
  } else if (!serviceReachable || !available) {
    showAppUpdateStatus(tr('app_update_unavailable'), 'err');
  } else if (git.fetch_error) {
    showAppUpdateStatus(String(git.fetch_error), 'err');
  } else if (git.dirty) {
    showAppUpdateStatus(tr('app_update_dirty'), 'err');
  } else if (running) {
    showAppUpdateStatus(tr('app_update_running'), 'ok');
  } else if (git.current_rev && git.remote_rev) {
    showAppUpdateStatus(tr('app_update_latest'), 'ok');
  }
}

function stopAppUpdateStatusPolling() {
  if (appUpdateStatusPollTimer) {
    clearInterval(appUpdateStatusPollTimer);
    appUpdateStatusPollTimer = null;
  }
}

function startAppUpdateStatusPolling() {
  if (!els.appUpdateTitle) return;
  stopAppUpdateStatusPolling();
  appUpdateStatusPollTimer = setInterval(async () => {
    if (state.view !== 'settings') return;
    try {
      const data = await loadAppUpdateStatus({ silent: true });
      if (!shouldKeepAppUpdatePolling(data)) stopAppUpdateStatusPolling();
    } catch {}
  }, APP_UPDATE_STATUS_POLL_MS);
}

function startAppUpdateBadgePolling() {
  if (!els.appUpdateTitle || appUpdateBadgePollTimer) return;
  const tick = () => {
    loadAppUpdateStatus({ silent: true, skipFollowPolling: true }).catch(() => {});
  };
  tick();
  appUpdateBadgePollTimer = setInterval(tick, APP_UPDATE_BADGE_POLL_MS);
}

async function loadAppUpdateStatus(opts = {}) {
  if (!els.appUpdateTitle) return null;
  try {
    const res = await fetch('/api/app-update/status', { cache: 'no-store' });
    const data = await res.json().catch(() => ({}));
    renderAppUpdate(data || {});
    if (!opts.skipFollowPolling && shouldKeepAppUpdatePolling(data || {})) startAppUpdateStatusPolling();
    return data;
  } catch (e) {
    const reconnecting = appUpdateReconnectActive();
    const prev = (state.appUpdate && typeof state.appUpdate === 'object') ? state.appUpdate : {};
    const data = {
      ok: false,
      service_reachable: false,
      running: reconnecting,
      status: reconnecting ? 'running' : 'idle',
      git: (prev.git && typeof prev.git === 'object') ? prev.git : {},
      log: Array.isArray(prev.log) ? prev.log : [],
      error: reconnecting ? '' : (opts.silent ? '' : tr('app_update_unavailable')),
    };
    renderAppUpdate(data);
    if (!opts.skipFollowPolling && reconnecting && !appUpdateStatusPollTimer) startAppUpdateStatusPolling();
    return data;
  }
}

async function checkAppUpdate() {
  if (!els.appUpdateTitle) return;
  const btn = els.appUpdateCheckBtn;
  const original = btn ? btn.textContent : tr('app_update_check');
  showAppUpdateStatus(tr('app_update_checking'), 'ok');
  try {
    if (btn) {
      btn.disabled = true;
      btn.classList.add('loading');
      btn.textContent = tr('app_update_checking');
    }
    const res = await fetch('/api/app-update/check', { method: 'POST', headers: { 'Content-Type': 'application/json' } });
    const data = await res.json().catch(() => ({}));
    renderAppUpdate(data || {});
  } catch {
    renderAppUpdate({ ok: false, service_reachable: false, error: tr('app_update_unavailable') });
  } finally {
    if (btn) {
      btn.classList.remove('loading');
      btn.textContent = original || tr('app_update_check');
      btn.disabled = false;
    }
    renderAppUpdate(state.appUpdate || {});
  }
}

function closeAppUpdateChoiceModal(choice = null) {
  if (els.appUpdateChoiceModal) els.appUpdateChoiceModal.classList.add('hidden');
  if (appUpdateChoiceResolver) {
    const resolve = appUpdateChoiceResolver;
    appUpdateChoiceResolver = null;
    resolve(choice);
  }
}

function openAppUpdateChoiceModal() {
  if (!els.appUpdateChoiceModal) return Promise.resolve(true);
  if (appUpdateChoiceResolver) closeAppUpdateChoiceModal(null);
  els.appUpdateChoiceModal.classList.remove('hidden');
  setTimeout(() => {
    try { (els.appUpdateChoiceCleanupBtn || els.appUpdateChoiceFastBtn || els.appUpdateChoiceClose).focus(); } catch {}
  }, 0);
  return new Promise((resolve) => {
    appUpdateChoiceResolver = resolve;
  });
}

async function startAppUpdate() {
  if (!els.appUpdateTitle) return;
  const cleanup = await openAppUpdateChoiceModal();
  if (cleanup === null) return;
  markAppUpdateReconnect();
  const btn = els.appUpdateStartBtn;
  const original = btn ? btn.textContent : tr('app_update_start');
  showAppUpdateStatus(tr('app_update_starting'), 'ok');
  try {
    if (btn) {
      btn.disabled = true;
      btn.classList.add('loading');
      btn.textContent = tr('app_update_starting');
    }
    const res = await fetch('/api/app-update/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cleanup }),
    });
    const data = await res.json().catch(() => ({}));
    renderAppUpdate(data || {});
    if (!res.ok || !data || data.ok === false) {
      clearAppUpdateReconnect();
      renderAppUpdate(data || {});
      return;
    }
    startAppUpdateStatusPolling();
  } catch {
    renderAppUpdate({ ok: false, service_reachable: false, running: true, status: 'running', error: '' });
    startAppUpdateStatusPolling();
  } finally {
    if (btn) {
      btn.classList.remove('loading');
      btn.textContent = original || tr('app_update_start');
      btn.disabled = false;
    }
    renderAppUpdate(state.appUpdate || {});
  }
}

async function saveAppUpdateSettings() {
  if (!els.appUpdateTitle) return;
  const btn = els.appUpdateSettingsSaveBtn;
  const original = btn ? btn.textContent : tr('app_update_save_settings');
  const enabled = !!(els.appUpdateAutoCheckToggle && els.appUpdateAutoCheckToggle.checked);
  const interval = Number(els.appUpdateIntervalInput ? els.appUpdateIntervalInput.value : 30);
  try {
    if (btn) {
      btn.disabled = true;
      btn.classList.add('loading');
    }
    const res = await fetch('/api/app-update/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        auto_check_enabled: enabled,
        auto_check_interval_minutes: Number.isFinite(interval) ? interval : 30,
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || data.ok === false) {
      showAppUpdateStatus((data && data.error) || tr('app_update_settings_failed'), 'err');
      return;
    }
    renderAppUpdate({ ...(state.appUpdate || {}), ...data });
    showAppUpdateStatus(tr('app_update_settings_saved'), 'ok');
  } catch {
    showAppUpdateStatus(tr('app_update_settings_failed'), 'err');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.classList.remove('loading');
      btn.textContent = original || tr('app_update_save_settings');
    }
  }
}

async function loadMapperTools(preferred = null) {
  try {
    const { res, data } = await fetchUploadDestinationConfig('uploads');
    if (!res.ok || !data || !data.ok) {
      const errMsg = String((data && data.error) || `HTTP ${res && res.status ? res.status : 'fejl'}`).trim();
      if (errMsg) showStatus(`Kunne ikke hente mapper: ${errMsg}`, 'err');
      return;
    }
    const folders = Array.isArray(data.folders) ? data.folders.filter(f => !!f) : [];
    state.mapperFolders = folders;
    if (state.mapperSelectedFolders && state.mapperSelectedFolders.size) {
      state.mapperSelectedFolders = new Set(
        Array.from(state.mapperSelectedFolders).filter(f => folders.includes(f))
      );
    }
    const wantedRaw = (preferred !== null) ? String(preferred || '') : String(state.mapperPath || data.subdir || '');
    const wanted = _normalizeMapperPath(wantedRaw);
    state.mapperPath = wanted;
    state.folder = wanted || null;
    _expandMapperAncestors(wanted);
    renderMapperContext(state.mapperPath);
    if (state.view === 'mapper') _syncRouteStateToUrl();
  } catch (e) {
    const errMsg = String((e && e.message) || e || '').trim();
    if (errMsg) showStatus(`Kunne ikke hente mapper: ${errMsg}`, 'err');
  }
}

async function createMapperFolder() {
  if (!els.mapperCreateModalInput) return;
  const parent = String(state.mapperPath || '');
  const path = (els.mapperCreateModalInput.value || '').trim();
  if (!path) {
    showStatus(tr('mapper_create_name_required'), 'err');
    try { els.mapperCreateModalInput.focus(); } catch {}
    return;
  }
  const createBtn = els.mapperCreateModalConfirm;
  const originalLabel = createBtn ? createBtn.textContent : tr('upload_create_folder');
  try {
    if (createBtn) {
      createBtn.disabled = true;
      createBtn.classList.add('loading');
      createBtn.textContent = tr('mapper_create_pending');
    }
    const res = await fetch('/api/settings/upload-folder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ destination: 'uploads', parent, path }),
    });
    const data = await res.json();
    if (!res.ok || !data || !data.ok) {
      showStatus((data && data.error) || tr('mapper_create_failed'), 'err');
      return;
    }
    els.mapperCreateModalInput.value = '';
    state.mapperFolders = Array.isArray(data.folders) ? data.folders.filter(f => !!f) : [];
    state.mapperPath = parent;
    state.folder = parent || null;
    renderMapperContext(parent);
    await loadPhotos();
    closeMapperCreateModal(false);
    const createdPath = String(data.created || path || '');
    showStatus(`${tr('mapper_created_status')}: ${createdPath}`, 'ok');
  } catch {
    showStatus(tr('mapper_create_error'), 'err');
  } finally {
    if (createBtn) {
      createBtn.classList.remove('loading');
      createBtn.textContent = originalLabel || tr('upload_create_folder');
      createBtn.disabled = false;
    }
  }
}

function _replaceMapperPathPrefix(value, oldPrefix, newPrefix) {
  const v = _normalizeMapperPath(value || '');
  const from = _normalizeMapperPath(oldPrefix || '');
  const to = _normalizeMapperPath(newPrefix || '');
  if (!v || !from || !to) return v;
  if (v === from) return to;
  if (v.startsWith(from + '/')) return to + v.slice(from.length);
  return v;
}

async function renameMapperFolder() {
  if (!els.mapperCreateModalInput) return;
  const target = _normalizeMapperPath(state.mapperRenameTargetPath || '');
  if (!target) {
    showStatus(tr('mapper_rename_select_one'), 'err');
    return;
  }
  const newName = String((els.mapperCreateModalInput.value || '')).trim();
  if (!newName) {
    showStatus(tr('mapper_rename_name_required'), 'err');
    try { els.mapperCreateModalInput.focus(); } catch {}
    return;
  }
  const currentName = target.includes('/') ? target.split('/').pop() : target;
  if (String(currentName || '').toLowerCase() === newName.toLowerCase()) {
    showStatus(tr('mapper_rename_same_name'), 'err');
    return;
  }

  const saveBtn = els.mapperCreateModalConfirm;
  const originalLabel = saveBtn ? saveBtn.textContent : tr('mapper_rename_action');
  try {
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.classList.add('loading');
      saveBtn.textContent = tr('mapper_rename_pending');
    }
    const res = await fetch('/api/settings/upload-folder-rename', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ destination: 'uploads', path: target, new_name: newName }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || !data.ok) {
      showStatus((data && data.error) || tr('mapper_rename_failed'), 'err');
      return;
    }

    const oldPath = _normalizeMapperPath(data.old_path || target);
    const newPath = _normalizeMapperPath(data.new_path || '');
    if (!newPath) {
      showStatus(tr('mapper_rename_failed'), 'err');
      return;
    }

    state.mapperFolders = Array.isArray(data.folders) ? data.folders.filter((f) => !!f) : [];
    if (state.mapperSelectedFolders && state.mapperSelectedFolders.size) {
      const next = new Set();
      state.mapperSelectedFolders.forEach((f) => {
        const mapped = _replaceMapperPathPrefix(String(f || ''), oldPath, newPath);
        if (mapped) next.add(mapped);
      });
      state.mapperSelectedFolders = next;
    }

    const nextCurrent = _replaceMapperPathPrefix(String(state.mapperPath || ''), oldPath, newPath);
    state.mapperPath = nextCurrent;
    state.folder = nextCurrent || null;
    _expandMapperAncestors(nextCurrent);

    closeMapperCreateModal();
    await loadMapperTools(nextCurrent);
    await loadPhotos();
    showStatus(`${tr('mapper_rename_success')}: ${oldPath} -> ${newPath}`, 'ok');
  } catch {
    showStatus(tr('mapper_rename_error'), 'err');
  } finally {
    if (saveBtn) {
      saveBtn.classList.remove('loading');
      saveBtn.textContent = originalLabel || tr('mapper_rename_action');
      saveBtn.disabled = false;
    }
  }
}

function setMapperEditMode(enabled) {
  state.mapperEditMode = !!enabled;
  if (!state.mapperEditMode) {
    _stopMapperDragSelectSession();
    state.mapperSelectedFolders = new Set();
    state.mapperSelectedPhotoIds = new Set();
  }
  renderMapperContext(state.mapperPath || '');
  if (state.view === 'mapper') renderGrid();
  // Hide or show any existing info overlays depending on mode
  try {
    document.querySelectorAll('.info-icon-overlay').forEach(el=>{
      el.style.display = state.mapperEditMode ? 'none' : '';
    });
  } catch {}
}

const MAPPER_DRAG_SELECT_MIN_DISTANCE_PX = 8;
const MAPPER_DRAG_SELECT_SAMPLE_STEP_PX = 18;
const MAPPER_DRAG_SELECT_ROW_TOP_EPS_PX = 10;
let mapperDragSelectSession = null;
let mapperDragSelectRefreshRaf = 0;
let mapperDragSelectSuppressClickUntil = 0;

function _queueMapperDragSelectContextRefresh() {
  if (mapperDragSelectRefreshRaf) return;
  mapperDragSelectRefreshRaf = window.requestAnimationFrame(() => {
    mapperDragSelectRefreshRaf = 0;
    try { renderMapperContext(state.mapperPath || ''); } catch {}
  });
}

function _isMapperSelectablePhotoCard(card) {
  if (!card || !card.classList) return false;
  if (!state || state.view !== 'mapper' || !state.mapperEditMode) return false;
  if (!els.grid || !els.grid.contains(card)) return false;
  if (!card.classList.contains('photo-card')) return false;
  if (card.classList.contains('folder-card')) return false;
  if (card.classList.contains('upload-card')) return false;
  return true;
}

function _applyMapperPhotoSelection(card) {
  if (!_isMapperSelectablePhotoCard(card)) return false;
  const photoId = Number(card.getAttribute('data-photo-id') || 0);
  if (!Number.isFinite(photoId) || photoId <= 0) return false;
  if (!state.mapperSelectedPhotoIds) state.mapperSelectedPhotoIds = new Set();
  if (state.mapperSelectedPhotoIds.has(photoId)) return false;
  state.mapperSelectedPhotoIds.add(photoId);
  card.classList.add('selected');
  return true;
}

function _getMapperSelectablePhotoCardsInOrder() {
  if (!els.grid) return [];
  return Array.from(els.grid.querySelectorAll('.photo-card[data-photo-id]')).filter((card) => _isMapperSelectablePhotoCard(card));
}

function _buildMapperDragRowMeta(cards) {
  const rowByIndex = new Array(cards.length).fill(0);
  const rowStartByRow = [];
  const rowEndByRow = [];
  let row = -1;
  let currentTop = null;

  for (let i = 0; i < cards.length; i++) {
    const rect = cards[i].getBoundingClientRect();
    const top = Number(rect && rect.top);
    if (currentTop === null || !Number.isFinite(top) || Math.abs(top - currentTop) > MAPPER_DRAG_SELECT_ROW_TOP_EPS_PX) {
      row += 1;
      currentTop = Number.isFinite(top) ? top : currentTop;
      rowStartByRow[row] = i;
      if (row > 0) rowEndByRow[row - 1] = i - 1;
    }
    rowByIndex[i] = row;
  }
  if (row >= 0) rowEndByRow[row] = cards.length - 1;

  return { rowByIndex, rowStartByRow, rowEndByRow };
}

function _mapperSelectableCardIndexAtPoint(session, x, y) {
  const node = document.elementFromPoint(Number(x), Number(y));
  if (!(node instanceof Element)) return -1;
  const card = node.closest('.photo-card[data-photo-id]');
  if (!_isMapperSelectablePhotoCard(card)) return -1;
  const key = card.getAttribute('data-photo-id') || '';
  if (!key) return -1;
  const idx = session && session.indexByPhotoId ? session.indexByPhotoId.get(key) : null;
  return Number.isFinite(idx) ? Number(idx) : -1;
}

function _normalizeMapperDragReadingTargetIndex(session, rawIndex) {
  const idx = Number(rawIndex);
  if (!Number.isFinite(idx) || idx < 0) return -1;
  if (!session || !Array.isArray(session.cards) || !session.cards.length) return idx;
  const max = session.cards.length - 1;
  return Math.max(0, Math.min(max, Math.round(idx)));
}

function _selectMapperPhotoRangeByIndex(session, fromIndex, toIndex) {
  if (!session || !Array.isArray(session.cards) || !session.cards.length) return false;
  const cards = session.cards;
  const max = cards.length - 1;
  const aRaw = Number(fromIndex);
  const bRaw = Number(toIndex);
  if (!Number.isFinite(aRaw) || !Number.isFinite(bRaw)) return false;
  const a = Math.max(0, Math.min(max, Math.round(aRaw)));
  const b = Math.max(0, Math.min(max, Math.round(bRaw)));
  const lo = Math.min(a, b);
  const hi = Math.max(a, b);
  let changed = false;
  for (let i = lo; i <= hi; i++) {
    const card = cards[i];
    if (!card) continue;
    if (_applyMapperPhotoSelection(card)) changed = true;
  }
  if (changed) _queueMapperDragSelectContextRefresh();
  return changed;
}

function _selectMapperPhotosAlongSegment(session, fromX, fromY, toX, toY) {
  if (!session) return;
  const dx = Number(toX) - Number(fromX);
  const dy = Number(toY) - Number(fromY);
  const distance = Math.hypot(dx, dy);
  const steps = Math.max(1, Math.ceil(distance / MAPPER_DRAG_SELECT_SAMPLE_STEP_PX));
  let lastTouchedIndex = -1;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const x = Number(fromX) + dx * t;
    const y = Number(fromY) + dy * t;
    const idx = _mapperSelectableCardIndexAtPoint(session, x, y);
    if (idx >= 0) lastTouchedIndex = idx;
  }
  if (lastTouchedIndex < 0) return;
  const targetIdx = _normalizeMapperDragReadingTargetIndex(session, lastTouchedIndex);
  if (targetIdx < 0) return;
  _selectMapperPhotoRangeByIndex(session, session.anchorIndex, targetIdx);
  session.lastTargetIndex = targetIdx;
}

function _buildMapperDragIndexMap(cards) {
  const map = new Map();
  cards.forEach((card, idx) => {
    const key = card.getAttribute('data-photo-id') || '';
    if (key) map.set(key, idx);
  });
  return map;
}

function _resolveMapperDragAnchorIndex(card, indexByPhotoId, cards) {
  const key = card && card.getAttribute ? (card.getAttribute('data-photo-id') || '') : '';
  const mapIdx = key ? indexByPhotoId.get(key) : null;
  if (Number.isFinite(mapIdx)) return Number(mapIdx);
  const fallback = Array.isArray(cards) ? cards.indexOf(card) : -1;
  return Number.isFinite(fallback) ? fallback : -1;
}

function _buildMapperDragSession(ev, card) {
  const cards = _getMapperSelectablePhotoCardsInOrder();
  if (!cards.length) return null;
  const indexByPhotoId = _buildMapperDragIndexMap(cards);
  const anchorIndex = _resolveMapperDragAnchorIndex(card, indexByPhotoId, cards);
  if (!Number.isFinite(anchorIndex) || anchorIndex < 0) return null;
  const rowMeta = _buildMapperDragRowMeta(cards);
  return {
    pointerId: Number(ev.pointerId),
    startX: Number(ev.clientX || 0),
    startY: Number(ev.clientY || 0),
    lastX: Number(ev.clientX || 0),
    lastY: Number(ev.clientY || 0),
    dragging: false,
    cards,
    indexByPhotoId,
    anchorIndex,
    lastTargetIndex: anchorIndex,
    rowByIndex: rowMeta.rowByIndex,
    rowStartByRow: rowMeta.rowStartByRow,
    rowEndByRow: rowMeta.rowEndByRow,
  };
}

function _beginMapperDragSelectionIfNeeded(session, x, y) {
  if (session.dragging) return true;
  const distance = Math.hypot(Number(x) - session.startX, Number(y) - session.startY);
  if (distance < MAPPER_DRAG_SELECT_MIN_DISTANCE_PX) return false;
  session.dragging = true;
  _selectMapperPhotoRangeByIndex(session, session.anchorIndex, session.anchorIndex);
  return true;
}

function _updateMapperDragSelection(session, x, y) {
  if (!_beginMapperDragSelectionIfNeeded(session, x, y)) return;
  _selectMapperPhotosAlongSegment(session, session.lastX, session.lastY, x, y);
  session.lastX = x;
  session.lastY = y;
}

function _createMapperDragSession(ev, card) {
  const session = _buildMapperDragSession(ev, card);
  if (!session) return null;
  return session;
}

function _startMapperDragSelection(ev, card) {
  _stopMapperDragSelectSession();
  const session = _createMapperDragSession(ev, card);
  if (!session) return null;
  mapperDragSelectSession = session;
  document.addEventListener('pointermove', _onMapperDragSelectPointerMove, { passive: false });
  document.addEventListener('pointerup', _onMapperDragSelectPointerUp, { passive: true });
  document.addEventListener('pointercancel', _onMapperDragSelectPointerCancel, { passive: true });
  return session;
}

function _handleMapperDragPointerMove(ev) {
  const session = mapperDragSelectSession;
  if (!session) return;
  if (Number(ev.pointerId) !== Number(session.pointerId)) return;
  const x = Number(ev.clientX || 0);
  const y = Number(ev.clientY || 0);
  _updateMapperDragSelection(session, x, y);
  try { ev.preventDefault(); } catch {}
}

function _handleMapperDragPointerStart(ev, card) {
  if (!_isMapperSelectablePhotoCard(card)) return;
  if (!ev) return;
  if (ev.button != null && Number(ev.button) !== 0) return;
  if (ev.pointerType === 'mouse' && ev.buttons != null && (Number(ev.buttons) & 1) !== 1) return;
  _startMapperDragSelection(ev, card);
}

function _finishMapperDragSelectSession(pointerId = null) {
  const session = mapperDragSelectSession;
  if (!session) return;
  if (pointerId !== null && Number(pointerId) !== Number(session.pointerId)) return;
  if (session.dragging) mapperDragSelectSuppressClickUntil = Date.now() + 280;
  _stopMapperDragSelectSession();
}

function _onMapperDragSelectPointerMove(ev) {
  _handleMapperDragPointerMove(ev);
}

function _onMapperDragSelectPointerUp(ev) {
  _finishMapperDragSelectSession(ev && ev.pointerId != null ? ev.pointerId : null);
}

function _onMapperDragSelectPointerCancel(ev) {
  _finishMapperDragSelectSession(ev && ev.pointerId != null ? ev.pointerId : null);
}

function _stopMapperDragSelectSession() {
  document.removeEventListener('pointermove', _onMapperDragSelectPointerMove);
  document.removeEventListener('pointerup', _onMapperDragSelectPointerUp);
  document.removeEventListener('pointercancel', _onMapperDragSelectPointerCancel);
  mapperDragSelectSession = null;
}

function _startMapperDragSelect(ev, card) {
  _handleMapperDragPointerStart(ev, card);
}

function _consumeMapperDragSelectClickSuppression() {
  if (Date.now() < mapperDragSelectSuppressClickUntil) {
    mapperDragSelectSuppressClickUntil = 0;
    return true;
  }
  return false;
}

function toggleMapperFolderSelection(folderPath) {
  if (!state.mapperSelectedFolders) state.mapperSelectedFolders = new Set();
  const wasSelected = state.mapperSelectedFolders.has(folderPath);
  if (wasSelected) state.mapperSelectedFolders.delete(folderPath); else state.mapperSelectedFolders.add(folderPath);
  // Update only the affected card in DOM to avoid grid re-render/flicker
  try {
    const sel = `.folder-card[data-folder="${CSS.escape(folderPath)}"]`;
    const card = document.querySelector(sel);
    if (card) {
      card.classList.toggle('selected', !wasSelected);
      let badge = card.querySelector('.folder-select-badge');
      if (!badge) {
        const thumb = card.querySelector('.card-thumb');
        badge = document.createElement('span');
        badge.className = 'folder-select-badge';
        if (thumb) thumb.appendChild(badge);
      }
      if (badge) badge.textContent = !wasSelected ? '✓' : '';
    }
  } catch {}
  // Update header/context counters, but do not re-render grid
  try { renderMapperContext(state.mapperPath || ''); } catch {}
}

async function deleteSelectedMapperFolders() {
  const selected = Array.from(state.mapperSelectedFolders || []);
  if (!selected.length) {
    showStatus(tr('mapper_select_delete_none'), 'err');
    return;
  }
  const confirmMsg = tr('mapper_delete_confirm').replace('{count}', String(selected.length));
  const ok = confirm(confirmMsg);
  if (!ok) return;
  const deleteBtn = els.mapperDeleteBtn;
  const originalLabel = deleteBtn ? deleteBtn.textContent : 'Slet valgte';
  try {
    if (deleteBtn) {
      deleteBtn.disabled = true;
      deleteBtn.classList.add('loading');
      deleteBtn.textContent = tr('mapper_delete_pending');
    }
    const res = await fetch('/api/settings/upload-folder-delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ destination: 'uploads', paths: selected }),
    });
    const data = await res.json();
    if (!res.ok || !data || !data.ok) {
      showStatus((data && data.error) || tr('mapper_delete_failed'), 'err');
      return;
    }
    state.mapperFolders = Array.isArray(data.folders) ? data.folders.filter(f => !!f) : [];
    invalidateStoredFolderPreviews([...(data.preview_folders || []), ...selected]);
    state.mapperSelectedFolders = new Set();
    setMapperEditMode(false);
    await loadMapperTools(state.mapperPath || '');
    await loadPhotos();
    const deletedCount = Array.isArray(data.deleted) ? data.deleted.length : 0;
    const removedPhotos = Number(data.removed_photos || 0);
    const successMsg = tr('mapper_delete_success')
      .replace('{count}', String(deletedCount))
      .replace('{removed}', String(removedPhotos));
    showStatus(successMsg, 'ok');
  } catch {
    showStatus(tr('mapper_delete_error'), 'err');
  } finally {
    if (deleteBtn) {
      deleteBtn.classList.remove('loading');
      deleteBtn.textContent = originalLabel || 'Slet valgte';
    }
    renderMapperContext(state.mapperPath || '');
  }
}

async function deleteSelectedMapperPhotos() {
  const selected = Array.from(state.mapperSelectedPhotoIds || []);
  if (!selected.length) {
    showStatus(tr('mapper_select_delete_none'), 'err');
    return;
  }
  const ok = confirm(tr('mapper_delete_confirm').replace('{count}', String(selected.length)));
  if (!ok) return;
  const deleteBtn = els.mapperDeleteBtn;
  const originalLabel = deleteBtn ? deleteBtn.textContent : 'Slet valgte';
  try {
    if (deleteBtn) {
      deleteBtn.disabled = true; deleteBtn.classList.add('loading'); deleteBtn.textContent = tr('mapper_delete_pending');
    }
    const res = await fetch('/api/photos/delete', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ photo_ids: selected }) });
    const data = await res.json().catch(()=>({}));
    if (!res.ok || !data || !data.ok) { showStatus((data && data.error) || tr('mapper_delete_failed'), 'err'); return; }
    invalidateStoredFolderPreviews(data.preview_folders || (data.removed && data.removed.preview_folders) || []);
    state.mapperSelectedPhotoIds = new Set();
    setMapperEditMode(false);
    await loadPhotos();
    const removed = Number((data.removed && data.removed.photos) || selected.length);
    showStatus(tr('mapper_delete_success').replace('{count}', String(removed)).replace('{removed}', String(removed)), 'ok');
  } catch {
    showStatus(tr('mapper_delete_error'), 'err');
  } finally {
    if (deleteBtn) { deleteBtn.classList.remove('loading'); deleteBtn.textContent = originalLabel || 'Slet valgte'; }
    renderMapperContext(state.mapperPath || '');
  }
}

async function deleteSelectedInMapper() {
  const photoCount = state.mapperSelectedPhotoIds ? state.mapperSelectedPhotoIds.size : 0;
  const folderCount = state.mapperSelectedFolders ? state.mapperSelectedFolders.size : 0;
  if (photoCount > 0) return deleteSelectedMapperPhotos();
  if (folderCount > 0) return deleteSelectedMapperFolders();
  showStatus(tr('mapper_select_delete_none'), 'err');
}

// Select all visible items in Mapper (prefer photos in current folder; else folders)
function mapperSelectAll() {
  try { if (!state.mapperEditMode) setMapperEditMode(true); } catch {}
  // Attempt to select all visible photo cards in current folder
  const current = String(state.mapperPath || '');
  const items = Array.isArray(state.items) ? state.items.slice() : [];
  // Normalize rel_path → folder path like in renderGrid()
  const folderOf = (rel) => {
    let f = String(rel || '');
    f = f.includes('/') ? f.split('/').slice(0, -1).join('/') : '';
    if (f === 'uploads') f = '';
    else if (f.startsWith('uploads/')) f = f.slice('uploads/'.length);
    if (f.startsWith('converted/')) f = f.slice('converted/'.length);
    if (f.startsWith('originals/')) f = f.slice('originals/'.length);
    return f;
  };
  const direct = items.filter(it => folderOf(String(it.rel_path || '')) === current);
  if (!state.mapperSelectedPhotoIds) state.mapperSelectedPhotoIds = new Set();
  if (direct.length > 0) {
    for (const it of direct) state.mapperSelectedPhotoIds.add(it.id);
    try { document.querySelectorAll('.gallery-grid .photo-card:not(.folder-card):not(.upload-card)').forEach(el=> el.classList.add('selected')); } catch {}
  } else {
    // No direct photos; select all child folders
    if (!state.mapperSelectedFolders) state.mapperSelectedFolders = new Set();
    try {
      document.querySelectorAll('.gallery-grid .folder-card').forEach(card => {
        const f = card.getAttribute('data-folder') || '';
        if (f) state.mapperSelectedFolders.add(f);
        card.classList.add('selected');
        let badge = card.querySelector('.folder-select-badge');
        if (!badge) { const t = card.querySelector('.card-thumb'); badge = document.createElement('span'); badge.className = 'folder-select-badge'; if (t) t.appendChild(badge); }
        if (badge) badge.textContent = '✓';
      });
    } catch {}
  }
  renderMapperContext(state.mapperPath || '');
}

function mapperClearSelection() {
  _stopMapperDragSelectSession();
  state.mapperSelectedPhotoIds = new Set();
  state.mapperSelectedFolders = new Set();
  try { document.querySelectorAll('.gallery-grid .photo-card.selected, .gallery-grid .folder-card.selected').forEach(el=> el.classList.remove('selected')); } catch {}
  try { document.querySelectorAll('.gallery-grid .folder-card .folder-select-badge').forEach(b=> b.textContent=''); } catch {}
  renderMapperContext(state.mapperPath || '');
}

// --- Drag & drop: collect files and directories with relative paths (supports empty folders) ---
async function _readDirectoryEntriesRecursive(entry, basePath, out) {
  const prefix = basePath ? `${basePath}/` : '';
  if (entry.isFile) {
    const file = await new Promise((resolve, reject) => {
      try { entry.file(resolve, reject); } catch (e) { reject(e); }
    });
    out.files.push({ file, relPath: `${prefix}${file.name}` });
  } else if (entry.isDirectory) {
    // Record the directory itself so we can recreate empty folders too
    const thisDir = `${prefix}${entry.name}`;
    if (thisDir) out.dirs.add(thisDir);
    const reader = entry.createReader();
    const readAll = async () => {
      const batch = await new Promise((resolve, reject) => {
        try { reader.readEntries(resolve, reject); } catch (e) { reject(e); }
      });
      if (!batch || !batch.length) return [];
      // Recursively walk children
      for (const child of batch) {
        await _readDirectoryEntriesRecursive(child, thisDir, out);
      }
      // Continue until no more entries
      await readAll();
    };
    await readAll();
  }
}

async function collectDroppedFilesWithPaths(dataTransfer) {
  const filesOut = [];
  const dirsOut = new Set();
  try {
    const items = (dataTransfer && dataTransfer.items) ? Array.from(dataTransfer.items) : [];
    const entries = [];
    for (const it of items) {
      try {
        if (it && it.kind === 'file' && typeof it.webkitGetAsEntry === 'function') {
          const entry = it.webkitGetAsEntry();
          if (entry) entries.push(entry);
        }
      } catch {}
    }
    if (entries.length) {
      for (const entry of entries) {
        const acc = { files: [], dirs: new Set() };
        await _readDirectoryEntriesRecursive(entry, '', acc);
        for (const f of acc.files) filesOut.push(f);
        for (const d of acc.dirs) dirsOut.add(d);
      }
      return { files: filesOut, dirs: Array.from(dirsOut) };
    }
  } catch {}
  // Fallback: use File.webkitRelativePath if present or just the filename
  const files = (dataTransfer && dataTransfer.files) ? Array.from(dataTransfer.files) : [];
  for (const f of files) {
    const rel = String(f.webkitRelativePath || f.relativePath || f.name || '').trim() || f.name;
    filesOut.push({ file: f, relPath: rel });
    // We can infer parent dirs from rel path (but cannot discover empty dirs in fallback)
    const parts = rel.replace(/\\/g, '/').split('/').filter(Boolean);
    if (parts.length > 1) {
      let cur = '';
      for (let i = 0; i < parts.length - 1; i += 1) {
        cur = cur ? `${cur}/${parts[i]}` : parts[i];
        dirsOut.add(cur);
      }
    }
  }
  return { files: filesOut, dirs: Array.from(dirsOut) };
}

function _groupByRelDir(fileItems, rootToStrip = '') {
  const groups = new Map();
  for (const { file, relPath } of fileItems) {
    let rp = String(relPath || '').replace(/\\/g, '/');
    if (rootToStrip) {
      const pfx = `${rootToStrip}/`;
      if (rp.startsWith(pfx)) rp = rp.slice(pfx.length);
    }
    const parts = rp.split('/').filter(Boolean);
    const dir = parts.length > 1 ? parts.slice(0, -1).join('/') : '';
    if (!groups.has(dir)) groups.set(dir, []);
    groups.get(dir).push(file);
  }
  return groups; // Map<dir, File[]>
}

async function uploadDroppedDataTransfer(dataTransfer, baseSubdir) {
  const payload = await collectDroppedFilesWithPaths(dataTransfer);
  if (!payload) return;
  const items = Array.isArray(payload.files) ? payload.files : [];
  const dirList = Array.isArray(payload.dirs) ? payload.dirs.slice() : [];
  if (!items.length && !dirList.length) return;
  // If all file items share the same top-level folder (dragged parent), strip it
  let commonRoot = '';
  try {
    if (items.length) {
      const first = String(items[0].relPath || '').replace(/\\/g, '/');
      const seg = first.split('/').filter(Boolean)[0] || '';
      if (seg && items.every(it => String(it.relPath || '').replace(/\\/g, '/').startsWith(seg + '/'))) {
        commonRoot = seg;
      }
    } else if (dirList.length) {
      const first = String(dirList[0] || '').replace(/\\/g, '/');
      const seg = first.split('/').filter(Boolean)[0] || '';
      if (seg && dirList.every(d => String(d || '').replace(/\\/g, '/').startsWith(seg + '/'))) {
        commonRoot = seg;
      }
    }
  } catch {}

  const groups = _groupByRelDir(items, commonRoot);
  // 1) Create all folders upfront for nicer UX (including empty ones)
  try {
    const makeOne = async (parent, name) => {
      const res = await fetch('/api/settings/upload-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ destination: 'uploads', parent, path: name }),
      });
      await res.json().catch(()=>({}));
    };
    const created = new Set();
    const base = String(baseSubdir || '').trim();
    // Ensure the dropped top folder itself is created
    let effectiveBase = base;
    if (commonRoot) {
      const rootTarget = base ? `${base}/${commonRoot}` : commonRoot;
      await makeOne(base, commonRoot);
      created.add(rootTarget);
      effectiveBase = rootTarget;
    }
    // Collect all dirs from file groups and explicit dirList
    const fileDirs = Array.from(groups.keys()).filter(Boolean);
    const allDirs = fileDirs.concat(dirList)
      .map((d) => {
        const s = String(d || '').replace(/\\/g, '/');
        if (!commonRoot) return s;
        if (s === commonRoot) return '';
        if (s.startsWith(commonRoot + '/')) return s.slice(commonRoot.length + 1);
        return s;
      })
      .filter(Boolean)
      .sort((a,b)=>a.split('/').length - b.split('/').length);
    for (const dir of allDirs) {
      let parent = effectiveBase;
      const parts = dir.split('/').filter(Boolean);
      for (const part of parts) {
        const p = parent ? `${parent}/${part}` : part;
        if (!created.has(p)) {
          await makeOne(parent, part);
          created.add(p);
        }
        parent = p;
      }
    }
  } catch {}

  // If there are no files to upload, we are done after creating the directories
  if (!items.length) return;

  // If everything is root files (single group with dir==''), fall back to a single batch
  if (groups.size === 1 && groups.has('')) {
    const base = String(baseSubdir || '').trim();
    const sub = commonRoot ? (base ? `${base}/${commonRoot}` : commonRoot) : base;
    await uploadFiles(groups.get(''), { destination: 'uploads', subdir: sub });
    return;
  }
  // Otherwise, queue one batch per subfolder to preserve structure
  const promises = [];
  for (const [dir, files] of groups.entries()) {
    const base = String(baseSubdir || '').trim();
    const baseWithRoot = commonRoot ? (base ? `${base}/${commonRoot}` : commonRoot) : base;
    const subdir = dir ? (baseWithRoot ? `${baseWithRoot}/${dir}` : dir) : baseWithRoot;
    // Enqueue all batches quickly; queue runner will handle sequence
    promises.push(uploadFiles(files, { destination: 'uploads', subdir }));
  }
  // Do not await here to keep UI snappy; callers don't depend on resolution
}

let _dragDepth = 0;
let _internalImageDrag = false;

document.addEventListener('dragstart', (e) => {
  const target = e.target;
  if (!(target instanceof HTMLElement)) return;
  if (!target.closest('.photo-card') && !target.closest('#viewer')) return;
  _internalImageDrag = true;
  if (target instanceof HTMLImageElement) {
    e.preventDefault();
  }
});

document.addEventListener('dragend', () => {
  _internalImageDrag = false;
  _dragDepth = 0;
  _hideGlobalDropOverlay();
});

function _showGlobalDropOverlay() {
  ensureUploadOverlayRefs();
  if (!els.uploadOverlay) return;
  const canUploadHere = (state.view === 'mapper' && !state.mapperEditMode);
  const targetLabel = state.mapperPath ? `uploads/${state.mapperPath}` : 'uploads (rodmappe)';
  const titleEl = document.querySelector('#uploadOverlay .upload-title');
  if (titleEl) {
    titleEl.textContent = canUploadHere
      ? 'Slip filer for at uploade'
      : 'Gå til Mapper for at uploade';
  }
  if (els.uploadProgressText) {
    els.uploadProgressText.textContent = canUploadHere
      ? `Upload destination: ${targetLabel}`
      : 'Upload er kun aktiv i Mapper-sektionen';
  }
  if (els.uploadProgressBar) {
    els.uploadProgressBar.style.width = canUploadHere ? '100%' : '0%';
  }
  els.uploadOverlay.classList.toggle('upload-ready', canUploadHere);
  els.uploadOverlay.classList.toggle('upload-blocked', !canUploadHere);
  els.uploadOverlay.classList.remove('hidden');
  els.uploadOverlay.classList.add('active');
}

function _hideGlobalDropOverlay() {
  ensureUploadOverlayRefs();
  if (!els.uploadOverlay) return;
  els.uploadOverlay.classList.remove('active', 'upload-ready', 'upload-blocked');
  els.uploadOverlay.classList.add('hidden');
}

window.addEventListener('dragenter', (e) => {
  if (_internalImageDrag) return;
  if (!(e.dataTransfer && e.dataTransfer.types && e.dataTransfer.types.includes('Files'))) return;
  _dragDepth += 1;
  _showGlobalDropOverlay();
});

window.addEventListener('dragover', (e) => {
  if (_internalImageDrag) return;
  if (e.dataTransfer && e.dataTransfer.types && e.dataTransfer.types.includes('Files')) {
    e.preventDefault();
    _showGlobalDropOverlay();
  }
});

window.addEventListener('dragleave', () => {
  _dragDepth = Math.max(0, _dragDepth - 1);
  if (_dragDepth === 0) _hideGlobalDropOverlay();
});

window.addEventListener('drop', async (e) => {
  _dragDepth = 0;
  if (_internalImageDrag) {
    _internalImageDrag = false;
    _hideGlobalDropOverlay();
    return;
  }
  const hasFiles = !!(e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length);
  if (hasFiles) {
    e.preventDefault();
    const droppedInsideMapperZone = !!(els.mapperDropZone && e.target && els.mapperDropZone.contains(e.target));
    if (state.view !== 'mapper' || state.mapperEditMode) {
      showStatus(tr('upload_mapper_only'), 'err');
    } else if (!droppedInsideMapperZone) {
      const targetSubdir = String(state.mapperPath || '');
      await uploadDroppedDataTransfer(e.dataTransfer, targetSubdir);
      await loadMapperTools(targetSubdir);
      await loadPhotos();
    }
  }
  _internalImageDrag = false;
  _hideGlobalDropOverlay();
});

function buildPlacesGeoJSON(items) {
  const feats = [];
  for (const it of items) {
    const lat = it.gps_lat != null ? parseFloat(it.gps_lat) : null;
    const lon = it.gps_lon != null ? parseFloat(it.gps_lon) : null;
    if (isFinite(lat) && isFinite(lon)) {
      feats.push({
        type: "Feature",
        geometry: { type: "Point", coordinates: [lon, lat] },
        properties: {
          id: it.id,
          name: it.filename || "(ukendt)",
          thumb: it.thumb_url || null,
          date: it.captured_at || it.modified_fs || "",
        },
      });
    }
  }
  return { type: "FeatureCollection", features: feats };
}

function initOrUpdatePlacesMap() {
  if (!els.placesMapEl) return;
  // Lazy init map
  if (typeof window.maplibregl === 'undefined') {
    // Try to load on demand; then re-enter
    ensureMaplibre().then((ok)=>{ if (ok) initOrUpdatePlacesMap(); else showStatus('Kortkode kunne ikke indlæses (MapLibre blokeret).', 'err'); });
    return;
  }
  if (!placesMap) {
    placesMap = new maplibregl.Map({
      container: els.placesMapEl,
      // Street/label style (Carto Positron GL) without API key
      style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
      center: [10, 56],
      zoom: 4,
      pitch: 0,
      bearing: 0,
      dragRotate: false,
      pitchWithRotate: false,
      attributionControl: false,
    });
    // Add attribution including MapLibre (plus source attributions from the style)
    placesMap.addControl(new maplibregl.AttributionControl({
      compact: true,
      customAttribution: "MapLibre"
    }));
    placesMap.addControl(new maplibregl.NavigationControl({ showCompass: false }));
    placesMap.on("load", () => {
      // Add clustered source + layers
      const geo0 = buildPlacesGeoJSON(state.items);
      console.log("[Steder] init features:", geo0.features.length);
      addOrUpdatePlacesSource(geo0);
      addPlacesLayers();
      // Cluster click expands
      placesMap.on("click", "clusters", (e) => {
        const features = placesMap.queryRenderedFeatures(e.point, { layers: ["clusters"] });
        const clusterId = features[0].properties.cluster_id;
        const src = placesMap.getSource("places");
        src.getClusterExpansionZoom(clusterId, (err, zoom) => {
          if (err) return;
          placesMap.easeTo({ center: features[0].geometry.coordinates, zoom });
        });
      });
      // Single point click shows popup
      placesMap.on("click", "unclustered-point", (e) => {
        const f = e.features && e.features[0];
        if (!f) return;
        const p = f.properties || {};
        const html = `
          <div class="places-map-popup">
            ${p.thumb ? `<img class="thumb" src="${p.thumb}" alt="">` : ""}
            <div class="meta">${p.name || ""}</div>
            <div class="meta">${p.date ? new Date(p.date).toLocaleString("da-DK") : ""}</div>
          </div>`;
        new maplibregl.Popup({ offset: 12 })
          .setLngLat(f.geometry.coordinates)
          .setHTML(html)
          .addTo(placesMap);
      });
      placesMap.on("mouseenter", "clusters", () => (placesMap.getCanvas().style.cursor = "pointer"));
      placesMap.on("mouseleave", "clusters", () => (placesMap.getCanvas().style.cursor = ""));
      placesMap.on("mouseenter", "unclustered-point", () => (placesMap.getCanvas().style.cursor = "pointer"));
      placesMap.on("mouseleave", "unclustered-point", () => (placesMap.getCanvas().style.cursor = ""));
      placesSourceReady = true;
      // Render initial HTML markers and keep them updated
      renderPlacesMarkers();
      placesMap.on("moveend", renderPlacesMarkers);
      placesMap.on("zoomend", renderPlacesMarkers);
      placesMap.on("data", (e) => { if (e.sourceId === "places" && e.isSourceLoaded) renderPlacesMarkers(); });
    });
  }
  // Update data if map already loaded
  if (placesMap && placesMap.isStyleLoaded()) {
    const geo = buildPlacesGeoJSON(state.items);
    if (!placesMap.getSource("places")) {
      addOrUpdatePlacesSource(geo);
      addPlacesLayers();
    } else {
      placesMap.getSource("places").setData(geo);
    }
    const banner = document.getElementById("placesBanner");
    if (banner) {
      const n = (geo.features && geo.features.length) || 0;
      if (n === 0) {
        banner.style.display = "block";
        banner.textContent = "Ingen GPS-billeder fundet i visningen";
      } else {
        banner.style.display = "block";
        banner.textContent = `GPS-billeder: ${n}`;
      }
    }
    // Fit bounds to data when entering view
    try {
      if (geo.features && geo.features.length) {
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        for (const f of geo.features) {
          const [x, y] = f.geometry.coordinates;
          if (x < minX) minX = x; if (y < minY) minY = y; if (x > maxX) maxX = x; if (y > maxY) maxY = y;
        }
        const b = [[minX, minY], [maxX, maxY]];
        placesMap.fitBounds(b, { padding: 40, duration: 400, maxZoom: 12 });
      }
    } catch {}
    setTimeout(() => { try { placesMap.resize(); renderPlacesMarkers(); } catch {} }, 50);
  }
}

function addOrUpdatePlacesSource(geo) {
  if (placesMap.getSource("places")) {
    placesMap.getSource("places").setData(geo);
    return;
  }
  placesMap.addSource("places", {
    type: "geojson",
    data: geo,
    cluster: true,
      // Klynger bevares ved tæt zoom; større radius gør dem mere stabile
      clusterMaxZoom: 20,
      clusterRadius: 80,
      clusterMinPoints: 2,
  });
}

function addPlacesLayers() {
  if (placesMap.getLayer("clusters")) return;
  placesMap.addLayer({
    id: "clusters",
    type: "circle",
    source: "places",
    filter: ["has", "point_count"],
    paint: {
      "circle-color": [
        "step",
        ["get", "point_count"],
        "#4f6bdc",
        25, "#4279f4",
        100, "#2c8cff"
      ],
      "circle-radius": ["step", ["get", "point_count"], 18, 25, 24, 100, 30],
      "circle-stroke-color": "#0b1020",
      "circle-stroke-width": 2
    }
  });
  placesMap.addLayer({
    id: "cluster-count",
    type: "symbol",
    source: "places",
    filter: ["has", "point_count"],
    layout: {
      "text-field": ["get", "point_count_abbreviated"],
      "text-size": 12
    },
    paint: { "text-color": "#ffffff" }
  });
  placesMap.addLayer({
    id: "unclustered-point",
    type: "circle",
    source: "places",
    filter: ["!has", "point_count"],
    paint: {
      "circle-color": "#7aa2ff",
      "circle-radius": 7,
      "circle-stroke-color": "#0b1020",
      "circle-stroke-width": 2
    }
  });
}

// HTML-baserede markører (små thumbs + tæller) – deaktiveret for stabilitet.
// Vi bruger i stedet MapLibres egne cluster/point-lag ovenfor.
let placesHtmlMarkers = [];
function clearPlacesMarkers() {
  for (const m of placesHtmlMarkers) {
    try { m.remove(); } catch {}
  }
  placesHtmlMarkers = [];
}

function renderPlacesMarkers() {
  if (!placesMap || !placesMap.isStyleLoaded()) return;
  const src = placesMap.getSource("places");
  if (!src) return;
  clearPlacesMarkers();

  try {
    const clusterFeats = placesMap.queryRenderedFeatures({ layers: ["clusters"] }) || [];
    for (const f of clusterFeats) {
      const cid = f && f.properties ? f.properties.cluster_id : null;
      const coords = f && f.geometry && f.geometry.coordinates ? f.geometry.coordinates : null;
      if (cid == null || !coords) continue;
      try {
        src.getClusterLeaves(cid, 1, 0, (err, leaves) => {
          const el = document.createElement("div");
          el.className = "cluster-marker";
          if (!err && leaves && leaves[0] && leaves[0].properties) {
            const thumb = leaves[0].properties.thumb || null;
            if (thumb) el.style.backgroundImage = `url(${thumb})`;
          }
          const badge = document.createElement("span");
          badge.className = "cluster-badge";
          badge.textContent = String(f.properties.point_count_abbreviated || f.properties.point_count || "");
          el.appendChild(badge);
          el.addEventListener("click", () => openClusterSheet(cid));
          const m = new maplibregl.Marker({ element: el, anchor: "center" })
            .setLngLat(coords)
            .addTo(placesMap);
          placesHtmlMarkers.push(m);
        });
      } catch {}
    }

    // Unclustered points: show small photo markers using thumbs
    const pointFeats = placesMap.queryRenderedFeatures({ layers: ["unclustered-point"] }) || [];
    for (const f of pointFeats) {
      const p = f.properties || {};
      const coords = f && f.geometry && f.geometry.coordinates ? f.geometry.coordinates : null;
      if (!coords) continue;
      const el = document.createElement("div");
      el.className = "photo-marker";
      if (p.thumb) el.style.backgroundImage = `url(${p.thumb})`;
      el.title = p.name || "";
      el.addEventListener("click", () => {
        const pid = typeof p.id === "string" ? parseInt(p.id, 10) : p.id;
        const idx = state.items.findIndex(i => i.id === pid);
        if (idx >= 0) {
          state.viewerItems = null;
          openViewer(idx);
        }
      });
      const m = new maplibregl.Marker({ element: el, anchor: "center" })
        .setLngLat(coords)
        .addTo(placesMap);
      placesHtmlMarkers.push(m);
    }
  } catch {}
}
function updateScanButton() {
  if (!SCAN_FEATURES_ENABLED || !els.scanBtn) return;
  if (state.scanning) {
    els.scanBtn.textContent = tr('btn_stop_scan');
  } else {
    els.scanBtn.textContent = tr('btn_scan_library');
  }
}

function openClusterSheet(clusterId) {
  const src = placesMap.getSource("places");
  if (!src) return;
  try {
    src.getClusterLeaves(clusterId, 100, 0, (err, leaves) => {
      const sheet = document.getElementById("clusterSheet");
      const grid = document.getElementById("clusterGrid");
      if (!sheet || !grid) return;
      grid.innerHTML = "";
      if (!err && leaves && leaves.length) {
        for (const lf of leaves) {
          const p = lf.properties || {};
          const img = document.createElement("img");
          if (p.thumb) img.src = p.thumb;
          img.title = p.name || "";
          img.addEventListener("click", () => {
            // Åbn viewer på dette billede hvis muligt
            const idx = state.items.findIndex(i => i.id === p.id);
            if (idx >= 0) {
              state.viewerItems = null;
              openViewer(idx);
            }
          });
          grid.appendChild(img);
        }
      }
      sheet.classList.remove("hidden");
    });
  } catch {}
}

// Luk sheet når man klikker på baggrund eller trykker Escape
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    const sheet = document.getElementById("clusterSheet");
    if (sheet) sheet.classList.add("hidden");
  }
});

// Luk sheet ved klik udenfor panelet
document.addEventListener("click", (e) => {
  const sheet = document.getElementById("clusterSheet");
  if (!sheet || sheet.classList.contains("hidden")) return;
  if (!sheet.contains(e.target)) {
    sheet.classList.add("hidden");
  }
});

async function pollScanStatus() {
  if (!SCAN_FEATURES_ENABLED) return;
  try {
    const res = await fetch("/api/scan/status");
    const data = await res.json();
    const running = !!(data && data.running);
    state.scanning = running;
    updateScanButton();
    if (!running) {
      showStatus(tr('scan_done_or_stopped'), "ok");
      await loadPhotos();
      return; // stop polling
    }
  } catch (_) {
    // ignore polling errors
  }
  // continue polling while scanning
  if (state.scanning) {
    setTimeout(pollScanStatus, 2000);
  }
}

async function scanLibrary() {
  if (!SCAN_FEATURES_ENABLED) {
    showStatus('Scan-funktioner er deaktiveret.', 'err');
    return;
  }
  if (state.scanning) {
    // act as stop
    try {
      const res = await fetch("/api/scan/stop", { method: "POST" });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        showStatus(tr('scan_stop_failed'), "err");
        return;
      }
      showStatus(tr('scan_stopping'), "ok");
    } catch (_) {
      showStatus(tr('scan_stop_error'), "err");
    }
    return;
  }

  // Start scan
  try {
    const res = await fetch("/api/scan", { method: "POST" });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      showStatus(`${tr('status_error_prefix')} ${data && data.error ? data.error : tr('scan_failed')}`, "err");
      return;
    }
    state.scanning = true;
    updateScanButton();
    showStatus(tr('scan_started_hint'), "ok");
    pollScanStatus();
  } catch (err) {
    showStatus(`${tr('scan_error_prefix')} ${err}`, "err");
  }
}

// Rescan metadata
async function pollRescanStatus() {
  try {
    const res = await fetch("/api/rescan/status");
    const data = await res.json();
    if (!data || !data.ok) return;
    if (!data.running) {
      if (data.result) {
        const r = data.result;
        showStatus(`${tr('rescan_done_prefix')}: ${r.scanned}, updated: ${r.updated}, missing: ${r.missing}, errors: ${r.errors}.`, "ok");
      }
      await loadPhotos();
      return;
    }
  } catch {}
  setTimeout(pollRescanStatus, 2000);
}

async function rescanMetadata() {
  try {
    els.rescanBtn.disabled = true;
    showStatus(tr('rescan_starting'), "ok");
    const res = await fetch("/api/rescan", { method: "POST" });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      showStatus(`${tr('status_error_prefix')} ${data && data.error ? data.error : tr('rescan_failed')}`, "err");
      els.rescanBtn.disabled = false;
      return;
    }
    pollRescanStatus();
  } catch (e) {
    showStatus(tr('rescan_error'), "err");
    els.rescanBtn.disabled = false;
  }
}

// Rethumb (rebuild thumbnails)
async function pollRethumbStatus() {
  try {
    const res = await fetch("/api/rethumb/status");
    const data = await res.json();
    if (!data || !data.ok) return;
    if (!data.running) {
      if (data.result) {
        const r = data.result;
        showStatus(`${tr('rethumb_done_prefix')}: ${r.processed}, errors: ${r.errors}.`, "ok");
      }
      await loadPhotos();
      return;
    }
  } catch {}
  setTimeout(pollRethumbStatus, 2000);
}

async function rethumbAll() {
  try {
    if (els.rethumbBtn) els.rethumbBtn.disabled = true;
    showStatus(tr('rethumb_starting'), "ok");
    const res = await fetch("/api/rethumb", { method: "POST" });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      showStatus(`${tr('status_error_prefix')} ${data && data.error ? data.error : tr('rethumb_failed')}`, "err");
      if (els.rethumbBtn) els.rethumbBtn.disabled = false;
      return;
    }
    pollRethumbStatus();
  } catch (e) {
    showStatus(tr('rethumb_error'), "err");
    if (els.rethumbBtn) els.rethumbBtn.disabled = false;
  }
}

async function stopAllProcesses() {
  const ok = confirm(tr('stop_all_processes_confirm'));
  if (!ok) return;
  const btn = els.stopAllProcessesBtn;
  const original = btn ? btn.textContent : tr('btn_stop_all_processes');
  try {
    if (btn) {
      btn.disabled = true;
      btn.classList.add('loading');
      btn.textContent = tr('status_stopping');
    }
    showStatus(tr('stop_all_processes_stopping'), 'ok');
    try {
      if (isUploadRunning() || uploadQueuePumpRunning) requestStopUpload();
      uploadQueue.length = 0;
    } catch {}
    const res = await fetch('/api/processes/stop-all', { method: 'POST' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || !data.ok) {
      showStatus(`${tr('stop_all_processes_failed')} ${data && data.error ? data.error : ''}`.trim(), 'err');
      return;
    }
    state.scanning = false;
    updateScanButton();
    try {
      uploadTransferActive = false;
      uploadStopRequested = false;
      uploadQueuePumpRunning = false;
      activeTusUpload = null;
      clearDirectPostprocessUploadUi();
      resetUploadUiState();
      renderUploadMonitor();
      if (els.uploadTopStatus) els.uploadTopStatus.classList.add('hidden');
    } catch {}
    if (els.rescanBtn) els.rescanBtn.disabled = false;
    if (els.rethumbBtn) els.rethumbBtn.disabled = false;
    if (els.fixThumbsBtn) els.fixThumbsBtn.disabled = false;
    showStatus(tr('stop_all_processes_done'), 'ok');
  } catch (e) {
    showStatus(tr('stop_all_processes_error'), 'err');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.classList.remove('loading');
      btn.textContent = original || tr('btn_stop_all_processes');
    }
  }
}

// Clear index (DB + thumbnails, not originals)
async function clearIndex() {
  const ok = confirm(tr('clear_confirm'));
  if (!ok) return;
  try {
    const btn = els.clearIndexBtn;
    const original = btn ? btn.textContent : tr('btn_reset_index');
    if (btn) {
      btn.disabled = true;
      btn.classList.add('loading');
      // Behold label eller brug oversat standard
      btn.textContent = original || tr('btn_reset_index');
    }
    showStatus(tr('clear_starting'), "ok");
    const res = await fetch("/api/clear", { method: "POST" });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      showStatus(`${tr('clear_failed')} ${data && data.error ? data.error : tr('clear_unknown')}`, "err");
      if (btn) {
        btn.disabled = false;
        btn.classList.remove('loading');
        btn.textContent = original || tr('btn_reset_index');
      }
      return;
    }
    const r = data.removed || {};
    showStatus(`${tr('clear_done_prefix')}: ${r.photos || 0} photos, ${r.faces || 0} faces, ${r.people || 0} people, ${r.thumbs || 0} thumbs, ${r.converted || 0} converted.`, "ok");
    // Tøm UI og hent frisk
    state.items = [];
    await loadPhotos();
  } catch (e) {
    showStatus(tr('clear_error'), "err");
  } finally {
    const btn = els.clearIndexBtn;
    if (btn) {
      btn.disabled = false;
      btn.classList.remove('loading');
      btn.textContent = btn.textContent || tr('btn_reset_index');
    }
  }
}

// Fix only missing/outdated thumbnails
async function fixMissingThumbs() {
  try {
    if (els.fixThumbsBtn) els.fixThumbsBtn.disabled = true;
    showStatus(tr('rethumb_starting'), 'ok');
    const res = await fetch('/api/rethumb/missing', { method: 'POST' });
    if (!res.ok) {
      showStatus(tr('rethumb_failed'), 'err');
      return;
    }
    // Reuse rethumb status polling (same thread/status variables)
    const poll = async () => {
      try {
        const r = await fetch('/api/rethumb/status');
        const d = await r.json();
        if (r.ok && d && d.ok) {
          if (!d.running) {
            const processed = d.result && (d.result.processed || 0);
            showStatus(`${tr('rethumb_done_prefix')} ${processed}.`, 'ok');
            await loadPhotos();
            return;
          }
        }
      } catch {}
      setTimeout(poll, 1000);
    };
    poll();
  } catch (e) {
    showStatus(tr('rethumb_error'), 'err');
  } finally {
    if (els.fixThumbsBtn) els.fixThumbsBtn.disabled = false;
  }
}
// Factory reset (DB file + all generated caches and uploads)
async function factoryReset() {
  const ok = confirm(tr('factory_confirm'));
  if (!ok) return;
  try {
    const btn = els.factoryResetBtn;
    const original = btn ? btn.textContent : tr('btn_factory_reset');
    if (btn) {
      btn.disabled = true;
      btn.classList.add('loading');
      btn.textContent = original || tr('btn_factory_reset');
    }
    showStatus(tr('factory_starting'), "ok");
    const res = await fetch('/api/factory-reset', { method: 'POST' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      showStatus(`${tr('factory_failed')} ${data && data.error ? data.error : tr('clear_unknown')}`, 'err');
      if (btn) {
        btn.disabled = false;
        btn.classList.remove('loading');
        btn.textContent = original || tr('btn_factory_reset');
      }
      return;
    }
    showStatus(tr('factory_done'), 'ok');
    // After reset, refresh UI state (empty grid etc.)
    state.items = [];
    await loadPhotos();
  } catch (e) {
    showStatus(tr('factory_error'), 'err');
  } finally {
    const btn = els.factoryResetBtn;
    if (btn) {
      btn.disabled = false;
      btn.classList.remove('loading');
      btn.textContent = btn.textContent || tr('btn_factory_reset');
    }
  }
}

async function toggleFavorite() {
  if (!state.selectedId) return;
  const selected = state.items.find(i => i.id === state.selectedId);
  if (!selected) return;

  const res = await fetch(`/api/photos/${state.selectedId}/favorite`, { method: "POST" });
  const data = await res.json();
  if (!res.ok || !data.ok) return;

  selected.favorite = !!data.favorite;
  renderGrid();
  setDetail(selected);
}

async function setView(view, opts = {}) {
  const { syncUrl = true } = opts || {};
  let nextView = APP_VIEW_KEYS.has(view) ? view : 'timeline';
  // Block settings for basic users (UI safety)
  try {
    const role = (state.currentUser && state.currentUser.role) ? String(state.currentUser.role) : 'user';
    if (nextView === 'settings' && role === 'user') nextView = 'timeline';
  } catch {}
  state.view = nextView;
  if (nextView === 'mapper') {
    state.mapperSort = _normalizeMapperSort(state.mapperSort);
  }
  const labels = navLabels();
  const [title, subtitle] = labels[nextView] || ['FjordLens', ''];
  if (els.viewTitle) els.viewTitle.textContent = title;
  if (els.viewSubtitle) els.viewSubtitle.textContent = subtitle;
  if (nextView !== 'mapper') _stopMapperDragSelectSession();
  if (nextView !== 'mapper') state.mapperPath = _normalizeMapperPath(state.mapperPath);
  state.folder = (nextView === 'mapper' ? (_normalizeMapperPath(state.mapperPath) || null) : null);
  state.selectedId = null;
  document.querySelectorAll(".nav-item").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.view === nextView);
  });
  updateMobileBottomNavActive(nextView);
  // Toggle body class to drive CSS for Settings view
  document.body.classList.toggle("view-settings", nextView === "settings");
  document.body.classList.toggle("view-timeline", nextView === "timeline");
  document.body.classList.toggle("view-favorites", nextView === "favorites");
  document.body.classList.toggle("view-steder", nextView === "steder");
  document.body.classList.toggle("view-kameraer", nextView === "kameraer");
  document.body.classList.toggle("view-personer", nextView === "personer");
  document.body.classList.toggle("view-mapper", nextView === "mapper");
  document.body.classList.toggle("view-photoframe", nextView === "photoframe");
  placeGlobalSearchSortForView();
  // Toggle compact Settings layout on small viewports
  try {
    const isSmall = window.matchMedia('(max-width: 760px)').matches;
    document.body.classList.toggle('compact-settings', nextView === 'settings' && isSmall);
  } catch {}
  if (nextView !== 'mapper') closeMapperHeaderMenu();
  if (nextView !== 'mapper' && els.mapperTreeNav) {
    if (els.mapperNavMenu) els.mapperNavMenu.classList.add('hidden');
    els.mapperTreeNav.classList.add('hidden');
  }
  if (nextView === 'photoframe') startPhotoframeStatusPolling();
  else stopPhotoframeStatusPolling();
  if (nextView !== 'settings') stopAppUpdateStatusPolling();
  if (syncUrl) _syncRouteStateToUrl();

  if (nextView === "settings") {
    // show logs panel, do not load photos
    renderGrid();
    const activeTab = _activeSettingsTabFromUi();
    const desiredTab = _normalizeSettingsTab(state.settingsTab) || activeTab || 'maint';
    if (desiredTab && desiredTab !== activeTab) {
      activateSettingsTab(desiredTab);
    }
    state.settingsTab = _activeSettingsTabFromUi() || desiredTab;
    if (syncUrl) _syncRouteStateToUrl();
    loadAppUpdateStatus({ silent: true }).catch(() => {});
  } else if (nextView === 'photoframe') {
    state.items = [];
    if (!Array.isArray(state.photoframeItems)) state.photoframeItems = [];
    renderGrid();
    await loadPhotoframeStatus();
  } else if (nextView === 'personer') {
    state.personView = { mode: 'list', personId: null, personName: null };
    await loadPeople();
  } else {
    if (nextView === 'mapper') await loadMapperTools(String(state.mapperPath || ''));
    await loadPhotos();
    if (nextView === 'mapper') checkMapperDiskSyncNow().catch(() => {});
  }
}

function updateMobileBottomNavActive(view) {
  document.querySelectorAll('.mobile-nav-item[data-view]').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.view === view);
  });
}

function applyUiLanguage() {
  try { document.documentElement.lang = state.uiLanguage || 'da'; } catch {}
  if (els.search) els.search.placeholder = tr('search_placeholder');
  if (els.mapperSearchInput) els.mapperSearchInput.placeholder = tr('search_placeholder');

  if (els.sort) {
    const sortTexts = {
      date_desc: tr('sort_date_desc'),
      date_asc: tr('sort_date_asc'),
      name_asc: tr('sort_name_asc'),
      name_desc: tr('sort_name_desc'),
      size_desc: tr('sort_size_desc'),
      size_asc: tr('sort_size_asc'),
    };
    Object.entries(sortTexts).forEach(([val, text]) => {
      const opt = els.sort.querySelector(`option[value="${val}"]`);
      if (opt) opt.textContent = text;
    });
  }
  if (els.mapperSortSelect) {
    const descOpt = els.mapperSortSelect.querySelector('option[value="date_desc"]');
    const ascOpt = els.mapperSortSelect.querySelector('option[value="date_asc"]');
    if (descOpt) descOpt.textContent = tr('sort_date_desc');
    if (ascOpt) ascOpt.textContent = tr('sort_date_asc');
  }
  

  if (els.mapperSortSelect) {
    const descOpt = els.mapperSortSelect.querySelector('option[value="date_desc"]');
    const ascOpt = els.mapperSortSelect.querySelector('option[value="date_asc"]');
    if (descOpt) descOpt.textContent = tr('sort_date_desc');
    if (ascOpt) ascOpt.textContent = tr('sort_date_asc');
    if (els.mapperSortSelect.value !== mapperSortMode) {
      els.mapperSortSelect.value = mapperSortMode;
    }
    els.mapperSortSelect.disabled = !!state.mapperEditMode;
  }
  const navMap = {
    timeline: tr('nav_timeline'),
    favorites: tr('nav_favorites'),
    steder: tr('nav_places'),
    kameraer: tr('nav_cameras'),
    mapper: tr('nav_folders'),
    photoframe: tr('nav_photoframe'),
    personer: tr('nav_people'),
    settings: tr('nav_settings'),
  };
  Object.entries(navMap).forEach(([view, text]) => {
    const el = document.querySelector(`.nav-item[data-view="${view}"]`);
    if (el) el.textContent = text;
  });

  if (els.profileLink) els.profileLink.textContent = tr('profile_link');
  const logoutLink = document.querySelector('.sidebar-footer a[href="/logout"]');
  if (logoutLink) logoutLink.textContent = tr('logout_link');
  if (els.similarPhashDistanceLabel) els.similarPhashDistanceLabel.textContent = tr('similar_phash_label');
  if (els.similarDhashDistanceLabel) els.similarDhashDistanceLabel.textContent = tr('similar_dhash_label');
  if (els.similarAhashDistanceLabel) els.similarAhashDistanceLabel.textContent = tr('similar_ahash_label');
  if (els.similarDistanceApply) els.similarDistanceApply.textContent = tr('similar_distance_find');
  if (els.similarSourceLabel) els.similarSourceLabel.textContent = tr('similar_source_label');
  if (els.similarAiMinLabel) els.similarAiMinLabel.textContent = tr('similar_ai_min_label');
  if (els.similarMethodLabel) els.similarMethodLabel.textContent = tr('similar_method_label');
  if (els.similarMethodSelect) {
    const methodLabels = {
      hash: tr('similar_method_hash'),
      ai: tr('similar_method_ai'),
      hybrid: tr('similar_method_hybrid'),
    };
    Object.entries(methodLabels).forEach(([value, text]) => {
      const opt = els.similarMethodSelect.querySelector(`option[value="${value}"]`);
      if (opt) opt.textContent = text;
    });
  }

  const tabText = {
    maint: tr('tab_maint'),
    update: tr('tab_update'),
    ai: tr('tab_ai'),
    upload_workflow: tr('tab_upload_workflow'),
    file_types: tr('tab_file_types'),
    hardware: tr('tab_hardware'),
    heic: tr('tab_heic'),
    dns: tr('tab_dns'),
    shared: tr('tab_shared'),
    logs: tr('tab_logs'),
    users: tr('tab_users'),
    profile: tr('tab_profile'),
    other: tr('tab_other'),
  };
  Object.entries(tabText).forEach(([tab, text]) => {
    const btn = document.querySelector(`#settingsPanel .tab-btn[data-tab="${tab}"]`);
    if (btn) btn.textContent = text;
  });
  Object.entries(tabText).forEach(([tab, text]) => {
    const opt = document.querySelector(`#settingsTabSelect option[value="${tab}"]`);
    if (opt) opt.textContent = text;
  });
  renderAppUpdateTabBadge(state.appUpdate || {});

  const settingsHeaderTitle = document.querySelector('#settingsPanel .settings-header h1');
  const settingsHeaderSub = document.querySelector('#settingsPanel .settings-header p');
  if (settingsHeaderTitle) settingsHeaderTitle.textContent = tr('settings_title');
  if (settingsHeaderSub) settingsHeaderSub.textContent = tr('settings_sub');

  const maintTitle = document.querySelector('#settingsPanel .tab-panel[data-tabpanel="maint"] .sidebar-card-title');
  if (maintTitle) maintTitle.textContent = tr('maint_title');
  if (els.appUpdateTitle) els.appUpdateTitle.textContent = tr('app_update_title');
  if (els.appUpdateBranchLabel) els.appUpdateBranchLabel.textContent = tr('app_update_branch');
  if (els.appUpdateCurrentLabel) els.appUpdateCurrentLabel.textContent = tr('app_update_current');
  if (els.appUpdateRemoteLabel) els.appUpdateRemoteLabel.textContent = tr('app_update_remote');
  if (els.appUpdateStateLabel) els.appUpdateStateLabel.textContent = tr('app_update_state');
  if (els.appUpdateAutoCheckText) els.appUpdateAutoCheckText.textContent = tr('app_update_auto_check');
  if (els.appUpdateIntervalLabel) els.appUpdateIntervalLabel.textContent = tr('app_update_interval');
  if (els.appUpdateSettingsSaveBtn && !els.appUpdateSettingsSaveBtn.classList.contains('loading')) els.appUpdateSettingsSaveBtn.textContent = tr('app_update_save_settings');
  if (els.appUpdateCheckBtn && !els.appUpdateCheckBtn.classList.contains('loading')) els.appUpdateCheckBtn.textContent = tr('app_update_check');
  if (els.appUpdateStartBtn && !els.appUpdateStartBtn.classList.contains('loading')) els.appUpdateStartBtn.textContent = tr('app_update_start');
  if (els.appUpdateChoiceTitle) els.appUpdateChoiceTitle.textContent = tr('app_update_choice_title');
  if (els.appUpdateChoiceText) els.appUpdateChoiceText.textContent = tr('app_update_choice_text');
  if (els.appUpdateChoiceClose) els.appUpdateChoiceClose.setAttribute('aria-label', tr('app_update_choice_close'));
  if (els.appUpdateChoiceCleanupBtn) els.appUpdateChoiceCleanupBtn.textContent = tr('app_update_choice_cleanup');
  if (els.appUpdateChoiceFastBtn) els.appUpdateChoiceFastBtn.textContent = tr('app_update_choice_fast');
  if (els.aiPanelTitle) els.aiPanelTitle.textContent = tr('ai_panel_title');
    // HEIC tab labels stay Danish/English defaults already in markup
  if (els.aiEmbedTitle) els.aiEmbedTitle.textContent = tr('ai_embed_title');
  if (els.aiEmbedDesc) els.aiEmbedDesc.textContent = tr('ai_embed_desc');
  if (els.aiDescTitle) els.aiDescTitle.textContent = tr('ai_desc_title');
  if (els.aiDescDesc) els.aiDescDesc.textContent = tr('ai_desc_desc');
  if (els.aiDescModelLabel) els.aiDescModelLabel.textContent = tr('ai_desc_model_label');
  if (els.aiDescExternalToggleText) els.aiDescExternalToggleText.textContent = tr('ai_desc_external_toggle');
  if (els.aiDescExternalChooseBtn) els.aiDescExternalChooseBtn.textContent = tr('ai_desc_external_choose');
  if (els.aiDescribeClearBtn) els.aiDescribeClearBtn.textContent = tr('btn_clear_ai_desc');
  if (els.aiExternalModalTitle) els.aiExternalModalTitle.textContent = tr('ai_desc_external_modal_title');
  if (els.aiExternalModalText) els.aiExternalModalText.textContent = tr('ai_desc_external_modal_text');
  const aiExternalTokenLabel = document.getElementById('aiExternalTokenLabel');
  if (aiExternalTokenLabel) aiExternalTokenLabel.textContent = tr('ai_desc_external_token_label');
  if (els.aiExternalCopyTokenBtn) els.aiExternalCopyTokenBtn.textContent = (resolveUiLanguage(state.uiLanguage || 'da') === 'en') ? 'Copy link' : 'Kopiér link';
  if (els.aiExternalLinksBtn) els.aiExternalLinksBtn.textContent = tr('ai_desc_external_links');
  if (els.aiExternalRotateTokenBtn) els.aiExternalRotateTokenBtn.textContent = tr('ai_desc_external_rotate');
  if (els.aiExternalModalSave) els.aiExternalModalSave.textContent = tr('ai_desc_external_save');
  if (els.aiExternalModalCancel) els.aiExternalModalCancel.textContent = tr('scan_modal_cancel');
  if (els.aiExternalModalClose) els.aiExternalModalClose.textContent = tr('scan_modal_close');
  if (els.aiExternalLinksModalTitle) els.aiExternalLinksModalTitle.textContent = tr('ai_desc_external_links_title');
  if (els.aiExternalLinksModalText) els.aiExternalLinksModalText.textContent = tr('ai_desc_external_links_text');
  if (els.aiExternalLinksModalClose) els.aiExternalLinksModalClose.textContent = tr('scan_modal_close');
  if (els.aiExternalLinksModalDone) els.aiExternalLinksModalDone.textContent = (resolveUiLanguage(state.uiLanguage || 'da') === 'en') ? 'Done' : 'Færdig';
  if (els.aiDescribeForceStopBtn) els.aiDescribeForceStopBtn.textContent = tr('btn_force_stop_qwen');
  if (els.aiDescribeModelSelect) {
    const lightOpt = els.aiDescribeModelSelect.querySelector('option[value="light"]');
    const qwenOpt = els.aiDescribeModelSelect.querySelector('option[value="qwen"]');
    if (lightOpt) lightOpt.textContent = tr('ai_desc_model_light');
    if (qwenOpt) qwenOpt.textContent = tr('ai_desc_model_qwen');
  }
  updateAiDescribeModelSelect();
  if (els.aiFacesTitle) els.aiFacesTitle.textContent = tr('ai_faces_title');
  if (els.aiFacesDesc) els.aiFacesDesc.textContent = tr('ai_faces_desc');
  if (els.uploadWorkflowTitle) els.uploadWorkflowTitle.textContent = tr('upload_workflow_title');
  if (els.uploadWorkflowDesc) els.uploadWorkflowDesc.textContent = tr('upload_workflow_desc');
  if (els.uploadWorkflowGentleTitle) els.uploadWorkflowGentleTitle.textContent = tr('upload_workflow_gentle_title');
  if (els.uploadWorkflowGentleDesc) els.uploadWorkflowGentleDesc.textContent = tr('upload_workflow_gentle_desc');
  if (els.uploadWorkflowAggressiveTitle) els.uploadWorkflowAggressiveTitle.textContent = tr('upload_workflow_aggressive_title');
  if (els.uploadWorkflowAggressiveDesc) els.uploadWorkflowAggressiveDesc.textContent = tr('upload_workflow_aggressive_desc');
  if (els.uploadWorkflowSaveBtn && !els.uploadWorkflowSaveBtn.classList.contains('loading')) {
    els.uploadWorkflowSaveBtn.textContent = tr('upload_workflow_save');
  }
  if (els.uploadWorkflowExtraInfo) {
    const runtimeText = state.uploadWorkflowThumbnailsUseGpu ? tr('status_runtime_gpu') : tr('status_runtime_cpu');
    els.uploadWorkflowExtraInfo.textContent = tr('upload_workflow_extra_info')
      .replace('{thumb_runtime}', runtimeText)
      .replace('{batch_size}', String(state.uploadWorkflowBatchSize || 10));
  }
  if (els.fileTypesTitle) els.fileTypesTitle.textContent = tr('file_types_title');
  if (els.fileTypesDesc) els.fileTypesDesc.textContent = tr('file_types_desc');
  if (els.fileTypeInput) els.fileTypeInput.placeholder = '.png';
  if (els.fileTypeAddBtn) els.fileTypeAddBtn.textContent = tr('file_types_add');
  if (els.fileTypeResetBtn) els.fileTypeResetBtn.textContent = tr('file_types_reset');
  if (els.fileTypeSaveBtn && !els.fileTypeSaveBtn.classList.contains('loading')) els.fileTypeSaveBtn.textContent = tr('file_types_save');
  if (els.fileTypeBlockedTitle) els.fileTypeBlockedTitle.textContent = tr('file_types_blocked_title');
  if (els.fileTypeBlockedDesc) els.fileTypeBlockedDesc.textContent = tr('file_types_blocked_desc');
  if (state.uploadFileTypes) renderUploadFileTypeSettings();
  updateRuntimeIndicator(els.aiEmbedRuntime, state.aiRuntime);
  updateRuntimeIndicator(els.aiDescribeRuntime, state.aiDescribeRuntime);
  updateRuntimeIndicator(els.aiFacesRuntime, state.facesRuntime);
  if (els.dnsPanelTitle) els.dnsPanelTitle.textContent = tr('dns_title');
  if (els.dnsPanelDesc) els.dnsPanelDesc.textContent = tr('dns_desc');
  if (els.dnsDuckdnsBaseUrlLabel) els.dnsDuckdnsBaseUrlLabel.textContent = tr('dns_duckdns_base_url');
  if (els.dnsDuckdnsBaseUrlInput) els.dnsDuckdnsBaseUrlInput.placeholder = tr('dns_duckdns_placeholder');
  if (els.dnsSaveBtn) els.dnsSaveBtn.textContent = tr('dns_save');
  if (els.sharedLinksTitle) els.sharedLinksTitle.textContent = tr('dns_shares_title');
  if (els.sharedLinksDesc) els.sharedLinksDesc.textContent = tr('dns_shares_desc');
  if (els.sharedLinksList && Array.isArray(state.sharedLinks) && state.sharedLinks.length) renderDnsSharesList();
  if (els.sharedEditModalTitle) els.sharedEditModalTitle.textContent = tr('dns_shares_edit_title');
  if (els.sharedEditModalClose) els.sharedEditModalClose.textContent = tr('scan_modal_close');
  if (els.sharedEditModalCancel) els.sharedEditModalCancel.textContent = tr('scan_modal_cancel');
  if (els.sharedEditModalSave && !els.sharedEditModalSave.classList.contains('loading')) {
    els.sharedEditModalSave.textContent = tr('dns_shares_edit_save');
  }
  if (els.sharedEditNameLabel) els.sharedEditNameLabel.textContent = tr('dns_shares_edit_name_label');
  if (els.sharedEditNameInput) els.sharedEditNameInput.placeholder = tr('mapper_share_name_placeholder');
  if (els.sharedEditFoldersLabel) els.sharedEditFoldersLabel.textContent = tr('dns_shares_edit_folders_label');
  if (els.sharedEditExpireValueLabel) els.sharedEditExpireValueLabel.textContent = tr('dns_shares_edit_expire_value');
  if (els.sharedEditExpireUnitLabel) els.sharedEditExpireUnitLabel.textContent = tr('dns_shares_edit_expire_unit');
  if (els.sharedEditNeverToggleText) els.sharedEditNeverToggleText.textContent = tr('dns_shares_edit_never');
  if (els.sharedEditPermissionLabel) els.sharedEditPermissionLabel.textContent = tr('dns_shares_edit_permission');
  if (els.sharedEditDuckdnsToggleText) els.sharedEditDuckdnsToggleText.textContent = tr('mapper_share_duckdns_toggle');
  if (els.sharedEditPasswordToggleText) els.sharedEditPasswordToggleText.textContent = tr('dns_shares_edit_password_toggle');
  if (els.sharedEditPasswordLabel) els.sharedEditPasswordLabel.textContent = tr('dns_shares_edit_password_label');
  if (els.sharedEditPasswordInput) els.sharedEditPasswordInput.placeholder = tr('dns_shares_edit_password_placeholder');
  if (els.sharedEditRequireNameToggleText) els.sharedEditRequireNameToggleText.textContent = tr('dns_shares_edit_require_name');
  if (els.sharedEditExpireUnit) {
    const dayOpt = els.sharedEditExpireUnit.querySelector('option[value="days"]');
    const hourOpt = els.sharedEditExpireUnit.querySelector('option[value="hours"]');
    if (dayOpt) dayOpt.textContent = tr('mapper_share_expire_days');
    if (hourOpt) hourOpt.textContent = tr('mapper_share_expire_hours');
  }
  if (els.sharedEditPermission) {
    const viewOpt = els.sharedEditPermission.querySelector('option[value="view"]');
    const uploadOpt = els.sharedEditPermission.querySelector('option[value="upload"]');
    const manageOpt = els.sharedEditPermission.querySelector('option[value="manage"]');
    if (viewOpt) viewOpt.textContent = tr('mapper_share_perm_view');
    if (uploadOpt) uploadOpt.textContent = tr('mapper_share_perm_upload');
    if (manageOpt) manageOpt.textContent = tr('mapper_share_perm_manage');
  }

  if (els.scanBtn) els.scanBtn.textContent = tr('btn_scan_library');
  if (els.rescanBtn) els.rescanBtn.textContent = tr('btn_rescan_metadata');
  if (els.rethumbBtn) els.rethumbBtn.textContent = tr('btn_rebuild_thumbs');
  if (els.fixThumbsBtn) els.fixThumbsBtn.textContent = tr('btn_fix_missing_thumbs');
  if (els.stopAllProcessesBtn) els.stopAllProcessesBtn.textContent = tr('btn_stop_all_processes');
  if (els.clearIndexBtn) els.clearIndexBtn.textContent = tr('btn_reset_index');
  if (els.factoryResetBtn) els.factoryResetBtn.textContent = tr('btn_factory_reset');
  updateAiToggleButton();
  updateAiDescribeToggleButton();
  updateFacesToggleButton();

  const logsLabel = document.querySelector('#logsPanel strong');
  if (logsLabel) logsLabel.textContent = tr('logs_label');
  if (els.logsStart) els.logsStart.textContent = state.logsRunning ? tr('btn_stop') : tr('btn_start');
  if (els.mainLogsClear) els.mainLogsClear.textContent = tr('btn_clear');

  const profileModalTitle = document.querySelector('#profileModal h3');
  if (profileModalTitle) profileModalTitle.textContent = tr('profile_title');
  if (els.profileModalClose) els.profileModalClose.textContent = tr('profile_close');
  const twofaModalTitle = document.getElementById('twofaModalTitle');
  if (twofaModalTitle) twofaModalTitle.textContent = tr('tab_twofa');
  if (els.twofaModalClose) els.twofaModalClose.textContent = tr('profile_close');

  const scanModalTitle = document.getElementById('scanModalTitle');
  const scanModalText = document.getElementById('scanModalText');
  if (scanModalTitle) scanModalTitle.textContent = tr('scan_modal_title');
  if (scanModalText) scanModalText.textContent = tr('scan_modal_text');
  if (els.scanModalClose) els.scanModalClose.textContent = tr('scan_modal_close');
  if (els.scanModalCancel) els.scanModalCancel.textContent = tr('scan_modal_cancel');
  if (els.scanModalStart) els.scanModalStart.textContent = tr('scan_modal_start');
  applyMapperFolderModalTexts();
  if (els.mapperShareModalTitle) els.mapperShareModalTitle.textContent = tr('mapper_share_title');
  if (els.mapperShareModalClose) els.mapperShareModalClose.textContent = tr('scan_modal_close');
  if (els.mapperShareModalCancel) els.mapperShareModalCancel.textContent = tr('scan_modal_cancel');
  if (els.mapperShareModalConfirm) els.mapperShareModalConfirm.textContent = tr('mapper_share_generate');
  if (els.mapperShareNameLabel) els.mapperShareNameLabel.textContent = tr('mapper_share_name_label');
  if (els.mapperShareNameInput) els.mapperShareNameInput.placeholder = tr('mapper_share_name_placeholder');
  if (els.mapperShareFolderLabel) els.mapperShareFolderLabel.textContent = tr('mapper_share_folder_label');
  if (els.mapperShareExpireLabel) els.mapperShareExpireLabel.textContent = tr('mapper_share_expire_label');
  if (els.mapperShareExpireUnitLabel) els.mapperShareExpireUnitLabel.textContent = tr('mapper_share_expire_unit_label');
  if (els.mapperSharePermissionLabel) els.mapperSharePermissionLabel.textContent = tr('mapper_share_permission_label');
  if (els.mapperShareDuckdnsToggleText) els.mapperShareDuckdnsToggleText.textContent = tr('mapper_share_duckdns_toggle');
  if (els.mapperSharePasswordToggleText) els.mapperSharePasswordToggleText.textContent = tr('mapper_share_password_toggle');
  if (els.mapperShareRequireNameToggleText) els.mapperShareRequireNameToggleText.textContent = tr('mapper_share_require_name_toggle');
  if (els.mapperSharePasswordLabel) els.mapperSharePasswordLabel.textContent = tr('mapper_share_password_label');
  if (els.mapperSharePasswordInput) els.mapperSharePasswordInput.placeholder = tr('mapper_share_password_placeholder');
  if (els.mapperShareResultLabel) els.mapperShareResultLabel.textContent = tr('mapper_share_result_label');
  if (els.mapperShareCopyBtn) els.mapperShareCopyBtn.textContent = tr('mapper_share_copy');
  if (els.mapperShareExpireUnit) {
    const dayOpt = els.mapperShareExpireUnit.querySelector('option[value="days"]');
    const hourOpt = els.mapperShareExpireUnit.querySelector('option[value="hours"]');
    if (dayOpt) dayOpt.textContent = tr('mapper_share_expire_days');
    if (hourOpt) hourOpt.textContent = tr('mapper_share_expire_hours');
  }
  if (els.mapperSharePermission) {
    const viewOpt = els.mapperSharePermission.querySelector('option[value="view"]');
    const uploadOpt = els.mapperSharePermission.querySelector('option[value="upload"]');
    const manageOpt = els.mapperSharePermission.querySelector('option[value="manage"]');
    if (viewOpt) viewOpt.textContent = tr('mapper_share_perm_view');
    if (uploadOpt) uploadOpt.textContent = tr('mapper_share_perm_upload');
    if (manageOpt) manageOpt.textContent = tr('mapper_share_perm_manage');
  }
  if (els.aiScopeModalText) els.aiScopeModalText.textContent = tr('ai_scope_text');
  if (els.aiScopeModalCancel) els.aiScopeModalCancel.textContent = tr('ai_scope_cancel');
  if (els.aiScopeModalClose) els.aiScopeModalClose.textContent = tr('scan_modal_close');
  if (els.aiScopeModalNew) els.aiScopeModalNew.textContent = tr('ai_scope_new');
  if (els.aiScopeModalAll) els.aiScopeModalAll.textContent = tr('ai_scope_all');
  if (els.aiScopeModalTitle) {
    const feature = state.aiScopePendingFeature;
    if (feature === 'faces') els.aiScopeModalTitle.textContent = tr('ai_scope_title_faces');
    else if (feature === 'describe_model') els.aiScopeModalTitle.textContent = tr('ai_scope_title_desc_model');
    else if (feature === 'describe') els.aiScopeModalTitle.textContent = tr('ai_scope_title_desc');
    else els.aiScopeModalTitle.textContent = tr('ai_scope_title_ai');
  }
  updateConversionScopeModalText();

  const labels = navLabels();
  const [title, subtitle] = labels[state.view] || ['FjordLens', ''];
  if (els.viewTitle) els.viewTitle.textContent = title;
  if (els.viewSubtitle) els.viewSubtitle.textContent = subtitle;
}

function activateSettingsTab(tab) {
  const safeTab = _normalizeSettingsTab(tab);
  if (!safeTab) return;
  const btn = document.querySelector(`#settingsPanel .tab-btn[data-tab="${safeTab}"]`);
  if (btn) btn.click();
}

function openProfileModal() {
  if (!els.profileModal) return;
  els.profileModal.classList.remove('hidden');
}

function closeProfileModal() {
  if (!els.profileModal) return;
  els.profileModal.classList.add('hidden');
}

function openTwofaModal() {
  if (!els.twofaModal) return;
  els.twofaModal.classList.remove('hidden');
}

function closeTwofaModal() {
  if (!els.twofaModal) return;
  els.twofaModal.classList.add('hidden');
}

function openMapperCreateModal() {
  if (!els.mapperCreateModal) return;
  state.mapperFolderModalMode = 'create';
  state.mapperRenameTargetPath = '';
  if (els.mapperCreateModalInput) els.mapperCreateModalInput.value = '';
  applyMapperFolderModalTexts();
  els.mapperCreateModal.classList.remove('hidden');
  if (els.mapperCreateModalInput) {
    requestAnimationFrame(() => {
      try {
        els.mapperCreateModalInput.focus();
        const len = String(els.mapperCreateModalInput.value || '').length;
        els.mapperCreateModalInput.setSelectionRange(len, len);
      } catch {}
    });
  }
}

function openMapperRenameModal(folderPath) {
  const target = _normalizeMapperPath(folderPath || '');
  if (!target) {
    showStatus(tr('mapper_rename_root_block'), 'err');
    return;
  }
  state.mapperFolderModalMode = 'rename';
  state.mapperRenameTargetPath = target;
  const currentName = target.includes('/') ? target.split('/').pop() : target;
  if (els.mapperCreateModalInput) {
    els.mapperCreateModalInput.value = String(currentName || '');
  }
  applyMapperFolderModalTexts();
  if (!els.mapperCreateModal) return;
  els.mapperCreateModal.classList.remove('hidden');
  if (els.mapperCreateModalInput) {
    requestAnimationFrame(() => {
      try {
        els.mapperCreateModalInput.focus();
        const len = String(els.mapperCreateModalInput.value || '').length;
        els.mapperCreateModalInput.setSelectionRange(0, len);
      } catch {}
    });
  }
}

function applyMapperFolderModalTexts() {
  const isRename = String(state.mapperFolderModalMode || 'create') === 'rename';
  if (els.mapperCreateModalTitle) {
    els.mapperCreateModalTitle.textContent = isRename ? tr('mapper_rename_modal_title') : tr('mapper_create_modal_title');
  }
  if (els.mapperCreateModalClose) els.mapperCreateModalClose.textContent = tr('scan_modal_close');
  if (els.mapperCreateModalCancel) els.mapperCreateModalCancel.textContent = tr('scan_modal_cancel');
  if (els.mapperCreateModalConfirm) {
    els.mapperCreateModalConfirm.disabled = false;
    els.mapperCreateModalConfirm.classList.remove('loading');
    els.mapperCreateModalConfirm.textContent = isRename ? tr('mapper_rename_action') : tr('upload_create_folder');
  }
  if (els.mapperCreateModalInput) {
    els.mapperCreateModalInput.placeholder = isRename ? tr('mapper_rename_placeholder') : tr('upload_new_folder_placeholder');
  }
}

function closeMapperCreateModal(clearInput = true) {
  if (!els.mapperCreateModal) return;
  els.mapperCreateModal.classList.add('hidden');
  if (clearInput && els.mapperCreateModalInput) {
    els.mapperCreateModalInput.value = '';
  }
  state.mapperFolderModalMode = 'create';
  state.mapperRenameTargetPath = '';
}

async function submitMapperFolderModal() {
  if (String(state.mapperFolderModalMode || 'create') === 'rename') {
    await renameMapperFolder();
    return;
  }
  await createMapperFolder();
}

function _getSelectedMapperFolders() {
  return Array.from(state.mapperSelectedFolders || [])
    .map((v) => String(v || '').trim())
    .filter((v) => !!v);
}

function _defaultMapperShareName(folders) {
  const list = Array.isArray(folders) ? folders.filter(Boolean) : [];
  if (!list.length) return '';
  if (list.length === 1) return `uploads/${list[0]}`;
  return `${list.length} mapper`;
}

function _selectedMapperFoldersText(folders) {
  const list = Array.isArray(folders) ? folders.filter(Boolean) : [];
  if (!list.length) return '';
  const labels = list.map((f) => `uploads/${f}`);
  if (labels.length <= 3) return labels.join(', ');
  return `${labels.slice(0, 3).join(', ')} (+${labels.length - 3})`;
}

function _syncMapperSharePasswordVisibility() {
  const enabled = !!(els.mapperSharePasswordToggle && els.mapperSharePasswordToggle.checked);
  if (els.mapperSharePasswordWrap) els.mapperSharePasswordWrap.classList.toggle('hidden', !enabled);
  if (!enabled && els.mapperSharePasswordInput) els.mapperSharePasswordInput.value = '';
}

async function refreshShareDuckdnsConfig() {
  try {
    const res = await fetch('/api/settings/dns/effective');
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || !data.ok) {
      state.shareDuckdnsConfigured = false;
      state.shareDuckdnsEffectiveBaseUrl = '';
      return;
    }
    state.shareDuckdnsConfigured = !!data.duckdns_configured;
    state.shareDuckdnsEffectiveBaseUrl = String(data.effective_duckdns_base_url || '');
  } catch {
    state.shareDuckdnsConfigured = false;
    state.shareDuckdnsEffectiveBaseUrl = '';
  }
}

async function openMapperShareModal() {
  if (!els.mapperShareModal) return;
  const folders = _getSelectedMapperFolders();
  if (!folders.length) {
    showStatus(tr('mapper_share_select_one'), 'err');
    return;
  }
  await refreshShareDuckdnsConfig();
  applyUiLanguage();
  if (els.mapperShareNameInput) els.mapperShareNameInput.value = _defaultMapperShareName(folders);
  if (els.mapperShareFolderInput) els.mapperShareFolderInput.value = _selectedMapperFoldersText(folders);
  if (els.mapperShareExpireValue) els.mapperShareExpireValue.value = '7';
  if (els.mapperShareExpireUnit) els.mapperShareExpireUnit.value = 'days';
  if (els.mapperSharePermission) els.mapperSharePermission.value = 'view';
  if (els.mapperShareDuckdnsToggle) {
    const enabled = !!state.shareDuckdnsConfigured;
    els.mapperShareDuckdnsToggle.checked = enabled;
    els.mapperShareDuckdnsToggle.disabled = !enabled;
    els.mapperShareDuckdnsToggle.title = enabled ? '' : tr('mapper_share_duckdns_not_configured');
  }
  if (els.mapperSharePasswordToggle) els.mapperSharePasswordToggle.checked = false;
  if (els.mapperShareRequireNameToggle) els.mapperShareRequireNameToggle.checked = false;
  _syncMapperSharePasswordVisibility();
  if (els.mapperShareResultWrap) els.mapperShareResultWrap.classList.add('hidden');
  if (els.mapperShareResultInput) els.mapperShareResultInput.value = '';
  const qrWrap = document.getElementById('mapperShareQrWrap');
  const qrImg = document.getElementById('mapperShareQrImg');
  if (qrWrap) qrWrap.classList.add('hidden');
  if (qrImg) qrImg.removeAttribute('src');
  const errEl = document.getElementById('mapperShareError');
  if (errEl) { errEl.classList.add('hidden'); errEl.textContent = ''; }
  if (els.mapperShareModalConfirm) {
    els.mapperShareModalConfirm.disabled = false;
    els.mapperShareModalConfirm.classList.remove('loading');
    els.mapperShareModalConfirm.textContent = tr('mapper_share_generate');
  }
  els.mapperShareModal.classList.remove('hidden');
}

function closeMapperShareModal(clearOutput = true) {
  if (!els.mapperShareModal) return;
  els.mapperShareModal.classList.add('hidden');
  if (clearOutput) {
    if (els.mapperShareResultWrap) els.mapperShareResultWrap.classList.add('hidden');
    if (els.mapperShareResultInput) els.mapperShareResultInput.value = '';
  }
}

async function createMapperShareLink() {
  const folders = _getSelectedMapperFolders();
  if (!folders.length) {
    showStatus(tr('mapper_share_select_one'), 'err');
    return;
  }
  const confirmBtn = els.mapperShareModalConfirm;
  const original = confirmBtn ? confirmBtn.textContent : tr('mapper_share_generate');
  const useDuckdns = !!(els.mapperShareDuckdnsToggle && els.mapperShareDuckdnsToggle.checked);
  const passwordEnabled = !!(els.mapperSharePasswordToggle && els.mapperSharePasswordToggle.checked);
  const requireVisitorName = !!(els.mapperShareRequireNameToggle && els.mapperShareRequireNameToggle.checked);
  const password = String((els.mapperSharePasswordInput && els.mapperSharePasswordInput.value) || '');
  if (passwordEnabled && password.length < 4) {
    showStatus(tr('mapper_share_password_placeholder'), 'err');
    const errEl = document.getElementById('mapperShareError');
    if (errEl) { errEl.textContent = tr('mapper_share_password_placeholder'); errEl.classList.remove('hidden'); }
    return;
  }
  try {
    if (confirmBtn) {
      confirmBtn.disabled = true;
      confirmBtn.classList.add('loading');
      confirmBtn.textContent = tr('mapper_share_generating');
    }
    const expiresRaw = String((els.mapperShareExpireValue && els.mapperShareExpireValue.value) || '').trim();
    let expiresValue = 0;
    if (expiresRaw) {
      const parsedExpires = Number(expiresRaw);
      if (!Number.isFinite(parsedExpires) || parsedExpires < 0) {
        const message = tr('dns_shares_edit_invalid_expiry');
        showStatus(message, 'err');
        const errEl = document.getElementById('mapperShareError');
        if (errEl) { errEl.textContent = message; errEl.classList.remove('hidden'); }
        return;
      }
      expiresValue = Math.floor(parsedExpires);
    }
    const expiresUnit = String((els.mapperShareExpireUnit && els.mapperShareExpireUnit.value) || 'days');
    const permission = String((els.mapperSharePermission && els.mapperSharePermission.value) || 'view');
    const shareNameRaw = String((els.mapperShareNameInput && els.mapperShareNameInput.value) || '').trim();
    const shareName = shareNameRaw || _defaultMapperShareName(folders);
    const res = await fetch('/api/shares', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        folder_paths: folders,
        share_name: shareName,
        permission,
        expires_value: expiresValue,
        expires_unit: expiresUnit,
        use_duckdns: useDuckdns,
        require_visitor_name: requireVisitorName,
        password_enabled: passwordEnabled,
        password,
      }),
    });
    const data = await res.json().catch(async () => {
      try { return { ok:false, error: await res.text() }; } catch { return { ok:false, error:'' }; }
    });
    if (!res.ok || !data || !data.ok) {
      const message = (data && data.error) || tr('mapper_share_create_failed');
      console.error('Share create failed:', { status: res.status, message, response: data });
      showStatus(message, 'err');
      const errEl = document.getElementById('mapperShareError');
      if (errEl) { errEl.textContent = message; errEl.classList.remove('hidden'); }
      return;
    }
    const link = String(data.link || '');
    if (els.mapperShareResultInput) els.mapperShareResultInput.value = link;
    if (els.mapperShareResultWrap) els.mapperShareResultWrap.classList.remove('hidden');
    // Show QR for the generated link
    try {
      const qrImg = document.getElementById('mapperShareQrImg');
      const qrWrap = document.getElementById('mapperShareQrWrap');
      if (qrImg) qrImg.src = `/api/qr?text=${encodeURIComponent(link)}&box=6&border=2`;
      if (qrWrap) qrWrap.classList.remove('hidden');
    } catch {}
    showStatus(tr('mapper_share_created'), 'ok');
  } catch {
    showStatus(tr('mapper_share_create_failed'), 'err');
    const errEl = document.getElementById('mapperShareError');
    if (errEl) { errEl.textContent = tr('mapper_share_create_failed'); errEl.classList.remove('hidden'); }
  } finally {
    if (confirmBtn) {
      confirmBtn.classList.remove('loading');
      confirmBtn.disabled = false;
      confirmBtn.textContent = original || tr('mapper_share_generate');
    }
  }
}

async function copyMapperShareLink() {
  const link = String((els.mapperShareResultInput && els.mapperShareResultInput.value) || '').trim();
  if (!link) return;
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(link);
    } else {
      if (els.mapperShareResultInput) {
        els.mapperShareResultInput.focus();
        els.mapperShareResultInput.select();
      }
      document.execCommand('copy');
    }
    showStatus(tr('mapper_share_copy_ok'), 'ok');
  } catch {
    showStatus(tr('mapper_share_copy_fail'), 'err');
  }
}

// Download QR image helper
const mapperShareQrDownload = document.getElementById('mapperShareQrDownload');
if (mapperShareQrDownload) {
  mapperShareQrDownload.addEventListener('click', async () => {
    const img = document.getElementById('mapperShareQrImg');
    if (!(img && img.src)) return;
    try {
      const res = await fetch(img.src, { cache: 'no-store' });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'share-qr.png';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {}
  });
}

function openScanModal() {
  if (!SCAN_FEATURES_ENABLED) return;
  if (!els.scanModal) return;
  els.scanModal.classList.remove('hidden');
}

function closeScanModal() {
  if (!els.scanModal) return;
  els.scanModal.classList.add('hidden');
}

function openAiScopeModal(feature) {
  if (feature === 'faces') state.aiScopePendingFeature = 'faces';
  else if (feature === 'describe_model') state.aiScopePendingFeature = 'describe_model';
  else if (feature === 'describe') state.aiScopePendingFeature = 'describe';
  else state.aiScopePendingFeature = 'ai';
  if (els.aiScopeModalTitle) {
    if (state.aiScopePendingFeature === 'faces') els.aiScopeModalTitle.textContent = tr('ai_scope_title_faces');
    else if (state.aiScopePendingFeature === 'describe_model') els.aiScopeModalTitle.textContent = tr('ai_scope_title_desc_model');
    else if (state.aiScopePendingFeature === 'describe') els.aiScopeModalTitle.textContent = tr('ai_scope_title_desc');
    else els.aiScopeModalTitle.textContent = tr('ai_scope_title_ai');
  }
  if (els.aiScopeModalText) els.aiScopeModalText.textContent = tr('ai_scope_text');
  if (els.aiScopeModalNew) els.aiScopeModalNew.textContent = tr('ai_scope_new');
  if (els.aiScopeModalAll) els.aiScopeModalAll.textContent = tr('ai_scope_all');
  if (els.aiScopeModalCancel) els.aiScopeModalCancel.textContent = tr('ai_scope_cancel');
  if (els.aiScopeModalClose) els.aiScopeModalClose.textContent = tr('scan_modal_close');
  if (els.aiScopeModal) els.aiScopeModal.classList.remove('hidden');
}

function closeAiScopeModal() {
  if (els.aiScopeModal) els.aiScopeModal.classList.add('hidden');
  state.aiScopePendingFeature = null;
  state.aiDescribePendingModel = null;
  updateAiToggleButton();
  updateAiDescribeToggleButton();
  updateAiDescribeModelSelect();
  updateFacesToggleButton();
}

function openMapperHeaderMenu() {
  if (!els.mapperHeaderMenu) return;
  const menu = els.mapperHeaderMenu;
  menu.classList.add('open');
  // On mobile, place the menu within the viewport using fixed positioning
  try {
    const btn = els.mapperEditBtn;
    if (btn && typeof btn.getBoundingClientRect === 'function') {
      const r = btn.getBoundingClientRect();
      const vw = Math.max(window.innerWidth || 0, document.documentElement.clientWidth || 0);
      const width = 220; // menu css width
      const pad = 8;
      let left = r.right - width; // prefer right-aligned to button
      left = Math.max(pad, Math.min(left, vw - width - pad));
      const top = Math.max(pad, r.bottom + 8);
      menu.style.position = 'fixed';
      menu.style.left = `${left}px`;
      menu.style.right = 'auto';
      menu.style.top = `${top}px`;
      menu.style.maxWidth = `${width}px`;
    }
  } catch {}
}

function closeMapperHeaderMenu() {
  if (!els.mapperHeaderMenu) return;
  const menu = els.mapperHeaderMenu;
  menu.classList.remove('open');
  // Reset any inline positioning to fall back to CSS on desktop
  try {
    menu.style.position = '';
    menu.style.left = '';
    menu.style.right = '';
    menu.style.top = '';
    menu.style.maxWidth = '';
  } catch {}
}

function toggleMapperHeaderMenu() {
  if (!els.mapperHeaderMenu) return;
  if (els.mapperHeaderMenu.classList.contains('open')) closeMapperHeaderMenu();
  else openMapperHeaderMenu();
}

let pendingIosUploadPicker = null;

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

function closeIosUploadPrepModal() {
  pendingIosUploadPicker = null;
  if (els.iosUploadPrepModal) els.iosUploadPrepModal.classList.add('hidden');
}

function showIosUploadPrepModal(onContinue) {
  if (!els.iosUploadPrepModal) {
    if (typeof onContinue === 'function') onContinue();
    return;
  }
  pendingIosUploadPicker = (typeof onContinue === 'function') ? onContinue : null;
  els.iosUploadPrepModal.classList.remove('hidden');
  try { els.iosUploadPrepContinue && els.iosUploadPrepContinue.focus({ preventScroll: true }); } catch {}
}

function continueIosUploadPrepModal() {
  const fn = pendingIosUploadPicker;
  pendingIosUploadPicker = null;
  if (els.iosUploadPrepModal) els.iosUploadPrepModal.classList.add('hidden');
  if (typeof fn === 'function') fn();
}

function openMapperUploadPicker(skipPrepNotice = false) {
  if (!els.mapperUploadInput) return;
  if (!skipPrepNotice && shouldShowUploadPrepNotice()) {
    showIosUploadPrepModal(() => openMapperUploadPicker(true));
    return;
  }
  els.mapperUploadInput.value = '';
  try {
    if (typeof els.mapperUploadInput.showPicker === 'function') {
      els.mapperUploadInput.showPicker();
      return;
    }
    els.mapperUploadInput.click();
  } catch {
    showStatus(tr('file_picker_open_failed'), 'err');
  }
}

function _syncSearchInputs(value, source = null) {
  const v = String(value || '');
  if (els.search && source !== 'top') els.search.value = v;
  if (els.mapperSearchInput && source !== 'mapper') els.mapperSearchInput.value = v;
}

let searchLoadTimer = null;
function scheduleSearchLoad(delay = 320) {
  if (searchLoadTimer) clearTimeout(searchLoadTimer);
  searchLoadTimer = setTimeout(() => {
    searchLoadTimer = null;
    loadPhotos();
  }, delay);
}

function expandSearchField(focusInput = true) {
  if (!els.searchShell) return;
  els.searchShell.classList.add('expanded');
  if (focusInput && els.search) {
    try {
      els.search.focus();
      const len = String(els.search.value || '').length;
      els.search.setSelectionRange(len, len);
    } catch {}
  }
}

function collapseSearchField() {
  if (!els.searchShell) return;
  els.searchShell.classList.remove('expanded');
}

// Events
if (els.searchToggleBtn) {
  els.searchToggleBtn.addEventListener('click', (e) => {
    e.preventDefault();
    const expanded = !!(els.searchShell && els.searchShell.classList.contains('expanded'));
    if (expanded) {
      if (els.search) els.search.focus();
      return;
    }
    expandSearchField(true);
  });
}

if (els.search) {
  els.search.addEventListener('focus', () => expandSearchField(false));
  els.search.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      collapseSearchField();
      try { els.search.blur(); } catch {}
    }
  });
}

document.addEventListener('pointerdown', (e) => {
  const target = e.target;
  if (!(target instanceof Node)) return;
  if (els.searchShell && els.searchShell.contains(target)) return;
  if (els.mapperSearchShell && els.mapperSearchShell.contains(target)) return;
  if (els.mapperHeaderActions && els.mapperHeaderActions.contains(target)) return;
  collapseSearchField();
  if (els.mapperSearchShell) els.mapperSearchShell.classList.remove('expanded');
  closeMapperHeaderMenu();
});

// Global ESC to cancel selection in Mapper view
document.addEventListener('keydown', (e) => {
  try {
    if (e.key === 'Escape' && state && state.view === 'mapper' && state.mapperEditMode) {
      setMapperEditMode(false);
      e.preventDefault();
      e.stopPropagation();
    }
  } catch {}
});

if (els.mapperSearchToggleBtn) {
  els.mapperSearchToggleBtn.addEventListener('click', (e) => {
    e.preventDefault();
    if (!els.mapperSearchShell) return;
    const expanded = els.mapperSearchShell.classList.contains('expanded');
    if (!expanded) {
      els.mapperSearchShell.classList.add('expanded');
      if (els.mapperSearchInput) {
        try {
          els.mapperSearchInput.focus();
          const len = String(els.mapperSearchInput.value || '').length;
          els.mapperSearchInput.setSelectionRange(len, len);
        } catch {}
      }
      return;
    }
    if (els.mapperSearchInput) els.mapperSearchInput.focus();
  });
}
if (els.mapperSearchInput) {
  els.mapperSearchInput.addEventListener('focus', () => {
    if (els.mapperSearchShell) els.mapperSearchShell.classList.add('expanded');
  });
  els.mapperSearchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (els.mapperSearchShell) els.mapperSearchShell.classList.remove('expanded');
      try { els.mapperSearchInput.blur(); } catch {}
    }
  });
  els.mapperSearchInput.addEventListener('input', () => {
    state.q = els.mapperSearchInput.value.trim();
    _syncSearchInputs(els.mapperSearchInput.value, 'mapper');
    scheduleSearchLoad();
  });
}
if (els.mapperEditBtn) {
  let _menuOpenedByTouchAt = 0;
  const _openMenu = (ev) => {
    try { ev && ev.preventDefault && ev.preventDefault(); } catch {}
    try { ev && ev.stopPropagation && ev.stopPropagation(); } catch {}
    toggleMapperHeaderMenu();
  };
  els.mapperEditBtn.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    // If a touch just opened the menu, ignore the follow-up synthetic click
    if (Date.now() - _menuOpenedByTouchAt < 500) return;
    toggleMapperHeaderMenu();
  });
  // Improve mobile tap support: open on touch without toggling twice
  els.mapperEditBtn.addEventListener('touchstart', (e) => {
    try { e.preventDefault(); e.stopPropagation(); } catch {}
    openMapperHeaderMenu();
    _menuOpenedByTouchAt = Date.now();
  }, { passive: false });
  // Do not react on mouse pointerdown; rely on normal click to toggle
  els.mapperEditBtn.addEventListener('pointerdown', (e) => {
    if (!e || e.pointerType !== 'touch') return;
    try { e.preventDefault(); e.stopPropagation(); } catch {}
    openMapperHeaderMenu();
    _menuOpenedByTouchAt = Date.now();
  }, { passive: false });
}
// Prevent outside-click handler from immediately closing when interacting inside the menu
if (els.mapperHeaderMenu) {
  ['pointerdown','touchstart','click'].forEach(ev => {
    els.mapperHeaderMenu.addEventListener(ev, (e) => { e.stopPropagation(); }, { passive: true });
  });
}
if (els.iosUploadPrepClose) {
  els.iosUploadPrepClose.addEventListener('click', closeIosUploadPrepModal);
}
if (els.iosUploadPrepCancel) {
  els.iosUploadPrepCancel.addEventListener('click', closeIosUploadPrepModal);
}
if (els.iosUploadPrepContinue) {
  els.iosUploadPrepContinue.addEventListener('click', continueIosUploadPrepModal);
}
if (els.iosUploadPrepModal) {
  els.iosUploadPrepModal.addEventListener('click', (e) => {
    if (e.target === els.iosUploadPrepModal || (e.target && e.target.classList && e.target.classList.contains('modal-backdrop'))) {
      closeIosUploadPrepModal();
    }
  });
}
if (els.mapperHeaderEditAction) {
  els.mapperHeaderEditAction.addEventListener('click', async () => {
    const selectedCount = state.mapperSelectedFolders ? state.mapperSelectedFolders.size : 0;
    if (!state.mapperEditMode) {
      setMapperEditMode(true);
      closeMapperHeaderMenu();
      return;
    }
    if (selectedCount > 0) {
      await deleteSelectedMapperFolders();
      closeMapperHeaderMenu();
      return;
    }
    setMapperEditMode(false);
    closeMapperHeaderMenu();
  });
}
if (els.mapperHeaderCreateAction) {
  els.mapperHeaderCreateAction.addEventListener('click', () => {
    openMapperCreateModal();
    closeMapperHeaderMenu();
  });
}
if (els.mapperHeaderUploadAction) {
  els.mapperHeaderUploadAction.addEventListener('click', () => {
    closeMapperHeaderMenu();
    openMapperUploadPicker();
  });
}
if (els.mapperHeaderSortNewestAction) {
  els.mapperHeaderSortNewestAction.addEventListener('click', async () => {
    if (state.mapperEditMode) return;
    state.mapperSort = 'date_desc';
    closeMapperHeaderMenu();
    await loadPhotos();
  });
}
if (els.mapperHeaderSortOldestAction) {
  els.mapperHeaderSortOldestAction.addEventListener('click', async () => {
    if (state.mapperEditMode) return;
    state.mapperSort = 'date_asc';
    closeMapperHeaderMenu();
    await loadPhotos();
  });
}
if (els.mapperSortSelect) {
  els.mapperSortSelect.addEventListener('change', async () => {
    if (state.mapperEditMode) return;
    state.mapperSort = _normalizeMapperSort(els.mapperSortSelect.value);
    await loadPhotos();
  });
}
if (els.mapperHeaderShareAction) {
  els.mapperHeaderShareAction.addEventListener('click', async () => {
    await openMapperShareModal();
    closeMapperHeaderMenu();
  });
}
if (els.mapperHeaderRenameAction) {
  els.mapperHeaderRenameAction.addEventListener('click', () => {
    const selFolders = Array.from(state.mapperSelectedFolders || []);
    const selPhotos = state.mapperSelectedPhotoIds ? state.mapperSelectedPhotoIds.size : 0;
    if (state.mapperEditMode) {
      if (selFolders.length !== 1 || selPhotos > 0) {
        showStatus(tr('mapper_rename_select_one'), 'err');
        closeMapperHeaderMenu();
        return;
      }
      openMapperRenameModal(selFolders[0]);
      closeMapperHeaderMenu();
      return;
    }
    const current = _normalizeMapperPath(String(state.mapperPath || ''));
    if (!current) {
      showStatus(tr('mapper_rename_root_block'), 'err');
      closeMapperHeaderMenu();
      return;
    }
    openMapperRenameModal(current);
    closeMapperHeaderMenu();
  });
}
if (els.search) {
  _syncSearchInputs(els.search.value || '', 'top');
}
els.search.addEventListener("input", () => {
  state.q = els.search.value.trim();
  _syncSearchInputs(els.search.value, 'top');
  scheduleSearchLoad();
});
els.sort.addEventListener("change", () => {
  state.sort = els.sort.value;
  loadPhotos();
});
els.scanBtn && els.scanBtn.addEventListener("click", () => {
  if (!SCAN_FEATURES_ENABLED) {
    showStatus('Scan-funktioner er deaktiveret.', 'err');
    return;
  }
  if (state.scanning) {
    scanLibrary();
    return;
  }
  openScanModal();
});
els.rescanBtn && els.rescanBtn.addEventListener("click", rescanMetadata);
els.rethumbBtn && els.rethumbBtn.addEventListener("click", rethumbAll);
els.stopAllProcessesBtn && els.stopAllProcessesBtn.addEventListener("click", stopAllProcesses);
els.clearIndexBtn && els.clearIndexBtn.addEventListener("click", clearIndex);
async function startAiIngest(scope = 'all') {
  try {
    showStatus(tr('ai_starting'), "ok");
    const qs = (scope === 'new') ? '?scope=new' : '?scope=all';
    const res = await fetch(`/api/ai/ingest${qs}`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      showStatus(tr('ai_start_failed'), "err");
      return;
    }
    if (scope === 'new') {
      showStatus(tr('ai_enabled_new_uploads'), 'ok');
    } else {
      showStatus(tr('ai_started_bg'), "ok");
    }
    state.aiAutoEnabled = true;
    state.aiRunning = !!(data && data.running);
    updateAiToggleButton();
    pollAiStatus();
  } catch { showStatus(tr('ai_start_error'), "err"); }
}

async function stopAiIngest() {
  try {
    const res = await fetch('/api/ai/stop', { method: 'POST' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || (data && data.ok === false)) {
      showStatus(tr('ai_stop_failed'), 'err');
      return;
    }
    showStatus(tr('ai_stopped'), 'ok');
    state.aiRunning = false;
    state.aiAutoEnabled = false;
    updateAiToggleButton();
    pollAiStatus();
  } catch {
    showStatus(tr('ai_stop_error'), 'err');
  }
}

async function setAiDescribeModel(model, scope = 'new') {
  const wantedModel = normalizeAiDescribeModel(model);
  const wantedScope = (scope === 'all') ? 'all' : 'new';
  try {
    const res = await fetch('/api/ai/describe/model', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: wantedModel, scope: wantedScope }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || data.ok === false) {
      showStatus((data && data.error) || tr('ai_desc_model_change_failed'), 'err');
      updateAiDescribeModelSelect();
      return false;
    }

    state.aiDescribeModel = normalizeAiDescribeModel((data && data.model) || wantedModel);
    if (typeof data.auto_ingest !== 'undefined') state.aiDescribeAutoEnabled = !!data.auto_ingest;
    if (typeof data.running !== 'undefined') state.aiDescribeRunning = !!data.running;
    state.aiDescribeStopping = false;
    state.aiDescribeForceStopPending = false;
    updateAiDescribeModelSelect();
    updateAiDescribeToggleButton();

    if (wantedScope === 'all') showStatus(tr('ai_desc_model_changed_all'), 'ok');
    else showStatus(tr('ai_desc_model_changed_new'), 'ok');

    pollAiDescribeStatus();
    return true;
  } catch {
    showStatus(tr('ai_desc_model_change_failed'), 'err');
    updateAiDescribeModelSelect();
    return false;
  }
}

async function startAiDescribeIngest(scope = 'all') {
  try {
    showStatus(tr('ai_desc_starting'), 'ok');
    const qs = (scope === 'new') ? '?scope=new' : '?scope=all';
    const res = await fetch(`/api/ai/describe/ingest${qs}`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      showStatus(tr('ai_desc_start_failed'), 'err');
      return;
    }
    state.aiDescribeModel = normalizeAiDescribeModel((data && data.model) || state.aiDescribeModel);
    if (scope === 'new') {
      showStatus(tr('ai_desc_enabled_new_uploads'), 'ok');
    } else {
      showStatus(tr('ai_desc_started_bg'), 'ok');
    }
    state.aiDescribeAutoEnabled = true;
    state.aiDescribeRunning = !!(data && data.running);
    state.aiDescribeStopping = false;
    state.aiDescribeForceStopPending = false;
    updateAiDescribeModelSelect();
    updateAiDescribeToggleButton();
    pollAiDescribeStatus();
  } catch {
    showStatus(tr('ai_desc_start_error'), 'err');
  }
}

async function stopAiDescribeIngest() {
  try {
    const res = await fetch('/api/ai/describe/stop', { method: 'POST' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || (data && data.ok === false)) {
      showStatus(tr('ai_desc_stop_failed'), 'err');
      return;
    }
    showStatus(tr('ai_desc_stopped'), 'ok');
    state.aiDescribeRunning = !!(data && data.running);
    state.aiDescribeStopping = !!(data && data.stopping);
    state.aiDescribeAutoEnabled = false;
    updateAiDescribeToggleButton();
    pollAiDescribeStatus();
  } catch {
    showStatus(tr('ai_desc_stop_error'), 'err');
  }
}

async function forceStopAiDescribeIngest() {
  state.aiDescribeForceStopPending = true;
  state.aiDescribeStopping = true;
  updateAiDescribeToggleButton();
  try {
    const res = await fetch('/api/ai/describe/stop?force=1', { method: 'POST' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || (data && data.ok === false)) {
      state.aiDescribeForceStopPending = false;
      state.aiDescribeStopping = false;
      updateAiDescribeToggleButton();
      showStatus(tr('ai_desc_force_failed'), 'err');
      return;
    }
    showStatus(tr('ai_desc_force_stopping'), 'ok');
    state.aiDescribeForceStopPending = false;
    state.aiDescribeAutoEnabled = false;
    pollAiDescribeStatus();
  } catch {
    state.aiDescribeForceStopPending = false;
    state.aiDescribeStopping = false;
    updateAiDescribeToggleButton();
    showStatus(tr('ai_desc_force_error'), 'err');
  }
}

function showAiExternalModalStatus(message, kind = 'ok') {
  if (!els.aiExternalModalStatus) return;
  els.aiExternalModalStatus.textContent = message || '';
  els.aiExternalModalStatus.classList.toggle('hidden', !message);
  els.aiExternalModalStatus.classList.toggle('err', kind === 'err');
}

function buildAiExternalConnectionUrl(token = state.aiDescExternalToken) {
  const value = String(token || '').trim();
  if (!value) return '';
  try {
    const url = new URL('/api/ai/describe/external/ping', window.location.origin);
    url.searchParams.set('token', value);
    return url.toString();
  } catch {
    return `/api/ai/describe/external/ping?token=${encodeURIComponent(value)}`;
  }
}

function aiExternalConnectionValue(data = null) {
  const direct = data && data.connection_url ? String(data.connection_url).trim() : '';
  const browserUrl = buildAiExternalConnectionUrl((data && data.token) || state.aiDescExternalToken);
  return browserUrl || direct;
}

function updateAiExternalConnectionInput(data = null) {
  const value = aiExternalConnectionValue(data);
  state.aiDescExternalConnectionUrl = value;
  if (els.aiExternalTokenInput) els.aiExternalTokenInput.value = value;
}

function normalizeAiExternalLinkForDisplay(rawUrl) {
  const raw = String(rawUrl || '').trim();
  if (!raw) return '';
  try {
    const parsed = new URL(raw, window.location.origin);
    const token = parsed.searchParams.get('token') || parsed.searchParams.get('api_token') || parsed.searchParams.get('fjordlens_token') || '';
    return token ? buildAiExternalConnectionUrl(token) : raw;
  } catch {
    return raw;
  }
}

function applyAiExternalSettings(data) {
  if (!data || data.ok === false) return;
  state.aiDescExternalEnabled = !!data.enabled;
  state.aiDescExternalFolders = Array.isArray(data.folders) ? data.folders : [];
  state.aiDescExternalAvailableFolders = Array.isArray(data.available_folders) ? data.available_folders : [];
  state.aiDescExternalToken = Object.prototype.hasOwnProperty.call(data, 'token') ? String(data.token || '') : String(state.aiDescExternalToken || '');
  state.aiDescExternalConnectionUrl = aiExternalConnectionValue(data);
  if (Array.isArray(data.links)) state.aiDescExternalLinks = data.links;
  state.aiDescExternalPending = Number(data.pending || 0);
  state.aiDescExternalDescribed = Number(data.described || 0);
  state.aiDescExternalTotal = Number(data.total || 0);
  updateAiDescribeToggleButton();
}

function renderAiExternalFolders() {
  if (!els.aiExternalFolders) return;
  const folders = Array.isArray(state.aiDescExternalAvailableFolders) ? state.aiDescExternalAvailableFolders : [];
  const selected = new Set(Array.isArray(state.aiDescExternalFolders) ? state.aiDescExternalFolders : []);
  if (!folders.length) {
    els.aiExternalFolders.innerHTML = `<div>${escapeHtml(tr('ai_desc_external_no_folders'))}</div>`;
    return;
  }
  els.aiExternalFolders.innerHTML = folders.map((folder) => {
    const checked = selected.has(folder) ? ' checked' : '';
    return `<label class="ai-toggle-row" style="align-items:flex-start;">
      <input type="checkbox" data-ai-external-folder="${escapeHtml(folder)}"${checked} />
      <span class="mini-label">${escapeHtml(folder)}</span>
    </label>`;
  }).join('');
}

function collectAiExternalFoldersFromModal() {
  if (!els.aiExternalFolders) return [];
  return Array.from(els.aiExternalFolders.querySelectorAll('input[data-ai-external-folder]:checked'))
    .map((input) => String(input.getAttribute('data-ai-external-folder') || '').trim())
    .filter(Boolean);
}

async function loadAiExternalSettings({ openModal = false } = {}) {
  try {
    const res = await fetch('/api/ai/describe/external/settings');
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || data.ok === false) throw new Error((data && data.error) || 'load_failed');
    applyAiExternalSettings(data);
    updateAiExternalConnectionInput(data);
    renderAiExternalFolders();
    if (openModal && els.aiExternalModal) {
      showAiExternalModalStatus('');
      els.aiExternalModal.classList.remove('hidden');
    }
    return data;
  } catch {
    showStatus(tr('ai_desc_external_load_failed'), 'err');
    return null;
  }
}

async function saveAiExternalSettings({ enabled = null, rotateToken = false, folders = null } = {}) {
  const wantedEnabled = (enabled === null) ? !!state.aiDescExternalEnabled : !!enabled;
  const wantedFolders = Array.isArray(folders) ? folders : (Array.isArray(state.aiDescExternalFolders) ? state.aiDescExternalFolders : []);
  try {
    const res = await fetch('/api/ai/describe/external/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        enabled: wantedEnabled,
        folders: wantedFolders,
        rotate_token: !!rotateToken,
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || data.ok === false) throw new Error((data && data.error) || 'save_failed');
    applyAiExternalSettings(data);
    updateAiExternalConnectionInput(data);
    renderAiExternalFolders();
    showStatus(wantedEnabled ? tr('ai_desc_external_saved') : tr('ai_desc_external_disabled'), 'ok');
    showAiExternalModalStatus(tr('ai_desc_external_saved'), 'ok');
    return data;
  } catch {
    showStatus(tr('ai_desc_external_save_failed'), 'err');
    showAiExternalModalStatus(tr('ai_desc_external_save_failed'), 'err');
    return null;
  }
}

function closeAiExternalModal() {
  if (els.aiExternalModal) els.aiExternalModal.classList.add('hidden');
}

async function copyAiExternalToken() {
  const value = String((els.aiExternalTokenInput && els.aiExternalTokenInput.value) || state.aiDescExternalConnectionUrl || aiExternalConnectionValue() || '').trim();
  if (!value) return;
  await copyAiExternalText(value, (message, kind) => showAiExternalModalStatus(message, kind));
}

async function copyAiExternalText(value, statusFn = null) {
  const text = String(value || '').trim();
  if (!text) return;
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      ta.remove();
    }
    if (typeof statusFn === 'function') statusFn(tr('ai_desc_external_token_copied'), 'ok');
  } catch {
    if (typeof statusFn === 'function') statusFn(tr('mapper_share_copy_fail'), 'err');
  }
}

function showAiExternalLinksStatus(message, kind = 'ok') {
  if (!els.aiExternalLinksStatus) return;
  els.aiExternalLinksStatus.textContent = message || '';
  els.aiExternalLinksStatus.classList.toggle('hidden', !message);
  els.aiExternalLinksStatus.classList.toggle('err', kind === 'err');
}

function renderAiExternalLinks(links) {
  if (!els.aiExternalLinksList) return;
  const items = Array.isArray(links) ? links : [];
  state.aiDescExternalLinks = items;
  if (!items.length) {
    els.aiExternalLinksList.innerHTML = `<div class="mini-label">${escapeHtml(tr('ai_desc_external_links_empty'))}</div>`;
    return;
  }
  els.aiExternalLinksList.innerHTML = items.map((link) => {
    const id = String(link.id || '').trim();
    const url = normalizeAiExternalLinkForDisplay(link.connection_url);
    const created = fmtDate(link.created_at);
    const hint = String(link.token_hint || '').trim();
    const current = link.current ? `<span class="pill">${escapeHtml(tr('ai_desc_external_current_link'))}</span>` : '';
    return `
      <div style="border:1px solid var(--border);border-radius:10px;padding:10px;background:var(--bg-soft);display:grid;gap:8px;">
        <div style="display:flex;justify-content:space-between;gap:10px;align-items:center;">
          <div>
            <strong>${escapeHtml(tr('ai_desc_external_token_label'))}</strong>
            <div class="mini-label">${escapeHtml(tr('ai_desc_external_created_label'))}: ${escapeHtml(created)}${hint ? ` · ***${escapeHtml(hint)}` : ''}</div>
          </div>
          ${current}
        </div>
        <div style="display:flex;gap:8px;align-items:center;">
          <input class="mapper-input" type="text" readonly value="${escapeHtml(url)}" style="min-width:0;width:100%;" />
          <button class="btn small" type="button" data-ai-external-link-copy="${escapeHtml(id)}">${escapeHtml((resolveUiLanguage(state.uiLanguage || 'da') === 'en') ? 'Copy' : 'Kopiér')}</button>
          <button class="btn small danger" type="button" data-ai-external-link-delete="${escapeHtml(id)}">${escapeHtml(tr('ai_desc_external_link_delete'))}</button>
        </div>
      </div>`;
  }).join('');
}

async function loadAiExternalLinks({ openModal = false } = {}) {
  try {
    const res = await fetch('/api/ai/describe/external/links');
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || data.ok === false) throw new Error((data && data.error) || 'load_failed');
    renderAiExternalLinks(data.links || []);
    showAiExternalLinksStatus('');
    if (openModal && els.aiExternalLinksModal) els.aiExternalLinksModal.classList.remove('hidden');
    return data;
  } catch {
    showAiExternalLinksStatus(tr('ai_desc_external_links_load_failed'), 'err');
    if (openModal && els.aiExternalLinksModal) els.aiExternalLinksModal.classList.remove('hidden');
    return null;
  }
}

async function deleteAiExternalLink(id) {
  const linkId = String(id || '').trim();
  if (!linkId) return;
  if (!window.confirm(tr('ai_desc_external_link_delete_confirm'))) return;
  try {
    const res = await fetch(`/api/ai/describe/external/links/${encodeURIComponent(linkId)}`, { method: 'DELETE' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || data.ok === false) throw new Error((data && data.error) || 'delete_failed');
    renderAiExternalLinks(data.links || []);
    if (data.token || data.connection_url) {
      state.aiDescExternalToken = String(data.token || '');
      state.aiDescExternalConnectionUrl = String(data.connection_url || '');
      updateAiExternalConnectionInput(data);
    } else if (Object.prototype.hasOwnProperty.call(data, 'token')) {
      state.aiDescExternalToken = '';
      state.aiDescExternalConnectionUrl = '';
      if (els.aiExternalTokenInput) els.aiExternalTokenInput.value = '';
    }
    showAiExternalLinksStatus(tr('ai_desc_external_link_deleted'), 'ok');
  } catch {
    showAiExternalLinksStatus(tr('ai_desc_external_link_delete_failed'), 'err');
  }
}

els.aiIngestToggle && els.aiIngestToggle.addEventListener('change', async () => {
  if (els.aiIngestToggle.checked) {
    openAiScopeModal('ai');
    return;
  }
  await stopAiIngest();
});

els.aiDescribeToggle && els.aiDescribeToggle.addEventListener('change', async () => {
  if (els.aiDescribeToggle.checked) {
    openAiScopeModal('describe');
    return;
  }
  await stopAiDescribeIngest();
});

els.aiDescExternalToggle && els.aiDescExternalToggle.addEventListener('change', async () => {
  const enabled = !!els.aiDescExternalToggle.checked;
  if (enabled) {
    await loadAiExternalSettings();
    const data = await saveAiExternalSettings({ enabled: true });
    if (!data) {
      state.aiDescExternalEnabled = false;
      updateAiDescribeToggleButton();
      return;
    }
    if (!state.aiDescExternalFolders.length) {
      await loadAiExternalSettings({ openModal: true });
    }
  } else {
    await saveAiExternalSettings({ enabled: false });
  }
});

els.aiDescExternalChooseBtn && els.aiDescExternalChooseBtn.addEventListener('click', async () => {
  await loadAiExternalSettings({ openModal: true });
});

els.aiDescribeForceStopBtn && els.aiDescribeForceStopBtn.addEventListener('click', async () => {
  await forceStopAiDescribeIngest();
});

async function rerunAiDescribe() {
  try {
    showStatus(tr('ai_desc_rerun_starting'), 'ok');
    const res = await fetch('/api/ai/describe/rerun', { method: 'POST' });
    const data = await res.json().catch(()=>({}));
    if (!res.ok || !data || data.ok === false) { showStatus(tr('ai_desc_rerun_failed'), 'err'); return; }
    showStatus(tr('ai_desc_rerun_started'), 'ok');
    state.aiDescribeRunning = true;
    state.aiDescribeStopping = false;
    state.aiDescribeAutoEnabled = true;
    updateAiDescribeToggleButton();
    pollAiDescribeStatus();
  } catch {
    showStatus(tr('ai_desc_rerun_failed'), 'err');
  }
}

els.aiDescribeRerunBtn && els.aiDescribeRerunBtn.addEventListener('click', rerunAiDescribe);

async function clearAiDescriptions() {
  if (!window.confirm(tr('ai_desc_clear_confirm'))) return;
  const btn = els.aiDescribeClearBtn;
  const original = btn ? btn.textContent : tr('btn_clear_ai_desc');
  try {
    if (btn) {
      btn.disabled = true;
      btn.classList.add('loading');
    }
    showStatus(tr('ai_desc_clear_starting'), 'ok');
    const res = await fetch('/api/ai/describe/clear', { method: 'POST' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || data.ok === false) {
      showStatus((data && data.error) || tr('ai_desc_clear_failed'), 'err');
      return;
    }
    const count = Number(data.cleared || 0);
    showStatus(tr('ai_desc_clear_done').replace('{count}', String(count)), 'ok');
    state.aiDescribeRunning = false;
    state.aiDescribeStopping = false;
    state.aiDescribeForceStopPending = false;
    updateAiDescribeToggleButton();
    pollAiDescribeStatus();
    loadPhotos();
  } catch {
    showStatus(tr('ai_desc_clear_failed'), 'err');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.classList.remove('loading');
      btn.textContent = original || tr('btn_clear_ai_desc');
    }
  }
}

els.aiDescribeClearBtn && els.aiDescribeClearBtn.addEventListener('click', clearAiDescriptions);

async function unloadQwenGpu() {
  try {
    if (els.hardwareStatus) { els.hardwareStatus.classList.remove('hidden','err'); els.hardwareStatus.textContent = tr('please_wait') || 'Arbejder...'; }
    const res = await fetch('/api/ai/hardware/qwen/unload', { method: 'POST' });
    const data = await res.json().catch(()=>({}));
    if (!res.ok || !data || data.ok === false) {
      if (els.hardwareStatus) { els.hardwareStatus.classList.remove('hidden'); els.hardwareStatus.classList.add('err'); els.hardwareStatus.textContent = tr('hw_unload_qwen_err'); }
      return;
    }
    if (els.hardwareStatus) { els.hardwareStatus.classList.remove('hidden','err'); els.hardwareStatus.textContent = tr('hw_unload_qwen_ok'); }
  } catch {
    if (els.hardwareStatus) { els.hardwareStatus.classList.remove('hidden'); els.hardwareStatus.classList.add('err'); els.hardwareStatus.textContent = tr('hw_unload_qwen_err'); }
  }
}

els.hardwareUnloadQwenBtn && els.hardwareUnloadQwenBtn.addEventListener('click', unloadQwenGpu);

if (els.aiDescribeModelSelect) {
  els.aiDescribeModelSelect.addEventListener('change', async () => {
    const nextModel = normalizeAiDescribeModel(els.aiDescribeModelSelect.value);
    const currentModel = normalizeAiDescribeModel(state.aiDescribeModel || 'light');
    if (nextModel === currentModel) {
      updateAiDescribeModelSelect();
      return;
    }

    if (state.aiDescribeAutoEnabled || state.aiDescribeRunning) {
      state.aiDescribePendingModel = nextModel;
      openAiScopeModal('describe_model');
      return;
    }

    await setAiDescribeModel(nextModel, 'new');
  });
}

// Faces indexing controls
async function pollFacesStatus() {
  try {
    const r = await fetch('/api/faces/status');
    const s = await r.json();
    state.facesRunning = !!(s && s.ok && s.running);
    state.facesAutoEnabled = !!(s && s.ok && s.auto_index);
    state.facesRuntime = String((s && s.runtime && (s.runtime.faces || s.runtime.ai)) || 'unknown');
    updateFacesToggleButton();
    updateRuntimeIndicator(els.aiFacesRuntime, state.facesRuntime);
    if (els.facesStatus) {
      const run = s && s.running ? tr('status_running') : tr('status_stopped');
      const source = (!s.running && s.last) ? s.last : s;
      const processed = Number(source && source.processed) || 0;
      const total = Number(source && source.total) || 0;
      const coverage = (s && s.coverage && typeof s.coverage === 'object') ? s.coverage : null;
      const coverageTotal = Number(coverage && coverage.total) || 0;
      const coverageIndexed = Number(coverage && coverage.indexed) || 0;
      const coverageMissing = Number(coverage && coverage.missing) || 0;
      const facesFound = Number(coverage && coverage.faces) || 0;
      const coverageText = coverage
        ? ` · ${tr('status_library_label')} ${coverageIndexed}/${coverageTotal} · ${tr('status_missing_label')} ${coverageMissing} · ${tr('status_faces_found_label')} ${facesFound}`
        : '';
      els.facesStatus.textContent = `${tr('status_faces_prefix')}: ${run} · ${tr('status_processed_label')} ${processed}/${total}${coverageText}`;
    }
    if (s && s.running) {
      // While faces are indexing, refresh People view incrementally when progress increases
      try {
        const source = (!s.running && s.last) ? s.last : s;
        const processed = Number(source && source.processed) || 0;
        const now = Date.now();
        if (!Number.isNaN(processed)) {
          const lastProc = Number(state._facesProcessed || 0);
          const lastAt = Number(state._facesAutoRefreshAt || 0);
          if (processed > lastProc && (now - lastAt) > 1200) {
            state._facesProcessed = processed;
            state._facesAutoRefreshAt = now;
            if (state.view === 'personer') {
              if (state.personView && state.personView.mode === 'photos' && state.personView.personId) {
                // Refresh current person's photos if viewing a person
                loadPersonPhotos(state.personView.personId, state.personView.personName);
              } else {
                // Refresh the People list so new thumbs appear without manual reload
                loadPeople();
              }
            }
          }
        }
      } catch {}
      setTimeout(pollFacesStatus, 1500);
    } else {
      // refresh lists when done
      if (state.view === 'personer') loadPeople();
      else loadPhotos();
    }
  } catch {
    state.facesRunning = false;
    state.facesAutoEnabled = false;
    state.facesRuntime = 'unknown';
    updateFacesToggleButton();
    updateRuntimeIndicator(els.aiFacesRuntime, state.facesRuntime);
    if (els.facesStatus) els.facesStatus.textContent = `${tr('status_faces_prefix')}: ${tr('status_dash')}`;
  }
}

async function startFacesIndex(scope = 'all') {
  try {
    showStatus(tr('faces_starting'), 'ok');
    const url = (scope === 'new') ? '/api/faces/index?scope=new' : '/api/faces/index?scope=all';
    const res = await fetch(url, { method: 'POST' });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      showStatus(data && data.error ? data.error : tr('faces_start_failed'), 'err');
      return;
    }
    state.facesAutoEnabled = true;
    state.facesRunning = !!(data && data.running);
    updateFacesToggleButton();
    if (scope === 'new') {
      showStatus(tr('faces_enabled_new_uploads'), 'ok');
    } else {
      showStatus(tr('faces_started_bg'), 'ok');
    }
    pollFacesStatus();
  } catch (e) {
    showStatus(tr('faces_start_error'), 'err');
  }
}

async function stopFacesIndex() {
  try {
    const res = await fetch('/api/faces/stop', { method: 'POST' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || data.ok === false) {
      showStatus(tr('faces_stop_failed'), 'err');
      return;
    }
    showStatus(tr('faces_stopped'), 'ok');
    state.facesAutoEnabled = false;
    state.facesRunning = false;
    updateFacesToggleButton();
    pollFacesStatus();
  } catch {
    showStatus(tr('faces_stop_error'), 'err');
  }
}

if (els.facesToggle) {
  els.facesToggle.addEventListener('change', async () => {
    if (els.facesToggle.checked) {
      openAiScopeModal('faces');
      return;
    }
    await stopFacesIndex();
  });
}

async function pollAiStatus() {
  try {
    const r = await fetch('/api/ai/status');
    const s = await r.json();
    state.aiRunning = !!(s && s.ok && s.running);
    state.aiAutoEnabled = !!(s && s.ok && s.auto_ingest);
    const coverage = (s && s.coverage && typeof s.coverage === 'object') ? s.coverage : null;
    state.aiCoverageTotal = Number(coverage && coverage.total) || 0;
    state.aiCoverageEmbedded = Number(coverage && coverage.embedded) || 0;
    state.aiCoverageMissing = Number(coverage && coverage.missing) || 0;
    state.aiRuntime = String((s && s.runtime && s.runtime.ai) || 'unknown');
    updateAiToggleButton();
    updateRuntimeIndicator(els.aiEmbedRuntime, state.aiRuntime);
    if (els.aiStatus) {
      if (!s || !s.ok) { els.aiStatus.textContent = `${tr('status_ai_prefix')}: ${tr('status_dash')}`; }
      else {
        const run = s.running ? tr('status_running') : tr('status_stopped');
        const source = (!s.running && s.last) ? s.last : s;
        const embedded = Number(source && source.embedded) || 0;
        const total = Number(source && source.total) || 0;
        const failed = Number(source && source.failed) || 0;
        const coverageTotal = Number(coverage && coverage.total) || 0;
        const coverageEmbedded = Number(coverage && coverage.embedded) || 0;
        const coverageMissing = Number(coverage && coverage.missing) || 0;
        const coverageText = coverage
          ? ` · ${tr('status_library_label')} ${coverageEmbedded}/${coverageTotal} · ${tr('status_missing_label')} ${coverageMissing}`
          : '';
        els.aiStatus.textContent = `${tr('status_ai_prefix')}: ${run} · ${tr('status_embedded_label')} ${embedded}/${total} · ${tr('status_errors_label')} ${failed}${coverageText}`;
      }
    }
    updateSimilarMethodAvailability();
  } catch {
    state.aiRunning = false;
    state.aiAutoEnabled = false;
    state.aiRuntime = 'unknown';
    updateAiToggleButton();
    updateRuntimeIndicator(els.aiEmbedRuntime, state.aiRuntime);
    if (els.aiStatus) els.aiStatus.textContent = `${tr('status_ai_prefix')}: ${tr('status_dash')}`;
    updateSimilarMethodAvailability();
  }
  // Poll mens der kører noget
  try {
    const r2 = await fetch('/api/ai/status');
    const s2 = await r2.json();
    if (s2 && s2.running) setTimeout(pollAiStatus, 1200);
  } catch {}
}

async function pollAiDescribeStatus() {
  try {
    const r = await fetch('/api/ai/describe/status');
    const s = await r.json();
    state.aiDescribeRunning = !!(s && s.ok && s.running);
    state.aiDescribeStopping = !!(s && s.ok && s.stopping);
    if (!state.aiDescribeStopping) state.aiDescribeForceStopPending = false;
    state.aiDescribeAutoEnabled = !!(s && s.ok && s.auto_ingest);
    state.aiDescribeModel = normalizeAiDescribeModel(s && s.model);
    if (s && s.external) applyAiExternalSettings(s.external);
    state.aiDescribeRuntime = String((s && s.runtime && (s.runtime.describe || s.runtime.ai)) || state.aiRuntime || 'unknown');
    updateAiDescribeModelSelect();
    updateAiDescribeToggleButton();
    updateRuntimeIndicator(els.aiDescribeRuntime, state.aiDescribeRuntime);
    if (els.aiDescribeStatus) {
      if (!s || !s.ok) {
        els.aiDescribeStatus.textContent = `${tr('status_ai_desc_prefix')}: ${tr('status_dash')}`;
      } else {
        const run = s.stopping ? tr('status_stopping') : (s.running ? tr('status_running') : tr('status_stopped'));
        const source = (!s.running && s.last) ? s.last : s;
        const described = Number(source && source.described) || 0;
        const total = Number(source && source.total) || 0;
        const failed = Number(source && source.failed) || 0;
        if (state.aiDescExternalEnabled) {
          const pending = Number(state.aiDescExternalPending || 0);
          const extTotal = Number(state.aiDescExternalTotal || total || 0);
          const extDone = Number(state.aiDescExternalDescribed || described || 0);
          els.aiDescribeStatus.textContent = `${tr('status_ai_desc_prefix')}: ${tr('ai_desc_external_enabled')} · ${tr('ai_desc_external_pending_label')} ${pending} · ${tr('status_described_label')} ${extDone}/${extTotal}`;
        } else {
          const modelLabel = (state.aiDescribeModel === 'qwen') ? tr('ai_desc_model_qwen') : tr('ai_desc_model_light');
          els.aiDescribeStatus.textContent = `${tr('status_ai_desc_prefix')}: ${run} · ${tr('status_model_label')} ${modelLabel} · ${tr('status_described_label')} ${described}/${total} · ${tr('status_errors_label')} ${failed}`;
        }
      }
    }
  } catch {
    state.aiDescribeRunning = false;
    state.aiDescribeStopping = false;
    state.aiDescribeForceStopPending = false;
    state.aiDescribeAutoEnabled = false;
    state.aiDescribeRuntime = 'unknown';
    updateAiDescribeToggleButton();
    updateRuntimeIndicator(els.aiDescribeRuntime, state.aiDescribeRuntime);
    if (els.aiDescribeStatus) els.aiDescribeStatus.textContent = `${tr('status_ai_desc_prefix')}: ${tr('status_dash')}`;
  }
  try {
    const r2 = await fetch('/api/ai/describe/status');
    const s2 = await r2.json();
    if (s2 && s2.running) setTimeout(pollAiDescribeStatus, 1200);
  } catch {}
}

// Start med at vise status hvis noget kører allerede
pollAiStatus();
pollAiDescribeStatus();
pollFacesStatus();
updateScanButton();
els.toggleRawBtn.addEventListener("click", () => {
  const hidden = els.rawMeta.classList.toggle("hidden");
  els.toggleRawBtn.textContent = hidden ? tr('raw_meta_show') : tr('raw_meta_hide');
});
els.favoriteBtn.addEventListener("click", toggleFavorite);

// Date edit interactions
if (els.editDateBtn) {
  els.editDateBtn.addEventListener('click', () => {
    if (els.dateEditWrap) {
      els.dateEditWrap.classList.remove('hidden');
      els.dateEditWrap.classList.add('floating');
      // Position under the pencil button (viewport coordinates)
      try {
        const r = els.editDateBtn.getBoundingClientRect();
        const w = Math.min(420, Math.max(300, window.innerWidth - 24));
        let left = r.right - w;
        const margin = 12;
        if (left < margin) left = margin;
        if (left + w > window.innerWidth - margin) left = window.innerWidth - margin - w;
        els.dateEditWrap.style.width = w + 'px';
        els.dateEditWrap.style.left = left + 'px';
        els.dateEditWrap.style.top = (r.bottom + 8) + 'px';
        els.dateEditWrap.style.zIndex = '100000';
      } catch {}
    }
    try {
      const row = els.editDateBtn.closest('.detail-row');
      if (row) row.classList.add('popover-open');
    } catch {}
  });
}
if (els.dateCancelBtn) {
  els.dateCancelBtn.addEventListener('click', () => {
    if (els.dateEditWrap) { els.dateEditWrap.classList.add('hidden'); els.dateEditWrap.classList.remove('floating'); els.dateEditWrap.style.left=''; els.dateEditWrap.style.top=''; }
    try {
      const row = els.editDateBtn.closest('.detail-row');
      if (row) row.classList.remove('popover-open');
    } catch {}
  });
}
if (els.dateSaveBtn) {
  els.dateSaveBtn.addEventListener('click', async () => {
    if (!state.selectedId || !els.dateInput) return;
    const v = els.dateInput.value;
    if (!v) return;
    try {
      const res = await fetch(`/api/photos/${state.selectedId}/captured-at`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ captured_at: v })});
      const data = await res.json();
      if (!res.ok || !data.ok) { showStatus(data.error || tr('date_update_failed'), 'err'); return; }
      const item = data.item;
      const idx = state.items.findIndex(i => i.id === item.id);
      if (idx >= 0) state.items[idx] = item;
      showStatus(tr('date_updated'), 'ok');
      renderGrid();
      setDetail(item);
      if (els.dateEditWrap) { els.dateEditWrap.classList.add('hidden'); els.dateEditWrap.classList.remove('floating'); els.dateEditWrap.style.left=''; els.dateEditWrap.style.top=''; }
      try {
        const row = els.editDateBtn.closest('.detail-row');
        if (row) row.classList.remove('popover-open');
      } catch {}
    } catch (e) {
      showStatus(tr('update_error'), 'err');
    }
  });
}

function selectedWeatherItem() {
  const sid = Number(state.selectedId || 0);
  if (!sid) return null;
  return (state.items || []).find(i => Number(i.id) === sid) || null;
}

if (els.detailWeatherBtn) {
  els.detailWeatherBtn.addEventListener('click', async () => {
    const item = selectedWeatherItem();
    if (item) await fetchWeatherForItem(item, { force: true, silent: false });
  });
}

if (els.viWeatherBtn) {
  els.viWeatherBtn.addEventListener('click', async () => {
    let item = selectedWeatherItem();
    try {
      const viewerItems = getViewerItems();
      item = viewerItems[state.selectedIndex] || item;
    } catch {}
    if (item) await fetchWeatherForItem(item, { force: true, silent: false });
  });
}

// --- GPS editor (MapLibre) ---
let gpsMap = null;
let gpsMarker = null;
let gpsLat = null;
let gpsLon = null;
let gpsPrevParent = null;
let gpsPrevNext = null;
let gpsBackdrop = null;
let gpsEarthOn = true;
let gpsSearchTimer = null;

function initGpsMap(item) {
  if (!els.gpsMapEl) return;
  if (typeof window.maplibregl === 'undefined') {
    if (els.gpsCoordText) els.gpsCoordText.textContent = 'Kunne ikke indlaese kort.';
    return;
  }
  if (!gpsMap) {
    gpsMap = new maplibregl.Map({
      container: els.gpsMapEl,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      center: [10,56], zoom: 4, attributionControl: false,
    });
    gpsMap.addControl(new maplibregl.NavigationControl({ showCompass:false }), 'top-right');
    gpsMap.on('click', (e)=> setGpsPoint(e.lngLat.lng, e.lngLat.lat));
    try { gpsMap.on('load', ()=> { gpsMap.getCanvas().style.cursor='crosshair'; }); } catch{}
  }
  ensureEarthLayer();
  ensurePickLayer();
  try { if (gpsMap.getLayer('esri')) gpsMap.setLayoutProperty('esri','visibility', gpsEarthOn ? 'visible' : 'none'); } catch{}
  applySatelliteLabelMode();
  if (item && item.gps_lon != null && item.gps_lat != null) {
    setGpsPoint(Number(item.gps_lon), Number(item.gps_lat), { fly:true });
  } else {
    if (gpsMarker) { gpsMarker.remove(); gpsMarker=null; }
    gpsLat=gpsLon=null;
    if (els.gpsCoordText) els.gpsCoordText.textContent = 'Klik på kortet for at vælge';
    try { gpsMap.jumpTo({ center:[10,56], zoom:4 }); } catch {}
  }
}
function ensureEarthLayer(){
  if (!gpsMap) return;
  const add = ()=>{
    try {
      if (!gpsMap.getSource('esri')) {
        gpsMap.addSource('esri', { type:'raster', tiles:['https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'], tileSize:256, attribution:'Esri' });
      }
      if (!gpsMap.getLayer('esri')) {
        // Insert raster below first symbol (labels) layer so labels stay on top
        let beforeId = null;
        try {
          const layers = gpsMap.getStyle().layers || [];
          for (const lyr of layers) { if (lyr.type === 'symbol') { beforeId = lyr.id; break; } }
        } catch {}
        gpsMap.addLayer({ id:'esri', type:'raster', source:'esri', layout:{ visibility: gpsEarthOn ? 'visible' : 'none' } }, beforeId || undefined);
      } else {
        gpsMap.setLayoutProperty('esri','visibility', gpsEarthOn ? 'visible' : 'none');
      }
      applySatelliteLabelMode();
    } catch(e){}
  };
  try { if (gpsMap.isStyleLoaded()) add(); else gpsMap.once('load', add); } catch { add(); }
}

// Keep only labels (symbol layers) above satellite and make text black
function applySatelliteLabelMode(){
  if (!gpsMap) return;
  try {
    const style = gpsMap.getStyle(); if (!style || !style.layers) return;
    let hasEarthLayer = false;
    try { hasEarthLayer = !!gpsMap.getLayer('esri'); } catch {}
    const useSatellite = !!gpsEarthOn && hasEarthLayer;
    for (const lyr of style.layers) {
      const id = lyr.id; const tp = lyr.type;
      if (id === 'pickCircle') {
        try { gpsMap.setLayoutProperty(id, 'visibility', 'visible'); } catch {}
        continue;
      }
      if (id === 'esri') {
        try { gpsMap.setLayoutProperty(id, 'visibility', useSatellite ? 'visible' : 'none'); } catch {}
        continue;
      }
      if (tp && tp !== 'symbol') {
        try { gpsMap.setLayoutProperty(id, 'visibility', useSatellite ? 'none' : 'visible'); } catch {}
      } else if (tp === 'symbol') {
        try { gpsMap.setLayoutProperty(id, 'visibility', 'visible'); } catch {}
        if (useSatellite) {
          try { gpsMap.setPaintProperty(id, 'text-color', '#000000'); } catch {}
          try { gpsMap.setPaintProperty(id, 'text-halo-color', '#ffffff'); } catch {}
          try { gpsMap.setPaintProperty(id, 'text-halo-width', 0.8); } catch {}
        }
      }
    }
  } catch {}
}
function setGpsPoint(lon, lat, opts={}){
  gpsLat=lat; gpsLon=lon;
  if (els.gpsCoordText) els.gpsCoordText.textContent = `${lat.toFixed(6)}, ${lon.toFixed(6)}`;
  // Update circle layer data for precise rendering (no DOM transform issues)
  try {
    const src = gpsMap.getSource('pick');
    if (src) {
      src.setData({ type:'FeatureCollection', features:[{ type:'Feature', geometry:{ type:'Point', coordinates:[lon,lat] } }] });
    }
  } catch {}
  // Tilføj eller flyt markør på kortet
  try {
    if (gpsMarker) { gpsMarker.remove(); gpsMarker = null; }
    gpsMarker = new maplibregl.Marker({ color: '#d00', draggable: false })
      .setLngLat([lon, lat])
      .addTo(gpsMap);
  } catch {}
  if (opts.fly) { try { gpsMap.jumpTo({ center:[lon,lat], zoom:11 }); } catch {} }
}
if (els.editGpsBtn) {
  els.editGpsBtn.addEventListener('click', async () => {
    // Safety: remove any stray backdrops before opening
    try { document.querySelectorAll('.modal-backdrop[data-ephemeral="1"]').forEach(el=>{ if(el.parentElement) el.parentElement.removeChild(el); }); } catch{}
    if (els.gpsEditWrap) {
      // Reparent to body and show centered modal with backdrop
      try { gpsPrevParent = els.gpsEditWrap.parentElement; gpsPrevNext = els.gpsEditWrap.nextElementSibling; document.body.appendChild(els.gpsEditWrap); } catch {}
      if (!gpsBackdrop) {
        gpsBackdrop = document.createElement('div');
        gpsBackdrop.className = 'modal-backdrop';
        gpsBackdrop.setAttribute('data-ephemeral', '1');
        gpsBackdrop.addEventListener('click', (e)=> { if (e.target === gpsBackdrop && els.gpsCancelBtn) els.gpsCancelBtn.click(); });
      }
      document.body.appendChild(gpsBackdrop);
      // place modal inside backdrop (centered via flex)
      gpsBackdrop.appendChild(els.gpsEditWrap);
      els.gpsEditWrap.classList.remove('hidden');
      els.gpsEditWrap.classList.add('gps-modal');
      gpsBackdrop.classList.add('active');
      const mapReady = await ensureMaplibre();
      if (!mapReady || typeof window.maplibregl === 'undefined') {
        if (els.gpsCoordText) els.gpsCoordText.textContent = 'Kunne ikke indlaese kort.';
        return;
      }
      const item = state.items.find(i => i.id === state.selectedId);
      initGpsMap(item);
      // Ensure correct size/transform after showing modal (fixes wrong click coords)
      try {
        if (gpsMap) {
          // resize now and on next frame
          gpsMap.resize();
          requestAnimationFrame(()=>{ try { gpsMap.resize(); } catch{} });
        }
      } catch {}
    }
  });
}
if (els.gpsCancelBtn) {
  els.gpsCancelBtn.addEventListener('click', ()=>{
    if (els.gpsEditWrap) { els.gpsEditWrap.classList.add('hidden'); els.gpsEditWrap.classList.remove('floating'); els.gpsEditWrap.classList.remove('gps-modal');
      try { if (gpsPrevParent) { if (gpsPrevNext) gpsPrevParent.insertBefore(els.gpsEditWrap, gpsPrevNext); else gpsPrevParent.appendChild(els.gpsEditWrap); } } catch {}
      try { if (gpsBackdrop) gpsBackdrop.classList.remove('active'); } catch{}
      try { if (gpsBackdrop && gpsBackdrop.parentElement) gpsBackdrop.parentElement.removeChild(gpsBackdrop); } catch{}
      gpsBackdrop = null;
    }
  });
}
if (els.gpsSaveBtn) {
  els.gpsSaveBtn.addEventListener('click', async ()=>{
    if (!state.selectedId || gpsLat==null || gpsLon==null) return;
    try {
      const res = await fetch(`/api/photos/${state.selectedId}/gps`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ lat: gpsLat, lon: gpsLon })});
      const data = await res.json();
      if (!res.ok || !data.ok) { showStatus(data.error || tr('gps_update_failed'), 'err'); return; }
      const item = data.item; const idx = state.items.findIndex(i => i.id === item.id); if (idx>=0) state.items[idx]=item;
      showStatus(tr('gps_updated'), 'ok'); renderGrid(); setDetail(item);
      if (els.gpsEditWrap) { els.gpsEditWrap.classList.add('hidden'); els.gpsEditWrap.classList.remove('floating'); els.gpsEditWrap.classList.remove('gps-modal');
        try { if (gpsPrevParent) { if (gpsPrevNext) gpsPrevParent.insertBefore(els.gpsEditWrap, gpsPrevNext); else gpsPrevParent.appendChild(els.gpsEditWrap); } } catch {}
        try { if (gpsBackdrop) gpsBackdrop.classList.remove('active'); } catch{}
        try { if (gpsBackdrop && gpsBackdrop.parentElement) gpsBackdrop.parentElement.removeChild(gpsBackdrop); } catch{}
        gpsBackdrop = null;
      }
    } catch(e){ showStatus(tr('update_error'), 'err'); }
  });
}

function ensurePickLayer(){
  if (!gpsMap) return;
  const add = ()=>{
    try {
      if (!gpsMap.getSource('pick')) {
        gpsMap.addSource('pick', { type:'geojson', data:{ type:'FeatureCollection', features:[] } });
      }
      if (!gpsMap.getLayer('pickCircle')) {
        gpsMap.addLayer({ id:'pickCircle', type:'circle', source:'pick', paint: { 'circle-radius': 6, 'circle-color':'#5b8cff', 'circle-stroke-color':'#ffffff', 'circle-stroke-width': 2 } });
      }
    } catch(e){}
  };
  try { if (gpsMap.isStyleLoaded()) add(); else gpsMap.once('load', add); } catch { add(); }
}

// --- Address search (Nominatim) ---
async function searchAddress(q){
  q = (q || '').trim();
  if (!els.gpsSearchList) return;
  if (!q) { els.gpsSearchList.classList.add('hidden'); els.gpsSearchList.innerHTML=''; return; }
  try{
    const url = `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=5&accept-language=da&q=${encodeURIComponent(q)}`;
    const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
    const data = await res.json();
    if (!Array.isArray(data)) { els.gpsSearchList.classList.add('hidden'); return; }
    const html = data.map(r=>`<div class="gps-result-item" data-lat="${r.lat}" data-lon="${r.lon}">${(r.display_name||'').replaceAll('<','&lt;')}</div>`).join('');
    els.gpsSearchList.innerHTML = html || '<div class="gps-result-item">Ingen resultater</div>';
    els.gpsSearchList.classList.remove('hidden');
    els.gpsSearchList.querySelectorAll('.gps-result-item').forEach(it=>{
      it.addEventListener('click', ()=>{
        const lat = parseFloat(it.getAttribute('data-lat'));
        const lon = parseFloat(it.getAttribute('data-lon'));
        setGpsPoint(lon, lat, { fly:true });
        els.gpsSearchList.classList.add('hidden');
      });
    });
  } catch{
    els.gpsSearchList.classList.add('hidden');
  }
}

if (els.gpsSearchInput){
  els.gpsSearchInput.addEventListener('input', ()=>{
    const q = els.gpsSearchInput.value;
    if (gpsSearchTimer) clearTimeout(gpsSearchTimer);
    gpsSearchTimer = setTimeout(()=> searchAddress(q), 350);
  });
}
// Earth overlay toggle
if (els.gpsEarthBtn) {
  els.gpsEarthBtn.addEventListener('click', ()=>{
    gpsEarthOn = !gpsEarthOn;
    if (els.gpsEarthBtn) els.gpsEarthBtn.classList.toggle('toggled', gpsEarthOn);
    ensureEarthLayer();
    try { if (gpsMap && gpsMap.getLayer('esri')) gpsMap.setLayoutProperty('esri','visibility', gpsEarthOn?'visible':'none'); } catch{}
  });
}

document.querySelectorAll(".nav-item").forEach(btn => {
  btn.addEventListener("click", async () => {
    const targetView = btn.dataset.view;
    if (targetView === 'mapper') {
      state.mapperPath = '';
      state.folder = null;
    }
    await setView(targetView);
    // Close drawer on mobile nav selection
    document.body.classList.remove("drawer-open");
  });
});

if (els.profileLink) {
  els.profileLink.addEventListener('click', async (e) => {
    e.preventDefault();
    await renderProfilePanel();
    openProfileModal();
    document.body.classList.remove('drawer-open');
  });
}

if (els.mobileNavItems && els.mobileNavItems.length) {
  els.mobileNavItems.forEach((btn) => {
    btn.addEventListener('click', async () => {
      const action = btn.dataset.mobileAction;
      if (action === 'navigate') {
        if (document.body.classList.contains('drawer-open')) closeDrawer();
        else openDrawer();
        return;
      }
      if (action === 'uploads') {
        ensureUploadMonitorRefs();
        const hidden = !els.uploadMonitor || els.uploadMonitor.classList.contains('hidden');
        if (hidden) {
          uploadUiState.collapsed = false;
          showUploadMonitor();
        } else {
          // Toggle detaljer: ét tryk minimerer/udfolder
          els.uploadMonitor.classList.toggle('collapsed');
        }
        return;
      }
      if (action === 'profile') {
        await renderProfilePanel();
        openProfileModal();
        closeDrawer();
        return;
      }
      if (action === 'view' && btn.dataset.view) {
        if (btn.dataset.view === 'mapper') {
          state.mapperPath = '';
          state.folder = null;
        }
        await setView(btn.dataset.view);
        closeDrawer();
      }
    });
  });
}

if (els.profileModalClose) {
  els.profileModalClose.addEventListener('click', closeProfileModal);
}
if (els.profileModal) {
  els.profileModal.addEventListener('click', (e) => {
    if (e.target === els.profileModal) closeProfileModal();
  });
}
if (els.twofaModalClose) {
  els.twofaModalClose.addEventListener('click', closeTwofaModal);
}
if (els.twofaModal) {
  els.twofaModal.addEventListener('click', (e) => {
    if (e.target === els.twofaModal) closeTwofaModal();
  });
}
if (els.mapperCreateModalClose) {
  els.mapperCreateModalClose.addEventListener('click', () => closeMapperCreateModal());
}
if (els.mapperCreateModalCancel) {
  els.mapperCreateModalCancel.addEventListener('click', () => closeMapperCreateModal());
}
if (els.mapperCreateModalConfirm) {
  els.mapperCreateModalConfirm.addEventListener('click', async () => {
    await submitMapperFolderModal();
  });
}
if (els.mapperCreateModalInput) {
  els.mapperCreateModalInput.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      await submitMapperFolderModal();
      return;
    }
    if (e.key === 'Escape') {
      e.preventDefault();
      closeMapperCreateModal();
    }
  });
}
if (els.mapperCreateModal) {
  els.mapperCreateModal.addEventListener('click', (e) => {
    if (e.target === els.mapperCreateModal) closeMapperCreateModal();
  });
}
if (els.mapperSharePasswordToggle) {
  els.mapperSharePasswordToggle.addEventListener('change', _syncMapperSharePasswordVisibility);
}
if (els.mapperShareModalClose) {
  els.mapperShareModalClose.addEventListener('click', () => closeMapperShareModal());
}
if (els.mapperShareModalCancel) {
  els.mapperShareModalCancel.addEventListener('click', () => closeMapperShareModal());
}
if (els.mapperShareModalConfirm) {
  els.mapperShareModalConfirm.addEventListener('click', async () => {
    await createMapperShareLink();
  });
}
if (els.mapperShareCopyBtn) {
  els.mapperShareCopyBtn.addEventListener('click', async () => {
    await copyMapperShareLink();
  });
}
if (els.mapperShareModal) {
  els.mapperShareModal.addEventListener('click', (e) => {
    if (e.target === els.mapperShareModal) closeMapperShareModal();
  });
}
if (els.sharedEditNeverToggle) {
  els.sharedEditNeverToggle.addEventListener('change', _syncSharedEditNeverToggle);
}
if (els.sharedEditPasswordToggle) {
  els.sharedEditPasswordToggle.addEventListener('change', _syncSharedEditPasswordToggle);
}
if (els.sharedEditModalClose) {
  els.sharedEditModalClose.addEventListener('click', closeSharedEditModal);
}
if (els.sharedEditModalCancel) {
  els.sharedEditModalCancel.addEventListener('click', closeSharedEditModal);
}
if (els.sharedEditModalSave) {
  els.sharedEditModalSave.addEventListener('click', async () => {
    await saveSharedEditModal();
  });
}
if (els.sharedEditModal) {
  els.sharedEditModal.addEventListener('click', (e) => {
    if (e.target === els.sharedEditModal) closeSharedEditModal();
  });
}

if (els.scanModalClose) {
  els.scanModalClose.addEventListener('click', closeScanModal);
}
if (els.scanModalCancel) {
  els.scanModalCancel.addEventListener('click', closeScanModal);
}
if (els.scanModalStart) {
  els.scanModalStart.addEventListener('click', async () => {
    closeScanModal();
    await scanLibrary();
  });
}
if (els.scanModal) {
  els.scanModal.addEventListener('click', (e) => {
    if (e.target === els.scanModal) closeScanModal();
  });
}
if (els.aiScopeModalClose) {
  els.aiScopeModalClose.addEventListener('click', closeAiScopeModal);
}
if (els.aiScopeModalCancel) {
  els.aiScopeModalCancel.addEventListener('click', closeAiScopeModal);
}
if (els.aiScopeModalNew) {
  els.aiScopeModalNew.addEventListener('click', async () => {
    const feature = state.aiScopePendingFeature;
    const pendingModel = state.aiDescribePendingModel;
    closeAiScopeModal();
    if (feature === 'faces') {
      await startFacesIndex('new');
    } else if (feature === 'describe_model') {
      await setAiDescribeModel(pendingModel, 'new');
    } else if (feature === 'describe') {
      await startAiDescribeIngest('new');
    } else {
      await startAiIngest('new');
    }
  });
}
if (els.aiScopeModalAll) {
  els.aiScopeModalAll.addEventListener('click', async () => {
    const feature = state.aiScopePendingFeature;
    const pendingModel = state.aiDescribePendingModel;
    closeAiScopeModal();
    if (feature === 'faces') {
      await startFacesIndex('all');
    } else if (feature === 'describe_model') {
      await setAiDescribeModel(pendingModel, 'all');
    } else if (feature === 'describe') {
      await startAiDescribeIngest('all');
    } else {
      await startAiIngest('all');
    }
  });
}
if (els.aiScopeModal) {
  els.aiScopeModal.addEventListener('click', (e) => {
    if (e.target === els.aiScopeModal) closeAiScopeModal();
  });
}
if (els.aiExternalModalClose) {
  els.aiExternalModalClose.addEventListener('click', closeAiExternalModal);
}
if (els.aiExternalModalCancel) {
  els.aiExternalModalCancel.addEventListener('click', closeAiExternalModal);
}
if (els.aiExternalModal) {
  els.aiExternalModal.addEventListener('click', (e) => {
    if (e.target === els.aiExternalModal) closeAiExternalModal();
  });
}
if (els.aiExternalModalSave) {
  els.aiExternalModalSave.addEventListener('click', async () => {
    const folders = collectAiExternalFoldersFromModal();
    await saveAiExternalSettings({ enabled: true, folders });
  });
}
if (els.aiExternalRotateTokenBtn) {
  els.aiExternalRotateTokenBtn.addEventListener('click', async () => {
    const folders = collectAiExternalFoldersFromModal();
    await saveAiExternalSettings({ enabled: !!state.aiDescExternalEnabled, folders, rotateToken: true });
  });
}
if (els.aiExternalCopyTokenBtn) {
  els.aiExternalCopyTokenBtn.addEventListener('click', copyAiExternalToken);
}
if (els.aiExternalLinksBtn) {
  els.aiExternalLinksBtn.addEventListener('click', async () => {
    await loadAiExternalLinks({ openModal: true });
  });
}
if (els.aiExternalLinksModalClose) {
  els.aiExternalLinksModalClose.addEventListener('click', () => els.aiExternalLinksModal && els.aiExternalLinksModal.classList.add('hidden'));
}
if (els.aiExternalLinksModalDone) {
  els.aiExternalLinksModalDone.addEventListener('click', () => els.aiExternalLinksModal && els.aiExternalLinksModal.classList.add('hidden'));
}
if (els.aiExternalLinksModal) {
  els.aiExternalLinksModal.addEventListener('click', (e) => {
    if (e.target === els.aiExternalLinksModal) els.aiExternalLinksModal.classList.add('hidden');
  });
}
if (els.aiExternalLinksList) {
  els.aiExternalLinksList.addEventListener('click', async (e) => {
    const copyBtn = e.target.closest('[data-ai-external-link-copy]');
    if (copyBtn) {
      const id = String(copyBtn.getAttribute('data-ai-external-link-copy') || '').trim();
      const link = (state.aiDescExternalLinks || []).find((item) => String(item.id || '') === id);
      await copyAiExternalText(link ? normalizeAiExternalLinkForDisplay(link.connection_url) : '', (message, kind) => showAiExternalLinksStatus(message, kind));
      return;
    }
    const deleteBtn = e.target.closest('[data-ai-external-link-delete]');
    if (deleteBtn) {
      await deleteAiExternalLink(deleteBtn.getAttribute('data-ai-external-link-delete'));
    }
  });
}

// Settings tabs switching
document.querySelectorAll('#settingsPanel .tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const tab = btn.dataset.tab;
    state.settingsTab = _normalizeSettingsTab(tab) || 'maint';
    // activate button
    document.querySelectorAll('#settingsPanel .tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    // show panel
    document.querySelectorAll('#settingsPanel .tab-panel').forEach(p => {
      p.classList.toggle('hidden', p.dataset.tabpanel !== tab);
    });
    // lazy-load embedded admin panels
    if (tab === 'users') renderUsersPanel();
    if (tab === 'update') {
      loadAppUpdateStatus({ silent: true }).catch(() => {});
    }
    if (tab === 'ai') {
      loadAiPerformanceSettings();
      loadAiExternalSettings();
    }
    if (tab === 'upload_workflow') {
      loadUploadWorkflowSettings();
    }
    if (tab === 'file_types') {
      loadUploadFileTypeSettings();
    }
    if (tab === 'dns') {
      loadDnsSettings();
    }
    if (tab === 'shared') {
      loadDnsShares();
    }
    // Sync mobile selector when clicking desktop tabs
    try { const sel = document.getElementById('settingsTabSelect'); if (sel) sel.value = tab; } catch {}
    if (state.view === 'settings') _syncRouteStateToUrl();
  });
});

// Mobile tab selector → switch tab
(function(){
  const sel = document.getElementById('settingsTabSelect');
  if (!sel) return;
  sel.addEventListener('change', () => {
    try {
      const tab = sel.value;
      const btn = document.querySelector(`#settingsPanel .tab-btn[data-tab="${tab}"]`);
      if (btn) btn.click();
    } catch {}
  });
})();

if (els.dnsSaveBtn) {
  els.dnsSaveBtn.addEventListener('click', async () => {
    await saveDnsSettings();
  });
}
if (els.aiPerfSaveBtn) {
  els.aiPerfSaveBtn.addEventListener('click', async () => {
    await saveAiPerformanceSettings();
  });
}
if (els.uploadWorkflowSaveBtn) {
  els.uploadWorkflowSaveBtn.addEventListener('click', async () => {
    await saveUploadWorkflowSettings();
  });
}
if (els.fileTypeAddBtn) {
  els.fileTypeAddBtn.addEventListener('click', addUploadFileTypeFromInput);
}
if (els.fileTypeInput) {
  els.fileTypeInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addUploadFileTypeFromInput();
    }
  });
}
if (els.fileTypeResetBtn) {
  els.fileTypeResetBtn.addEventListener('click', () => {
    const data = state.uploadFileTypes || {};
    const defaults = Array.isArray(data.default_extensions) ? data.default_extensions.slice().sort() : [];
    if (!defaults.length) return;
    state.uploadFileTypes = { ...data, allowed_extensions: defaults };
    updateUploadFileTypeBlockedFromAllowed();
    showFileTypeStatus('');
    renderUploadFileTypeSettings();
  });
}
if (els.fileTypeSaveBtn) {
  els.fileTypeSaveBtn.addEventListener('click', async () => {
    await saveUploadFileTypeSettings();
  });
}
if (els.fileTypeAllowedList) {
  els.fileTypeAllowedList.addEventListener('click', (e) => {
    const btn = e.target && e.target.closest ? e.target.closest('[data-file-type-remove]') : null;
    if (!btn) return;
    const ext = normalizeUploadFileExtension(btn.getAttribute('data-file-type-remove'));
    if (!ext || !state.uploadFileTypes) return;
    const allowed = (state.uploadFileTypes.allowed_extensions || []).filter((item) => item !== ext);
    state.uploadFileTypes = { ...state.uploadFileTypes, allowed_extensions: allowed };
    updateUploadFileTypeBlockedFromAllowed();
    showFileTypeStatus('');
    renderUploadFileTypeSettings();
  });
}
if (els.appUpdateCheckBtn) {
  els.appUpdateCheckBtn.addEventListener('click', async () => {
    await checkAppUpdate();
  });
}
if (els.appUpdateStartBtn) {
  els.appUpdateStartBtn.addEventListener('click', async () => {
    await startAppUpdate();
  });
}
if (els.appUpdateChoiceCleanupBtn) {
  els.appUpdateChoiceCleanupBtn.addEventListener('click', () => {
    closeAppUpdateChoiceModal(true);
  });
}
if (els.appUpdateChoiceFastBtn) {
  els.appUpdateChoiceFastBtn.addEventListener('click', () => {
    closeAppUpdateChoiceModal(false);
  });
}
if (els.appUpdateChoiceClose) {
  els.appUpdateChoiceClose.addEventListener('click', () => {
    closeAppUpdateChoiceModal(null);
  });
}
if (els.appUpdateChoiceModal) {
  els.appUpdateChoiceModal.addEventListener('click', (e) => {
    if (e.target === els.appUpdateChoiceModal || (e.target && e.target.classList && e.target.classList.contains('modal-backdrop'))) {
      closeAppUpdateChoiceModal(null);
    }
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !els.appUpdateChoiceModal.classList.contains('hidden')) {
      closeAppUpdateChoiceModal(null);
    }
  });
}
if (els.appUpdateAutoCheckToggle) {
  els.appUpdateAutoCheckToggle.addEventListener('change', () => {
    const nextState = { ...(state.appUpdate || {}), auto_check_enabled: !!els.appUpdateAutoCheckToggle.checked };
    applyAppUpdateSettingsUi(nextState);
    renderAppUpdateTabBadge(nextState);
  });
}
if (els.appUpdateSettingsSaveBtn) {
  els.appUpdateSettingsSaveBtn.addEventListener('click', async () => {
    await saveAppUpdateSettings();
  });
}
if (els.aiPerfPresetLow) {
  els.aiPerfPresetLow.addEventListener('click', async () => {
    applyAiPerfPreset('low');
    await saveAiPerformanceSettings();
  });
}
if (els.aiPerfPresetNormal) {
  els.aiPerfPresetNormal.addEventListener('click', async () => {
    applyAiPerfPreset('normal');
    await saveAiPerformanceSettings();
  });
}
if (els.aiPerfPresetFast) {
  els.aiPerfPresetFast.addEventListener('click', async () => {
    applyAiPerfPreset('fast');
    await saveAiPerformanceSettings();
  });
}
if (els.sharedLinksList) {
  els.sharedLinksList.addEventListener('click', async (e) => {
    const target = e.target;
    if (!(target instanceof HTMLElement)) return;
    const copyId = Number(target.getAttribute('data-share-copy') || 0) || 0;
    if (copyId > 0) {
      const item = Array.isArray(state.sharedLinks) ? state.sharedLinks.find((s) => Number(s.id || 0) === copyId) : null;
      await _copySharedLink(item && item.link ? String(item.link) : '');
      return;
    }
    const qrId = Number(target.getAttribute('data-share-qr') || 0) || 0;
    if (qrId > 0) {
      const item = Array.isArray(state.sharedLinks) ? state.sharedLinks.find((s) => Number(s.id || 0) === qrId) : null;
      const link = item && item.link ? String(item.link) : '';
      if (link) await _downloadQrForLink(link, `share-${qrId}-qr.png`);
      return;
    }
    const editId = Number(target.getAttribute('data-share-edit') || 0) || 0;
    if (editId > 0) {
      await openSharedEditModal(editId);
      return;
    }
    const revokeId = Number(target.getAttribute('data-share-revoke') || 0) || 0;
    if (revokeId > 0) {
      await revokeDnsShare(revokeId);
      return;
    }
    const activateId = Number(target.getAttribute('data-share-activate') || 0) || 0;
    if (activateId > 0) {
      await activateDnsShare(activateId);
      return;
    }
    const extendId = Number(target.getAttribute('data-share-extend') || 0) || 0;
    if (extendId > 0) {
      await extendDnsShare(extendId);
      return;
    }
    const deleteId = Number(target.getAttribute('data-share-delete') || 0) || 0;
    if (deleteId > 0) {
      await deleteDnsShare(deleteId);
    }
  });
}

els.mapperDeleteBtn && els.mapperDeleteBtn.addEventListener('click', deleteSelectedInMapper);
els.mapperSelectAllBtn && els.mapperSelectAllBtn.addEventListener('click', mapperSelectAll);
els.mapperClearBtn && els.mapperClearBtn.addEventListener('click', mapperClearSelection);
els.mapperDownloadBtn && els.mapperDownloadBtn.addEventListener('click', openDownloadModal);
els.mapperDownloadModalClose && els.mapperDownloadModalClose.addEventListener('click', closeDownloadModal);
els.downloadConvertedBtn && els.downloadConvertedBtn.addEventListener('click', ()=>{ closeDownloadModal(); runMapperDownload('converted'); });
els.downloadOriginalBtn && els.downloadOriginalBtn.addEventListener('click', ()=>{ closeDownloadModal(); runMapperDownload('original'); });
if (els.downloadTopStatusCancel) {
  els.downloadTopStatusCancel.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    cancelActiveMapperDownload();
  });
}
if (els.mapperDownloadModal) {
  els.mapperDownloadModal.addEventListener('click', (e) => {
    const t = e && e.target;
    if (t === els.mapperDownloadModal) { closeDownloadModal(); return; }
    if (t && t.classList && t.classList.contains('modal-backdrop')) closeDownloadModal();
  });
}
document.addEventListener('keydown', (e) => {
  if (!e || e.key !== 'Escape') return;
  if (els.sharedEditModal && !els.sharedEditModal.classList.contains('hidden')) {
    closeSharedEditModal();
    return;
  }
  if (els.similarModal && !els.similarModal.classList.contains('hidden')) {
    closeSimilarModal();
    return;
  }
  if (els.mapperDownloadModal && !els.mapperDownloadModal.classList.contains('hidden')) closeDownloadModal();
});
els.mapperCancelBtn && els.mapperCancelBtn.addEventListener('click', () => setMapperEditMode(false));
els.mapperUpBtn && els.mapperUpBtn.addEventListener('click', async () => {
  const cur = String(state.mapperPath || '');
  if (!cur) return;
  const parts = cur.split('/').filter(Boolean);
  parts.pop();
  const parent = parts.join('/');
  state.mapperPath = parent;
  state.folder = parent || null;
  renderMapperContext(parent);
  await loadMapperTools(parent);
  await loadPhotos();
});
if (els.mapperDropZone) {
  els.mapperDropZone.addEventListener('dragover', (e) => {
    if (state.view !== 'mapper') return;
    if (e.dataTransfer && e.dataTransfer.types && e.dataTransfer.types.includes('Files')) {
      e.preventDefault();
      els.mapperDropZone.classList.add('dragover');
    }
  });
  els.mapperDropZone.addEventListener('dragleave', () => {
    els.mapperDropZone.classList.remove('dragover');
  });
  els.mapperDropZone.addEventListener('drop', async (e) => {
    els.mapperDropZone.classList.remove('dragover');
    if (state.view !== 'mapper') return;
    if (!(e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length)) return;
    e.preventDefault();
    const targetSubdir = String(state.mapperPath || '');
    await uploadDroppedDataTransfer(e.dataTransfer, targetSubdir);
    await loadMapperTools(targetSubdir);
    await loadPhotos();
  });
}

if (els.mapperUploadInput) {
  els.mapperUploadInput.addEventListener('change', () => {
    const list = (els.mapperUploadInput && els.mapperUploadInput.files) ? els.mapperUploadInput.files : null;
    if (!list || !list.length) return;
    const targetSubdir = String(state.mapperPath || '');
    // Clone FileList immediately; iOS may keep the picker open until the handler returns.
    // Defer heavy work so the system UI can dismiss smoothly.
    const files = Array.from(list);
    window.setTimeout(() => {
      try {
        uploadFiles(files, { destination: 'uploads', subdir: targetSubdir });
      } catch (e) {
        console.error(e);
      }
    }, 50);
    // Clear value so the same files can be picked again later if needed
    els.mapperUploadInput.value = '';
  });
}

// viewer events
els.viewerClose && els.viewerClose.addEventListener("click", closeViewer);
els.viewerPrev && els.viewerPrev.addEventListener("click", () => nextViewer(-1));
els.viewerNext && els.viewerNext.addEventListener("click", () => nextViewer(1));

let viewerTouchStartX = null;
let viewerTouchStartY = null;
let viewerTouchStartTime = 0;
let viewerDragActive = false;
let viewerDragDx = 0;
let viewerSwipePreviewEl = null;
let viewerSwipePreviewIndex = -1;

function getViewerTargetIndex(step) {
  const n = getViewerItems().length;
  if (!n || state.selectedIndex < 0) return -1;
  return (state.selectedIndex + step + n) % n;
}

function removeViewerSwipePreview() {
  if (!viewerSwipePreviewEl) {
    viewerSwipePreviewIndex = -1;
    return;
  }
  try {
    if (viewerSwipePreviewEl.tagName === 'VIDEO') {
      try { viewerSwipePreviewEl.pause(); } catch (_) {}
      viewerSwipePreviewEl.removeAttribute('src');
    }
  } catch (_) {}
  try {
    if (viewerSwipePreviewEl.parentElement) viewerSwipePreviewEl.parentElement.removeChild(viewerSwipePreviewEl);
  } catch (_) {}
  viewerSwipePreviewEl = null;
  viewerSwipePreviewIndex = -1;
}

function ensureViewerSwipePreview(targetIndex) {
  if (!els.viewer || els.viewer.classList.contains('hidden')) return null;
  const items = getViewerItems();
  if (targetIndex < 0 || !items[targetIndex]) {
    removeViewerSwipePreview();
    return null;
  }
  if (viewerSwipePreviewEl && viewerSwipePreviewIndex === targetIndex) return viewerSwipePreviewEl;

  removeViewerSwipePreview();
  const it = items[targetIndex];
  if (!it || !it.original_url) return null;

  const node = it.is_video ? document.createElement('video') : document.createElement('img');
  if (it.is_video) {
    node.muted = true;
    node.playsInline = true;
    node.preload = 'metadata';
    node.src = it.original_url;
  } else {
    node.alt = '';
    node.src = it.original_url || it.thumb_url || '';
  }
  node.style.position = 'absolute';
  node.style.left = '0';
  node.style.top = '0';
  node.style.width = '100%';
  node.style.height = '100%';
  node.style.objectFit = 'contain';
  node.style.background = '#000';
  node.style.pointerEvents = 'none';
  node.style.zIndex = '1';
  node.style.opacity = '1';
  node.style.transform = 'translateX(0)';
  node.style.willChange = 'transform, opacity';

  els.viewer.insertBefore(node, els.viewer.firstChild || null);
  viewerSwipePreviewEl = node;
  viewerSwipePreviewIndex = targetIndex;
  return node;
}

function resetViewerTouchState() {
  viewerTouchStartX = null;
  viewerTouchStartY = null;
  viewerTouchStartTime = 0;
  viewerDragActive = false;
  viewerDragDx = 0;
}

function applyViewerDragTransform(dx) {
  const active = getActiveViewerMediaElement();
  if (!active) return;
  const w = Math.max(1, window.innerWidth || 1);
  const ratio = Math.min(1, Math.abs(dx) / w);
  const step = dx < 0 ? 1 : -1;
  const targetIndex = getViewerTargetIndex(step);
  const preview = ensureViewerSwipePreview(targetIndex);
  active.style.willChange = 'transform, opacity';
  active.style.transition = 'none';
  active.style.transform = `translateX(${Math.round(dx)}px)`;
  active.style.opacity = String(Math.max(0.72, 1 - ratio * 0.38));
  if (preview) {
    const offset = step > 0 ? w : -w;
    preview.style.transition = 'none';
    preview.style.transform = `translateX(${Math.round(dx + offset)}px)`;
    preview.style.opacity = '1';
  }
}

function animateViewerDragReset() {
  const active = getActiveViewerMediaElement();
  if (!active) return;
  active.style.willChange = 'transform, opacity';
  active.style.transition = 'transform 170ms ease, opacity 170ms ease';
  active.style.transform = 'translateX(0)';
  active.style.opacity = '1';
  if (viewerSwipePreviewEl) {
    const step = viewerDragDx < 0 ? 1 : -1;
    const w = Math.max(1, window.innerWidth || 1);
    const offset = step > 0 ? w : -w;
    viewerSwipePreviewEl.style.transition = 'transform 170ms ease, opacity 170ms ease';
    viewerSwipePreviewEl.style.transform = `translateX(${offset}px)`;
    viewerSwipePreviewEl.style.opacity = '1';
  }
  window.setTimeout(() => {
    cleanupViewerMediaAnimation();
    removeViewerSwipePreview();
    scheduleViewerInfoPosition();
  }, 190);
}

function commitViewerDragSwipe(step) {
  const items = getViewerItems();
  const targetIndex = getViewerTargetIndex(step);
  if (targetIndex < 0 || !items[targetIndex]) {
    animateViewerDragReset();
    return;
  }
  const active = getActiveViewerMediaElement();
  const preview = ensureViewerSwipePreview(targetIndex);
  if (!active || !preview) {
    state.selectedIndex = targetIndex;
    openViewer(targetIndex);
    removeViewerSwipePreview();
    scheduleViewerInfoPosition();
    viewerTransitionRunning = false;
    return;
  }

  const duration = 170;
  const w = Math.max(1, window.innerWidth || 1);
  const outX = step > 0 ? -w : w;
  active.style.willChange = 'transform, opacity';
  active.style.transition = `transform ${duration}ms ease, opacity ${duration}ms ease`;
  active.style.transform = `translateX(${outX}px)`;
  active.style.opacity = '0.25';

  preview.style.willChange = 'transform, opacity';
  preview.style.transition = `transform ${duration}ms ease, opacity ${duration}ms ease`;
  preview.style.transform = 'translateX(0)';
  preview.style.opacity = '1';

  window.setTimeout(() => {
    state.selectedIndex = targetIndex;
    removeViewerSwipePreview();
    openViewer(targetIndex);
    cleanupViewerMediaAnimation();
    scheduleViewerInfoPosition();
    viewerTransitionRunning = false;
    if (viewerPendingStep !== 0) {
      const pending = viewerPendingStep;
      viewerPendingStep = 0;
      nextViewer(pending);
    }
  }, duration + 25);
}

if (els.viewer) {
  els.viewer.addEventListener('touchstart', (e) => {
    if (!e.touches || e.touches.length !== 1) return;
    if (viewerTransitionRunning) return;
    const target = e.target;
    if (target && (target.closest('#viewerClose, #viewerInfoMediaBtn, #viewerMenuBtn, #viewerMenu, #viewerInfoBtn, #viewerPrev, #viewerNext, #viewerInfo, .btn, a'))) return;
    const t = e.touches[0];
    viewerTouchStartX = t.clientX;
    viewerTouchStartY = t.clientY;
    viewerTouchStartTime = Date.now();
    viewerDragActive = false;
    viewerDragDx = 0;
  }, { passive: true });

  els.viewer.addEventListener('touchmove', (e) => {
    if (viewerTouchStartX === null || viewerTouchStartY === null) return;
    if (!els.viewer || els.viewer.classList.contains('hidden')) return;
    if (viewerTransitionRunning) return;
    const t = e.touches && e.touches[0];
    if (!t) return;
    const dx = t.clientX - viewerTouchStartX;
    const dy = t.clientY - viewerTouchStartY;
    const absX = Math.abs(dx);
    const absY = Math.abs(dy);
    if (!viewerDragActive) {
      if (absX < 8 || absX <= absY * 1.1) return;
      viewerDragActive = true;
    }
    viewerDragDx = dx;
    applyViewerDragTransform(dx);
    e.preventDefault();
  }, { passive: false });

  els.viewer.addEventListener('touchend', (e) => {
    if (viewerTouchStartX === null || viewerTouchStartY === null) return;
    if (!els.viewer || els.viewer.classList.contains('hidden')) {
      resetViewerTouchState();
      return;
    }
    const changed = e.changedTouches && e.changedTouches[0];
    if (!changed) return;
    const dx = viewerDragActive ? viewerDragDx : (changed.clientX - viewerTouchStartX);
    const dy = changed.clientY - viewerTouchStartY;
    const dt = Date.now() - viewerTouchStartTime;
    const absX = Math.abs(dx);
    const absY = Math.abs(dy);
    const minSwipe = Math.max(52, Math.round((window.innerWidth || 320) * 0.16));
    const isHorizontalSwipe = absX >= minSwipe && absX > absY * 1.12 && dt <= 900;
    if (isHorizontalSwipe) {
      const step = dx < 0 ? 1 : -1;
      if (viewerDragActive) {
        viewerTransitionRunning = true;
        commitViewerDragSwipe(step);
      } else {
        nextViewer(step);
      }
    } else if (viewerDragActive) {
      animateViewerDragReset();
    }
    resetViewerTouchState();
  }, { passive: true });

  els.viewer.addEventListener('touchcancel', () => {
    if (viewerDragActive) animateViewerDragReset();
    resetViewerTouchState();
  }, { passive: true });
}

window.addEventListener("keydown", (e) => {
  if (!els.viewer || els.viewer.classList.contains("hidden")) return;
  if (e.key === "Escape") closeViewer();
  if (e.key === "ArrowLeft") nextViewer(-1);
  if (e.key === "ArrowRight") nextViewer(1);
});

// Keep compact-settings class in sync on resize
window.addEventListener('resize', () => {
  try {
    const isSmall = window.matchMedia('(max-width: 760px)').matches;
    if (document.body.classList.contains('view-settings')) {
      document.body.classList.toggle('compact-settings', isSmall);
    } else {
      document.body.classList.remove('compact-settings');
    }
    if (state.view === 'photoframe') {
      syncPhotoframePreviewHeights();
    }
  } catch {}
});

// Detail panel: luk med Escape og klik udenfor
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    try { document.body.classList.remove('detail-open'); } catch {}
  }
});
const __mainEl = document.querySelector('main.main');
if (__mainEl) {
  __mainEl.addEventListener('click', (e) => {
    if (!document.body.classList.contains('detail-open')) return;
    // Bevar åben hvis man klikker på info-ikon eller inde i panelet
    const t = e.target;
    if (t && (t.closest('.detail-panel') || t.closest('.info-icon-overlay'))) return;
    document.body.classList.remove('detail-open');
  });
}

// Close viewer when clicking the dark backdrop (outside media/content)
if (els.viewer) {
  els.viewer.addEventListener('click', (e) => {
    if (e.target === els.viewer) closeViewer();
  });
}

// Viewer Info toggle
const viPanel = document.getElementById('viewerInfo');
const viBtn = document.getElementById('viewerInfoBtn');
const viMediaBtn = els.viewerInfoMediaBtn || document.getElementById('viewerInfoMediaBtn');
const viewerMenu = els.viewerMenu;
const viewerMenuBtn = els.viewerMenuBtn;
const viewerMenuInfoBtn = els.viewerMenuInfoBtn;
const viewerInfoGrab = document.getElementById('viewerInfoGrab');
let viewerInfoHideTimer = null;
let viewerInfoDragActive = false;
let viewerInfoDragStartY = 0;
let viewerInfoDragDeltaY = 0;
let viewerInfoDragStartTime = 0;

function isMobileViewerLayout() {
  return window.matchMedia('(max-width: 760px)').matches;
}

function isViewerInfoPanelOpen() {
  return !!viPanel && viPanel.classList.contains('open') && !viPanel.classList.contains('hidden');
}

function resetViewerInfoDragState() {
  viewerInfoDragActive = false;
  viewerInfoDragStartY = 0;
  viewerInfoDragDeltaY = 0;
  viewerInfoDragStartTime = 0;
}

function setViewerInfoOpenLayout(open) {
  if (!els.viewer) return;
  els.viewer.classList.toggle('viewer-info-open', !!open && !isMobileViewerLayout());
}

function positionViewerInfoPanel() {
  if (!viPanel) return;
  if (isMobileViewerLayout()) {
    viPanel.style.left = '';
    viPanel.style.right = '';
    viPanel.style.top = '';
    viPanel.style.bottom = '';
    viPanel.style.height = '';
    return;
  }
  try {
    const r = getViewerMediaAnchorRect();
    if (!r) return;
    const w = viPanel.offsetWidth || 360;
    const underOffset = 8;
    const viewportPad = 16;
    const preferredVisibleLeft = Math.round(r.right - underOffset);
    const maxVisibleLeft = Math.max(viewportPad, Math.round(window.innerWidth - w - viewportPad));
    const visibleLeft = Math.min(preferredVisibleLeft, maxVisibleLeft);
    viPanel.style.left = `${Math.round(visibleLeft - w)}px`;
    viPanel.style.right = 'auto';
    const vPad = 16;
    const top = Math.max(0, Math.round(r.top + vPad));
    const bottomGap = Math.max(0, Math.round(window.innerHeight - (r.bottom - vPad)));
    viPanel.style.top = `${top}px`;
    viPanel.style.bottom = `${bottomGap}px`;
    viPanel.style.height = '';
  } catch {}
}

function positionViewerInfoTrigger() {
  if (!viMediaBtn) return;
  if (!els.viewer || els.viewer.classList.contains('hidden')) return;
  try {
    const r = getViewerMediaAnchorRect();
    if (!r) {
      viMediaBtn.style.left = isMobileViewerLayout() ? '10px' : '62px';
      viMediaBtn.style.top = isMobileViewerLayout() ? 'calc(env(safe-area-inset-top) + 10px)' : '12px';
      viMediaBtn.style.right = 'auto';
      return;
    }
    if (!Number.isFinite(r.left) || !Number.isFinite(r.right) || r.width <= 0 || r.height <= 0) return;

    const pad = isMobileViewerLayout() ? 10 : 8;
    viMediaBtn.style.left = `${Math.round(r.left + pad)}px`;
    viMediaBtn.style.top = `${Math.round(r.top + pad)}px`;
    viMediaBtn.style.right = 'auto';
  } catch {}
}

function toggleViewerInfoPanel(forceOpen = null) {
  if (!viPanel) return;
  if (viewerInfoHideTimer) {
    window.clearTimeout(viewerInfoHideTimer);
    viewerInfoHideTimer = null;
  }
  resetViewerInfoDragState();
  viPanel.style.transition = '';
  viPanel.style.transform = '';
  const shouldOpen = forceOpen === null ? !viPanel.classList.contains('open') : !!forceOpen;
  if (!shouldOpen) {
    setViewerInfoOpenLayout(false);
    viPanel.classList.remove('open');
    if (isMobileViewerLayout()) {
      viPanel.classList.add('hidden');
      viPanel.style.transition = '';
      viPanel.style.transform = '';
      return;
    }
    viewerInfoHideTimer = window.setTimeout(() => {
      viPanel.classList.add('hidden');
      viewerInfoHideTimer = null;
    }, isMobileViewerLayout() ? 260 : 220);
    return;
  }
  setViewerInfoOpenLayout(true);
  viPanel.classList.remove('hidden');
  try { void els.viewer.offsetWidth; } catch {}
  positionViewerInfoPanel();
  positionViewerInfoTrigger();
  void viPanel.offsetWidth;
  viPanel.classList.add('open');
  scheduleViewerInfoPosition();
}

if (viBtn && viPanel) {
  viBtn.addEventListener('click', () => toggleViewerInfoPanel());
}
if (viMediaBtn && viPanel) {
  viMediaBtn.addEventListener('click', (e) => {
    try { e.stopPropagation(); } catch {}
    toggleViewerInfoPanel();
  });
}

if (viewerMenuBtn && viewerMenu) {
  viewerMenuBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    viewerMenu.classList.toggle('hidden');
  });
}

if (viewerMenuInfoBtn) {
  viewerMenuInfoBtn.addEventListener('click', () => {
    if (viewerMenu) viewerMenu.classList.add('hidden');
    toggleViewerInfoPanel();
  });
}

if (viPanel) {
  viPanel.addEventListener('touchstart', (e) => {
    if (!isMobileViewerLayout() || !isViewerInfoPanelOpen()) return;
    if (!e.touches || e.touches.length !== 1) return;
    const touch = e.touches[0];
    const target = e.target;
    const fromGrab = !!(target && target.closest && target.closest('#viewerInfoGrab'));
    const panelTop = viPanel.getBoundingClientRect().top;
    const touchNearTop = (touch.clientY - panelTop) <= 72;
    const panelAtTop = (viPanel.scrollTop || 0) <= 0;
    if (!fromGrab && !(touchNearTop && panelAtTop)) return;

    viewerInfoDragActive = true;
    viewerInfoDragStartY = touch.clientY;
    viewerInfoDragDeltaY = 0;
    viewerInfoDragStartTime = Date.now();
    viPanel.style.transition = 'none';
  }, { passive: true });

  viPanel.addEventListener('touchmove', (e) => {
    if (!viewerInfoDragActive || !isMobileViewerLayout()) return;
    const touch = e.touches && e.touches[0];
    if (!touch) return;
    const delta = Math.max(0, touch.clientY - viewerInfoDragStartY);
    viewerInfoDragDeltaY = delta;
    viPanel.style.transform = `translateY(${Math.round(delta)}px)`;
    if (delta > 0) e.preventDefault();
  }, { passive: false });

  viPanel.addEventListener('touchend', () => {
    if (!viewerInfoDragActive || !isMobileViewerLayout()) {
      resetViewerInfoDragState();
      return;
    }
    const dt = Math.max(1, Date.now() - viewerInfoDragStartTime);
    const velocity = viewerInfoDragDeltaY / dt;
    const minSwipeDown = Math.max(90, Math.round((window.innerHeight || 640) * 0.12));
    const shouldClose = viewerInfoDragDeltaY >= minSwipeDown || velocity > 0.42;
    if (shouldClose) {
      viPanel.style.transition = '';
      viPanel.style.transform = '';
      resetViewerInfoDragState();
      toggleViewerInfoPanel(false);
      return;
    }
    viPanel.style.transition = 'transform .2s ease';
    viPanel.style.transform = 'translateY(0)';
    window.setTimeout(() => {
      if (isViewerInfoPanelOpen()) {
        viPanel.style.transition = '';
        viPanel.style.transform = '';
      }
    }, 210);
    resetViewerInfoDragState();
  }, { passive: true });

  viPanel.addEventListener('touchcancel', () => {
    if (!viewerInfoDragActive) return;
    viPanel.style.transition = '';
    viPanel.style.transform = '';
    resetViewerInfoDragState();
  }, { passive: true });
}

if (els.viewer && viPanel) {
  els.viewer.addEventListener('click', (e) => {
    if (!isMobileViewerLayout() || !isViewerInfoPanelOpen()) return;
    const target = e.target;
    if (target === els.viewerImg || target === els.viewerVideo) {
      toggleViewerInfoPanel(false);
    }
  });
}

if (els.viewer && viewerMenu) {
  els.viewer.addEventListener('click', (e) => {
    if (viewerMenu.classList.contains('hidden')) return;
    const target = e.target;
    if (target && (target.closest('#viewerMenu') || target.closest('#viewerMenuBtn'))) return;
    viewerMenu.classList.add('hidden');
  });
}
// Hide panel on close
const _origCloseViewer = closeViewer;
closeViewer = function(){
  try {
    if (viewerInfoHideTimer) {
      window.clearTimeout(viewerInfoHideTimer);
      viewerInfoHideTimer = null;
    }
    if (viPanel) {
      viPanel.classList.remove('open');
      viPanel.classList.add('hidden');
      viPanel.style.left = '';
      viPanel.style.right = '';
      viPanel.style.top = '';
      viPanel.style.bottom = '';
      viPanel.style.height = '';
      viPanel.style.transition = '';
      viPanel.style.transform = '';
      resetViewerInfoDragState();
    }
    setViewerInfoOpenLayout(false);
    if (viewerMenu) { viewerMenu.classList.add('hidden'); }
    cleanupViewerMediaAnimation();
    removeViewerSwipePreview();
    resetViewerTouchState();
    state.viewerItems = null;
  } catch {}
  _origCloseViewer();
}

// Keep the slide-out anchored to the media edge on resize
window.addEventListener('resize', ()=>{
  try {
    if (!els.viewer || els.viewer.classList.contains('hidden')) return;
    updateViewerLandscapeClass();
    setViewerInfoOpenLayout(isViewerInfoPanelOpen());
    positionViewerInfoPanel();
    positionViewerInfoTrigger();
  } catch {}
});

// Proxy edit buttons inside viewer to open the main editors
const viEditDateBtn = document.getElementById('viEditDateBtn');
if (viEditDateBtn) {
  viEditDateBtn.addEventListener('click', ()=>{ try { closeViewer(); } catch{}; try { els.editDateBtn && els.editDateBtn.click(); } catch{} });
}
const viEditGpsBtn = document.getElementById('viEditGpsBtn');
if (viEditGpsBtn) {
  viEditGpsBtn.addEventListener('click', ()=>{ try { closeViewer(); } catch{}; try { els.editGpsBtn && els.editGpsBtn.click(); } catch{} });
}

// Viewer actions: favorite + similar
const viFavoriteBtn = document.getElementById('viFavoriteBtn');
if (viFavoriteBtn) {
  viFavoriteBtn.addEventListener('click', async ()=>{
    await toggleFavorite();
    try {
      const selected = Array.isArray(state.items) ? state.items.find(i=>i.id===state.selectedId) : null;
      const viewerItems = getViewerItems();
      const current = viewerItems[state.selectedIndex] || null;
      if (selected) {
        viFavoriteBtn.textContent = selected.favorite ? '★' : '☆';
      } else if (current) {
        current.favorite = !current.favorite;
        viFavoriteBtn.textContent = current.favorite ? '★' : '☆';
      }
    } catch {}
  });
}

const SIMILAR_HASH_DISTANCE_DEFAULTS = { phash: 9, dhash: 12, ahash: 12 };
const SIMILAR_HASH_DISTANCE_STORAGE_KEY = 'fjordlens.similarHashDistances.v2';
const SIMILAR_PHASH_DISTANCE_STORAGE_KEY = 'fjordlens.similarPhashDistance.v1';
const SIMILAR_METHOD_STORAGE_KEY = 'fjordlens.similarMethod.v1';
const SIMILAR_METHODS = new Set(['hash', 'ai', 'hybrid']);
const SIMILAR_AI_MIN_DEFAULT = 88;
const SIMILAR_AI_MIN_STORAGE_KEY = 'fjordlens.similarAiMin.v1';

function normalizeSimilarMethod(value) {
  const method = String(value || '').trim().toLowerCase();
  return SIMILAR_METHODS.has(method) ? method : 'hybrid';
}

function normalizeSimilarSourceFolder(relPath) {
  let folder = String(relPath || '').replace(/\\/g, '/').trim();
  if (!folder) return '';
  folder = folder.includes('/') ? folder.split('/').slice(0, -1).join('/') : '';
  if (folder === 'uploads') folder = '';
  else if (folder.startsWith('uploads/')) folder = folder.slice('uploads/'.length);
  if (folder.startsWith('converted/')) folder = folder.slice('converted/'.length);
  if (folder.startsWith('originals/')) folder = folder.slice('originals/'.length);
  return folder;
}

function setSimilarSourceFolderCoverage(coverage) {
  const sourceFolder = String(state.similarSourceFolder || '');
  if (!coverage || typeof coverage !== 'object') {
    state.similarSourceCoverageFolder = sourceFolder;
    state.similarSourceFolderCoverageKnown = false;
    state.similarSourceFolderEmbedded = 0;
    state.similarSourceFolderTotal = 0;
    state.similarSourceFolderMissing = 0;
    return;
  }
  const coverageFolder = normalizeSimilarSourceFolder(
    Object.prototype.hasOwnProperty.call(coverage, 'folder') ? coverage.folder : sourceFolder
  );
  state.similarSourceCoverageFolder = coverageFolder;
  state.similarSourceFolderEmbedded = Number(coverage.embedded) || 0;
  state.similarSourceFolderTotal = Number(coverage.total) || 0;
  state.similarSourceFolderMissing = Number(coverage.missing) || 0;
  state.similarSourceFolderCoverageKnown = (coverageFolder === sourceFolder);
}

function setSimilarSourceItem(item) {
  state.similarSourceItem = item || null;
  state.similarSourceFolder = normalizeSimilarSourceFolder(
    state.similarSourceItem && state.similarSourceItem.rel_path ? state.similarSourceItem.rel_path : ''
  );
  setSimilarSourceFolderCoverage(null);
  renderSimilarSource(state.similarSourceItem);
}

function isSimilarAiMethodAvailable() {
  if (!!state.aiAutoEnabled || !!state.aiRunning) return true;
  const hasSourceContext = !!state.similarSourceItem || Number(state.similarSourceId || 0) > 0;
  if (hasSourceContext) {
    const sourceFolder = String(state.similarSourceFolder || '');
    const coverageFolder = String(state.similarSourceCoverageFolder || '');
    if (state.similarSourceFolderCoverageKnown && coverageFolder === sourceFolder) {
      return Number(state.similarSourceFolderEmbedded || 0) > 0;
    }
    return false;
  }
  const embedded = Number(state.aiCoverageEmbedded || 0);
  return embedded > 0;
}

function shouldPreselectSimilarAiMethod() {
  if (!!state.aiAutoEnabled || !!state.aiRunning) return true;
  const sourceFolder = String(state.similarSourceFolder || '');
  const coverageFolder = String(state.similarSourceCoverageFolder || '');
  if (state.similarSourceFolderCoverageKnown && coverageFolder === sourceFolder) {
    return Number(state.similarSourceFolderEmbedded || 0) > 0;
  }
  return false;
}

function applyPreferredSimilarMethod(opts = {}) {
  const force = !!(opts && opts.force);
  if (!force && !!state.similarMethodTouchedInModal) return false;
  if (!shouldPreselectSimilarAiMethod()) return false;
  const preferred = normalizeSimilarMethodForAvailability('ai');
  if (preferred !== 'ai') return false;
  const current = currentSimilarMethod();
  if (current === 'ai') return false;
  storeSimilarMethod('ai');
  setSimilarMethodInput('ai');
  return true;
}

function normalizeSimilarMethodForAvailability(value) {
  const method = normalizeSimilarMethod(value);
  if (!isSimilarAiMethodAvailable() && method === 'ai') return 'hash';
  return method;
}

function updateSimilarMethodAvailability() {
  if (!els.similarMethodSelect) return;
  const aiOption = els.similarMethodSelect.querySelector('option[value="ai"]');
  const aiAvailable = isSimilarAiMethodAvailable();
  if (aiOption) {
    aiOption.disabled = !aiAvailable;
    aiOption.hidden = !aiAvailable;
  }
  const current = normalizeSimilarMethod(els.similarMethodSelect.value);
  const next = normalizeSimilarMethodForAvailability(current);
  if (next !== current) {
    storeSimilarMethod(next);
    setSimilarMethodInput(next);
  }
}

function readSimilarMethod() {
  try {
    const stored = window.localStorage.getItem(SIMILAR_METHOD_STORAGE_KEY);
    if (stored) return normalizeSimilarMethodForAvailability(stored);
  } catch {}
  return normalizeSimilarMethodForAvailability(state.similarMethod || 'hybrid');
}

function storeSimilarMethod(value) {
  const method = normalizeSimilarMethodForAvailability(value);
  state.similarMethod = method;
  try {
    window.localStorage.setItem(SIMILAR_METHOD_STORAGE_KEY, method);
  } catch {}
  return method;
}

function setSimilarMethodInput(value) {
  const method = normalizeSimilarMethodForAvailability(value);
  if (els.similarMethodSelect) els.similarMethodSelect.value = method;
  if (els.similarDistanceForm) els.similarDistanceForm.dataset.method = method;
  return method;
}

function currentSimilarMethod() {
  return normalizeSimilarMethodForAvailability(els.similarMethodSelect ? els.similarMethodSelect.value : state.similarMethod);
}

function normalizeSimilarAiMin(value, fallback = SIMILAR_AI_MIN_DEFAULT) {
  const n = Math.round(Number(value));
  if (!Number.isFinite(n)) return fallback;
  return Math.max(0, Math.min(100, n));
}

function readSimilarAiMin() {
  try {
    const stored = window.localStorage.getItem(SIMILAR_AI_MIN_STORAGE_KEY);
    if (stored !== null && stored !== undefined && stored !== '') {
      return normalizeSimilarAiMin(stored);
    }
  } catch {}
  return normalizeSimilarAiMin(state.similarAiMin, SIMILAR_AI_MIN_DEFAULT);
}

function storeSimilarAiMin(value) {
  const min = normalizeSimilarAiMin(value);
  state.similarAiMin = min;
  try {
    window.localStorage.setItem(SIMILAR_AI_MIN_STORAGE_KEY, String(min));
  } catch {}
  return min;
}

function setSimilarAiMinInput(value) {
  const min = normalizeSimilarAiMin(value);
  if (els.similarAiMinInput) els.similarAiMinInput.value = String(min);
  return min;
}

function currentSimilarAiMin() {
  return normalizeSimilarAiMin(els.similarAiMinInput ? els.similarAiMinInput.value : state.similarAiMin);
}

function normalizeSimilarHashDistance(value, fallback = 12) {
  const n = Math.round(Number(value));
  if (!Number.isFinite(n)) return fallback;
  return Math.max(0, Math.min(64, n));
}

function normalizeSimilarHashSettings(value = {}) {
  const src = (value && typeof value === 'object') ? value : {};
  return {
    phash: normalizeSimilarHashDistance(src.phash, SIMILAR_HASH_DISTANCE_DEFAULTS.phash),
    dhash: normalizeSimilarHashDistance(src.dhash, SIMILAR_HASH_DISTANCE_DEFAULTS.dhash),
    ahash: normalizeSimilarHashDistance(src.ahash, SIMILAR_HASH_DISTANCE_DEFAULTS.ahash),
  };
}

function readSimilarHashSettings() {
  try {
    const stored = window.localStorage.getItem(SIMILAR_HASH_DISTANCE_STORAGE_KEY);
    if (stored) {
      return normalizeSimilarHashSettings(JSON.parse(stored));
    }
  } catch {}
  try {
    const oldPhash = window.localStorage.getItem(SIMILAR_PHASH_DISTANCE_STORAGE_KEY);
    if (oldPhash !== null && oldPhash !== undefined && oldPhash !== '') {
      return normalizeSimilarHashSettings({ ...SIMILAR_HASH_DISTANCE_DEFAULTS, phash: oldPhash });
    }
  } catch {}
  if (state.similarHashDistances && typeof state.similarHashDistances === 'object') {
    return normalizeSimilarHashSettings(state.similarHashDistances);
  }
  return normalizeSimilarHashSettings(SIMILAR_HASH_DISTANCE_DEFAULTS);
}

function storeSimilarHashSettings(value) {
  const settings = normalizeSimilarHashSettings(value);
  state.similarHashDistances = settings;
  try {
    window.localStorage.setItem(SIMILAR_HASH_DISTANCE_STORAGE_KEY, JSON.stringify(settings));
  } catch {}
  return settings;
}

function setSimilarDistanceInputs(value) {
  const settings = normalizeSimilarHashSettings(value);
  if (els.similarPhashDistanceInput) els.similarPhashDistanceInput.value = String(settings.phash);
  if (els.similarDhashDistanceInput) els.similarDhashDistanceInput.value = String(settings.dhash);
  if (els.similarAhashDistanceInput) els.similarAhashDistanceInput.value = String(settings.ahash);
  return settings;
}

function currentSimilarHashInputValues() {
  return normalizeSimilarHashSettings({
    phash: els.similarPhashDistanceInput ? els.similarPhashDistanceInput.value : undefined,
    dhash: els.similarDhashDistanceInput ? els.similarDhashDistanceInput.value : undefined,
    ahash: els.similarAhashDistanceInput ? els.similarAhashDistanceInput.value : undefined,
  });
}

function _setSimilarModalStatus(message, kind = 'ok') {
  if (!els.similarModalStatus) return;
  const txt = String(message || '').trim();
  if (!txt) {
    els.similarModalStatus.classList.add('hidden');
    els.similarModalStatus.textContent = '';
    els.similarModalStatus.classList.remove('ok', 'err');
    return;
  }
  els.similarModalStatus.textContent = txt;
  els.similarModalStatus.classList.remove('hidden');
  els.similarModalStatus.classList.toggle('ok', kind === 'ok');
  els.similarModalStatus.classList.toggle('err', kind !== 'ok');
}

function closeSimilarModal(opts = {}) {
  const clearItems = opts && opts.clearItems !== false;
  if (els.similarModal) els.similarModal.classList.add('hidden');
  if (els.similarModalGrid) els.similarModalGrid.innerHTML = '';
  _setSimilarModalStatus('');
  if (clearItems) {
    state.similarModalItems = [];
    state.similarSourceId = 0;
    state.similarMethodTouchedInModal = false;
    state.similarAutoSelectAiPending = false;
    setSimilarSourceItem(null);
  }
}

function openSimilarModal() {
  if (!els.similarModal) return;
  els.similarModal.classList.remove('hidden');
}

function findPhotoItemById(photoId) {
  const id = Number(photoId || 0);
  if (!Number.isFinite(id) || id <= 0) return null;
  const pools = [state.items, state.viewerItems, state.similarModalItems];
  for (const pool of pools) {
    if (!Array.isArray(pool)) continue;
    const found = pool.find((it) => Number(it && it.id) === id);
    if (found) return found;
  }
  return null;
}

function renderSimilarSource(item) {
  if (!els.similarSourcePanel || !els.similarSourcePreview) return;
  els.similarSourcePreview.innerHTML = '';
  if (!item) {
    els.similarSourcePanel.classList.add('hidden');
    return;
  }
  if (els.similarSourceLabel) els.similarSourceLabel.textContent = tr('similar_source_label');
  const card = document.createElement('article');
  card.className = 'photo-card similar-source-card';
  card.innerHTML = cardHTML(item);
  try {
    const title = String(item.filename || item.rel_path || '').trim();
    if (title) card.setAttribute('title', title);
  } catch {}
  card.querySelectorAll('img').forEach((img) => {
    img.setAttribute('draggable', 'false');
  });
  card.addEventListener('click', (ev) => {
    ev.preventDefault();
    ev.stopPropagation();
    closeSimilarModal({ clearItems: false });
    openViewerWithItems([item], 0);
  });
  els.similarSourcePreview.appendChild(card);
  els.similarSourcePanel.classList.remove('hidden');
}

function renderSimilarModalGrid(items, opts = {}) {
  if (!els.similarModalGrid) return;
  els.similarModalGrid.innerHTML = '';
  const arr = Array.isArray(items) ? items : [];
  const showEmpty = !(opts && opts.showEmpty === false);
  if (!arr.length) {
    if (showEmpty) {
      els.similarModalGrid.innerHTML = `<div class="similar-modal-empty">${escapeHtml(tr('similar_modal_empty'))}</div>`;
    }
    return;
  }
  arr.forEach((it, idx) => {
    appendCardTo(it, els.similarModalGrid);
    const card = els.similarModalGrid.lastElementChild;
    if (!card || !(card instanceof HTMLElement)) return;
    const hd = it && it.hash_distances && typeof it.hash_distances === 'object' ? it.hash_distances : null;
    if (hd) {
      const hashTitle = `pHash ${hd.phash ?? '-'} · dHash ${hd.dhash ?? '-'} · aHash ${hd.ahash ?? '-'} · match ${hd.matched_hashes ?? '-'}/3`;
      card.setAttribute('title', card.getAttribute('title') ? `${card.getAttribute('title')} · ${hashTitle}` : hashTitle);
    }
    if (Number.isFinite(Number(it && it.ai_similarity))) {
      const aiTitle = `AI ${(Number(it.ai_similarity) * 100).toFixed(1)}%`;
      card.setAttribute('title', card.getAttribute('title') ? `${card.getAttribute('title')} · ${aiTitle}` : aiTitle);
    }
    card.addEventListener('click', (ev) => {
      if (ev && ev.target && ev.target.closest && ev.target.closest('.info-icon-overlay')) return;
      if (_consumeMapperDragSelectClickSuppression()) {
        ev.preventDefault();
        ev.stopPropagation();
        return;
      }
      ev.preventDefault();
      ev.stopPropagation();
      const viewerItems = Array.isArray(state.similarModalItems) ? state.similarModalItems.slice() : [];
      if (!viewerItems.length) return;
      closeSimilarModal({ clearItems: false });
      openViewerWithItems(viewerItems, idx);
    }, true);
  });
}

async function loadSimilarForSource(sourceId, distanceValue) {
  let retryWithPreferredAi = false;
  const distances = storeSimilarHashSettings(distanceValue);
  const method = storeSimilarMethod(currentSimilarMethod());
  const aiMin = storeSimilarAiMin(currentSimilarAiMin());
  setSimilarMethodInput(method);
  setSimilarAiMinInput(aiMin);
  setSimilarDistanceInputs(distances);
  if (!sourceId) return;
  if (els.similarModalTitle) els.similarModalTitle.textContent = tr('similar_modal_title');
  if (!state.similarSourceItem) {
    setSimilarSourceItem(findPhotoItemById(sourceId));
  } else {
    renderSimilarSource(state.similarSourceItem);
  }
  _setSimilarModalStatus(tr('similar_modal_loading'), 'ok');
  if (els.similarDistanceApply) els.similarDistanceApply.disabled = true;
  [els.similarMethodSelect, els.similarAiMinInput, els.similarPhashDistanceInput, els.similarDhashDistanceInput, els.similarAhashDistanceInput].forEach((input) => {
    if (input) input.disabled = true;
  });
  renderSimilarModalGrid([], { showEmpty: false });
  try {
    const qs = new URLSearchParams({
      limit: '120',
      mode: method,
      ai_min_similarity: String(aiMin / 100),
      distance: String(distances.phash),
      phash_distance: String(distances.phash),
      dhash_distance: String(distances.dhash),
      ahash_distance: String(distances.ahash),
    });
    const res = await fetch(`/api/photos/${sourceId}/similar-phash?${qs.toString()}`);
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data || data.ok === false) {
      _setSimilarModalStatus((data && data.error) ? String(data.error) : tr('similar_fetch_failed'), 'err');
      return;
    }
    const items = Array.isArray(data.items) ? data.items : [];
    if (data.source_item && typeof data.source_item === 'object') {
      setSimilarSourceItem(data.source_item);
    }
    if (data.ai_folder_coverage && typeof data.ai_folder_coverage === 'object') {
      setSimilarSourceFolderCoverage(data.ai_folder_coverage);
      updateSimilarMethodAvailability();
      if (state.similarAutoSelectAiPending && applyPreferredSimilarMethod()) {
        retryWithPreferredAi = (method !== 'ai');
      }
    }
    state.similarModalItems = items;
    const returnedDistances = data && data.distances && typeof data.distances === 'object' ? data.distances : distances;
    const returnedMethod = normalizeSimilarMethod((data && data.method) || method);
    const returnedAiMin = normalizeSimilarAiMin(
      Number.isFinite(Number(data && data.ai_min_similarity)) ? Number(data.ai_min_similarity) * 100 : aiMin,
      aiMin
    );
    const msgKey = returnedMethod === 'ai'
      ? 'similar_modal_count_ai'
      : (returnedMethod === 'hybrid' ? 'similar_modal_count_hybrid' : 'similar_modal_count');
    const msg = tr(msgKey)
      .replace('{count}', String(items.length))
      .replace('{aiMin}', String(returnedAiMin))
      .replace('{phash}', String(returnedDistances.phash ?? distances.phash))
      .replace('{dhash}', String(returnedDistances.dhash ?? distances.dhash))
      .replace('{ahash}', String(returnedDistances.ahash ?? distances.ahash));
    _setSimilarModalStatus(items.length ? msg : tr('similar_modal_empty'), items.length ? 'ok' : 'ok');
    if (els.similarModalTitle) {
      els.similarModalTitle.textContent = `${tr('similar_modal_title')} (${items.length})`;
    }
    renderSimilarModalGrid(items);
  } catch {
    _setSimilarModalStatus(tr('similar_fetch_error'), 'err');
  } finally {
    state.similarAutoSelectAiPending = false;
    if (els.similarDistanceApply) els.similarDistanceApply.disabled = false;
    [els.similarMethodSelect, els.similarAiMinInput, els.similarPhashDistanceInput, els.similarDhashDistanceInput, els.similarAhashDistanceInput].forEach((input) => {
      if (input) input.disabled = false;
    });
  }
  if (retryWithPreferredAi) {
    await loadSimilarForSource(sourceId, distances);
  }
}

async function openSimilarForSelected(){
  const sourceId = _resolveSelectedPhotoIdForSimilar();
  if (!sourceId) return;
  if (els.viewer && !els.viewer.classList.contains('hidden')) {
    closeViewer();
  }
  state.similarSourceId = sourceId;
  state.similarMethodTouchedInModal = false;
  state.similarAutoSelectAiPending = true;
  setSimilarSourceItem(findPhotoItemById(sourceId));
  state.similarModalItems = [];
  updateSimilarMethodAvailability();
  setSimilarMethodInput(readSimilarMethod());
  applyPreferredSimilarMethod({ force: true });
  setSimilarAiMinInput(readSimilarAiMin());
  const distances = setSimilarDistanceInputs(readSimilarHashSettings());
  renderSimilarModalGrid([], { showEmpty: false });
  openSimilarModal();
  await loadSimilarForSource(sourceId, distances);
}
const viSimilarBtn = document.getElementById('viSimilarBtn');
if (viSimilarBtn) viSimilarBtn.addEventListener('click', openSimilarForSelected);
if (els.similarBtn) els.similarBtn.addEventListener('click', openSimilarForSelected);
if (els.similarDistanceForm) {
  els.similarDistanceForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const sourceId = Number(state.similarSourceId || _resolveSelectedPhotoIdForSimilar() || 0);
    if (!sourceId) return;
    loadSimilarForSource(sourceId, currentSimilarHashInputValues()).catch(() => {
      _setSimilarModalStatus(tr('similar_fetch_error'), 'err');
    });
  });
}
if (els.similarMethodSelect) {
  els.similarMethodSelect.addEventListener('change', () => {
    state.similarMethodTouchedInModal = true;
    state.similarAutoSelectAiPending = false;
    const method = storeSimilarMethod(els.similarMethodSelect.value);
    setSimilarMethodInput(method);
    updateSimilarMethodAvailability();
  });
  updateSimilarMethodAvailability();
  setSimilarMethodInput(readSimilarMethod());
}
if (els.similarAiMinInput) {
  els.similarAiMinInput.addEventListener('change', () => {
    setSimilarAiMinInput(storeSimilarAiMin(els.similarAiMinInput.value));
  });
  setSimilarAiMinInput(readSimilarAiMin());
}
if (els.similarModalClose) {
  els.similarModalClose.addEventListener('click', () => closeSimilarModal());
}
if (els.similarModal) {
  els.similarModal.addEventListener('click', (e) => {
    const t = e && e.target;
    if (t === els.similarModal) {
      closeSimilarModal();
      return;
    }
    if (t && t.classList && t.classList.contains('modal-backdrop')) closeSimilarModal();
  });
}

// Mobile drawer toggle
function openDrawer(){ document.body.classList.add("drawer-open"); }
function closeDrawer(){ document.body.classList.remove("drawer-open"); }
els.menuBtn && els.menuBtn.addEventListener("click", () => {
  if (document.body.classList.contains("drawer-open")) closeDrawer(); else openDrawer();
});
els.drawerBackdrop && els.drawerBackdrop.addEventListener("click", closeDrawer);
window.addEventListener("keydown", (e) => { if (e.key === "Escape") closeDrawer(); });

// Initial load
const _initialRoute = _readRouteStateFromUrl();
if (_initialRoute.view) {
  state.view = _initialRoute.view;
}
if (state.view === 'mapper') {
  state.mapperPath = _initialRoute.mapperPath || '';
  state.folder = state.mapperPath || null;
} else if (state.view === 'settings') {
  state.settingsTab = _normalizeSettingsTab(_initialRoute.settingsTab) || '';
}

applyUiLanguage();
startAppUpdateBadgePolling();

function renderHeicConversionSettings(data) {
  if (!data || !data.ok) return;
  if (els.heicConvertToggle) els.heicConvertToggle.checked = !!data.convert_on_upload;
  if (els.heicKeepToggle) els.heicKeepToggle.checked = !!data.keep_originals;
  if (els.heicStatus) els.heicStatus.textContent = `HEIC: konvertering ${data.convert_on_upload ? 'til' : 'fra'}, ${data.keep_originals ? 'bevar originaler' : 'slet originaler'}`;
}

function renderRawConversionSettings(data) {
  if (!data || !data.ok) return;
  if (els.rawConvertToggle) els.rawConvertToggle.checked = !!data.convert_on_upload;
  if (els.rawKeepToggle) els.rawKeepToggle.checked = !!data.keep_originals;
  if (els.rawStatus) els.rawStatus.textContent = `RAW/DNG: konvertering ${data.convert_on_upload ? 'til' : 'fra'}, ${data.keep_originals ? 'bevar originaler' : 'slet originaler'}`;
}

function renderMovConversionSettings(data) {
  if (!data || !data.ok) return;
  if (els.movConvertToggle) els.movConvertToggle.checked = !!data.convert_on_upload;
  if (els.movKeepToggle) els.movKeepToggle.checked = !!data.keep_originals;
  if (els.movStatus) els.movStatus.textContent = `MOV: konvertering ${data.convert_on_upload ? 'til' : 'fra'}, ${data.keep_originals ? 'bevar originaler' : 'slet originaler'}`;
}

function conversionTypeConfig(type) {
  if (type === 'raw') {
    return {
      type: 'raw',
      settingsUrl: '/api/settings/raw',
      bulkUrl: '/api/raw/convert-existing',
      statusUrl: '/api/raw/convert-existing/status',
      render: renderRawConversionSettings,
      titleKey: 'conversion_scope_title_raw',
      label: 'RAW',
      startText: 'RAW-konvertering starter…',
      runningText: 'RAW-konvertering kører…',
      doneText: 'RAW-konvertering færdig',
      failText: 'Kunne ikke starte RAW-konvertering',
      buttonText: 'Konvertér eksisterende RAW/DNG → JPEG',
    };
  }
  if (type === 'mov') {
    return {
      type: 'mov',
      settingsUrl: '/api/settings/mov',
      bulkUrl: '/api/mov/convert-existing',
      statusUrl: '/api/mov/convert-existing/status',
      render: renderMovConversionSettings,
      titleKey: 'conversion_scope_title_mov',
      label: 'MOV',
      startText: 'MOV-konvertering starter…',
      runningText: 'MOV-konvertering kører…',
      doneText: 'MOV-konvertering færdig',
      failText: 'Kunne ikke starte MOV-konvertering',
      buttonText: 'Konvertér eksisterende MOV → MP4',
    };
  }
  return {
    type: 'heic',
    settingsUrl: '/api/settings/heic',
    bulkUrl: '/api/heic/convert-existing',
    statusUrl: '/api/heic/convert-existing/status',
    render: renderHeicConversionSettings,
    titleKey: 'conversion_scope_title_heic',
    label: 'HEIC',
    startText: 'HEIC-konvertering starter…',
    runningText: 'HEIC-konvertering kører…',
    doneText: 'HEIC-konvertering færdig',
    failText: 'Kunne ikke starte HEIC-konvertering',
    buttonText: 'Konvertér eksisterende HEIC → JPEG',
  };
}

async function loadConversionSettings(type = null) {
  const types = type ? [type] : ['heic', 'raw', 'mov'];
  await Promise.all(types.map(async (itemType) => {
    const cfg = conversionTypeConfig(itemType);
    try {
      const r = await fetch(cfg.settingsUrl);
      const d = await r.json();
      cfg.render(d);
    } catch {}
  }));
}

async function saveConversionSettings(type, body) {
  const cfg = conversionTypeConfig(type);
  const r = await fetch(cfg.settingsUrl, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
  const d = await r.json().catch(()=>({}));
  if (!r.ok || !d || d.ok === false) throw new Error((d && d.error) || 'settings_failed');
  cfg.render(d);
  return d;
}

function updateConversionScopeModalText() {
  const pendingType = state.conversionScopePendingType || 'heic';
  const cfg = conversionTypeConfig(pendingType);
  if (els.conversionScopeModalTitle) els.conversionScopeModalTitle.textContent = tr(cfg.titleKey);
  if (els.conversionScopeModalText) els.conversionScopeModalText.textContent = tr('conversion_scope_text');
  if (els.conversionScopeModalNew) els.conversionScopeModalNew.textContent = tr('conversion_scope_new');
  if (els.conversionScopeModalAll) els.conversionScopeModalAll.textContent = tr('conversion_scope_all');
  if (els.conversionScopeModalCancel) els.conversionScopeModalCancel.textContent = tr('conversion_scope_cancel');
  if (els.conversionScopeModalClose) els.conversionScopeModalClose.textContent = tr('scan_modal_close');
}

function openConversionScopeModal(type) {
  state.conversionScopePendingType = conversionTypeConfig(type).type;
  updateConversionScopeModalText();
  if (els.conversionScopeModal) els.conversionScopeModal.classList.remove('hidden');
}

function closeConversionScopeModal(options = {}) {
  const pendingType = state.conversionScopePendingType;
  if (els.conversionScopeModal) els.conversionScopeModal.classList.add('hidden');
  state.conversionScopePendingType = null;
  if (options && options.restore && pendingType) {
    loadConversionSettings(pendingType).catch(()=>{});
  }
}

async function startExistingConversion(type, btn = null) {
  const cfg = conversionTypeConfig(type);
  const originalText = btn ? btn.textContent : '';
  try {
    if (btn) { btn.disabled = true; btn.classList.add('loading'); btn.textContent = 'Konverterer…'; }
    const r = await fetch(cfg.bulkUrl, { method:'POST' });
    if (!r.ok) {
      const d = await r.json().catch(()=>({}));
      showStatus(d && d.error ? d.error : cfg.failText, 'err');
      if (btn) { btn.disabled = false; btn.classList.remove('loading'); btn.textContent = originalText || cfg.buttonText; }
      return;
    }
    showStatus(`Starter konvertering af eksisterende ${cfg.label}…`, 'ok');
    showTopStatusMessage(cfg.startText, 0);
    const poll = async () => {
      try {
        const s = await fetch(cfg.statusUrl);
        const d = await s.json();
        if (s.ok && d && d.ok) {
          if (!d.running) {
            if (d.result) {
              const p = Number(d.result.processed || 0);
              const e = Number(d.result.errors || 0);
              showStatus(`${cfg.doneText}: ${p} filer${e ? `, fejl: ${e}` : ''}.`, e ? 'err' : 'ok');
            }
            await loadPhotos();
            if (state.view === 'mapper') loadMapperTools();
            hideTopStatusMessage();
            if (btn) { btn.disabled = false; btn.classList.remove('loading'); btn.textContent = originalText || cfg.buttonText; }
            return;
          }
          const pr = d.progress || {};
          const total = Number(pr.total || 0);
          const done = Number(pr.processed || 0);
          const pct = total > 0 ? Math.round((done / total) * 100) : null;
          const lbl = total > 0 ? `${cfg.doneText.replace(' færdig', '')} · ${done}/${total}${pct!==null?` · ${pct}%`:''}` : cfg.runningText;
          showTopStatusMessage(lbl, pct);
        }
      } catch {}
      setTimeout(poll, 1200);
    };
    setTimeout(poll, 800);
  } catch {
    showStatus(cfg.failText, 'err');
    if (btn) { btn.disabled = false; btn.classList.remove('loading'); btn.textContent = originalText || cfg.buttonText; }
  }
}

// Resolve user role early to gate admin UI (wrapped to avoid top-level await)
(async () => {
  try {
    const mr = await fetch('/api/me');
    const mj = await mr.json();
    if (mr.ok && mj && mj.ok && mj.item) {
      state.currentUser = { id: mj.item.id, username: mj.item.username, role: mj.item.role || 'user' };
    }
  } catch {}
  try {
    const role = (state.currentUser && state.currentUser.role) ? String(state.currentUser.role) : 'user';
    if (role === 'user') {
      const settingsBtn = document.querySelector('.nav-item[data-view="settings"]');
      if (settingsBtn) settingsBtn.style.display = 'none';
      document.querySelectorAll('.mobile-nav-item[data-view="settings"]').forEach(el=>{ el.style.display = 'none'; });
      if (state.view === 'settings') state.view = 'timeline';
    }
  } catch {}
})();

setView(state.view, { syncUrl: false }).then(async () => {
  // Start with a quick status check in case scan was running
  if (SCAN_FEATURES_ENABLED) {
    fetch("/api/scan/status").then(r => r.json()).then(d => {
      if (d && d.running) {
        state.scanning = true;
        updateScanButton();
        pollScanStatus();
      }
    }).catch(() => {});
  }
  // Start logs only for elevated roles (not basic 'user')
  try {
    const role = (state.currentUser && state.currentUser.role) ? String(state.currentUser.role) : 'user';
    if (role !== 'user') {
      startLogs();
    } else {
      // Ensure UI reflects stopped state
      state.logsRunning = false;
      if (els.logsStart) els.logsStart.textContent = tr ? tr('btn_start') : 'Start';
    }
  } catch {
    // Fallback: do not start logs if uncertain about role
    state.logsRunning = false;
  }
  loadUploadFileTypeSettings({ silent: true }).catch(() => {});
  // Load conversion settings into toggles
  try {
    loadConversionSettings().catch(()=>{});
  } catch {}
  // If a bulk HEIC conversion is already running, start a passive poll to show top status
  try {
    const s = await fetch('/api/heic/convert-existing/status');
    const d = await s.json();
    if (s.ok && d && d.ok && d.running) {
      const poll = async () => {
        try {
          const s2 = await fetch('/api/heic/convert-existing/status');
          const d2 = await s2.json();
          if (s2.ok && d2 && d2.ok) {
            if (!d2.running) { hideTopStatusMessage(); return; }
            const pr = d2.progress || {};
            const total = Number(pr.total || 0);
            const done = Number(pr.processed || 0);
            const pct = total > 0 ? Math.round((done / total) * 100) : null;
            const lbl = total > 0 ? `RAW/HEIC-konvertering · ${done}/${total}${pct!==null?` · ${pct}%`:''}` : 'RAW/HEIC-konvertering kører…';
            showTopStatusMessage(lbl, pct);
          }
        } catch {}
        setTimeout(poll, 1200);
      };
      poll();
    }
  } catch {}
  _announceUploadResumeDraftIfNeeded();
  try {
    if (els.uploadMonitor) els.uploadMonitor.classList.add('hidden');
  } catch {}
  startMapperDiskSyncWatcher();
  // Safety: remove any stray backdrops/overlays that might block UI after reload
  try { document.querySelectorAll('.modal-backdrop[data-ephemeral="1"]').forEach(el=>{ if(el.parentElement) el.parentElement.removeChild(el); }); } catch{}
  try { document.querySelectorAll('.upload-overlay').forEach(el=> el.classList.remove('active')); } catch{}
  // Watchdog: every 5s remove any backdrop with no visible modal child
  setInterval(()=>{
    try {
      document.querySelectorAll('.modal-backdrop[data-ephemeral="1"]').forEach(el=>{
        const hasModal = !!el.querySelector('.gps-modal:not(.hidden)');
        if (!hasModal) { if (el.parentElement) el.parentElement.removeChild(el); }
      });
      document.querySelectorAll('.upload-overlay').forEach(el=>{ if (!el.classList.contains('active')) el.classList.remove('active'); });
    } catch{}
  }, 1000);
});

// Conversion settings handlers
try {
  if (els.heicConvertToggle) els.heicConvertToggle.addEventListener('change', async ()=>{
    try {
      if (els.heicConvertToggle.checked) {
        openConversionScopeModal('heic');
      } else {
        await saveConversionSettings('heic', { convert_on_upload: false });
      }
    } catch { loadConversionSettings('heic').catch(()=>{}); }
  });
  if (els.heicKeepToggle) els.heicKeepToggle.addEventListener('change', async ()=>{
    try {
      await saveConversionSettings('heic', { keep_originals: !!els.heicKeepToggle.checked });
    } catch { loadConversionSettings('heic').catch(()=>{}); }
  });
  if (els.rawConvertToggle) els.rawConvertToggle.addEventListener('change', async ()=>{
    try {
      if (els.rawConvertToggle.checked) {
        openConversionScopeModal('raw');
      } else {
        await saveConversionSettings('raw', { convert_on_upload: false });
      }
    } catch { loadConversionSettings('raw').catch(()=>{}); }
  });
  if (els.rawKeepToggle) els.rawKeepToggle.addEventListener('change', async ()=>{
    try {
      await saveConversionSettings('raw', { keep_originals: !!els.rawKeepToggle.checked });
    } catch { loadConversionSettings('raw').catch(()=>{}); }
  });
  if (els.movConvertToggle) els.movConvertToggle.addEventListener('change', async ()=>{
    try {
      if (els.movConvertToggle.checked) {
        openConversionScopeModal('mov');
      } else {
        await saveConversionSettings('mov', { convert_on_upload: false });
      }
    } catch { loadConversionSettings('mov').catch(()=>{}); }
  });
  if (els.movKeepToggle) els.movKeepToggle.addEventListener('change', async ()=>{
    try {
      await saveConversionSettings('mov', { keep_originals: !!els.movKeepToggle.checked });
    } catch { loadConversionSettings('mov').catch(()=>{}); }
  });
  if (els.conversionScopeModalClose) els.conversionScopeModalClose.addEventListener('click', ()=> closeConversionScopeModal({ restore: true }));
  if (els.conversionScopeModalCancel) els.conversionScopeModalCancel.addEventListener('click', ()=> closeConversionScopeModal({ restore: true }));
  if (els.conversionScopeModal) {
    els.conversionScopeModal.addEventListener('click', (e) => {
      if (e.target === els.conversionScopeModal) closeConversionScopeModal({ restore: true });
    });
  }
  if (els.conversionScopeModalNew) els.conversionScopeModalNew.addEventListener('click', async ()=>{
    const pendingType = state.conversionScopePendingType;
    closeConversionScopeModal();
    if (!pendingType) return;
    try {
      await saveConversionSettings(pendingType, { convert_on_upload: true });
    } catch {
      showStatus('Kunne ikke gemme konverteringsindstilling', 'err');
      loadConversionSettings(pendingType).catch(()=>{});
    }
  });
  if (els.conversionScopeModalAll) els.conversionScopeModalAll.addEventListener('click', async ()=>{
    const pendingType = state.conversionScopePendingType;
    closeConversionScopeModal();
    if (!pendingType) return;
    try {
      await saveConversionSettings(pendingType, { convert_on_upload: true });
      await startExistingConversion(pendingType);
    } catch {
      showStatus('Kunne ikke starte konvertering', 'err');
      loadConversionSettings(pendingType).catch(()=>{});
    }
  });
  if (els.heicBulkConvertBtn) els.heicBulkConvertBtn.addEventListener('click', async ()=>{
    startExistingConversion('heic', els.heicBulkConvertBtn);
  });

  if (els.rawBulkConvertBtn) els.rawBulkConvertBtn.addEventListener('click', async ()=>{
    startExistingConversion('raw', els.rawBulkConvertBtn);
  });
  if (els.movBulkConvertBtn) els.movBulkConvertBtn.addEventListener('click', async ()=>{
    startExistingConversion('mov', els.movBulkConvertBtn);
  });
} catch {}

// --- Embedded Admin Panels ---
async function renderUsersPanel(){
  const wrap = document.getElementById('usersPanelInner');
  if (!wrap) return;
  wrap.textContent = 'Indlæser…';
  try{
    const r = await fetch('/api/admin/users');
    const raw = await r.text();
    let js;
    try { js = JSON.parse(raw); }
    catch(parseErr){
      const snippet = (raw || '').slice(0, 200).trim();
      wrap.innerHTML = `<div class="empty">Kan ikke hente brugere. Server svarede ikke med JSON.${snippet ? `\n\n${escapeHtml(snippet)}` : ''}</div>`;
      return;
    }
    if (!r.ok || !js.ok){
      wrap.innerHTML = `<div class="empty">Kan ikke hente brugere. ${js && js.error ? js.error : ''}</div>`;
      return;
    }
    const items = js.items || [];
    const loginAudit = Array.isArray(js.login_audit) ? js.login_audit : [];
    const availableFolders = Array.isArray(js.available_folders) ? js.available_folders : [];
    const managedByHub = !!js.managed_by_fjordhub;
    const rows = items.map(u => {
      const role = String(u.role || '').toLowerCase();
      const aclButton = role === 'admin'
        ? ''
        : `<button data-acl="${u.id}" class="btn small">Mapper</button>`;
      return `
      <tr>
        <td class="col-id muted">#${u.id}</td>
        <td class="col-user"><strong>${u.username}</strong>${managedByHub ? ' <span class="badge muted">Hub</span>' : ''}</td>
        <td class="col-role">${u.role}</td>
        <td class="col-lang">${(u.ui_language || 'da').toUpperCase()} / ${(u.search_language || 'da').toUpperCase()}</td>
        <td class="col-2fa">${u.totp_enabled ? '<span class="badge twofa">2FA</span>' : '<span class="badge muted">—</span>'}</td>
        <td class="col-actions" style="text-align:right;display:flex;gap:6px;justify-content:flex-end;">
          ${aclButton}
          <button data-edit="${u.id}" class="btn small" aria-label="Rediger bruger">Rediger</button>
          <button data-del="${u.id}" class="btn danger small">Slet</button>
        </td>
      </tr>`;
    }).join('');
    // Build compact, paginated login log (4 per page) with expandable details
    const LOG_PAGE_SIZE = 4;
    const curPageInput = parseInt(window.usersLogPage || '1', 10);
    const pageSafe = isNaN(curPageInput) ? 1 : Math.max(1, curPageInput);
    const totalPages = Math.max(1, Math.ceil((loginAudit.length || 0) / LOG_PAGE_SIZE));
    const curPage = Math.min(pageSafe, totalPages);
    if (curPage !== pageSafe) window.usersLogPage = curPage;
    const start = (curPage - 1) * LOG_PAGE_SIZE;
    const pageItems = (loginAudit || []).slice(start, start + LOG_PAGE_SIZE);
    const auditRows = pageItems.map((entry, idx) => {
      const status = entry && entry.success ? tr('users_login_status_ok') : tr('users_login_status_fail');
      const statusClass = entry && entry.success ? 'ok' : 'err';
      const userTxt = (entry && entry.username) || (entry && entry.username_input) || tr('users_login_unknown');
      const reasonTxt = (entry && entry.reason) || (entry && entry.event_type) || '—';
      const targetId = `log_${start + idx}`;
      return `
      <tr>
        <td class="col-time">${escapeHtml(fmtDate(entry && entry.at))}</td>
        <td class="col-user">${escapeHtml(userTxt)}</td>
        <td class="col-status"><span class="upload-monitor-item-status ${statusClass}">${escapeHtml(status)}</span></td>
        <td class="col-action" style="text-align:right;"><button class="btn small log-toggle" data-target="${targetId}">Vis mere</button></td>
      </tr>
      <tr class="log-details hidden" id="${targetId}">
        <td colspan="4">
          <div class="mini-label">Begrundelse: ${escapeHtml(reasonTxt)}</div>
          <div class="mini-label">IP: ${escapeHtml((entry && entry.ip) || '—')} · Land: ${escapeHtml((entry && entry.country) || '—')} · Enhed: ${escapeHtml((entry && entry.device) || '—')}</div>
        </td>
      </tr>`;
    }).join('');
    wrap.innerHTML = `
      <div class="panel" style="margin-bottom:12px;">
        <div class="toolbar">
          <strong>${escapeHtml(tr('users_panel_title'))}</strong>
          <button id="nu_open" class="btn primary" style="margin-left:auto;">${escapeHtml(tr('users_add_user'))}</button>
        </div>
      </div>
      <div class="data-table" style="margin-bottom:12px;">
        <table>
          <thead><tr><th class="col-id">${escapeHtml(tr('users_col_id'))}</th><th class="col-user">${escapeHtml(tr('users_col_username'))}</th><th class="col-role">${escapeHtml(tr('users_col_role'))}</th><th class="col-lang">${escapeHtml(tr('users_col_language'))}</th><th class="col-2fa">${escapeHtml(tr('users_col_2fa'))}</th><th class="col-actions"></th></tr></thead>
          <tbody>${rows || `<tr><td colspan=6 class="muted">${escapeHtml(tr('users_no_users'))}</td></tr>`}</tbody>
        </table>
      </div>
      <div class="panel" style="margin-bottom:8px;">
        <div class="toolbar"><strong>${escapeHtml(tr('users_login_log_title'))}</strong></div>
      </div>
      <div class="data-table" style="margin-bottom:8px;">
        <table>
          <thead><tr><th>${escapeHtml(tr('users_login_col_time'))}</th><th>${escapeHtml(tr('users_login_col_user'))}</th><th>${escapeHtml(tr('users_login_col_status'))}</th><th></th></tr></thead>
          <tbody>${auditRows || `<tr><td colspan=4 class="muted">${escapeHtml(tr('users_login_log_empty'))}</td></tr>`}</tbody>
        </table>
      </div>
      <div class="pager" id="loginLogPager" style="display:flex;gap:8px;align-items:center;justify-content:flex-end;margin:6px 0 12px;">
        <button id="log_prev" class="btn small" ${(typeof totalPages!=='undefined' && totalPages>1 && window.usersLogPage>1)?'':'disabled'}>Forrige</button>
        <span class="mini-label">Side <strong>${(typeof totalPages!=='undefined') ? Math.min(window.usersLogPage||1,totalPages) : 1}</strong> / ${(typeof totalPages!=='undefined') ? totalPages : 1}</span>
        <button id="log_next" class="btn small" ${(typeof totalPages!=='undefined' && (window.usersLogPage||1) < totalPages)?'':'disabled'}>Næste</button>
      </div>
      <!-- Create user modal -->
      <div id="nu_modal" class="hidden" style="position:fixed;inset:0;background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;z-index:9999;">
        <div style="width:520px;max-width:92vw;background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px;">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
            <h3 style="margin:0;">Tilføj bruger</h3>
            <button id="nu_close" class="btn">Luk</button>
          </div>
          <div class="form-row"><label for="nu_username">Brugernavn</label><input id="nu_username" placeholder="Brugernavn"></div>
          <div class="form-row reveal-wrap"><label for="nu_password">Adgangskode</label>
            <div class="pwd-field">
              <input id="nu_password" placeholder="Adgangskode" type="password" style="padding-right:42px;">
              <button id="nu_pw_toggle" type="button" class="reveal-btn" aria-label="Vis adgangskode">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 5c4.5 0 8.4 2.9 10 7-1.6 4.1-5.5 7-10 7s-8.4-2.9-10-7c1.6-4.1 5.5-7 10-7zm0 2c-3.3 0-6.3 2.1-7.6 5 1.3 2.9 4.3 5 7.6 5s6.3-2.1 7.6-5c-1.3-2.9-4.3-5-7.6-5zm0 2.5a2.5 2.5 0 110 5 2.5 2.5 0 010-5z"/></svg>
              </button>
            </div>
          </div>
          <div class="form-row"><label for="nu_role">Rolle</label>
            <select id="nu_role" class="select">
              <option value="user">Bruger</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div class="form-row"><label for="nu_ui_language">UI-sprog</label>
            <select id="nu_ui_language" class="select">
              <option value="da">Dansk</option>
              <option value="en">English</option>
            </select>
          </div>
          <div class="form-row"><label for="nu_search_language">Søgesprog</label>
            <select id="nu_search_language" class="select">
              <option value="da">Dansk</option>
              <option value="en">English</option>
            </select>
          </div>
          <div class="toolbar" style="gap:8px;margin:8px 0;align-items:center;">
            <button id="nu_acl" class="btn">Mappeadgang…</button>
            <div id="nu_acl_count" class="mini-label" style="opacity:.8;">Ingen mapper valgt</div>
          </div>
          <label style="display:flex;align-items:center;gap:8px;margin:6px 0 2px;">
            <input type="checkbox" id="nu_2fa" />
            <span>Aktivér 2FA fra start</span>
          </label>
          <div class="actions" style="justify-content:flex-end;">
            <button id="nu_cancel" class="btn">Annuller</button>
            <button id="nu_save" class="btn primary">Opret</button>
          </div>
        </div>
      </div>

      <!-- Edit user modal -->
      <div id="eu_modal" class="hidden" style="position:fixed;inset:0;background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;z-index:9999;">
        <div style="width:520px;max-width:92vw;background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px;">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
            <h3 style="margin:0;">Rediger bruger</h3>
            <button id="eu_close" class="btn">Luk</button>
          </div>
          <div class="form-row"><label for="eu_username">Brugernavn</label><input id="eu_username" placeholder="Brugernavn"></div>
          <div class="form-row"><label for="eu_password">Nyt password (valgfrit)</label><input id="eu_password" placeholder="Tom = uændret" type="password"></div>
          <div class="form-row"><label for="eu_role">Rolle</label>
            <select id="eu_role" class="select">
              <option value="user">Bruger</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div class="form-row"><label for="eu_ui_language">UI-sprog</label>
            <select id="eu_ui_language" class="select">
              <option value="da">Dansk</option>
              <option value="en">English</option>
            </select>
          </div>
          <div class="form-row"><label for="eu_search_language">Søgesprog</label>
            <select id="eu_search_language" class="select">
              <option value="da">Dansk</option>
              <option value="en">English</option>
            </select>
          </div>
          <div class="actions" style="justify-content:space-between;gap:8px;">
            <button id="eu_delete" class="btn danger">Slet bruger</button>
            <div style="display:flex;gap:8px;">
              <button id="eu_cancel" class="btn">Annuller</button>
              <button id="eu_save" class="btn primary">Gem</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Folder access modal -->
      <div id="ua_modal" class="hidden" style="position:fixed;inset:0;background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;z-index:10000;">
        <div class="ua-box" style="width:700px;max-width:95vw;max-height:90vh;overflow:auto;background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px;">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;gap:8px;">
            <h3 style="margin:0;">${escapeHtml(tr('users_folders_title'))}</h3>
            <button id="ua_close" class="btn">${escapeHtml(tr('users_close'))}</button>
          </div>
          <div id="ua_user" class="mini-label" style="margin-bottom:8px;"></div>
          <div id="ua_hint" class="mini-label" style="margin-bottom:8px;">${escapeHtml(tr('users_folders_hint'))}</div>
          <div id="ua_folder_access" class="ua-list" style="max-height:55vh;overflow:auto;padding:10px;border:1px solid var(--border);border-radius:8px;background:var(--bg-soft);"></div>
          <div class="actions" style="justify-content:flex-end;margin-top:10px;">
            <button id="ua_clear_all" class="btn">${escapeHtml(tr('users_clear_all'))}</button>
            <button id="ua_cancel" class="btn">${escapeHtml(tr('users_cancel'))}</button>
            <button id="ua_save" class="btn primary">${escapeHtml(tr('users_save_access'))}</button>
          </div>
        </div>
      </div>
    `;

    const byId = new Map(items.map(u => [String(u.id), u]));

    const normalizeAclFolder = (value) => String(value || '')
      .replace(/\\/g, '/')
      .replace(/\/+/g, '/')
      .replace(/^\/+|\/+$/g, '');

    const toPerm = (raw) => {
      const v = String(raw || '').toLowerCase();
      if (v === 'edit' || v === 'manage' || v === 'delete') return 'edit';
      if (v === 'upload') return 'upload';
      if (v === 'view') return 'view';
      return 'none';
    };

    const permRank = (p) => (p === 'edit' ? 3 : p === 'upload' ? 2 : p === 'view' ? 1 : 0);

    const setFolderSelection = (containerId, selectedFolders, allFolders = []) => {
      const root = document.getElementById(containerId);
      if (!root) return;
      if (Array.isArray(allFolders) && allFolders.length) {
        // Build a map of folder -> permission from selectedFolders (supports legacy strings)
        const selectedPerm = new Map();
        (selectedFolders || []).forEach((it) => {
          if (typeof it === 'string') {
            const p = normalizeAclFolder(it);
            if (p && p !== 'uploads') selectedPerm.set(p, 'view');
            return;
          }
          if (it && typeof it === 'object'){
            const p = normalizeAclFolder(it.folder_path || it.folder || it.path || '');
            const perm = toPerm(it.permission || it.perm);
            if (p && p !== 'uploads' && perm !== 'none') selectedPerm.set(p, perm);
          }
        });
        const seen = new Set();
        const filteredFolders = allFolders
          .map((folder) => normalizeAclFolder(folder))
          .filter((folder) => folder && folder !== 'uploads')
          .filter((folder) => {
            if (seen.has(folder)) return false;
            seen.add(folder);
            return true;
          });
        // Build parent->hasChildren map
        const hasChildren = new Set();
        const parentOf = (p) => {
          const i = String(p||'').lastIndexOf('/');
          return i === -1 ? '' : String(p).slice(0, i);
        };
        filteredFolders.forEach((f)=>{
          const parent = parentOf(f);
          if (parent) hasChildren.add(parent);
        });
        const rows = filteredFolders.map((folder) => {
          const depth = String(folder || '').split('/').filter(Boolean).length;
          const pad = Math.max(0, (depth - 1) * 14);
          const labelFull = String(folder || '').startsWith('uploads/') ? String(folder || '').slice(8) : String(folder || '');
          const label = labelFull.split('/').filter(Boolean).pop() || labelFull;
          const current = selectedPerm.get(folder) || 'none';
          const name = `perm:${folder}`;
          const cell = (val, txt) => `
            <label class="ua-dot" data-level="${val}" title="${escapeHtml(txt||'')}">
              <input type="radio" name="${escapeHtml(name)}" value="${val}" ${current===val?'checked':''} />
              <span class="dot" aria-hidden="true"></span>
              <span class="ua-cap">${escapeHtml(txt||'')}</span>
            </label>`;
          const caret = hasChildren.has(folder)
            ? `<button class=\"ua-caret\" type=\"button\" aria-label=\"Fold\"></button>`
            : `<span class=\"ua-caret ua-caret-placeholder\"></span>`;
          const parent = parentOf(folder);
          return `
            <div class="ua-row" data-folder="${escapeHtml(folder)}" data-parent="${escapeHtml(parent)}" data-depth="${depth}" style="display:grid;grid-template-columns:auto 96px 110px 110px;gap:8px;align-items:center;padding:4px 0;border-bottom:1px dashed var(--border-soft);">
              <div class="ua-label" style="padding-left:${pad}px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${caret}<span class="ua-name" title="${escapeHtml(labelFull)}">${escapeHtml(label)}</span></div>
              ${cell('view','Viser')}
              ${cell('upload','Uploader')}
              ${cell('edit','Redigere')}
            </div>`;
        }).join('');
        const header = `
          <div class="ua-head" style="display:grid;grid-template-columns:auto 96px 110px 110px;gap:8px;align-items:center;padding:6px 0;border-bottom:1px solid var(--border);font-weight:600;">
            <div>Mappe</div>
            <div style="text-align:center;">Viser</div>
            <div style="text-align:center;">Uploader</div>
            <div style="text-align:center;">Redigere</div>
          </div>`;
        root.innerHTML = header + rows;

        // Initialize visual levels so earlier dots fill up
        const toRank = (v) => (v==='edit'?3:(v==='upload'?2:(v==='view'?1:0)));
        const updateRowLevel = (row) => {
          const folder = normalizeAclFolder(row.getAttribute('data-folder') || '');
          const sel = row.querySelector(`input[type="radio"][name="perm:${CSS.escape(folder)}"]:checked`);
          const val = sel ? String(sel.value||'') : 'none';
          row.classList.remove('lvl-view','lvl-upload','lvl-edit');
          if (val==='view') row.classList.add('lvl-view');
          else if (val==='upload') row.classList.add('lvl-upload');
          else if (val==='edit') row.classList.add('lvl-edit');
        };
        const rowsAll = Array.from(root.querySelectorAll('.ua-row[data-folder]'));
        const rowByPath = new Map(rowsAll.map(r => [String(r.getAttribute('data-folder')||''), r]));
        const updateTreeVisibility = () => {
          rowsAll.forEach((row)=>{
            const depth = parseInt(row.getAttribute('data-depth')||'1', 10) || 1;
            if (depth === 1) { row.style.display = 'grid'; return; }
            const path = String(row.getAttribute('data-folder')||'');
            let parent = parentOf(path);
            let visible = true;
            while (parent) {
              const pr = rowByPath.get(parent);
              if (pr && !pr.classList.contains('open')) { visible = false; break; }
              parent = parentOf(parent);
            }
            row.style.display = visible ? 'grid' : 'none';
          });
        };

        rowsAll.forEach((row)=>{
          const folder = normalizeAclFolder(row.getAttribute('data-folder') || '');
          const caretBtn = row.querySelector('.ua-caret');
          if (caretBtn && !caretBtn.classList.contains('ua-caret-placeholder')){
            caretBtn.addEventListener('click', ()=>{
              row.classList.toggle('open');
              updateTreeVisibility();
            });
          }
        });
        updateTreeVisibility();

        rowsAll.forEach((row)=>{
          updateRowLevel(row);
          const folder = normalizeAclFolder(row.getAttribute('data-folder') || '');
          row.querySelectorAll(`input[type="radio"][name="perm:${CSS.escape(folder)}"]`).forEach((r)=>{
            r.addEventListener('change', ()=> updateRowLevel(row));
          });
        });
      } else if (!root.children.length) {
        root.innerHTML = `<div class="mini-label muted">${escapeHtml(tr('users_acl_none_found'))}</div>`;
      }
      // Pre-selection handled above by radio 'checked' attributes
    };

    const getFolderSelection = (containerId) => {
      const root = document.getElementById(containerId);
      if (!root) return [];
      const rows = Array.from(root.querySelectorAll('.ua-row[data-folder]'));
      const out = [];
      rows.forEach((row) => {
        const folder = normalizeAclFolder(row.getAttribute('data-folder') || '');
        if (!folder || folder === 'uploads') return;
        const sel = row.querySelector(`input[type="radio"][name="perm:${CSS.escape(folder)}"]:checked`);
        const perm = sel ? toPerm(sel.value) : 'none';
        if (perm !== 'none') out.push({ folder_path: folder, permission: perm });
      });
      return out;
    };

    const bindAclHierarchy = (containerId) => {
      const root = document.getElementById(containerId);
      if (!root) return;
      root.querySelectorAll('input[type="checkbox"][data-folder]').forEach((el) => {
        el.addEventListener('change', () => {
          const folder = normalizeAclFolder(el.getAttribute('data-folder') || '');
          if (!folder) return;
          if (!el.checked) return;
          root.querySelectorAll('input[type="checkbox"][data-folder]').forEach((other) => {
            if (other === el) return;
            const otherFolder = normalizeAclFolder(other.getAttribute('data-folder') || '');
            if (!otherFolder || !otherFolder.startsWith(folder + '/')) return;
            other.checked = true;
          });
        });
      });
    };

    const aclModal = document.getElementById('ua_modal');
    const aclCloseBtn = document.getElementById('ua_close');
    const aclCancelBtn = document.getElementById('ua_cancel');
    const aclClearAllBtn = document.getElementById('ua_clear_all');
    const aclSaveBtn = document.getElementById('ua_save');
    const aclUserLabel = document.getElementById('ua_user');
    let aclEditingUserId = null;

    function closeAclModal() {
      if (!aclModal) return;
      aclModal.classList.add('hidden');
      aclEditingUserId = null;
    }

    wrap.querySelectorAll('button[data-acl]').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = String(btn.getAttribute('data-acl') || '');
        const user = byId.get(id);
        if (!user) return;
        aclEditingUserId = user.id;
        if (aclUserLabel) {
          const count = Array.isArray(user.allowed_folders) ? user.allowed_folders.length : 0;
          aclUserLabel.textContent = `${tr('users_acl_user_prefix')}: ${user.username} (#${user.id}) — ${count ? `${count} ${tr('users_acl_selected_suffix')}` : tr('users_acl_all_folders')}`;
        }
        setFolderSelection('ua_folder_access', user.allowed_folders || [], availableFolders);
        bindAclHierarchy('ua_folder_access');
        if (aclModal) aclModal.classList.remove('hidden');
      });
    });

    aclCloseBtn && aclCloseBtn.addEventListener('click', closeAclModal);
    aclCancelBtn && aclCancelBtn.addEventListener('click', closeAclModal);
    aclClearAllBtn && aclClearAllBtn.addEventListener('click', () => {
      const root = document.getElementById('ua_folder_access');
      if (!root) return;
      root.querySelectorAll('.ua-row[data-folder]').forEach((row) => {
        const folder = normalizeAclFolder(row.getAttribute('data-folder') || '');
        const radios = row.querySelectorAll(`input[type="radio"][name="perm:${CSS.escape(folder)}"]`);
        radios.forEach((r)=>{ r.checked = false; });
        row.classList.remove('lvl-view','lvl-upload','lvl-edit');
      });
    });
    aclModal && aclModal.addEventListener('click', (e)=>{ if(e.target === aclModal) closeAclModal(); });
    aclSaveBtn && aclSaveBtn.addEventListener('click', async () => {
      const allowed_folders = getFolderSelection('ua_folder_access');
      // If editing existing user
      if (aclEditingUserId) {
        await withBtnLoading(aclSaveBtn, async () => {
          const rr = await fetch('/api/admin/users/' + aclEditingUserId + '/folders', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ allowed_folders }),
          });
          const jj = await rr.json();
          if (!rr.ok || !jj.ok) {
            showStatus(`${tr('users_status_acl_save_failed')} ${((jj && jj.error) || '')}`.trim(), 'err');
            return;
          }
          showStatus(tr('users_status_acl_saved'), 'ok');
          closeAclModal();
          renderUsersPanel();
        });
      } else {
        // Pre-create mode: just store locally for the new user form
        newUserAllowedFolders = allowed_folders || [];
        setNuAclCount();
        closeAclModal();
      }
    });

    // bind delete
    wrap.querySelectorAll('button[data-del]').forEach(btn=>{
      btn.addEventListener('click', async ()=>{
        const id = btn.getAttribute('data-del');
        if (!confirm(`${tr('users_confirm_delete')} #${id}?`)) return;
        const rr = await fetch('/api/admin/users/'+id, {method:'DELETE'});
        const jj = await rr.json();
        if (!rr.ok || !jj.ok){ showStatus(`${tr('users_status_delete_failed')} ${(jj && jj.error || '')}`.trim(), 'err'); return; }
        showStatus(tr('users_status_deleted'), 'ok');
        renderUsersPanel();
      });
    });

    // edit modal wiring
    const editModal = document.getElementById('eu_modal');
    const editCloseBtn = document.getElementById('eu_close');
    const editCancelBtn = document.getElementById('eu_cancel');
    let editingUserId = null;

    function closeEdit(){
      if (!editModal) return;
      editModal.classList.add('hidden');
      editingUserId = null;
      const ep = document.getElementById('eu_password');
      if (ep) ep.value = '';
    }

    wrap.querySelectorAll('button[data-edit]').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = String(btn.getAttribute('data-edit') || '');
        const user = byId.get(id);
        if (!user) return;
        editingUserId = user.id;
        const eu = document.getElementById('eu_username');
        const ep = document.getElementById('eu_password');
        const er = document.getElementById('eu_role');
        const eul = document.getElementById('eu_ui_language');
        const esl = document.getElementById('eu_search_language');
        if (eu) eu.value = user.username || '';
        if (ep) ep.value = '';
        if (eu) eu.disabled = managedByHub;
        if (ep) {
          ep.disabled = managedByHub;
          ep.placeholder = managedByHub ? 'Styres i FjordHub' : 'Tom = uændret';
        }
        if (er) er.value = user.role || 'user';
        if (eul) eul.value = user.ui_language || 'da';
        if (esl) esl.value = user.search_language || 'da';
        if (editModal) editModal.classList.remove('hidden');
      });
    });

    editCloseBtn && editCloseBtn.addEventListener('click', closeEdit);
    editCancelBtn && editCancelBtn.addEventListener('click', closeEdit);
    editModal && editModal.addEventListener('click', (e)=>{ if(e.target === editModal) closeEdit(); });

    const editSaveBtn = document.getElementById('eu_save');
    const editDeleteBtn = document.getElementById('eu_delete');
    if (editSaveBtn) {
      editSaveBtn.addEventListener('click', async () => {
        await withBtnLoading(editSaveBtn, async () => {
          if (!editingUserId) return;
          const username = (document.getElementById('eu_username').value || '').trim();
          const password = document.getElementById('eu_password').value || '';
          const role = document.getElementById('eu_role').value || 'user';
          const ui_language = document.getElementById('eu_ui_language').value || 'da';
          const search_language = document.getElementById('eu_search_language').value || 'da';
          if (!username) { showStatus(tr('users_status_username_required'), 'err'); return; }
          const payload = { username, role, ui_language, search_language };
          if (password) payload.password = password;
          const rr = await fetch('/api/admin/users/' + editingUserId, { method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
          const jj = await rr.json();
          if (!rr.ok || !jj.ok) { showStatus(`${tr('users_status_update_failed')} ${((jj && jj.error) || '')}`.trim(), 'err'); return; }
          showStatus(tr('users_status_updated'), 'ok');
          closeEdit();
          renderUsersPanel();
        });
      });
    }

    if (editDeleteBtn) {
      editDeleteBtn.addEventListener('click', async () => {
        if (!editingUserId) return;
        if (!confirm(`${tr('users_confirm_delete')} #${editingUserId}?`)) return;
        await withBtnLoading(editDeleteBtn, async () => {
          const rr = await fetch('/api/admin/users/' + editingUserId, { method:'DELETE' });
          const jj = await rr.json();
          if (!rr.ok || !jj.ok) { showStatus(`${tr('users_status_delete_failed')} ${((jj && jj.error) || '')}`.trim(), 'err'); return; }
          showStatus(tr('users_status_deleted'), 'ok');
          closeEdit();
          renderUsersPanel();
        });
      });
    }

    // Expand/collapse login log details
    wrap.querySelectorAll('.log-toggle').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.getAttribute('data-target');
        const row = document.getElementById(id);
        if (!row) return;
        const hidden = row.classList.toggle('hidden');
        btn.textContent = hidden ? 'Vis mere' : 'Skjul';
      });
    });
    // Pager handlers
    const prevBtn = document.getElementById('log_prev');
    const nextBtn = document.getElementById('log_next');
    prevBtn && prevBtn.addEventListener('click', () => {
      const p = parseInt(window.usersLogPage || '1', 10) || 1;
      if (p <= 1) return;
      window.usersLogPage = p - 1;
      renderUsersPanel();
    });
    nextBtn && nextBtn.addEventListener('click', () => {
      const p = parseInt(window.usersLogPage || '1', 10) || 1;
      const total = Math.max(1, Math.ceil(((Array.isArray(loginAudit)?loginAudit.length:0)) / 4));
      if (p >= total) return;
      window.usersLogPage = p + 1;
      renderUsersPanel();
    });

    // small helper for button loading states
    const withBtnLoading = async (btn, fn) => {
      if (!btn || typeof fn !== 'function') return await fn?.();
      const prevDisabled = btn.disabled;
      btn.classList.add('loading');
      btn.disabled = true;
      try { return await fn(); }
      finally { btn.classList.remove('loading'); btn.disabled = prevDisabled; }
    };

    // modal wiring
    const modal = document.getElementById('nu_modal');
    const openBtn = document.getElementById('nu_open');
    const closeBtn = document.getElementById('nu_close');
    const cancelBtn = document.getElementById('nu_cancel');
    const nuAclBtn = document.getElementById('nu_acl');
    const nuAclCount = document.getElementById('nu_acl_count');
    let newUserAllowedFolders = [];
    const setNuAclCount = () => {
      const n = Array.isArray(newUserAllowedFolders) ? newUserAllowedFolders.length : 0;
      if (nuAclCount) nuAclCount.textContent = n ? `${n} mapper valgt` : 'Ingen mapper valgt';
    };
    function open(){ if(modal) modal.classList.remove('hidden'); }
    function clear(){
      const u = document.getElementById('nu_username');
      const p = document.getElementById('nu_password');
      const r = document.getElementById('nu_role');
      const f = document.getElementById('nu_2fa');
      const ul = document.getElementById('nu_ui_language');
      const sl = document.getElementById('nu_search_language');
      if (u) u.value = '';
      if (p) p.value = '';
      if (r) r.value = 'user';
      if (f) f.checked = false;
      if (ul) ul.value = 'da';
      if (sl) sl.value = 'da';
      newUserAllowedFolders = [];
      setNuAclCount();
    }
    function close(){ if(modal) { modal.classList.add('hidden'); clear(); } }
    openBtn && openBtn.addEventListener('click', open);
    closeBtn && closeBtn.addEventListener('click', close);
    cancelBtn && cancelBtn.addEventListener('click', close);
    modal && modal.addEventListener('click', (e)=>{ if(e.target === modal) close(); });

    // Password reveal in create-user modal
    const nuPwToggle = document.getElementById('nu_pw_toggle');
    const nuPwInput = document.getElementById('nu_password');
    if (nuPwToggle && nuPwInput) {
      nuPwToggle.addEventListener('click', () => {
        nuPwInput.type = (nuPwInput.type === 'password') ? 'text' : 'password';
        try { nuPwInput.focus({ preventScroll: true }); } catch {}
      });
    }

    // Open ACL modal for new user
    nuAclBtn && nuAclBtn.addEventListener('click', () => {
      if (!availableFolders) return;
      aclEditingUserId = null; // pre-create mode
      if (aclUserLabel) aclUserLabel.textContent = `Mappeadgang: ny bruger`;
      setFolderSelection('ua_folder_access', newUserAllowedFolders || [], availableFolders);
      bindAclHierarchy('ua_folder_access');
      if (aclModal) aclModal.classList.remove('hidden');
    });

    // bind create (modal)
    const saveBtn = document.getElementById('nu_save');
    if (saveBtn){
      saveBtn.addEventListener('click', async ()=>{
        await withBtnLoading(saveBtn, async () => {
          const username = (document.getElementById('nu_username').value || '').trim();
          const password = document.getElementById('nu_password').value || '';
          const role = document.getElementById('nu_role').value || 'user';
          const ui_language = document.getElementById('nu_ui_language').value || 'da';
          const search_language = document.getElementById('nu_search_language').value || 'da';
          const enforce_2fa = !!(document.getElementById('nu_2fa') && document.getElementById('nu_2fa').checked);
          if (!username || !password){ showStatus(tr('users_status_username_password_required'), 'err'); return; }
          const payload = { username, password, role, enforce_2fa, ui_language, search_language, allowed_folders: newUserAllowedFolders || [] };
          const rr = await fetch('/api/admin/users', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
          const raw = await rr.text();
          let jj; try { jj = JSON.parse(raw); } catch(e){ jj = null; }
          if (!rr.ok || !jj || !jj.ok){
            const snippet = raw ? raw.slice(0,200) : '';
            showStatus(`${tr('users_status_create_failed')} ${jj && jj.error ? jj.error : snippet}`.trim(), 'err');
            return;
          }
          showStatus(tr('users_status_created'), 'ok');
          close();
          renderUsersPanel();
        });
      });
    }
  }catch(e){ wrap.innerHTML = `<div class="empty">${tr('users_panel_render_error')}: ${e}</div>`; }
}

async function renderTwofaPanel(){
  const wrap = document.getElementById('twofaPanelInner');
  if (!wrap) return;
  wrap.textContent = tr('twofa_loading');
  try{
    const r = await fetch('/api/me/2fa');
    const js = await r.json();
    if (!r.ok || !js.ok){ wrap.innerHTML = `<div class="empty">${tr('twofa_load_failed')}</div>`; return; }
    const enabled = !!js.enabled;
    const daysVal = (js.remember_days||0);
    // Build UI depending on state
    let leftCol = '';
    if (!enabled && js.qr) {
      leftCol = `<img src="${js.qr}" alt="QR" style="width:140px;height:140px;border:1px solid var(--border);border-radius:8px;background:#fff;"/>`;
    }
    let secretRow = '';
    const toggleLabel = enabled ? tr('twofa_disable') : tr('twofa_enable');
    const toggleClass = enabled ? 'btn danger' : 'btn primary';
    const regenBtnHtml = enabled ? `<button id="tf_regen" class="btn">${escapeHtml(tr('twofa_regen'))}</button>` : '';
    wrap.innerHTML = `
      <div class="panel" style="display:flex;gap:16px;align-items:flex-start;flex-wrap:wrap;">
        ${leftCol}
        <div style="flex:1;min-width:260px;">
          <div class="form-row"><label>${tr('twofa_remember_days')}</label><input id="tf_days" class="input-number" type="number" min="0" max="30" value="${daysVal}"></div>
          ${secretRow}
          <div class="form-row"><label>${tr('twofa_onetime_code')}</label><input id="tf_code" class="input-number" placeholder="${tr('twofa_code_placeholder')}" autocomplete="one-time-code"></div>
          <div class="actions" style="flex-wrap:wrap;gap:8px;justify-content:flex-start;">
            <button id="tf_toggle" class="${toggleClass}">${toggleLabel}</button>
            <button id="tf_save" class="btn">${tr('twofa_save_btn')}</button>
            ${regenBtnHtml}
          </div>
          <div class="mini-label" style="margin-top:6px;">${tr('twofa_status_label')}: <strong>${enabled ? tr('twofa_status_enabled') : tr('twofa_status_disabled')}</strong></div>
        </div>
      </div>
    `;
    async function post(action){
      const payload = { action, code: (document.getElementById('tf_code').value||'').trim(), days: parseInt(document.getElementById('tf_days').value || '0',10) };
      const rr = await fetch('/api/me/2fa', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
      const jj = await rr.json();
      if (!rr.ok || !jj.ok){ showStatus(`${tr('twofa_error_prefix')} ${(jj && jj.error || '')}`.trim(), 'err'); return; }
      showStatus(tr('twofa_updated'), 'ok');
      renderTwofaPanel();
    }
    document.getElementById('tf_toggle').addEventListener('click', ()=>post(enabled ? 'disable' : 'enable'));
    document.getElementById('tf_save').addEventListener('click', ()=>post('save'));
    const regenBtn = document.getElementById('tf_regen');
    regenBtn && regenBtn.addEventListener('click', ()=>post('regen'));
  }catch(e){ wrap.innerHTML = `<div class="empty">Fejl: ${e}</div>`; }
}

async function renderProfilePanel() {
  const wrap = document.getElementById('profilePanelInner');
  wrap.textContent = '...';

  const setProfileInlineStatus = (text, type = 'ok') => {
    const box = document.getElementById('pf_status');
    if (!box) return;
    if (!text) {
      box.textContent = '';
      box.className = 'mini-label hidden';
      return;
    }
    box.textContent = text;
    box.className = `status ${type}`;
    box.classList.remove('hidden');
  };

  try {
    const r = await fetch('/api/me');
    const js = await r.json();
    if (!r.ok || !js.ok || !js.item) {
      wrap.innerHTML = `<div class="empty">${state.uiLanguage === 'en' ? 'Could not load profile.' : 'Kan ikke hente profil.'} ${js && js.error ? js.error : ''}</div>`;
      return;
    }
    const me = js.item;
    state.currentUser = { id: me.id, username: me.username, role: me.role || 'user' };
    wrap.innerHTML = `
      <div class="panel" style="max-width:700px;">
        <div class="form-row"><label for="pf_username">${tr('profile_username')}</label><input id="pf_username" value="${escapeHtml(me.username || '')}" /></div>
        <div class="form-row"><label for="pf_password">${tr('profile_password_new_optional')}</label><input id="pf_password" type="password" placeholder="${tr('profile_password_unchanged_placeholder')}" /></div>
        <div class="form-row"><label for="pf_password2">${tr('profile_password_repeat')}</label><input id="pf_password2" type="password" placeholder="${tr('profile_password_repeat_placeholder')}" /></div>
        <div class="form-row"><label for="pf_ui_language">${tr('profile_ui_lang')}</label>
          <select id="pf_ui_language" class="select">
            <option value="da">Dansk</option>
            <option value="en">English</option>
          </select>
        </div>
        <div class="form-row"><label for="pf_search_language">${tr('profile_search_lang')}</label>
          <select id="pf_search_language" class="select">
            <option value="da">Dansk</option>
            <option value="en">English</option>
          </select>
        </div>
        <div class="form-row"><label for="pf_theme_mode">${tr('profile_theme')}</label>
          <select id="pf_theme_mode" class="select">
            <option value="system">${tr('theme_auto')}</option>
            <option value="light">${tr('theme_light')}</option>
            <option value="dark">${tr('theme_dark')}</option>
          </select>
        </div>
        <div class="actions" style="justify-content:flex-start;margin-bottom:8px;">
          <button id="pf_open_twofa" class="btn">${tr('profile_open_twofa')}</button>
        </div>
        <div class="actions" style="justify-content:flex-end;">
          <button id="pf_save" class="btn primary">${tr('profile_save')}</button>
        </div>
        <div id="pf_status" class="mini-label hidden" style="margin-top:8px;"></div>
      </div>
    `;

    const uiSelect = document.getElementById('pf_ui_language');
    const searchSelect = document.getElementById('pf_search_language');
    if (uiSelect) uiSelect.value = me.ui_language || state.uiLanguage || 'da';
    if (searchSelect) searchSelect.value = me.search_language || state.searchLanguage || 'da';
    const themeSelect = document.getElementById('pf_theme_mode');
    if (themeSelect) themeSelect.value = (me.theme_mode || 'system');

    const openTwofaBtn = document.getElementById('pf_open_twofa');
    if (openTwofaBtn) {
      openTwofaBtn.addEventListener('click', async () => {
        await renderTwofaPanel();
        openTwofaModal();
      });
    }

    const saveBtn = document.getElementById('pf_save');
    if (saveBtn) {
      saveBtn.addEventListener('click', async () => {
        const username = (document.getElementById('pf_username').value || '').trim();
        const password = document.getElementById('pf_password').value || '';
        const password2 = document.getElementById('pf_password2').value || '';
        const ui_language = document.getElementById('pf_ui_language').value || 'da';
        const search_language = document.getElementById('pf_search_language').value || 'da';
        const theme_mode = (document.getElementById('pf_theme_mode').value || 'system');
        if (!username) { setProfileInlineStatus(state.uiLanguage === 'en' ? 'Username cannot be empty.' : 'Brugernavn må ikke være tomt.', 'err'); return; }
        if (password && password !== password2) { setProfileInlineStatus(state.uiLanguage === 'en' ? 'Passwords do not match.' : 'Password matcher ikke.', 'err'); return; }

        setProfileInlineStatus('', 'ok');

        const payload = { username, ui_language, search_language, theme_mode };
        if (password) payload.password = password;

        const rr = await fetch('/api/me/profile', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const jj = await rr.json();
        if (!rr.ok || !jj.ok) {
          setProfileInlineStatus((state.uiLanguage === 'en' ? 'Could not save profile: ' : 'Kunne ikke gemme profil: ') + ((jj && jj.error) || ''), 'err');
          return;
        }

        state.currentUser.username = username;
        state.uiLanguage = resolveUiLanguage(ui_language);
        state.searchLanguage = resolveUiLanguage(search_language);
        applyUiLanguage();
        try { applyTheme(theme_mode); } catch {}
        await loadPhotos();
        setProfileInlineStatus(tr('profile_saved'), 'ok');
        const p1 = document.getElementById('pf_password');
        const p2 = document.getElementById('pf_password2');
        if (p1) p1.value = '';
        if (p2) p2.value = '';
      });
    }
  } catch (e) {
    wrap.innerHTML = `<div class="empty">${state.uiLanguage === 'en' ? 'Error' : 'Fejl'}: ${e}</div>`;
  }
}

// Duplicates UI
async function fetchDuplicates() {
  const dist = parseInt(els.dupeDist ? els.dupeDist.value : 5, 10) || 5;
  const min = parseInt(els.dupeMin ? els.dupeMin.value : 2, 10) || 2;
  try {
    if (els.dupeStatus) { els.dupeStatus.textContent = `Søger efter dupletter (afstand=${dist}, min=${min})...`; els.dupeStatus.classList.remove("hidden", "err"); els.dupeStatus.classList.add("ok"); }
    if (els.dupeResults) els.dupeResults.innerHTML = "";
    const res = await fetch(`/api/duplicates?distance=${encodeURIComponent(dist)}&min=${encodeURIComponent(min)}`);
    const data = await res.json();
    renderDuplicates(data);
    if (els.dupeStatus) { els.dupeStatus.textContent = `Færdig. Checksum-grupper: ${data?.counts?.checksum || 0}, pHash-lige: ${data?.counts?.phash_equal || 0}, pHash-nære: ${data?.counts?.phash_near || 0}`; }
  } catch (e) {
    if (els.dupeStatus) { els.dupeStatus.textContent = `Fejl ved duplet-søgning.`; els.dupeStatus.classList.remove("ok"); els.dupeStatus.classList.add("err"); }
  }
}

function renderDuplicates(data) {
  if (!els.dupeResults) return;
  const wrap = els.dupeResults;
  wrap.innerHTML = "";
  if (!data || !data.groups) {
    wrap.innerHTML = "<div class='empty'>Ingen resultater.</div>";
    return;
  }
  // Build quick lookup of group pairs for intersection (checksum ∩ phash_equal)
  const checksumPairs = new Set();
  const phashPairs = new Set();
  try {
    const findGrp = (reason) => (data.groups.find(g => g.reason === reason) || {}).items || [];
    const addPairs = (items, set) => {
      for (const arr of items) {
        if (arr.length === 2) {
          const ids = [Number(arr[0].id), Number(arr[1].id)].sort((a,b)=>a-b).join(':');
          set.add(ids);
        }
      }
    };
    addPairs(findGrp('checksum'), checksumPairs);
    addPairs(findGrp('phash_equal'), phashPairs);
  } catch {}

  const intersectionPairs = [...checksumPairs].filter(x => phashPairs.has(x));
  if (intersectionPairs.length) {
    const sec = document.createElement('section');
    sec.className = 'dupe-group';
    const title = document.createElement('h4');
    title.textContent = `100% match · ${intersectionPairs.length} par`;
    title.style.cursor = 'pointer';
    const content = document.createElement('div');
    content.style.display = 'none';
    title.addEventListener('click', ()=>{ content.style.display = (content.style.display==='none'?'block':'none'); });
    sec.appendChild(title);
    // Render each pair with merge buttons
    const getItemById = (reason, id) => {
      const g = (data.groups.find(x=>x.reason===reason)||{}).items||[];
      for (const arr of g) {
        for (const it of arr) if (Number(it.id)===Number(id)) return it;
      }
      return null;
    };
    for (const key of intersectionPairs) {
      const [aId, bId] = key.split(':').map(Number);
      const a = getItemById('checksum', aId) || getItemById('phash_equal', aId);
      const b = getItemById('checksum', bId) || getItemById('phash_equal', bId);
      const strip = document.createElement('div');
      strip.className = 'dupe-strip';
      const makeCell = (it) => {
        const cell = document.createElement('div');
        cell.className = 'dupe-item';
        cell.innerHTML = `${it.thumb_url ? `<img class='dupe-thumb' src='${it.thumb_url}' alt=''>` : `<div class='dupe-thumb' style='display:grid;place-items:center;background:#1b1f29;'>Ingen</div>`}<small>${it.filename || ''}</small>`;
        return cell;
      };
      const left = makeCell(a);
      const right = makeCell(b);
      const btnWrap = document.createElement('div');
      btnWrap.style.display = 'grid';
      btnWrap.style.placeItems = 'center';
      btnWrap.style.gap = '6px';
      const lbl = document.createElement('div'); lbl.className='mini-label'; lbl.textContent='100% match';
      const autoBtn = document.createElement('button'); autoBtn.className='btn tiny primary'; autoBtn.textContent='Flet (auto)';
      autoBtn.addEventListener('click', async ()=>{
        try {
          autoBtn.disabled = true; autoBtn.classList.add('loading');
          const r = await fetch('/api/duplicates/merge-auto', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ id1: aId, id2: bId })});
          let txt = await r.text();
          let d = {};
          try { d = JSON.parse(txt); } catch { d = {}; }
          autoBtn.disabled = false; autoBtn.classList.remove('loading');
          if (!r.ok || !d || !d.ok) { showStatus((d && d.error) || (txt || 'Fletning fejlede'), 'err'); alert((d && d.error) || txt || 'Fletning fejlede'); return; }
          showStatus('Flettet automatisk (metadata vurderet).', 'ok');
          strip.parentElement && strip.parentElement.removeChild(strip);
          // Refresh counts so grupper opdateres
          try { if (document.getElementById('dupeResults')) fetchDuplicates(); } catch {}
        } catch { autoBtn.disabled = false; autoBtn.classList.remove('loading'); showStatus('Fletning fejlede', 'err'); }
      });
      btnWrap.appendChild(lbl); btnWrap.appendChild(autoBtn);
      strip.appendChild(left); strip.appendChild(btnWrap); strip.appendChild(right);
      content.appendChild(strip);
    }
    sec.appendChild(content);
    wrap.appendChild(sec);
  }

  for (const grp of data.groups) {
    const sets = grp.items || [];
    if (!sets.length) continue;
    const sec = document.createElement("section");
    sec.className = "dupe-group";
    const titleMap = { checksum: "Checksum", phash_equal: "pHash (ens)", phash_near: `pHash (nær)` };
    const name = titleMap[grp.reason] || grp.reason;
    const header = document.createElement('h4');
    header.textContent = `${name} · ${sets.length} grupper`;
    header.style.cursor = 'pointer';
    sec.appendChild(header);
    const content = document.createElement('div');
    content.style.display = 'none';
    header.addEventListener('click', ()=>{ content.style.display = (content.style.display==='none'?'block':'none'); });
    for (const arr of sets) {
      const strip = document.createElement("div");
      strip.className = "dupe-strip";
      for (const it of arr) {
        const a = document.createElement("a");
        a.className = "dupe-item";
        a.href = it.rel_path ? `/api/original/${encodeURIComponent(it.rel_path)}` : "#";
        a.target = "_blank";
        a.rel = "noopener";
        a.innerHTML = `${it.thumb_url ? `<img class='dupe-thumb' src='${it.thumb_url}' alt=''>` : `<div class='dupe-thumb' style='display:grid;place-items:center;background:#1b1f29;'>Ingen</div>`}<small>${it.filename || ''}</small>`;
        strip.appendChild(a);
      }
      content.appendChild(strip);
    }
    sec.appendChild(content);
    wrap.appendChild(sec);
  }
  if (!wrap.children.length) {
    wrap.innerHTML = "<div class='empty'>Ingen dupletter fundet med de aktuelle kriterier.</div>";
  }
}

// Buttons for duplicates (both buttons do the same action)
els.dupesBtn && els.dupesBtn.addEventListener('click', fetchDuplicates);
els.dupesRun && els.dupesRun.addEventListener('click', fetchDuplicates);

// Live logs
// Determine severity for a log event -> one of: 'ok' | 'warn' | 'err' | 'info'
function classifySeverity(eventName) {
  const ev = String(eventName || '').toLowerCase();
  // Errors: hard failures
  if (ev === 'error' || ev.endsWith('_error') || ev.endsWith('_fail') || ev === 'ai_http_error') return 'err';
  // Warnings: skipped or not critical changes
  if (ev === 'skip_unchanged' || ev === 'no_new' || ev === 'upload_skip_unsupported' || ev === 'upload_skip_blocked_file_type' || ev === 'share_upload_skip_blocked_file_type' || ev === 'missing' || ev.endsWith('_check')) return 'warn';
  // Success/info: the rest of positive events
  if (ev.endsWith('_done') || ev.endsWith('_saved') || ev.endsWith('_ok') || ev === 'indexed' || ev === 'faces_detect' || ev === 'faces_index_done' || ev === 'face_saved' || ev === 'upload_indexed' || ev === 'rethumb_ok') return 'ok';
  return 'info';
}

function appendLogLine(text, level = 'info') {
  const makeLineEl = (container) => {
    if (!container) return;
    const line = document.createElement('span');
    line.className = `log-line log-${level}`;
    line.textContent = text;
    container.appendChild(line);
    // Trim to keep DOM light
    const maxLines = (container.id === 'mainLogs') ? 1200 : 400;
    while (container.childElementCount > maxLines) {
      container.removeChild(container.firstElementChild);
    }
    container.scrollTop = container.scrollHeight;
  };
  makeLineEl(els.logsBox);
  makeLineEl(els.mainLogsBox);
}

function fmtLogTime(ts) {
  const raw = (ts == null) ? '' : String(ts).trim();
  if (!raw) return '-';
  try {
    const d = new Date(raw);
    if (!Number.isFinite(d.getTime())) return raw;
    const dd = String(d.getDate()).padStart(2, '0');
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const yyyy = d.getFullYear();
    const hh = String(d.getHours()).padStart(2, '0');
    const mi = String(d.getMinutes()).padStart(2, '0');
    const ss = String(d.getSeconds()).padStart(2, '0');
    return `${dd}-${mm}-${yyyy} ${hh}:${mi}:${ss}`;
  } catch {
    return raw;
  }
}

async function pollLogs() {
  if (!state.logsRunning) return;
  try {
    const res = await fetch(`/api/logs?after=${state.logsAfter}`);
    // If user lacks permission (401/403), stop polling to avoid spam
    if (res && (res.status === 401 || res.status === 403)) {
      stopLogs();
      return;
    }
    if (!res.ok) {
      throw new Error('logs fetch failed');
    }
    const data = await res.json();
    if (data && data.items) {
      for (const it of data.items) {
        let extra = "";
        if (it.rel_path) extra += ` :: ${it.rel_path}`;
        if (it.from_path) extra += ` ← ${it.from_path}`;
        if (typeof it.distance !== "undefined") extra += ` [d=${it.distance}]`;
        if (typeof it.scanned !== "undefined") extra += ` scanned=${it.scanned}`;
        if (typeof it.updated !== "undefined") extra += ` updated=${it.updated}`;
        if (typeof it.errors !== "undefined") extra += ` errors=${it.errors}`;
        if (typeof it.missing !== "undefined") extra += ` missing=${it.missing}`;
        if (typeof it.heic_converted !== "undefined") extra += ` converted=${it.heic_converted}`;
        // Upload postprocess summaries: include useful counters
        if (typeof it.files !== "undefined") extra += ` files=${it.files}`;
        if (typeof it.indexed !== "undefined") extra += ` indexed=${it.indexed}`;
        if (typeof it.faces_scanned !== "undefined") extra += ` faces_scanned=${it.faces_scanned}`;
        if (typeof it.faces_found !== "undefined") extra += ` faces_found=${it.faces_found}`;
        if (typeof it.index_errors !== "undefined") extra += ` index_errors=${it.index_errors}`;
        if (typeof it.faces_errors !== "undefined") extra += ` faces_errors=${it.faces_errors}`;
        if (typeof it.ai_done !== "undefined") extra += ` ai=${it.ai_done}`;
        if (typeof it.ai_errors !== "undefined") extra += ` ai_errors=${it.ai_errors}`;
        if (typeof it.ai_desc_done !== "undefined") extra += ` ai_desc=${it.ai_desc_done}`;
        if (typeof it.ai_desc_errors !== "undefined") extra += ` ai_desc_errors=${it.ai_desc_errors}`;
        if (it.error) extra += ` :: ${it.error}`;
        const label = (it.event === 'skip_unchanged' || it.event === 'no_new') ? 'no new' : it.event;
        const msg = `[${fmtLogTime(it.t)}] ${label}${extra}`;
        const lvl = classifySeverity(it.event);
        appendLogLine(msg, lvl);
        state.logsAfter = it.id;
      }
    }
  } catch {}
  setTimeout(pollLogs, 1000);
}

function startLogs() {
  state.logsRunning = true;
  if (els.logsStart) els.logsStart.textContent = "Stop";
  pollLogs();
}
function stopLogs() {
  state.logsRunning = false;
  if (els.logsStart) els.logsStart.textContent = "Start";
}

async function clearLogs() {
  try { await fetch('/api/logs/clear', { method: 'POST' }); } catch {}
  state.logsAfter = 0;
  if (els.logsBox) els.logsBox.innerHTML = "";
  if (els.mainLogsBox) els.mainLogsBox.innerHTML = "";
}

els.logsStart && els.logsStart.addEventListener('click', () => {
  if (state.logsRunning) stopLogs(); else startLogs();
});
els.logsClear && els.logsClear.addEventListener('click', clearLogs);
els.mainLogsClear && els.mainLogsClear.addEventListener('click', clearLogs);
els.factoryResetBtn && els.factoryResetBtn.addEventListener('click', factoryReset);
els.fixThumbsBtn && els.fixThumbsBtn.addEventListener('click', fixMissingThumbs);
