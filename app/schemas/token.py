# app/schemas/token.py
from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None


class TokenPayload(BaseModel):
    sub: Optional[str] = None