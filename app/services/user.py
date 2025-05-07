# Step 3: Fix app/services/user.py to use synchronous methods
# app/services/user.py
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_users(self, role=None, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users, optionally filtered by role"""
        query = self.db.query(User)
        
        # Add filter by role if provided
        if role is not None:
            query = query.filter(User.role == role)
            
        return query.offset(skip).limit(limit).all()
    
    # app/services/user.py - Update the create_user method
    def create_user(self, user_in: UserCreate) -> User:
        """Create new user"""
        # Create user ID if not provided
        user_id = str(uuid.uuid4())
        
        # Create user object with a default is_active=True if not provided
        db_user = User(
            id=user_id,
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            role=user_in.role,
            is_active=getattr(user_in, 'is_active', True),  # Default to True if not provided
            department=user_in.department,
            roll_number=user_in.roll_number,
        )
        
        # Add to database
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def update_user(self, user_id: str, user_in: UserUpdate) -> Optional[User]:
        """Update existing user"""
        # Get user
        db_user = self.get_user(user_id)
        if not db_user:
            return None
        
        # Update user data
        user_data = user_in.dict(exclude_unset=True)
        
        # Hash password if provided
        if user_data.get("password"):
            user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
        
        # Update fields
        for field, value in user_data.items():
            setattr(db_user, field, value)
        
        # Save changes
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def delete_user(self, user_id: str) -> Optional[User]:
        """Delete user"""
        # Get user
        db_user = self.get_user(user_id)
        if not db_user:
            return None
        
        # Delete user
        self.db.delete(db_user)
        self.db.commit()
        
        return db_user
    
    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        # Get user by email
        user = self.get_user_by_email(email)
        if not user:
            return None
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def activate_user(self, user_id: str) -> Optional[User]:
        """Activate user"""
        # Get user
        db_user = self.get_user(user_id)
        if not db_user:
            return None
        
        # Activate user
        db_user.is_active = True
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def deactivate_user(self, user_id: str) -> Optional[User]:
        """Deactivate user"""
        # Get user
        db_user = self.get_user(user_id)
        if not db_user:
            return None
        
        # Deactivate user
        db_user.is_active = False
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user