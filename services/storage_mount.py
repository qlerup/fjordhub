"""Generate reviewable PVE commands; never execute them from FjordHub."""
import re
import shlex


class MountRequired(ValueError):
    def __init__(self, status):
        super().__init__(status['message'])
        self.status = status


def pve_commands(ctid, disk, target):
    if not re.fullmatch(r'[1-9][0-9]{2,8}', str(ctid)):
        raise ValueError('Indtast LXC-ID (mindst 100).')
    # These values are included both in shell and in PVE's comma-delimited config.
    for path in (disk, target):
        if not isinstance(path, str) or not re.fullmatch(r'/(?:mnt|media)/[A-Za-z0-9_./ -]+', path) or '..' in path.split('/'):
            raise ValueError('Brug en sti under /mnt eller /media uden specialtegn.')
    return f'''bash <<'FJORDHUB_MOUNT'
set -euo pipefail
ctid={shlex.quote(str(ctid))}
disk={shlex.quote(disk.rstrip('/'))}
target={shlex.quote(target.rstrip('/'))}
source="$disk/fjordhub"

# Stop, hvis den nye disk ikke faktisk er monteret på PVE.
mountpoint -q "$disk" || {{ echo "Disken er ikke monteret: $disk"; exit 1; }}
[ "$(readlink -f "$disk")" = "$disk" ] || {{ echo 'Diskstien må ikke indeholde links'; exit 1; }}
[ ! -L "$source" ] || {{ echo 'Kildemappen må ikke være et link'; exit 1; }}
config=$(pct config "$ctid")
slot=''
for i in $(seq 0 255); do
  line=$(printf '%s\\n' "$config" | grep "^mp$i:" || true)
  existing=$(printf '%s\\n' "$line" | sed -n 's/.*,mp=\\([^,]*\\).*/\\1/p')
  if [ -n "$line" ] && [ "$existing" = "$target" ]; then
    if [ "$line" != "mp$i: $source,mp=$target" ]; then
      echo 'Mountpunktet findes med andre indstillinger. Kontrollér PVE-konfigurationen.'; exit 1
    fi
    slot="mp$i"; break
  fi
done
if [ -z "$slot" ]; then
  for i in $(seq 0 255); do
    if ! printf '%s\\n' "$config" | grep -q "^mp$i:"; then slot="mp$i"; break; fi
  done
fi
[ -n "$slot" ] || {{ echo 'Ingen ledige mount-numre'; exit 1; }}

# Undgå at skjule filer, som allerede ligger i LXC-mappen.
pct exec "$ctid" -- sh -c '
  if ! mountpoint -q "$1" && [ -d "$1" ] && [ -n "$(ls -A "$1")" ]; then
    echo "Mappen indeholder filer. Flyt dem sikkert, før mountet tilføjes: $1"; exit 1
  fi
' sh "$target"
mkdir -p -- "$source"
cp -- "/etc/pve/lxc/$ctid.conf" "/root/fjordhub-mount-$ctid-$(date +%Y%m%d-%H%M%S).conf"
pct set "$ctid" "-$slot" "$source,mp=$target"

# Afslut uploads først: dette genstarter LXC og dens apps.
pct reboot "$ctid"
FJORDHUB_MOUNT'''


def volume_commands(ctid, storage_id, target, size_gib):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', storage_id) or not str(size_gib).isdigit() or not 1 <= int(size_gib) <= 1048576:
        raise ValueError('Vælg et gyldigt lager og en diskstørrelse i GiB.')
    # Share the backup, free-slot selection and nonempty-target guards.
    script = pve_commands(ctid, '/mnt/unused', target)
    start = script.index('disk=')
    end = script.index('config=')
    script = script[:start] + f'''storage_id={shlex.quote(storage_id)}
target={shlex.quote(target)}
source="$storage_id:{int(size_gib)}"
# Proxmox opretter en containerdisk på det valgte lager.
''' + script[end:]
    start = script.index('    if [ "$line" !=')
    end = script.index('    slot=', start)
    script = script[:start] + '''    volume="${line#*: }"
    volume="${volume%%,*}"
    case "$volume" in
      "$storage_id":*) source="$volume"; reuse=1 ;;
      *) echo 'Mountpunktet bruges af et andet lager.'; exit 1 ;;
    esac
''' + script[end:]
    script = script.replace("slot=''", "slot=''\nreuse=0")
    script = script.replace('pct set "$ctid" "-$slot" "$source,mp=$target"', 'if [ "$reuse" = 0 ]; then pct set "$ctid" "-$slot" "$source,mp=$target"; fi')
    return script.replace('mkdir -p -- "$source"\n','')
