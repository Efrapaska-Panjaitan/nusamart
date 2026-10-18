from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models.user import User
from app.models.catalog import Category, Product, ProductVariant
from app.models.commerce import Cart, Coupon

CATEGORIES = [
    ("Elektronik", "elektronik", "Gadget, audio, dan kebutuhan digital."),
    ("Fashion", "fashion", "Pakaian dan aksesori sehari-hari."),
    ("Rumah & Dapur", "rumah-dapur", "Produk fungsional untuk rumah."),
    ("Kecantikan", "kecantikan", "Perawatan dan kebutuhan personal."),
    ("Olahraga", "olahraga", "Perlengkapan gaya hidup aktif."),
    ("Hobi & Lifestyle", "hobi-lifestyle", "Pilihan untuk aktivitas dan ruang favorit."),
]
PRODUCTS = [
    ("TWS NusaBuds Pro", "tws-nusabuds-pro", "elektronik", "Earbuds ringan dengan charging case dan suara seimbang.", "https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?auto=format&fit=crop&w=900&q=85", "NB-PRO-BLK", {"Warna":"Hitam"}, 249000, 28),
    ("Tas Ransel Urban Daily", "tas-ransel-urban", "fashion", "Ransel harian dengan banyak kompartemen dan desain minimal.", "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=85", "BAG-URB-BLK", {"Warna":"Hitam"}, 189000, 16),
    ("Sepatu Sneakers Nusa Classic", "sneakers-nusa-classic", "fashion", "Sneakers versatile dengan sol empuk untuk aktivitas sehari-hari.", "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=85", "SN-CLS-40", {"Ukuran":"40"}, 299000, 20),
    ("Tanaman Hias Monstera", "tanaman-monstera", "rumah-dapur", "Tanaman hias untuk menyegarkan sudut rumah atau meja kerja.", "https://images.unsplash.com/photo-1501004318641-b39e6451bec6?auto=format&fit=crop&w=900&q=85", "PLANT-MON-M", {"Ukuran":"Medium"}, 85000, 30),
    ("Lampu Meja LED Minimalis", "lampu-meja-led", "rumah-dapur", "Lampu meja modern dengan pencahayaan nyaman untuk belajar.", "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=900&q=85", "LAMP-LED-WHT", {"Warna":"Putih"}, 179000, 12),
    ("Headphone Wireless Studio", "headphone-wireless-studio", "elektronik", "Headphone nirkabel untuk musik, kelas online, dan kerja fokus.", "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=85", "HP-STU-BLK", {"Warna":"Hitam"}, 349000, 18),
    ("Botol Minum Active", "botol-minum-active", "olahraga", "Botol minum reusable untuk menemani aktivitas sepanjang hari.", "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=900&q=85", "BT-ACT-750", {"Kapasitas":"750 ml"}, 79000, 40),
    ("Serum Daily Glow", "serum-daily-glow", "kecantikan", "Serum perawatan harian dengan tekstur ringan.", "https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?auto=format&fit=crop&w=900&q=85", "SER-GLOW-30", {"Ukuran":"30 ml"}, 119000, 24),
    ("Keyboard Mechanical NusaType", "keyboard-mechanical-nusatype", "elektronik", "Keyboard compact untuk setup kerja dan gaming.", "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=900&q=85", "KB-NT-87", {"Layout":"87 keys"}, 329000, 14),
    ("Organizer Meja Minimal", "organizer-meja-minimal", "hobi-lifestyle", "Organizer desktop untuk menjaga ruang kerja tetap rapi.", "https://images.unsplash.com/photo-1494438639946-1ebd1d20bf85?auto=format&fit=crop&w=900&q=85", "ORG-MIN-NAT", {"Warna":"Natural"}, 99000, 22),
    ("Mouse Wireless Silent", "mouse-wireless-silent", "elektronik", "Mouse nirkabel ergonomis dengan klik senyap.", "https://images.unsplash.com/photo-1527814050087-3793815479db?auto=format&fit=crop&w=900&q=85", "MS-SIL-BLK", {"Warna":"Hitam"}, 129000, 31),
    ("Yoga Mat Essential", "yoga-mat-essential", "olahraga", "Matras yoga dengan permukaan anti-slip untuk latihan di rumah.", "https://images.unsplash.com/photo-1592432678016-e910b452f9a2?auto=format&fit=crop&w=900&q=85", "YG-MAT-GRN", {"Warna":"Hijau"}, 159000, 10),
]

def seed():
    Base.metadata.create_all(bind=engine)
    settings = get_settings()
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.email == settings.admin_email.lower()))
        if not admin:
            admin = User(email=settings.admin_email.lower(), full_name="NusaMart Admin", password_hash=hash_password(settings.admin_password), role="admin", is_active=True)
            db.add(admin); db.flush(); db.add(Cart(user_id=admin.id))
        cat_map = {}
        for name, slug, description in CATEGORIES:
            category = db.scalar(select(Category).where(Category.slug == slug))
            if not category:
                category = Category(name=name, slug=slug, description=description); db.add(category); db.flush()
            cat_map[slug] = category
        for name, slug, cat_slug, desc, image, sku, attrs, price, stock in PRODUCTS:
            product = db.scalar(select(Product).where(Product.slug == slug))
            if not product:
                product = Product(category_id=cat_map[cat_slug].id, name=name, slug=slug, description=desc, image_url=image, status="active")
                product.variants.append(ProductVariant(sku=sku, attributes=attrs, price=Decimal(price), stock_on_hand=stock, stock_reserved=0, is_active=True))
                db.add(product)
        coupon = db.scalar(select(Coupon).where(Coupon.code == "HEMAT10"))
        if not coupon: db.add(Coupon(code="HEMAT10", discount_type="percent", discount_value=Decimal("10"), minimum_subtotal=Decimal("100000"), is_active=True, max_uses=1000, used_count=0))
        db.commit()

if __name__ == "__main__": seed()
