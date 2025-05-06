# app/schemas/room.py
from typing import Optional, List
from pydantic import BaseModel

# Base Room Schema (shared properties)
class RoomBase(BaseModel):
    room_number: str
    building: Optional[str] = None
    capacity: Optional[int] = None
    description: Optional[str] = None

# Schema for creating a room
class RoomCreate(RoomBase):
    pass

# Schema for updating a room
class RoomUpdate(BaseModel):
    room_number: Optional[str] = None
    building: Optional[str] = None
    capacity: Optional[int] = None
    description: Optional[str] = None

# Schema for room in response
class Room(RoomBase):
    id: str
    
    class Config:
        from_attributes = True  # Changed from orm_mode = True

# Schema for list of rooms
class RoomList(BaseModel):
    rooms: List[Room] = []