import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer
from models.auth import get_current_user
from database.database import get_db

router = APIRouter()
security = HTTPBearer()
logger = structlog.get_logger()

@router.get("/")
async def get_library(
    token: HTTPBearer = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get user's personal library"""
    current_user = await get_current_user(token, db)
    
    return {
        "data": [],
        "meta": {"total": 0}
    }