"""
User Schemas
============

Pydantic schemas for user requests and responses.

Author: Prior Auth AI Team
Version: 1.0.0
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator

from backend.models import UserRole, UserStatus


class UserBase(BaseModel):
    """Base user schema with common fields."""
    
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class UserCreate(UserBase):
    """Schema for creating a new user."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    first_name: str = Field(..., max_length=100, description="First name")
    last_name: str = Field(..., max_length=100, description="Last name")
    role: UserRole = Field(default=UserRole.STAFF, description="User role")
    clinic_id: Optional[str] = Field(None, description="Clinic ID")
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password meets strength requirements."""
        from backend.core.security import validate_password_strength
        validate_password_strength(v)
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
                "first_name": "John",
                "last_name": "Doe",
                "role": "staff",
                "clinic_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class UserUpdate(UserBase):
    """Schema for updating user information."""
    
    phone: Optional[str] = Field(None, max_length=20)
    preferences: Optional[dict] = Field(None, description="User preferences")
    
    class Config:
        schema_extra = {
            "example": {
                "first_name": "Jane",
                "last_name": "Smith",
                "phone": "+1-555-123-4567",
                "preferences": {
                    "email_notifications": True,
                    "theme": "dark"
                }
            }
        }


class UserResponse(UserBase):
    """Schema for user response."""
    
    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="Email address")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole = Field(..., description="User role")
    status: UserStatus = Field(..., description="Account status")
    clinic_id: Optional[str] = Field(None, description="Clinic ID")
    is_active: bool = Field(..., description="Whether user is active")
    mfa_enabled: bool = Field(..., description="Whether MFA is enabled")
    email_verified: bool = Field(..., description="Whether email is verified")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    preferences: Optional[dict] = Field(None, description="User preferences")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1-555-123-4567",
                "role": "staff",
                "status": "active",
                "clinic_id": "clinic-uuid",
                "is_active": True,
                "mfa_enabled": False,
                "email_verified": True,
                "last_login_at": "2026-01-14T10:30:00Z",
                "preferences": {"email_notifications": True},
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-14T10:30:00Z"
            }
        }


class UserListResponse(BaseModel):
    """Schema for paginated user list response."""
    
    users: list[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Users per page")
    
    class Config:
        schema_extra = {
            "example": {
                "users": [],
                "total": 25,
                "page": 1,
                "per_page": 20
            }
        }