# app/models/__init__.py
# Import models in the correct order to avoid circular dependencies
from app.models.user import User, UserRole
from app.models.course import Course 
from app.models.room import Room
from app.models.session import Session, SessionStatus
from app.models.attendance import Attendance
from app.models.assignment import Assignment  # This line is important