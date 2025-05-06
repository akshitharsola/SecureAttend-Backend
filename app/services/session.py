# app/services/session.py
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
import uuid
from datetime import datetime
import secrets
from app.models.session import Session as SessionModel, SessionStatus
from app.services.qr_code import QRCodeService
from sqlalchemy.orm import Session as DBSession
from app.models.session import Session, SessionStatus
import logging

logger = logging.getLogger(__name__)

class SessionService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_session(self, session_id: str) -> Optional[SessionModel]:
        """Get session by ID"""
        try:
            # Enhanced logging
            logger.debug(f"Getting session with ID: {session_id}, type: {type(session_id)}")
            
            # Use string comparison for SQLite
            if isinstance(session_id, uuid.UUID):
                session_id = str(session_id)
                
            # Query directly with string ID
            session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
            
            if session:
                logger.debug(f"Found session: {session.id}, status: {session.status}")
            else:
                logger.warning(f"Session not found with ID: {session_id}")
                
            return session
        except Exception as e:
            logger.error(f"Error getting session: {str(e)}")
            return None
    
    
    def get_faculty_sessions(self, faculty_id: uuid.UUID) -> List[SessionModel]:
        """Get sessions created by a faculty"""
        return self.db.query(SessionModel).filter(SessionModel.faculty_id == faculty_id).all()
    
    def get_active_sessions(self, faculty_id: Optional[uuid.UUID] = None) -> List[SessionModel]:
        """Get active sessions, optionally filtered by faculty"""
        query = self.db.query(SessionModel).filter(SessionModel.status == SessionStatus.ACTIVE)
        if faculty_id:
            query = query.filter(SessionModel.faculty_id == faculty_id)
        
        return query.all()
    
    def create_session(
        self,
        faculty_id: Union[str, uuid.UUID],
        course_code: str,
        room_number: str,
        proximity_uuid: str = None
    ) -> Session:
        """Create a new attendance session"""
        # Convert faculty_id to string if it's a UUID object
        faculty_id_str = str(faculty_id) if faculty_id else None
        
        # Generate unique ID as string
        session_id = str(uuid.uuid4())
        
        # Generate proximity UUID if not provided
        if not proximity_uuid:
            proximity_uuid = secrets.token_hex(4)  # 8 chars, 4 bytes
        
        # Create session with string IDs
        session = Session(
            id=session_id,
            faculty_id=faculty_id_str,  # Use string version
            course_code=course_code,
            room_number=room_number,
            proximity_uuid=proximity_uuid,
            start_time=datetime.utcnow(),
            is_active=True,
            status=SessionStatus.CREATED
        )
        
        # Add to database and commit
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session
        
    
    # In SessionService class, session.py
    def start_session(self, session_id):
        session = self.get_session(session_id)
        if not session:
            print(f"Session {session_id} not found")
            return None
            
        print(f"Starting session {session_id}, current status: {session.status}")
        
        # Only allow starting from CREATED status
        if session.status != SessionStatus.CREATED:
            print(f"Cannot start session with status {session.status}")
            return None
            
        # Update status to ACTIVE
        session.status = SessionStatus.ACTIVE
        session.start_time = datetime.utcnow()
        self.db.commit()
        
        print(f"Session {session_id} started successfully, new status: {session.status}")
        return session
    
    def end_session(self, session_id: uuid.UUID) -> Optional[SessionModel]:
        """End a session (change status to ENDED)"""
        session = self.get_session(session_id)
        if not session or session.status != SessionStatus.ACTIVE:
            return None
        
        # Update session
        session.status = SessionStatus.ENDED
        session.end_time = datetime.utcnow()
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def delete_session(self, session_id: uuid.UUID) -> bool:
        """Delete session"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        self.db.delete(session)
        self.db.commit()
        return True
    
    def get_session_with_qr(self, session_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get session with QR code data"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Generate QR code
        qr_code_service = QRCodeService()
        qr_data = qr_code_service.generate_session_qr(
            session_id=str(session.id),
            faculty_id=str(session.faculty_id),
            course_code=session.course_code,
            room_number=session.room_number,
            proximity_uuid=session.proximity_uuid
        )
        
        return {
            "session": session,
            "qr_data": qr_data
        }