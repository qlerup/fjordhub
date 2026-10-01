#!/usr/bin/env bash
# FjordHub-owned Proxmox installer. Run on the PVE node, not inside a guest.
set -Eeuo pipefail
[ "$(id -u)" = 0 ] && command -v pct >/dev/null || { echo 'Run on Proxmox as root.' >&2; exit 1; }
[ "$(dpkg --print-architecture)" = amd64 ] || { echo 'This installer requires amd64.' >&2; exit 1; }
REPO_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
CTID=${CTID:-$(pvesh get /cluster/nextid)}
STORAGE=${STORAGE:-local-lvm}
TEMPLATE_STORAGE=${TEMPLATE_STORAGE:-local}
BRIDGE=${BRIDGE:-vmbr0}
DISK_GIB=${DISK_GIB:-24}
[[ $CTID =~ ^[1-9][0-9]{2,8}$ && $STORAGE =~ ^[A-Za-z0-9_.-]+$ && $TEMPLATE_STORAGE =~ ^[A-Za-z0-9_.-]+$ && $BRIDGE =~ ^[A-Za-z0-9_.-]+$ && $DISK_GIB =~ ^[1-9][0-9]{0,3}$ ]] || { echo 'Invalid installer options.'; exit 1; }
HOST_IP=${HOST_IP:-$(ip -4 -o addr show dev "$BRIDGE" | awk '{split($4,a,"/"); print a[1]; exit}')}
python3 -c 'import ipaddress,sys; ipaddress.IPv4Address(sys.argv[1])' "$HOST_IP"
pvesh get /cluster/nextid --vmid "$CTID" >/dev/null
pvesm status --storage "$STORAGE" --content rootdir >/dev/null
pvesm status --storage "$TEMPLATE_STORAGE" --content vztmpl >/dev/null
pveam update
TEMPLATE=$(pveam available --section system | awk '$2 ~ /^debian-13-standard_.*_amd64.tar.zst$/ {print $2}' | sort -V | tail -1)
[ -n "$TEMPLATE" ] || { echo 'Debian 13 amd64 template not found.'; exit 1; }
pveam download "$TEMPLATE_STORAGE" "$TEMPLATE"
pct create "$CTID" "$TEMPLATE_STORAGE:vztmpl/$TEMPLATE" --hostname fjordhub --unprivileged 1 \
  --features nesting=1,keyctl=1 --cores 2 --memory 2048 --swap 512 --rootfs "$STORAGE:$DISK_GIB" \
  --net0 "name=eth0,bridge=$BRIDGE,ip=dhcp" --onboot 1
echo "Created LXC $CTID. If setup fails, keep this ID and inspect it before retrying."
pct start "$CTID"
pct exec "$CTID" -- bash -s <<'GUEST'
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive
for attempt in {1..30}; do getent hosts deb.debian.org >/dev/null && break; sleep 2; done
apt-get update
apt-get install -y ca-certificates curl git python3
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo 'deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian trixie stable' > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker
git clone --depth 1 https://github.com/qlerup/fjordhub.git /opt/fjordhub
cd /opt/fjordhub
python3 - <<'ENV'
from pathlib import Path
import secrets
values={'SECRET_KEY':secrets.token_hex(32),'APP_PORT':'8091','DATA_DIR':'/opt/fjordhub/data',
        'APPS_DIR':'/opt/fjordhub/apps','FJORDHUB_HOST_DIR':'/opt/fjordhub'}
lines=Path('.env.example').read_text().splitlines()
Path('.env').write_text('\n'.join([line for line in lines if line.partition('=')[0] not in values]+[k+'='+v for k,v in values.items()])+'\n')
Path('.env').chmod(0o600)
ENV
docker compose up -d --build --wait --wait-timeout 180
GUEST
python3 "$REPO_DIR/scripts/configure_proxmox.py" "$CTID" --host "$HOST_IP"
echo "FjordHub is ready in LXC $CTID on port 8091. Its own pool access is configured."
pct exec "$CTID" -- hostname -I
