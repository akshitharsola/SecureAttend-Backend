# app/models/user.py
import uuid
from enum import Enum
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    FACULTY = "FACULTY"
    STUDENT = "STUDENT"

class User(Base):
    __tablename__ = "user"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(SQLEnum(UserRole), nullable=False)
    department = Column(String, nullable=True)  # For faculty
    roll_number = Column(String, nullable=True)  # For students
    
    # Relationships
    sessions = relationship("Session", back_populates="faculty")
    attendances = relationship("Attendance", back_populates="student")
    # Add the missing relationship
    assignments = relationship("Assignment", back_populates="faculty", foreign_keys="Assignment.faculty_id")