import logging
import time
from decimal import Decimal
from typing import Optional

import redis

from app.config import settings
from app.observability.metrics import redis_latency, redis_ops

logger = logging.getLogger(__name__)

redis_client = redis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)


def set_cache(key: str, value: Decimal, ttl: int = settings.cache_ttl):
    latency_start = time.perf_counter()
    try:
        redis_client.setex(f"rates:{key}", ttl, str(value))
        redis_ops.labels(operation=f"SET", status="ok").inc()
        logging.info("Set cache OK", extra={"key": key})
        return True

    except Exception as e:
        redis_ops.labels(operation=f"SET", status="error").inc()
        logger.exception("Set cache error", extra={"key": key, "error_type": type(e).__name__})
        return False

    finally:
        redis_latency.labels(operation="SET").observe(time.perf_counter() - latency_start)


def get_cached(key: str) -> Optional[Decimal]:
    latency_start = time.perf_counter()
    try:
        result = redis_client.get(f"rates:{key}")
        if result:
            redis_ops.labels(operation=f"GET", status="hit").inc()
            return Decimal(result)
        else:
            redis_ops.labels(operation=f"GET", status="miss").inc()
            return None

    except Exception as e:
        redis_ops.labels(operation=f"GET", status="error").inc()
        logger.exception("Cache read error", extra={"key": key, "error_type": type(e).__name__})
        return None

    finally:
        redis_latency.labels(operation="GET").observe(time.perf_counter() - latency_start)
