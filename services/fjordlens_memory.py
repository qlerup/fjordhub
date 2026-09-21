"""FjordLens budget derived from the same measurements as the Hub dashboard."""
import time

RESERVE = 2 * 1024**3


def budget_from_resources(snapshot):
    system = snapshot.get('system', {})
    if not snapshot.get('ok') or not system.get('available'):
        raise RuntimeError(system.get('message') or 'Host RAM measurement unavailable')
    group = next((a for a in snapshot.get('apps', []) if a.get('id') == 'fjordlens'), None)
    if not group or not group.get('containers'):
        raise RuntimeError('FjordLens containers missing from resource measurement')
    if any(c.get('error') for c in group['containers']):
        raise RuntimeError('Incomplete FjordLens memory measurement')
    total = int(system['memory_limit'])
    used = int(system['memory_usage'])
    own = int(group['memory_usage'])
    if not 0 <= used <= total or not 0 <= own <= total or total <= RESERVE:
        raise RuntimeError('Inconsistent host/FjordLens RAM measurement')
    # Proxmox's LXC usage and Docker's per-container working sets subtract
    # different cache categories and are sampled independently. Docker's sum
    # can legitimately exceed the Proxmox reading, especially after startup.
    # Never reject or inflate the authoritative host reading for that reason.
    # Keep the legacy per-service fields nonnegative; protocol 3 consumers use
    # total_bytes/used_bytes directly and ignore other_bytes/budget_bytes.
    other = max(0, used - own)
    return dict(ok=True, enabled=True, source='fjordhub', measured_at=time.time(),
                total_bytes=total, used_bytes=used, other_bytes=other,
                reserve_bytes=RESERVE, budget_bytes=max(0, total-other-RESERVE),
                pressure=total-used < RESERVE + 128*1024**2)
