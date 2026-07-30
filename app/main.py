from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers import services, orders, profiles

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="RESTful API Backend untuk aplikasi mobile CleanGo (Customer & Admin di Flutter dengan GetX, Database Supabase PostgreSQL).",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup CORS (Mengizinkan koneksi dari emulator Android, perangkat fisik, atau web)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dalam produksi, ganti dengan domain/IP khusus
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(services.router)
app.include_router(orders.router)
app.include_router(profiles.router)

@app.get("/", tags=["Health Check"])
async def root():
    return {
        "status": "online",
        "app": settings.app_name,
        "message": "Selamat datang di API CleanGo! Buka /docs untuk melihat spesifikasi Swagger UI."
    }

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "ok", "database": "supabase"}
