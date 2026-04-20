from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class OrderMessageBase(BaseModel):
    order_id: UUID
    cart_price: Decimal = Field(decimal_places=2, max_digits=20, gt=0)
    cart_amount: Decimal = Field(default_factory=Decimal)
    delivery_price: Decimal = Field(decimal_places=2, max_digits=20, gt=0)
    total_price: Decimal = Field(decimal_places=2, max_digits=20, gt=0)


class OrderMessageReceived(OrderMessageBase):
    pass
