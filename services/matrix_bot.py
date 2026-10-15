"""FjordHub's Matrix bot: encrypted chats, read-only status and alert messages.

No Docker socket, server admin credentials or shell access is mounted here.
A Matrix account must be explicitly allowlisted from the FjordHub admin UI.
"""
import asyncio
import io
import json
import logging
import os
import time
from pathlib import Path

import requests
from nio import AsyncClient, ClientConfig, InviteEvent, LoginResponse, MatrixRoom, RoomMessageText

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("fjordhub.matrix")
ROOT = Path("/config")
CONFIG = ROOT / "config.json"
HEALTH = ROOT / "health.json"
SESSION = ROOT / "session.json"
SERVER = os.environ.get("MATRIX_HOMESERVER", "")
API = os.environ.get("FJORDHUB_RESOURCE_API", "")
COMMANDS = {
    "hjælp": "Skriv: status, apps eller rapport. FjordHub sender også beskeder om appnedbrud.",
    "help": "Skriv: status, apps eller rapport. FjordHub sender også beskeder om appnedbrud.",
}


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
        self.old_status = None
        self.next_health = 0

    async def login(self):
        if self.saved.get("access_token") and self.saved.get("device_id"):
            self.client.restore_login(self.saved["user_id"], self.saved["access_token"],
                                      self.saved["device_id"])
            log.info("Restored Matrix device session")
            return
        response = await self.client.login(read(CONFIG)["password"], device_name="FjordHub Bot")
        if not isinstance(response, LoginResponse):
            raise RuntimeError("Bot-login fejlede; kontrollér Matrix-kontoen.")
        write(SESSION, {"user_id": response.user_id, "device_id": response.device_id,
                        "access_token": response.access_token})
        log.info("Created new Matrix bot device")

    async def on_invite(self, room: MatrixRoom, event: InviteEvent):
        if not allowed(event.sender):
            log.warning("Ignored Matrix invite from unauthorized user")
            return
        await self.client.join(room.room_id)

    def rooms_for(self, user_id):
        return [room.room_id for room in self.client.rooms.values()
                if room.encrypted and user_id in room.users and self.client.user_id in room.users]

    async def send(self, room_id, body):
        # Payloads are encrypted; a new device must later be verified manually in Element X.
        await self.client.room_send(
            room_id, "m.room.message", {"msgtype": "m.text", "body": body[:8000]},
            ignore_unverified_devices=True)

    async def on_message(self, room: MatrixRoom, event: RoomMessageText):
        if not room.encrypted or not event.decrypted or not allowed(event.sender):
            return
        if event.sender == self.client.user_id:
            return
        command = event.body.strip().lower().lstrip("/")
        try:
            if command in COMMANDS:
                await self.send(room.room_id, COMMANDS[command])
            elif command in ("status", "apps", "rapport"):
                snapshot = await asyncio.to_thread(resources)
                if command == "rapport":
                    await self.send_report(room.room_id, snapshot)
                else:
                    await self.send(room.room_id, status_text(snapshot, details=command == "apps"))
            else:
                await self.send(room.room_id, "Jeg forstår: status, apps, rapport eller hjælp.")
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
            if now >= self.next_health:
                self.next_health = now + 60
                await self.watch_status()
            write(HEALTH, {"updated": time.time(), "connected": True})
            await asyncio.sleep(6)

    async def watch_status(self):
        try:
            snapshot = await asyncio.to_thread(resources)
            state = {a["name"]: a["running"] == a["total"] and a["total"] > 0
                     for a in running_apps(snapshot)}
            if self.old_status is not None:
                for app_name, healthy in state.items():
                    if app_name in self.old_status and self.old_status[app_name] != healthy:
                        text = (("✅ " if healthy else "🚨 ") + app_name +
                                (" kører igen." if healthy else " har stoppede containere."))
                        for recipient in read(CONFIG).get("allowed_users", []):
                            if self.rooms_for(recipient):
                                await self.send(self.rooms_for(recipient)[0], text)
            self.old_status = state
        except Exception:
            log.exception("Failed to retrieve FjordHub health snapshot")

    async def run(self):
        await self.login()
        try:
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
