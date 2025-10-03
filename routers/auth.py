import structlog
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from models.auth import LoginRequest, LoginResponse, authenticate_user, create_access_token, get_current_user
from database.database import get_db

router = APIRouter()
security = HTTPBearer()
logger = structlog.get_logger()

@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password"""
    logger.info("🔐 [AUTH] Login attempt", email=credentials.email)
    
    user = await authenticate_user(db, credentials.email, credentials.password)
    if not user:
        logger.warning("❌ [AUTH] Invalid credentials", email=credentials.email)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(data={"sub": user["email"], "role": user["role"]})
    
    logger.info("✅ [AUTH] Login successful", email=credentials.email, user_id=user["id"])
    
    return LoginResponse(
        access_token=token,
        user=user
    )