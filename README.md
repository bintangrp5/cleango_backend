# CleanGo Backend API (FastAPI & Supabase)

Backend RESTful API untuk aplikasi mobile laundry online **CleanGo**. Dibuat menggunakan **FastAPI (Python)** dan terhubung ke **Supabase PostgreSQL**.

Sesuai arsitektur sistem:
- **Customer & Admin** akan mengakses sistem melalui aplikasi mobile **Flutter GetX**.
- Perbedaan hak akses ditentukan oleh kolom `role` ('user' atau 'admin') di tabel `profiles` Supabase.

---

## 🏗️ Struktur Folder (Clean Architecture)

```
cleango_web_backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # Entrypoint aplikasi & konfigurasi CORS
│   ├── config.py        # Pengaturan environment & inisialisasi Supabase client
│   ├── dependencies.py  # Autentikasi dan autorisasi role Admin
│   ├── schemas/         # Validasi Pydantic untuk Service, Order, Profile
│   └── routers/         # Endpoint API (Services, Orders, Profiles)
├── sql/
│   └── schema.sql       # Script migrasi database Supabase
├── requirements.txt     # Daftar dependency Python
├── .env.example         # Contoh environment variables
└── run.py               # Script untuk menjalankan server Uvicorn
```

---

## 🚀 Cara Instalasi & Menjalankan Backend

### 1. Buat Virtual Environment (Opsional namun direkomendasikan)
```bash
python -m venv venv
venv\Scripts\activate  # Untuk Windows
```

### 2. Install Dependency
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi Environment Variable
Salin file `.env.example` menjadi `.env` dan masukkan API Key Supabase Anda:
```bash
copy .env.example .env
```
Isi nilai di `.env`:
- `SUPABASE_URL`: URL dari project Supabase Anda.
- `SUPABASE_KEY`: `anon` / public key Supabase Anda.
- `SUPABASE_SERVICE_ROLE_KEY`: `service_role` key (agar FastAPI bisa mengelola order & profil untuk admin).

### 4. Jalankan Server
```bash
python run.py
```
Atau menggunakan perintah Uvicorn langsung:
```bash
uvicorn app.main:app --reload --port 8000
```

---

## 📖 Dokumentasi API (Swagger UI)
Setelah server berjalan, Anda bisa menguji seluruh endpoint API secara interaktif melalui browser dengan membuka:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📋 Daftar API Utama

| Method | Endpoint | Keterangan | Akses |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/services` | Mengambil daftar layanan laundry aktif | Umum / Customer |
| `POST` | `/api/v1/services` | Menambahkan layanan laundry baru | **Admin Only** |
| `POST` | `/api/v1/orders` | Membuat pesanan baru + koordinat GPS | Customer |
| `GET` | `/api/v1/orders/user/{id}`| Riwayat pesanan milik user tertentu | Customer |
| `GET` | `/api/v1/orders/admin/all`| Melihat seluruh pesanan masuk | **Admin Only** |
| `PATCH`| `/api/v1/orders/admin/{id}/status` | Update status (Dijemput, Diproses, Diantar, Selesai) | **Admin Only** |
| `GET` | `/api/v1/profiles/me` | Mengambil data profil sendiri | Authenticated |
