"""
Prior Authorization Pydantic Schemas

Request/response schemas for PA API endpoints.

Author: Prior Auth AI Team
Version: 1.0.0
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator

from backend.models.prior_authorization import PAStatus, PAUrgency, PAType


# Base schemas
class PABase(BaseModel):
    """Base schema for PA with common fields."""
    
    pa_type: PAType = Field(..., description="Type of prior authorization")
    urgency: PAUrgency = Field(
        default=PAUrgency.ROUTINE,
        description="Urgency level for processing"
    )
    service_code: Optional[str] = Field(
        None,
        max_length=50,
        description="CPT/HCPCS code"
    )
    service_description: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Description of requested service"
    )
    medication_name: Optional[str] = Field(None, max_length=200)
    medication_ndc: Optional[str] = Field(None, max_length=20)
    diagnosis_codes: List[str] = Field(
        default_factory=list,
        description="ICD-10 diagnosis codes"
    )
    clinical_rationale: Optional[str] = Field(None, max_length=10000)
    medical_necessity: Optional[str] = Field(None, max_length=10000)
    requested_quantity: Optional[int] = Field(None, ge=1)
    requested_duration_days: Optional[int] = Field(None, ge=1)
    treatment_start_date: Optional[date] = None
    treatment_end_date: Optional[date] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PACreate(PABase):
    """Schema for creating a new PA request."""
    
    patient_id: UUID = Field(..., description="Patient ID")
    provider_id: UUID = Field(..., description="Requesting provider ID")
    payer_id: Optional[UUID] = Field(None, description="Insurance payer ID")
    
    @field_validator("treatment_end_date")
    @classmethod
    def validate_treatment_dates(cls, v, info):
        """Ensure end date is after start date."""
        if v and info.data.get("treatment_start_date"):
            if v < info.data["treatment_start_date"]:
                raise ValueError("treatment_end_date must be after treatment_start_date")
        return v
    
    @field_validator("diagnosis_codes")
    @classmethod
    def validate_diagnosis_codes(cls, v):
        """Validate ICD-10 format."""
        for code in v:
            if not code or len(code) < 3:
                raise ValueError(f"Invalid ICD-10 code: {code}")
        return v


class PAUpdate(BaseModel):
    """Schema for updating an existing PA request."""
    
    status: Optional[PAStatus] = None
    urgency: Optional[PAUrgency] = None
    pa_type: Optional[PAType] = None
    service_code: Optional[str] = Field(None, max_length=50)
    service_description: Optional[str] = Field(None, min_length=1, max_length=5000)
    medication_name: Optional[str] = Field(None, max_length=200)
    medication_ndc: Optional[str] = Field(None, max_length=20)
    diagnosis_codes: Optional[List[str]] = None
    clinical_rationale: Optional[str] = Field(None, max_length=10000)
    medical_necessity: Optional[str] = Field(None, max_length=10000)
    requested_quantity: Optional[int] = Field(None, ge=1)
    requested_duration_days: Optional[int] = Field(None, ge=1)
    treatment_start_date: Optional[date] = None
    treatment_end_date: Optional[date] = None
    payer_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None
    external_reference: Optional[str] = Field(None, max_length=100)
    approval_number: Optional[str] = Field(None, max_length=100)
    denial_reason: Optional[str] = None
    denial_code: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(extra="forbid")


class PAStatusUpdate(BaseModel):
    """Schema for updating PA status with reason."""
    
    status: PAStatus = Field(..., description="New status")
    reason: Optional[str] = Field(None, description="Reason for status change")
    notes: Optional[str] = Field(None, description="Additional notes")


# Response schemas
class PAStatusHistoryResponse(BaseModel):
    """Schema for PA status history entry."""
    
    id: UUID
    from_status: Optional[PAStatus]
    to_status: PAStatus
    changed_by_id: UUID
    reason: Optional[str]
    notes: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PAResponse(PABase):
    """Schema for PA response with all fields."""
    
    id: UUID
    status: PAStatus
    external_reference: Optional[str]
    patient_id: UUID
    provider_id: UUID
    payer_id: Optional[UUID]
    created_by_id: UUID
    assigned_to_id: Optional[UUID]
    
    # Submission tracking
    submitted_at: Optional[datetime]
    submission_method: Optional[str]
    
    # Decision tracking
    decision_date: Optional[datetime]
    approval_number: Optional[str]
    denial_reason: Optional[str]
    denial_code: Optional[str]
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    
    # AI tracking
    ai_confidence_score: Optional[float]
    ai_recommendation: Optional[str]
    requires_human_review: bool
    workflow_id: Optional[UUID]
    
    # Flags
    is_appeal: bool
    original_pa_id: Optional[UUID]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    is_active: bool = Field(description="Whether PA is in active state")
    is_completed: bool = Field(description="Whether PA has reached final state")
    days_since_submission: Optional[int] = Field(
        None,
        description="Days since submission"
    )
    is_overdue: bool = Field(description="Whether PA is overdue for decision")
    
    model_config = ConfigDict(from_attributes=True)


class PADetailResponse(PAResponse):
    """Extended PA response with related entities."""
    
    # Include nested objects
    patient: Optional[Dict[str, Any]] = None
    provider: Optional[Dict[str, Any]] = None
    payer: Optional[Dict[str, Any]] = None
    created_by: Optional[Dict[str, Any]] = None
    assigned_to: Optional[Dict[str, Any]] = None
    status_history: List[PAStatusHistoryResponse] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class PAListResponse(BaseModel):
    """Schema for paginated PA list response."""
    
    items: List[PAResponse]
    total: int = Field(..., description="Total number of PAs matching filters")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum records returned")
    
    model_config = ConfigDict(from_attributes=True)


class PAStatsResponse(BaseModel):
    """Schema for PA statistics."""
    
    total_count: int
    by_status: Dict[str, int]
    by_urgency: Dict[str, int]
    by_type: Dict[str, int]
    avg_approval_time_days: Optional[float]
    approval_rate: Optional[float]
    overdue_count: int


class PASubmitRequest(BaseModel):
    """Schema for submitting a PA to payer."""
    
    submission_method: str = Field(
        ...,
        description="Method to use for submission"
    )
    notes: Optional[str] = None


class PASubmitResponse(BaseModel):
    """Schema for PA submission response."""
    
    pa_id: UUID
    submitted_at: datetime
    submission_method: str
    external_reference: Optional[str]
    status: PAStatus
    message: str