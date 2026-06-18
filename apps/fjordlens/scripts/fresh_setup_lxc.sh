#!/usr/bin/env sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_DIR="$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${ENV_FILE:-${REPO_DIR}/.env}"
EXAMPLE_ENV="${REPO_DIR}/.env.example"

if [ -t 1 ]; then
  if command -v clear >/dev/null 2>&1; then
    clear || printf '\033c'
  else
    printf '\033c'
  fi
fi

ask_input() {
  prompt="$1"
  default="${2:-}"
  example="${3:-}"
  explain="${4:-}"
  printf "\n%s\n" "$prompt" >&2
  if [ -n "$explain" ]; then
    printf "Description: %s\n" "$explain" >&2
  fi
  if [ -n "$example" ]; then
    printf "Example: %s\n" "$example" >&2
  fi
  if [ -n "$default" ]; then
    printf "Default: %s\n" "$default" >&2
  fi
  printf "Answer (press Enter for default): " >&2
  IFS= read -r answer || true
  if [ -z "$answer" ]; then
    printf "%s" "$default"
  else
    printf "%s" "$answer"
  fi
}

ask_yes_no() {
  prompt="$1"
  default="${2:-y}"
  while :; do
    printf "\n%s\n" "$prompt" >&2
    if [ "$default" = "y" ]; then
      printf "Answer [Y/n] (Enter=Y): " >&2
    else
      printf "Answer [y/N] (Enter=N): " >&2
    fi
    IFS= read -r answer || true
    answer="$(printf "%s" "$answer" | tr '[:upper:]' '[:lower:]')"
    if [ -z "$answer" ]; then
      answer="$default"
    fi
    case "$answer" in
      y|yes) return 0 ;;
      n|no) return 1 ;;
      *) echo "Please answer y or n." ;;
    esac
  done
}

print_cmd() {
  printf "  > %s\n" "$*"
}

detect_host_ip() {
  ip_candidate=""
  if command -v hostname >/dev/null 2>&1; then
    ip_candidate="$(hostname -I 2>/dev/null | awk '{for(i=1;i<=NF;i++) if ($i !~ /^127\./) {print $i; exit}}')"
  fi
  if [ -z "$ip_candidate" ] && command -v ip >/dev/null 2>&1; then
    ip_candidate="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '/src/ {for(i=1;i<=NF;i++) if($i=="src") {print $(i+1); exit}}')"
  fi
  if [ -z "$ip_candidate" ] && command -v hostname >/dev/null 2>&1; then
    ip_candidate="$(hostname 2>/dev/null || true)"
  fi
  if [ -z "$ip_candidate" ]; then
    ip_candidate="localhost"
  fi
  printf "%s" "$ip_candidate"
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "ERROR: Missing required command: $1"
    exit 1
  }
}

is_truthy() {
  case "$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]')" in
    1|true|yes|on) return 0 ;;
    *) return 1 ;;
  esac
}

csv_has() {
  csv="$1"
  needle="$2"
  old_ifs="$IFS"
  IFS=','
  for item in $csv; do
    clean="$(printf '%s' "$item" | tr -d '[:space:]')"
    if [ "$clean" = "$needle" ]; then
      IFS="$old_ifs"
      return 0
    fi
  done
  IFS="$old_ifs"
  return 1
}

char_major() {
  device_path="$1"
  if [ ! -e "$device_path" ]; then
    return 0
  fi
  ls -l "$device_path" 2>/dev/null | awk 'NR==1 {gsub(",", "", $5); print $5}'
}

dir_char_major() {
  dir_path="$1"
  if [ ! -d "$dir_path" ]; then
    return 0
  fi
  ls -l "$dir_path" 2>/dev/null | awk 'NR>1 && $1 ~ /^c/ {gsub(",", "", $5); print $5; exit}'
}

ensure_absolute_dir() {
  path="$1"
  label="$2"
  if [ -z "$path" ]; then
    echo "ERROR: ${label} is empty."
    exit 1
  fi
  case "$path" in
    /*) ;;
    *)
      echo "ERROR: ${label} must be an absolute path, got: ${path}"
      exit 1
      ;;
  esac
  mkdir -p "$path"
  if [ ! -d "$path" ]; then
    echo "ERROR: Could not create/read directory for ${label}: ${path}"
    exit 1
  fi
}

assert_writable() {
  path="$1"
  label="$2"
  probe="${path}/.fjordlens_write_test.$$"
  if ! ( : > "$probe" ) 2>/dev/null; then
    echo "ERROR: ${label} is not writable: ${path}"
    exit 1
  fi
  rm -f "$probe" >/dev/null 2>&1 || true
}

mount_field() {
  path="$1"
  field="$2"
  findmnt -T "$path" -n -o "$field" 2>/dev/null | head -n 1 || true
}

report_mount() {
  path="$1"
  label="$2"
  expected_csv="$3"
  target="$(mount_field "$path" TARGET)"
  source="$(mount_field "$path" SOURCE)"
  fstype="$(mount_field "$path" FSTYPE)"
  if [ -z "$target" ] || [ -z "$fstype" ]; then
    echo "ERROR: Could not resolve mount info for ${label}: ${path}"
    exit 1
  fi
  echo "    ${label}: ${path}"
  echo "      mount: ${source} on ${target} (fstype=${fstype})"
  if [ -n "$expected_csv" ] && ! csv_has "$expected_csv" "$fstype"; then
    echo "ERROR: ${label} fstype '${fstype}' is not in EXPECT list: ${expected_csv}"
    exit 1
  fi
}

require_runtime_tools() {
  need_cmd docker
  need_cmd findmnt
  if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker daemon is not reachable from inside this LXC."
    echo "       FjordLens and the in-app updater both require local Docker access."
    exit 1
  fi
  if [ ! -S /var/run/docker.sock ]; then
    echo "ERROR: /var/run/docker.sock was not found."
    echo "       The in-app updater mounts this socket so it can rebuild/restart FjordLens."
    exit 1
  fi
  docker compose version >/dev/null 2>&1 || {
    echo "ERROR: docker compose plugin not available."
    exit 1
  }
}

load_env_with_defaults() {
  if [ -f "$ENV_FILE" ]; then
    set -a
    # shellcheck disable=SC1090
    . "$ENV_FILE"
    set +a
  fi

  : "${APP_PORT:=9080}"
  : "${APP_REPO_DIR:=${REPO_DIR}}"
  : "${DATA_DIR:=/opt/fjordlens-data/appdata}"
  : "${UPLOADS_HOST_DIR:=/mnt/fjordlens-nfs/uploads}"
  : "${THUMBS_HOST_DIR:=/opt/fjordlens-data/thumbs}"
  : "${TZ:=Europe/Copenhagen}"
  : "${LOG_LEVEL:=INFO}"
  : "${AI_DEVICE:=auto}"
  : "${ENABLE_GPU_GUIDE:=1}"
  : "${SQLITE_JOURNAL_MODE:=}"
  : "${SQLITE_BUSY_TIMEOUT_MS:=10000}"
  : "${ENABLE_LIBRARY_SOURCE:=0}"
  : "${ENABLE_SCAN_FEATURES:=0}"
  : "${PHOTOFRAME_TEXT_ONLY:=0}"
  : "${PHOTOFRAME_UPDATE_UPLOAD_MAX_BYTES:=314572800}"
  : "${FJORDLENS_AUTO_UPDATE_CHECK:=1}"
  : "${FJORDLENS_AUTO_UPDATE_CHECK_INTERVAL_MINUTES:=30}"
  : "${FJORDLENS_UPDATER_TIMEOUT_SEC:=20}"
  : "${EXPECT_DATA_FSTYPES:=ext4,xfs,btrfs,overlay}"
  : "${EXPECT_UPLOADS_FSTYPES:=}"
  : "${EXPECT_THUMBS_FSTYPES:=ext4,xfs,btrfs,overlay}"
  : "${EXPECT_PHOTO_FSTYPES:=}"
  : "${PHOTO_DIR:=/mnt/fjordlens-nfs/photos}"
  : "${LXC_MOUNTS_MANAGED_BY_PROXMOX:=1}"
}

write_env_file() {
  target="$1"
  cat > "$target" <<EOF2
# Generated by scripts/fresh_setup_lxc.sh
APP_PORT=${APP_PORT}
APP_REPO_DIR=${APP_REPO_DIR}
DATA_DIR=${DATA_DIR}
UPLOADS_HOST_DIR=${UPLOADS_HOST_DIR}
THUMBS_HOST_DIR=${THUMBS_HOST_DIR}
TZ=${TZ}
LOG_LEVEL=${LOG_LEVEL}
AI_DEVICE=${AI_DEVICE}
ENABLE_GPU_GUIDE=${ENABLE_GPU_GUIDE}
SQLITE_JOURNAL_MODE=${SQLITE_JOURNAL_MODE}
SQLITE_BUSY_TIMEOUT_MS=${SQLITE_BUSY_TIMEOUT_MS}
ENABLE_LIBRARY_SOURCE=${ENABLE_LIBRARY_SOURCE}
ENABLE_SCAN_FEATURES=${ENABLE_SCAN_FEATURES}
PHOTOFRAME_TEXT_ONLY=${PHOTOFRAME_TEXT_ONLY}
PHOTOFRAME_UPDATE_UPLOAD_MAX_BYTES=${PHOTOFRAME_UPDATE_UPLOAD_MAX_BYTES}
FJORDLENS_AUTO_UPDATE_CHECK=${FJORDLENS_AUTO_UPDATE_CHECK}
FJORDLENS_AUTO_UPDATE_CHECK_INTERVAL_MINUTES=${FJORDLENS_AUTO_UPDATE_CHECK_INTERVAL_MINUTES}
FJORDLENS_UPDATER_TIMEOUT_SEC=${FJORDLENS_UPDATER_TIMEOUT_SEC}
EXPECT_DATA_FSTYPES=${EXPECT_DATA_FSTYPES}
EXPECT_UPLOADS_FSTYPES=${EXPECT_UPLOADS_FSTYPES}
EXPECT_THUMBS_FSTYPES=${EXPECT_THUMBS_FSTYPES}
EXPECT_PHOTO_FSTYPES=${EXPECT_PHOTO_FSTYPES}
LXC_MOUNTS_MANAGED_BY_PROXMOX=${LXC_MOUNTS_MANAGED_BY_PROXMOX}
EOF2

  if is_truthy "$ENABLE_LIBRARY_SOURCE"; then
    printf "PHOTO_DIR=%s\n" "$PHOTO_DIR" >> "$target"
  else
    cat >> "$target" <<EOF2
# PHOTO_DIR is optional when ENABLE_LIBRARY_SOURCE=0
# PHOTO_DIR=/mnt/fjordlens-photos
EOF2
  fi

  if [ -n "${FJORDHUB_URL:-}" ] || [ -n "${FJORDHUB_API_KEY:-}" ] || [ -n "${FJORDHUB_APP_ID:-}" ]; then
    cat >> "$target" <<EOF2
FJORDHUB_URL=${FJORDHUB_URL:-}
FJORDHUB_APP_ID=${FJORDHUB_APP_ID:-fjordlens}
FJORDHUB_API_KEY=${FJORDHUB_API_KEY:-}
EOF2
  fi
}

preflight_paths() {
  echo
  echo "==> Mount preflight"
  print_cmd "mkdir -p ${DATA_DIR}"
  ensure_absolute_dir "$DATA_DIR" "DATA_DIR"
  print_cmd "mkdir -p ${UPLOADS_HOST_DIR}"
  ensure_absolute_dir "$UPLOADS_HOST_DIR" "UPLOADS_HOST_DIR"
  print_cmd "mkdir -p ${THUMBS_HOST_DIR}"
  ensure_absolute_dir "$THUMBS_HOST_DIR" "THUMBS_HOST_DIR"

  print_cmd "mkdir -p ${UPLOADS_HOST_DIR}/originals ${UPLOADS_HOST_DIR}/converted"
  mkdir -p "${UPLOADS_HOST_DIR}/originals" "${UPLOADS_HOST_DIR}/converted"

  assert_writable "$DATA_DIR" "DATA_DIR"
  assert_writable "$UPLOADS_HOST_DIR" "UPLOADS_HOST_DIR"
  assert_writable "$THUMBS_HOST_DIR" "THUMBS_HOST_DIR"

  report_mount "$DATA_DIR" "DATA_DIR" "$EXPECT_DATA_FSTYPES"
  report_mount "$UPLOADS_HOST_DIR" "UPLOADS_HOST_DIR" "$EXPECT_UPLOADS_FSTYPES"
  report_mount "$THUMBS_HOST_DIR" "THUMBS_HOST_DIR" "$EXPECT_THUMBS_FSTYPES"

  if is_truthy "$ENABLE_LIBRARY_SOURCE"; then
    if [ -z "${PHOTO_DIR:-}" ]; then
      echo "ERROR: ENABLE_LIBRARY_SOURCE=1 requires PHOTO_DIR in ${ENV_FILE}"
      exit 1
    fi
    if [ ! -d "$PHOTO_DIR" ]; then
      echo "ERROR: PHOTO_DIR does not exist: ${PHOTO_DIR}"
      exit 1
    fi
    report_mount "$PHOTO_DIR" "PHOTO_DIR" "$EXPECT_PHOTO_FSTYPES"
  else
    echo "    PHOTO_DIR check skipped (ENABLE_LIBRARY_SOURCE=${ENABLE_LIBRARY_SOURCE})"
  fi
}

print_gpu_host_fix_hint() {
  nvidia_uvm_major="$1"
  nvidia_caps_major="$2"
  if [ -z "$nvidia_uvm_major" ]; then
    nvidia_uvm_major="510"
  fi
  if [ -z "$nvidia_caps_major" ]; then
    nvidia_caps_major="235"
  fi
  cat <<EOF2
    Suggested Proxmox host checks (run on host, not inside LXC):
      pct stop <CTID>
      nano /etc/pve/lxc/<CTID>.conf

    Ensure these lines exist:
      features: nesting=1,keyctl=1
      lxc.apparmor.profile: unconfined
      lxc.cgroup2.devices.allow: c 195:* rwm
      lxc.cgroup2.devices.allow: c ${nvidia_uvm_major}:* rwm
      lxc.cgroup2.devices.allow: c ${nvidia_caps_major}:* rwm
      lxc.mount.entry: /dev/nvidia0 dev/nvidia0 none bind,optional,create=file
      lxc.mount.entry: /dev/nvidiactl dev/nvidiactl none bind,optional,create=file
      lxc.mount.entry: /dev/nvidia-uvm dev/nvidia-uvm none bind,optional,create=file
      lxc.mount.entry: /dev/nvidia-uvm-tools dev/nvidia-uvm-tools none bind,optional,create=file
      lxc.mount.entry: /dev/nvidia-caps dev/nvidia-caps none bind,optional,create=dir
      lxc.mount.entry: /dev/nvidia-modeset dev/nvidia-modeset none bind,optional,create=file
      lxc.mount.entry: /sys/class/drm sys/class/drm none ro,bind,optional,create=dir

    Then restart the CT:
      pct start <CTID>
EOF2
}

ensure_nvidia_no_cgroups() {
  cfg="/etc/nvidia-container-runtime/config.toml"
  NVIDIA_RUNTIME_UPDATED=0
  if [ ! -f "$cfg" ]; then
    echo "WARNING: NVIDIA runtime config not found: $cfg"
    return 1
  fi
  if grep -Eq '^[[:space:]]*no-cgroups[[:space:]]*=[[:space:]]*true([[:space:]]|$)' "$cfg"; then
    echo "    NVIDIA runtime already has no-cgroups=true"
    return 0
  fi
  print_cmd "sed -i 's/^#\\?no-cgroups *= *.*/no-cgroups = true/' ${cfg}"
  if grep -Eq '^[[:space:]]*#?[[:space:]]*no-cgroups[[:space:]]*=' "$cfg"; then
    sed -i 's/^[[:space:]]*#\?[[:space:]]*no-cgroups[[:space:]]*=.*/no-cgroups = true/' "$cfg"
  else
    printf "\nno-cgroups = true\n" >> "$cfg"
  fi
  if grep -Eq '^[[:space:]]*no-cgroups[[:space:]]*=[[:space:]]*true([[:space:]]|$)' "$cfg"; then
    NVIDIA_RUNTIME_UPDATED=1
    echo "    NVIDIA runtime updated: no-cgroups=true"
    return 0
  fi
  echo "WARNING: Could not set no-cgroups=true in $cfg"
  return 1
}

gpu_preflight_lxc() {
  if [ "$AI_DEVICE" = "cpu" ]; then
    echo
    echo "==> GPU preflight skipped (AI_DEVICE=cpu)"
    return 0
  fi

  echo
  echo "==> GPU preflight (LXC)"

  uvm_major="$(char_major /dev/nvidia-uvm || true)"
  caps_major="$(dir_char_major /dev/nvidia-caps || true)"
  if [ -e /dev/nvidia0 ]; then
    echo "    Found /dev/nvidia0"
  else
    echo "WARNING: /dev/nvidia0 not found inside this LXC."
    print_gpu_host_fix_hint "$uvm_major" "$caps_major"
    return 1
  fi
  if [ -n "$uvm_major" ]; then
    echo "    Detected /dev/nvidia-uvm major: $uvm_major"
  fi
  if [ -n "$caps_major" ]; then
    echo "    Detected /dev/nvidia-caps major: $caps_major"
  fi

  NVIDIA_RUNTIME_UPDATED=0
  if ensure_nvidia_no_cgroups; then
    :
  else
    echo "WARNING: Continuing, but NVIDIA runtime may not initialize CUDA in LXC."
  fi
  if [ "${NVIDIA_RUNTIME_UPDATED:-0}" = "1" ]; then
    echo "    Restarting Docker to apply runtime config"
    if command -v systemctl >/dev/null 2>&1; then
      systemctl restart docker >/dev/null 2>&1 || service docker restart >/dev/null 2>&1 || true
    else
      service docker restart >/dev/null 2>&1 || true
    fi
  fi

  print_cmd "docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi"
  if ! docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi >/dev/null 2>&1; then
    echo "WARNING: Docker cannot run nvidia-smi with --gpus all."
    print_gpu_host_fix_hint "$uvm_major" "$caps_major"
    return 1
  fi
  echo "    CUDA container smoke test: OK"

  print_cmd "docker run --rm --gpus all pytorch/pytorch:2.1.2-cuda12.1-cudnn8-runtime python -c \"import torch; print(torch.cuda.is_available())\""
  torch_probe="$(docker run --rm --gpus all pytorch/pytorch:2.1.2-cuda12.1-cudnn8-runtime python -c "import torch; print(torch.cuda.is_available()); print(torch.version.cuda); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no gpu')" 2>&1 || true)"
  torch_available="$(printf "%s\n" "$torch_probe" | awk '/^(True|False)$/{v=$0} END{print v}')"
  echo "$torch_probe"
  if [ "$torch_available" != "True" ]; then
    echo "WARNING: PyTorch CUDA probe still reports False."
    print_gpu_host_fix_hint "$uvm_major" "$caps_major"
    return 1
  fi
  echo "    PyTorch CUDA probe: OK"
  return 0
}

run_preflight_and_start() {
  require_runtime_tools
  preflight_paths

  if is_truthy "$ENABLE_GPU_GUIDE"; then
    if ! gpu_preflight_lxc; then
      if [ "$AI_DEVICE" = "cuda" ]; then
        echo "ERROR: AI_DEVICE=cuda but GPU preflight failed."
        echo "Fix the host passthrough/runtime and rerun:"
        echo "  sh scripts/fresh_setup_lxc.sh --start-only"
        exit 1
      fi
      if [ -t 0 ] && [ -t 1 ]; then
        if ! ask_yes_no "GPU preflight failed. Continue with CPU fallback (AI_DEVICE=${AI_DEVICE})?" "n"; then
          echo "Stopped before container start."
          echo "Run again after fixing host GPU passthrough:"
          echo "  sh scripts/fresh_setup_lxc.sh --start-only"
          exit 1
        fi
      else
        echo "WARNING: GPU preflight failed. Continuing (AI_DEVICE=${AI_DEVICE}) may fall back to CPU."
      fi
    fi
  else
    echo
    echo "==> GPU guide skipped (ENABLE_GPU_GUIDE=${ENABLE_GPU_GUIDE})"
  fi

  echo
  echo "==> Starting containers"
  cd "$REPO_DIR"
  print_cmd "docker compose up -d --build"
  docker compose up -d --build
  host_ip="$(detect_host_ip)"
  echo "==> Done"
  echo "    Open: http://${host_ip}:${APP_PORT:-9080}"
}

step_1_basic() {
  echo
  echo "Step 1/7: Basic app settings"
  APP_PORT="$(ask_input "Web port (APP_PORT)" "$APP_PORT" "9080 or 9090" "The port you open in your browser. Enter any free port number.")"
  TZ="$(ask_input "Timezone (TZ)" "$TZ" "Europe/Copenhagen" "Timezone in Region/City format. Affects timestamps in logs and UI.")"
  LOG_LEVEL="$(ask_input "Log level (LOG_LEVEL)" "$LOG_LEVEL" "INFO or DEBUG" "How verbose logs should be. DEBUG shows more details.")"
  ai_device_choice="$(ask_input "AI device preference (AI_DEVICE: auto/cpu/cuda)" "$AI_DEVICE" "auto" "auto uses CUDA when available and falls back to CPU.")"
  ai_device_choice_lc="$(printf "%s" "$ai_device_choice" | tr '[:upper:]' '[:lower:]')"
  case "$ai_device_choice_lc" in
    auto|cpu|cuda) AI_DEVICE="$ai_device_choice_lc" ;;
    *)
      echo "Invalid AI_DEVICE '${ai_device_choice}'. Using auto."
      AI_DEVICE="auto"
      ;;
  esac
  if ask_yes_no "Run guided GPU checks/fixes for Proxmox LXC (ENABLE_GPU_GUIDE)?" "$(is_truthy "$ENABLE_GPU_GUIDE" && echo y || echo n)"; then
    ENABLE_GPU_GUIDE="1"
  else
    ENABLE_GPU_GUIDE="0"
  fi
}

step_2_mounts() {
  echo
  echo "Step 2/7: Proxmox LXC mount strategy"
  echo "  This LXC version does NOT edit /etc/fstab and does NOT mount NFS itself."
  echo "  Expected model: Proxmox host mounts Synology/NFS and bind-mounts paths into the LXC."
  echo "  Example LXC mount points:"
  echo "    uploads: /mnt/fjordlens-uploads"
  echo "    photos : /mnt/fjordlens-photos"
  if ask_yes_no "Use a Proxmox-provided bind mount for uploads?" "y"; then
    UPLOADS_HOST_DIR="$(ask_input "UPLOADS_HOST_DIR inside the LXC" "$UPLOADS_HOST_DIR" "/mnt/fjordlens-nfs/uploads" "Path inside this LXC that points to your uploads bind mount from Proxmox.")"
    if [ -z "$EXPECT_UPLOADS_FSTYPES" ]; then
      EXPECT_UPLOADS_FSTYPES="nfs,nfs4,cifs,fuseblk"
    fi
  else
    UPLOADS_HOST_DIR="$(ask_input "UPLOADS_HOST_DIR inside the LXC" "$UPLOADS_HOST_DIR" "/opt/fjordlens-data/uploads" "Local uploads path inside this LXC.")"
    EXPECT_UPLOADS_FSTYPES=""
  fi
}

step_3_storage() {
  echo
  echo "Step 3/7: Storage paths (inside the LXC)"
  DATA_DIR="$(ask_input "DATA_DIR (db/cache/internal state)" "$DATA_DIR" "/opt/fjordlens-data/appdata" "Stores database, cache, temp files, and internal app data.")"
  THUMBS_HOST_DIR="$(ask_input "THUMBS_HOST_DIR (thumbnails)" "$THUMBS_HOST_DIR" "/opt/fjordlens-data/thumbs" "Root directory where thumbnails are stored. Local storage is recommended.")"
}

step_4_library() {
  echo
  echo "Step 4/7: Optional library source"
  if ask_yes_no "Enable separate read-only library source (PHOTO_DIR)?" "$(is_truthy "$ENABLE_LIBRARY_SOURCE" && echo y || echo n)"; then
    ENABLE_LIBRARY_SOURCE="1"
    PHOTO_DIR="$(ask_input "PHOTO_DIR (library source path)" "$PHOTO_DIR" "/mnt/fjordlens-nfs/photos" "Path inside this LXC pointing to a Proxmox bind mount with your library photos.")"
    if [ -z "$EXPECT_PHOTO_FSTYPES" ]; then
      EXPECT_PHOTO_FSTYPES="nfs,nfs4,cifs,fuseblk"
    fi
  else
    ENABLE_LIBRARY_SOURCE="0"
    EXPECT_PHOTO_FSTYPES=""
  fi
}

step_5_features() {
  echo
  echo "Step 5/7: Feature toggles"
  if ask_yes_no "Enable scan/rescan/rethumb UI + endpoints?" "$(is_truthy "$ENABLE_SCAN_FEATURES" && echo y || echo n)"; then
    ENABLE_SCAN_FEATURES="1"
  else
    ENABLE_SCAN_FEATURES="0"
  fi
}

step_6_updater() {
  echo
  echo "Step 6/7: In-app updater"
  echo "  FjordLens includes an admin-only updater tab."
  echo "  It checks GitHub for new commits and can run the same update flow as scripts/update.sh."
  echo "  The updater container uses /var/run/docker.sock to rebuild/restart the FjordLens services."
  if ask_yes_no "Enable automatic background update checks?" "$(is_truthy "$FJORDLENS_AUTO_UPDATE_CHECK" && echo y || echo n)"; then
    FJORDLENS_AUTO_UPDATE_CHECK="1"
    FJORDLENS_AUTO_UPDATE_CHECK_INTERVAL_MINUTES="$(ask_input "Auto-check interval in minutes" "$FJORDLENS_AUTO_UPDATE_CHECK_INTERVAL_MINUTES" "30" "How often the updater checks origin/main for new commits. Minimum is 5 minutes.")"
    case "$FJORDLENS_AUTO_UPDATE_CHECK_INTERVAL_MINUTES" in
      *[!0-9]*|"") FJORDLENS_AUTO_UPDATE_CHECK_INTERVAL_MINUTES="30" ;;
    esac
    if [ "$FJORDLENS_AUTO_UPDATE_CHECK_INTERVAL_MINUTES" -lt 5 ]; then
      FJORDLENS_AUTO_UPDATE_CHECK_INTERVAL_MINUTES="5"
    fi
  else
    FJORDLENS_AUTO_UPDATE_CHECK="0"
  fi
  FJORDLENS_UPDATER_TIMEOUT_SEC="$(ask_input "Updater API timeout seconds" "$FJORDLENS_UPDATER_TIMEOUT_SEC" "20" "Only affects UI calls to the updater service. The update job itself keeps running in the background.")"
  case "$FJORDLENS_UPDATER_TIMEOUT_SEC" in
    *[!0-9]*|"") FJORDLENS_UPDATER_TIMEOUT_SEC="20" ;;
  esac
}

step_7_sqlite() {
  echo
  echo "Step 7/7: SQLite + mount checks"
  sqlite_choice="$(ask_input "SQLite journal mode (auto/WAL/DELETE/TRUNCATE/PERSIST/MEMORY/OFF)" "${SQLITE_JOURNAL_MODE:-auto}" "auto or DELETE (network storage)" "Choose auto for automatic selection. On some network-backed paths, DELETE can be more stable.")"
  sqlite_choice_lc="$(printf "%s" "$sqlite_choice" | tr '[:upper:]' '[:lower:]')"
  if [ "$sqlite_choice_lc" = "auto" ] || [ -z "$sqlite_choice_lc" ]; then
    SQLITE_JOURNAL_MODE=""
  else
    SQLITE_JOURNAL_MODE="$(printf "%s" "$sqlite_choice" | tr '[:lower:]' '[:upper:]')"
  fi
  SQLITE_BUSY_TIMEOUT_MS="$(ask_input "SQLite busy timeout ms" "$SQLITE_BUSY_TIMEOUT_MS" "10000 or 15000" "Wait time for database locks in milliseconds.")"
  if ask_yes_no "Enable strict fs-type checks?" "n"; then
    EXPECT_UPLOADS_FSTYPES="$(ask_input "EXPECT_UPLOADS_FSTYPES (blank to skip)" "$EXPECT_UPLOADS_FSTYPES" "nfs,nfs4,cifs" "Allowed filesystem types for UPLOADS_HOST_DIR.")"
    EXPECT_THUMBS_FSTYPES="$(ask_input "EXPECT_THUMBS_FSTYPES (blank to skip)" "$EXPECT_THUMBS_FSTYPES" "ext4,xfs,btrfs,overlay" "Allowed filesystem types for THUMBS_HOST_DIR.")"
    EXPECT_DATA_FSTYPES="$(ask_input "EXPECT_DATA_FSTYPES (blank to skip)" "$EXPECT_DATA_FSTYPES" "ext4,xfs,btrfs,overlay" "Allowed filesystem types for DATA_DIR.")"
    if is_truthy "$ENABLE_LIBRARY_SOURCE"; then
      EXPECT_PHOTO_FSTYPES="$(ask_input "EXPECT_PHOTO_FSTYPES (blank to skip)" "$EXPECT_PHOTO_FSTYPES" "nfs,nfs4,cifs" "Allowed filesystem types for PHOTO_DIR.")"
    fi
  else
    :
  fi
}

print_summary() {
  echo
  echo "Summary:"
  echo "  APP_PORT=${APP_PORT}"
  echo "  APP_REPO_DIR=${APP_REPO_DIR}"
  echo "  AI_DEVICE=${AI_DEVICE}"
  echo "  ENABLE_GPU_GUIDE=${ENABLE_GPU_GUIDE}"
  echo "  DATA_DIR=${DATA_DIR}"
  echo "  UPLOADS_HOST_DIR=${UPLOADS_HOST_DIR}"
  echo "  THUMBS_HOST_DIR=${THUMBS_HOST_DIR}"
  echo "  ENABLE_LIBRARY_SOURCE=${ENABLE_LIBRARY_SOURCE}"
  if is_truthy "$ENABLE_LIBRARY_SOURCE"; then
    echo "  PHOTO_DIR=${PHOTO_DIR}"
  fi
  echo "  ENABLE_SCAN_FEATURES=${ENABLE_SCAN_FEATURES}"
  echo "  FJORDLENS_AUTO_UPDATE_CHECK=${FJORDLENS_AUTO_UPDATE_CHECK}"
  if is_truthy "$FJORDLENS_AUTO_UPDATE_CHECK"; then
    echo "  FJORDLENS_AUTO_UPDATE_CHECK_INTERVAL_MINUTES=${FJORDLENS_AUTO_UPDATE_CHECK_INTERVAL_MINUTES}"
  fi
  echo "  LXC_MOUNTS_MANAGED_BY_PROXMOX=${LXC_MOUNTS_MANAGED_BY_PROXMOX}"
  if [ -n "$SQLITE_JOURNAL_MODE" ]; then
    echo "  SQLITE_JOURNAL_MODE=${SQLITE_JOURNAL_MODE}"
  else
    echo "  SQLITE_JOURNAL_MODE=<auto>"
  fi
}

backup_env_once() {
  if [ "${ENV_BACKUP_DONE:-0}" = "1" ]; then
    return 0
  fi
  if [ -f "$ENV_FILE" ]; then
    backup_file="${ENV_FILE}.bak.$(date +%Y%m%d%H%M%S)"
    cp "$ENV_FILE" "$backup_file"
    echo
    echo "Backup of existing env saved to:"
    echo "  ${backup_file}"
  fi
  ENV_BACKUP_DONE=1
}

save_env() {
  backup_env_once
  write_env_file "$ENV_FILE"
  echo
  echo "Wrote configuration:"
  echo "  ${ENV_FILE}"
}

edit_menu() {
  while :; do
    echo
    echo "Edit settings menu:"
    echo "  1) Basic app settings"
    echo "  2) Proxmox/LXC mount paths"
    echo "  3) Storage paths"
    echo "  4) Library source (PHOTO_DIR)"
    echo "  5) Feature toggles"
    echo "  6) In-app updater"
    echo "  7) SQLite + fs-type checks"
    echo "  8) Done editing (back to summary)"
    choice="$(ask_input "Choose section number" "8" "1-8" "Type the number for what you want to edit.")"
    case "$choice" in
      1) step_1_basic ;;
      2) step_2_mounts ;;
      3) step_3_storage ;;
      4) step_4_library ;;
      5) step_5_features ;;
      6) step_6_updater ;;
      7) step_7_sqlite ;;
      8|"") break ;;
      *) echo "Invalid choice. Please select 1-8." ;;
    esac
  done
}

if [ "${1:-}" = "--start-only" ]; then
  echo "==> FjordLens LXC start-only mode"
  echo "    Repo: ${REPO_DIR}"
  echo "    Env : ${ENV_FILE}"
  if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: Missing env file: ${ENV_FILE}"
    echo "Run full wizard first:"
    echo "  sh scripts/fresh_setup_lxc.sh"
    exit 1
  fi
  load_env_with_defaults
  run_preflight_and_start
  exit 0
fi

if [ "${1:-}" != "" ]; then
  echo "Usage:"
  echo "  sh scripts/fresh_setup_lxc.sh               # guided setup for Proxmox LXC"
  echo "  sh scripts/fresh_setup_lxc.sh --start-only  # preflight + start"
  exit 1
fi

echo "==> FjordLens guided setup for Proxmox LXC"
echo "    Repo: ${REPO_DIR}"
echo "    Env : ${ENV_FILE}"
echo "    This variant assumes network mounts are handled by Proxmox host bind mounts."
echo "    It does NOT edit /etc/fstab or mount NFS inside the LXC."
echo "    Tip : press Enter to use the default at each prompt."
echo "    LXC mode expects your Proxmox host to bind-mount the Synology/NFS share into this container, typically at /mnt/fjordlens-nfs."
echo "    The in-app updater is configured here too. It needs Docker access inside this LXC."
echo "    Input examples:"
echo "      - APP_PORT: 9080 or 9090"
echo "      - DATA_DIR: /opt/fjordlens-data/appdata"
echo "      - UPLOADS_HOST_DIR: /mnt/fjordlens-nfs/uploads"
echo "      - PHOTO_DIR: /mnt/fjordlens-nfs/photos"

if [ ! -f "$EXAMPLE_ENV" ]; then
  echo "ERROR: Missing .env.example in repo root."
  exit 1
fi

load_env_with_defaults
step_1_basic
step_2_mounts
step_3_storage
step_4_library
step_5_features
step_6_updater
step_7_sqlite

while :; do
  save_env
  print_summary
  echo
  if ask_yes_no "Run preflight + docker compose up -d --build now?" "y"; then
    run_preflight_and_start
    break
  fi
  edit_menu
  echo
  if ask_yes_no "Return to summary and start prompt?" "y"; then
    continue
  fi
  echo "Skipped start."
  echo "Run later with:"
  echo "  sh scripts/fresh_setup_lxc.sh --start-only"
  break
done
