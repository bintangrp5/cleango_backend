from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from app.config import get_supabase, get_supabase_admin
from app.dependencies import require_admin

router = APIRouter(prefix="/api/v1/services", tags=["Services (Layanan Laundry)"])

@router.get("", response_model=List[ServiceResponse])
async def get_all_services(active_only: bool = True):
    """
    Mengambil daftar semua layanan laundry (misal: Cuci Reguler, Express, Dry Clean).
    Bisa diakses umum (tanpa autentikasi) untuk ditampilkan di beranda aplikasi mobile.
    """
    supabase = get_supabase()
    query = supabase.table("services").select("*")
    if active_only:
        query = query.eq("is_active", True)
    
    response = query.order("price_per_kg").execute()
    return response.data

@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service_by_id(service_id: str):
    """Mengambil detail satu layanan laundry berdasarkan ID."""
    supabase = get_supabase()
    response = supabase.table("services").select("*").eq("id", service_id).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layanan tidak ditemukan")
    return response.data[0]

@router.post("", response_model=ServiceResponse, dependencies=[Depends(require_admin)])
async def create_service(service: ServiceCreate):
    """[Admin Only] Menambahkan layanan laundry baru."""
    supabase = get_supabase_admin()
    response = supabase.table("services").insert(service.model_dump()).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gagal membuat layanan")
    return response.data[0]

@router.put("/{service_id}", response_model=ServiceResponse, dependencies=[Depends(require_admin)])
async def update_service(service_id: str, service: ServiceUpdate):
    """[Admin Only] Mengubah data layanan laundry (harga, nama, durasi, status aktif)."""
    supabase = get_supabase_admin()
    update_data = {k: v for k, v in service.model_dump().items() if v is not None}
    response = supabase.table("services").update(update_data).eq("id", service_id).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layanan tidak ditemukan atau gagal diupdate")
    return response.data[0]

@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def delete_service(service_id: str):
    """[Admin Only] Menghapus atau menonaktifkan layanan."""
    supabase = get_supabase_admin()
    supabase.table("services").delete().eq("id", service_id).execute()
    return None
