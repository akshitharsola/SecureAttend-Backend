# app/schemas/assignment.py
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

# Base Assignment Schema
class AssignmentBase(BaseModel):
    faculty_id: str
    course_id: str
    room_id: str
    day_of_week: Optional[str] = None  # This will be a comma-separated list of days
    time_slot: Optional[str] = None

# Schema for creating an assignment
class AssignmentCreate(AssignmentBase):
    pass

# Schema for updating an assignment
class AssignmentUpdate(BaseModel):
    faculty_id: Optional[str] = None
    course_id: Optional[str] = None
    room_id: Optional[str] = None
    day_of_week: Optional[str] = None
    time_slot: Optional[str] = None
    is_active: Optional[bool] = None

# Schema for assignment in response
class Assignment(AssignmentBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Include related data
    faculty_name: Optional[str] = None
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    room_number: Optional[str] = None
    
    class Config:
        from_attributes = True

# Schema for list of assignments
class AssignmentList(BaseModel):
    assignments: List[Assignment] = []