
# FjordLens

FjordLens is a self-hosted photo library for Synology NAS and Docker hosts, with built-in photoframe management for Raspberry Pi devices.

This repository contains two parts:

- `fjordlens/`: the main web app and API (Flask + JS)
- `photoframe/`: Raspberry Pi client (fullscreen viewer + local setup app)

---

## Feature Matrix

| Feature                        | Requires Ollama | Requires Photoframe | Requires External Worker |
|--------------------------------|:---------------:|:-------------------:|:-----------------------:|
| Timeline/Folders/Places        |                 |                     |                         |
| Metadata indexing              |                 |                     |                         |
| Weather enrichment             |                 |                     |                         |
| Thumbnail generation           |                 |                     |                         |
| AI embedding/search/similarity |                 |                     |                         |
| AI image description           |       X*        |                     |      X                  |
| Face detection/indexing        |                 |                     |                         |
| Public share links             |                 |                     |                         |
| Photoframe management          |                 |         X           |                         |
| Remote photoframe update       |                 |         X           |                         |
| External AI queue              |       X         |                     |           X             |

*Ollama is only required if you use the external AI describer/worker.

---

## What You Get

### Photo library

- Timeline, Favorites, Folders, Places, Cameras, People views
- Metadata indexing (EXIF/file info)
- Historical weather enrichment from photo date + GPS, with city fallback
- Thumbnail generation and cache management
- Per-photo editing for captured date, GPS and favorite state
- Duplicate detection and merge tools
- Single file and ZIP downloads

### Upload and file handling

- Folder-based upload workflows from the UI
- Resumable uploads via TUS (`/api/upload/tus`)
- Share-link uploads (including TUS on share links)
- Optional HEIC and RAW conversion flows
- Post-processing pipeline for uploads

### AI and face features

- AI embedding ingest with start/stop/status
- AI description ingest with start/stop/status
- External AI description queue for offloaded processing workers
- AI search and "similar photos" tools
- Face indexing jobs with progress tracking
- People training, rename, hide, unknown-face matching

### Sharing and permissions

- Public share links for folders
- Share permissions (`view`, `upload`, `delete`)
- Optional password protection
- Expiry and admin management (extend/revoke/activate/edit)

### Photoframe platform

- Create and manage photoframe tokens from FjordLens
- Remote status cards (online, IP/local IP, version, sync, update state)
- Scope control per frame (all/folders/selected photos)
- Proxy access to frame settings from FjordLens
- Frame update rollout via uploaded ZIP (single frame or all)
- Restart/cancel commands and update progress reporting

### Admin and security

- Initial setup wizard for first admin account
- Role-based access (`admin`, `manager`, `user`)
- TOTP 2FA for accounts
- Per-user UI language and search language (`da`/`en`)

## Quick Start

### Fastest Setup (Recommended)

If you want the easiest path from a fresh server, use this exact flow:

```bash
ssh <user>@<server-ip>
cd ~
git clone https://github.com/qlerup/fjordlens.git
cd fjordlens
chmod +x scripts/Fresh_start_ubuntu_vm.sh
./scripts/Fresh_start_ubuntu_vm.sh
```

The wizard is interactive and guides you through:

- app port, timezone, and logging
- storage paths
- optional NFS `/etc/fstab` setup
- optional scan/library settings
- final preflight + `docker compose up -d --build`

### Local Docker host

```bash
sh scripts/Fresh_start_ubuntu_vm.sh
```

Open `http://localhost:9080` (or your configured `APP_PORT`).

Important: keep `GUNICORN_WORKERS=1`.
Background jobs use in-process runtime state, so multiple workers can cause inconsistent job status.

Weather enrichment is enabled by default with `WEATHER_AUTO_FETCH=1`. New uploads and metadata rescans store weather under each photo's metadata when the photo has a date plus either GPS coordinates or a city/country value. FjordLens uses Open-Meteo's historical weather endpoint and caches both weather lookups and city geocoding locally.

`scripts/Fresh_start_ubuntu_vm.sh` is a guided A-Z wizard. It asks for paths and options, writes `.env`, runs mount preflight checks, and starts containers.

If you prefer to start manually without preflight:

```bash
docker compose up -d --build
```

### Synology NAS (SSH)

```bash
cd /volume1/docker
git clone https://github.com/<your-user>/<your-repo>.git fjordlens
cd fjordlens/fjordlens
sh scripts/Fresh_start_ubuntu_vm.sh
```

Open `http://<nas-ip>:9080`.

`scripts/Fresh_start_ubuntu_vm.sh` will:

- ask guided setup questions (port, storage paths, optional library source, scan toggle, SQLite mode, optional fs-type checks)
- optionally configure NFS upload mount in `/etc/fstab` and run `mount -a`
- write `.env` (with backup if `.env` already exists)
- check mount status with `findmnt`
- create required host folders (`DATA_DIR`, `UPLOADS_HOST_DIR`, `THUMBS_HOST_DIR`)
- start `docker compose up -d --build`

### Upload-only mode (no `/photos` mount)

If you only use uploads and do not have a separate photo library mount:

```bash
docker compose -f docker-compose.yml -f docker-compose.no-library.yml up -d --build
```

For upload-only setups with preflight checks:

```bash
ENABLE_LIBRARY_SOURCE=0 sh scripts/Fresh_start_ubuntu_vm.sh
```

Start later with existing `.env` (no wizard):

```bash
sh scripts/Fresh_start_ubuntu_vm.sh --start-only
```

### Manual transfers outside FjordLens

If you copy files into the upload storage manually, outside the FjordLens UI, place them inside the `originals` folder under the configured upload folder. Create or choose the target folder first, then copy files into that folder under `originals`.

Example:

```text
<UPLOADS_HOST_DIR>/originals/<your-folder>/photo.jpg
```

FjordLens will then discover the files when that folder is opened and handle indexing, thumbnails, and normal post-processing.

### Proxmox LXC guided setup

For Proxmox LXC environments (where host bind mounts and GPU passthrough are configured on the Proxmox host):

```bash
sh scripts/fresh_setup_lxc.sh
```

`scripts/fresh_setup_lxc.sh` now includes optional guided GPU setup (`ENABLE_GPU_GUIDE=1`):

- checks `/dev/nvidia*` visibility inside the LXC
- auto-sets `no-cgroups = true` in `/etc/nvidia-container-runtime/config.toml` when needed
- restarts Docker runtime when runtime config changes
- runs CUDA + PyTorch GPU smoke tests before `docker compose up`
- prints exact Proxmox host `pct`/`/etc/pve/lxc/<CTID>.conf` hints if passthrough is still incomplete
- configures in-app updater defaults, including automatic background update checks
- verifies Docker and `/var/run/docker.sock` availability for the updater container

### Proxmox Host -> LXC Bind-Mount (Manual quick commands)

Use this if you want NAS-backed uploads with host mount + LXC bind mount.

1. Mount NFS share on the Proxmox host:

```bash
mkdir -p /mnt/pve/synology-fjordlens
mount -t nfs 10.10.0.161:/volume1/FjordlensProxmox /mnt/pve/synology-fjordlens
```

2. Verify host mount:

```bash
ls -la /mnt/pve/synology-fjordlens
```

3. Bind-mount share into the LXC (example CTID `1001`):

```bash
pct set 1001 -mp0 /mnt/pve/synology-fjordlens,mp=/mnt/fjordlens-nfs
pct restart 1001
```

4. Enter container and verify:

```bash
pct enter 1001
ls -la /mnt/fjordlens-nfs
```

5. Create upload/library folders inside container:

```bash
mkdir -p /mnt/fjordlens-nfs/uploads
mkdir -p /mnt/fjordlens-nfs/photos
```

Then use these in setup when relevant:

- `UPLOADS_HOST_DIR=/mnt/fjordlens-nfs/uploads`
- `PHOTO_DIR=/mnt/fjordlens-nfs/photos` (only if `ENABLE_LIBRARY_SOURCE=1`)

## Photoframe Quick Start

### 1) Create a frame token in FjordLens

Open the `Photoframe` view and create a frame entry/token.

### 2) Install photoframe on Raspberry Pi

On a fresh Raspberry Pi (SSH as normal user):

```bash
curl -fsSL https://raw.githubusercontent.com/qlerup/fjordlens/main/photoframe/scripts/bootstrap_install.sh | bash
```

### 3) First setup on the frame

Open `http://<frame-ip>:5001`.

Current setup flow supports:

- Country selection first
- Wi-Fi setup
- Connection setup (server URL + token)
- QR-assisted phone setup
- Temporary setup hotspot support for no-keyboard/no-touch scenarios

After setup is completed, the frame starts fullscreen slideshow mode.

## Photoframe via FjordLens (remote settings)

In each photoframe card, `Settings` opens a proxied settings session through FjordLens.

Notes:

- FjordLens needs a recent frame heartbeat with local IP
- If `:5001` is temporarily unavailable, FjordLens now attempts wake/retry behavior automatically
- If your reverse proxy or Cloudflare is used, allow frame API paths (see below)

## External AI Worker (Windows)

FjordLens can offload AI image description jobs to an external Windows client.

Worker files are included in:

- `external_worker/windows/ai_billedbeskriver.py`
- `external_worker/windows/ai_billedbeskriver_gui.pyw`
- `external_worker/windows/Start AI Billedbeskriver.vbs`

Quick flow:

1. In FjordLens, open `Indstillinger` -> `AI` and enable external AI descriptions.
2. Copy the generated connection link.
3. On Windows, open `external_worker/windows/README.md` and run the setup steps.
4. Start the GUI, paste the link, and click `Kor ekstern ko`.

The worker uses your local Ollama runtime and posts caption/tags back to FjordLens over the tokenized external API endpoints.

## Reverse Proxy / Cloudflare Notes

For photoframe feeds and media delivery, exclude these paths from bot/challenge pages:

- `/api/frame/*`
- `/api/frame/*/view/*`

If Cloudflare challenge pages are returned, frames cannot parse feed JSON.

## Updating

### Update FjordLens

Admins can also update from the web UI:

- Open `Indstillinger` -> `Opdatering`
- Click `Tjek` to fetch the latest `origin/<branch>` revision
- Click `Opdater`
- Choose `Ryd plads og opdater` or `Hurtig opdatering`

The in-app updater runs the same update flow as `scripts/update.sh`. `Ryd plads og opdater` runs the script with `--cleanup`; `Hurtig opdatering` runs it with `--no-cleanup`.

After pulling new code, the update script also appends missing active variables from `.env.example` to `.env`. Existing `.env` values are never overwritten, and commented optional examples stay commented in `.env.example`.

Note: the in-app updater uses an internal `fjordlens-updater` container with access to the Docker socket so it can rebuild/restart the FjordLens services. Keep the update UI admin-only.

The updater can automatically check for new commits in the background. The default is enabled every 30 minutes, and admins can change or disable it under `Indstillinger` -> `Opdatering`.

```bash
cd fjordlens
sh scripts/update.sh
```

Useful options:

```bash
sh scripts/update.sh --no-cache
sh scripts/update.sh --no-build
sh scripts/update.sh --branch main
sh scripts/update.sh --cleanup
sh scripts/update.sh --no-cleanup
```

The update script asks about optional Docker cleanup when run interactively. To intentionally free space outside an update:

```bash
sh scripts/cleanup.sh
```

The cleanup script prunes Docker build cache and unused Docker objects, but preserves volumes and mounted data directories.

### Full restart

```bash
docker compose down
docker compose up -d --build
```

### Photoframe updates from UI

FjordLens supports ZIP-based remote updates:

- Per-frame: `Upload zip`
- Global: `Upload zip to all`

Update states are reported by frames (`queued`, `downloading`, `installing`, `restarting`, `success`, `failed`).

## Key Configuration

See `.env.example` for defaults. Most-used variables:

- `APP_PORT`: web UI port (default `9080`)
- `PHOTO_DIR`: optional host library path mounted read-only as `/photos` (used only when `ENABLE_LIBRARY_SOURCE=1`)
- `UPLOADS_HOST_DIR`: host path mounted to `/uploads` (folder creation + uploads/originals + uploads/converted)
- `THUMBS_HOST_DIR`: host path mounted to `/thumbs` (thumbnails)
- `DATA_DIR`: persistent app state (`db`, converted cache, temp uploads, secrets, other internal data)
- `TZ`: timezone
- `LOG_LEVEL`: app log level
- `ENABLE_LIBRARY_SOURCE`: enable/disable library source (`PHOTO_DIR`) usage (`0` by default)
- `ENABLE_SCAN_FEATURES`: enable/disable scan/rescan/rethumb tools (`0` by default)
- `AI_DEVICE`: AI runtime preference (`auto`, `cpu`, `cuda`; default `auto`)
- `ENABLE_GPU_GUIDE`: enable guided GPU preflight in `scripts/fresh_setup_lxc.sh` (`1` by default)
- `AI_DEBUG_PORT`: optional host port for AI service
- `AI_INGEST_THROTTLE_SEC`: pacing for embeddings ingest
- `FACES_INDEX_THROTTLE_SEC`: pacing for face indexing
- `PHOTOFRAME_TEXT_ONLY`: frame feed test card mode
- `PHOTOFRAME_UPDATE_UPLOAD_MAX_BYTES`: max uploaded frame ZIP size
- `SHARE_DUCKDNS_BASE_URL`: optional external base URL for share links

Common advanced settings in code/env:

- `GUNICORN_WORKERS` (recommended: `1`)
- `GUNICORN_LOG_LEVEL`
- `GEOCODE_ENABLE`, `GEOCODE_PROVIDER`, `GEOCODE_LANG`, `GEOCODE_TIMEOUT`, `GEOCODE_RETRIES`, `GEOCODE_DELAY`
- `EXPECT_UPLOADS_FSTYPES`, `EXPECT_THUMBS_FSTYPES`, `EXPECT_DATA_FSTYPES`, `EXPECT_PHOTO_FSTYPES` (optional strict mount checks for `scripts/Fresh_start_ubuntu_vm.sh`)
- `SETUP_NFS_UPLOADS_ENABLED`, `SETUP_NFS_EXPORT`, `SETUP_NFS_MOUNT_ROOT`, `SETUP_NFS_UPLOADS_SUBDIR`, `SETUP_NFS_FSTAB_OPTIONS` (optional setup metadata for reruns)

## Useful API Endpoints

- Health: `GET /api/health`
- Scan jobs: `/api/scan`, `/api/rescan`, `/api/rethumb`
- AI jobs: `/api/ai/ingest`, `/api/ai/describe/ingest`, `/api/faces/index`
- Photos: `/api/photos`, `/api/photos/<id>`, `/api/photos/download-zip`
- Shares: `/api/shares`, `/api/share/<token>/*`
- Photoframes: `/api/photoframes/*`, `/api/frame/<token>/*`

## Troubleshooting

### Frame settings returns "connection refused"

This means FjordLens can see the frame IP, but frame settings service on port `5001` is not accepting connections at that moment.

- Wait a few seconds and retry
- Ensure frame services are running (`photoframe-app.service`, `photoframe-kiosk.service`)
- Keep frame and FjordLens on reachable network paths

### Jobs look inconsistent

Use one Gunicorn worker only (`GUNICORN_WORKERS=1`).

### Proxmox + NFS: folder click / random DB errors

If `DATA_DIR` is on NFS/CIFS, set SQLite journal mode to `DELETE` (not `WAL`):

```env
SQLITE_JOURNAL_MODE=DELETE
SQLITE_BUSY_TIMEOUT_MS=15000
```

Then restart the container. `WAL` often causes locking instability on network filesystems.
If `SQLITE_JOURNAL_MODE` is not set, FjordLens now auto-selects `DELETE` on detected network filesystems and `WAL` on local disks.

### Upload issues behind reverse proxy

Use TUS endpoints and confirm proxy allows `PATCH`, `HEAD`, `OPTIONS` and long-running uploads.

### Containers unhealthy

```bash
docker compose ps
docker compose logs --tail=200
```

### GPU acceleration is not used

`AI_DEVICE=auto` enables automatic CUDA use when the container can see a GPU.

If health still reports CPU, run the LXC GPU guide first:

```bash
sh scripts/fresh_setup_lxc.sh --start-only
```

Then verify Docker GPU passthrough is enabled on the host/runtime and rebuild:

```bash
docker compose up -d --build
```

Manual recovery checklist is available in:

- `GPU_RECOVERY_LXC.md`

## Project Layout

```txt
fjordlens_synology_github_ready/
|- fjordlens/
|  |- app.py
|  |- Dockerfile
|  |- docker-compose.yml
|  |- docker-compose.no-library.yml
|  |- ai_service/
|  |- static/
|  |- templates/
|  `- scripts/
`- photoframe/
   |- app/
   |- viewer/
   |- systemd/
   |- scripts/
   |- install.sh
   `- update.sh
```

## Security Checklist

- Do not commit `.env` with secrets
- Keep `/photos` read-only when possible
- Use strong admin passwords
- Enable 2FA for admin accounts
- Keep `DATA_DIR` on persistent storage

---


---

## Backup & Restore

### Backup

- Backup your persistent data directory (`DATA_DIR`), uploads, thumbs, and optionally your `.env` file.
- Example (from host):
   ```bash
   tar czf fjordlens-backup-$(date +%Y%m%d).tar.gz /path/to/data_dir /path/to/uploads /path/to/thumbs /path/to/fjordlens/.env
   ```

### Restore

- Stop FjordLens containers.
- Extract your backup to the original locations.
- Start FjordLens again.

---

## Screenshots & GIFs

To improve onboarding, consider adding screenshots or GIFs for each major view (`Timeline`, `Folders`, `Photoframe`, `Settings`).

---
