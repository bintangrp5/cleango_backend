from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class OrderItemCreate(BaseModel):
    service_id: str
    weight_kg: float = Field(..., gt=0, description="Berat perkiraan / berat riil dalam kg")

class OrderItemResponse(BaseModel):
    id: str
    order_id: str
    service_id: Optional[str] = None
    service_name: str
    price_per_kg: float
    weight_kg: float
    subtotal: float
    created_at: datetime

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    user_id: str = Field(..., description="UUID dari pengguna (auth.uid)")
    customer_name: str = Field(..., description="Nama lengkap pelanggan saat checkout")
    phone_number: str = Field(..., description="Nomor telepon yang bisa dihubungi")
    address: str = Field(..., description="Alamat penjemputan laundry")
    
    # Integrasi GPS (sesuai PRD 4.5)
    latitude: float = Field(..., description="Latitude koordinat GPS saat ini")
    longitude: float = Field(..., description="Longitude koordinat GPS saat ini")
    
    payment_method: str = Field("COD (Bayar di Tempat)", description="Metode pembayaran")
    notes: Optional[str] = Field(None, description="Catatan tambahan untuk kurir/laundry")
    items: List[OrderItemCreate] = Field(..., min_length=1, description="Daftar layanan yang dipesan")

class OrderStatusUpdate(BaseModel):
    status: str = Field(..., description="Status baru pesanan: Menunggu Penjemputan, Dijemput, Diproses, Diantar, Selesai, Dibatalkan")

class OrderResponse(BaseModel):
    id: str
    order_number: str
    user_id: str
    customer_name: str
    phone_number: str
    address: str
    latitude: float
    longitude: float
    total_price: float
    status: str
    payment_method: Optional[str] = None
    payment_status: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    order_items: Optional[List[OrderItemResponse]] = None

    class Config:
        from_attributes = True
