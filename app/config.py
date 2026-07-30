import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from supabase import create_client, Client

class Settings(BaseSettings):
    app_name: str = "CleanGo Backend API"
    debug: bool = True
    port: int = 8000
    
    # Supabase credentials
    supabase_url: str = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
    supabase_key: str = os.getenv("SUPABASE_KEY", "your-anon-key")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "your-service-role-key")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()

def get_supabase() -> Client:
    """Mengembalikan instance Supabase client standar (Anon Key)."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_key)

def get_supabase_admin() -> Client:
    """Mengembalikan instance Supabase client dengan Service Role Key (Hak akses admin / bypass RLS)."""
    settings = get_settings()
    key = settings.supabase_service_role_key if settings.supabase_service_role_key != "your-service-role-key" else settings.supabase_key
    return create_client(settings.supabase_url, key)
