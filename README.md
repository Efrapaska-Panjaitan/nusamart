# NusaMart

NusaMart adalah aplikasi toko online berbasis web dengan sistem penjualan satu toko (*single-vendor e-commerce*). Aplikasi ini dikembangkan menggunakan Vue 3 dan TypeScript untuk frontend, serta FastAPI dan PostgreSQL untuk backend.

NusaMart menyediakan fitur pengelolaan katalog produk, keranjang belanja, checkout, pesanan, dan inventaris. Aplikasi juga dilengkapi dengan dashboard admin untuk mengelola produk, kategori, stok, dan pesanan.

## Teknologi yang Digunakan

- **Frontend:** Vue 3, TypeScript, Vite
- **Backend:** Python, FastAPI
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy 2
- **Migrasi database:** Alembic
- **Autentikasi:** JWT dan Argon2 untuk hashing password
- **Containerization:** Docker dan Docker Compose
- **API Documentation:** OpenAPI dan Swagger UI

## Persyaratan

Sebelum menjalankan aplikasi, pastikan perangkat telah memiliki:

- Docker Desktop atau Docker Engine dengan Docker Compose.
- Git untuk mengelola kode sumber, jika project diambil dari repositori Git.
- Node.js versi 20 atau lebih baru dan Python versi 3.12 atau lebih baru jika ingin menjalankan frontend dan backend tanpa Docker.

## Instalasi dan Menjalankan Aplikasi

### 1. Siapkan project

Buka terminal pada direktori utama NusaMart, yaitu direktori yang berisi file `compose.yaml` dan `.env.example`.

### 2. Buat file environment

Salin `.env.example` menjadi `.env`.

Pada Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Pada Linux atau macOS:

```bash
cp .env.example .env
```

Periksa konfigurasi pada file `.env`, terutama koneksi database dan secret key. Untuk penggunaan lokal, gunakan nilai yang sesuai dengan konfigurasi project.

### 3. Jalankan aplikasi

Jalankan perintah berikut dari direktori utama project:

```bash
docker compose up --build -d
```

Docker Compose akan membangun image yang diperlukan dan menjalankan layanan aplikasi.

### 4. Akses aplikasi

Setelah seluruh layanan berjalan, aplikasi dapat diakses melalui alamat berikut.

| Komponen | Alamat |
|---|---|
| Frontend | http://localhost:5173 |
| Dokumentasi API | http://localhost:8000/docs |
| Pemeriksaan kesehatan backend | http://localhost:8000/health |
| Pemeriksaan kesiapan database | http://localhost:8000/health/ready |

Migrasi database menggunakan Alembic dan pengisian data awal dijalankan melalui proses startup yang disediakan oleh project.

## Akun Pengujian

Untuk pengujian lokal, tersedia akun admin berikut:

- **Email:** `admin@nusamart.local`
- **Password:** `Admin1234!`

Pengguna juga dapat membuat akun pelanggan melalui halaman registrasi.

Kredensial tersebut hanya ditujukan untuk pengembangan lokal. Ganti password admin, `SECRET_KEY`, kredensial database, dan seluruh nilai rahasia sebelum aplikasi dibagikan atau di-deploy ke lingkungan publik.

## Fitur Aplikasi

### Pelanggan

- Registrasi dan login menggunakan email dan password.
- Melihat katalog produk, mencari produk, dan memfilter berdasarkan kategori.
- Mengurutkan dan menelusuri produk melalui pagination.
- Melihat detail produk dan memilih varian yang tersedia.
- Menambahkan produk ke keranjang belanja dan mengelola jumlahnya.
- Menyimpan produk ke wishlist.
- Mengelola alamat pengiriman.
- Memeriksa estimasi total belanja melalui checkout quote.
- Menggunakan kode kupon `HEMAT10` yang tersedia pada data awal.
- Menghitung biaya pengiriman berdasarkan aturan yang diterapkan aplikasi.
- Membuat pesanan dan menjalankan alur pembayaran simulasi.
- Membatalkan pesanan yang masih memenuhi ketentuan pembatalan.
- Melihat riwayat dan detail pesanan.

### Admin

- Melihat ringkasan data melalui dashboard.
- Menambah, melihat, mengubah, dan menghapus kategori serta produk sesuai aturan aplikasi.
- Mengelola informasi produk dan varian.
- Menyesuaikan stok dan mencatat perubahan inventaris.
- Melihat pesanan dan memperbarui status pemenuhannya.

### Backend

- Menyediakan REST API yang terdokumentasi melalui OpenAPI.
- Menggunakan JWT untuk autentikasi API.
- Melakukan hashing password menggunakan Argon2.
- Menyimpan data aplikasi dalam PostgreSQL.
- Menggunakan SQLAlchemy untuk interaksi dengan database.
- Mengelola perubahan skema database melalui Alembic.
- Menerapkan validasi data dan constraint database.
- Menyediakan pengujian otomatis untuk backend.

## Ringkasan Endpoint API

API aplikasi menggunakan prefix `/api/v1`.

| Fitur | Endpoint |
|---|---|
| Autentikasi | `/auth/register`, `/auth/login`, `/auth/me` |
| Katalog | `/products`, `/products/{slug}`, `/categories` |
| Keranjang | `/cart`, `/cart/items`, `/cart/items/{item_id}` |
| Wishlist | `/wishlist`, `/wishlist/{variant_id}` |
| Alamat | `/addresses`, `/addresses/{address_id}` |
| Checkout | `/checkout/quote` |
| Pesanan | `/orders`, `/orders/{order_id}` |
| Pembayaran | `/orders/{order_id}/pay` |
| Pembatalan pesanan | `/orders/{order_id}/cancel` |
| Dashboard admin | `/admin/dashboard` |
| Kategori admin | `/admin/categories` |
| Produk admin | `/admin/products` |
| Inventaris admin | `/admin/inventory` |
| Pesanan admin | `/admin/orders` |

Metode HTTP, parameter, format request, dan response setiap endpoint dapat dilihat melalui dokumentasi Swagger di `http://localhost:8000/docs` ketika backend berjalan.

## Pengujian

Pengujian backend dapat dijalankan menggunakan perintah:

```bash
docker compose exec backend pytest
```

Untuk melihat status migrasi database:

```bash
docker compose exec backend alembic current
```

Untuk memeriksa log backend:

```bash
docker compose logs -f backend
```

Untuk memeriksa log frontend:

```bash
docker compose logs -f frontend
```

Untuk menghentikan seluruh layanan:

```bash
docker compose down
```

Jika ingin menghapus volume database lokal beserta data di dalamnya, jalankan:

```bash
docker compose down -v
```

Perintah terakhir akan menghapus data yang tersimpan pada volume Docker terkait. Gunakan hanya ketika data tersebut memang tidak lagi diperlukan.

## Catatan Pengembangan

NusaMart merupakan project portofolio untuk menerapkan pengembangan aplikasi e-commerce dari sisi frontend, backend, dan database.

Pembayaran pada versi ini masih menggunakan simulasi dan tidak memproses transaksi uang sungguhan. Sebelum digunakan untuk transaksi nyata, aplikasi memerlukan integrasi payment gateway, validasi tanda tangan webhook, dan pengujian alur pembayaran secara menyeluruh.

Gambar produk menggunakan URL gambar. Fitur unggah gambar dan penyimpanan berkas ke object storage belum diimplementasikan.

Untuk penggunaan produksi, beberapa hal yang masih perlu dipertimbangkan antara lain rotasi dan pencabutan refresh token, pembatasan request, verifikasi email, pemulihan password, integrasi layanan pengiriman, pencatatan aktivitas yang terstruktur, pemantauan aplikasi, penyimpanan berkas, pencadangan database, dan pengujian keamanan.

Aplikasi ini belum dimaksudkan sebagai sistem perdagangan yang siap menangani transaksi produksi tanpa pengembangan dan pengujian lanjutan.
