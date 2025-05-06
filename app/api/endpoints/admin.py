# app/api/endpoints/admin.py
from typing import Any, Dict
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.session import Session
from app.schemas.session import Session
from app.services.qr_code import QRCodeService
from app.models.user import User as UserModel  # Import the User model and rename it to UserModel

router = APIRouter()

# Create templates directory if it doesn't exist
os.makedirs("templates", exist_ok=True)
os.makedirs("templates/admin", exist_ok=True)

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request
) -> Any:
    """Admin dashboard - No authentication required for research purposes"""
    return templates.TemplateResponse(
        "admin/dashboard.html", 
        {"request": request, "user": {"full_name": "Admin User"}}
    )

@router.post("/maintenance/cleanup-qr", response_model=Dict[str, int])
def cleanup_qr_codes(  # Remove async
    db: Session = Depends(get_db),  # Change from AsyncSession to Session
    current_user: UserModel = Depends(get_current_admin)
) -> Any:
    """Clean up expired QR code files"""
    qr_code_service = QRCodeService()
    count = qr_code_service.cleanup_expired_qr_codes()
    return {"removed_files": count}