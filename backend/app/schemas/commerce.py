import uuid
from pydantic import BaseModel, Field
class AddressCreate(BaseModel):
    label: str = Field(default="Rumah", min_length=1, max_length=50)
    recipient_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=8, max_length=30)
    address_line: str = Field(min_length=5, max_length=255)
    city: str = Field(min_length=2, max_length=100)
    province: str = Field(min_length=2, max_length=100)
    postal_code: str = Field(min_length=4, max_length=10)
    is_default: bool = False
class CartItemCreate(BaseModel):
    variant_id: uuid.UUID
    quantity: int = Field(ge=1, le=99)
class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=99)
class CheckoutQuoteRequest(BaseModel):
    address_id: uuid.UUID | None = None
    shipping_method: str = Field(default="regular", pattern=r"^(regular|express)$")
    coupon_code: str | None = Field(default=None, max_length=40)
class OrderCreate(BaseModel):
    address_id: uuid.UUID
    shipping_method: str = Field(default="regular", pattern=r"^(regular|express)$")
    coupon_code: str | None = Field(default=None, max_length=40)
class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)
class AdminOrderStatusUpdate(BaseModel):
    status: str = Field(pattern=r"^(processing|shipped|delivered|cancelled)$")
    tracking_number: str | None = Field(default=None, max_length=80)
