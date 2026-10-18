import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class Category(Base):
    __tablename__ = "categories"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    products: Mapped[list["Product"]] = relationship(back_populates="category")

class Product(Base):
    __tablename__ = "products"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(180), index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", server_default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    category: Mapped["Category"] = relationship(back_populates="products")
    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="product", cascade="all, delete-orphan")

class ProductVariant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (
        UniqueConstraint("product_id", "sku", name="uq_product_variant_sku"),
        CheckConstraint("price >= 0", name="ck_variant_price_nonnegative"),
        CheckConstraint("stock_on_hand >= 0", name="ck_variant_stock_nonnegative"),
        CheckConstraint("stock_reserved >= 0 AND stock_reserved <= stock_on_hand", name="ck_variant_reserved_valid"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False)
    sku: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    attributes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    stock_on_hand: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    stock_reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    product: Mapped["Product"] = relationship(back_populates="variants")

    @property
    def stock_available(self) -> int:
        return max(0, self.stock_on_hand - self.stock_reserved)
