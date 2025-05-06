# app/api/endpoints/attendance.py
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from app.db.session import get_db
from app.api.deps import get_current_faculty, get_current_student, get_current_active_user
from app.schemas.session import Session
from app.models.session import Session
from app.services.attendance import AttendanceService
from app.services.session import SessionService
from app.models.user import User  # Import User model
from app.schemas.attendance import Attendance, AttendanceCreate, AttendanceList, AttendanceMark, AttendanceMarkWithQR

router = APIRouter()


@router.get("/session/{session_id}", response_model=AttendanceList)
async def get_session_attendances(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Attendance = Depends(get_current_active_user)
) -> Any:
    """Get all attendances for a session"""
    # Verify session ownership if faculty
    if current_user.role == "FACULTY":
        session_service = SessionService(db)
        session = await session_service.get_session(session_id)
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
    
    attendance_service = AttendanceService(db)
    attendances = await attendance_service.get_session_attendances(session_id)
    return {"attendances": attendances}


@router.get("/student/{student_id}", response_model=AttendanceList)
async def get_student_attendances(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Attendance = Depends(get_current_active_user)
) -> Any:
    """Get all attendances for a student"""
    # Verify student ID matches current user if student
    if current_user.role == "STUDENT" and current_user.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this student's attendance"
        )
    
    attendance_service = AttendanceService(db)
    attendances = await attendance_service.get_student_attendances(student_id)
    return {"attendances": attendances}


@router.get("/my", response_model=AttendanceList)
async def get_my_attendances(
    db: AsyncSession = Depends(get_db),
    current_user: Attendance = Depends(get_current_student)
) -> Any:
    """Get current student's attendances"""
    attendance_service = AttendanceService(db)
    attendances = await attendance_service.get_student_attendances(current_user.id)
    return {"attendances": attendances}


@router.post("/mark", response_model=Attendance)
async def mark_attendance(
    attendance_in: AttendanceMark,
    db: AsyncSession = Depends(get_db),
    current_user: Attendance = Depends(get_current_student)
) -> Any:
    """Mark attendance for current student"""
    attendance_service = AttendanceService(db)
    attendance = await attendance_service.mark_attendance(
        session_id=attendance_in.session_id,
        student_id=current_user.id,
        verification_factors=attendance_in.verification_factors
    )
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot mark attendance"
        )
    return attendance

# app/api/endpoints/attendance.py
# Keep most of the code the same, but update the mark_attendance_with_qr endpoint

@router.post("/mark-with-qr", response_model=Dict[str, Any])
def mark_attendance_with_qr(
    data: AttendanceMarkWithQR,  # Use a single request body parameter
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
) -> Any:
    """Mark attendance using QR code data with verification factors"""
    # Convert to synchronous function instead of async
    attendance_service = AttendanceService(db)
    result = attendance_service.mark_attendance_with_qr(
        student_id=current_user.id,
        encrypted_qr_data=data.encrypted_qr_data,
        verification_factors=data.verification_factors
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to mark attendance")
        )
    
    return {
        "success": True,
        "message": "Attendance marked successfully",
        "session_id": str(result["session"].id),
        "course_code": result["session"].course_code,
        "marked_at": result["attendance"].marked_at.isoformat()
    }
    
@router.get("/history", response_model=List[Dict[str, Any]])
def get_attendance_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
) -> Any:
    """Get attendance history for current student"""
    attendance_service = AttendanceService(db)
    history = attendance_service.get_student_attendance_history(current_user.id)
    return history

@router.get("/faculty/sessions", response_model=List[Dict[str, Any]])
def get_faculty_sessions_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_faculty)
) -> Any:
    """Get attendance stats for all sessions created by current faculty"""
    attendance_service = AttendanceService(db)
    sessions = attendance_service.get_faculty_session_attendance(current_user.id)
    return sessions

@router.get("/session/{session_id}/full", response_model=List[Dict[str, Any]])
def get_full_session_attendance(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_faculty)
) -> Any:
    """Get detailed attendance for a specific session"""
    # Verify session belongs to this faculty
    session_service = SessionService(db)
    session = session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if str(session.faculty_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session"
        )
    
    # Get detailed attendance list
    attendance_service = AttendanceService(db)
    attendances = attendance_service.get_session_attendances_with_details(session_id)
    
    return attendances

@router.post("/mark-with-factors", response_model=Dict[str, Any])
def mark_attendance_with_factors(
    data: AttendanceMarkWithQR,  # Reuse the same schema
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
) -> Any:
    """Mark attendance with multiple verification factors"""
    # This can just call the same service method as mark-with-qr
    attendance_service = AttendanceService(db)
    result = attendance_service.mark_attendance_with_qr(
        student_id=current_user.id,
        encrypted_qr_data=data.encrypted_qr_data,
        verification_factors=data.verification_factors
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to mark attendance")
        )
    
    return {
        "success": True,
        "message": "Attendance marked successfully",
        "session_id": str(result["session"].id),
        "course_code": result["session"].course_code,
        "marked_at": result["attendance"].marked_at.isoformat()
    }