<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="static/logos/logos/fjordhub-logo-horizontal-light.png">
    <img src="static/logos/logos/fjordhub-logo-horizontal-dark.png" alt="FjordHub" width="420">
  </picture>
</p>

<p align="center">
  A self-hosted application hub for your home server.<br>
  Install, run, update and monitor Docker apps from one dashboard — with shared users and single sign-on.
</p>

---

## What is FjordHub?

FjordHub is a lightweight control panel for a small fleet of self-hosted apps. Instead of managing each app by hand (clone the repo, write an `.env`, run compose, keep it updated), FjordHub does it for you:

- **App catalog** — apps are discovered from a remote registry on GitHub. New apps show up in the dashboard without updating the hub itself.
- **One-click install** — a guided wizard collects the app's settings (ports, timezone, secrets), clones the app's repository, writes its `.env` and brings it up with Docker Compose.
- **Lifecycle management** — start, stop, update and uninstall apps from the dashboard, with live health checks per app.
- **Central users & SSO** — user accounts live in the hub. Installed apps authenticate against the hub's API, users are synced automatically, and "Open app" links can log you straight in via short-lived SSO tokens.
- **Password recovery** — configure an SMTP sender under Settings. FjordHub sends five-minute security codes and handles recovery centrally for the hub and integrated apps.
- **Self-update** — a small sidecar container pulls the latest FjordHub from GitHub and rebuilds/restarts the hub, triggered from the Settings page.
- **Resource monitoring** — host CPU, memory and disk usage plus per-container stats, with a one-click Docker cleanup for reclaiming space.
- **Reverse proxy included** — Traefik routes each app under its own path prefix, so everything is reachable through a single entrypoint.

It is built for the home-lab case: one Linux host (bare metal, VM or Proxmox LXC) running Docker, administered by one or a few people.

## Access tokens for other apps

Administrators can create named tokens under **Indstillinger → Adgangstokens**,
with a lifetime of 30, 90 or 365 days, or **Udløber aldrig** (no expiry). Copy the token when it is created: only
its SHA-256 hash is stored, and the full token cannot be displayed again.
The same page lists expiry, last use (UTC) and a revoke button.

Tokens grant read-only access to Docker resource metrics on the local network:

```sh
curl http://192.168.1.10:8091/api/integrations/v1/resources \
  -H "Authorization: Bearer $FJORDHUB_ACCESS_TOKEN"
```

The endpoint uses the same collector as the Docker tab on the resources page.
The top-level `hub_url` provides a browser link, for example
`http://192.168.1.10:8091/`. It uses the detected host LAN IP (or `HOST_LAN_IP`)
and the published `APP_PORT`. If the host IP cannot be detected, it falls back
to the request's root URL; call the API through a browser-reachable LAN address.
Use this URL for an **Open FjordHub** link with `target="_blank"` and
`rel="noopener noreferrer"`. Do not append the token; normal FjordHub login applies.

The JSON response contains `ok`, `generated_at` (UTC), `capacity` (CPU count and
total memory), `hub` (core plus managed apps), `core` (FjordHub containers only),
and `apps` (app groups identified by `id` and `name`). Each group includes
`containers`, `container_count`, `running_count`, `cpu_percent`,
`cpu_capacity_percent`, `memory_usage`, `memory_percent`, `net_rx`, `net_tx`,
`block_read`, and `block_write`. Containers include `id`, `name`, `status`,
`cpu_percent`, `memory_usage`, `memory_limit`, the same network and I/O counters,
and `error` (`null` or a generic metrics failure). Display labels are also provided.

Memory and I/O values are bytes. Network and disk I/O are cumulative counters,
not bytes per second; calculate rates using counter differences and elapsed time,
discarding samples where counters reset. `cpu_percent` uses Docker's convention
(100% per CPU core); group `cpu_capacity_percent` expresses usage relative to total
CPU capacity on a 0–100 scale. Poll sequentially, for example every 10 seconds,
and store samples in the consuming app for graphs; this endpoint has no history.

Missing, invalid, expired or revoked tokens return 401; non-LAN requests return
403; unavailable metrics return 503. Responses use `Cache-Control: no-store`.
Requests must supply the token in the Authorization header, even with a logged-in
session. The socket peer and every forwarded address must be local; unsupported
`Forwarded` headers are rejected. Preserve client addresses through proxies.

The token does not grant container control, logs, configuration, user management,
Proxmox/LXC metrics or access to the existing session-only `/api/resources` route.
Tokens are stored in persistent `hub.db` and stop authenticating if their creator
is deleted, loses administrator rights or must change their password.

For app names, descriptions and icons, read the public GitHub `registry.json`
and each entry's `manifest_url` directly. No running FjordHub or token is required.

## How it works

The stack is three containers, defined in [docker-compose.yml](docker-compose.yml):

| Container | Role |
|---|---|
| `fjordhub` | The hub itself — a Flask app (Python 3.11, Gunicorn) that talks to Docker through the host's Docker socket. State lives in a SQLite database under `DATA_DIR`. |
| `fjordhub-traefik` | Traefik v3 reverse proxy. Apps register themselves via Docker labels and are routed by path prefix on a shared `fjord-net` network. |
| `fjordhub-updater` | A minimal HTTP service that performs the hub's own `git pull` + rebuild when you start a self-update. |

Installed apps are ordinary Docker Compose projects. Each one is cloned into `APPS_DIR/<app-id>` on the host and managed with `docker compose` — there is no proprietary packaging, and every app keeps working even if you remove the hub.

```
┌─────────────────────────── your server ───────────────────────────┐
│                                                                    │
│   :80  Traefik ──► /           FjordHub dashboard                  │
│                ──► /app-a      app A (own compose project)         │
│                ──► /app-b      app B (own compose project)         │
│                                                                    │
│   FjordHub ── docker socket ──► install / start / stop / update    │
│            ── hub API ◄──────── user sync & SSO from apps          │
└────────────────────────────────────────────────────────────────────┘
```

## Quick start

Requirements: a Linux host with Docker and the Docker Compose plugin.

```bash
git clone https://github.com/qlerup/fjordhub.git /opt/fjordhub
cd /opt/fjordhub
cp .env.example .env
# edit .env — at minimum set a real SECRET_KEY
docker compose up -d --build
```

Then open `http://<server-ip>/` (or the direct port from `APP_PORT`). The first visit runs a setup flow where you create the admin account. After that, the dashboard shows the app catalog and you can install apps from there.

## Configuration

All configuration is environment variables, read from `.env` (see [.env.example](.env.example)):

| Variable | Default | Description |
|---|---|---|
| `APP_PORT` | `8888` | Direct port for the hub, bypassing Traefik. |
| `TRAEFIK_HTTP_PORT` | `80` | Traefik's HTTP entrypoint — the port you normally browse to. |
| `TRAEFIK_DASHBOARD_PORT` | `8080` | Traefik's own dashboard. |
| `DATA_DIR` | `./data` | Hub state: SQLite database, install state, updater logs. |
| `SECRET_KEY` | — | Flask session secret. **Set this to a long random value.** |
| `TZ` | `Europe/Copenhagen` | Timezone for the hub and default for installed apps. |
| `REGISTRY_URL` | this repo's `registry.json` | Raw URL of the app registry. Point it at your own fork to curate your own catalog. |
| `FJORDHUB_HOST_DIR` | `/opt/fjordhub` | Host path of this repository — required for self-update. |
| `FJORDHUB_IMAGE` | `fjordhub-fjordhub:latest` | Image used for the hub's privileged helper jobs. |
| `FJORDLENS_DIR` / `FJORDSHARE_DIR` / `FJORDPARCEL_DIR` | — | Optional host paths for apps that were installed manually, so the hub can manage them too. |
| `PROXMOX_*` | — | Optional Proxmox API credentials, used for LXC-specific helpers such as GPU passthrough setup. |

## The app catalog

The catalog is driven by two layers of JSON:

1. **[registry.json](registry.json)** — the list of available apps. Each entry points to a manifest in the app's own repository:

   ```json
   {
     "schema": "fjordhub-registry/v1",
     "apps": [
       { "id": "orbitmap", "manifest_url": "https://raw.githubusercontent.com/qlerup/orbitmap/main/fjordhub.json" }
     ]
   }
   ```

2. **`fjordhub.json`** — the app's manifest, describing how it is presented and installed:

   ```json
   {
     "id": "orbitmap",
     "name": "OrbitMap",
     "tagline": "Roadmaps and project plans in one place",
     "container_name": "orbitmap",
     "default_port": 3005,
     "health_path": "/api/health",
     "traefik_prefix": "/orbitmap",
     "source_url": "https://github.com/qlerup/orbitmap",
     "setup_steps": [
       {
         "id": "basic",
         "title": "Basic settings",
         "fields": [
           { "key": "APP_PORT", "label": "Web port", "type": "number", "default": "3005" },
           { "key": "JWT_SECRET", "label": "Session secret", "type": "auto_secret" }
         ]
       }
     ]
   }
   ```

The install wizard is generated from `setup_steps`. Field types include plain `text` and `number` inputs and `auto_secret`, which generates a random secret so users never have to invent one. On install, FjordHub shallow-clones `source_url` into `APPS_DIR/<id>`, writes the collected values to the app's `.env` and runs `docker compose up -d --build`.

The hub also caches the remote registry in `DATA_DIR`, so the dashboard keeps working if GitHub is unreachable, and ships local fallback manifests in [app_registry/](app_registry/).

### Making your own app installable

Any Docker Compose project can join the catalog:

1. Add a `fjordhub.json` manifest to the root of your app's repository.
2. Make sure the app reads its configuration from `.env` and exposes a health endpoint.
3. Add the app to the `registry.json` that your hub's `REGISTRY_URL` points at.

Apps can optionally integrate with the hub's user API (`/api/hub/apps/authenticate`, `/api/hub/user-sync`, `/api/hub/sso-verify`) to share the hub's user accounts and accept SSO logins instead of keeping their own.

FjordFlix is available in the catalog with central accounts, app-specific `admin`/`user` roles and SSO. It disables its local signup/invitation system when managed by FjordHub and rechecks access while it is in use. Grant users access through **Users → FjordFlix**. The manifest's optional `compose_file` selects the managed Compose file explicitly, so an app can retain a separate standalone Compose setup.

The FjordFlix wizard offers CPU or NVIDIA transcoding, separate movie and database/cache directories, a remote-control URL and a simultaneous conversion limit. FjordLens and FjordFlix can share the same GPU; they share its VRAM and processing capacity without automatic workload prioritization. On Docker Desktop/WSL, GPU access uses the NVIDIA runtime without Linux `/dev/nvidia*` bind mounts; Linux/LXC continues to use device discovery.

## Updates

- **Apps** — the dashboard checks each installed app's repository for new commits. Updating pulls the latest code and re-runs compose for that app only.
- **The hub itself** — Settings → Update triggers the `fjordhub-updater` sidecar, which pulls this repository, rebuilds the hub image and restarts the hub container. Progress and logs are shown in the UI and persisted under `DATA_DIR/fjordhub-updater`.

## GPU passthrough (NVIDIA)

FjordFlix declares `gpu_video: true`. Its preflight checks that Docker receives NVIDIA encode/decode libraries in addition to the common `nvidia-smi` test. Missing video libraries show a video-only PVE addon, which backs up the selected LXC configuration, adds read-only library mounts and registers that LXC in `/etc/fjordhub/gpu-video-cts`. It does not reinstall drivers or change FjordLens' Docker configuration. Reboot the LXC and run `pct exec <CTID> -- ldconfig` on PVE afterward, then repeat the test. Installation also runs a real FFmpeg/NVENC test inside FjordFlix; a failed encoder test is reported as an installation error instead of GPU success. The already-started container may remain running on CPU until repaired.

Both FjordLens and FjordFlix automatically test the shared Docker GPU runtime when the GPU step opens. If it works, the wizard hides host setup and offers to reuse it. Missing device access shows the PVE/LXC instructions; existing devices with a failed Docker test show the runtime setup and diagnostic error. The installer checks GPU access again before a GPU-enabled installation. The automatic setup worker also tests first and skips package changes and Docker restarts when the runtime already works. Each app still receives its own container GPU mapping; host configuration is shared. PVE commands still need to be run on the host when passthrough is missing.

Apps that can use a GPU (e.g. FjordLens' AI service) get a **GPU helper** in the install wizard. It sets up NVIDIA GPU access for the FjordHub LXC container on a Proxmox host — one copy-paste, once per host:

1. **One-time host script** — run on the PVE host. It first checks the prerequisites (driver installed, device nodes present, privileged container) and fails with a clear message instead of writing a half-broken config. It then installs a small `fjordhub-gpu-sync` systemd service and runs it immediately.
2. **`fjordhub-gpu-sync`** runs at every host boot, before the containers start. It loads the NVIDIA kernel modules, removes stale GPU mount lines whose source files no longer exist, and rewrites `/etc/pve/lxc/<CTID>.conf` to match the driver currently installed on the host. **Host driver updates therefore never break the containers** — reboot the host and everything is re-synced automatically.
3. **In-container auto-setup** — one click in the wizard. Installs the NVIDIA container toolkit, installs userspace libraries matching the host driver exactly (or falls back to the bind-mounted host libraries when the exact version isn't packaged), sets `no-cgroups = true` (an LXC may not manage cgroup device rules itself — the host already grants access), configures the Docker runtime and restarts Docker. The GPU test button unlocks automatically once everything is back up.

A few facts worth knowing:

- **The GPU model doesn't matter.** All GeForce cards (RTX 20/30/40 series, …) use the same unified NVIDIA driver — the only requirement is that the host's driver is new enough to know the card. Nothing in FjordHub is card-specific.
- **GPU devices are detected dynamically.** FjordHub passes every NVIDIA GPU and control/capability device found in the LXC to Docker, so the same setup supports one or several GPUs without hardcoded card models or `/dev/nvidia0` assumptions.
- **The GPU is shared, not locked.** Unlike VM PCI passthrough, LXC containers only get *access* to the host's GPU — the host keeps owning it, and any number of containers can use it at the same time (they share VRAM and compute).
- **Requirements:** the NVIDIA driver installed on the PVE host (Proxmox doesn't ship it), a privileged LXC container, and a Debian/Ubuntu-based container for the in-container auto-setup.

### Sharing the GPU with another LXC container

Say you have another container with CTID **1010** that should also use the GPU. On the PVE host (e.g. via the Proxmox web UI shell), run:

```bash
echo "1010" >> /etc/fjordhub/gpu-cts
/usr/local/sbin/fjordhub-gpu-sync
pct reboot 1010
```

What each line does:

1. `echo "1010" >> /etc/fjordhub/gpu-cts` — adds CT 1010 to the list of containers that `fjordhub-gpu-sync` maintains. The FjordHub container is already on this list from the one-time setup.
2. `/usr/local/sbin/fjordhub-gpu-sync` — runs the sync immediately, writing the GPU lines (device access, driver libraries, environment) into `/etc/pve/lxc/1010.conf`. Without this it would happen at the next host boot instead.
3. `pct reboot 1010` — restarts the container so it starts with GPU access.

From then on CT 1010 is maintained automatically alongside the others — including after host driver updates.

> **Prerequisite:** the one-time host script from the GPU helper must have been run on this host first — that's what installs `/usr/local/sbin/fjordhub-gpu-sync`.

What to do *inside* the container afterwards depends on what it runs:

- **Docker workloads** (like FjordHub/FjordLens): the container also needs the NVIDIA container toolkit and `no-cgroups = true` — the same steps FjordHub's in-container auto-setup performs.
- **Programs running directly** (e.g. Jellyfin/Plex transcoding, a Python/CUDA script): the bind-mounted host libraries are usually enough. Verify with `nvidia-smi` inside the container after the reboot.

## Security notes

- The hub container mounts `/var/run/docker.sock`, which is equivalent to root on the host. Treat the hub as an admin tool: run it on a trusted network and put it behind a VPN or an authenticated tunnel if you expose it to the internet.
- Set a strong `SECRET_KEY` before first start — sessions are signed with it.
- The Traefik dashboard is enabled in insecure mode by default for convenience on a LAN. Close `TRAEFIK_DASHBOARD_PORT` in your firewall or disable it if that doesn't fit your setup.

## Repository layout

```
app.py              Flask app: routes, auth gate, SSO endpoints
services/           Auth, installer, Docker manager, registries, updater client,
                    resource monitor
updater_service/    Self-update sidecar (plain http.server, no dependencies)
app_registry/       Local fallback manifests for the built-in catalog
templates/ static/  Server-rendered UI (Jinja2, vanilla JS)
registry.json       The default app registry served from this repo
```

### FjordFlix: Cloudflare Tunnel and direct video

The FjordFlix installer includes **Adgang og Cloudflare**. Choose No to skip gateway setup, or Yes to follow the DNS and router guide. After app installation, FjordHub configures its own Caddy container and verifies HTTPS with a temporary proof served by that FjordFlix instance before enabling direct delivery. The same guide is available from the gear on the app card. Update both FjordHub and FjordFlix first for an existing installation.

Certificates and configuration persist in Docker volumes; retries reuse the gateway. Other services occupying ports 80/443 are not changed. You can select an existing reverse proxy instead and configure its media-only route. Failed verification leaves playback settings unchanged. Web and media require different HTTPS domains. DNS and router configuration remain steps in their respective interfaces; automatic dynamic DNS is not included. Test playback from outside the LAN after setup.

Validation: `python -m unittest discover -s tests -q`. `tests/browser_media_guide.py` tests the shared UI using isolated state. `tests/docker_media_gateway.py` uses a disposable FjordFlix on 8099 and real Caddy on test ports without requesting public certificates.

The automatic media gateway recognizes the bundled `fjordhub-traefik` HTTP entrypoint. It registers a hostname-specific route using Docker labels on the shared `fjord-net` network, and publishes only Caddy's HTTPS port 443. Traefik is not restarted. Its HTTP route forwards certificate challenges and redirects to Caddy. Other port owners still block automatic setup. See [Traefik Docker routing](https://doc.traefik.io/traefik/v3.3/routing/providers/docker/).

`tests/docker_traefik_media.py` verifies hostname routing through real Traefik, Caddy and a disposable Flix container. Set `TRAEFIK_TEST_IMAGE=traefik:v3.6` for Docker engines incompatible with the older bundled v3.3 Docker API client. The test uses isolated ports and does not issue public certificates or change the deployed proxy version.


## Change an app's file location

Open the app's gear menu and use **Filplaceringer**. This is available to hub
administrators for configured bind-mount paths declared by the app's installer.
Choose the app folder, a **Proxmox-lager**, and a **Mappenavn**. FjordHub
reads eligible storages from the configured Proxmox node (including ones not yet
attached to the LXC), displays capacity and flags the system storage pool.
It computes the destination itself; users do not enter Linux paths. Missing
folders are created automatically; existing destinations must be empty.

Discovery uses the existing `PROXMOX_API_URL`, `PROXMOX_NODE`, `PROXMOX_VMID`,
`PROXMOX_TOKEN_ID`, `PROXMOX_TOKEN_SECRET` and `PROXMOX_VERIFY_SSL` settings.
The token needs LXC configuration read access and storage audit permissions.
If Proxmox returns no visible storages, the dialog offers copyable `PVEAuditor`
ACL commands for the token and its user, scoped to `/storage`. These only grant
read access. FjordHub never runs PVE commands itself.

Active storages allowing `rootdir` are selectable. Directory/NAS storage is
attached through a `fjordhub` subdirectory; block storage such as `local-lvm`
requires a new container disk size in GiB. Unprivileged containers also use
managed container disks to avoid bind-mount UID mapping problems. An existing
matching LXC data mount is reused. A move within the system storage pool does
not free capacity in that pool.

For missing mounts the dialog generates commands for the selected storage and
LXC: check the source, select an unused `mpN`, back up the LXC configuration,
attach storage and reboot the LXC. Finish uploads before running them. The
commands refuse to hide a nonempty destination or replace a conflicting mount.
The browser checks every five seconds after each response and survives the
restart. **Start flytning/kopiering** becomes available once the matching mount
is visible; starting still requires a click and a fresh server-side check.
The access-permissions dialog similarly polls until storage becomes visible,
without requiring a restart or starting a file operation.

**Kopiér filer og skift placering** checks the destination and available space,
pauses the app's Compose services, copies and verifies files with SHA-256, and
updates only the selected `.env` entry. Existing Compose overrides and secrets
are retained. Only previously running services are restarted; the operation
waits for their running/healthy state. It never pulls or builds new app images.
Finish uploads before starting. The settings dialog can be closed and reopened
while the copy runs.

Choose **Kopiér** (default) to retain the original files, or **Flyt** to reclaim
the old space automatically. Move first makes the same verified copy, switches
the configuration and waits for previously running services to start successfully.
Only then does it remove the unchanged originals. A stopped app stays stopped;
its files are removed after verification and the configuration switch.
The empty source directory itself remains in place.

A sealed `.fjordhub-storage-transfer.json` manifest on the destination records
the verified copy. Its checksum is also stored in the hub's job state. Changed
or new source files, missing destination files and changed links stop cleanup.
If cleanup fails after activation, the new location remains active: FjordHub
reports incomplete cleanup and never rolls back to a partially emptied source.
Inspect the remaining files before manual cleanup. Do not restore the old
environment after cleanup has started. Successful cleanup removes the manifest.

Failed copies may leave
partial files in the destination; no files there are overwritten or automatically
deleted. The previous environment is backed up under
`/data/storage-backups/<app-id>/<job-id>.env`, outside the app's Git repository.
If activation fails, FjordHub restores the old configuration and attempts to
restart the previously running services.

A hub restart during migration is reported as interrupted and blocks further app
changes. An administrator must inspect the helper container labelled
`dk.fjordhub.storage-copy=1`, both directories and the environment backup before
recovering the app. Do not clear a running storage job or restart the app until
the copy helper and configuration have been checked. Normal app updates and
FjordHub self-update are blocked while migration is in progress.
