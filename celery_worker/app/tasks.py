import logging

from celery import shared_task

from app.config import settings
from app.utils.redis import set_cache
from app.utils.currency_rate import get_rate, get_currency_rate
from app.utils.prices import calculate_prices, update_order_prices

logger = logging.getLogger(__name__)


@shared_task(name="calculate_order_prices", bind=True, max_retries=3, default_retry_delay=5)
def calculate_order_prices(self, order: dict):
    headers = order.get("headers", {})
    request_id = headers.get("X-Request-ID")
    user_id = headers.get("user_id")

    try:
        rate = get_currency_rate(settings.db_currency)
        updated_order = calculate_prices(order=order, rate=rate)
        result = update_order_prices(order=updated_order)

        if not result:
            logger.warning("Order price update failed", extra={
                "request_id": request_id,
                "user_id": user_id,
                "order_id": order.get("order_id")
            })
            raise RuntimeError("Update order prices failed")
        logger.info("Order price updated", extra={
            "order_id": order.get("order_id"),
            "user_id": user_id,
            "request_id": request_id
        })
        return True

    except Exception as e:
        logger.exception("Failed to update order prices", extra={
            "request_id": request_id,
            "user_id": user_id,
            "order_id": order.get("order_id"),
            "error_type": type(e).__name__
        })
        raise self.retry(exc=e)


@shared_task(name="update_currency_rate", bind=True, max_retries=3, default_retry_delay=5)
def update_currency_rate(self):
    try:
        rate = get_rate(settings.db_currency)

        if rate is None:
            logger.warning("Currency rate update failed: returned None")
            raise RuntimeError("Updating currency rate API returned None")

        set_cache(settings.db_currency, rate)
        logger.info("Currency rate updated")
        return True

    except Exception as e:
        logger.exception("Failed to get currency rate", extra={"error_type": type(e).__name__})
        raise self.retry(exc=e)
