# Step 2: Update app/api/deps.py to remove async/await
# app/api/deps.py
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import TokenPayload
from app.services.user import UserService

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

# Define these if they're not already in your file
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


# Now modify the get_current_user function
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Get the subject directly from the payload
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        # For debugging
        print(f"User ID from token: {user_id}")
        
        # Use user_id to retrieve the user
        user_service = UserService(db)
        user = user_service.get_user(user_id)
        
        if user is None:
            raise credentials_exception
        return user
    except (JWTError, ValidationError) as e:
        print(f"JWT error: {str(e)}")
        raise credentials_exception
    except Exception as e:
        print(f"Unexpected error in get_current_user: {str(e)}")
        raise credentials_exception
        
def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    # Check if user is admin
    if current_user.role.value != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def get_current_faculty(
    current_user: User = Depends(get_current_user),
) -> User:
    # Check if user is faculty
    if current_user.role.value != "FACULTY":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faculty access required"
        )
    return current_user

def get_current_student(
    current_user: User = Depends(get_current_user),
) -> User:
    # Check if user is student
    if current_user.role.value != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required"
        )
    return current_user