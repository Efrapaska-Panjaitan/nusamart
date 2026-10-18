from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload
from app.db.session import get_db
from app.models.catalog import Category, Product, ProductVariant
from app.models.commerce import Review
from app.services.serializers import product_payload
router = APIRouter()

@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    rows = db.scalars(select(Category).where(Category.is_active.is_(True)).order_by(Category.name)).all()
    return [{"id": c.id, "name": c.name, "slug": c.slug, "description": c.description,
             "product_count": db.scalar(select(func.count(Product.id)).where(Product.category_id == c.id, Product.status == "active")) or 0} for c in rows]

@router.get("/products")
def list_products(search: str | None = None, category: str | None = None,
                 min_price: float | None = Query(default=None, ge=0), max_price: float | None = Query(default=None, ge=0),
                 sort: str = Query(default="popular", pattern=r"^(popular|newest|price_asc|price_desc|rating)$"),
                 page: int = Query(default=1, ge=1), page_size: int = Query(default=12, ge=1, le=48),
                 db: Session = Depends(get_db)):
    stmt = select(Product).options(selectinload(Product.category), selectinload(Product.variants)).where(Product.status == "active")
    if search and search.strip():
        like = f"%{search.strip()}%"
        stmt = stmt.where(or_(Product.name.ilike(like), Product.description.ilike(like), Product.slug.ilike(like)))
    if category:
        stmt = stmt.join(Category).where(Category.slug == category)
    products = db.scalars(stmt).unique().all()
    payloads = [product_payload(db, p) for p in products]
    if min_price is not None: payloads = [p for p in payloads if float(p["max_price"]) >= min_price]
    if max_price is not None: payloads = [p for p in payloads if float(p["min_price"]) <= max_price]
    if sort == "newest": payloads.sort(key=lambda p: next((x.created_at.timestamp() for x in products if x.id == p["id"]), 0), reverse=True)
    elif sort == "price_asc": payloads.sort(key=lambda p: float(p["min_price"]))
    elif sort == "price_desc": payloads.sort(key=lambda p: float(p["max_price"]), reverse=True)
    elif sort == "rating": payloads.sort(key=lambda p: (p["average_rating"], p["review_count"]), reverse=True)
    else: payloads.sort(key=lambda p: (p["review_count"], p["average_rating"]), reverse=True)
    total = len(payloads)
    start = (page - 1) * page_size
    items = payloads[start:start + page_size]
    return {"items": items, "pagination": {"page": page, "page_size": page_size, "total_items": total, "total_pages": (total + page_size - 1) // page_size}}

@router.get("/products/{slug}")
def product_detail(slug: str, db: Session = Depends(get_db)):
    product = db.scalar(select(Product).options(selectinload(Product.category), selectinload(Product.variants)).where(Product.slug == slug, Product.status == "active"))
    if not product: raise HTTPException(404, "Produk tidak ditemukan")
    data = product_payload(db, product)
    reviews = db.execute(select(Review, ).where(Review.product_id == product.id).order_by(Review.created_at.desc()).limit(10)).scalars().all()
    users = {r.user_id: db.get(__import__('app.models.user', fromlist=['User']).User, r.user_id) for r in reviews}
    data["reviews"] = [{"id": r.id, "rating": r.rating, "comment": r.comment, "created_at": r.created_at,
                        "customer_name": (users[r.user_id].full_name.split()[0] if users.get(r.user_id) else "Customer")} for r in reviews]
    return data
