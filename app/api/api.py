# app/api/api.py
from fastapi import APIRouter
from app.api.endpoints import auth, users, sessions, attendance, admin, courses, rooms, assignments

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])