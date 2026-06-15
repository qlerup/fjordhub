#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"

if [ -z "${APP_DIR:-}" ]; then
	if [ -f "$REPO_DIR/docker-compose.yml" ]; then
		APP_DIR="$REPO_DIR"
	elif [ -f "./docker-compose.yml" ]; then
		APP_DIR="$(pwd)"
	else
		APP_DIR="/opt/fjordhub"
	fi
fi

SERVICE_NAME="${SERVICE_NAME:-fjordhub}"
UPDATER_SERVICE_NAME="${UPDATER_SERVICE_NAME:-fjordhub-updater}"
REPO_BRANCH="${REPO_BRANCH:-}"
DO_BUILD=1
NO_CACHE=0
SHOW_LOGS=1
CLEANUP_DOCKER="${CLEANUP_DOCKER:-no}"
COMPOSE_SERVICES="${COMPOSE_SERVICES:-fjordhub}"
FJORDHUB_UPDATE_REEXECED="${FJORDHUB_UPDATE_REEXECED:-0}"

usage() {
	cat <<EOF
Usage: $0 [options]

Normal FjordHub update:
  - backs up .env and hub.db when possible
  - pulls the current Git branch with --ff-only
  - appends new active .env.example variables to .env without overwriting values
  - runs docker compose up -d --build for the FjordHub web service
  - prints recent FjordHub container logs

Options:
  --app-dir DIR        FjordHub app directory (default: auto, then /opt/fjordhub)
  --branch BRANCH      Git branch to pull (default: current branch, then main)
  --no-build           Do not build images; only docker compose up -d
  --no-cache           Rebuild images without Docker cache
  --cleanup            Run optional Docker cleanup
  --no-cleanup         Skip optional Docker cleanup
  --no-logs            Do not print recent container logs at the end
  -h, --help           Show this help

Environment:
  APP_DIR, REPO_BRANCH, SERVICE_NAME, UPDATER_SERVICE_NAME, CLEANUP_DOCKER, COMPOSE_SERVICES
EOF
}

while [ "$#" -gt 0 ]; do
	case "$1" in
		--app-dir)
			if [ "$#" -lt 2 ]; then
				echo "Fejl: --app-dir mangler en mappe."
				exit 1
			fi
			shift
			APP_DIR="$1"
			;;
		--branch)
			if [ "$#" -lt 2 ]; then
				echo "Fejl: --branch mangler et branch-navn."
				exit 1
			fi
			shift
			REPO_BRANCH="$1"
			;;
		--no-build)
			DO_BUILD=0
			;;
		--no-cache)
			NO_CACHE=1
			DO_BUILD=1
			;;
		--cleanup)
			CLEANUP_DOCKER="yes"
			;;
		--no-cleanup)
			CLEANUP_DOCKER="no"
			;;
		--no-logs)
			SHOW_LOGS=0
			;;
		-h|--help)
			usage
			exit 0
			;;
		*)
			echo "Fejl: ukendt option: $1"
			usage
			exit 1
			;;
	esac
	shift
done

need_cmd() {
	if ! command -v "$1" >/dev/null 2>&1; then
		echo "Fejl: $1 blev ikke fundet i PATH."
		exit 1
	fi
}

docker_compose() {
	if [ -n "${DOCKER_SUDO:-}" ]; then
		sudo docker compose "$@"
	else
		docker compose "$@"
	fi
}

docker_cmd() {
	if [ -n "${DOCKER_SUDO:-}" ]; then
		sudo docker "$@"
	else
		docker "$@"
	fi
}

cleanup_docker_space() {
	echo "==> Rydder Docker build-cache og ubrugte objekter (bevarer volumes/data)"
	docker_cmd builder prune -af || true
	docker_cmd image prune -af || true
	docker_cmd container prune -f || true
	docker_cmd network prune -f || true
	docker_cmd system df || true
}

run_optional_cleanup() {
	case "$CLEANUP_DOCKER" in
		yes|YES|true|TRUE|1)
			cleanup_docker_space
			;;
		*)
			echo "==> Springer Docker oprydning over"
			;;
	esac
}

compose_build_no_cache() {
	if [ -n "$COMPOSE_SERVICES" ]; then
		docker_compose build --no-cache $COMPOSE_SERVICES
	else
		docker_compose build --no-cache
	fi
}

compose_up() {
	if [ -n "$COMPOSE_SERVICES" ]; then
		docker_compose up -d $COMPOSE_SERVICES
	else
		docker_compose up -d
	fi
}

compose_up_build() {
	if [ -n "$COMPOSE_SERVICES" ]; then
		docker_compose up -d --build $COMPOSE_SERVICES
	else
		docker_compose up -d --build
	fi
}

show_fjordhub_logs() {
	echo "==> FjordHub logs"
	docker_cmd logs --tail=120 "$SERVICE_NAME" || true
}

read_env_value() {
	key="$1"
	file="$APP_DIR/.env"
	[ -f "$file" ] || return 1
	line="$(grep -E "^[[:space:]]*${key}[[:space:]]*=" "$file" | tail -n 1 || true)"
	[ -n "$line" ] || return 1
	value="${line#*=}"
	printf '%s' "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//;s/^"//;s/"$//'
}

container_mount_source() {
	container="$1"
	destination="$2"
	docker_cmd inspect --format "{{range .Mounts}}{{if eq .Destination \"$destination\"}}{{.Source}}{{end}}{{end}}" "$container" 2>/dev/null || true
}

current_container_id() {
	hostname 2>/dev/null || true
}

is_absolute_path() {
	case "$1" in
		/*|[A-Za-z]:[\\/]*|\\\\*) return 0 ;;
		*) return 1 ;;
	esac
}

resolve_dir_from_env_or_mount() {
	key="$1"
	service="$2"
	destination="$3"
	fallback="$4"
	value="$(read_env_value "$key" 2>/dev/null || true)"
	mount_dir="$(container_mount_source "$service" "$destination")"
	if [ -n "$value" ] && ! is_absolute_path "$value" && [ -n "$mount_dir" ]; then
		value="$mount_dir"
	fi
	if [ -z "$value" ]; then
		value="$mount_dir"
	fi
	if [ -z "$value" ]; then
		value="$fallback"
	fi
	if is_absolute_path "$value"; then
		printf '%s' "$value"
	else
		printf '%s/%s' "$APP_DIR" "$value"
	fi
}

repo_host_dir() {
	value="$(read_env_value FJORDHUB_HOST_DIR 2>/dev/null || true)"
	current_container="$(current_container_id)"
	mount_dir=""
	if [ -n "$current_container" ]; then
		mount_dir="$(container_mount_source "$current_container" "/repo")"
	fi
	if [ -z "$mount_dir" ]; then
		mount_dir="$(container_mount_source "$UPDATER_SERVICE_NAME" "/repo")"
	fi
	if [ -n "$value" ] && ! is_absolute_path "$value" && [ -n "$mount_dir" ]; then
		value="$mount_dir"
	fi
	if [ -z "$value" ]; then
		value="$mount_dir"
	fi
	if [ -z "$value" ]; then
		value="$APP_DIR"
	fi
	if is_absolute_path "$value"; then
		printf '%s' "$value"
	else
		printf '%s/%s' "$APP_DIR" "$value"
	fi
}

escape_env_value() {
	printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

ensure_env_value() {
	key="$1"
	value="$2"
	env_file="$APP_DIR/.env"
	[ -n "$value" ] || return 0
	current="$(read_env_value "$key" 2>/dev/null || true)"
	if [ -n "$current" ] && is_absolute_path "$current"; then
		return 0
	fi
	{
		printf '\n# Added by scripts/update.sh on %s so in-app updates keep host mounts\n' "$TS"
		printf '%s="%s"\n' "$key" "$(escape_env_value "$value")"
	} >> "$env_file"
	echo "==> .env opdateret med $key=$value"
}

backup_env_file() {
	data_dir="${DATA_DIR:-$(resolve_dir_from_env_or_mount DATA_DIR "$SERVICE_NAME" /data "$APP_DIR/data")}"
	backup_dir="$data_dir/backups"
	if [ ! -f "$APP_DIR/.env" ]; then
		return 0
	fi
	if mkdir -p "$backup_dir" 2>/dev/null; then
		backup_path="$backup_dir/fjordhub.env.$TS.bak"
		cp -p "$APP_DIR/.env" "$backup_path"
		echo "==> .env backup: $backup_path"
	else
		backup_path="$APP_DIR/.env.bak.$TS"
		cp -p "$APP_DIR/.env" "$backup_path"
		echo "==> .env backup: $backup_path"
	fi
}

merge_env_example_new_keys() {
	env_file="$APP_DIR/.env"
	example_file="$APP_DIR/.env.example"
	if [ ! -f "$example_file" ]; then
		echo "==> Springer .env merge over: .env.example blev ikke fundet"
		return 0
	fi
	if [ ! -f "$env_file" ]; then
		echo "==> Opretter .env"
		: > "$env_file"
	fi

	tmp_file="${TMPDIR:-/tmp}/fjordhub-env-merge.$$"
	: > "$tmp_file"

	while IFS= read -r line || [ -n "$line" ]; do
		case "$line" in
			""|\#*) continue ;;
		esac
		key="$(printf '%s\n' "$line" | sed -n 's/^[[:space:]]*\(export[[:space:]][[:space:]]*\)\{0,1\}\([A-Za-z_][A-Za-z0-9_]*\)[[:space:]]*=.*/\2/p')"
		[ -n "$key" ] || continue
		if grep -Eq "^[[:space:]]*(export[[:space:]]+)?${key}[[:space:]]*=" "$env_file"; then
			continue
		fi
		printf '%s\n' "$line" >> "$tmp_file"
	done < "$example_file"

	if [ -s "$tmp_file" ]; then
		count="$(wc -l < "$tmp_file" | sed 's/[[:space:]]//g')"
		{
			printf '\n# Added from .env.example by scripts/update.sh on %s\n' "$TS"
			cat "$tmp_file"
		} >> "$env_file"
		echo "==> .env opdateret med $count nye variabler fra .env.example"
	else
		echo "==> .env har allerede alle aktive variabler fra .env.example"
	fi
	rm -f "$tmp_file"
}

backup_database() {
	data_dir="${DATA_DIR:-$(resolve_dir_from_env_or_mount DATA_DIR "$SERVICE_NAME" /data "$APP_DIR/data")}"
	db_path="$data_dir/hub.db"
	backup_dir="$data_dir/backups"
	if [ ! -f "$db_path" ]; then
		echo "==> Ingen database fundet til backup endnu: $db_path"
		return 0
	fi
	mkdir -p "$backup_dir"
	backup_path="$backup_dir/hub.db.$TS.bak"
	cp -p "$db_path" "$backup_path"
	echo "==> Database backup: $backup_path"
}

need_cmd docker
need_cmd git

DOCKER_SUDO=""
if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1; then
	if ! docker info >/dev/null 2>&1; then
		DOCKER_SUDO="sudo"
	fi
fi

if [ ! -d "$APP_DIR" ]; then
	echo "Fejl: APP_DIR findes ikke: $APP_DIR"
	exit 1
fi

if [ ! -f "$APP_DIR/docker-compose.yml" ]; then
	echo "Fejl: docker-compose.yml blev ikke fundet i APP_DIR: $APP_DIR"
	exit 1
fi

cd "$APP_DIR" || exit 1
TS="$(date +%Y%m%d-%H%M%S)"
DATA_DIR="${DATA_DIR:-$(resolve_dir_from_env_or_mount DATA_DIR "$SERVICE_NAME" /data "$APP_DIR/data")}"
APPS_DIR="${APPS_DIR:-$(resolve_dir_from_env_or_mount APPS_DIR "$SERVICE_NAME" /apps "$APP_DIR/apps")}"
FJORDHUB_HOST_DIR="${FJORDHUB_HOST_DIR:-$(repo_host_dir)}"
if ! is_absolute_path "$DATA_DIR"; then
	DATA_DIR="$(resolve_dir_from_env_or_mount DATA_DIR "$SERVICE_NAME" /data "$APP_DIR/data")"
fi
if ! is_absolute_path "$APPS_DIR"; then
	APPS_DIR="$(resolve_dir_from_env_or_mount APPS_DIR "$SERVICE_NAME" /apps "$APP_DIR/apps")"
fi
if ! is_absolute_path "$FJORDHUB_HOST_DIR"; then
	FJORDHUB_HOST_DIR="$(repo_host_dir)"
fi
export DATA_DIR APPS_DIR FJORDHUB_HOST_DIR

echo "==> App directory: $APP_DIR"
echo "==> Host repo directory: $FJORDHUB_HOST_DIR"
echo "==> Data directory: $DATA_DIR"
echo "==> Apps directory: $APPS_DIR"
docker_compose config >/dev/null

if [ ! -d .git ]; then
	echo "Fejl: $APP_DIR er ikke et git repository."
	echo "Tip: kontroller APP_DIR, eller klon FjordHub repoet igen i denne mappe."
	exit 1
fi

dirty="$(git status --porcelain --untracked-files=no)"
if [ -n "$dirty" ]; then
	echo "Fejl: der er lokale tracked aendringer i $APP_DIR."
	echo "Commit/stash dem foerst, eller ret mappen manuelt foer update koeres igen."
	git status --short --untracked-files=no
	exit 1
fi

if [ -z "$REPO_BRANCH" ]; then
	REPO_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
	if [ -z "$REPO_BRANCH" ] || [ "$REPO_BRANCH" = "HEAD" ]; then
		REPO_BRANCH="main"
	fi
fi

OLD_REV="$(git rev-parse HEAD 2>/dev/null || true)"
OLD_SCRIPT_HASH=""
if [ -f "$SCRIPT_DIR/update.sh" ]; then
	OLD_SCRIPT_HASH="$(git hash-object "$SCRIPT_DIR/update.sh" 2>/dev/null || true)"
fi

backup_env_file
ensure_env_value DATA_DIR "$DATA_DIR"
ensure_env_value APPS_DIR "$APPS_DIR"
ensure_env_value FJORDHUB_HOST_DIR "$FJORDHUB_HOST_DIR"
backup_database

echo "==> Henter seneste kode fra origin/$REPO_BRANCH"
git fetch origin "$REPO_BRANCH"
git merge --ff-only "origin/$REPO_BRANCH"

NEW_SCRIPT_HASH=""
if [ -f "$SCRIPT_DIR/update.sh" ]; then
	NEW_SCRIPT_HASH="$(git hash-object "$SCRIPT_DIR/update.sh" 2>/dev/null || true)"
fi
if [ "$FJORDHUB_UPDATE_REEXECED" != "1" ] && [ -n "$OLD_SCRIPT_HASH" ] && [ -n "$NEW_SCRIPT_HASH" ] && [ "$OLD_SCRIPT_HASH" != "$NEW_SCRIPT_HASH" ]; then
	echo "==> Update-scriptet er opdateret. Genstarter updater-flow med ny script-version."
	set -- --app-dir "$APP_DIR" --branch "$REPO_BRANCH"
	case "$CLEANUP_DOCKER" in
		yes|YES|true|TRUE|1) set -- "$@" --cleanup ;;
		no|NO|false|FALSE|0) set -- "$@" --no-cleanup ;;
	esac
	if [ "$DO_BUILD" = "0" ]; then
		set -- "$@" --no-build
	fi
	if [ "$NO_CACHE" = "1" ]; then
		set -- "$@" --no-cache
	fi
	if [ "$SHOW_LOGS" = "0" ]; then
		set -- "$@" --no-logs
	fi
	FJORDHUB_UPDATE_REEXECED=1 exec sh "$SCRIPT_DIR/update.sh" "$@"
fi

NEW_REV="$(git rev-parse HEAD 2>/dev/null || true)"
if [ -n "$OLD_REV" ] && [ "$OLD_REV" = "$NEW_REV" ]; then
	echo "==> Ingen nye commits. Sikrer at containeren koerer."
else
	echo "==> Opdateret: ${OLD_REV:-unknown} -> $NEW_REV"
fi

merge_env_example_new_keys
run_optional_cleanup

if [ "$NO_CACHE" = "1" ]; then
	echo "==> Bygger uden Docker cache"
	compose_build_no_cache
	echo "==> Starter FjordHub"
	compose_up
elif [ "$DO_BUILD" = "1" ]; then
	echo "==> Bygger og starter FjordHub"
	compose_up_build
else
	echo "==> Starter FjordHub uden build"
	compose_up
fi

echo "==> Status"
docker_compose ps

if [ "$SHOW_LOGS" = "1" ]; then
	echo "==> Seneste logs"
	show_fjordhub_logs
fi
