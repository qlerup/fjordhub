# FjordLens GPU Recovery (Proxmox LXC)

This is the quick manual recovery flow we used when FjordLens unexpectedly falls back to CPU after reboot or config changes.

## 1) Proxmox host: verify GRUB kernel cmdline

```bash
grep '^GRUB_CMDLINE_LINUX_DEFAULT=' /etc/default/grub
```

Expected (Intel):

```bash
GRUB_CMDLINE_LINUX_DEFAULT="quiet intel_iommu=on iommu=pt"
```

If you changed it:

```bash
update-grub
reboot
```

## 2) Proxmox host: re-create NVIDIA runtime devices (if missing)

```bash
nvidia-smi
modprobe nvidia
modprobe nvidia_uvm
modprobe nvidia_modeset
command -v nvidia-modprobe >/dev/null && nvidia-modprobe -u -c=0
ls -l /dev/nvidia-uvm /dev/nvidia-uvm-tools
ls -l /dev/nvidia-caps/*
```

## 3) Proxmox host: validate LXC config (CTID 1002)

```bash
grep -nE 'features|apparmor|cgroup2.devices.allow|mount.entry: /dev/nvidia|mount.entry: /sys/class/drm' /etc/pve/lxc/1002.conf
```

Required lines:

```conf
features: nesting=1,keyctl=1
lxc.apparmor.profile: unconfined
lxc.cgroup2.devices.allow: c 195:* rwm
lxc.cgroup2.devices.allow: c 510:* rwm
lxc.cgroup2.devices.allow: c 235:* rwm
lxc.mount.entry: /dev/nvidia0 dev/nvidia0 none bind,optional,create=file
lxc.mount.entry: /dev/nvidiactl dev/nvidiactl none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-uvm dev/nvidia-uvm none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-uvm-tools dev/nvidia-uvm-tools none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-caps dev/nvidia-caps none bind,optional,create=dir
lxc.mount.entry: /dev/nvidia-modeset dev/nvidia-modeset none bind,optional,create=file
lxc.mount.entry: /sys/class/drm sys/class/drm none ro,bind,optional,create=dir
```

Note: `c 510:*` must match your host `/dev/nvidia-uvm` major number.

## 4) Restart LXC and enter container

```bash
pct stop 1002
pct start 1002
pct enter 1002
```

## 5) Inside LXC: NVIDIA container runtime + CUDA tests

```bash
grep -n "no-cgroups" /etc/nvidia-container-runtime/config.toml
```

Expected:

```text
no-cgroups = true
```

If not true:

```bash
sed -i 's/^#\?no-cgroups *= *.*/no-cgroups = true/' /etc/nvidia-container-runtime/config.toml
systemctl restart docker || service docker restart
```

Smoke tests:

```bash
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
docker run --rm --gpus all pytorch/pytorch:2.1.2-cuda12.1-cudnn8-runtime python -c "import torch; print(torch.cuda.is_available()); print(torch.version.cuda); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no gpu')"
```

Expected:

- `True`
- CUDA version printed (for example `12.1`)
- GPU name printed (for example `NVIDIA GeForce RTX 2060`)

## 6) Recreate FjordLens containers

```bash
cd /opt/fjordlens
docker compose up -d --build --force-recreate
curl -s http://localhost:8001/health | python3 -m json.tool
```

Expected in health output:

- `"device": "cuda"`
- `"torch_cuda_available": true`
- `"face_device": "cuda"` (or CPU fallback if face provider initialization fails)

## 7) Verify UI runtime

```bash
curl -s http://localhost:9080/api/ai/status
curl -s http://localhost:9080/api/faces/status
curl -s http://localhost:9080/api/ai/describe/status
```

Then hard refresh browser (`Ctrl+F5`) and confirm runtime shows GPU in Settings -> AI.
