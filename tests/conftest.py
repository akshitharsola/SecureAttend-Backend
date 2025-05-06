# tests/conftest.py
import pytest
import os
import sys
from pathlib import Path
import base64

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure test environment
os.environ["TESTING"] = "1"
os.environ["QR_CODE_STORAGE_PATH"] = "static/qr_codes/test"
os.environ["QR_CODE_EXPIRY_MINUTES"] = "10"

# Create test directory
os.makedirs("static/qr_codes/test", exist_ok=True)

# Create a fixture to mock the settings
@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings with test values"""
    from app.core.config import settings
    
    # Create a valid Fernet key for testing
    import secrets
    import base64
    import hashlib
    
    # Generate a proper 32-byte key and URL-safe base64 encode it
    test_key = secrets.token_bytes(32)
    encoded_key = base64.urlsafe_b64encode(test_key)
    
    # Patch the settings
    monkeypatch.setattr(settings, "SECRET_KEY", encoded_key.decode())
    monkeypatch.setattr(settings, "QR_CODE_STORAGE_PATH", "static/qr_codes/test")
    monkeypatch.setattr(settings, "QR_CODE_EXPIRY_MINUTES", 10)
    
    return settings

# Fix the QR service fixture
@pytest.fixture
def qr_service(mock_settings):
    """Fixture for QR code service with proper key"""
    from app.services.qr_code import QRCodeService
    
    # Create a QR service with the mocked settings
    service = QRCodeService()
    return service

# Clean up test environment after tests
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_files():
    yield
    # Clean up any test files
    import shutil
    if os.path.exists("static/qr_codes/test"):
        shutil.rmtree("static/qr_codes/test")