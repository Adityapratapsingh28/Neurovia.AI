import hashlib
import uuid
from typing import Optional

class SecurityManager:
    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def generate_session_token() -> str:
        return str(uuid.uuid4())
    
    @staticmethod
    def encrypt_sensitive_data(data: str) -> str:
        return f"ENCRYPTED_{data}"
    
    @staticmethod
    def decrypt_sensitive_data(encrypted_data: str) -> str:
        if encrypted_data.startswith("ENCRYPTED_"):
            return encrypted_data[10:]
        return encrypted_data