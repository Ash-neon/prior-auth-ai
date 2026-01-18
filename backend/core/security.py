"""
Security Module
===============

Handles authentication, password hashing, JWT tokens, and encryption.

Features:
- Password hashing with bcrypt
- JWT token generation and validation
- PHI encryption/decryption (AES-256)
- API key generation
- Security utilities

Author: Prior Auth AI Team
Version: 1.0.0
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
import secrets
import base64

from passlib.context import CryptContext
from jose import JWTError, jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend

from core.config import settings
from core.logging import get_logger


logger = get_logger(__name__)


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# PHI encryption (uses Fernet symmetric encryption)
class PHIEncryption:
    """
    Handles encryption/decryption of PHI fields.
    Uses AES-256 via Fernet for symmetric encryption.
    """
    
    def __init__(self):
        """Initialize encryption with key from settings."""
        # Derive encryption key from settings
        if not settings.PHI_ENCRYPTION_KEY:
            raise ValueError("PHI_ENCRYPTION_KEY not set in configuration")
        
        # Use PBKDF2 to derive a proper Fernet key
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'priorauth_salt',  # In production, use unique salt per deployment
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(
            kdf.derive(settings.PHI_ENCRYPTION_KEY.encode())
        )
        
        self.fernet = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext PHI.
        
        Args:
            plaintext: The sensitive data to encrypt
            
        Returns:
            Base64-encoded encrypted data
        """
        if not plaintext:
            return ""
        
        try:
            encrypted = self.fernet.encrypt(plaintext.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt encrypted PHI.
        
        Args:
            encrypted: Base64-encoded encrypted data
            
        Returns:
            Decrypted plaintext
        """
        if not encrypted:
            return ""
        
        try:
            decoded = base64.b64decode(encrypted.encode())
            decrypted = self.fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise


# Global PHI encryption instance
phi_encryption = PHIEncryption()


# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password for storage.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


# JWT token utilities
def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in token (user_id, email, etc.)
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    # Encode token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    logger.debug(f"Created access token for user: {data.get('sub')}")
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Data to encode in token
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    
    # Set expiration (refresh tokens live longer)
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    # Encode token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"Token validation failed: {e}")
        raise


def verify_token_type(token: str, expected_type: str) -> bool:
    """
    Verify that a token is of the expected type.
    
    Args:
        token: JWT token string
        expected_type: Expected token type ("access" or "refresh")
        
    Returns:
        True if token type matches
    """
    try:
        payload = decode_token(token)
        return payload.get("type") == expected_type
    except JWTError:
        return False


# API key utilities
def generate_api_key() -> str:
    """
    Generate a secure API key.
    
    Returns:
        Random API key string
    """
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for storage.
    
    Args:
        api_key: Plain API key
        
    Returns:
        Hashed API key
    """
    return get_password_hash(api_key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """
    Verify an API key against its hash.
    
    Args:
        plain_key: Plain API key
        hashed_key: Hashed API key from database
        
    Returns:
        True if API key matches
    """
    return verify_password(plain_key, hashed_key)


# Request validation utilities
def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password meets security requirements.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"
    
    return True, None


# HIPAA security utilities
def generate_audit_id() -> str:
    """
    Generate a unique audit ID for tracking PHI access.
    
    Returns:
        Unique audit ID
    """
    return secrets.token_hex(16)


def sanitize_phi_for_logs(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove or redact PHI fields from data before logging.
    
    Args:
        data: Dictionary that may contain PHI
        
    Returns:
        Sanitized dictionary safe for logging
    """
    # List of field names that contain PHI
    phi_fields = {
        'ssn', 'social_security_number',
        'dob', 'date_of_birth',
        'first_name', 'last_name', 'name',
        'address', 'phone', 'email',
        'mrn', 'medical_record_number',
        'patient_name', 'patient_id'
    }
    
    sanitized = {}
    
    for key, value in data.items():
        if key.lower() in phi_fields:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_phi_for_logs(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_phi_for_logs(item) if isinstance(item, dict) else "[REDACTED]"
                for item in value
            ]
        else:
            sanitized[key] = value
    
    return sanitized


# Session security
class SessionManager:
    """
    Manages user sessions and token blacklisting.
    
    In production, this would use Redis for distributed session management.
    For now, we use an in-memory set (will be replaced in Phase 3).
    """
    
    def __init__(self):
        self._blacklisted_tokens = set()
    
    def blacklist_token(self, token: str) -> None:
        """
        Add a token to the blacklist (for logout).
        
        Args:
            token: JWT token to blacklist
        """
        # In production, store in Redis with TTL matching token expiration
        self._blacklisted_tokens.add(token)
        logger.info("Token blacklisted")
    
    def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if a token has been blacklisted.
        
        Args:
            token: JWT token to check
            
        Returns:
            True if token is blacklisted
        """
        return token in self._blacklisted_tokens
    
    def cleanup_expired_tokens(self) -> None:
        """
        Remove expired tokens from blacklist.
        
        Should be called periodically by a background task.
        """
        # In production, Redis TTL handles this automatically
        valid_tokens = set()
        
        for token in self._blacklisted_tokens:
            try:
                decode_token(token)
                valid_tokens.add(token)
            except JWTError:
                # Token expired, don't keep it
                pass
        
        self._blacklisted_tokens = valid_tokens


# Global session manager
session_manager = SessionManager()


# Rate limiting utilities (basic implementation)
class RateLimiter:
    """
    Simple in-memory rate limiter.
    
    In production, use Redis-based rate limiting.
    """
    
    def __init__(self):
        self._requests = {}  # key -> list of timestamps
    
    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, Optional[int]]:
        """
        Check if request is within rate limit.
        
        Args:
            key: Identifier (user_id, IP, etc.)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=window_seconds)
        
        # Get request history for this key
        if key not in self._requests:
            self._requests[key] = []
        
        # Remove old requests outside window
        self._requests[key] = [
            ts for ts in self._requests[key]
            if ts > cutoff
        ]
        
        # Check if under limit
        if len(self._requests[key]) < max_requests:
            self._requests[key].append(now)
            return True, None
        else:
            # Calculate retry_after
            oldest = min(self._requests[key])
            retry_after = int((oldest - cutoff).total_seconds()) + 1
            return False, retry_after


# Global rate limiter
rate_limiter = RateLimiter()


# CORS security
def get_cors_origins() -> list:
    """
    Get allowed CORS origins from configuration.
    
    Returns:
        List of allowed origin URLs
    """
    if settings.CORS_ORIGINS:
        if isinstance(settings.CORS_ORIGINS, str):
            return [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
        return settings.CORS_ORIGINS
    return []


# Security headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
}