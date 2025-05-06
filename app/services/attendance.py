# app/services/attendance.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from app.models.attendance import Attendance
from app.models.session import Session, SessionStatus
from app.services.qr_code import QRCodeService
from app.services.session import SessionService
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class AttendanceService:
    def __init__(self, db: Session):
        self.db = db
        # Initialize the session service here for consistency
        self.session_service = SessionService(db)
    
    async def get_attendance(self, attendance_id: uuid.UUID) -> Optional[Attendance]:
        """Get attendance by ID"""
        result = await self.db.execute(select(Attendance).where(Attendance.id == attendance_id))
        return result.scalar_one_or_none()
    
    # async def get_session_attendances(self, session_id: uuid.UUID) -> List[Attendance]:
    #     """Get all attendances for a session"""
    #     result = await self.db.execute(select(Attendance).where(Attendance.session_id == session_id))
    #     return result.scalars().all()
    
    def get_session_attendances_with_details(self, session_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get detailed attendance list for a session including student names"""
        try:
            # Get all attendances for this session
            attendances = self.db.query(Attendance).filter(
                Attendance.session_id == session_id
            ).order_by(Attendance.marked_at.desc()).all()
            
            # Get student details
            from app.models.user import User
            student_ids = [attendance.student_id for attendance in attendances]
            students = {}
            
            if student_ids:
                student_results = self.db.query(User).filter(User.id.in_(student_ids)).all()
                students = {str(student.id): {
                    "name": student.full_name,
                    "email": student.email,
                    "roll_number": student.roll_number
                } for student in student_results}
            
            # Format results
            result = []
            for attendance in attendances:
                student_id = str(attendance.student_id)
                student_info = students.get(student_id, {"name": "Unknown", "email": "Unknown", "roll_number": ""})
                
                # Format verification information
                verification_factors = attendance.verification_factors or {}
                verification_methods = list(verification_factors.keys())
                verification_complete = all(verification_factors.values()) if verification_factors else False
                
                result.append({
                    "id": str(attendance.id),
                    "student_id": student_id,
                    "student_name": student_info["name"],
                    "student_email": student_info["email"],
                    "student_roll": student_info["roll_number"],
                    "marked_at": attendance.marked_at.isoformat(),
                    "verification": {
                        "methods": verification_methods,
                        "complete": verification_complete,
                        "qr": verification_factors.get('qr', False),
                        "face": verification_factors.get('face', False),
                        "proximity": verification_factors.get('proximity', False)
                    }
                })
                
            return result
        except Exception as e:
            logger.error(f"Error getting session attendances with details: {str(e)}")
            return []
    
    async def get_student_attendances(self, student_id: uuid.UUID) -> List[Attendance]:
        """Get all attendances for a student"""
        result = await self.db.execute(select(Attendance).where(Attendance.student_id == student_id))
        return result.scalars().all()
    
    async def mark_attendance(
        self, 
        session_id: uuid.UUID, 
        student_id: uuid.UUID,
        verification_factors: Dict[str, bool]
    ) -> Optional[Attendance]:
        """Mark attendance for a student in a session"""
        # Check if attendance already exists
        result = await self.db.execute(
            select(Attendance).where(
                Attendance.session_id == session_id,
                Attendance.student_id == student_id
            )
        )
        attendance = result.scalar_one_or_none()
        if attendance:
            return attendance
        
        # Check if session exists and is active
        session_result = await self.db.execute(select(Session).where(Session.id == session_id))
        session = session_result.scalar_one_or_none()
        if not session or session.status != SessionStatus.ACTIVE:
            return None
        
        # Create attendance
        db_attendance = Attendance(
            session_id=session_id,
            student_id=student_id,
            marked_at=datetime.utcnow(),
            verification_factors=verification_factors
        )
        self.db.add(db_attendance)
        await self.db.commit()
        await self.db.refresh(db_attendance)
        return db_attendance
    
    def mark_attendance_with_qr(
        self,
        student_id: uuid.UUID,
        encrypted_qr_data: str,
        verification_factors: Dict[str, bool]
    ) -> Optional[Dict[str, Any]]:
        """Mark attendance using QR code data
        
        Verifies QR code and records attendance with verification factors
        """
        try:
            # Verify QR code data
            qr_code_service = QRCodeService()
            verification_result = qr_code_service.verify_qr_data(encrypted_qr_data)
            
            logger.debug(f"QR verification result: {verification_result}")
            
            if not verification_result.get("valid"):
                return {
                    "success": False,
                    "error": verification_result.get("error", "Invalid QR code")
                }
            
            # Get session data from verification result
            session_data = verification_result.get("data", {})
            session_id_str = session_data.get("session_id")
            
            if not session_id_str:
                logger.error("Session ID missing from QR data")
                return {
                    "success": False,
                    "error": "Invalid session data in QR code"
                }
                
            logger.debug(f"Getting session with ID: {session_id_str}")
            
            # Get the session using the session service
            session = self.session_service.get_session(session_id_str)
            
            if not session:
                logger.error(f"Session not found with ID: {session_id_str}")
                return {
                    "success": False,
                    "error": "Session not found"
                }
                
            logger.debug(f"Found session with status: {session.status}")
            
            if session.status != SessionStatus.ACTIVE:
                return {
                    "success": False,
                    "error": f"Session is not active (status: {session.status})"
                }
            
            # Check if student has already marked attendance for this session
            existing_attendance = self.get_student_attendance_for_session(
                student_id=student_id,
                session_id=session.id
            )
            
            if existing_attendance:
                return {
                    "success": False,
                    "error": "Attendance already marked for this session"
                }
            
            # Mark attendance
            attendance = self.create_attendance(
                student_id=student_id,
                session_id=session.id,
                verification_factors=verification_factors
            )
            
            if not attendance:
                return {
                    "success": False,
                    "error": "Failed to mark attendance"
                }
            
            return {
                "success": True,
                "attendance": attendance,
                "session": session
            }
        except Exception as e:
            logger.error(f"Error in mark_attendance_with_qr: {str(e)}")
            return {
                "success": False,
                "error": f"Error marking attendance: {str(e)}"
            }
        
    def get_student_attendance_for_session(
        self,
        student_id: uuid.UUID,
        session_id: str
    ) -> Optional[Attendance]:
        """Get a student's attendance for a specific session"""
        try:
            result = self.db.query(Attendance).filter(
                Attendance.session_id == session_id,
                Attendance.student_id == student_id
            ).first()
            return result
        except Exception as e:
            logger.error(f"Error getting attendance: {str(e)}")
            return None
        
    def create_attendance(
        self,
        student_id: uuid.UUID,
        session_id: str,
        verification_factors: Dict[str, bool]
    ) -> Optional[Attendance]:
        """Create an attendance record"""
        try:
            # Convert UUIDs to strings if needed
            if isinstance(student_id, uuid.UUID):
                student_id_str = str(student_id)
            else:
                student_id_str = student_id
                
            if isinstance(session_id, uuid.UUID):
                session_id_str = str(session_id)
            else:
                session_id_str = session_id
                
            # Create attendance record
            db_attendance = Attendance(
                session_id=session_id_str,
                student_id=student_id_str,
                marked_at=datetime.utcnow(),
                verification_factors=verification_factors
            )
            self.db.add(db_attendance)
            self.db.commit()
            self.db.refresh(db_attendance)
            return db_attendance
        except Exception as e:
            logger.error(f"Error creating attendance record: {str(e)}")
            self.db.rollback()
            return None
        
    # Fix for get_student_attendance_history method

    def get_student_attendance_history(self, student_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get detailed attendance history for a student with session details"""
        try:
            # Use aliases to refer to the models in the join
            from app.models.session import Session as SessionModel
            
            # Get all attendance records for this student with session data
            query = (
                self.db.query(
                    Attendance,  # Full attendance record
                    SessionModel  # Full session record
                )
                .join(SessionModel, Attendance.session_id == SessionModel.id)
                .filter(Attendance.student_id == student_id)
                .order_by(Attendance.marked_at.desc())
            )
            
            results = query.all()
            
            # Format results
            history = []
            for attendance, session in results:
                # Calculate verification summary
                verification_factors = attendance.verification_factors or {}
                verification_methods = list(verification_factors.keys())
                verification_complete = all(verification_factors.values()) if verification_factors else False
                
                # Format session date/time
                session_date = None
                session_time = None
                if hasattr(session, 'start_time') and session.start_time:
                    session_date = session.start_time.date().isoformat()
                    session_time = session.start_time.time().isoformat()
                
                history.append({
                    "id": str(attendance.id),
                    "session_id": str(attendance.session_id),
                    "course_code": session.course_code if hasattr(session, 'course_code') else "Unknown Course",
                    "room_number": session.room_number if hasattr(session, 'room_number') else "No Room",
                    "session_status": session.status.value if hasattr(session, 'status') else "UNKNOWN",
                    "session_date": session_date,
                    "session_time": session_time,
                    "marked_at": attendance.marked_at.isoformat(),
                    "verification": {
                        "methods": verification_methods,
                        "complete": verification_complete,
                        "qr": verification_factors.get('qr', False),
                        "face": verification_factors.get('face', False),
                        "proximity": verification_factors.get('proximity', False)
                    }
                })
                    
            return history
        except Exception as e:
            logger.error(f"Error getting student attendance history: {str(e)}")
            return []

    def get_faculty_session_attendance(self, faculty_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get attendance stats for all sessions created by a faculty"""
        try:
            from app.models.session import Session as SessionModel
            from app.models.user import User
            
            # Get all sessions by this faculty
            sessions = self.db.query(SessionModel).filter(SessionModel.faculty_id == faculty_id).all()
            
            result = []
            
            for session in sessions:
                # Count attendances for this session
                attendances_count = self.db.query(Attendance).filter(
                    Attendance.session_id == session.id
                ).count()
                
                # Get the latest few attendances for preview
                recent_attendances = (
                    self.db.query(Attendance)
                    .filter(Attendance.session_id == session.id)
                    .order_by(Attendance.marked_at.desc())
                    .limit(5)
                    .all()
                )
                
                # Get student names for the recent attendances
                student_ids = [attendance.student_id for attendance in recent_attendances]
                student_info = {}
                
                if student_ids:
                    students = self.db.query(User).filter(User.id.in_(student_ids)).all()
                    student_info = {str(student.id): {
                        "name": student.full_name,
                        "roll_number": student.roll_number if hasattr(student, 'roll_number') else None
                    } for student in students}
                
                # Format date/time information
                session_date = None
                session_time = None
                if hasattr(session, 'start_time') and session.start_time:
                    session_date = session.start_time.date().isoformat()
                    session_time = session.start_time.time().isoformat()
                elif hasattr(session, 'created_at') and session.created_at:
                    session_date = session.created_at.date().isoformat()
                
                result.append({
                    "session_id": str(session.id),
                    "course_code": session.course_code if hasattr(session, 'course_code') else "Unknown Course",
                    "room_number": session.room_number if hasattr(session, 'room_number') else "No Room",
                    "date": session_date,
                    "time": session_time,
                    "status": session.status.value if hasattr(session, 'status') else "UNKNOWN",
                    "attendances_count": attendances_count,
                    "recent_attendances": [
                        {
                            "id": str(a.id),
                            "student_id": str(a.student_id),
                            "student_name": student_info.get(str(a.student_id), {}).get("name", "Unknown"),
                            "student_roll": student_info.get(str(a.student_id), {}).get("roll_number", ""),
                            "marked_at": a.marked_at.isoformat(),
                            "verification_methods": list(a.verification_factors.keys()) if a.verification_factors else []
                        } for a in recent_attendances
                    ]
                })
                    
            return result
        except Exception as e:
            logger.error(f"Error getting faculty session attendance: {str(e)}")
            return []