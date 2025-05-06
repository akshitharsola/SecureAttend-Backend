# app/api/endpoints/assignments.py
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.assignment import Assignment, AssignmentCreate, AssignmentUpdate, AssignmentList
from app.services.assignment import AssignmentService
from app.models.user import User
from app.models.course import Course
from app.models.room import Room

router = APIRouter()

@router.post("/", response_model=Assignment, status_code=status.HTTP_201_CREATED)
def create_assignment(
    assignment_in: AssignmentCreate,
    db: Session = Depends(get_db)
) -> Any:
    """Create a new assignment"""
    assignment_service = AssignmentService(db)
    try:
        assignment = assignment_service.create_assignment(assignment_in)
        
        # Enrich with related data
        faculty = db.query(User).filter(User.id == assignment.faculty_id).first()
        course = db.query(Course).filter(Course.id == assignment.course_id).first()
        room = db.query(Room).filter(Room.id == assignment.room_id).first()
        
        # Create response
        response = assignment.__dict__.copy()
        response["faculty_name"] = faculty.full_name if faculty else None
        response["course_code"] = course.course_code if course else None
        response["course_name"] = course.course_name if course else None
        response["room_number"] = room.room_number if room else None
        
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# app/api/endpoints/assignments.py
@router.get("/", response_model=AssignmentList)
def get_all_assignments(
    db: Session = Depends(get_db)
) -> Any:
    """Get all assignments"""
    assignment_service = AssignmentService(db)
    assignments = assignment_service.get_all_assignments()
    
    # Enrich assignments with related data
    enriched_assignments = []
    for assignment in assignments:
        faculty = db.query(User).filter(User.id == assignment.faculty_id).first()
        course = db.query(Course).filter(Course.id == assignment.course_id).first()
        room = db.query(Room).filter(Room.id == assignment.room_id).first()
        
        if faculty and course and room:  # Make sure all exist
            assignment_dict = assignment.__dict__.copy()
            assignment_dict["faculty_name"] = faculty.full_name
            assignment_dict["course_code"] = course.course_code
            assignment_dict["course_name"] = course.course_name
            assignment_dict["room_number"] = room.room_number
            
            enriched_assignments.append(assignment_dict)
    
    return {"assignments": enriched_assignments}

@router.get("/faculty/{faculty_id}", response_model=AssignmentList)
def get_faculty_assignments(
    faculty_id: str,
    db: Session = Depends(get_db)
) -> Any:
    """Get all assignments for a faculty member"""
    assignment_service = AssignmentService(db)
    assignments = assignment_service.get_faculty_assignments(faculty_id)
    
    # Enrich assignments with related data
    enriched_assignments = []
    for assignment in assignments:
        faculty = db.query(User).filter(User.id == assignment.faculty_id).first()
        course = db.query(Course).filter(Course.id == assignment.course_id).first()
        room = db.query(Room).filter(Room.id == assignment.room_id).first()
        
        assignment_dict = assignment.__dict__.copy()
        assignment_dict["faculty_name"] = faculty.full_name if faculty else None
        assignment_dict["course_code"] = course.course_code if course else None
        assignment_dict["course_name"] = course.course_name if course else None
        assignment_dict["room_number"] = room.room_number if room else None
        
        enriched_assignments.append(assignment_dict)
    
    return {"assignments": enriched_assignments}

@router.get("/{assignment_id}", response_model=Assignment)
def get_assignment(
    assignment_id: str,
    db: Session = Depends(get_db)
) -> Any:
    """Get a specific assignment by ID"""
    assignment_service = AssignmentService(db)
    assignment = assignment_service.get_assignment(assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Enrich with related data
    faculty = db.query(User).filter(User.id == assignment.faculty_id).first()
    course = db.query(Course).filter(Course.id == assignment.course_id).first()
    room = db.query(Room).filter(Room.id == assignment.room_id).first()
    
    response = assignment.__dict__.copy()
    response["faculty_name"] = faculty.full_name if faculty else None
    response["course_code"] = course.course_code if course else None
    response["course_name"] = course.course_name if course else None
    response["room_number"] = room.room_number if room else None
    
    return response

@router.put("/{assignment_id}", response_model=Assignment)
def update_assignment(
    assignment_id: str,
    assignment_in: AssignmentUpdate,
    db: Session = Depends(get_db)
) -> Any:
    """Update an assignment"""
    assignment_service = AssignmentService(db)
    assignment = assignment_service.update_assignment(assignment_id, assignment_in)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Enrich with related data
    faculty = db.query(User).filter(User.id == assignment.faculty_id).first()
    course = db.query(Course).filter(Course.id == assignment.course_id).first()
    room = db.query(Room).filter(Room.id == assignment.room_id).first()
    
    response = assignment.__dict__.copy()
    response["faculty_name"] = faculty.full_name if faculty else None
    response["course_code"] = course.course_code if course else None
    response["course_name"] = course.course_name if course else None
    response["room_number"] = room.room_number if room else None
    
    return response

@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: str,
    db: Session = Depends(get_db)
) -> None:
    """Delete an assignment"""
    assignment_service = AssignmentService(db)
    success = assignment_service.delete_assignment(assignment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )