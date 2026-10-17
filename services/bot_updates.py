"""Narrow Matrix update capability: fresh checks, scoped one-use confirmations."""
from concurrent.futures import ThreadPoolExecutor
import fcntl
import json
import secrets
import time


def handle_updates(hub, manager, install_state, app_defs, data):
    sender, room = data.get('sender'), data.get('room')
    config = hub._load(hub.bot_dir / 'config.json')
    if not isinstance(sender, str) or sender not in config.get('allowed_users', []) or not isinstance(room, str) or not room.startswith('!') or len(room) > 512:
        return {'ok': False, 'error': 'Ingen adgang til denne botforespørgsel.'}, 403
    action = data.get('action')
    if action not in {'check', 'confirm', 'cancel'}:
        return {'ok': False, 'error': 'Ugyldig handling.'}, 400
    writable = sender in config.get('update_users', [])
    if action == 'confirm' and not writable:
        return {'ok': False, 'error': 'Aktivér opdateringsadgang for din Matrix-bruger i FjordHub først.'}, 403
    apps = [a for a in app_defs if a['id'] != 'fjordhub' and install_state.get_install_dir(a['id'])]
    if action == 'check':
        def check(a):
            try:
                status = manager.check_now(a)
                return {'id': a['id'], 'name': a.get('name', a['id']),
                        'update_available': bool(status.get('update_available')),
                        'running': bool(status.get('running')),
                        'blocked': bool(status.get('dirty')),
                        'error': bool(status.get('error')) or status.get('state') in {'error', 'failed'}}
            except Exception:
                return {'id': a['id'], 'name': a.get('name', a['id']), 'error': True}
        with ThreadPoolExecutor(max_workers=4) as pool:
            rows = list(pool.map(check, apps))
        selected = [r['id'] for r in rows if r.get('update_available') and not r.get('running') and not r.get('blocked') and not r.get('error')]
    hub.bot_dir.mkdir(parents=True, exist_ok=True)
    path = hub.bot_dir / 'update-confirmations.json'
    # Synchronize concurrent requests and workers; consume before starting jobs.
    with (hub.bot_dir / 'update-confirmations.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        pending = hub._load(path)
        pending = {k: v for k, v in pending.items() if isinstance(v, dict) and v.get('expires', 0) > time.time()}
        if action == 'check':
            pending = {k: v for k, v in pending.items() if (v.get('sender'), v.get('room')) != (sender, room)}
            token = secrets.token_urlsafe(24) if selected and writable else ''
            if token:
                pending[token] = {'sender': sender, 'room': room, 'apps': selected, 'expires': time.time() + 300}
            hub._save(path, pending)
            return {'ok': True, 'apps': rows, 'confirmation': token, 'can_update': writable}, 200
        token = data.get('confirmation')
        plan = pending.get(token) if isinstance(token, str) else None
        if not plan or plan.get('sender') != sender or plan.get('room') != room:
            return {'ok': False, 'error': 'Bekræftelsen er udløbet. Bed om et nyt opdateringstjek.'}, 409
        pending.pop(token)
        hub._save(path, pending)
        if action == 'cancel':
            return {'ok': True, 'cancelled': True}, 200
        selected_apps = [a for a in apps if a['id'] in plan['apps']]
        payload, code = manager.start_all_updates(selected_apps)
        return payload, code
