"""FjordHub's Matrix bot: encrypted chats, status, confirmed app updates and alerts.

No Docker socket, server admin credentials or shell access is mounted here.
A Matrix account must be explicitly allowlisted from the FjordHub admin UI.
"""
import asyncio
import io
import json
import logging
import os
import re
import time
from pathlib import Path

import requests
from nio import (AsyncClient, ClientConfig, InviteEvent, LoginResponse, MatrixRoom,
                 RoomMessageText, RoomMessagesResponse, RoomRedactResponse, RoomSendError)
if __package__:
    from .bot_identity import ensure_identity
    from .bot_queries import torrent_query, torrent_messages, torrent_message_html, download_period, download_history_messages, upload_question, upload_menu, upload_answer, storage_question, storage_answer
else:
    from bot_identity import ensure_identity
    from bot_queries import torrent_query, torrent_messages, torrent_message_html, download_period, download_history_messages, upload_question, upload_menu, upload_answer, storage_question, storage_answer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("fjordhub.matrix")
ROOT = Path("/config")
CONFIG = ROOT / "config.json"
HEALTH = ROOT / "health.json"
SESSION = ROOT / "session.json"
ALERTS = ROOT / "status-alerts.json"
SERVER = os.environ.get("MATRIX_HOMESERVER", "")
API = os.environ.get("FJORDHUB_RESOURCE_API", "")
HELP_TEXT = "\n".join((
    "Kommandoer:",
    "• status",
    "• apps",
    "• rapport",
    "• hjælp",
    "• opdateringer – tjek hvilke apps der kan opdateres",
    "",
    "Du kan også spørge:",
    "• Kan du sende mit krediterede upload?",
    "• Hvor meget midlertidig plads bruger RSS?",
    "• Hvad seeder nu?",
    "• Hvad downloader nu?",
    "• Er der downloadet noget nyt i dag?",
    "• Har du downloadet noget nyt siden i går?",
    "• Hvad er downloadet de sidste 7 dage?",
    "",
    "• ryd botbeskeder – fjern mine beskeder i denne samtale.",
))
COMMANDS = {"hjælp": HELP_TEXT, "help": HELP_TEXT}
CLEAR_BOT_COMMANDS = {'ryd botbeskeder', 'ryd bot beskeder', 'clear bot messages'}


def read(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def write(path, payload):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(path)


def allowed(user_id):
    return user_id in read(CONFIG).get("allowed_users", [])


def update_request(action, sender, room, confirmation=''):
    config = read(CONFIG)
    endpoint = API.split('/api/', 1)[0] + '/api/matrix/bot/updates'
    with requests.Session() as session:
        session.trust_env = False
        response = session.post(endpoint, json={'action': action, 'sender': sender,
            'room': room, 'confirmation': confirmation},
            headers={'Authorization': 'Bearer ' + config.get('monitor_token', '')},
            timeout=(5, 180), allow_redirects=False)
        payload = response.json()
        if not response.ok or not payload.get('ok'):
            raise RuntimeError(payload.get('error') or 'Opdateringsforespørgslen mislykkedes.')
        return payload


def update_question(command):
    text = command.lower().replace("é", "e")
    return any(word in text for word in ('opdatering', 'opdatere', 'opdater ', 'update')) or text in {'opdater', 'opdatér'}


def resources():
    token = read(CONFIG).get("monitor_token")
    if not token:
        raise RuntimeError("FjordHub-monitorering er ikke konfigureret.")
    response = requests.get(API, headers={"Authorization": "Bearer " + token}, timeout=15)
    response.raise_for_status()
    result = response.json()
    if not result.get("ok"):
        raise RuntimeError("FjordHub-status er midlertidigt utilgængelig.")
    return result


def running_apps(snapshot):
    apps = snapshot.get("apps", []) or []
    return [
        {"name": str(app.get("name") or app.get("id") or "App")[:70],
         "running": int(app.get("running_count") or 0),
         "total": int(app.get("container_count") or 0)}
        for app in apps if isinstance(app, dict)
    ]


def status_text(snapshot, details=False):
    apps = running_apps(snapshot)
    total = sum(app["total"] for app in apps)
    running = sum(app["running"] for app in apps)
    title = f"FjordHub: {running}/{total} app-containere kører."
    if not details:
        return title + "\nSkriv 'apps' for detaljer eller 'rapport' for en fil."
    if not apps:
        return title + "\nIngen appdata fundet."
    return title + "\n" + "\n".join(
        ("✅ " if item["running"] == item["total"] and item["total"] > 0 else "⚠️ ") +
        f"{item['name']}: {item['running']}/{item['total']}" for item in apps
    )



def asks_about_todays_downloads(message):
    text = message.strip().lower()
    today = "i dag" in text or "idag" in text
    subject = any(term in text for term in ("download", "hentet", "færdig", "ny", "rss"))
    return today and subject


def seeding_snapshot(intent='seeding'):
    token = read(CONFIG).get('monitor_token')
    if not token:
        raise RuntimeError('FjordHub-bottens læseadgang mangler.')
    response = requests.get('http://fjordhub:8080/api/matrix/bot/seeding',
                            params={'activity': intent if intent in {'seeding', 'downloading'} else 'all'},
                            headers={'Authorization': 'Bearer ' + token}, timeout=20)
    response.raise_for_status()
    payload = response.json()
    if not payload.get('ok') or not isinstance(payload.get('torrents'), list):
        raise RuntimeError('FjordSeed-status er ikke tilgængelig.')
    return payload


def storage_snapshot():
    token = read(CONFIG).get('monitor_token')
    if not token:
        raise RuntimeError('FjordHub-bottens læseadgang mangler.')
    response = requests.get('http://fjordhub:8080/api/matrix/bot/storage',
                            headers={'Authorization': 'Bearer ' + token}, timeout=50)
    response.raise_for_status()
    payload = response.json()
    if payload.get('ok') is not True:
        raise RuntimeError('Pladsforbruget er ikke tilgængeligt.')
    return payload


def credit_snapshot():
    token = read(CONFIG).get('monitor_token')
    if not token:
        raise RuntimeError('FjordHub-bottens læseadgang mangler.')
    response = requests.get('http://fjordhub:8080/api/matrix/bot/upload',
                            headers={'Authorization': 'Bearer ' + token}, timeout=20)
    response.raise_for_status()
    payload = response.json()
    if payload.get('ok') is not True or not isinstance(payload.get('options'), list):
        raise RuntimeError('Uploadtal er ikke tilgængelige.')
    return payload['options']


def download_history(period='today'):
    token = read(CONFIG).get("monitor_token")
    if not token:
        raise RuntimeError("FjordHub-bottens læseadgang mangler.")
    response = requests.get("http://fjordhub:8080/api/matrix/bot/downloads",
                            params={'period': period},
                            headers={"Authorization": "Bearer " + token}, timeout=10)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError("FjordHub kan ikke hente FjordSeed-hændelser.")
    return download_history_messages(payload)


def todays_downloads_text():
    return '\n\n'.join(download_history('today'))


class FjordBot:
    def __init__(self):
        cfg = read(CONFIG)
        user_id = cfg["user_id"]
        (ROOT / "store").mkdir(parents=True, exist_ok=True)
        saved = read(SESSION)
        device_id = saved.get("device_id")
        self.client = AsyncClient(
            SERVER, user_id, device_id=device_id, store_path=str(ROOT / "store"),
            config=ClientConfig(store_sync_tokens=True, encryption_enabled=True))
        self.saved = saved
        self.client.add_event_callback(self.on_invite, InviteEvent)
        self.client.add_event_callback(self.on_message, RoomMessageText)
        self.pending_status = {}
        self.alerted_users = {}
        saved_alerts = read(ALERTS)
        entries = saved_alerts.get('apps', {}) if isinstance(saved_alerts, dict) else {}
        if isinstance(entries, dict):
            for name, users in entries.items():
                if isinstance(name, str) and isinstance(users, list):
                    recipients = {user for user in users if isinstance(user, str) and user}
                    if recipients:
                        self.alerted_users[name] = recipients
        # Only delivered outages need to survive a process/container restart.
        # All other apps retain the silent healthy baseline at first observation.
        self.old_status = {name: False for name in self.alerted_users}
        self.next_health = 0
        self.cleaning_rooms = set()
        self.identity_state = {"status":"pending","message":"Klargør bottens identitet."}
        self.next_identity_check = 0

    async def login(self):
        if self.saved.get("access_token") and self.saved.get("device_id"):
            self.client.restore_login(user_id=self.saved["user_id"],
                                      device_id=self.saved["device_id"],
                                      access_token=self.saved["access_token"])
            log.info("Restored Matrix device session")
            return
        response = await self.client.login(read(CONFIG)["password"], device_name="FjordHub Bot")
        if not isinstance(response, LoginResponse):
            raise RuntimeError("Bot-login fejlede; kontrollér Matrix-kontoen.")
        write(SESSION, {"user_id": response.user_id, "device_id": response.device_id,
                        "access_token": response.access_token})
        log.info("Created new Matrix bot device")

    async def verify_identity(self):
        self.next_identity_check = time.time() + 300
        try:
            if self.client.should_upload_keys:
                await self.client.keys_upload()
            self.identity_state = await asyncio.to_thread(
                ensure_identity, SERVER, self.client.user_id, self.client.device_id,
                self.client.access_token, read(CONFIG).get('password', ''),
                self.client.olm.account, ROOT / 'cross-signing.json')
            log.info('Bot identity: %s', self.identity_state['status'])
        except Exception:
            # Never log server response bodies or credentials during UI auth.
            log.warning('Bot identity verification unavailable; retrying in five minutes')
            self.identity_state = {'status':'retrying','message':'Kunne ikke verificere botenheden endnu. Prøver igen automatisk.'}

    async def on_invite(self, room: MatrixRoom, event: InviteEvent):
        if not allowed(event.sender):
            log.warning("Ignored Matrix invite from unauthorized user")
            return
        await self.client.join(room.room_id)

    def rooms_for(self, user_id):
        return [room.room_id for room in self.client.rooms.values()
                if room.encrypted and user_id in room.users and self.client.user_id in room.users]

    async def send(self, room_id, body):
        # The managed bot signs its own device at startup. Recipient devices
        # still follow their existing encryption and trust settings.
        content = {"msgtype": "m.text", "body": body[:8000]}
        if body.startswith(('FjordSeed · Seeding', 'FjordSeed · Downloads')):
            content.update(format='org.matrix.custom.html', formatted_body=torrent_message_html(body[:8000]))
        response = await self.client.room_send(
            room_id, "m.room.message", content,
            ignore_unverified_devices=True)
        if isinstance(response, RoomSendError):
            raise RuntimeError('Matrix kunne ikke levere botbeskeden.')

    def save_status_alerts(self):
        write(ALERTS, {'apps': {name: sorted(users) for name, users in self.alerted_users.items() if users}})

    async def clear_bot_messages(self, room, requester):
        # This is intentionally limited to the requester's private bot chat.
        # Never remove another participant's messages or any room state.
        if (not room.encrypted or not allowed(requester) or
                set(room.users) != {requester, self.client.user_id}):
            await self.send(room.room_id, "Jeg kan kun rydde mine beskeder i din private, krypterede samtale med mig.")
            return
        cleaning = getattr(self, 'cleaning_rooms', None)
        if cleaning is None:
            self.cleaning_rooms = cleaning = set()
        if room.room_id in cleaning:
            return
        cleaning.add(room.room_id)
        removed = 0
        incomplete = False
        limited = False
        try:
            cursor = None
            seen_cursors = set()
            seen_events = set()
            for page in range(50):
                response = await self.client.room_messages(room.room_id, start=cursor, limit=100,
                    message_filter={'senders': [self.client.user_id],
                                    'types': ['m.room.message', 'm.room.encrypted']})
                if not isinstance(response, RoomMessagesResponse):
                    incomplete = True
                    break
                for event in response.chunk:
                    source = getattr(event, 'source', {}) or {}
                    event_id = getattr(event, 'event_id', None)
                    if (getattr(event, 'sender', None) != self.client.user_id or not event_id or
                            event_id in seen_events or source.get('type') not in {'m.room.message', 'm.room.encrypted'} or
                            source.get('unsigned', {}).get('redacted_because')):
                        continue
                    seen_events.add(event_id)
                    result = await self.client.room_redact(room.room_id, event_id,
                                                          reason='Ryd botbeskeder · anmodet af samtalens bruger')
                    if not isinstance(result, RoomRedactResponse):
                        incomplete = True
                        break
                    removed += 1
                if incomplete or not response.end:
                    break
                if response.end == cursor or response.end in seen_cursors:
                    incomplete = True
                    break
                seen_cursors.add(response.end)
                cursor = response.end
            else:
                limited = True
        except Exception:
            log.exception('Bot message cleanup interrupted')
            incomplete = True
        finally:
            cleaning.discard(room.room_id)
        text = f'Fjernede indholdet af {removed} af mine beskeder. Dine beskeder er bevaret.'
        if incomplete:
            text += ' Oprydningen blev afbrudt; ikke alle botbeskeder kunne fjernes.'
        elif limited:
            text += ' Oprydningen nåede sin grænse; ældre botbeskeder kan være tilbage.'
        text += ' Element kan stadig vise markeringer for slettede beskeder.'
        await self.send(room.room_id, text)

    async def handle_updates(self, room, sender, command):
        if set(room.users) != {sender, self.client.user_id}:
            await self.send(room.room_id, 'Opdateringer kan kun styres i din private, krypterede samtale med mig.')
            return
        pending = getattr(self, 'pending_updates', None)
        if pending is None:
            pending = self.pending_updates = {}
        key = (sender, room.room_id)
        plan = pending.get(key)
        confirming = command in {'ja', 'ja opdater', 'ja opdatér', 'bekræft opdatering'}
        cancelling = command in {'nej', 'annuller', 'annullér'}
        if confirming or cancelling:
            pending.pop(key, None)
            if not plan or plan['expires'] < time.time():
                await self.send(room.room_id, 'Bekræftelsen er udløbet. Skriv opdateringer for at tjekke igen.')
                return
            try:
                result = await asyncio.to_thread(update_request, 'confirm' if confirming else 'cancel', sender, room.room_id, plan['token'])
            except Exception as exc:
                await self.send(room.room_id, str(exc))
                return
            if cancelling:
                await self.send(room.room_id, 'Opdatering annulleret.')
            else:
                queued = result.get('queued', [])
                names = plan['names']
                text = 'FjordHub · Opdateringer\n\n'
                text += 'Sat i den normale opdateringskø:\n' + '\n'.join('• ' + names.get(i, i) for i in queued) if queued else 'Ingen apps blev sat i kø. De kan allerede være opdateret eller optaget.'
                if result.get('skipped'):
                    text += '\n\nKunne ikke sættes i kø:\n' + '\n'.join('• ' + names.get(i, i) for i in result['skipped'])
                await self.send(room.room_id, text + '\n\nSe fremdriften i FjordHub.')
            return
        pending.pop(key, None)
        await self.send(room.room_id, 'FjordHub · Opdateringer\n\nJeg tjekker dine installerede apps…')
        try:
            result = await asyncio.to_thread(update_request, 'check', sender, room.room_id)
        except Exception:
            await self.send(room.room_id, 'Kunne ikke tjekke opdateringer lige nu. Prøv igen senere.')
            return
        rows = result.get('apps', [])
        available = [r for r in rows if r.get('update_available') and not r.get('blocked') and not r.get('running') and not r.get('error')]
        blocks = ['FjordHub · Appopdateringer']
        if available:
            blocks.append('Klar til opdatering:\n' + '\n'.join('• ' + r['name'] for r in available))
        else:
            blocks.append('Ingen nye appopdateringer klar.')
        for field, title in [('running', 'Opdaterer allerede'), ('blocked', 'Kræver manuel håndtering (lokale ændringer)'), ('error', 'Kunne ikke kontrolleres')]:
            entries = [r['name'] for r in rows if r.get(field)]
            if entries:
                blocks.append(title + ':\n' + '\n'.join('• ' + name for name in entries))
        token = result.get('confirmation')
        if token:
            pending[key] = {'token': token, 'expires': time.time() + 300, 'names': {r['id']: r['name'] for r in available}}
            blocks.append('Skal jeg opdatere appsene under Klar til opdatering?\nSvar ja eller nej inden 5 minutter.')
        elif available:
            blocks.append('Aktivér Tillad opdateringer via botten for din Matrix-bruger i FjordHub → Integrationer → Matrix, hvis jeg skal starte dem for dig.')
        blocks.append('Dette tjek gælder installerede apps. FjordHub og selve botten opdateres fra FjordHub.')
        await self.send(room.room_id, '\n\n'.join(blocks))

    async def handle_upload(self, room_id, sender, command):
        menus = getattr(self, 'upload_menus', None)
        if menus is None:
            menus = self.upload_menus = {}
        key = sender, room_id
        if upload_question(command):
            options = await asyncio.to_thread(credit_snapshot)
            now = time.time()
            for expired in [k for k, v in menus.items() if v['expires'] <= now]:
                menus.pop(expired, None)
            if options:
                if len(menus) >= 200 and key not in menus:
                    menus.pop(next(iter(menus)))
                menus[key] = {'expires': now + 300,
                              'choices': [(o['kind'], o['id']) for o in options]}
            else:
                menus.pop(key, None)
            await self.send(room_id, upload_menu(options))
            return True
        menu = menus.get(key)
        if menu is None or not (re.fullmatch(r'[0-9]{1,3}\.?', command) or command in {'annuller', 'annullér'}):
            return False
        if command in {'annuller', 'annullér'}:
            menus.pop(key, None)
            await self.send(room_id, 'Uploadmenuen er lukket.')
            return True
        if menu['expires'] <= time.time():
            menus.pop(key, None)
            await self.send(room_id, 'Uploadmenuen er udløbet. Spørg om krediteret upload igen.')
            return True
        index = int(command.rstrip('.')) - 1
        if not 0 <= index < len(menu['choices']):
            await self.send(room_id, f"Vælg et nummer fra 1 til {len(menu['choices'])}.")
            return True
        identity = menu['choices'][index]
        # Resolve stable IDs against a fresh snapshot, never against a reordered
        # list or another user's conversation. Selection remains retryable.
        options = await asyncio.to_thread(credit_snapshot)
        option = next((o for o in options if (o['kind'], o['id']) == identity), None)
        await self.send(room_id, upload_answer(option) if option else
                        'Valget findes ikke længere. Spørg om krediteret upload igen.')
        return True

    async def on_message(self, room: MatrixRoom, event: RoomMessageText):
        if not room.encrypted or not event.decrypted or not allowed(event.sender):
            return
        if event.sender == self.client.user_id:
            return
        command = event.body.strip().lower().lstrip("/")
        try:
            if update_question(command) or (command in {'ja', 'ja opdater', 'ja opdatér', 'bekræft opdatering', 'nej', 'annuller', 'annullér'} and (event.sender, room.room_id) in getattr(self, 'pending_updates', {})):
                await self.handle_updates(room, event.sender, command)
            elif await self.handle_upload(room.room_id, event.sender, command):
                pass
            elif command in CLEAR_BOT_COMMANDS:
                await self.clear_bot_messages(room, event.sender)
            elif command in COMMANDS:
                await self.send(room.room_id, COMMANDS[command])
            elif storage_question(command):
                payload = await asyncio.to_thread(storage_snapshot)
                await self.send(room.room_id, storage_answer(payload))
            elif (period := download_period(command)):
                for answer in await asyncio.to_thread(download_history, period):
                    await self.send(room.room_id, answer)
            elif (intent := torrent_query(command)):
                payload = await asyncio.to_thread(seeding_snapshot, intent)
                for answer in torrent_messages(payload, intent):
                    await self.send(room.room_id, answer)
            elif command in ("status", "apps", "rapport"):
                snapshot = await asyncio.to_thread(resources)
                if command == "rapport":
                    await self.send_report(room.room_id, snapshot)
                else:
                    await self.send(room.room_id, status_text(snapshot, details=command == "apps"))
            else:
                await self.send(room.room_id, "Jeg genkendte ikke kommandoen.\n\n" + HELP_TEXT)
        except Exception:
            log.exception("Failed to handle bot command")
            await self.send(room.room_id, "Kunne ikke hente oplysninger lige nu.")

    async def send_report(self, room_id, snapshot):
        # Upload encrypted file content (rather than merely encrypting the message).
        content = json.dumps(snapshot, indent=2, ensure_ascii=False).encode("utf-8")
        response, keys = await self.client.upload(
            io.BytesIO(content), content_type="application/json",
            filename="fjordhub-rapport.json", filesize=len(content), encrypt=True)
        if not hasattr(response, "content_uri") or not keys:
            await self.send(room_id, "Kunne ikke uploade den krypterede rapport.")
            return
        await self.client.room_send(
            room_id, "m.room.message",
            {"msgtype": "m.file", "body": "fjordhub-rapport.json",
             "file": {**keys, "url": response.content_uri},
             "info": {"mimetype": "application/json", "size": len(content)}},
            ignore_unverified_devices=True)

    async def poll_outbox(self):
        queue = ROOT / "outbox"
        queue.mkdir(exist_ok=True)
        while True:
            for path in sorted(queue.glob("*.json"))[:30]:
                data = read(path)
                recipient = data.get("recipient", "")
                rooms = self.rooms_for(recipient) if allowed(recipient) else []
                if not rooms:
                    continue  # Keep queued until user has started an encrypted chat.
                try:
                    await self.send(rooms[0], data.get("text", ""))
                    path.unlink(missing_ok=True)
                except Exception:
                    log.exception("Could not deliver Matrix notification")
            now = time.time()
            if now >= self.next_identity_check and self.identity_state.get('status') != 'verified':
                await self.verify_identity()
            if now >= self.next_health:
                self.next_health = now + 60
                await self.watch_status()
            write(HEALTH, {"updated": time.time(), "connected": True, "identity": self.identity_state})
            await asyncio.sleep(6)

    async def watch_status(self):
        try:
            snapshot = await asyncio.to_thread(resources)
            if not snapshot.get("ok"):
                raise RuntimeError("Invalid health snapshot")
            apps = {a['name']: a for a in running_apps(snapshot) if a['total'] > 0}
            state = {name: a['running'] == a['total'] for name, a in apps.items()}
            # Missing app data is unknown, not a stopped or recovered app.
            self.pending_status = {name: value for name, value in self.pending_status.items()
                                   if name in state}
            recipients = set(read(CONFIG).get("allowed_users", []))
            for app_name, healthy in state.items():
                if app_name not in self.old_status and healthy:
                    self.old_status[app_name] = True
                alerted = self.alerted_users.get(app_name, set())
                outstanding = recipients & alerted if healthy else recipients - alerted
                if self.old_status.get(app_name) == healthy and not outstanding:
                    self.pending_status.pop(app_name, None)
                    continue
                previous, count = self.pending_status.get(app_name, (None, 0))
                count = count + 1 if previous == healthy else 1
                self.pending_status[app_name] = (healthy, count)
                log.info("Health candidate %s: running=%s sample=%s", app_name, healthy, count)
                # Polls are one minute apart: require confirmation in both directions.
                if count < 2:
                    continue
                alerted = self.alerted_users.setdefault(app_name, set())
                targets = recipients & alerted if healthy else recipients - alerted
                for recipient in targets:
                    rooms = self.rooms_for(recipient)
                    if not rooms:
                        continue
                    text = (("✅ " if healthy else "🚨 ") + app_name +
                            (f" kører igen. Alle containere er startet ({apps[app_name]['running']}/{apps[app_name]['total']})."
                             if healthy else " har stoppede containere."))
                    await self.send(rooms[0], text)
                    if healthy:
                        alerted.discard(recipient)
                    else:
                        alerted.add(recipient)
                    self.save_status_alerts()
                self.old_status[app_name] = healthy
                self.pending_status.pop(app_name, None)
                if healthy:
                    # Keep undelivered recoveries until the recipient's encrypted
                    # room is available; removed users must never receive them.
                    alerted.intersection_update(recipients)
                    if not alerted:
                        self.alerted_users.pop(app_name, None)
                    self.save_status_alerts()
                log.info("Confirmed health change %s: running=%s", app_name, healthy)
        except Exception:
            self.pending_status.clear()
            log.exception("Failed to retrieve FjordHub health snapshot")

    async def run(self):
        await self.login()
        try:
            await self.verify_identity()
            # Sync runs continuously, including encrypted key exchange.
            await asyncio.gather(self.client.sync_forever(timeout=30000, full_state=True),
                                 self.poll_outbox())
        finally:
            write(HEALTH, {"updated": time.time(), "connected": False})
            await self.client.close()


async def main():
    while True:
        try:
            await FjordBot().run()
        except (Exception,):
            log.exception("Matrix bot disconnected")
            write(HEALTH, {"updated": time.time(), "connected": False})
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
