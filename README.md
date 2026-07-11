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
- **Self-update** — a small sidecar container pulls the latest FjordHub from GitHub and rebuilds/restarts the hub, triggered from the Settings page.
- **Resource monitoring** — host CPU, memory and disk usage plus per-container stats, with a one-click Docker cleanup for reclaiming space.
- **Reverse proxy included** — Traefik routes each app under its own path prefix, so everything is reachable through a single entrypoint.

It is built for the home-lab case: one Linux host (bare metal, VM or Proxmox LXC) running Docker, administered by one or a few people.

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

## Updates

- **Apps** — the dashboard checks each installed app's repository for new commits. Updating pulls the latest code and re-runs compose for that app only.
- **The hub itself** — Settings → Update triggers the `fjordhub-updater` sidecar, which pulls this repository, rebuilds the hub image and restarts the hub container. Progress and logs are shown in the UI and persisted under `DATA_DIR/fjordhub-updater`.

## GPU passthrough (NVIDIA)

Apps that can use a GPU (e.g. FjordLens' AI service) get a **GPU helper** in the install wizard. It sets up NVIDIA GPU access for the FjordHub LXC container on a Proxmox host — one copy-paste, once per host:

1. **One-time host script** — run on the PVE host. It first checks the prerequisites (driver installed, device nodes present, privileged container) and fails with a clear message instead of writing a half-broken config. It then installs a small `fjordhub-gpu-sync` systemd service and runs it immediately.
2. **`fjordhub-gpu-sync`** runs at every host boot, before the containers start. It loads the NVIDIA kernel modules, removes stale GPU mount lines whose source files no longer exist, and rewrites `/etc/pve/lxc/<CTID>.conf` to match the driver currently installed on the host. **Host driver updates therefore never break the containers** — reboot the host and everything is re-synced automatically.
3. **In-container auto-setup** — one click in the wizard. Installs the NVIDIA container toolkit, installs userspace libraries matching the host driver exactly (or falls back to the bind-mounted host libraries when the exact version isn't packaged), sets `no-cgroups = true` (an LXC may not manage cgroup device rules itself — the host already grants access), configures the Docker runtime and restarts Docker. The GPU test button unlocks automatically once everything is back up.

A few facts worth knowing:

- **The GPU model doesn't matter.** All GeForce cards (RTX 20/30/40 series, …) use the same unified NVIDIA driver — the only requirement is that the host's driver is new enough to know the card. Nothing in FjordHub is card-specific.
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
