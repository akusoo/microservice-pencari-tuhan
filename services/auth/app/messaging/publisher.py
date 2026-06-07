import json
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class EventPublisher:
    """Async Redis Pub/Sub publisher.

    Jika Redis tidak tersedia (misal saat unit test), publish di-skip
    dan hanya di-log sebagai warning — service tetap jalan normal.
    """

    def __init__(self) -> None:
        self._redis: aioredis.Redis | None = None

    async def connect(self, redis_url: str) -> None:
        try:
            self._redis = aioredis.from_url(redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info("EventPublisher connected to Redis at %s", redis_url)
        except Exception as exc:
            logger.warning("Redis unavailable (%s) — events will be skipped", exc)
            self._redis = None

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()
            logger.info("EventPublisher disconnected from Redis")

    async def publish(self, channel: str, data: dict) -> None:
        if not self._redis:
            logger.debug("Publisher not connected — skipped event '%s'", channel)
            return
        payload = json.dumps({
            "event": channel,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        })
        await self._redis.publish(channel, payload)
        logger.info("Published event '%s'", channel)


# Singleton — di-import oleh router dan di-init saat app startup
publisher = EventPublisher()
