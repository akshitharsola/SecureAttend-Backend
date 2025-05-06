# app/schemas/user.py
from typing import Optional, List
from pydantic import BaseModel, EmailStr, UUID4
from app.models.user import UserRole


# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool = True
    department: Optional[str] = None
    roll_number: Optional[str] = None


# Properties to receive via API on creation
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole
    is_active: bool = True
    department: Optional[str] = None
    roll_number: Optional[str] = None


# Properties to receive via API on update
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    department: Optional[str] = None
    roll_number: Optional[str] = None


class UserInDBBase(UserBase):
    id: UUID4
    
    class Config:
        orm_mode = True


# Additional properties to return via API
class User(UserInDBBase):
    pass


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str


class UserList(BaseModel):
    users: List[User]