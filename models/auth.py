# models/auth.py
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from config import settings
import hashlib

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class User(BaseModel):
    id: int
    email: str
    name: str
    role: str

class TokenData(BaseModel):
    email: Optional[str] = None

def simple_hash(password: str) -> str:
    """Simple hash for POC - DON'T use in production"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using simple hash"""
    return simple_hash(plain_password) == hashed_password

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(seconds=settings.jwt_expiration)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        if email is None:
            return None
        return {"email": email}
    except JWTError:
        return None

# Función para ser usada desde routers
async def authenticate_user(db, email: str, password: str) -> Optional[dict]:
    from database.operations import UserOperations
    user = await UserOperations.get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role
    }

async def get_current_user(token, db):
    from fastapi import HTTPException
    from database.operations import UserOperations
    
    user_data = verify_token(token.credentials)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await UserOperations.get_user_by_email(db, user_data["email"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role
    }