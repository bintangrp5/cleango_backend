import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    print(f"Menjalankan {settings.app_name} di port {settings.port}...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=settings.debug)
