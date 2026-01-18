"""
Security Tests
==============

Test authentication, authorization, encryption, and security utilities.

Author: Prior Auth AI Team
Version: 1.0.0
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt

from backend.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    encrypt_phi,
    decrypt_phi,
    generate_api_key,
    validate_password_strength,
)
from backend.core.config import settings
from backend.core.exceptions import AuthenticationError, ValidationError


@pytest.mark.unit
@pytest.mark.security
class TestPasswordHashing:
    """Test password hashing functionality."""
    
    def test_password_hashing(self):
        """Test password hashing."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # Bcrypt prefix
    
    def test_password_verification_success(self):
        """Test successful password verification."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_verification_failure(self):
        """Test failed password verification."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password("WrongPassword", hashed) is False
    
    def test_same_password_different_hashes(self):
        """Test that same password generates different hashes."""
        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different due to random salt
        assert hash1 != hash2
        
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


@pytest.mark.unit
@pytest.mark.security
class TestPasswordStrength:
    """Test password strength validation."""
    
    def test_strong_password(self):
        """Test that strong password passes validation."""
        strong_password = "MyStr0ng!Password123"
        
        # Should not raise exception
        validate_password_strength(strong_password)
    
    def test_weak_password_too_short(self):
        """Test that short password fails validation."""
        with pytest.raises(ValidationError) as exc:
            validate_password_strength("Short1!")
        
        assert "at least 8 characters" in str(exc.value)
    
    def test_weak_password_no_uppercase(self):
        """Test that password without uppercase fails."""
        with pytest.raises(ValidationError) as exc:
            validate_password_strength("mypassword123!")
        
        assert "uppercase letter" in str(exc.value)
    
    def test_weak_password_no_lowercase(self):
        """Test that password without lowercase fails."""
        with pytest.raises(ValidationError) as exc:
            validate_password_strength("MYPASSWORD123!")
        
        assert "lowercase letter" in str(exc.value)
    
    def test_weak_password_no_digit(self):
        """Test that password without digit fails."""
        with pytest.raises(ValidationError) as exc:
            validate_password_strength("MyPassword!")
        
        assert "digit" in str(exc.value)
    
    def test_weak_password_no_special(self):
        """Test that password without special char fails."""
        with pytest.raises(ValidationError) as exc:
            validate_password_strength("MyPassword123")
        
        assert "special character" in str(exc.value)


@pytest.mark.unit
@pytest.mark.security
class TestJWTTokens:
    """Test JWT token creation and validation."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        user_id = "test-user-123"
        token = create_access_token(subject=user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = "test-user-123"
        token = create_refresh_token(subject=user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_valid_token(self):
        """Test decoding valid token."""
        user_id = "test-user-123"
        token = create_access_token(subject=user_id)
        
        payload = decode_token(token)
        
        assert payload is not None
        assert payload["sub"] == user_id
        assert "exp" in payload
    
    def test_decode_expired_token(self):
        """Test decoding expired token."""
        user_id = "test-user-123"
        
        # Create token that expired 1 hour ago
        expires_delta = timedelta(hours=-1)
        token = create_access_token(subject=user_id, expires_delta=expires_delta)
        
        with pytest.raises(AuthenticationError) as exc:
            decode_token(token)
        
        assert "expired" in str(exc.value).lower()
    
    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(AuthenticationError):
            decode_token(invalid_token)
    
    def test_token_contains_correct_algorithm(self):
        """Test that token uses correct algorithm."""
        user_id = "test-user-123"
        token = create_access_token(subject=user_id)
        
        # Decode without verification to check algorithm
        unverified = jwt.get_unverified_header(token)
        assert unverified["alg"] == settings.JWT_ALGORITHM
    
    def test_access_token_expiration_time(self):
        """Test that access token has correct expiration."""
        user_id = "test-user-123"
        token = create_access_token(subject=user_id)
        payload = decode_token(token)
        
        exp = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        
        # Should expire in approximately ACCESS_TOKEN_EXPIRE_MINUTES
        time_diff = (exp - now).total_seconds() / 60
        
        assert time_diff > 0
        assert time_diff <= settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES + 1
    
    def test_custom_token_expiration(self):
        """Test token with custom expiration."""
        user_id = "test-user-123"
        expires_delta = timedelta(hours=1)
        
        token = create_access_token(subject=user_id, expires_delta=expires_delta)
        payload = decode_token(token)
        
        exp = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        
        time_diff = (exp - now).total_seconds() / 3600  # in hours
        
        assert 0.95 < time_diff < 1.05  # Allow small variance


@pytest.mark.unit
@pytest.mark.security
class TestPHIEncryption:
    """Test PHI encryption and decryption."""
    
    def test_encrypt_phi(self):
        """Test PHI encryption."""
        sensitive_data = "Patient SSN: 123-45-6789"
        encrypted = encrypt_phi(sensitive_data)
        
        assert encrypted != sensitive_data
        assert len(encrypted) > 0
        assert isinstance(encrypted, str)
    
    def test_decrypt_phi(self):
        """Test PHI decryption."""
        sensitive_data = "Patient SSN: 123-45-6789"
        encrypted = encrypt_phi(sensitive_data)
        decrypted = decrypt_phi(encrypted)
        
        assert decrypted == sensitive_data
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test complete encryption/decryption cycle."""
        test_data = [
            "Simple text",
            "Special chars: !@#$%^&*()",
            "Numbers: 1234567890",
            "Unicode: 你好世界 🎉",
        ]
        
        for data in test_data:
            encrypted = encrypt_phi(data)
            decrypted = decrypt_phi(encrypted)
            assert decrypted == data
    
    def test_encrypt_empty_string(self):
        """Test encrypting empty string."""
        encrypted = encrypt_phi("")
        decrypted = decrypt_phi(encrypted)
        
        assert decrypted == ""
    
    def test_same_data_different_encryption(self):
        """Test that same data encrypts differently each time."""
        data = "Test data"
        encrypted1 = encrypt_phi(data)
        encrypted2 = encrypt_phi(data)
        
        # Fernet uses random IV, so encryptions should differ
        assert encrypted1 != encrypted2
        
        # But both should decrypt to same value
        assert decrypt_phi(encrypted1) == data
        assert decrypt_phi(encrypted2) == data


@pytest.mark.unit
@pytest.mark.security
class TestAPIKeys:
    """Test API key generation."""
    
    def test_generate_api_key(self):
        """Test API key generation."""
        api_key = generate_api_key()
        
        assert api_key is not None
        assert isinstance(api_key, str)
        assert len(api_key) >= 32
    
    def test_api_keys_unique(self):
        """Test that generated API keys are unique."""
        keys = [generate_api_key() for _ in range(100)]
        
        # All keys should be unique
        assert len(keys) == len(set(keys))
    
    def test_api_key_format(self):
        """Test API key format."""
        api_key = generate_api_key()
        
        # Should be alphanumeric
        assert api_key.isalnum()


@pytest.mark.unit
@pytest.mark.security
class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter can be initialized."""
        from backend.core.security import RateLimiter
        
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        
        assert limiter.max_requests == 10
        assert limiter.window_seconds == 60
    
    def test_rate_limit_allows_under_limit(self):
        """Test that requests under limit are allowed."""
        from backend.core.security import RateLimiter
        
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        identifier = "test-user"
        
        # First 5 requests should be allowed
        for _ in range(5):
            assert limiter.check_rate_limit(identifier) is True
    
    def test_rate_limit_blocks_over_limit(self):
        """Test that requests over limit are blocked."""
        from backend.core.security import RateLimiter
        
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        identifier = "test-user"
        
        # Use up the limit
        for _ in range(5):
            limiter.check_rate_limit(identifier)
        
        # 6th request should be blocked
        assert limiter.check_rate_limit(identifier) is False
    
    def test_rate_limit_separate_identifiers(self):
        """Test that different identifiers have separate limits."""
        from backend.core.security import RateLimiter
        
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # User 1 uses their limit
        for _ in range(5):
            limiter.check_rate_limit("user1")
        
        # User 2 should still be allowed
        assert limiter.check_rate_limit("user2") is True


@pytest.mark.security
class TestSecurityHeaders:
    """Test security header generation."""
    
    def test_get_security_headers(self):
        """Test security headers generation."""
        from backend.core.security import get_security_headers
        
        headers = get_security_headers()
        
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Strict-Transport-Security" in headers
        assert "Content-Security-Policy" in headers
    
    def test_security_header_values(self):
        """Test that security headers have correct values."""
        from backend.core.security import get_security_headers
        
        headers = get_security_headers()
        
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert "max-age" in headers["Strict-Transport-Security"]