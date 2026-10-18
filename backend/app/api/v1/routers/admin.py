import uuid
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from app.api.dependencies import require_admin
from app.db.session import get_db
from app.models.user import User
from app.models.catalog import Category, Product, ProductVariant
from app.models.commerce import Order, OrderItem, InventoryMovement
from app.schemas.catalog import CategoryCreate, ProductCreate, ProductUpdate, StockAdjustment
from app.schemas.commerce import AdminOrderStatusUpdate
from app.services.serializers import product_payload, order_payload
router = APIRouter()

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    users = db.scalar(select(func.count(User.id))) or 0
    products = db.scalar(select(func.count(Product.id)).where(Product.status == "active")) or 0
    orders = db.scalar(select(func.count(Order.id))) or 0
    pending = db.scalar(select(func.count(Order.id)).where(Order.status == "pending_payment")) or 0
    revenue = db.scalar(select(func.coalesce(func.sum(Order.total), 0)).where(Order.payment_status == "paid")) or 0
    low_stock = db.scalar(select(func.count(ProductVariant.id)).where((ProductVariant.stock_on_hand - ProductVariant.stock_reserved) <= 5, ProductVariant.is_active.is_(True))) or 0
    latest = db.scalars(select(Order).options(selectinload(Order.items)).order_by(Order.created_at.desc()).limit(8)).all()
    return {"user_count": users, "active_product_count": products, "order_count": orders, "pending_order_count": pending,
            "paid_revenue": revenue, "low_stock_variant_count": low_stock, "latest_orders": [order_payload(o) for o in latest]}

@router.post("/categories", status_code=201)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    category = Category(name=payload.name.strip(), slug=payload.slug, description=payload.description)
    db.add(category)
    try: db.commit(); db.refresh(category)
    except IntegrityError as exc: db.rollback(); raise HTTPException(409, "Nama atau slug kategori sudah digunakan") from exc
    return category

@router.patch("/categories/{category_id}")
def update_category(category_id: uuid.UUID, payload: CategoryCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    category = db.get(Category, category_id)
    if not category: raise HTTPException(404, "Kategori tidak ditemukan")
    category.name = payload.name.strip(); category.slug = payload.slug; category.description = payload.description
    try: db.commit(); db.refresh(category)
    except IntegrityError as exc: db.rollback(); raise HTTPException(409, "Nama atau slug kategori sudah digunakan") from exc
    return category

@router.delete("/categories/{category_id}", status_code=204)
def deactivate_category(category_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    category = db.get(Category, category_id)
    if not category: raise HTTPException(404, "Kategori tidak ditemukan")
    category.is_active = False; db.commit(); return None

@router.get("/products")
def admin_products(search: str | None = None, page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db), _: User = Depends(require_admin)):
    stmt = select(Product).options(selectinload(Product.category), selectinload(Product.variants)).order_by(Product.created_at.desc())
    if search: stmt = stmt.where(Product.name.ilike(f"%{search.strip()}%"))
    rows = db.scalars(stmt).unique().all(); total = len(rows); rows = rows[(page-1)*page_size:page*page_size]
    return {"items": [product_payload(db, p) for p in rows], "pagination": {"page": page, "page_size": page_size, "total_items": total, "total_pages": (total+page_size-1)//page_size}}

@router.post("/products", status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    category = db.get(Category, payload.category_id)
    if not category or not category.is_active: raise HTTPException(400, "Kategori tidak valid")
    product = Product(category_id=payload.category_id, name=payload.name.strip(), slug=payload.slug,
                      description=payload.description, image_url=payload.image_url, status=payload.status)
    db.add(product)
    try:
        db.flush()
        for item in payload.variants:
            product.variants.append(ProductVariant(sku=item.sku, attributes=item.attributes, price=item.price, stock_on_hand=item.stock_quantity))
        db.commit(); db.refresh(product)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(409, "Slug produk atau SKU sudah digunakan") from exc
    product = db.scalar(select(Product).options(selectinload(Product.category), selectinload(Product.variants)).where(Product.id == product.id))
    return product_payload(db, product)

@router.patch("/products/{product_id}")
def update_product(product_id: uuid.UUID, payload: ProductUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    product = db.scalar(select(Product).options(selectinload(Product.category), selectinload(Product.variants)).where(Product.id == product_id))
    if not product: raise HTTPException(404, "Produk tidak ditemukan")
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "category_id" and value and not db.get(Category, value): raise HTTPException(400, "Kategori tidak ditemukan")
        setattr(product, field, value)
    try: db.commit(); db.refresh(product)
    except IntegrityError as exc: db.rollback(); raise HTTPException(409, "Slug produk sudah digunakan") from exc
    return product_payload(db, product)

@router.delete("/products/{product_id}", status_code=204)
def archive_product(product_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    product = db.get(Product, product_id)
    if not product: raise HTTPException(404, "Produk tidak ditemukan")
    product.status = "archived"; db.commit(); return None

@router.post("/inventory/adjust")
def adjust_stock(payload: StockAdjustment, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    variant = db.scalar(select(ProductVariant).where(ProductVariant.id == payload.variant_id).with_for_update())
    if not variant: raise HTTPException(404, "Varian tidak ditemukan")
    new_on_hand = variant.stock_on_hand + payload.delta
    if new_on_hand < variant.stock_reserved: raise HTTPException(409, "Stok fisik tidak boleh lebih rendah daripada stok yang direservasi")
    if new_on_hand < 0: raise HTTPException(409, "Stok tidak boleh negatif")
    variant.stock_on_hand = new_on_hand
    db.add(InventoryMovement(variant_id=variant.id, movement_type="adjustment", quantity=payload.delta, note=f"{payload.note} (admin {user.email})"))
    db.commit(); return {"variant_id": variant.id, "stock_on_hand": variant.stock_on_hand, "stock_reserved": variant.stock_reserved, "stock_available": variant.stock_available}

@router.get("/orders")
def admin_orders(status: str | None = None, page: int = Query(default=1, ge=1), page_size: int = Query(default=30, ge=1, le=100), db: Session = Depends(get_db), _: User = Depends(require_admin)):
    stmt = select(Order).options(selectinload(Order.items)).order_by(Order.created_at.desc())
    if status: stmt = stmt.where(Order.status == status)
    rows = db.scalars(stmt).unique().all(); total = len(rows); rows = rows[(page-1)*page_size:page*page_size]
    return {"items": [order_payload(o) for o in rows], "pagination": {"page": page, "page_size": page_size, "total_items": total, "total_pages": (total+page_size-1)//page_size}}

@router.patch("/orders/{order_id}/status")
def update_order_status(order_id: uuid.UUID, payload: AdminOrderStatusUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    order = db.scalar(select(Order).options(selectinload(Order.items)).where(Order.id == order_id).with_for_update())
    if not order: raise HTTPException(404, "Pesanan tidak ditemukan")
    allowed = {"processing": {"shipped", "cancelled"}, "shipped": {"delivered"}}
    if payload.status not in allowed.get(order.status, set()): raise HTTPException(409, f"Transisi status {order.status} ke {payload.status} tidak diizinkan")
    if payload.status == "cancelled" and order.payment_status == "paid": raise HTTPException(409, "Pesanan yang sudah dibayar tidak bisa dibatalkan lewat endpoint ini")
    order.status = payload.status
    if payload.tracking_number: order.tracking_number = payload.tracking_number
    db.commit(); return order_payload(order)
