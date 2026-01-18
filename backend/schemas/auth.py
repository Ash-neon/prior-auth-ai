"""
Authentication Schemas
======================

Pydantic schemas for authentication requests and responses.

Author: Prior Auth AI Team
Version: 1.0.0
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator


class LoginRequest(BaseModel):
    """Login request schema."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")
    mfa_code: Optional[str] = Field(None, max_length=6, description="MFA code if enabled")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123!",
                "mfa_code": "123456"
            }
        }


class LoginResponse(BaseModel):
    """Login response schema."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: dict = Field(..., description="User information")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "role": "staff"
                }
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    
    refresh_token: str = Field(..., description="Refresh token")
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class RefreshTokenResponse(BaseModel):
    """Refresh token response schema."""
    
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class ForgotPasswordRequest(BaseModel):
    """Forgot password request schema."""
    
    email: EmailStr = Field(..., description="User email address")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class ForgotPasswordResponse(BaseModel):
    """Forgot password response schema."""
    
    message: str = Field(..., description="Success message")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "If an account exists with this email, a password reset link has been sent."
            }
        }


class ResetPasswordRequest(BaseModel):
    """Reset password request schema."""
    
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(
        ...,
        min_length=8,
        description="New password (min 8 characters)"
    )
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password meets strength requirements."""
        from backend.core.security import validate_password_strength
        validate_password_strength(v)
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "token": "reset_token_here",
                "new_password": "NewSecurePassword123!"
            }
        }


class ResetPasswordResponse(BaseModel):
    """Reset password response schema."""
    
    message: str = Field(..., description="Success message")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Password has been reset successfully."
            }
        }


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        description="New password (min 8 characters)"
    )
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password meets strength requirements."""
        from backend.core.security import validate_password_strength
        validate_password_strength(v)
        return v
    
    @validator('new_password')
    def passwords_different(cls, v, values):
        """Ensure new password is different from current."""
        if 'current_password' in values and v == values['current_password']:
            raise ValueError('New password must be different from current password')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePassword123!"
            }
        }


class ChangePasswordResponse(BaseModel):
    """Change password response schema."""
    
    message: str = Field(..., description="Success message")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Password changed successfully."
            }
        }


class LogoutResponse(BaseModel):
    """Logout response schema."""
    
    message: str = Field(..., description="Success message")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Logged out successfully."
            }
        }