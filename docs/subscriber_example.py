"""
Contoh cara service lain (book, member, loan, fine) subscribe ke auth events.

Cara pakai:
  pip install redis>=4.6.0
  python subscriber_example.py

Pastikan Redis sudah jalan:
  cd infra && docker compose up -d

Event yang tersedia (dari auth-service):
  auth.user.registered  → user baru daftar
  auth.user.logged_in   → user login
  auth.user.logged_out  → user logout

Format payload semua event:
{
  "event":     "auth.user.registered",
  "timestamp": "2026-06-07T10:00:00+00:00",
  "data": { ... }   <- isi beda tiap event, lihat komentar di bawah
}
"""

import asyncio
import json

import redis.asyncio as aioredis

REDIS_URL = "redis://localhost:6379"  # ganti ke redis://library-redis:6379 jika dalam Docker

CHANNELS = [
    "auth.user.registered",   # data: user_id, username, email, role
    "auth.user.logged_in",    # data: user_id, username
    "auth.user.logged_out",   # data: user_id
]


async def handle_user_registered(data: dict) -> None:
    """
    Contoh: member service auto-create profil member saat user baru daftar.
    Ganti isi fungsi ini sesuai kebutuhan service masing-masing.
    """
    print(f"  → User baru: {data['username']} ({data['email']}) role={data['role']}")
    # Contoh: db.add(MemberProfile(user_id=data["user_id"], ...))


async def handle_user_logged_in(data: dict) -> None:
    print(f"  → User login: {data['username']} (id={data['user_id']})")


async def handle_user_logged_out(data: dict) -> None:
    print(f"  → User logout: id={data['user_id']}")


HANDLERS = {
    "auth.user.registered": handle_user_registered,
    "auth.user.logged_in":  handle_user_logged_in,
    "auth.user.logged_out": handle_user_logged_out,
}


async def main() -> None:
    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe(*CHANNELS)
    print(f"Subscribed to: {CHANNELS}")
    print("Waiting for events... (Ctrl+C to stop)\n")

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            payload = json.loads(message["data"])
            event   = payload.get("event", "")
            data    = payload.get("data", {})
            print(f"[{payload['timestamp']}] EVENT: {event}")
            handler = HANDLERS.get(event)
            if handler:
                await handler(data)
            print()
        except Exception as exc:
            print(f"Error processing message: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
