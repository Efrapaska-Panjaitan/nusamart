import uuid
from decimal import Decimal
from pydantic import BaseModel, Field, HttpUrl, ConfigDict
class VariantInput(BaseModel):
    sku: str = Field(min_length=2, max_length=80)
    attributes: dict[str, str] = Field(default_factory=dict)
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    stock_quantity: int = Field(ge=0, le=1000000)
class ProductCreate(BaseModel):
    category_id: uuid.UUID
    name: str = Field(min_length=2, max_length=180)
    slug: str = Field(min_length=2, max_length=200, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str = Field(min_length=5, max_length=10000)
    image_url: str = Field(min_length=5, max_length=500)
    status: str = Field(default="active", pattern=r"^(active|draft|archived)$")
    variants: list[VariantInput] = Field(min_length=1, max_length=30)
class ProductUpdate(BaseModel):
    category_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=2, max_length=180)
    slug: str | None = Field(default=None, min_length=2, max_length=200, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = Field(default=None, max_length=10000)
    image_url: str | None = Field(default=None, min_length=5, max_length=500)
    status: str | None = Field(default=None, pattern=r"^(active|draft|archived)$")
class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=2, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = Field(default=None, max_length=1000)
class StockAdjustment(BaseModel):
    variant_id: uuid.UUID
    delta: int = Field(ge=-100000, le=100000)
    note: str = Field(min_length=3, max_length=255)
class ProductOut(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    category_name: str
    category_slug: str
    name: str
    slug: str
    description: str | None
    image_url: str
    status: str
    min_price: Decimal
    max_price: Decimal
    average_rating: float
    review_count: int
    in_stock: bool
    variants: list[dict]
