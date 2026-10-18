import uuid
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.commerce import Order, Payment, OrderItem, InventoryMovement, Cart, CartItem
from app.models.catalog import ProductVariant
from app.schemas.commerce import CheckoutQuoteRequest, OrderCreate, ReviewCreate
from app.models.commerce import Address, Review, Coupon
from app.services.checkout import compute_totals, create_order
from app.services.serializers import order_payload
router = APIRouter()

@router.post("/checkout/quote")
def checkout_quote(payload: CheckoutQuoteRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cart, subtotal, discount, shipping, total, coupon = compute_totals(db, user, payload.coupon_code, payload.shipping_method)
    address = None
    if payload.address_id:
        address = db.scalar(select(Address).where(Address.id == payload.address_id, Address.user_id == user.id))
        if not address: raise HTTPException(404, "Alamat tidak ditemukan")
    return {"subtotal": subtotal, "discount_amount": discount, "shipping_fee": shipping, "total": total,
            "coupon_code": coupon.code if coupon else None, "shipping_method": payload.shipping_method}

@router.post("/orders", status_code=201)
def submit_order(payload: OrderCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    # A persisted per-user idempotency key makes safe client retries return the existing order.
    order = create_order(db, user, payload.address_id, payload.coupon_code, payload.shipping_method, idempotency_key)
    order = db.scalar(select(Order).options(selectinload(Order.items)).where(Order.id == order.id))
    return order_payload(order)

@router.get("/orders")
def list_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    orders = db.scalars(select(Order).options(selectinload(Order.items)).where(Order.user_id == user.id).order_by(Order.created_at.desc())).all()
    return [order_payload(o) for o in orders]

@router.get("/orders/{order_id}")
def get_order(order_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.scalar(select(Order).options(selectinload(Order.items)).where(Order.id == order_id, Order.user_id == user.id))
    if not order: raise HTTPException(404, "Pesanan tidak ditemukan")
    return order_payload(order)

@router.post("/orders/{order_id}/pay")
def pay_order_mock(order_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.scalar(select(Order).options(selectinload(Order.items)).where(Order.id == order_id, Order.user_id == user.id).with_for_update())
    if not order: raise HTTPException(404, "Pesanan tidak ditemukan")
    if order.payment_status == "paid": return {"message": "Pembayaran sudah dikonfirmasi", "order": order_payload(order)}
    if order.status != "pending_payment": raise HTTPException(409, "Pesanan tidak dalam status menunggu pembayaran")
    payment = Payment(order_id=order.id, provider="mock", provider_reference="MOCK-" + uuid4().hex.upper(), status="paid", amount=order.total)
    order.payment_status = "paid"; order.status = "processing"
    # Consume stock reservation only after mock payment is marked successful.
    for item in order.items:
        variant = db.scalar(select(ProductVariant).where(ProductVariant.id == item.variant_id).with_for_update())
        if variant is None or variant.stock_reserved < item.quantity or variant.stock_on_hand < item.quantity:
            db.rollback(); raise HTTPException(409, "Reservasi stok tidak konsisten")
        variant.stock_reserved -= item.quantity; variant.stock_on_hand -= item.quantity
        db.add(InventoryMovement(variant_id=variant.id, order_id=order.id, movement_type="sale", quantity=-item.quantity, note="Pembayaran terkonfirmasi (mock)"))
    db.add(payment); db.commit()
    order = db.scalar(select(Order).options(selectinload(Order.items)).where(Order.id == order.id))
    return {"message": "Pembayaran mock berhasil; tidak ada uang sungguhan yang ditagihkan", "order": order_payload(order)}

@router.post("/orders/{order_id}/cancel")
def cancel_order(order_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.scalar(select(Order).options(selectinload(Order.items)).where(Order.id == order_id, Order.user_id == user.id).with_for_update())
    if not order: raise HTTPException(404, "Pesanan tidak ditemukan")
    if order.status != "pending_payment": raise HTTPException(409, "Hanya pesanan yang menunggu pembayaran yang dapat dibatalkan")
    for item in order.items:
        variant = db.scalar(select(ProductVariant).where(ProductVariant.id == item.variant_id).with_for_update())
        if variant:
            variant.stock_reserved = max(0, variant.stock_reserved - item.quantity)
            db.add(InventoryMovement(variant_id=variant.id, order_id=order.id, movement_type="release", quantity=item.quantity, note="Order dibatalkan"))
    if order.coupon_code:
        coupon = db.scalar(select(Coupon).where(Coupon.code == order.coupon_code).with_for_update())
        if coupon and coupon.used_count > 0:
            coupon.used_count -= 1
    order.status = "cancelled"; order.payment_status = "cancelled"; db.commit()
    return {"message": "Pesanan dibatalkan", "order_id": order.id, "status": order.status}

@router.post("/products/{product_id}/reviews", status_code=201)
def create_review(product_id: uuid.UUID, payload: ReviewCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from app.models.catalog import Product
    product = db.get(Product, product_id)
    if not product or product.status != "active": raise HTTPException(404, "Produk tidak ditemukan")
    existing = db.scalar(select(Review).where(Review.user_id == user.id, Review.product_id == product_id))
    if existing: raise HTTPException(409, "Kamu sudah memberi ulasan untuk produk ini")
    # Reviews are limited to customers who have paid for the product.
    bought = db.scalar(select(OrderItem.id).join(Order).join(ProductVariant, ProductVariant.id == OrderItem.variant_id).where(
        Order.user_id == user.id, Order.payment_status == "paid", ProductVariant.product_id == product_id).limit(1))
    if not bought: raise HTTPException(403, "Ulasan hanya tersedia setelah pembelian terbayar")
    review = Review(user_id=user.id, product_id=product_id, rating=payload.rating, comment=payload.comment)
    db.add(review); db.commit(); db.refresh(review)
    return {"id": review.id, "rating": review.rating, "comment": review.comment, "created_at": review.created_at}
