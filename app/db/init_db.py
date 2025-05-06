# app/db/init_db.py
import uuid
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.core.config import settings
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)

# app/db/init_db.py
def init_db():
    """Initialize database with default data"""
    # Create a fresh session for initialization
    db = SessionLocal()
    try:
        # Check if admin exists first in a single query
        admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        
        if not admin:
            # Create admin user with string UUID
            admin_id = str(uuid.uuid4())
            logger.info(f"Creating admin user with ID: {admin_id}")
            
            admin = User(
                id=admin_id,
                email=settings.ADMIN_EMAIL,
                full_name="Admin User",
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                is_active=True
            )
            
            try:
                # Use a transaction to ensure atomic operation
                db.add(admin)
                db.commit()
                logger.info(f"Successfully created admin user with email {settings.ADMIN_EMAIL}")
            except IntegrityError as ie:
                # This might happen if another process created the user in parallel
                db.rollback()
                logger.warning(f"Admin user creation failed due to integrity error: {str(ie)}")
            except Exception as e:
                db.rollback()
                logger.error(f"Error in admin user creation transaction: {str(e)}", exc_info=True)
        else:
            logger.info(f"Admin user already exists with email {settings.ADMIN_EMAIL}")
    except Exception as e:
        logger.error(f"Error in init_db function: {str(e)}", exc_info=True)
    finally:
        db.close()
        logger.info("Closed database session after initialization")