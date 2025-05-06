# app/api/endpoints/sessions.py
from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from sqlalchemy.orm import Session
import uuid
import secrets
from app.db.session import get_db
from app.api.deps import get_current_faculty, get_current_active_user, get_current_student, get_current_user
from app.models.session import SessionStatus, Session as SessionModel
from app.models.user import UserRole
from app.schemas.user import User
from app.services.attendance import AttendanceService
from app.services.session import SessionService
from app.services.qr_code import QRCodeService
from app.schemas.session import (
    Session, SessionCreate, SessionResponse, SessionList, QRCodeResponse, VerifySessionRequest
)

from fastapi.concurrency import run_in_threadpool
import json
import logging
from app.api.deps import get_db, get_current_faculty, get_current_student
from app.schemas.session import SessionCreate, SessionResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=SessionList)
def get_sessions(
    faculty_id: uuid.UUID = None,
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get sessions, optionally filtered by faculty or status"""
    session_service = SessionService(db)
    
    if active_only:
        sessions = session_service.get_active_sessions(faculty_id)
    elif faculty_id:
        sessions = session_service.get_faculty_sessions(faculty_id)
    else:
        # If no filters, return faculty's own sessions
        sessions = session_service.get_faculty_sessions(current_user.id)
        
    return {"sessions": sessions}

@router.get("/my", response_model=SessionList)
def get_my_sessions(
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_faculty)
) -> Any:
    """Get current faculty's sessions"""
    session_service = SessionService(db)
    
    if active_only:
        sessions = session_service.get_active_sessions(current_user.id)
    else:
        sessions = session_service.get_faculty_sessions(current_user.id)
        
    return {"sessions": sessions}

@router.get("/{session_id}", response_model=Session)
def get_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get session by ID"""
    session_service = SessionService(db)
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session

# app/api/endpoints/sessions.py
@router.post("/create", response_model=SessionResponse)
def create_session(
    session_in: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_faculty)
) -> Any:
    """Create new attendance session"""
    try:
        # Create the session
        session_service = SessionService(db)
        qr_code_service = QRCodeService()
        
        # Generate a unique proximity UUID for BLE
        proximity_uuid = secrets.token_hex(4)  # 8 chars, 4 bytes
        
        # Create session (passing the user ID as string)
        session = session_service.create_session(
            faculty_id=current_user.id,
            course_code=session_in.course_code,
            room_number=session_in.room_number,
            proximity_uuid=proximity_uuid
        )
        
        # Automatically start the session
        session = session_service.start_session(session.id)
        
        # Generate QR code for session
        qr_data = qr_code_service.generate_session_qr(
            session_id=session.id,
            faculty_id=session.faculty_id,
            course_code=session.course_code,
            room_number=session.room_number,
            proximity_uuid=proximity_uuid
        )
        
        return {
            "session": session,
            "qr_data": qr_data
        }
    except Exception as e:
        # Add detailed logging for debugging
        print(f"Error creating session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )
    
# app/api/endpoints/sessions.py
@router.get("/{session_id}/qr", response_model=QRCodeResponse)
def get_session_qr(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Allow any authenticated user
) -> Any:
    """Get QR code for a session"""
    try:
        # Get session
        session_service = SessionService(db)
        qr_code_service = QRCodeService()
        
        # Convert string ID to UUID format if needed
        session = session_service.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        # Check permissions (faculty who created the session or student in the course)
        if current_user.role == UserRole.FACULTY and current_user.id != session.faculty_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this session"
            )
        
        # Generate or retrieve QR code
        qr_data = qr_code_service.generate_session_qr(
            session_id=session.id,
            faculty_id=session.faculty_id,
            course_code=session.course_code,
            room_number=session.room_number,
            proximity_uuid=session.proximity_uuid
        )
        
        return qr_data
    except Exception as e:
        # Add detailed logging
        print(f"Error getting QR code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get QR code: {str(e)}"
        )

@router.post("/{session_id}/start", response_model=Session)
def start_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_faculty)
) -> Any:
    """Start a session (change status to ACTIVE)"""
    # Verify the session exists and belongs to the faculty
    session_service = SessionService(db)
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    if session.faculty_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session"
        )
    
    # Start session
    session = session_service.start_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start session"
        )
    
    return session

@router.post("/{session_id}/end", response_model=Session)
def end_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_faculty)
) -> Any:
    """End a session (change status to ENDED)"""
    # Verify the session exists and belongs to the faculty
    session_service = SessionService(db)
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    if session.faculty_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session"
        )
    
    # End session
    session = session_service.end_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot end session"
        )
    
    return session
# app/api/endpoints/sessions.py

@router.post("/verify")
def verify_session(
    encrypted_data: VerifySessionRequest = Body(...),  # Use FastAPI's Body extraction
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
) -> Any:
    """Verify a session token from QR code"""
    try:
        print("\n===== REQUEST DEBUG INFO =====")
        print(f"Received request for session verification")
        print(f"encrypted_data: {encrypted_data.encrypted_data}")
        print(f"Type of encrypted_data: {type(encrypted_data.encrypted_data)}")
        print("==============================\n")
        
        if not encrypted_data or not encrypted_data.encrypted_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Missing required field: encrypted_data"
            )
        
        # Verify QR code data
        qr_code_service = QRCodeService()
        verification_result = qr_code_service.verify_qr_data(encrypted_data.encrypted_data)
        
        if not verification_result.get("valid"):
            print(f"Decryption error: \n{verification_result.get('error', 'Unknown error')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=verification_result.get("error", "Invalid QR code")
            )
        
        # Get session data from verification result
        session_data = verification_result.get("data")
        
        # Check if session exists and is active
        session_service = SessionService(db)
        session = session_service.get_session(session_data.get("session_id"))
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        if session.status != SessionStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session is not active (status: {session.status})"
            )
        
        # Return session information
        return {
            "valid": True,
            "session_id": str(session.id),
            "faculty_id": str(session.faculty_id),
            "course_code": session.course_code,
            "room_number": session.room_number,
            "proximity_uuid": session.proximity_uuid
        }
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing request: {str(e)}"
        )
    
# app/api/endpoints/sessions.py
@router.post("/{session_id}/refresh-qr", response_model=QRCodeResponse)
def refresh_session_qr(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_faculty)  # Only faculty can refresh
) -> Any:
    """Refresh QR code for a session (generate new one with updated expiry)"""
    try:
        # Get session
        session_service = SessionService(db)
        qr_code_service = QRCodeService()
        
        session = session_service.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        # Check permissions (only the faculty who created the session)
        if current_user.id != session.faculty_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to refresh this session's QR code"
            )
        
        # Refresh QR code
        qr_data = qr_code_service.refresh_session_qr(
            session_id=session.id,
            faculty_id=session.faculty_id,
            course_code=session.course_code,
            room_number=session.room_number,
            proximity_uuid=session.proximity_uuid
        )
        
        return qr_data
    except Exception as e:
        print(f"Error refreshing QR code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh QR code: {str(e)}"
        )
        
# Add this to app/api/endpoints/sessions.py
@router.get("/{session_id}/uuid")
def get_session_uuid(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Allow any authenticated user
) -> Any:
    """Get proximity UUID for a session"""
    try:
        # Get session
        session_service = SessionService(db)
        
        # Convert string ID to UUID format if needed
        session = session_service.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        # Check permissions (faculty who created the session or student in the course)
        if current_user.role == UserRole.FACULTY and current_user.id != session.faculty_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this session"
            )
        
        # Return the proximity UUID
        return {
            "session_id": str(session.id),
            "proximity_uuid": session.proximity_uuid
        }
    except Exception as e:
        # Add detailed logging
        print(f"Error getting session UUID: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session UUID: {str(e)}"
        )
        
# app/api/endpoints/sessions.py
# Add this endpoint if it doesn't already exist

@router.get("/{session_id}/info", response_model=Dict[str, Any])
def get_session_info(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get detailed information about a session"""
    session_service = SessionService(db)
    session = session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # For students, check if they have marked attendance for this session
    attendance_info = None
    if current_user.role == UserRole.STUDENT:
        attendance_service = AttendanceService(db)
        attendance = attendance_service.get_student_attendance_for_session(
            student_id=current_user.id,
            session_id=session_id
        )
        if attendance:
            attendance_info = {
                "marked_at": attendance.marked_at.isoformat(),
                "verification_factors": attendance.verification_factors
            }
    
    # Format date/time information
    start_time = session.start_time.isoformat() if session.start_time else None
    end_time = session.end_time.isoformat() if session.end_time else None
    
    # Get faculty info
    faculty_info = None
    if session.faculty_id:
        from app.models.user import User
        faculty = db.query(User).filter(User.id == session.faculty_id).first()
        if faculty:
            faculty_info = {
                "id": str(faculty.id),
                "name": faculty.full_name,
                "department": faculty.department
            }
    
    return {
        "id": str(session.id),
        "course_code": session.course_code,
        "room_number": session.room_number,
        "proximity_uuid": session.proximity_uuid,
        "status": session.status.value,
        "start_time": start_time,
        "end_time": end_time,
        "faculty": faculty_info,
        "student_attendance": attendance_info
    }