# tests/unit/test_qr_code_service.py
import pytest
import os
import json
from datetime import datetime, timedelta
from app.services.qr_code import QRCodeService
from app.core.config import settings

@pytest.fixture
def qr_service():
    """Fixture for QR code service"""
    return QRCodeService()


@pytest.fixture
def session_data():
    """Fixture for session data"""
    return {
        "session_id": "123e4567-e89b-12d3-a456-426614174000",
        "faculty_id": "123e4567-e89b-12d3-a456-426614174001",
        "course_code": "CS101",
        "room_number": "R202",
        "proximity_uuid": "abcd1234"
    }


class TestQRCodeService:
    """Tests for QR code service"""

    def test_initialization(self, qr_service, mock_settings):
        """Test QR code service initialization"""
        assert qr_service.qr_path == mock_settings.QR_CODE_STORAGE_PATH
        assert qr_service.cipher_suite is not None

    def test_encrypt_decrypt(self, qr_service):
        """Test encryption and decryption"""
        original_data = "test data"
        encrypted = qr_service._encrypt_data(original_data)
        decrypted = qr_service._decrypt_data(encrypted)
        assert decrypted == original_data
        assert encrypted != original_data  # Ensure data was actually encrypted

    def test_generate_qr_code(self, qr_service, session_data):
        """Test QR code generation"""
        result = qr_service.generate_session_qr(
            session_id=session_data["session_id"],
            faculty_id=session_data["faculty_id"],
            course_code=session_data["course_code"],
            room_number=session_data["room_number"],
            proximity_uuid=session_data["proximity_uuid"]
        )

        # Check result structure
        assert "session_id" in result
        assert "encrypted_data" in result
        assert "image_url" in result
        assert "expires_at" in result

        # Verify QR file was created
        filename = f"session_{session_data['session_id']}.png"
        file_path = os.path.join(settings.QR_CODE_STORAGE_PATH, filename)
        assert os.path.exists(file_path)

        # Clean up file after test
        if os.path.exists(file_path):
            os.remove(file_path)

    def test_verify_qr_data(self, qr_service, session_data):
        """Test QR code verification"""
        # Generate QR code
        result = qr_service.generate_session_qr(
            session_id=session_data["session_id"],
            faculty_id=session_data["faculty_id"],
            course_code=session_data["course_code"],
            room_number=session_data["room_number"],
            proximity_uuid=session_data["proximity_uuid"]
        )

        # Verify QR data
        verification = qr_service.verify_qr_data(result["encrypted_data"])
        assert verification["valid"] is True
        assert "data" in verification
        assert verification["data"]["session_id"] == session_data["session_id"]
        assert verification["data"]["proximity_uuid"] == session_data["proximity_uuid"]

        # Clean up file after test
        filename = f"session_{session_data['session_id']}.png"
        file_path = os.path.join(settings.QR_CODE_STORAGE_PATH, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    def test_qr_expiry(self, qr_service, session_data, monkeypatch):
        """Test QR code expiry verification"""
        # Generate QR code
        result = qr_service.generate_session_qr(
            session_id=session_data["session_id"],
            faculty_id=session_data["faculty_id"],
            course_code=session_data["course_code"],
            room_number=session_data["room_number"],
            proximity_uuid=session_data["proximity_uuid"]
        )

        # Extract and modify the data to simulate expiry
        encrypted_data = result["encrypted_data"]
        decrypted_data = qr_service._decrypt_data(encrypted_data)
        data_dict = json.loads(decrypted_data)
        
        # Set expiry to the past
        past_time = (datetime.utcnow() - timedelta(minutes=15)).isoformat()
        data_dict["expires_at"] = past_time
        
        # Re-encrypt the modified data
        modified_data = qr_service._encrypt_data(json.dumps(data_dict))
        
        # Verify the expired QR data
        verification = qr_service.verify_qr_data(modified_data)
        assert verification["valid"] is False
        assert "QR code has expired" in verification["error"]

        # Clean up file after test
        filename = f"session_{session_data['session_id']}.png"
        file_path = os.path.join(settings.QR_CODE_STORAGE_PATH, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    def test_refresh_qr_code(self, qr_service, session_data):
        """Test QR code refresh"""
        # Generate initial QR code
        initial_result = qr_service.generate_session_qr(
            session_id=session_data["session_id"],
            faculty_id=session_data["faculty_id"],
            course_code=session_data["course_code"],
            room_number=session_data["room_number"],
            proximity_uuid=session_data["proximity_uuid"]
        )

        # Refresh QR code
        refreshed_result = qr_service.refresh_session_qr(
            session_id=session_data["session_id"],
            faculty_id=session_data["faculty_id"],
            course_code=session_data["course_code"],
            room_number=session_data["room_number"],
            proximity_uuid=session_data["proximity_uuid"]
        )

        # Check that the data is different (new expiry)
        assert initial_result["encrypted_data"] != refreshed_result["encrypted_data"]
        
        # Verify both QR codes contain the same basic data
        initial_verification = qr_service.verify_qr_data(initial_result["encrypted_data"])
        refreshed_verification = qr_service.verify_qr_data(refreshed_result["encrypted_data"])
        
        assert initial_verification["valid"] is True
        assert refreshed_verification["valid"] is True
        
        assert initial_verification["data"]["session_id"] == refreshed_verification["data"]["session_id"]
        assert initial_verification["data"]["proximity_uuid"] == refreshed_verification["data"]["proximity_uuid"]
        
        # Clean up file after test
        filename = f"session_{session_data['session_id']}.png"
        file_path = os.path.join(settings.QR_CODE_STORAGE_PATH, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    def test_cleanup_expired_qr_codes(self, qr_service, session_data):
        """Test cleanup of expired QR codes"""
        # Generate multiple QR codes
        for i in range(3):
            qr_service.generate_session_qr(
                session_id=f"{session_data['session_id']}-{i}",
                faculty_id=session_data["faculty_id"],
                course_code=session_data["course_code"],
                room_number=session_data["room_number"],
                proximity_uuid=session_data["proximity_uuid"]
            )
        
        # Manually set file time to be older
        for i in range(3):
            filename = f"session_{session_data['session_id']}-{i}.png"
            file_path = os.path.join(settings.QR_CODE_STORAGE_PATH, filename)
            if os.path.exists(file_path):
                # Set modification time to 30 minutes ago
                old_time = datetime.now() - timedelta(minutes=30)
                os.utime(file_path, (old_time.timestamp(), old_time.timestamp()))
        
        # Run cleanup
        count = qr_service.cleanup_expired_qr_codes()
        
        # Check that files were removed
        assert count > 0
        
        # Clean up any remaining files
        for i in range(3):
            filename = f"session_{session_data['session_id']}-{i}.png"
            file_path = os.path.join(settings.QR_CODE_STORAGE_PATH, filename)
            if os.path.exists(file_path):
                os.remove(file_path)