"""
Encryption service for sensitive data like API tokens
"""

import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import settings


class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self):
        self._fernet = self._create_fernet()
    
    def _create_fernet(self) -> Fernet:
        """Create Fernet instance using the secret key"""
        # Use the secret key from settings to derive encryption key
        password = settings.secret_key.encode()
        salt = self._get_or_create_salt()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)
    
    def _get_or_create_salt(self) -> bytes:
        """Get existing salt or create a new one"""
        import os
        from pathlib import Path
        
        # Store salt in data directory
        salt_file = Path(settings.data_dir) / "encryption_salt.bin"
        
        if salt_file.exists():
            return salt_file.read_bytes()
        else:
            # Create data directory if it doesn't exist
            salt_file.parent.mkdir(parents=True, exist_ok=True)
            # Generate secure random salt
            salt = os.urandom(16)
            salt_file.write_bytes(salt)
            return salt
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string and return base64 encoded result"""
        if not data:
            return ""
        
        encrypted_data = self._fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: str) -> Optional[str]:
        """Decrypt base64 encoded encrypted data"""
        if not encrypted_data:
            return None
        
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self._fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception:
            # Return None if decryption fails
            return None


# Global instance
encryption_service = EncryptionService()