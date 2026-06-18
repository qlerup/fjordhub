#!/bin/sh
set -eu

ASSUME_YES=0

usage() {
	cat <<EOF
Usage: $0 [options]

FjordLens Docker cleanup:
  - shows current FjordLens containers/images/networks
  - prunes Docker build cache and unused Docker objects
  - preserves Docker volumes and mounted data directories

Options:
  -y, --yes     Run without confirmation
  -h, --help    Show this help

Note:
  This is a global Docker cleanup. It can remove unused images/cache from
  other Docker projects on the same host, but it does not remove volumes.
EOF
}

while [ "$#" -gt 0 ]; do
	case "$1" in
		-y|--yes)
			ASSUME_YES=1
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

docker_cmd() {
	if [ -n "${DOCKER_SUDO:-}" ]; then
		sudo docker "$@"
	else
		docker "$@"
	fi
}

need_cmd docker

DOCKER_SUDO=""
if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1; then
	if ! docker info >/dev/null 2>&1; then
		DOCKER_SUDO="sudo"
	fi
fi

echo "=== FjordLens containers ==="
docker_cmd ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}' | grep -E '^fjordlens($|-ai)' || true

echo
echo "=== FjordLens images ==="
docker_cmd image ls --format 'table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}' | grep -E '^fjordlens-|^fjordlens_' || true

echo
echo "=== FjordLens networks ==="
docker_cmd network ls --format '{{.Name}}' | grep '^fjordlens' || true

echo
echo "=== Docker disk usage before cleanup ==="
docker_cmd system df || true

if [ "$ASSUME_YES" != "1" ]; then
	echo
	printf "Ryd Docker build-cache og ubrugte images/containere/netvaerk? Volumes/data bevares. [y/N] "
	read -r reply || reply=""
	case "$reply" in
		y|Y|yes|YES|Yes) ;;
		*) echo "Afbrudt."; exit 0 ;;
	esac
fi

echo
echo "=== Rydder build cache ==="
docker_cmd builder prune -af || true

echo
echo "=== Rydder unused images ==="
docker_cmd image prune -af || true

echo
echo "=== Rydder stoppede containere ==="
docker_cmd container prune -f || true

echo
echo "=== Rydder unused netvaerk ==="
docker_cmd network prune -f || true

echo
echo "=== Docker disk usage after cleanup ==="
docker_cmd system df || true

echo
echo "=== Oprydning faerdig ==="
