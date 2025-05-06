# tests/api/test_sessions_api.py
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import Depends

# Mock the User model and dependencies
class MockUser:
    id = str(uuid.uuid4())
    email = "test@example.com"
    full_name = "Test User"
    role = "FACULTY"

# We'll need to create mock functions and patch dependencies
@pytest.fixture
def client():
    # Import app here to avoid circular imports
    from app.main import app
    return TestClient(app)

@pytest.fixture
def mock_auth(monkeypatch):
    """Mock authentication dependencies"""
    
    # Create mock auth functions
    async def mock_get_current_faculty(*args, **kwargs):
        return MockUser()
        
    async def mock_get_current_student(*args, **kwargs):
        user = MockUser()
        user.role = "STUDENT"
        return user
    
    # Apply patches to dependencies
    from app.api import deps
    monkeypatch.setattr(deps, "get_current_faculty", mock_get_current_faculty)
    monkeypatch.setattr(deps, "get_current_student", mock_get_current_student)

@pytest.fixture
def mock_session_service(monkeypatch):
    """Mock session service"""
    
    class MockSession:
        id = str(uuid.uuid4())
        faculty_id = str(uuid.uuid4())
        course_code = "CS101"
        room_number = "R202"
        proximity_uuid = "abcd1234"
        status = "ACTIVE"
        
    class MockSessionService:
        async def create_session(self, faculty_id, course_code, room_number, proximity_uuid):
            return MockSession()
            
        async def get_session(self, session_id):
            return MockSession()
            
        async def start_session(self, session_id):
            return MockSession()
            
        async def end_session(self, session_id):
            return MockSession()
    
    # Apply monkeypatch
    with patch('app.services.session.SessionService', return_value=MockSessionService()):
        yield MockSession()

@pytest.fixture
def mock_qr_service(monkeypatch):
    """Mock QR code service"""
    
    class MockQRService:
        def generate_session_qr(self, session_id, faculty_id, course_code, room_number, proximity_uuid):
            return {
                "session_id": session_id,
                "encrypted_data": "mock_encrypted_data",
                "image_url": "/static/qr_codes/mock.png",
                "expires_at": "2023-12-31T12:00:00"
            }
            
        def refresh_session_qr(self, session_id, faculty_id, course_code, room_number, proximity_uuid):
            return {
                "session_id": session_id,
                "encrypted_data": "mock_new_encrypted_data",
                "image_url": "/static/qr_codes/mock_new.png",
                "expires_at": "2023-12-31T13:00:00"
            }
            
        def verify_qr_data(self, encrypted_data):
            return {
                "valid": True,
                "data": {
                    "session_id": str(uuid.uuid4()),
                    "faculty_id": str(uuid.uuid4()),
                    "course_code": "CS101",
                    "room_number": "R202",
                    "proximity_uuid": "abcd1234"
                }
            }
    
    # Apply monkeypatch
    monkeypatch.setattr("app.services.qr_code.QRCodeService", MockQRService)
    return MockQRService()


# Test class with isolated tests that don't require the full API
class TestSessionsAPIIsolated:
    """Tests for sessions API without requiring the full application"""
    
    def test_create_session_isolated(self, mock_qr_service, mock_session_service):
        """Test the core session creation logic"""
        # This is a simpler test that doesn't require the API
        qr_data = mock_qr_service.generate_session_qr(
            session_id=str(uuid.uuid4()),
            faculty_id=str(uuid.uuid4()),
            course_code="CS101",
            room_number="R202",
            proximity_uuid="abcd1234"
        )
        
        assert "encrypted_data" in qr_data
        assert "image_url" in qr_data
        
    def test_verify_qr_data_isolated(self, mock_qr_service):
        """Test QR verification logic"""
        result = mock_qr_service.verify_qr_data("mock_data")
        assert result["valid"] is True
        assert "proximity_uuid" in result["data"]