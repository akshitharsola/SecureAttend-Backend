# app/services/course.py
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.course import Course
from app.schemas.course import CourseCreate, CourseUpdate

class CourseService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_course(self, course_id: str) -> Optional[Course]:
        """Get course by ID"""
        return self.db.query(Course).filter(Course.id == course_id).first()
    
    def get_course_by_code(self, course_code: str) -> Optional[Course]:
        """Get course by code"""
        return self.db.query(Course).filter(Course.course_code == course_code).first()
    
    def get_all_courses(self) -> List[Course]:
        """Get all courses"""
        return self.db.query(Course).all()
    
    def create_course(self, course_in: CourseCreate) -> Course:
        """Create new course"""
        # Check if course with this code already exists
        existing_course = self.get_course_by_code(course_in.course_code)
        if existing_course:
            raise ValueError(f"Course with code {course_in.course_code} already exists")
        
        # Create course ID
        course_id = str(uuid.uuid4())
        
        # Create course object
        db_course = Course(
            id=course_id,
            course_code=course_in.course_code,
            course_name=course_in.course_name,
            department=course_in.department,
            description=course_in.description
        )
        
        # Add to database
        self.db.add(db_course)
        self.db.commit()
        self.db.refresh(db_course)
        
        return db_course
    
    def update_course(self, course_id: str, course_in: CourseUpdate) -> Optional[Course]:
        """Update existing course"""
        # Get course
        db_course = self.get_course(course_id)
        if not db_course:
            return None
        
        # Update course data
        course_data = course_in.dict(exclude_unset=True)
        
        # Check if course_code is being updated and already exists
        if course_data.get("course_code") and course_data["course_code"] != db_course.course_code:
            existing_course = self.get_course_by_code(course_data["course_code"])
            if existing_course:
                raise ValueError(f"Course with code {course_data['course_code']} already exists")
        
        # Update fields
        for field, value in course_data.items():
            setattr(db_course, field, value)
        
        # Save changes
        self.db.commit()
        self.db.refresh(db_course)
        
        return db_course
    
    def delete_course(self, course_id: str) -> bool:
        """Delete course"""
        # Get course
        db_course = self.get_course(course_id)
        if not db_course:
            return False
        
        # Delete course
        self.db.delete(db_course)
        self.db.commit()
        
        return True