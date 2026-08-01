from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional
from app.database import get_db_connection
from app.security import get_password_hash, verify_password, create_access_token
import psycopg2.extras

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserRegister):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Cek apakah email sudah terdaftar
        cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Email sudah terdaftar"
            )
            
        hashed_password = get_password_hash(user.password)
        
        cursor.execute(
            "INSERT INTO users (email, password_hash, full_name) VALUES (%s, %s, %s) RETURNING id",
            (user.email, hashed_password, user.full_name)
        )
        new_user = cursor.fetchone()
        conn.commit()
        
        return {"message": "Registrasi berhasil", "user_id": str(new_user['id'])}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/login")
def login(user: UserLogin):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("SELECT id, email, password_hash, full_name, role FROM users WHERE email = %s", (user.email,))
        db_user = cursor.fetchone()
        
        if not db_user or not verify_password(user.password, db_user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email atau password salah",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        access_token = create_access_token(subject=str(db_user['id']))
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(db_user['id']),
                "email": db_user['email'],
                "full_name": db_user['full_name'],
                "role": db_user['role']
            }
        }
    finally:
        cursor.close()
        conn.close()
