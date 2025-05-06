# app/schemas/course.py
from typing import Optional, List
from pydantic import BaseModel

# Base Course Schema (shared properties)
class CourseBase(BaseModel):
    course_code: str
    course_name: str
    department: Optional[str] = None
    description: Optional[str] = None

# Schema for creating a course
class CourseCreate(CourseBase):
    pass

# Schema for updating a course
class CourseUpdate(BaseModel):
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None

# Schema for course in response
class Course(CourseBase):
    id: str
    
    class Config:
        from_attributes = True  # Changed from orm_mode = True

# Schema for list of courses
class CourseList(BaseModel):
    courses: List[Course] = []