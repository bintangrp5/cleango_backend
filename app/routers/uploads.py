from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Request
import shutil
import os
from uuid import uuid4
from app.deps import require_admin
import pathlib

router = APIRouter(prefix="/api/v1/upload", tags=["Upload"])

UPLOAD_DIR = pathlib.Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("", dependencies=[Depends(require_admin)])
async def upload_image(request: Request, file: UploadFile = File(...)):
    """[Admin Only] Mengunggah gambar."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File harus berupa gambar.")
    
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid4().hex}.{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Gagal menyimpan gambar.")
    
    base_url = str(request.base_url)
    return {"image_url": f"{base_url}uploads/{unique_filename}"}
