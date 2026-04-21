from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

import httpx
import pytest

from app.config import settings
from app.utils.currency_rate import get_rate, get_currency_rate
from app.utils.prices import update_order_prices

API_KEY = "test_api_key"


@pytest.fixture()
def mock_response():
    response = MagicMock()
    response.status_code = 200
    return response


@pytest.fixture
def order_data():
    return {
        "order_id": "f6b35aa5-22ad-4681-88e8-036fe9d3209e",
        "cart_price": Decimal("100.50"),
        "delivery_price": Decimal("20.00"),
        "total_price": Decimal("120.50")
    }


class TestPrices:
    def test_get_rate_success(self, mock_response):
        mock_response.json.return_value = {"success": True, "rates": {settings.db_currency: 1.23396}}

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            result = get_rate(currency=settings.db_currency, api_key=API_KEY)

        assert result == Decimal("1.23396")

    def test_get_rate_failure(self):
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.TimeoutException(
                "Connection timeout")
            result = get_rate(currency=settings.db_currency, api_key=API_KEY)

        assert result is None

    def test_get_currency_rate_cache_hit(self):
        cached_value = "1.23396"

        with patch('app.utils.currency_rate.get_cached', new=MagicMock(return_value=Decimal(cached_value))):
            result = get_currency_rate(currency=settings.db_currency)

        assert result == Decimal(cached_value)


class TestUpdateOrder:
    def test_update_order_prices_success(self, mock_response, order_data):
        with patch('httpx.Client') as mock_client:
            mock_instance = mock_client.return_value.__enter__.return_value
            mock_instance.patch.return_value = mock_response
            result = update_order_prices(order_data)

        expected_url = f"{settings.orders_service_url}/{order_data['order_id']}"
        expected_json = {
            "cart_price": str(order_data["cart_price"]),
            "delivery_price": str(order_data["delivery_price"]),
            "total_price": str(order_data["total_price"])
        }

        assert result is True
        mock_instance.patch.assert_called_once_with(expected_url, json=expected_json)

    def test_update_order_prices_failure(self, order_data):
        with patch('httpx.Client') as mock_client:
            mock_instance = mock_client.return_value.__enter__.return_value
            mock_instance.patch.side_effect = httpx.TimeoutException("Connection timeout")
            result = update_order_prices(order_data)

        assert result is False
        mock_instance.patch.assert_called_once()
