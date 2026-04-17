import logging
from decimal import Decimal

import httpx

from app.config import ORDERS_SERVICE_URL

logger = logging.getLogger(__name__)


def calculate_prices(order: dict, rate: Decimal):
    order['cart_price'] = Decimal(order['cart_price']) / rate
    order['total_price'] = Decimal(order['total_price']) / rate
    order['delivery_price'] = Decimal(order['delivery_price']) / rate
    return order


async def update_order_prices(order: dict):
    url = f"{ORDERS_SERVICE_URL}/{order['id']}"
    update_data = {
        "cart_price": str(order['cart_price']),
        "delivery_price": str(order['delivery_price']),
        "total_price": str(order['total_price'])
    }

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.patch(url, json=update_data)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Update order prices failed: {e}")
            return False
