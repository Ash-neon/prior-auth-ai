"""
Provider Pydantic Schemas

Request/response schemas for Provider API endpoints.

Author: Prior Auth AI Team
Version: 1.0.0
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator

from backend.models.provider import ProviderType, ProviderSpecialty


# Base schemas
class ProviderBase(BaseModel):
    """Base schema for provider with common fields."""
    
    npi: str = Field(..., min_length=10, max_length=10, description="National Provider Identifier")
    provider_type: ProviderType
    specialty: Optional[ProviderSpecialty] = None
    subspecialties: List[str] = Field(default_factory=list)
    
    # Individual provider (for physicians, NPs, PAs)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    credentials: Optional[str] = Field(None, max_length=50)
    
    # Organization (for facilities)
    organization_name: Optional[str] = Field(None, max_length=255)
    doing_business_as: Optional[str] = Field(None, max_length=255)
    
    # Contact
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    fax: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=2)
    zip_code: Optional[str] = Field(None, max_length=10)
    country: str = Field(default="US", max_length=2)
    
    # Practice info
    accepts_new_patients: bool = Field(default=True)
    hospital_affiliations: List[str] = Field(default_factory=list)
    languages_spoken: List[str] = Field(default_factory=list)
    insurance_networks: List[str] = Field(default_factory=list)
    
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("npi")
    @classmethod
    def validate_npi(cls, v):
        """Validate NPI format (10 digits)."""
        if not v.isdigit():
            raise ValueError("NPI must contain only digits")
        if len(v) != 10:
            raise ValueError("NPI must be exactly 10 digits")
        return v
    
    @field_validator("state")
    @classmethod
    def validate_state(cls, v):
        """Validate state code format."""
        if v and len(v) != 2:
            raise ValueError("State must be 2-letter code")
        return v.upper() if v else v


class ProviderCreate(ProviderBase):
    """Schema for creating a new provider."""
    
    tax_id: Optional[str] = Field(None, max_length=20)
    license_number: Optional[str] = Field(None, max_length=50)
    license_state: Optional[str] = Field(None, max_length=2)
    dea_number: Optional[str] = Field(None, max_length=20)
    external_id: Optional[str] = Field(None, max_length=100)
    
    # Credentialing
    board_certified: bool = Field(default=False)
    board_certification_date: Optional[date] = None
    board_certification_expiry: Optional[date] = None
    medical_school: Optional[str] = Field(None, max_length=255)
    graduation_year: Optional[int] = Field(None, ge=1900, le=2100)
    
    license_active: bool = Field(default=True)
    license_expiry_date: Optional[date] = None


class ProviderUpdate(BaseModel):
    """Schema for updating an existing provider."""
    
    provider_type: Optional[ProviderType] = None
    specialty: Optional[ProviderSpecialty] = None
    subspecialties: Optional[List[str]] = None
    
    # Individual provider
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    credentials: Optional[str] = Field(None, max_length=50)
    
    # Organization
    organization_name: Optional[str] = Field(None, max_length=255)
    doing_business_as: Optional[str] = Field(None, max_length=255)
    
    # Contact
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    fax: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=2)
    zip_code: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = Field(None, max_length=2)
    
    # Practice info
    accepts_new_patients: Optional[bool] = None
    hospital_affiliations: Optional[List[str]] = None
    languages_spoken: Optional[List[str]] = None
    insurance_networks: Optional[List[str]] = None
    
    # Identifiers
    tax_id: Optional[str] = Field(None, max_length=20)
    license_number: Optional[str] = Field(None, max_length=50)
    license_state: Optional[str] = Field(None, max_length=2)
    dea_number: Optional[str] = Field(None, max_length=20)
    
    # Credentialing
    board_certified: Optional[bool] = None
    board_certification_date: Optional[date] = None
    board_certification_expiry: Optional[date] = None
    medical_school: Optional[str] = Field(None, max_length=255)
    graduation_year: Optional[int] = Field(None, ge=1900, le=2100)
    
    license_active: Optional[bool] = None
    license_expiry_date: Optional[date] = None
    
    # Status
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(extra="forbid")


# Response schemas
class ProviderResponse(ProviderBase):
    """Schema for provider response."""
    
    id: UUID
    tax_id: Optional[str]
    license_number: Optional[str]
    license_state: Optional[str]
    dea_number: Optional[str]
    external_id: Optional[str]
    
    # Credentialing
    board_certified: bool
    board_certification_date: Optional[date]
    board_certification_expiry: Optional[date]
    medical_school: Optional[str]
    graduation_year: Optional[int]
    
    license_active: bool
    license_expiry_date: Optional[date]
    
    # Performance metrics
    total_pa_requests: int
    approved_pa_count: int
    denied_pa_count: int
    average_approval_time_days: Optional[float]
    
    # Status
    is_active: bool
    is_verified: bool
    verification_date: Optional[datetime]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    full_name: Optional[str] = Field(None, description="Full name for individuals")
    display_name: str = Field(description="Display name")
    full_address: Optional[str] = Field(None, description="Formatted address")
    approval_rate: Optional[float] = Field(None, description="PA approval rate")
    needs_credentialing_update: bool = Field(
        description="Whether credentials need updating"
    )
    
    model_config = ConfigDict(from_attributes=True)


class ProviderSummaryResponse(BaseModel):
    """Minimal provider info for lists."""
    
    id: UUID
    npi: str
    display_name: str
    provider_type: ProviderType
    specialty: Optional[ProviderSpecialty]
    city: Optional[str]
    state: Optional[str]
    is_active: bool
    is_verified: bool
    approval_rate: Optional[float]
    
    model_config = ConfigDict(from_attributes=True)


class ProviderListResponse(BaseModel):
    """Schema for paginated provider list response."""
    
    items: List[ProviderSummaryResponse]
    total: int = Field(..., description="Total number of providers matching filters")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum records returned")
    
    model_config = ConfigDict(from_attributes=True)


class ProviderStatsResponse(BaseModel):
    """Schema for provider statistics."""
    
    provider_id: UUID
    total_pa_requests: int
    approved_count: int
    denied_count: int
    pending_count: int
    approval_rate: float
    average_approval_time_days: Optional[float]
    by_pa_type: Dict[str, int]
    by_urgency: Dict[str, int]
    monthly_trend: List[Dict[str, Any]]


class ProviderVerifyRequest(BaseModel):
    """Schema for provider verification request."""
    
    verification_notes: Optional[str] = None


class ProviderVerifyResponse(BaseModel):
    """Schema for provider verification response."""
    
    provider_id: UUID
    is_verified: bool
    verification_date: datetime
    verified_by_id: UUID
    message: str