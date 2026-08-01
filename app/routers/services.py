from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from app.database import get_db_connection
from app.deps import require_admin
import psycopg2.extras

router = APIRouter(prefix="/api/v1/services", tags=["Services (Layanan Laundry)"])

@router.get("", response_model=List[ServiceResponse])
def get_all_services(active_only: bool = True):
    """Mengambil daftar semua layanan laundry (misal: Cuci Reguler, Express, Dry Clean)."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if active_only:
            cursor.execute("SELECT * FROM services WHERE is_active = true ORDER BY price_per_kg")
        else:
            cursor.execute("SELECT * FROM services ORDER BY price_per_kg")
            
        services = cursor.fetchall()
        for s in services:
            s['id'] = str(s['id'])
        return services
    finally:
        cursor.close()
        conn.close()

@router.get("/{service_id}", response_model=ServiceResponse)
def get_service_by_id(service_id: str):
    """Mengambil detail satu layanan laundry berdasarkan ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM services WHERE id = %s", (service_id,))
        service = cursor.fetchone()
        if not service:
            raise HTTPException(status_code=404, detail="Layanan tidak ditemukan")
        service['id'] = str(service['id'])
        return service
    finally:
        cursor.close()
        conn.close()

@router.post("", response_model=ServiceResponse, dependencies=[Depends(require_admin)])
def create_service(service: ServiceCreate):
    """[Admin Only] Menambahkan layanan laundry baru."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            "INSERT INTO services (name, description, price_per_kg, estimated_duration, category, image_url, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *",
            (service.name, service.description, service.price_per_kg, service.estimated_duration, service.category, service.image_url, service.is_active)
        )
        new_service = cursor.fetchone()
        conn.commit()
        new_service['id'] = str(new_service['id'])
        return new_service
    finally:
        cursor.close()
        conn.close()

@router.put("/{service_id}", response_model=ServiceResponse, dependencies=[Depends(require_admin)])
def update_service(service_id: str, service: ServiceUpdate):
    """[Admin Only] Mengubah data layanan laundry."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        update_data = {k: v for k, v in service.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="Tidak ada data yang diupdate")
            
        set_clause = ", ".join([f"{k} = %s" for k in update_data.keys()])
        values = list(update_data.values())
        values.append(service_id)
        
        cursor.execute(f"UPDATE services SET {set_clause} WHERE id = %s RETURNING *", values)
        updated_service = cursor.fetchone()
        conn.commit()
        
        if not updated_service:
            raise HTTPException(status_code=404, detail="Layanan tidak ditemukan")
        updated_service['id'] = str(updated_service['id'])
        return updated_service
    finally:
        cursor.close()
        conn.close()

@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_service(service_id: str):
    """[Admin Only] Menghapus atau menonaktifkan layanan."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM services WHERE id = %s", (service_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
