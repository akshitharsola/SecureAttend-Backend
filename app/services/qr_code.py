# app/services/qr_code.py
import os
import json
import qrcode
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from app.core.config import settings

logger = logging.getLogger(__name__)

class QRCodeService:

    def __init__(self):
        """Initialize QR Code service"""
        self.qr_path = settings.QR_CODE_STORAGE_PATH
        
        # Ensure QR code directory exists
        os.makedirs(self.qr_path, exist_ok=True)
        
        # Set up encryption
        try:
            # Generate a proper Fernet key using base64
            import base64
            key_bytes = settings.SECRET_KEY.encode()
            # Create a hash and encode it properly for Fernet
            import hashlib
            key_hash = hashlib.sha256(key_bytes).digest()
            key = base64.urlsafe_b64encode(key_hash)
            self.cipher_suite = Fernet(key)
            logger.info("QR Code service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing QR Code service: {str(e)}")
            raise RuntimeError(f"Failed to initialize QR Code service: {str(e)}")
    
    def generate_session_qr(
        self, 
        session_id: str, 
        faculty_id: str, 
        course_code: str, 
        room_number: str, 
        proximity_uuid: str
    ) -> Dict[str, Any]:
        """Generate QR code for an attendance session
        
        Returns the QR data and image URL
        """
        try:
            # 1. Prepare QR data
            session_data = {
                "session_id": session_id,
                "faculty_id": faculty_id,
                "course_code": course_code,
                "room_number": room_number or "Not specified",
                "proximity_uuid": proximity_uuid,  # Same UUID for BLE broadcasting
                "timestamp": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + 
                    timedelta(minutes=settings.QR_CODE_EXPIRY_MINUTES)).isoformat()
            }
            
            # 2. Encrypt the data
            encrypted_data = self._encrypt_data(json.dumps(session_data))
            
            # 3. Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium error correction for better reliability
                box_size=10,
                border=4,
            )
            qr.add_data(encrypted_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 4. Save QR code
            filename = f"session_{session_id}.png"
            img_path = os.path.join(self.qr_path, filename)
            img.save(img_path)
            
            # Add these debug lines:
            print(f"QR code saved to: {img_path}")
            print(f"QR image URL: static/qr_codes/{filename}")
            print(f"File exists: {os.path.exists(img_path)}")
            print(f"File size: {os.path.getsize(img_path) if os.path.exists(img_path) else 'N/A'}")
            logger.info(f"Generated QR code for session {session_id}")
            
            # 5. Return data and image URL
            # In generate_session_qr method, update the image_url construction:
            return {
                "session_id": session_id,
                "encrypted_data": encrypted_data,
                "image_url": f"/static/qr_codes/{filename}",  # Keep the leading slash for consistency
                "expires_at": session_data["expires_at"],
                "proximityUuid": proximity_uuid  # Add this to ensure it's in the response
            }
        except Exception as e:
            logger.error(f"Error generating QR code: {str(e)}")
            raise RuntimeError(f"Failed to generate QR code: {str(e)}")
    
    def refresh_session_qr(
        self, 
        session_id: str, 
        faculty_id: str, 
        course_code: str, 
        room_number: str, 
        proximity_uuid: str
    ) -> Dict[str, Any]:
        """Refresh an existing QR code for a session
        
        Creates a new QR code with updated expiry time
        """
        # Clean up the old QR code if it exists
        self._remove_old_qr(session_id)
        
        # Generate new QR code
        return self.generate_session_qr(
            session_id, faculty_id, course_code, room_number, proximity_uuid
        )
    
    def verify_qr_data(self, encrypted_data: str) -> Dict[str, Any]:
        """Verify QR code data
        
        Decrypts and verifies the QR code data
        """
        try:
            # 1. Decrypt data
            decrypted_data = self._decrypt_data(encrypted_data)
            session_data = json.loads(decrypted_data)
            
            # 2. Check expiry
            expires_at = datetime.fromisoformat(session_data["expires_at"])
            if datetime.utcnow() > expires_at:
                logger.warning(f"QR code has expired for session {session_data.get('session_id', 'unknown')}")
                return {"valid": False, "error": "QR code has expired"}
            
            # 3. Return session data
            logger.info(f"Successfully verified QR code for session {session_data.get('session_id', 'unknown')}")
            return {"valid": True, "data": session_data}
            
        except Exception as e:
            logger.error(f"Error verifying QR code: {str(e)}")
            return {"valid": False, "error": str(e)}
    
    def _encrypt_data(self, data: str) -> str:
        """Encrypt data using Fernet symmetric encryption"""
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return encrypted_data.decode()
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            raise ValueError(f"Failed to encrypt data: {str(e)}")
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data using Fernet symmetric encryption"""
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption error: {str(e)}")
            raise ValueError(f"Failed to decrypt data: {str(e)}")
    
    def _remove_old_qr(self, session_id: str) -> None:
        """Remove old QR code file if it exists"""
        try:
            filename = f"session_{session_id}.png"
            file_path = os.path.join(self.qr_path, filename)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Removed old QR code for session {session_id}")
        except Exception as e:
            logger.warning(f"Failed to remove old QR code: {str(e)}")

    def cleanup_expired_qr_codes(self) -> int:
        """Clean up expired QR code files
        
        Returns the number of files removed
        """
        try:
            # Get all QR code files
            count = 0
            for filename in os.listdir(self.qr_path):
                if filename.startswith("session_") and filename.endswith(".png"):
                    file_path = os.path.join(self.qr_path, filename)
                    
                    # Check file age
                    file_time = os.path.getmtime(file_path)
                    file_datetime = datetime.fromtimestamp(file_time)
                    
                    # Calculate cutoff time based on expiry minutes
                    expiry_minutes = settings.QR_CODE_EXPIRY_MINUTES
                    cutoff_time = datetime.now() - timedelta(minutes=expiry_minutes + 5)
                    
                    # If file is older than cutoff time, remove it
                    if file_datetime < cutoff_time:
                        os.remove(file_path)
                        count += 1
                        logger.info(f"Removed expired QR code file: {filename}")
            
            logger.info(f"Cleaned up {count} expired QR code files")
            return count
        except Exception as e:
            logger.error(f"Error cleaning up QR codes: {str(e)}")
            return 0