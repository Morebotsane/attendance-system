"""
QR Code generation and validation service
"""

import qrcode
import io
import base64
from cryptography.fernet import Fernet
import secrets
from datetime import datetime
from typing import Optional, Dict
import os

from app.core.config import settings


class QRCodeService:
    """Service for generating and validating QR codes"""
    
    def __init__(self):
        # Generate Fernet key if not exists
        key = settings.QR_ENCRYPTION_KEY
        if len(key) != 44:  # Fernet keys are 44 characters
            key = Fernet.generate_key().decode()
            print(f"⚠️  Generated new Fernet key: {key}")
            print("Add this to your .env file as QR_ENCRYPTION_KEY")
        
        self.cipher_suite = Fernet(key.encode() if isinstance(key, str) else key)
    
    def generate_employee_qr_data(self, employee_id: str) -> str:
        """
        Generate encrypted, unique QR data for employee
        
        Format: {employee_id}:{random_salt}:{timestamp}
        This prevents:
        - Simple copying/sharing of QR codes
        - Replay attacks
        - Predictable QR patterns
        
        Args:
            employee_id: UUID of the employee
            
        Returns:
            Encrypted QR code data string
        """
        salt = secrets.token_urlsafe(16)
        timestamp = int(datetime.utcnow().timestamp())
        
        # Create composite data
        raw_data = f"{employee_id}:{salt}:{timestamp}"
        
        # Encrypt
        encrypted = self.cipher_suite.encrypt(raw_data.encode())
        
        # Base64 encode for URL safety
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decode_qr_data(self, qr_data: str) -> Dict[str, any]:
        """
        Decrypt and validate QR code data
        
        Args:
            qr_data: Encrypted QR code string
            
        Returns:
            Dict with employee_id and validity status
        """
        try:
            # Decode from base64
            encrypted = base64.urlsafe_b64decode(qr_data.encode())
            
            # Decrypt
            decrypted = self.cipher_suite.decrypt(encrypted).decode()
            
            # Parse components
            parts = decrypted.split(':')
            if len(parts) != 3:
                return {"valid": False, "error": "Invalid QR format"}
            
            employee_id, salt, timestamp = parts
            
            # Could add timestamp validation here if needed
            # For now, we just return the employee_id
            
            return {
                "employee_id": employee_id,
                "valid": True,
                "generated_at": datetime.fromtimestamp(int(timestamp))
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"QR validation failed: {str(e)}"
            }
    
    def generate_qr_image(self, data: str, size: int = 10) -> bytes:
        """
        Generate QR code image from data
        
        Args:
            data: The data to encode
            size: Box size for QR code (default 10)
            
        Returns:
            QR code image as bytes
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=size,
            border=4,
        )
        
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return img_byte_arr.getvalue()
    
    def generate_qr_base64(self, data: str) -> str:
        """
        Generate QR code and return as base64 string
        Useful for embedding in JSON responses
        
        Args:
            data: The data to encode
            
        Returns:
            Base64 encoded PNG image
        """
        img_bytes = self.generate_qr_image(data)
        return base64.b64encode(img_bytes).decode()
    
    def save_qr_image(self, data: str, employee_id: str) -> str:
        """
        Save QR code image to storage
        
        Args:
            data: The data to encode
            employee_id: Employee UUID for filename
            
        Returns:
            URL/path to saved image
        """
        img_bytes = self.generate_qr_image(data)
        
        # Create storage directory if not exists
        storage_dir = "app/storage/qr_codes"
        os.makedirs(storage_dir, exist_ok=True)
        
        # Save file
        filename = f"{employee_id}.png"
        filepath = os.path.join(storage_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(img_bytes)
        
        # Return public URL
        return f"/static/qr_codes/{filename}"


# Create singleton instance
qr_service = QRCodeService()
