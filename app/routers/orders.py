from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from app.database import get_db_connection
from app.deps import get_current_user, require_admin
import psycopg2.extras
import json
from decimal import Decimal

router = APIRouter(prefix="/api/v1/orders", tags=["Orders (Pemesanan & Tracking)"])

def fetch_order_with_items(cursor, order_id):
    cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    order = cursor.fetchone()
    if not order:
        return None
        
    cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
    items = cursor.fetchall()
    
    order['id'] = str(order['id'])
    order['user_id'] = str(order['user_id'])
    for item in items:
        item['id'] = str(item['id'])
        item['order_id'] = str(item['order_id'])
        if item.get('service_id'):
            item['service_id'] = str(item['service_id'])
            
    order['order_items'] = items
    return order

@router.post("", response_model=OrderResponse)
async def create_order(order: OrderCreate, current_user: dict = Depends(get_current_user)):
    """Membuat pesanan laundry baru dari aplikasi mobile Flutter."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # 1. Hitung total harga dan validasi layanan
        total_price = Decimal('0.0')
        items_to_insert = []
        
        for item in order.items:
            cursor.execute("SELECT * FROM services WHERE id = %s", (item.service_id,))
            service = cursor.fetchone()
            
            if not service:
                raise HTTPException(status_code=400, detail=f"Layanan ID {item.service_id} tidak valid.")
            
            subtotal = service["price_per_kg"] * Decimal(str(item.weight_kg))
            total_price += subtotal
            
            items_to_insert.append({
                "service_id": str(item.service_id),
                "service_name": service["name"],
                "price_per_kg": service["price_per_kg"],
                "weight_kg": Decimal(str(item.weight_kg)),
                "subtotal": subtotal
            })
            
        # 2. Insert data order utama
        cursor.execute(
            """INSERT INTO orders (user_id, customer_name, phone_number, address, latitude, longitude, total_price, status, payment_method, notes) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (current_user['id'], order.customer_name, order.phone_number, order.address, order.latitude, order.longitude, total_price, "Dijemput", order.payment_method, order.notes)
        )
        new_order_id = cursor.fetchone()['id']
        
        # 3. Insert order items
        for item in items_to_insert:
            cursor.execute(
                """INSERT INTO order_items (order_id, service_id, service_name, price_per_kg, weight_kg, subtotal)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (new_order_id, item['service_id'], item['service_name'], item['price_per_kg'], item['weight_kg'], item['subtotal'])
            )
            
        conn.commit()
        return fetch_order_with_items(cursor, new_order_id)
        
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.get("/user/{user_id}", response_model=List[OrderResponse])
async def get_user_orders(user_id: str, current_user: dict = Depends(get_current_user)):
    """Mengambil riwayat pesanan untuk satu user."""
    if str(current_user['id']) != user_id and current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Tidak diizinkan melihat pesanan orang lain")
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT id FROM orders WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
        order_rows = cursor.fetchall()
        
        orders = []
        for row in order_rows:
            orders.append(fetch_order_with_items(cursor, row['id']))
            
        return orders
    finally:
        cursor.close()
        conn.close()

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_detail(order_id: str, current_user: dict = Depends(get_current_user)):
    """Mengambil detail satu pesanan."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        order = fetch_order_with_items(cursor, order_id)
        
        if not order:
            raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan.")
            
        if order['user_id'] != str(current_user['id']) and current_user['role'] != 'admin':
             raise HTTPException(status_code=403, detail="Tidak diizinkan melihat pesanan ini")
             
        return order
    finally:
        cursor.close()
        conn.close()

@router.get("/admin/all", response_model=List[OrderResponse], dependencies=[Depends(require_admin)])
async def get_all_orders_for_admin():
    """[Admin Only] Mengambil SEMUA pesanan dari seluruh pelanggan."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT id FROM orders ORDER BY created_at DESC")
        order_rows = cursor.fetchall()
        
        orders = []
        for row in order_rows:
            orders.append(fetch_order_with_items(cursor, row['id']))
            
        return orders
    finally:
        cursor.close()
        conn.close()

@router.patch("/admin/{order_id}/status", response_model=OrderResponse, dependencies=[Depends(require_admin)])
async def update_order_status(order_id: str, status_update: OrderStatusUpdate):
    """[Admin Only] Mengubah status pesanan."""
    valid_statuses = ['Menunggu Penjemputan', 'Dijemput', 'Diproses', 'Diantar', 'Selesai', 'Dibatalkan']
    if status_update.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status tidak valid. Gunakan salah satu: {valid_statuses}")
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("UPDATE orders SET status = %s WHERE id = %s RETURNING id", (status_update.status, order_id))
        updated = cursor.fetchone()
        
        if not updated:
            raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan.")
            
        conn.commit()
        return fetch_order_with_items(cursor, order_id)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
