# app/services/assignment.py
import uuid
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate

class AssignmentService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_assignment(self, assignment_id: str) -> Optional[Assignment]:
        """Get assignment by ID"""
        return self.db.query(Assignment).filter(Assignment.id == assignment_id).first()
    
    def get_all_assignments(self) -> List[Assignment]:
        """Get all assignments"""
        return self.db.query(Assignment).all()
    
    def get_faculty_assignments(self, faculty_id: str) -> List[Assignment]:
        """Get all assignments for a faculty member"""
        return self.db.query(Assignment).filter(Assignment.faculty_id == faculty_id).all()
    
    def create_assignment(self, assignment_in: AssignmentCreate) -> Assignment:
        """Create new assignment"""
        # Create assignment ID
        assignment_id = str(uuid.uuid4())
        
        # Create assignment object
        db_assignment = Assignment(
            id=assignment_id,
            faculty_id=assignment_in.faculty_id,
            course_id=assignment_in.course_id,
            room_id=assignment_in.room_id,
            day_of_week=assignment_in.day_of_week,
            time_slot=assignment_in.time_slot,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=None
        )
        
        # Add to database
        self.db.add(db_assignment)
        self.db.commit()
        self.db.refresh(db_assignment)
        
        return db_assignment
    
    def update_assignment(self, assignment_id: str, assignment_in: AssignmentUpdate) -> Optional[Assignment]:
        """Update existing assignment"""
        # Get assignment
        db_assignment = self.get_assignment(assignment_id)
        if not db_assignment:
            return None
        
        # Update assignment data
        assignment_data = assignment_in.dict(exclude_unset=True)
        
        # Update fields
        for field, value in assignment_data.items():
            setattr(db_assignment, field, value)
        
        # Update updated_at timestamp
        db_assignment.updated_at = datetime.utcnow()
        
        # Save changes
        self.db.commit()
        self.db.refresh(db_assignment)
        
        return db_assignment
    
    def delete_assignment(self, assignment_id: str) -> bool:
        """Delete assignment"""
        # Get assignment
        db_assignment = self.get_assignment(assignment_id)
        if not db_assignment:
            return False
        
        # Delete assignment
        self.db.delete(db_assignment)
        self.db.commit()
        
        return True