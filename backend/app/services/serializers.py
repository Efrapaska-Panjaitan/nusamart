from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from app.models.catalog import Category, Product, ProductVariant
from app.models.commerce import Review, Order, OrderItem

def product_payload(db: Session, product: Product) -> dict:
    variants = sorted(product.variants, key=lambda v: (str(v.attributes), v.sku))
    prices = [Decimal(v.price) for v in variants if v.is_active]
    review_avg, review_count = db.execute(select(func.avg(Review.rating), func.count(Review.id)).where(Review.product_id == product.id)).one()
    return {
        "id": product.id, "category_id": product.category_id,
        "category_name": product.category.name if product.category else "",
        "category_slug": product.category.slug if product.category else "",
        "name": product.name, "slug": product.slug, "description": product.description,
        "image_url": product.image_url, "status": product.status,
        "min_price": min(prices) if prices else Decimal("0"),
        "max_price": max(prices) if prices else Decimal("0"),
        "average_rating": round(float(review_avg or 0), 1), "review_count": int(review_count or 0),
        "in_stock": any(v.stock_on_hand - v.stock_reserved > 0 for v in variants if v.is_active),
        "variants": [{"id": v.id, "sku": v.sku, "attributes": v.attributes, "price": v.price,
                      "stock_quantity": v.stock_on_hand, "stock_available": v.stock_available, "is_active": v.is_active} for v in variants],
    }

def order_payload(order: Order) -> dict:
    return {
        "id": order.id, "order_number": order.order_number, "status": order.status,
        "payment_status": order.payment_status, "subtotal": order.subtotal,
        "discount_amount": order.discount_amount, "shipping_fee": order.shipping_fee,
        "total": order.total, "coupon_code": order.coupon_code,
        "shipping_method": order.shipping_method, "shipping_address": order.shipping_address_snapshot,
        "tracking_number": order.tracking_number, "created_at": order.created_at,
        "items": [{"id": item.id, "variant_id": item.variant_id, "product_name": item.product_name_snapshot,
                   "sku": item.sku_snapshot, "image_url": item.image_url_snapshot,
                   "attributes": item.attributes_snapshot, "quantity": item.quantity, "unit_price": item.unit_price,
                   "line_total": item.unit_price * item.quantity} for item in order.items],
    }
