# app/services/auth.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.models.user import User
from app.core.security import verify_password
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password"""
        try:
            # Use SQLAlchemy 1.4+ async style
            stmt = select(User).where(User.email == email)
            result = await self.db.execute(stmt)
            user = result.scalars().first()
            
            if not user:
                return None
            
            if not verify_password(password, user.hashed_password):
                return None
            
            return user
        except Exception as e:
            logger.error(f"Error in authenticate: {str(e)}")
            logger.exception("Full exception details:")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            stmt = select(User).where(User.email == email)
            result = await self.db.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error in get_user_by_email: {str(e)}")
            logger.exception("Full exception details:")
            raise