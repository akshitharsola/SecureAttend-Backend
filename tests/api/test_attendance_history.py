# tests/api/test_attendance_history.py
import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.session import Session as SessionModel, SessionStatus
from app.models.attendance import Attendance
from app.services.attendance import AttendanceService


# Test data setup
@pytest.fixture
def test_users(db: Session):
    """Create test users - faculty and students"""
    faculty = User(
        id=str(uuid.uuid4()),
        email="faculty@test.com",
        full_name="Test Faculty",
        hashed_password="hashed_password",  # This would normally be properly hashed
        role=UserRole.FACULTY,
        department="Computer Science",
        is_active=True
    )
    
    students = []
    for i in range(3):
        student = User(
            id=str(uuid.uuid4()),
            email=f"student{i+1}@test.com",
            full_name=f"Test Student {i+1}",
            hashed_password="hashed_password",  # This would normally be properly hashed
            role=UserRole.STUDENT,
            roll_number=f"S2023{i+1:03d}",
            is_active=True
        )
        students.append(student)
    
    db.add(faculty)
    for student in students:
        db.add(student)
    db.commit()
    
    for user in [faculty] + students:
        db.refresh(user)
    
    return {"faculty": faculty, "students": students}


@pytest.fixture
def test_session(db: Session, test_users):
    """Create a test session"""
    faculty = test_users["faculty"]
    
    session = SessionModel(
        id=str(uuid.uuid4()),
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
    
    return session


@pytest.fixture
def test_attendances(db: Session, test_users, test_session):
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
    
    for attendance in attendances:
        db.refresh(attendance)
    
    return attendances


# Service tests
def test_get_student_attendance_history(db: Session, test_users, test_attendances):
    """Test getting attendance history for a student"""
    # Get first student
    student = test_users["students"][0]
    
    # Create the service
    attendance_service = AttendanceService(db)
    
    # Get attendance history
    history = attendance_service.get_student_attendance_history(student.id)
    
    # Assertions
    assert len(history) > 0, "Should return at least one attendance record"
    
    # Check the structure of the history data
    record = history[0]
    assert "course_code" in record, "History should include course code"
    assert record["course_code"] == "CS101", "Course code should match"
    assert "verification" in record, "Should have verification info"
    assert "methods" in record["verification"], "Should have verification methods"
    assert "qr" in record["verification"], "Should indicate QR verification"
    assert "face" in record["verification"], "Should indicate face verification"
    assert "proximity" in record["verification"], "Should indicate proximity verification"


def test_get_faculty_session_attendance(db: Session, test_users, test_session, test_attendances):
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
    assert session["attendances_count"] == len(test_users["students"]), "Attendance count should match number of students"
    assert "recent_attendances" in session, "Should have recent attendances"
    assert len(session["recent_attendances"]) <= 5, "Should have up to 5 recent attendances"
    
    # Check recent attendance data
    recent = session["recent_attendances"][0]
    assert "student_name" in recent, "Should include student name"
    assert "student_roll" in recent, "Should include student roll number"
    assert "verification_methods" in recent, "Should have verification methods"


def test_get_session_attendances_with_details(db: Session, test_session, test_attendances):
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
    assert "student_roll" in attendance, "Should include student roll number"
    assert "verification" in attendance, "Should have verification info"
    assert "methods" in attendance["verification"], "Should have verification methods"


# API tests (will need API client fixture)
@pytest.mark.asyncio
async def test_get_attendance_history_api(client, test_users, test_attendances, token_headers):
    """Test the attendance history API endpoint"""
    # Get first student token headers
    student = test_users["students"][0]
    headers = token_headers(student)
    
    # Make API request
    response = await client.get("/api/v1/attendance/history", headers=headers)
    
    # Assertions
    assert response.status_code == 200, "Should return 200 OK"
    data = response.json()
    assert isinstance(data, list), "Should return a list"
    assert len(data) > 0, "Should return at least one attendance record"
    
    # Check data structure
    record = data[0]
    assert "course_code" in record, "Should include course code"
    assert "verification" in record, "Should include verification info"


@pytest.mark.asyncio
async def test_get_faculty_sessions_api(client, test_users, test_session, test_attendances, token_headers):
    """Test the faculty sessions API endpoint"""
    # Get faculty token headers
    faculty = test_users["faculty"]
    headers = token_headers(faculty)
    
    # Make API request
    response = await client.get("/api/v1/attendance/faculty/sessions", headers=headers)
    
    # Assertions
    assert response.status_code == 200, "Should return 200 OK"
    data = response.json()
    assert isinstance(data, list), "Should return a list"
    assert len(data) > 0, "Should return at least one session"
    
    # Check data structure
    session = data[0]
    assert "course_code" in session, "Should include course code"
    assert "attendances_count" in session, "Should include attendance count"
    assert "recent_attendances" in session, "Should include recent attendances"


@pytest.mark.asyncio
async def test_get_session_attendance_full_api(client, test_users, test_session, test_attendances, token_headers):
    """Test the full session attendance API endpoint"""
    # Get faculty token headers
    faculty = test_users["faculty"]
    headers = token_headers(faculty)
    
    # Make API request
    response = await client.get(f"/api/v1/attendance/session/{test_session.id}/full", headers=headers)
    
    # Assertions
    assert response.status_code == 200, "Should return 200 OK"
    data = response.json()
    assert isinstance(data, list), "Should return a list"
    assert len(data) == len(test_attendances), "Should return all attendance records"
    
    # Check data structure
    attendance = data[0]
    assert "student_name" in attendance, "Should include student name"
    assert "verification" in attendance, "Should include verification info"