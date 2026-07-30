-- ==========================================
-- SUPABASE POSTGRESQL SCHEMA FOR CLEANGO
-- ==========================================
-- PRD CleanGo - Aplikasi Mobile Laundry Online
-- ==========================================

-- Aktifkan ekstensi UUID (biasanya sudah aktif di Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- 1. TABEL PROFILES (Dihubungkan ke auth.users)
-- ==========================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    phone_number VARCHAR(50),
    address TEXT,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Komentar untuk dokumentasi
COMMENT ON TABLE public.profiles IS 'Menyimpan data profil pengguna dan role (user atau admin), terhubung otomatis ke auth.users Supabase.';

-- ==========================================
-- 2. TRIGGER AUTOMATIS: Buat Profile Saat User Register/Login OAuth
-- ==========================================
CREATE OR REPLACE FUNCTION public.handle_new_user() 
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name, email, avatar_url, role)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', 'Pelanggan CleanGo'),
        NEW.email,
        NEW.raw_user_meta_data->>'avatar_url',
        COALESCE(NEW.raw_user_meta_data->>'role', 'user')
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Hapus trigger jika sudah ada sebelumnya agar tidak duplikat
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


-- ==========================================
-- 3. TABEL SERVICES (Layanan Laundry)
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
-- 4. TABEL CART ITEMS (Keranjang Belanja)
-- ==========================================
CREATE TABLE IF NOT EXISTS public.cart_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    service_id UUID NOT NULL REFERENCES public.services(id) ON DELETE CASCADE,
    weight_kg NUMERIC(8, 2) NOT NULL DEFAULT 1.0, -- Perkiraan berat awal / berat minimal
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    UNIQUE(user_id, service_id) -- Mencegah duplikasi item layanan yang sama di keranjang
);

COMMENT ON TABLE public.cart_items IS 'Item pesanan sementara di keranjang belanja sebelum checkout.';


-- ==========================================
-- 5. TABEL ORDERS (Transaksi Pesanan)
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
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE RESTRICT,
    
    -- Data Pelanggan (Disimpan sebagai snapshot saat order)
    customer_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(50) NOT NULL,
    address TEXT NOT NULL,
    
    -- Integrasi GPS (Latitude & Longitude)
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    
    -- Status dan Keuangan
    total_price NUMERIC(12, 2) NOT NULL DEFAULT 0.0,
    status VARCHAR(50) NOT NULL DEFAULT 'Dijemput' CHECK (status IN ('Menunggu Penjemputan', 'Dijemput', 'Diproses', 'Diantar', 'Selesai', 'Dibatalkan')),
    payment_method VARCHAR(50) DEFAULT 'COD (Bayar di Tempat)',
    payment_status VARCHAR(50) DEFAULT 'Belum Dibayar' CHECK (payment_status IN ('Belum Dibayar', 'Sudah Dibayar')),
    
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

COMMENT ON TABLE public.orders IS 'Data utama transaksi pesanan laundry, termasuk koordinat GPS untuk penjemputan dan status tracking.';


-- ==========================================
-- 6. TABEL ORDER ITEMS (Detail Rincian Pesanan)
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
-- 7. FUNCTION & TRIGGER: Auto Update `updated_at`
-- ==========================================
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc'::text, NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_profiles_updated_at ON public.profiles;
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON public.profiles FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_services_updated_at ON public.services;
CREATE TRIGGER update_services_updated_at BEFORE UPDATE ON public.services FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_orders_updated_at ON public.orders;
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON public.orders FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();



-- ==========================================
-- 8. ROW LEVEL SECURITY (RLS) POLICIES
-- ==========================================
-- Aktifkan RLS di semua tabel
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.services ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cart_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_items ENABLE ROW LEVEL SECURITY;

-- --- POLICIES FOR PROFILES ---
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

DROP POLICY IF EXISTS "Admins can view all profiles" ON public.profiles;
CREATE POLICY "Admins can view all profiles" ON public.profiles
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
    );

-- --- POLICIES FOR SERVICES ---
DROP POLICY IF EXISTS "Anyone can view active services" ON public.services;
CREATE POLICY "Anyone can view active services" ON public.services
    FOR SELECT USING (is_active = true);

DROP POLICY IF EXISTS "Admins can manage services" ON public.services;
CREATE POLICY "Admins can manage services" ON public.services
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
    );

-- --- POLICIES FOR CART ITEMS ---
DROP POLICY IF EXISTS "Users can manage own cart" ON public.cart_items;
CREATE POLICY "Users can manage own cart" ON public.cart_items
    FOR ALL USING (auth.uid() = user_id);

-- --- POLICIES FOR ORDERS ---
DROP POLICY IF EXISTS "Users can view own orders" ON public.orders;
CREATE POLICY "Users can view own orders" ON public.orders
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own orders" ON public.orders;
CREATE POLICY "Users can create own orders" ON public.orders
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Admins can view and update all orders" ON public.orders;
CREATE POLICY "Admins can view and update all orders" ON public.orders
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
    );

-- --- POLICIES FOR ORDER ITEMS ---
DROP POLICY IF EXISTS "Users can view own order items" ON public.order_items;
CREATE POLICY "Users can view own order items" ON public.order_items
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM public.orders WHERE orders.id = order_items.order_id AND orders.user_id = auth.uid())
    );

DROP POLICY IF EXISTS "Users can insert order items for own order" ON public.order_items;
CREATE POLICY "Users can insert order items for own order" ON public.order_items
    FOR INSERT WITH CHECK (
        EXISTS (SELECT 1 FROM public.orders WHERE orders.id = order_items.order_id AND orders.user_id = auth.uid())
    );

DROP POLICY IF EXISTS "Admins can manage all order items" ON public.order_items;
CREATE POLICY "Admins can manage all order items" ON public.order_items
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
    );


-- ==========================================
-- 9. SEED DATA (DATA AWAL LAYANAN LAUNDRY)
-- ==========================================
INSERT INTO public.services (name, description, price_per_kg, estimated_duration, image_url)
VALUES
    ('Cuci Setrika Reguler', 'Layanan cuci bersih, wangi, dan setrika rapi. Cocok untuk pakaian sehari-hari.', 7000, '2 - 3 Hari', 'https://images.unsplash.com/photo-1545173168-9f1947eebb7f?q=80&w=600&auto=format&fit=crop'),
    ('Cuci Setrika Express', 'Layanan prioritas cepat selesai dalam 24 jam dengan hasil maksimal.', 12000, '24 Jam', 'https://images.unsplash.com/photo-1582735689369-4fe89db7114c?q=80&w=600&auto=format&fit=crop'),
    ('Cuci Kering (Dry Cleaning)', 'Perawatan khusus untuk jas, gaun, gaun pengantin, atau bahan sensitif lainnya.', 25000, '3 - 4 Hari', 'https://images.unsplash.com/photo-1517677208171-0bc6725a3e60?q=80&w=600&auto=format&fit=crop'),
    ('Setrika Saja', 'Layanan setrika rapi dan harum untuk pakaian yang sudah dicuci.', 5000, '1 - 2 Hari', 'https://images.unsplash.com/photo-1610557892470-55d9e80c0bce?q=80&w=600&auto=format&fit=crop'),
    ('Cuci Bedcover / Selimut', 'Pencucian mendalam untuk bedcover, selimut, sprei, dan handuk tebal.', 15000, '2 - 3 Hari', 'https://images.unsplash.com/photo-1635805737707-575885ab0820?q=80&w=600&auto=format&fit=crop')
ON CONFLICT DO NOTHING;
