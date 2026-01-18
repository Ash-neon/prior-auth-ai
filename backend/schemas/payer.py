"""
Payer Pydantic Schemas

Request/response schemas for Payer API endpoints.

Author: Prior Auth AI Team
Version: 1.0.0
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator

from backend.models.payer import PayerType, SubmissionMethod


# Base schemas
class PayerBase(BaseModel):
    """Base schema for payer with common fields."""
    
    payer_id: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Standard payer ID"
    )
    name: str = Field(..., min_length=1, max_length=255)
    legal_name: Optional[str] = Field(None, max_length=255)
    payer_type: PayerType
    
    # Contact
    phone: Optional[str] = Field(None, max_length=20)
    fax: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)
    pa_portal_url: Optional[str] = Field(None, max_length=500)
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=2)
    zip_code: Optional[str] = Field(None, max_length=10)
    country: str = Field(default="US", max_length=2)
    
    # Submission requirements
    preferred_submission_method: SubmissionMethod = Field(
        default=SubmissionMethod.PORTAL
    )
    accepted_submission_methods: List[str] = Field(default_factory=list)
    requires_electronic_signature: bool = Field(default=False)
    accepts_rush_requests: bool = Field(default=False)
    
    # Processing times
    standard_processing_days: Optional[int] = Field(None, ge=1, le=90)
    urgent_processing_days: Optional[int] = Field(None, ge=1, le=30)
    expedited_processing_days: Optional[int] = Field(None, ge=1, le=7)
    
    # Required documentation
    required_documents: List[str] = Field(default_factory=list)
    optional_documents: List[str] = Field(default_factory=list)
    
    # Coverage
    covered_services: List[str] = Field(default_factory=list)
    medical_policies: Dict[str, Any] = Field(default_factory=dict)
    formulary_url: Optional[str] = Field(None, max_length=500)
    
    # Notes
    submission_notes: Optional[str] = None
    appeal_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("state")
    @classmethod
    def validate_state(cls, v):
        """Validate state code format."""
        if v and len(v) != 2:
            raise ValueError("State must be 2-letter code")
        return v.upper() if v else v


class PayerCreate(PayerBase):
    """Schema for creating a new payer."""
    
    external_id: Optional[str] = Field(None, max_length=100)
    
    # API integration
    has_api_integration: bool = Field(default=False)
    api_endpoint: Optional[str] = Field(None, max_length=500)
    api_version: Optional[str] = Field(None, max_length=20)
    api_documentation_url: Optional[str] = Field(None, max_length=500)
    requires_api_authentication: bool = Field(default=True)
    
    # Portal credentials (will be encrypted)
    portal_username: Optional[str] = Field(None, max_length=255)
    portal_password: Optional[str] = Field(
        None,
        max_length=255,
        description="Will be hashed before storage"
    )


class PayerUpdate(BaseModel):
    """Schema for updating an existing payer."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    legal_name: Optional[str] = Field(None, max_length=255)
    payer_type: Optional[PayerType] = None
    
    # Contact
    phone: Optional[str] = Field(None, max_length=20)
    fax: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)
    pa_portal_url: Optional[str] = Field(None, max_length=500)
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=2)
    zip_code: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = Field(None, max_length=2)
    
    # Submission requirements
    preferred_submission_method: Optional[SubmissionMethod] = None
    accepted_submission_methods: Optional[List[str]] = None
    requires_electronic_signature: Optional[bool] = None
    accepts_rush_requests: Optional[bool] = None
    
    # Processing times
    standard_processing_days: Optional[int] = Field(None, ge=1, le=90)
    urgent_processing_days: Optional[int] = Field(None, ge=1, le=30)
    expedited_processing_days: Optional[int] = Field(None, ge=1, le=7)
    
    # Required documentation
    required_documents: Optional[List[str]] = None
    optional_documents: Optional[List[str]] = None
    
    # Coverage
    covered_services: Optional[List[str]] = None
    medical_policies: Optional[Dict[str, Any]] = None
    formulary_url: Optional[str] = Field(None, max_length=500)
    
    # API integration
    has_api_integration: Optional[bool] = None
    api_endpoint: Optional[str] = Field(None, max_length=500)
    api_version: Optional[str] = Field(None, max_length=20)
    api_documentation_url: Optional[str] = Field(None, max_length=500)
    requires_api_authentication: Optional[bool] = None
    
    # Portal credentials
    portal_username: Optional[str] = Field(None, max_length=255)
    portal_password: Optional[str] = Field(None, max_length=255)
    
    # Status
    is_active: Optional[bool] = None
    accepts_new_submissions: Optional[bool] = None
    
    # Notes
    submission_notes: Optional[str] = None
    appeal_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(extra="forbid")


# Response schemas
class PayerResponse(PayerBase):
    """Schema for payer response."""
    
    id: UUID
    external_id: Optional[str]
    
    # API integration
    has_api_integration: bool
    api_endpoint: Optional[str]
    api_version: Optional[str]
    api_documentation_url: Optional[str]
    requires_api_authentication: bool
    
    # Performance metrics
    total_submissions: int
    approved_count: int
    denied_count: int
    average_approval_time_days: Optional[float]
    
    # Status
    is_active: bool
    accepts_new_submissions: bool
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_verified_at: Optional[datetime]
    
    # Computed properties
    full_address: Optional[str] = Field(None, description="Formatted address")
    approval_rate: Optional[float] = Field(None, description="Approval rate")
    is_configured_for_api: bool = Field(
        description="Ready for API submissions"
    )
    is_configured_for_portal: bool = Field(
        description="Ready for portal submissions"
    )
    
    model_config = ConfigDict(from_attributes=True)


class PayerSummaryResponse(BaseModel):
    """Minimal payer info for lists."""
    
    id: UUID
    payer_id: str
    name: str
    payer_type: PayerType
    preferred_submission_method: SubmissionMethod
    is_active: bool
    accepts_new_submissions: bool
    approval_rate: Optional[float]
    
    model_config = ConfigDict(from_attributes=True)


class PayerListResponse(BaseModel):
    """Schema for paginated payer list response."""
    
    items: List[PayerSummaryResponse]
    total: int = Field(..., description="Total number of payers matching filters")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum records returned")
    
    model_config = ConfigDict(from_attributes=True)


class PayerStatsResponse(BaseModel):
    """Schema for payer statistics."""
    
    payer_id: UUID
    total_submissions: int
    approved_count: int
    denied_count: int
    pending_count: int
    approval_rate: float
    average_approval_time_days: Optional[float]
    by_pa_type: Dict[str, int]
    by_urgency: Dict[str, int]
    monthly_trend: List[Dict[str, Any]]


class PayerRequirements(BaseModel):
    """Schema for payer PA requirements."""
    
    payer_id: UUID
    payer_name: str
    pa_type: str
    required_documents: List[str]
    optional_documents: List[str]
    medical_necessity_criteria: Dict[str, Any]
    submission_method: SubmissionMethod
    estimated_processing_days: int
    special_instructions: Optional[str]


class PayerFormularyCheck(BaseModel):
    """Schema for checking if medication is on formulary."""
    
    payer_id: UUID
    medication_ndc: str
    medication_name: str


class PayerFormularyResponse(BaseModel):
    """Schema for formulary check response."""
    
    payer_id: UUID
    medication_ndc: str
    medication_name: str
    is_on_formulary: bool
    tier: Optional[str]
    requires_pa: bool
    requires_step_therapy: bool
    alternatives: List[str] = Field(default_factory=list)
    notes: Optional[str]