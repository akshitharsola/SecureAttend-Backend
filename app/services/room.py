# app/services/room.py
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.room import Room
from app.schemas.room import RoomCreate, RoomUpdate

class RoomService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_room(self, room_id: str) -> Optional[Room]:
        """Get room by ID"""
        return self.db.query(Room).filter(Room.id == room_id).first()
    
    def get_room_by_number(self, room_number: str) -> Optional[Room]:
        """Get room by number"""
        return self.db.query(Room).filter(Room.room_number == room_number).first()
    
    def get_all_rooms(self) -> List[Room]:
        """Get all rooms"""
        return self.db.query(Room).all()
    
    def create_room(self, room_in: RoomCreate) -> Room:
        """Create new room"""
        # Check if room with this number already exists
        existing_room = self.get_room_by_number(room_in.room_number)
        if existing_room:
            raise ValueError(f"Room with number {room_in.room_number} already exists")
        
        # Create room ID
        room_id = str(uuid.uuid4())
        
        # Create room object
        db_room = Room(
            id=room_id,
            room_number=room_in.room_number,
            building=room_in.building,
            capacity=room_in.capacity,
            description=room_in.description
        )
        
        # Add to database
        self.db.add(db_room)
        self.db.commit()
        self.db.refresh(db_room)
        
        return db_room
    
    def update_room(self, room_id: str, room_in: RoomUpdate) -> Optional[Room]:
        """Update existing room"""
        # Get room
        db_room = self.get_room(room_id)
        if not db_room:
            return None
        
        # Update room data
        room_data = room_in.dict(exclude_unset=True)
        
        # Check if room_number is being updated and already exists
        if room_data.get("room_number") and room_data["room_number"] != db_room.room_number:
            existing_room = self.get_room_by_number(room_data["room_number"])
            if existing_room:
                raise ValueError(f"Room with number {room_data['room_number']} already exists")
        
        # Update fields
        for field, value in room_data.items():
            setattr(db_room, field, value)
        
        # Save changes
        self.db.commit()
        self.db.refresh(db_room)
        
        return db_room
    
    def delete_room(self, room_id: str) -> bool:
        """Delete room"""
        # Get room
        db_room = self.get_room(room_id)
        if not db_room:
            return False
        
        # Delete room
        self.db.delete(db_room)
        self.db.commit()
        
        return True