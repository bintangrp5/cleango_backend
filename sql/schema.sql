-- ==========================================
-- POSTGRESQL SCHEMA FOR CLEANGO (NEON DB)
-- ==========================================
-- PRD CleanGo - Aplikasi Mobile Laundry Online
-- ==========================================

-- Aktifkan ekstensi UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- 1. TABEL USERS (Pengganti Supabase Auth)
-- ==========================================
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone_number VARCHAR(50),
    address TEXT,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

COMMENT ON TABLE public.users IS 'Menyimpan data akun pengguna dan role (user atau admin).';


-- ==========================================
-- 2. TABEL SERVICES (Layanan Laundry)
-- ==========================================
CREATE TABLE IF NOT EXISTS public.services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price_per_kg NUMERIC(10, 2) NOT NULL,
    estimated_duration VARCHAR(100) NOT NULL, -- Contoh: "2-3 Hari", "24 Jam"
    image_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

COMMENT ON TABLE public.services IS 'Daftar layanan laundry beserta harga per kilogram dan estimasi waktu selesai.';


-- ==========================================
-- 3. TABEL CART ITEMS (Keranjang Belanja)
-- ==========================================
CREATE TABLE IF NOT EXISTS public.cart_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    service_id UUID NOT NULL REFERENCES public.services(id) ON DELETE CASCADE,
    weight_kg NUMERIC(8, 2) NOT NULL DEFAULT 1.0, -- Perkiraan berat awal / berat minimal
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    UNIQUE(user_id, service_id) -- Mencegah duplikasi item layanan yang sama di keranjang
);

COMMENT ON TABLE public.cart_items IS 'Item pesanan sementara di keranjang belanja sebelum checkout.';


-- ==========================================
-- 4. TABEL ORDERS (Transaksi Pesanan)
-- ==========================================
CREATE SEQUENCE IF NOT EXISTS order_number_seq START 1;

CREATE OR REPLACE FUNCTION generate_order_number()
RETURNS TEXT AS $$
BEGIN
    RETURN 'ORD-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(NEXTVAL('order_number_seq')::TEXT, 4, '0');
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS public.orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_number VARCHAR(100) UNIQUE NOT NULL DEFAULT generate_order_number(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE RESTRICT,
    
    -- Data Pelanggan (Disimpan sebagai snapshot saat order)
    customer_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(50) NOT NULL,
    address TEXT NOT NULL,
    
    -- Integrasi GPS (Latitude & Longitude)
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    
    -- Status dan Keuangan
    total_price NUMERIC(12, 2) NOT NULL DEFAULT 0.0,
    status VARCHAR(50) NOT NULL DEFAULT 'Dijemput' CHECK (status IN ('Menunggu Penjemputan', 'Dijemput', 'Diproses', 'Diantar', 'Selesai')),
    payment_method VARCHAR(50) DEFAULT 'COD (Bayar di Tempat)',
    payment_status VARCHAR(50) DEFAULT 'Belum Dibayar' CHECK (payment_status IN ('Belum Dibayar', 'Sudah Dibayar')),
    
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

COMMENT ON TABLE public.orders IS 'Data utama transaksi pesanan laundry, termasuk koordinat GPS untuk penjemputan dan status tracking.';


-- ==========================================
-- 5. TABEL ORDER ITEMS (Detail Rincian Pesanan)
-- ==========================================
CREATE TABLE IF NOT EXISTS public.order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES public.orders(id) ON DELETE CASCADE,
    service_id UUID REFERENCES public.services(id) ON DELETE SET NULL,
    
    -- Snapshot data layanan saat order dibuat
    service_name VARCHAR(255) NOT NULL,
    price_per_kg NUMERIC(10, 2) NOT NULL,
    weight_kg NUMERIC(8, 2) NOT NULL,
    subtotal NUMERIC(12, 2) NOT NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

COMMENT ON TABLE public.order_items IS 'Rincian layanan dan berat untuk setiap pesanan laundry.';


-- ==========================================
-- 6. FUNCTION & TRIGGER: Auto Update `updated_at`
-- ==========================================
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc'::text, NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_users_updated_at ON public.users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_services_updated_at ON public.services;
CREATE TRIGGER update_services_updated_at BEFORE UPDATE ON public.services FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_orders_updated_at ON public.orders;
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON public.orders FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


-- ==========================================
-- 7. SEED DATA (DATA AWAL LAYANAN LAUNDRY)
-- ==========================================
INSERT INTO public.services (name, description, price_per_kg, estimated_duration, image_url)
VALUES
    ('Cuci Setrika Reguler', 'Layanan cuci bersih, wangi, dan setrika rapi. Cocok untuk pakaian sehari-hari.', 7000, '2 - 3 Hari', 'https://images.unsplash.com/photo-1545173168-9f1947eebb7f?q=80&w=600&auto=format&fit=crop'),
    ('Cuci Setrika Express', 'Layanan prioritas cepat selesai dalam 24 jam dengan hasil maksimal.', 12000, '24 Jam', 'https://images.unsplash.com/photo-1582735689369-4fe89db7114c?q=80&w=600&auto=format&fit=crop'),
    ('Cuci Kering (Dry Cleaning)', 'Perawatan khusus untuk jas, gaun, gaun pengantin, atau bahan sensitif lainnya.', 25000, '3 - 4 Hari', 'https://images.unsplash.com/photo-1517677208171-0bc6725a3e60?q=80&w=600&auto=format&fit=crop'),
    ('Setrika Saja', 'Layanan setrika rapi dan harum untuk pakaian yang sudah dicuci.', 5000, '1 - 2 Hari', 'https://images.unsplash.com/photo-1610557892470-55d9e80c0bce?q=80&w=600&auto=format&fit=crop'),
    ('Cuci Bedcover / Selimut', 'Pencucian mendalam untuk bedcover, selimut, sprei, dan handuk tebal.', 15000, '2 - 3 Hari', 'https://images.unsplash.com/photo-1635805737707-575885ab0820?q=80&w=600&auto=format&fit=crop')
ON CONFLICT DO NOTHING;
