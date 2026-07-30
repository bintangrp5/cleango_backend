from fastapi import Header, HTTPException, status, Depends
from typing import Optional, Dict, Any
from app.config import get_supabase_admin

async def get_current_user_profile(user_id: Optional[str] = Header(None, alias="X-User-ID")) -> Dict[str, Any]:
    """
    Mengambil profil user dari Supabase berdasarkan Header X-User-ID atau Authorization.
    Untuk kemudahan navigasi mobile Flutter, kita bisa mengirim X-User-ID dari GetX service.
    """
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header X-User-ID tidak ditemukan. Silakan login terlebih dahulu."
        )
    
    supabase = get_supabase_admin()
    response = supabase.table("profiles").select("*").eq("id", user_id).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil user tidak ditemukan di database."
        )
    
    return response.data[0]

async def require_admin(profile: Dict[str, Any] = Depends(get_current_user_profile)) -> Dict[str, Any]:
    """
    Memastikan bahwa user yang mengakses endpoint memiliki role 'admin'.
    Sesuai PRD, admin dapat memantau pesanan dan mengupdate status pesanan.
    """
    if profile.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak. Endpoint ini hanya untuk role Admin."
        )
    return profile
