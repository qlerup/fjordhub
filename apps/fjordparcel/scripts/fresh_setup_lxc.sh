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

generate_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -base64 48 | tr -d '\n/+=' | cut -c1-64
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    python3 - <<'PY'
import base64, os
print(base64.urlsafe_b64encode(os.urandom(48)).decode("ascii").rstrip("=")[:64])
PY
    return 0
  fi
  echo "ERROR: Could not generate secret key. Install openssl or python3 and rerun setup."
  exit 1
}

ensure_secret_key() {
  if [ -n "${SECRET_KEY:-}" ] && [ "$SECRET_KEY" != "change-me-to-a-long-random-string" ]; then
    return 0
  fi
  echo
  echo "SECRET_KEY: Bruges til at sikre sessions og cookies i Flask."
  if ask_yes_no "Generer tilfaeldig SECRET_KEY automatisk?" "y"; then
    SECRET_KEY="$(generate_secret)"
    echo "    Genereret automatisk."
  else
    while :; do
      printf "\nSkriv din SECRET_KEY (mindst 32 tegn): " >&2
      IFS= read -r input || true
      if [ "${#input}" -ge 32 ]; then
        SECRET_KEY="$input"
        break
      fi
      echo "    For kort. Mindst 32 tegn kraeves."
    done
  fi
}

ensure_app_encryption_key() {
  if [ -n "${APP_ENCRYPTION_KEY:-}" ]; then
    return 0
  fi
  echo
  echo "APP_ENCRYPTION_KEY: Bruges til at kryptere gemte mail-credentials (Microsoft/Google)."
  if ask_yes_no "Generer tilfaeldig APP_ENCRYPTION_KEY automatisk?" "y"; then
    APP_ENCRYPTION_KEY="$(generate_secret)"
    echo "    Genereret automatisk."
  else
    while :; do
      printf "\nSkriv din APP_ENCRYPTION_KEY (mindst 32 tegn): " >&2
      IFS= read -r input || true
      if [ "${#input}" -ge 32 ]; then
        APP_ENCRYPTION_KEY="$input"
        break
      fi
      echo "    For kort. Mindst 32 tegn kraeves."
    done
  fi
}

require_runtime_tools() {
  need_cmd docker
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

  : "${APP_PORT:=8096}"
  : "${TZ:=Europe/Copenhagen}"
  : "${SECRET_KEY:=}"
  : "${APP_ENCRYPTION_KEY:=}"
  : "${PUBLIC_BASE_URL:=}"
  : "${DATA_DIR:=${REPO_DIR}/data}"
  : "${DATABASE_PATH:=data/fjordparcel.db}"
  : "${APP_CONFIG_PATH:=data/app_config.json}"
  : "${MS_TOKEN_CACHE_PATH:=data/msal_cache.json}"
  : "${MS_TENANT:=consumers}"
  : "${MS_CLIENT_ID:=}"
  : "${MS_CLIENT_SECRET:=}"
  : "${MS_IMAP_HOST:=outlook.office365.com}"
  : "${MS_IMAP_PORT:=993}"
  : "${MS_IMAP_MAX_SCAN_MESSAGES:=1000}"
  : "${GOOGLE_CLIENT_ID:=}"
  : "${GOOGLE_CLIENT_SECRET:=}"
  : "${GOOGLE_GMAIL_MAX_SCAN_MESSAGES:=1000}"
  : "${FJORDPARCEL_AUTO_UPDATE_CHECK:=1}"
  : "${FJORDPARCEL_AUTO_UPDATE_CHECK_INTERVAL_MINUTES:=30}"
}

write_env_file() {
  target="$1"
  cat > "$target" <<EOF
# Generated by scripts/fresh_setup_lxc.sh
SECRET_KEY=${SECRET_KEY}
APP_ENCRYPTION_KEY=${APP_ENCRYPTION_KEY}
PUBLIC_BASE_URL=${PUBLIC_BASE_URL}
APP_PORT=${APP_PORT}
TZ=${TZ}
DATA_DIR=${DATA_DIR}
DATABASE_PATH=${DATABASE_PATH}
APP_CONFIG_PATH=${APP_CONFIG_PATH}
MS_TOKEN_CACHE_PATH=${MS_TOKEN_CACHE_PATH}
MS_TENANT=${MS_TENANT}
MS_CLIENT_ID=${MS_CLIENT_ID}
MS_CLIENT_SECRET=${MS_CLIENT_SECRET}
MS_IMAP_HOST=${MS_IMAP_HOST}
MS_IMAP_PORT=${MS_IMAP_PORT}
MS_IMAP_MAX_SCAN_MESSAGES=${MS_IMAP_MAX_SCAN_MESSAGES}
GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
GOOGLE_GMAIL_MAX_SCAN_MESSAGES=${GOOGLE_GMAIL_MAX_SCAN_MESSAGES}
FJORDPARCEL_AUTO_UPDATE_CHECK=${FJORDPARCEL_AUTO_UPDATE_CHECK}
FJORDPARCEL_AUTO_UPDATE_CHECK_INTERVAL_MINUTES=${FJORDPARCEL_AUTO_UPDATE_CHECK_INTERVAL_MINUTES}
EOF
}

run_preflight_and_start() {
  require_runtime_tools

  echo
  echo "==> Opretter data-mappe"
  data_dir="${REPO_DIR}/data"
  print_cmd "mkdir -p ${data_dir}"
  mkdir -p "$data_dir"
  print_cmd "chmod 777 ${data_dir}"
  chmod 777 "$data_dir"
  echo "    OK: ${data_dir}"

  echo
  echo "==> Starter containere"
  cd "$REPO_DIR"
  print_cmd "docker compose up -d --build"
  docker compose up -d --build

  host_ip="$(detect_host_ip)"
  echo
  echo "==> Faerdig!"
  echo "    Aaben: http://${host_ip}:${APP_PORT:-8096}"
  echo "    (Eller den PUBLIC_BASE_URL du satte: ${PUBLIC_BASE_URL})"
}

step_1_basic() {
  echo
  echo "Step 1/3: Basis indstillinger"
  APP_PORT="$(ask_input "Web-port (APP_PORT)" "$APP_PORT" "8096" "Den port du aabner i browseren.")"
  TZ="$(ask_input "Tidszone (TZ)" "$TZ" "Europe/Copenhagen" "Tidszone i Region/By format.")"

  detected_ip="$(detect_host_ip)"
  suggested_url="http://${detected_ip}:${APP_PORT}"
  if [ -z "$PUBLIC_BASE_URL" ] || [ "$PUBLIC_BASE_URL" = "http://localhost:8096" ]; then
    PUBLIC_BASE_URL="$suggested_url"
  fi
  echo
  echo "    Opdaget IP: ${detected_ip}"
  PUBLIC_BASE_URL="$(ask_input "PUBLIC_BASE_URL" "$PUBLIC_BASE_URL" "http://10.10.0.50:8096" "Bruges til OAuth redirect-URIs (Microsoft/Google mail).")"
}

step_2_secrets() {
  echo
  echo "Step 2/3: Hemmelige nogler"
  ensure_secret_key
  ensure_app_encryption_key
}

step_3_updater() {
  echo
  echo "Step 3/3: In-app opdatering"
  auto_default="$(is_truthy "${FJORDPARCEL_AUTO_UPDATE_CHECK:-1}" && echo y || echo n)"
  if ask_yes_no "Aktiver automatisk tjek for opdateringer?" "$auto_default"; then
    FJORDPARCEL_AUTO_UPDATE_CHECK="1"
    FJORDPARCEL_AUTO_UPDATE_CHECK_INTERVAL_MINUTES="$(ask_input "Tjek-interval (minutter)" "$FJORDPARCEL_AUTO_UPDATE_CHECK_INTERVAL_MINUTES" "30" "Hvor ofte FjordParcel tjekker GitHub for nye versioner.")"
  else
    FJORDPARCEL_AUTO_UPDATE_CHECK="0"
  fi
}

print_summary() {
  echo
  echo "Opsummering:"
  echo "  APP_PORT=${APP_PORT}"
  echo "  TZ=${TZ}"
  echo "  PUBLIC_BASE_URL=${PUBLIC_BASE_URL}"
  echo "  DATA_DIR=${DATA_DIR}"
  echo "  SECRET_KEY=(sat)"
  echo "  APP_ENCRYPTION_KEY=(sat)"
  echo "  FJORDPARCEL_AUTO_UPDATE_CHECK=${FJORDPARCEL_AUTO_UPDATE_CHECK}"
  if is_truthy "$FJORDPARCEL_AUTO_UPDATE_CHECK"; then
    echo "  FJORDPARCEL_AUTO_UPDATE_CHECK_INTERVAL_MINUTES=${FJORDPARCEL_AUTO_UPDATE_CHECK_INTERVAL_MINUTES}"
  fi
  echo "  Data-mappe: ${DATA_DIR}"
}

backup_env_once() {
  if [ "${ENV_BACKUP_DONE:-0}" = "1" ]; then
    return 0
  fi
  if [ -f "$ENV_FILE" ]; then
    backup_file="${ENV_FILE}.bak.$(date +%Y%m%d%H%M%S)"
    cp "$ENV_FILE" "$backup_file"
    echo
    echo "Backup af eksisterende .env gemt:"
    echo "  ${backup_file}"
  fi
  ENV_BACKUP_DONE=1
}

save_env() {
  backup_env_once
  write_env_file "$ENV_FILE"
  echo
  echo "Konfiguration skrevet til:"
  echo "  ${ENV_FILE}"
}

edit_menu() {
  while :; do
    echo
    echo "Rediger indstillinger:"
    echo "  1) Basis indstillinger (port, tidszone, URL)"
    echo "  2) Hemmelige nogler"
    echo "  3) In-app opdatering"
    echo "  4) Faerdig (tilbage til opsummering)"
    choice="$(ask_input "Vaelg nummer" "4" "1-4" "")"
    case "$choice" in
      1) step_1_basic ;;
      2) step_2_secrets ;;
      3) step_3_updater ;;
      4|"") break ;;
      *) echo "Ugyldigt valg. Vaelg 1-4." ;;
    esac
  done
}

if [ "${1:-}" = "--start-only" ]; then
  echo "==> FjordParcel LXC start-only mode"
  echo "    Repo: ${REPO_DIR}"
  echo "    Env : ${ENV_FILE}"
  if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: Mangler .env fil: ${ENV_FILE}"
    echo "Koer fuld wizard foerst:"
    echo "  sh scripts/fresh_setup_lxc.sh"
    exit 1
  fi
  load_env_with_defaults
  run_preflight_and_start
  exit 0
fi

if [ "${1:-}" != "" ]; then
  echo "Brug:"
  echo "  sh scripts/fresh_setup_lxc.sh               # guidet opsætning (fra bunden)"
  echo "  sh scripts/fresh_setup_lxc.sh --start-only  # preflight + docker compose up"
  exit 1
fi

echo "==> FjordParcel guidet opsætning til LXC"
echo "    Repo: ${REPO_DIR}"
echo "    Env : ${ENV_FILE}"
echo "    Tip : Tryk Enter for at bruge standardvaerdien ved hvert spoergsmaal."
echo "    Trin:"
echo "      1) Basis indstillinger (port, tidszone, URL)"
echo "      2) Hemmelige nogler (SECRET_KEY, APP_ENCRYPTION_KEY)"
echo "      3) In-app opdatering"

if [ ! -f "$EXAMPLE_ENV" ]; then
  echo "ERROR: Mangler .env.example i repo-roden."
  exit 1
fi

load_env_with_defaults
step_1_basic
step_2_secrets
step_3_updater

while :; do
  save_env
  print_summary
  echo
  if ask_yes_no "Kjaer preflight + docker compose up -d --build nu?" "y"; then
    run_preflight_and_start
    break
  fi
  edit_menu
  echo
  if ask_yes_no "Tilbage til opsummering og startmenu?" "y"; then
    continue
  fi
  echo "Spring start over."
  echo "Koer senere med:"
  echo "  sh scripts/fresh_setup_lxc.sh --start-only"
  break
done
