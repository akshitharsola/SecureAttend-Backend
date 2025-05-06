# app/schemas/session.py
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, UUID4
from app.models.session import SessionStatus

class VerifySessionRequest(BaseModel):
    encrypted_data: str

# Shared properties
class SessionBase(BaseModel):
    faculty_id: UUID4
    course_code: str
    room_number: Optional[str] = None
    status: SessionStatus = SessionStatus.CREATED
    proximity_uuid: Optional[str] = None

# Properties to receive via API on creation
class SessionCreate(BaseModel):
    course_code: str
    room_number: Optional[str] = None

# Properties for QR code data
class QRCodeData(BaseModel):
    session_id: str
    faculty_id: str
    course_code: str
    room_number: str
    proximity_uuid: str
    timestamp: str
    expires_at: str

# Properties for QR code response
class QRCodeResponse(BaseModel):
    session_id: str
    encrypted_data: str
    image_url: str
    expires_at: str
    proximityUuid: Optional[str] = None  # Add this field to match what's being returned

class SessionInDBBase(SessionBase):
    id: UUID4
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# Additional properties to return via API
class Session(SessionInDBBase):
    pass

# Combined session and QR code response
class SessionResponse(BaseModel):
    session: Session
    qr_data: Optional[QRCodeResponse] = None

class SessionList(BaseModel):
    sessions: List[Session]