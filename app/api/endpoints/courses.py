# app/api/endpoints/courses.py
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.course import Course, CourseCreate, CourseUpdate, CourseList
from app.services.course import CourseService

router = APIRouter()

@router.post("/", response_model=Course, status_code=status.HTTP_201_CREATED)
def create_course(
    course_in: CourseCreate,
    db: Session = Depends(get_db)
) -> Any:
    """Create a new course (no authentication required)"""
    course_service = CourseService(db)
    try:
        course = course_service.create_course(course_in)
        return course
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=CourseList)
def get_all_courses(
    db: Session = Depends(get_db)
) -> Any:
    """Get all courses (no authentication required)"""
    course_service = CourseService(db)
    courses = course_service.get_all_courses()
    return CourseList(courses=courses)

@router.get("/{course_id}", response_model=Course)
def get_course(
    course_id: str,
    db: Session = Depends(get_db)
) -> Any:
    """Get a specific course by ID"""
    course_service = CourseService(db)
    course = course_service.get_course(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    return course

@router.put("/{course_id}", response_model=Course)
def update_course(
    course_id: str,
    course_in: CourseUpdate,
    db: Session = Depends(get_db)
) -> Any:
    """Update a course (no authentication required)"""
    course_service = CourseService(db)
    course = course_service.update_course(course_id, course_in)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    return course

@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: str,
    db: Session = Depends(get_db)
) -> None:
    """Delete a course (no authentication required)"""
    course_service = CourseService(db)
    success = course_service.delete_course(course_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )