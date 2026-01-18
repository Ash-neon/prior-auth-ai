"""
Configuration Tests
===================

Test configuration loading and environment variable handling.

Author: Prior Auth AI Team
Version: 1.0.0
"""

import pytest
from backend.core.config import Settings


class TestSettings:
    """Test configuration settings."""
    
    def test_settings_initialization(self):
        """Test that settings can be initialized."""
        settings = Settings()
        
        assert settings.APP_NAME is not None
        assert settings.DATABASE_URL is not None
        assert settings.SECRET_KEY is not None
    
    def test_debug_mode_default(self):
        """Test default debug mode."""
        settings = Settings()
        
        # Should be True in development
        assert isinstance(settings.DEBUG, bool)
    
    def test_database_url_format(self):
        """Test database URL format."""
        settings = Settings()
        
        assert settings.DATABASE_URL.startswith("postgresql://")
        assert "priorauth" in settings.DATABASE_URL
    
    def test_redis_url_format(self):
        """Test Redis URL format."""
        settings = Settings()
        
        assert settings.REDIS_URL.startswith("redis://")
    
    def test_cors_origins(self):
        """Test CORS origins configuration."""
        settings = Settings()
        
        assert isinstance(settings.CORS_ORIGINS, list)
        assert len(settings.CORS_ORIGINS) > 0
    
    def test_jwt_settings(self):
        """Test JWT configuration."""
        settings = Settings()
        
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS > 0
    
    def test_security_settings(self):
        """Test security configuration."""
        settings = Settings()
        
        assert len(settings.SECRET_KEY) >= 32
        assert settings.ENCRYPTION_KEY is not None
    
    def test_rate_limiting_settings(self):
        """Test rate limiting configuration."""
        settings = Settings()
        
        assert settings.RATE_LIMIT_PER_MINUTE > 0
        assert settings.RATE_LIMIT_PER_HOUR > 0
    
    def test_file_upload_settings(self):
        """Test file upload configuration."""
        settings = Settings()
        
        assert settings.MAX_UPLOAD_SIZE_MB > 0
        assert isinstance(settings.ALLOWED_UPLOAD_EXTENSIONS, list)
        assert "pdf" in settings.ALLOWED_UPLOAD_EXTENSIONS


class TestEnvironmentVariables:
    """Test environment variable handling."""
    
    def test_required_variables_present(self):
        """Test that required environment variables are set."""
        settings = Settings()
        
        # These should always be present
        required = [
            "DATABASE_URL",
            "SECRET_KEY",
            "REDIS_URL"
        ]
        
        for var in required:
            assert getattr(settings, var) is not None
    
    def test_optional_variables_have_defaults(self):
        """Test that optional variables have sensible defaults."""
        settings = Settings()
        
        # These should have defaults
        assert settings.APP_NAME is not None
        assert settings.LOG_LEVEL is not None
        assert settings.CORS_ORIGINS is not None


class TestFeatureFlags:
    """Test feature flag configuration."""
    
    def test_feature_flags_type(self):
        """Test that feature flags are boolean."""
        settings = Settings()
        
        assert isinstance(settings.ENABLE_WEB_SEARCH, bool)
        assert isinstance(settings.ENABLE_AI_EXTRACTION, bool)
        assert isinstance(settings.ENABLE_EMAIL_NOTIFICATIONS, bool)
    
    def test_feature_flags_defaults(self):
        """Test default feature flag values."""
        settings = Settings()
        
        # AI extraction should be enabled by default
        assert settings.ENABLE_AI_EXTRACTION is True


@pytest.mark.unit
class TestConfigValidation:
    """Test configuration validation."""
    
    def test_secret_key_length(self):
        """Test secret key has minimum length."""
        settings = Settings()
        
        assert len(settings.SECRET_KEY) >= 32
    
    def test_database_pool_settings(self):
        """Test database connection pool settings."""
        settings = Settings()
        
        assert settings.DB_POOL_SIZE > 0
        assert settings.DB_MAX_OVERFLOW > 0
        assert settings.DB_POOL_SIZE + settings.DB_MAX_OVERFLOW <= 50
    
    def test_celery_concurrency(self):
        """Test Celery worker concurrency setting."""
        settings = Settings()
        
        assert settings.CELERY_WORKER_CONCURRENCY > 0
        assert settings.CELERY_WORKER_CONCURRENCY <= 16