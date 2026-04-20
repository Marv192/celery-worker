import logging
from decimal import Decimal
from typing import Optional

import redis

from app.config import settings

logger = logging.getLogger(__name__)

redis_client = redis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)


def set_cache(key: str, value: Decimal, ttl: int = settings.cache_ttl):
    try:
        redis_client.setex(f"rates:{key}", ttl, str(value))
        return True

    except Exception as e:
        logger.error(f"{key} cache write error: {e}")
        return False


def get_cached(key: str) -> Optional[Decimal]:
    try:
        result = redis_client.get(f"rates:{key}")
        if result:
            return Decimal(result)
        else:
            return None

    except Exception as e:
        logger.error(f"{key} cache read error: {e}")
        return None
