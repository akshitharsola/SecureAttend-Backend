# app/models/attendance.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("session.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("user.id"), nullable=False)
    marked_at = Column(DateTime, default=datetime.utcnow)
    verification_factors = Column(JSON, nullable=True)  # Store verification factors
    
    # Relationships
    session = relationship("Session", back_populates="attendances")
    student = relationship("User", back_populates="attendances")