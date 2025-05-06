# app/db/base.py
# Import base class first
from app.db.base_class import Base

# Import models - removing association tables
from app.models.user import User
from app.models.course import Course
from app.models.room import Room
from app.models.session import Session
from app.models.attendance import Attendance
from app.models.assignment import Assignment  # Fixed import