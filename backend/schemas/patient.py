"""
Patient Pydantic Schemas

Request/response schemas for Patient API endpoints.

Author: Prior Auth AI Team
Version: 1.0.0
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator

from backend.models.patient import Gender


# Base schemas
class PatientBase(BaseModel):
    """Base schema for patient with common fields."""
    
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: date
    gender: Gender
    
    # Contact
    email: Optional[EmailStr] = None
    phone_primary: Optional[str] = Field(None, max_length=20)
    phone_secondary: Optional[str] = Field(None, max_length=20)
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=2)
    zip_code: Optional[str] = Field(None, max_length=10)
    country: str = Field(default="US", max_length=2)
    
    # Insurance - Primary
    insurance_primary_member_id: Optional[str] = Field(None, max_length=50)
    insurance_primary_group_number: Optional[str] = Field(None, max_length=50)
    insurance_primary_payer_name: Optional[str] = Field(None, max_length=200)
    insurance_primary_plan_name: Optional[str] = Field(None, max_length=200)
    insurance_primary_effective_date: Optional[date] = None
    insurance_primary_termination_date: Optional[date] = None
    
    # Insurance - Secondary
    insurance_secondary_member_id: Optional[str] = Field(None, max_length=50)
    insurance_secondary_group_number: Optional[str] = Field(None, max_length=50)
    insurance_secondary_payer_name: Optional[str] = Field(None, max_length=200)
    
    # Medical
    primary_diagnosis_codes: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    medical_history: Optional[str] = None
    
    # Emergency contact
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)
    
    # Preferences
    preferred_language: str = Field(default="en", max_length=10)
    communication_preferences: Dict[str, Any] = Field(default_factory=dict)
    
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v):
        """Ensure DOB is not in the future."""
        if v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v
    
    @field_validator("state")
    @classmethod
    def validate_state(cls, v):
        """Validate state code format."""
        if v and len(v) != 2:
            raise ValueError("State must be 2-letter code")
        return v.upper() if v else v


class PatientCreate(PatientBase):
    """Schema for creating a new patient."""
    
    mrn: Optional[str] = Field(None, max_length=50)
    external_id: Optional[str] = Field(None, max_length=100)
    ssn: Optional[str] = Field(
        None,
        max_length=11,
        description="SSN (will be encrypted)"
    )
    consent_to_treat: bool = Field(default=False)
    consent_to_share_info: bool = Field(default=False)


class PatientUpdate(BaseModel):
    """Schema for updating an existing patient."""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    
    # Contact
    email: Optional[EmailStr] = None
    phone_primary: Optional[str] = Field(None, max_length=20)
    phone_secondary: Optional[str] = Field(None, max_length=20)
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=2)
    zip_code: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = Field(None, max_length=2)
    
    # Insurance - Primary
    insurance_primary_member_id: Optional[str] = Field(None, max_length=50)
    insurance_primary_group_number: Optional[str] = Field(None, max_length=50)
    insurance_primary_payer_name: Optional[str] = Field(None, max_length=200)
    insurance_primary_plan_name: Optional[str] = Field(None, max_length=200)
    insurance_primary_effective_date: Optional[date] = None
    insurance_primary_termination_date: Optional[date] = None
    
    # Insurance - Secondary
    insurance_secondary_member_id: Optional[str] = Field(None, max_length=50)
    insurance_secondary_group_number: Optional[str] = Field(None, max_length=50)
    insurance_secondary_payer_name: Optional[str] = Field(None, max_length=200)
    
    # Medical
    primary_diagnosis_codes: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    medical_history: Optional[str] = None
    
    # Emergency contact
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)
    
    # Consent
    consent_to_treat: Optional[bool] = None
    consent_to_share_info: Optional[bool] = None
    
    # Preferences
    preferred_language: Optional[str] = Field(None, max_length=10)
    communication_preferences: Optional[Dict[str, Any]] = None
    
    # Status
    is_active: Optional[bool] = None
    is_deceased: Optional[bool] = None
    deceased_date: Optional[date] = None
    
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(extra="forbid")


# Response schemas
class PatientResponse(PatientBase):
    """Schema for patient response."""
    
    id: UUID
    mrn: Optional[str]
    external_id: Optional[str]
    
    # Status
    is_active: bool
    is_deceased: bool
    deceased_date: Optional[date]
    
    # Consent
    consent_to_treat: bool
    consent_to_share_info: bool
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_verified_at: Optional[datetime]
    
    # Computed properties
    full_name: str = Field(description="Full name")
    age: int = Field(description="Current age")
    has_active_insurance: bool = Field(description="Has active insurance")
    full_address: Optional[str] = Field(None, description="Formatted address")
    
    model_config = ConfigDict(from_attributes=True)


class PatientSummaryResponse(BaseModel):
    """Minimal patient info for lists."""
    
    id: UUID
    mrn: Optional[str]
    full_name: str
    date_of_birth: date
    age: int
    gender: Gender
    insurance_primary_member_id: Optional[str]
    insurance_primary_payer_name: Optional[str]
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class PatientListResponse(BaseModel):
    """Schema for paginated patient list response."""
    
    items: List[PatientSummaryResponse]
    total: int = Field(..., description="Total number of patients matching filters")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum records returned")
    
    model_config = ConfigDict(from_attributes=True)


class PatientEligibilityCheck(BaseModel):
    """Schema for insurance eligibility check request."""
    
    patient_id: UUID
    service_date: date = Field(default_factory=date.today)
    service_codes: List[str] = Field(..., min_length=1)


class PatientEligibilityResponse(BaseModel):
    """Schema for eligibility check response."""
    
    patient_id: UUID
    is_eligible: bool
    coverage_status: str
    plan_name: Optional[str]
    member_id: Optional[str]
    effective_date: Optional[date]
    termination_date: Optional[date]
    copay_amount: Optional[float]
    deductible_amount: Optional[float]
    deductible_met: Optional[float]
    out_of_pocket_max: Optional[float]
    out_of_pocket_met: Optional[float]
    messages: List[str] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=datetime.utcnow)