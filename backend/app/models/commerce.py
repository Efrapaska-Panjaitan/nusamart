import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class Address(Base):
    __tablename__ = "addresses"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(50), nullable=False, default="Rumah")
    recipient_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    address_line: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    province: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(10), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user: Mapped["User"] = relationship(back_populates="addresses")

class Cart(Base):
    __tablename__ = "carts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    user: Mapped["User"] = relationship(back_populates="cart")
    items: Mapped[list["CartItem"]] = relationship(back_populates="cart", cascade="all, delete-orphan")

class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("cart_id", "variant_id", name="uq_cart_variant"), CheckConstraint("quantity > 0", name="ck_cart_item_quantity_positive"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cart_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("carts.id", ondelete="CASCADE"), index=True, nullable=False)
    variant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    cart: Mapped["Cart"] = relationship(back_populates="items")
    variant: Mapped["ProductVariant"] = relationship()

class WishlistItem(Base):
    __tablename__ = "wishlist_items"
    __table_args__ = (UniqueConstraint("user_id", "variant_id", name="uq_wishlist_user_variant"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    variant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    variant: Mapped["ProductVariant"] = relationship()

class Coupon(Base):
    __tablename__ = "coupons"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False, default="percent")
    discount_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    minimum_subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (UniqueConstraint("user_id", "idempotency_key", name="uq_order_user_idempotency_key"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending_payment", index=True)
    payment_status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    shipping_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    coupon_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    shipping_method: Mapped[str] = mapped_column(String(40), nullable=False, default="regular")
    shipping_address_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    tracking_number: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False)
    variant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=False)
    product_name_snapshot: Mapped[str] = mapped_column(String(180), nullable=False)
    sku_snapshot: Mapped[str] = mapped_column(String(80), nullable=False)
    image_url_snapshot: Mapped[str] = mapped_column(String(500), nullable=False)
    attributes_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    order: Mapped["Order"] = relationship(back_populates="items")

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="mock")
    provider_reference: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    order: Mapped["Order"] = relationship(back_populates="payments")

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    variant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="RESTRICT"), index=True, nullable=False)
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    movement_type: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_review_user_product"), CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating_range"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
