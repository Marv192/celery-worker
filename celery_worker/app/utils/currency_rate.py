import logging
import httpx

from decimal import Decimal
from typing import Optional

from app.config import API_KEY, DB_CURRENCY
from app.utils.redis import get_cached, set_cache

logger = logging.getLogger(__name__)


async def get_rate(currency: str = DB_CURRENCY, api_key: str = API_KEY) -> Optional[Decimal]:
    url = 'https://data.fixer.io/api/latest'
    params = {
        'access_key': api_key,
        'symbols': currency
    }

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(url=url, params=params, timeout=10)
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


async def get_currency_rate(currency: str = DB_CURRENCY) -> Optional[Decimal]:
    rate = await get_cached(currency)
    if rate is not None:
        return rate

    rate = await get_rate(currency)

    if rate is not None:
        await set_cache(currency, rate)

    return rate
