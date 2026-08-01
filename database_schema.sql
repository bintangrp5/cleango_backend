--
-- PostgreSQL database dump
--
-- Dumped from database version 15.4
-- Dumped by pg_dump version 15.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: neondb_owner
--
CREATE SCHEMA IF NOT EXISTS public;
ALTER SCHEMA public OWNER TO neondb_owner;

SET default_tablespace = '';
SET default_table_access_method = heap;

--
-- Table structure for table `services`
--
DROP TABLE IF EXISTS public.services CASCADE;
CREATE TABLE public.services (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    description TEXT, 
    price_per_kg NUMERIC(10, 2) NOT NULL, 
    estimated_duration VARCHAR(100) NOT NULL, 
    image_url TEXT, 
    is_active BOOLEAN DEFAULT true, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    category VARCHAR(50) DEFAULT 'Reguler'::character varying, 
    CONSTRAINT services_pkey PRIMARY KEY (id)
);
ALTER TABLE public.services OWNER TO neondb_owner;


--
-- Table structure for table `users`
--
DROP TABLE IF EXISTS public.users CASCADE;
CREATE TABLE public.users (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    full_name VARCHAR(255), 
    email VARCHAR(255) NOT NULL, 
    password_hash VARCHAR(255) NOT NULL, 
    phone_number VARCHAR(50), 
    address TEXT, 
    role VARCHAR(50) DEFAULT 'user'::character varying, 
    avatar_url TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    CONSTRAINT users_pkey PRIMARY KEY (id), 
    CONSTRAINT users_email_key UNIQUE (email), 
    CONSTRAINT users_role_check CHECK (role::text = ANY (ARRAY['user'::character varying, 'admin'::character varying]::text[]))
);
ALTER TABLE public.users OWNER TO neondb_owner;


--
-- Table structure for table `cart_items`
--
DROP TABLE IF EXISTS public.cart_items CASCADE;
CREATE TABLE public.cart_items (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    user_id UUID NOT NULL, 
    service_id UUID NOT NULL, 
    weight_kg NUMERIC(8, 2) DEFAULT 1.0 NOT NULL, 
    notes TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    CONSTRAINT cart_items_pkey PRIMARY KEY (id), 
    CONSTRAINT cart_items_service_id_fkey FOREIGN KEY(service_id) REFERENCES public.services (id) ON DELETE CASCADE, 
    CONSTRAINT cart_items_user_id_fkey FOREIGN KEY(user_id) REFERENCES public.users (id) ON DELETE CASCADE, 
    CONSTRAINT cart_items_user_id_service_id_key UNIQUE (user_id, service_id)
);
ALTER TABLE public.cart_items OWNER TO neondb_owner;


--
-- Table structure for table `orders`
--
DROP TABLE IF EXISTS public.orders CASCADE;
CREATE TABLE public.orders (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    order_number VARCHAR(100) NOT NULL, 
    user_id UUID NOT NULL, 
    customer_name VARCHAR(255) NOT NULL, 
    phone_number VARCHAR(50) NOT NULL, 
    address TEXT NOT NULL, 
    latitude DOUBLE PRECISION NOT NULL, 
    longitude DOUBLE PRECISION NOT NULL, 
    total_price NUMERIC(12, 2) DEFAULT 0.0 NOT NULL, 
    status VARCHAR(50) DEFAULT 'Dijemput'::character varying NOT NULL, 
    payment_method VARCHAR(50) DEFAULT 'COD (Bayar di Tempat)'::character varying, 
    payment_status VARCHAR(50) DEFAULT 'Belum Dibayar'::character varying, 
    notes TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    CONSTRAINT orders_pkey PRIMARY KEY (id), 
    CONSTRAINT orders_user_id_fkey FOREIGN KEY(user_id) REFERENCES public.users (id) ON DELETE RESTRICT, 
    CONSTRAINT orders_order_number_key UNIQUE (order_number), 
    CONSTRAINT orders_payment_status_check CHECK (payment_status::text = ANY (ARRAY['Belum Dibayar'::character varying, 'Sudah Dibayar'::character varying]::text[])), 
    CONSTRAINT orders_status_check CHECK (status::text = ANY (ARRAY['Menunggu Penjemputan'::character varying, 'Dijemput'::character varying, 'Diproses'::character varying, 'Diantar'::character varying, 'Selesai'::character varying, 'Dibatalkan'::character varying]::text[]))
);
ALTER TABLE public.orders OWNER TO neondb_owner;


--
-- Table structure for table `order_items`
--
DROP TABLE IF EXISTS public.order_items CASCADE;
CREATE TABLE public.order_items (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    order_id UUID NOT NULL, 
    service_id UUID, 
    service_name VARCHAR(255) NOT NULL, 
    price_per_kg NUMERIC(10, 2) NOT NULL, 
    weight_kg NUMERIC(8, 2) NOT NULL, 
    subtotal NUMERIC(12, 2) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    CONSTRAINT order_items_pkey PRIMARY KEY (id), 
    CONSTRAINT order_items_order_id_fkey FOREIGN KEY(order_id) REFERENCES public.orders (id) ON DELETE CASCADE, 
    CONSTRAINT order_items_service_id_fkey FOREIGN KEY(service_id) REFERENCES public.services (id) ON DELETE SET NULL
);
ALTER TABLE public.order_items OWNER TO neondb_owner;

--
-- PostgreSQL database dump complete
--
