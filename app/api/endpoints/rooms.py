# app/api/endpoints/rooms.py
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.room import Room, RoomCreate, RoomUpdate, RoomList
from app.services.room import RoomService

router = APIRouter()

@router.post("/", response_model=Room, status_code=status.HTTP_201_CREATED)
def create_room(
    room_in: RoomCreate,
    db: Session = Depends(get_db)
) -> Any:
    """Create a new room (no authentication required)"""
    room_service = RoomService(db)
    try:
        room = room_service.create_room(room_in)
        return room
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=RoomList)
def get_all_rooms(
    db: Session = Depends(get_db)
) -> Any:
    """Get all rooms (no authentication required)"""
    room_service = RoomService(db)
    rooms = room_service.get_all_rooms()
    return RoomList(rooms=rooms)

@router.get("/{room_id}", response_model=Room)
def get_room(
    room_id: str,
    db: Session = Depends(get_db)
) -> Any:
    """Get a specific room by ID"""
    room_service = RoomService(db)
    room = room_service.get_room(room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    return room

@router.put("/{room_id}", response_model=Room)
def update_room(
    room_id: str,
    room_in: RoomUpdate,
    db: Session = Depends(get_db)
) -> Any:
    """Update a room (no authentication required)"""
    room_service = RoomService(db)
    room = room_service.update_room(room_id, room_in)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    return room

@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(
    room_id: str,
    db: Session = Depends(get_db)
) -> None:
    """Delete a room (no authentication required)"""
    room_service = RoomService(db)
    success = room_service.delete_room(room_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )