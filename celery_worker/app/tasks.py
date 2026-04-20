import logging

from celery import shared_task

from app.config import settings
from app.utils.redis import set_cache
from app.utils.currency_rate import get_rate, get_currency_rate
from app.utils.prices import calculate_prices, update_order_prices

logger = logging.getLogger(__name__)


@shared_task(name="calculate_order_prices", bind=True, max_retries=3, default_retry_delay=5)
def calculate_order_prices(self, order: dict):
    try:
        rate = get_currency_rate(settings.db_currency)
        updated_order = calculate_prices(order=order, rate=rate)
        result = update_order_prices(order=updated_order)

        if not result:
            raise RuntimeError("Update order prices failed")
        return True

    except Exception as e:
        logger.error("Failed to update order prices")
        raise self.retry(exc=e)


@shared_task(name="update_currency_rate", bind=True, max_retries=3, default_retry_delay=5)
def update_currency_rate(self):
    try:
        rate = get_rate(settings.db_currency)

        if rate is None:
            raise RuntimeError("Updating currency rate API returned None")

        set_cache(settings.db_currency, rate)
        return True

    except Exception as e:
        logger.error("Failed to get currency rate")
        raise self.retry(exc=e)
