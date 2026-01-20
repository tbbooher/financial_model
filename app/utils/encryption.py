"""
Family Office Platform - Encryption Utilities

Provides secure encryption and decryption services for sensitive financial data
using AES-256 encryption with PBKDF2 key derivation.
"""

import os
import base64
import hashlib
import secrets
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from app.utils.exceptions import ConfigurationError


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data.

    Uses Fernet symmetric encryption (AES-128-CBC) with PBKDF2 key derivation.
    Suitable for encrypting account numbers, SSNs, and other sensitive data.
    """

    def __init__(self, password: bytes = None, salt: bytes = None):
        """
        Initialize the encryption service.

        Args:
            password: Encryption password (defaults to ENCRYPTION_KEY env var)
            salt: Salt for key derivation (defaults to fixed salt, use random in production)
        """
        if password is None:
            env_key = os.environ.get('ENCRYPTION_KEY')
            if not env_key:
                raise ConfigurationError(
                    "ENCRYPTION_KEY environment variable is not set",
                    config_key='ENCRYPTION_KEY'
                )
            password = env_key.encode()

        if salt is None:
            # In production, use a proper random salt stored securely
            salt = os.environ.get('ENCRYPTION_SALT', 'family_office_salt_v1').encode()

        self._salt = salt
        self._cipher_suite = self._create_cipher(password)

    def _create_cipher(self, password: bytes) -> Fernet:
        """
        Create Fernet cipher with derived key.

        Args:
            password: Password bytes for key derivation

        Returns:
            Fernet cipher instance
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)

    def encrypt(self, data: str) -> str:
        """
        Encrypt a string value.

        Args:
            data: Plain text string to encrypt

        Returns:
            Base64 encoded encrypted string
        """
        if not data:
            return data

        encrypted = self._cipher_suite.encrypt(data.encode('utf-8'))
        return encrypted.decode('utf-8')

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt an encrypted string value.

        Args:
            encrypted_data: Base64 encoded encrypted string

        Returns:
            Decrypted plain text string

        Raises:
            ValueError: If decryption fails (invalid token or corrupted data)
        """
        if not encrypted_data:
            return encrypted_data

        try:
            decrypted = self._cipher_suite.decrypt(encrypted_data.encode('utf-8'))
            return decrypted.decode('utf-8')
        except InvalidToken:
            raise ValueError("Failed to decrypt data: invalid token or corrupted data")

    def encrypt_account_number(self, account_number: str) -> str:
        """
        Encrypt an account number with additional masking info.

        Args:
            account_number: Plain account number

        Returns:
            Encrypted account number
        """
        return self.encrypt(account_number)

    def decrypt_account_number(self, encrypted_account: str) -> str:
        """
        Decrypt an account number.

        Args:
            encrypted_account: Encrypted account number

        Returns:
            Decrypted account number
        """
        return self.decrypt(encrypted_account)

    def mask_account_number(self, account_number: str, visible_chars: int = 4) -> str:
        """
        Mask an account number, showing only last N characters.

        Args:
            account_number: Full account number
            visible_chars: Number of characters to show at end

        Returns:
            Masked account number (e.g., "****1234")
        """
        if not account_number or len(account_number) <= visible_chars:
            return account_number

        masked_length = len(account_number) - visible_chars
        return '*' * masked_length + account_number[-visible_chars:]

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """
        Generate a cryptographically secure random token.

        Args:
            length: Length of token in bytes (default 32)

        Returns:
            URL-safe base64 encoded token
        """
        return secrets.token_urlsafe(length)

    @staticmethod
    def hash_value(value: str, salt: str = None) -> str:
        """
        Create a one-way hash of a value (useful for comparison without storing plain text).

        Args:
            value: Value to hash
            salt: Optional salt (generates random if not provided)

        Returns:
            Hashed value with salt prepended
        """
        if salt is None:
            salt = secrets.token_hex(16)

        salted_value = (salt + value).encode('utf-8')
        hash_digest = hashlib.sha256(salted_value).hexdigest()
        return f"{salt}:{hash_digest}"

    @staticmethod
    def verify_hash(value: str, hashed_value: str) -> bool:
        """
        Verify a value against its hash.

        Args:
            value: Plain text value to verify
            hashed_value: Previously hashed value

        Returns:
            True if value matches hash, False otherwise
        """
        try:
            salt, _ = hashed_value.split(':')
            expected_hash = EncryptionService.hash_value(value, salt)
            return secrets.compare_digest(expected_hash, hashed_value)
        except ValueError:
            return False


def get_encryption_service() -> EncryptionService:
    """
    Factory function to get configured encryption service.

    Returns:
        Configured EncryptionService instance
    """
    return EncryptionService()
