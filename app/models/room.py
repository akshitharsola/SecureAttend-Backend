# app/models/room.py
import uuid
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    room_number = Column(String, unique=True, index=True, nullable=False)
    building = Column(String, nullable=True)
    capacity = Column(Integer, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    assignments = relationship("Assignment", back_populates="room")