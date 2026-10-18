import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.catalog import Product, ProductVariant
from app.models.commerce import Address, Cart, CartItem, WishlistItem
from app.schemas.commerce import AddressCreate, CartItemCreate, CartItemUpdate
router = APIRouter()

def ensure_cart(db: Session, user: User) -> Cart:
    cart = db.scalar(select(Cart).options(selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.product)).where(Cart.user_id == user.id))
    if cart is None:
        cart = Cart(user_id=user.id); db.add(cart); db.commit(); db.refresh(cart)
    return cart

def cart_payload(cart: Cart):
    items = []
    subtotal = 0
    for item in cart.items:
        v = item.variant; p = v.product
        line = v.price * item.quantity; subtotal += line
        items.append({"id": item.id, "variant_id": v.id, "quantity": item.quantity,
                      "sku": v.sku, "attributes": v.attributes, "price": v.price,
                      "stock_available": v.stock_available, "product": {"id": p.id, "name": p.name,
                      "slug": p.slug, "image_url": p.image_url, "status": p.status}, "line_total": line})
    return {"id": cart.id, "items": items, "item_count": sum(x["quantity"] for x in items), "subtotal": subtotal}

@router.get("/addresses")
def list_addresses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Address).where(Address.user_id == user.id).order_by(Address.is_default.desc(), Address.created_at.desc())).all()
    return rows

@router.post("/addresses", status_code=201)
def create_address(payload: AddressCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    count = db.scalar(select(Address.id).where(Address.user_id == user.id).limit(1))
    address = Address(user_id=user.id, **payload.model_dump())
    if payload.is_default or not count:
        db.query(Address).filter(Address.user_id == user.id).update({Address.is_default: False})
        address.is_default = True
    db.add(address); db.commit(); db.refresh(address); return address

@router.delete("/addresses/{address_id}", status_code=204)
def delete_address(address_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    address = db.scalar(select(Address).where(Address.id == address_id, Address.user_id == user.id))
    if not address: raise HTTPException(404, "Alamat tidak ditemukan")
    db.delete(address); db.commit(); return None

@router.get("/cart")
def get_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return cart_payload(ensure_cart(db, user))

@router.post("/cart/items", status_code=201)
def add_cart_item(payload: CartItemCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    variant = db.scalar(select(ProductVariant).options(selectinload(ProductVariant.product)).where(ProductVariant.id == payload.variant_id, ProductVariant.is_active.is_(True)))
    if not variant or variant.product.status != "active": raise HTTPException(404, "Varian produk tidak ditemukan")
    if variant.stock_available < payload.quantity: raise HTTPException(409, f"Stok tersedia hanya {variant.stock_available}")
    cart = ensure_cart(db, user)
    item = db.scalar(select(CartItem).where(CartItem.cart_id == cart.id, CartItem.variant_id == variant.id))
    new_quantity = payload.quantity + (item.quantity if item else 0)
    if new_quantity > variant.stock_available: raise HTTPException(409, f"Jumlah melebihi stok tersedia ({variant.stock_available})")
    if item: item.quantity = new_quantity
    else: db.add(CartItem(cart_id=cart.id, variant_id=variant.id, quantity=payload.quantity))
    db.commit()
    return cart_payload(ensure_cart(db, user))

@router.patch("/cart/items/{item_id}")
def update_cart_item(item_id: uuid.UUID, payload: CartItemUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cart = ensure_cart(db, user)
    item = db.scalar(select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id))
    if not item: raise HTTPException(404, "Item keranjang tidak ditemukan")
    variant = db.get(ProductVariant, item.variant_id)
    if not variant or payload.quantity > variant.stock_available: raise HTTPException(409, "Jumlah melebihi stok yang tersedia")
    item.quantity = payload.quantity; db.commit(); return cart_payload(ensure_cart(db, user))

@router.delete("/cart/items/{item_id}", status_code=204)
def remove_cart_item(item_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cart = ensure_cart(db, user)
    item = db.scalar(select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id))
    if not item: raise HTTPException(404, "Item keranjang tidak ditemukan")
    db.delete(item); db.commit(); return None

@router.delete("/cart", status_code=204)
def clear_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cart = ensure_cart(db, user)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(); db.commit(); return None

@router.get("/wishlist")
def get_wishlist(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = db.scalars(select(WishlistItem).options(selectinload(WishlistItem.variant).selectinload(ProductVariant.product)).where(WishlistItem.user_id == user.id).order_by(WishlistItem.created_at.desc())).all()
    return [{"id": x.id, "variant_id": x.variant_id, "price": x.variant.price, "sku": x.variant.sku,
             "product": {"id": x.variant.product.id, "name": x.variant.product.name, "slug": x.variant.product.slug, "image_url": x.variant.product.image_url}} for x in items]

@router.post("/wishlist/{variant_id}", status_code=201)
def add_wishlist(variant_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    variant = db.get(ProductVariant, variant_id)
    if not variant: raise HTTPException(404, "Varian tidak ditemukan")
    item = db.scalar(select(WishlistItem).where(WishlistItem.user_id == user.id, WishlistItem.variant_id == variant_id))
    if not item: db.add(WishlistItem(user_id=user.id, variant_id=variant_id)); db.commit()
    return {"status": "saved"}

@router.delete("/wishlist/{variant_id}", status_code=204)
def delete_wishlist(variant_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.scalar(select(WishlistItem).where(WishlistItem.user_id == user.id, WishlistItem.variant_id == variant_id))
    if item: db.delete(item); db.commit()
    return None
