# tests/unit/test_attendance_service.py
import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.session import Session as SessionModel, SessionStatus
from app.models.attendance import Attendance
from app.services.attendance import AttendanceService

# Create a fixture for the database session
@pytest.fixture
def db():
    """Create a database session for testing"""
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test data setup
@pytest.fixture
def test_users(db):
    """Create test users - faculty and students"""
    # Generate unique IDs for this test run
    faculty_id = str(uuid.uuid4())
    student_ids = [str(uuid.uuid4()) for _ in range(3)]
    
    # Create a faculty user
    faculty = User(
        id=faculty_id,
        email=f"faculty_{faculty_id[:8]}@test.com",
        full_name="Test Faculty",
        hashed_password="hashed_password",
        role=UserRole.FACULTY,
        department="Computer Science",
        is_active=True
    )
    
    students = []
    for i, student_id in enumerate(student_ids):
        student = User(
            id=student_id,
            email=f"student_{student_id[:8]}@test.com",
            full_name=f"Test Student {i+1}",
            hashed_password="hashed_password",
            role=UserRole.STUDENT,
            roll_number=f"S2023{i+1:03d}",
            is_active=True
        )
        students.append(student)
    
    db.add(faculty)
    for student in students:
        db.add(student)
    db.commit()
    
    # Yield users and cleanup after test
    try:
        yield {"faculty": faculty, "students": students}
    finally:
        # Clean up test data
        for user in [faculty] + students:
            db.delete(user)
        db.commit()

@pytest.fixture
def test_session(db, test_users):
    """Create a test session"""
    faculty = test_users["faculty"]
    
    # Create session with a unique ID
    session_id = str(uuid.uuid4())
    session = SessionModel(
        id=session_id,
        faculty_id=faculty.id,
        course_code="CS101",
        room_number="R101",
        proximity_uuid="test-uuid-123",
        status=SessionStatus.ACTIVE,
        start_time=datetime.utcnow() - timedelta(hours=1)
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Yield session and cleanup after test
    try:
        yield session
    finally:
        db.delete(session)
        db.commit()

@pytest.fixture
def test_attendances(db, test_users, test_session):
    """Create test attendance records"""
    attendances = []
    for i, student in enumerate(test_users["students"]):
        # Create attendance with different verification factors
        verification_factors = {
            "qr": True,
            "face": True if i % 2 == 0 else False,
            "proximity": True if i % 3 == 0 else False
        }
        
        attendance = Attendance(
            id=str(uuid.uuid4()),
            session_id=test_session.id,
            student_id=student.id,
            marked_at=datetime.utcnow() - timedelta(minutes=30 * i),
            verification_factors=verification_factors
        )
        
        attendances.append(attendance)
    
    for attendance in attendances:
        db.add(attendance)
    db.commit()
    
    # Yield attendances and cleanup after test
    try:
        yield attendances
    finally:
        for attendance in attendances:
            db.delete(attendance)
        db.commit()

# Service tests
def test_get_student_attendance_history(db, test_users, test_attendances):
    """Test getting attendance history for a student"""
    # Get first student
    student = test_users["students"][0]
    
    # Create the service
    attendance_service = AttendanceService(db)
    
    # Get attendance history
    history = attendance_service.get_student_attendance_history(student.id)
    
    # Log history for debugging
    import logging
    logging.getLogger().info(f"Student attendance history: {history}")
    
    # Assertions
    assert len(history) > 0, "Should return at least one attendance record"
    
    # Check the structure of the history data
    record = history[0]
    assert "session_id" in record, "History should include session_id"
    assert "verification" in record, "Should have verification info"
def test_get_faculty_session_attendance(db, test_users, test_session, test_attendances):
    """Test getting attendance stats for faculty sessions"""
    # Get faculty
    faculty = test_users["faculty"]
    
    # Create the service
    attendance_service = AttendanceService(db)
    
    # Get sessions with attendance
    sessions = attendance_service.get_faculty_session_attendance(faculty.id)
    
    # Assertions
    assert len(sessions) > 0, "Should return at least one session"
    
    # Check the structure of the session data
    session = sessions[0]
    assert "course_code" in session, "Session should include course code"
    assert session["course_code"] == "CS101", "Course code should match"
    assert "attendances_count" in session, "Should have attendance count"
    assert "recent_attendances" in session, "Should have recent attendances"

def test_get_session_attendances_with_details(db, test_session, test_attendances):
    """Test getting detailed attendance for a session"""
    # Create the service
    attendance_service = AttendanceService(db)
    
    # Get detailed attendances
    attendances = attendance_service.get_session_attendances_with_details(test_session.id)
    
    # Assertions
    assert len(attendances) == len(test_attendances), "Should return all attendance records"
    
    # Check the structure of the attendance data
    attendance = attendances[0]
    assert "student_name" in attendance, "Should include student name"
    assert "student_email" in attendance, "Should include student email"
    assert "verification" in attendance, "Should have verification info"