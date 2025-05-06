# app/models/assignment.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Assignment(Base):
    __tablename__ = "assignments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    faculty_id = Column(String(36), ForeignKey("user.id"), nullable=False)
    course_id = Column(String(36), ForeignKey("courses.id"), nullable=False)
    room_id = Column(String(36), ForeignKey("rooms.id"), nullable=False)
    day_of_week = Column(String, nullable=True)  # For recurring schedules
    time_slot = Column(String, nullable=True)    # For recurring schedules
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    faculty = relationship("User", back_populates="assignments", foreign_keys=[faculty_id])
    course = relationship("Course", back_populates="assignments")
    room = relationship("Room", back_populates="assignments")