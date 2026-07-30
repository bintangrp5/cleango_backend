from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from app.config import get_supabase_admin
from app.dependencies import require_admin, get_current_user_profile

router = APIRouter(prefix="/api/v1/orders", tags=["Orders (Pemesanan & Tracking)"])

@router.post("", response_model=OrderResponse)
async def create_order(order: OrderCreate):
    """
    Membuat pesanan laundry baru dari aplikasi mobile Flutter.
    Menerima data koordinat GPS (latitude & longitude), data diri, dan rincian layanan.
    """
    supabase = get_supabase_admin()
    
    # 1. Hitung total harga dan validasi layanan
    total_price = 0.0
    items_to_insert = []
    
    for item in order.items:
        service_res = supabase.table("services").select("*").eq("id", item.service_id).execute()
        if not service_res.data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Layanan ID {item.service_id} tidak valid.")
        
        service = service_res.data[0]
        subtotal = service["price_per_kg"] * item.weight_kg
        total_price += subtotal
        
        items_to_insert.append({
            "service_id": item.service_id,
            "service_name": service["name"],
            "price_per_kg": service["price_per_kg"],
            "weight_kg": item.weight_kg,
            "subtotal": subtotal
        })
    
    # 2. Insert data order utama
    order_data = {
        "user_id": order.user_id,
        "customer_name": order.customer_name,
        "phone_number": order.phone_number,
        "address": order.address,
        "latitude": order.latitude,
        "longitude": order.longitude,
        "total_price": total_price,
        "status": "Dijemput", # Sesuai alur PRD
        "payment_method": order.payment_method,
        "notes": order.notes
    }
    
    order_res = supabase.table("orders").insert(order_data).execute()
    if not order_res.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal menyimpan pesanan utama.")
    
    new_order = order_res.data[0]
    
    # 3. Insert order items
    for item_data in items_to_insert:
        item_data["order_id"] = new_order["id"]
    
    supabase.table("order_items").insert(items_to_insert).execute()
    
    # Return order dengan itemnya
    new_order["order_items"] = items_to_insert
    return new_order

@router.get("/user/{user_id}", response_model=List[OrderResponse])
async def get_user_orders(user_id: str):
    """Mengambil riwayat pesanan untuk satu user (dilengkapi detail item pesanan)."""
    supabase = get_supabase_admin()
    orders_res = supabase.table("orders").select("*, order_items(*)").eq("user_id", user_id).order("created_at", desc=True).execute()
    return orders_res.data

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_detail(order_id: str):
    """Mengambil detail satu pesanan beserta koordinat GPS dan rincian itemnya."""
    supabase = get_supabase_admin()
    order_res = supabase.table("orders").select("*, order_items(*)").eq("id", order_id).execute()
    if not order_res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pesanan tidak ditemukan.")
    return order_res.data[0]

# --- ENDPOINT KHUSUS ADMIN (diakses oleh Mobile App dengan akun ber-role Admin) ---

@router.get("/admin/all", response_model=List[OrderResponse], dependencies=[Depends(require_admin)])
async def get_all_orders_for_admin():
    """
    [Admin Only] Mengambil SEMUA pesanan dari seluruh pelanggan.
    Digunakan oleh Admin di aplikasi mobile Flutter untuk memantau pesanan masuk dan koordinat lokasi jemput.
    """
    supabase = get_supabase_admin()
    orders_res = supabase.table("orders").select("*, order_items(*)").order("created_at", desc=True).execute()
    return orders_res.data

@router.patch("/admin/{order_id}/status", response_model=OrderResponse, dependencies=[Depends(require_admin)])
async def update_order_status(order_id: str, status_update: OrderStatusUpdate):
    """
    [Admin Only] Mengubah status pesanan.
    Pilihan status sesuai PRD: 'Menunggu Penjemputan', 'Dijemput', 'Diproses', 'Diantar', 'Selesai', 'Dibatalkan'.
    """
    supabase = get_supabase_admin()
    valid_statuses = ['Menunggu Penjemputan', 'Dijemput', 'Diproses', 'Diantar', 'Selesai', 'Dibatalkan']
    if status_update.status not in valid_statuses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Status tidak valid. Gunakan salah satu: {valid_statuses}")
    
    update_res = supabase.table("orders").update({"status": status_update.status}).eq("id", order_id).select("*, order_items(*)").execute()
    if not update_res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pesanan tidak ditemukan.")
    return update_res.data[0]
