from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.schemas.profile import ProfileUpdate, ProfileResponse
from app.config import get_supabase_admin
from app.dependencies import require_admin, get_current_user_profile

router = APIRouter(prefix="/api/v1/profiles", tags=["Profiles (Data Pengguna)"])

@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(profile = Depends(get_current_user_profile)):
    """Mengambil data profil user yang sedang login saat ini berdasarkan X-User-ID."""
    return profile

@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile_by_id(user_id: str):
    """Mengambil profil user berdasarkan UUID."""
    supabase = get_supabase_admin()
    res = supabase.table("profiles").select("*").eq("id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profil tidak ditemukan")
    return res.data[0]

@router.put("/{user_id}", response_model=ProfileResponse)
async def update_profile(user_id: str, profile_update: ProfileUpdate):
    """Mengubah data diri (nama, no HP, alamat)."""
    supabase = get_supabase_admin()
    update_data = {k: v for k, v in profile_update.model_dump().items() if v is not None}
    res = supabase.table("profiles").update(update_data).eq("id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gagal mengupdate profil")
    return res.data[0]

@router.get("", response_model=List[ProfileResponse], dependencies=[Depends(require_admin)])
async def get_all_profiles():
    """[Admin Only] Mengambil daftar semua pelanggan dan admin CleanGo."""
    supabase = get_supabase_admin()
    res = supabase.table("profiles").select("*").order("created_at", desc=True).execute()
    return res.data
