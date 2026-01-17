"""
Encryption service for sensitive credentials using Fernet symmetric encryption.
"""
from cryptography.fernet import Fernet
import os
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class EncryptionService:
    """Handle encryption/decryption of sensitive credentials"""
    
    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize encryption service
        
        Args:
            key: Fernet key (32 url-safe base64-encoded bytes)
                 If None, loads from ENCRYPTION_KEY env var
        """
        if key is None:
            key_str = os.getenv("ENCRYPTION_KEY")
            if not key_str:
                raise ValueError(
                    "ENCRYPTION_KEY environment variable not set. "
                    "Generate a key with: python scripts/generate_encryption_key.py"
                )
            key = key_str.encode()
        
        try:
            self.fernet = Fernet(key)
        except Exception as e:
            raise ValueError(f"Invalid encryption key: {e}")
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string, return base64 encoded string
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64 encoded encrypted string
        """
        if not plaintext:
            return ""
        
        try:
            encrypted = self.fernet.encrypt(plaintext.encode())
            return encrypted.decode()  # Return as string for JSON storage
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt base64 encoded string, return plaintext
        
        Args:
            ciphertext: Encrypted string to decrypt
            
        Returns:
            Decrypted plaintext string
        """
        if not ciphertext:
            return ""
            
        try:
            decrypted = self.fernet.decrypt(ciphertext.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_dict(self, data: dict, sensitive_fields: Optional[list] = None) -> dict:
        """
        Encrypt specific fields in a dictionary
        
        Args:
            data: Dictionary to encrypt fields in
            sensitive_fields: List of field names to encrypt. If None, uses default list.
            
        Returns:
            Dictionary with encrypted sensitive fields
        """
        if sensitive_fields is None:
            sensitive_fields = ['password', 'token', 'private_key', 'secret', 'ssh_private_key']
        
        encrypted_data = data.copy()
        
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))
        
        return encrypted_data
    
    def decrypt_dict(self, data: dict, sensitive_fields: Optional[list] = None) -> dict:
        """
        Decrypt specific fields in a dictionary
        
        Args:
            data: Dictionary to decrypt fields in
            sensitive_fields: List of field names to decrypt. If None, uses default list.
            
        Returns:
            Dictionary with decrypted sensitive fields
        """
        if sensitive_fields is None:
            sensitive_fields = ['password', 'token', 'private_key', 'secret', 'ssh_private_key']
        
        decrypted_data = data.copy()
        
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = self.decrypt(decrypted_data[field])
                except Exception:
                    # Field might not be encrypted (backward compatibility)
                    logger.debug(f"Field '{field}' could not be decrypted, leaving as-is")
        
        return decrypted_data


def generate_key() -> str:
    """
    Generate a new Fernet key
    
    Returns:
        Base64 encoded Fernet key as string
    """
    return Fernet.generate_key().decode()


def rotate_encryption_key(
    old_key: bytes,
    new_key: bytes,
    encrypted_values: list
) -> list:
    """
    Rotate encryption keys for a list of encrypted values
    
    Args:
        old_key: Current encryption key
        new_key: New encryption key
        encrypted_values: List of encrypted strings
        
    Returns:
        List of values re-encrypted with new key
    """
    old_service = EncryptionService(old_key)
    new_service = EncryptionService(new_key)
    
    rotated_values = []
    for encrypted_value in encrypted_values:
        try:
            # Decrypt with old key
            decrypted = old_service.decrypt(encrypted_value)
            # Re-encrypt with new key
            re_encrypted = new_service.encrypt(decrypted)
            rotated_values.append(re_encrypted)
        except Exception as e:
            logger.error(f"Failed to rotate key for value: {e}")
            rotated_values.append(encrypted_value)  # Keep original
    
    return rotated_values
