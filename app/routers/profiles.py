from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.schemas.profile import ProfileUpdate, ProfileResponse
from app.deps import get_current_user, require_admin
from app.database import get_db_connection
import psycopg2.extras

router = APIRouter(prefix="/api/v1/profiles", tags=["Profiles (Data Pengguna)"])

@router.get("/me", response_model=ProfileResponse)
def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Mengambil data profil user yang sedang login saat ini berdasarkan Token."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT id, full_name, email, phone_number, address, role, avatar_url, created_at, updated_at FROM users WHERE id = %s", (current_user['id'],))
        profile = cursor.fetchone()
        if not profile:
            raise HTTPException(status_code=404, detail="Profil tidak ditemukan")
        profile['id'] = str(profile['id'])
        return profile
    finally:
        cursor.close()
        conn.close()

@router.get("/{user_id}", response_model=ProfileResponse)
def get_profile_by_id(user_id: str):
    """Mengambil profil user berdasarkan UUID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT id, full_name, email, phone_number, address, role, avatar_url, created_at, updated_at FROM users WHERE id = %s", (user_id,))
        profile = cursor.fetchone()
        if not profile:
            raise HTTPException(status_code=404, detail="Profil tidak ditemukan")
        profile['id'] = str(profile['id'])
        return profile
    finally:
        cursor.close()
        conn.close()

@router.put("/{user_id}", response_model=ProfileResponse)
def update_profile(user_id: str, profile_update: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    """Mengubah data diri (nama, no HP, alamat)."""
    if str(current_user['id']) != user_id and current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Tidak diizinkan mengubah profil orang lain")
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        update_data = {k: v for k, v in profile_update.model_dump().items() if v is not None}
        if not update_data:
             raise HTTPException(status_code=400, detail="Tidak ada data yang diupdate")
             
        set_clause = ", ".join([f"{k} = %s" for k in update_data.keys()])
        values = list(update_data.values())
        values.append(user_id)
        
        query = f"UPDATE users SET {set_clause} WHERE id = %s RETURNING id, full_name, email, phone_number, address, role, avatar_url, created_at, updated_at"
        
        cursor.execute(query, values)
        updated_profile = cursor.fetchone()
        conn.commit()
        
        if not updated_profile:
            raise HTTPException(status_code=404, detail="Profil tidak ditemukan")
            
        updated_profile['id'] = str(updated_profile['id'])
        return updated_profile
    finally:
        cursor.close()
        conn.close()

@router.get("", response_model=List[ProfileResponse], dependencies=[Depends(require_admin)])
def get_all_profiles():
    """[Admin Only] Mengambil daftar semua pelanggan dan admin CleanGo."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT id, full_name, email, phone_number, address, role, avatar_url, created_at, updated_at FROM users ORDER BY created_at DESC")
        profiles = cursor.fetchall()
        for p in profiles:
            p['id'] = str(p['id'])
        return profiles
    finally:
        cursor.close()
        conn.close()
