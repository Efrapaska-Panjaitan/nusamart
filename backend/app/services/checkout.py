from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.models.catalog import ProductVariant
from app.models.commerce import Address, Cart, CartItem, Coupon, Order, OrderItem, InventoryMovement
from app.models.user import User
from app.services.serializers import order_payload

MONEY = Decimal("0.01")
def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)

def compute_totals(db: Session, user: User, coupon_code: str | None, shipping_method: str, items=None):
    cart = db.scalar(select(Cart).options(selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.product)).where(Cart.user_id == user.id))
    cart_items = items if items is not None else (cart.items if cart else [])
    if not cart_items: raise HTTPException(400, "Keranjang masih kosong")
    subtotal = Decimal("0.00")
    for item in cart_items:
        variant = item.variant if hasattr(item, "variant") else item["variant"]
        quantity = item.quantity if hasattr(item, "quantity") else item["quantity"]
        if not variant or not variant.is_active or variant.product.status != "active": raise HTTPException(409, "Ada produk yang tidak tersedia")
        if variant.stock_available < quantity: raise HTTPException(409, f"Stok {variant.product.name} tidak cukup")
        subtotal += Decimal(variant.price) * quantity
    discount = Decimal("0.00"); coupon = None
    if coupon_code:
        coupon = db.scalar(select(Coupon).where(Coupon.code == coupon_code.strip().upper()).with_for_update())
        if not coupon or not coupon.is_active: raise HTTPException(400, "Kode promo tidak valid")
        now = datetime.now(timezone.utc)
        if coupon.expires_at and coupon.expires_at < now: raise HTTPException(400, "Kode promo sudah kedaluwarsa")
        if coupon.max_uses is not None and coupon.used_count >= coupon.max_uses: raise HTTPException(400, "Kuota promo habis")
        if subtotal < Decimal(coupon.minimum_subtotal): raise HTTPException(400, "Subtotal belum memenuhi minimum promo")
        if coupon.discount_type == "percent": discount = subtotal * Decimal(coupon.discount_value) / Decimal("100")
        else: discount = Decimal(coupon.discount_value)
        discount = min(money(discount), subtotal)
    shipping = Decimal("15000.00") if shipping_method == "regular" else Decimal("30000.00")
    if subtotal >= Decimal("200000.00") and shipping_method == "regular": shipping = Decimal("0.00")
    total = max(Decimal("0.00"), subtotal - discount) + shipping
    return cart, money(subtotal), money(discount), money(shipping), money(total), coupon

def create_order(db: Session, user: User, address_id, coupon_code: str | None, shipping_method: str, idempotency_key: str | None = None):
    if idempotency_key:
        if len(idempotency_key) > 128:
            raise HTTPException(400, "Idempotency-Key maksimal 128 karakter")
        existing = db.scalar(select(Order).options(selectinload(Order.items)).where(Order.user_id == user.id, Order.idempotency_key == idempotency_key))
        if existing:
            return existing
    address = db.scalar(select(Address).where(Address.id == address_id, Address.user_id == user.id))
    if not address: raise HTTPException(404, "Alamat pengiriman tidak ditemukan")
    cart = db.scalar(select(Cart).options(selectinload(Cart.items)).where(Cart.user_id == user.id).with_for_update())
    if not cart or not cart.items: raise HTTPException(400, "Keranjang masih kosong")
    # Lock variants and validate all stock before mutating any of them.
    prepared = []
    for cart_item in cart.items:
        variant = db.scalar(select(ProductVariant).options(selectinload(ProductVariant.product)).where(ProductVariant.id == cart_item.variant_id).with_for_update())
        if not variant or not variant.is_active or variant.product.status != "active": raise HTTPException(409, "Ada produk yang tidak tersedia")
        if variant.stock_available < cart_item.quantity: raise HTTPException(409, f"Stok {variant.product.name} tidak cukup")
        prepared.append((cart_item, variant))
    _, subtotal, discount, shipping, total, coupon = compute_totals(db, user, coupon_code, shipping_method,
        items=[{"variant": v, "quantity": ci.quantity} for ci, v in prepared])
    address_snapshot = {"label": address.label, "recipient_name": address.recipient_name, "phone": address.phone,
        "address_line": address.address_line, "city": address.city, "province": address.province, "postal_code": address.postal_code}
    order = Order(order_number="NM-" + uuid4().hex[:12].upper(), user_id=user.id, status="pending_payment", payment_status="pending",
        subtotal=subtotal, discount_amount=discount, shipping_fee=shipping, total=total, coupon_code=coupon.code if coupon else None,
        shipping_method=shipping_method, shipping_address_snapshot=address_snapshot, idempotency_key=idempotency_key)
    db.add(order); db.flush()
    for cart_item, variant in prepared:
        variant.stock_reserved += cart_item.quantity
        db.add(InventoryMovement(variant_id=variant.id, order_id=order.id, movement_type="reserve", quantity=cart_item.quantity, note="Reservasi stok untuk order"))
        db.add(OrderItem(order_id=order.id, variant_id=variant.id, product_name_snapshot=variant.product.name,
            sku_snapshot=variant.sku, image_url_snapshot=variant.product.image_url, attributes_snapshot=variant.attributes,
            quantity=cart_item.quantity, unit_price=variant.price))
    if coupon: coupon.used_count += 1
    for cart_item in list(cart.items): db.delete(cart_item)
    db.commit()
    return db.scalar(select(Order).options(selectinload(Order.items)).where(Order.id == order.id))
