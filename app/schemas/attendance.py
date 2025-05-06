# app/schemas/attendance.py
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, UUID4
import uuid

# Shared properties
class AttendanceBase(BaseModel):
    session_id: UUID4
    student_id: UUID4
    marked_at: datetime
    verification_factors: Dict[str, bool]


# Properties to receive via API on creation
class AttendanceMark(BaseModel):
    session_id: UUID4
    verification_factors: Dict[str, bool]


class AttendanceInDBBase(AttendanceBase):
    id: UUID4
    
    class Config:
        orm_mode = True


# Additional properties to return via API
class Attendance(AttendanceInDBBase):
    pass

class AttendanceMarkWithQR(BaseModel):
    encrypted_qr_data: str
    verification_factors: Dict[str, bool]

class AttendanceList(BaseModel):
    attendances: List[Attendance]
    
class AttendanceCreate(BaseModel):
    session_id: str
    student_id: str
    verification_factors: Optional[Dict[str, bool]] = None
    
    class Config:
        from_attributes = True  # Previously orm_mode=True in Pydantic v1