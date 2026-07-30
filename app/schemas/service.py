from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ServiceBase(BaseModel):
    name: str = Field(..., description="Nama layanan laundry")
    description: Optional[str] = Field(None, description="Deskripsi layanan")
    price_per_kg: float = Field(..., gt=0, description="Harga per kilogram (IDR)")
    estimated_duration: str = Field(..., description="Estimasi waktu selesai (misal: 24 Jam)")
    image_url: Optional[str] = None
    is_active: bool = True

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price_per_kg: Optional[float] = Field(None, gt=0)
    estimated_duration: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

class ServiceResponse(ServiceBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
