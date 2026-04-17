import logging
import os
from decimal import Decimal
from typing import Optional

import redis.asyncio as redis

from app.config import CACHE_TTL

REDIS_HOST = os.getenv('REDIS_HOST', 'redis_celery_worker')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}'

logger = logging.getLogger(__name__)


async def set_cache(key: str, value: Decimal, ttl: int = CACHE_TTL):
    async with redis.from_url(REDIS_URL, decode_responses=True) as redis_client:
        try:
            await redis_client.setex(f"rates:{key}", ttl, str(value))
            return True

        except Exception as e:
            logger.error(f"{key} cache write error: {e}")
            return False


async def get_cached(key: str) -> Optional[Decimal]:
    async with redis.from_url(REDIS_URL, decode_responses=True) as redis_client:
        try:
            result = await redis_client.get(f"rates:{key}")
            if result:
                return Decimal(result)
            else:
                return None

        except Exception as e:
            logger.error(f"{key} cache read error: {e}")
            return None
