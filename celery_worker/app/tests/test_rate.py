from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

import httpx
import pytest

from app.config import ORDERS_SERVICE_URL
from app.utils.currency_rate import get_rate, get_currency_rate
from app.utils.prices import update_order_prices

DB_CURRENCY = "USD"
API_KEY = "test_api_key"


@pytest.fixture()
def mock_response():
    response = MagicMock()
    response.status_code = 200
    return response


@pytest.fixture
def order_data():
    return {
        "id": 123,
        "cart_price": Decimal("100.50"),
        "delivery_price": Decimal("20.00"),
        "total_price": Decimal("120.50")
    }


class TestPrices:
    @pytest.mark.asyncio
    async def test_get_rate_success(self, mock_response):
        mock_response.json.return_value = {"success": True, "rates": {DB_CURRENCY: 1.23396}}
        mock_get = AsyncMock(return_value=mock_response)

        with patch('httpx.AsyncClient.get', new=mock_get):
            result = await get_rate(currency=DB_CURRENCY, api_key=API_KEY)

        assert result == Decimal("1.23396")

    @pytest.mark.asyncio
    async def test_get_rate_failure(self):
        mock_get = AsyncMock(side_effect=httpx.TimeoutException("Connection timeout"))

        with patch('httpx.AsyncClient.get', new=mock_get):
            result = await get_rate(currency=DB_CURRENCY, api_key=API_KEY)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_currency_rate_cache_hit(self):
        cached_value = "1.23396"

        with patch('app.utils.currency_rate.get_cached', new=AsyncMock(return_value=Decimal(cached_value))):
            result = await get_currency_rate(currency=DB_CURRENCY)

        assert result == Decimal(cached_value)


class TestUpdateOrder:
    @pytest.mark.asyncio
    async def test_update_order_prices_success(self, mock_response, order_data):
        mock_patch = AsyncMock(return_value=mock_response)

        with patch('httpx.AsyncClient.patch', new=mock_patch):
            result = await update_order_prices(order_data)

        expected_url = f"{ORDERS_SERVICE_URL}/{order_data['id']}"
        expected_json = {
            "cart_price": str(order_data["cart_price"]),
            "delivery_price": str(order_data["delivery_price"]),
            "total_price": str(order_data["total_price"])
        }

        assert result is True
        mock_patch.assert_called_once_with(expected_url, json=expected_json)

    @pytest.mark.asyncio
    async def test_update_order_prices_failure(self, order_data):
        mock_patch = AsyncMock(side_effect=httpx.TimeoutException("Connection timeout"))

        with patch('httpx.AsyncClient.patch', new=mock_patch):
            result = await update_order_prices(order_data)

        assert result is False
        mock_patch.assert_called_once()
