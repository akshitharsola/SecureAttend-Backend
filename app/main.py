# Step 7: Update main.py to use synchronous style
# app/main.py
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from app.api.api import api_router
from app.core.config import settings

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

os.makedirs(settings.QR_CODE_STORAGE_PATH, exist_ok=True)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create dirs if they don't exist
os.makedirs("static/qr_codes", exist_ok=True)

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Admin dashboard
@app.get("/api/v1/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin/dashboard.html", {"request": request})

# Error handler for exceptions
@app.exception_handler(Exception)
def handle_exception(request: Request, exc: Exception):
    print(f"Error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "detail": str(exc)}
    )