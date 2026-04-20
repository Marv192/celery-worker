import logging
import httpx

from decimal import Decimal
from typing import Optional

from app.config import settings
from app.utils.redis import get_cached, set_cache

logger = logging.getLogger(__name__)


def get_rate(currency: str = settings.db_currency, api_key: str = settings.api_key) -> Optional[Decimal]:
    url = 'https://data.fixer.io/api/latest'
    params = {
        'access_key': api_key,
        'symbols': currency
    }

    with httpx.Client(timeout=10) as client:
        try:
            response = client.get(url=url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('success'):
                rate = Decimal(str(data['rates'][currency]))
                return rate
            else:
                logger.error(f"Error getting {currency} rate: {data.get('error')}")
                return None

        except Exception as e:
            logger.error(f"Request getting currency rate failed: {e}")
            return None


def get_currency_rate(currency: str = settings.db_currency) -> Optional[Decimal]:
    rate = get_cached(currency)
    if rate is not None:
        return rate

    rate = get_rate(currency)

    if rate is not None:
        set_cache(currency, rate)

    return rate
