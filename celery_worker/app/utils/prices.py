import logging
from decimal import Decimal

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def calculate_prices(order: dict, rate: Decimal):
    order['cart_price'] = (Decimal(order['cart_price']) / rate).quantize(Decimal('.00'))
    order['delivery_price'] = (Decimal(order['delivery_price']) / rate).quantize(Decimal('.00'))
    order['total_price'] = Decimal(order['cart_price'] + order['delivery_price'])

    return order


def update_order_prices(order: dict):
    url = f"{settings.orders_service_url}/{order['order_id']}"
    update_data = {
        "cart_price": str(order['cart_price']),
        "delivery_price": str(order['delivery_price']),
        "total_price": str(order['total_price'])
    }

    with httpx.Client(timeout=10) as client:
        try:
            response = client.patch(url, json=update_data)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Update order prices failed: {e}")
            return False
