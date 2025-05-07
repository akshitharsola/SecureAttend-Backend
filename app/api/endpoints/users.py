# app/api/endpoints/users.py
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session  # Change from AsyncSession
import uuid
from app.db.session import get_db
from app.services.user import UserService
from app.schemas.user import User, UserCreate, UserUpdate, UserList
from app.models.user import UserRole

router = APIRouter()

@router.get("/{user_id}", response_model=User)
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db)
) -> Any:
    """Get user by ID"""
    user_service = UserService(db)
    user = user_service.get_user(str(user_id))  # Convert UUID to string
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.get("/me", response_model=User)
def get_user_me(
    db: Session = Depends(get_db)
) -> Any:
    """Get current user"""
    # For proof of concept, return a dummy admin user
    user_service = UserService(db)
    admin_users = user_service.get_users(UserRole.ADMIN)
    admin = admin_users[0]
    return admin

@router.get("/", response_model=UserList)
def get_users(
    role: UserRole = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> Any:
    """Get all users, optionally filtered by role"""
    user_service = UserService(db)
    users = user_service.get_users(role, skip, limit)
    return {"users": users}

@router.post("/", response_model=User)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """Create new user"""
    user_service = UserService(db)
    # Check if user with this email already exists
    user = user_service.get_user_by_email(user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    user = user_service.create_user(user_in)
    return user

@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: uuid.UUID,
    user_in: UserUpdate,
    db: Session = Depends(get_db)
) -> Any:
    """Update user"""
    user_service = UserService(db)
    user = user_service.update_user(str(user_id), user_in)  # Convert UUID to string
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.delete("/{user_id}", response_model=dict)
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db)
) -> Any:
    """Delete user"""
    user_service = UserService(db)
    result = user_service.delete_user(str(user_id))  # Convert UUID to string
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"success": True}

@router.put("/{user_id}/activate", response_model=User)
def activate_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db)
) -> Any:
    """Activate user"""
    user_service = UserService(db)
    user = user_service.activate_user(str(user_id))  # Convert UUID to string
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/{user_id}/deactivate", response_model=User)
def deactivate_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db)
) -> Any:
    """Deactivate user"""
    user_service = UserService(db)
    user = user_service.deactivate_user(str(user_id))  # Convert UUID to string
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user