"""
Prior Authorization Database Model

Represents a prior authorization request in its complete lifecycle.

Author: Prior Auth AI Team
Version: 1.0.0
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    String, Text, DateTime, Boolean, Integer, JSON, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class PAStatus(str, Enum):
    """Prior authorization request status."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    PENDING_INFO = "pending_info"
    APPROVED = "approved"
    DENIED = "denied"
    APPEALED = "appealed"
    APPEAL_APPROVED = "appeal_approved"
    APPEAL_DENIED = "appeal_denied"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PAUrgency(str, Enum):
    """Urgency level for PA processing."""
    ROUTINE = "routine"
    URGENT = "urgent"
    EXPEDITED = "expedited"
    EMERGENCY = "emergency"


class PAType(str, Enum):
    """Type of prior authorization."""
    MEDICATION = "medication"
    PROCEDURE = "procedure"
    IMAGING = "imaging"
    DME = "dme"  # Durable Medical Equipment
    HOME_HEALTH = "home_health"
    SPECIALTY_CARE = "specialty_care"
    INPATIENT = "inpatient"
    OUTPATIENT = "outpatient"
    OTHER = "other"


class PriorAuthorization(Base):
    """
    Prior Authorization request model.
    
    Represents a complete PA request including patient info,
    requested service/medication, clinical justification,
    and tracking through submission and approval process.
    """
    
    __tablename__ = "prior_authorizations"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True,
    )
    
    # External reference number (from payer if submitted)
    external_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    
    # Status tracking
    status: Mapped[PAStatus] = mapped_column(
        SQLEnum(PAStatus),
        default=PAStatus.DRAFT,
        nullable=False,
        index=True,
    )
    
    urgency: Mapped[PAUrgency] = mapped_column(
        SQLEnum(PAUrgency),
        default=PAUrgency.ROUTINE,
        nullable=False,
    )
    
    pa_type: Mapped[PAType] = mapped_column(
        SQLEnum(PAType),
        nullable=False,
        index=True,
    )
    
    # Foreign keys
    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    provider_id: Mapped[UUID] = mapped_column(
        ForeignKey("providers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    
    payer_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("payers.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    
    created_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    
    assigned_to_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Service/medication details
    service_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="CPT/HCPCS code",
    )
    
    service_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    
    medication_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    
    medication_ndc: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="National Drug Code",
    )
    
    diagnosis_codes: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="ICD-10 diagnosis codes",
    )
    
    # Clinical information
    clinical_rationale: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    medical_necessity: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Medical necessity justification",
    )
    
    # Treatment details
    requested_quantity: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    
    requested_duration_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    
    treatment_start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    
    treatment_end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    
    # Submission tracking
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )
    
    submission_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="fax, portal, api, etc.",
    )
    
    # Decision tracking
    decision_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )
    
    approval_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    denial_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    denial_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    # Validity period (if approved)
    valid_from: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    
    valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    
    # AI/Automation tracking
    ai_confidence_score: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="0-1 confidence score from AI review",
    )
    
    ai_recommendation: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="AI suggested action",
    )
    
    requires_human_review: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    workflow_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("workflows.id", ondelete="SET NULL"),
        nullable=True,
        comment="Link to orchestration workflow",
    )
    
    # Additional metadata
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    metadata: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="Flexible field for additional data",
    )
    
    # Flags
    is_appeal: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )
    
    original_pa_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("prior_authorizations.id", ondelete="SET NULL"),
        nullable=True,
        comment="If this is an appeal, link to original PA",
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    
    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="prior_authorizations",
        lazy="selectin",
    )
    
    provider: Mapped["Provider"] = relationship(
        "Provider",
        back_populates="prior_authorizations",
        lazy="selectin",
    )
    
    payer: Mapped[Optional["Payer"]] = relationship(
        "Payer",
        back_populates="prior_authorizations",
        lazy="selectin",
    )
    
    created_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by_id],
        lazy="selectin",
    )
    
    assigned_to: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assigned_to_id],
        lazy="selectin",
    )
    
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="prior_authorization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    submissions: Mapped[list["Submission"]] = relationship(
        "Submission",
        back_populates="prior_authorization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    appeals: Mapped[list["Appeal"]] = relationship(
        "Appeal",
        back_populates="prior_authorization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    status_history: Mapped[list["PAStatusHistory"]] = relationship(
        "PAStatusHistory",
        back_populates="prior_authorization",
        cascade="all, delete-orphan",
        order_by="PAStatusHistory.created_at.desc()",
        lazy="selectin",
    )
    
    workflow: Mapped[Optional["Workflow"]] = relationship(
        "Workflow",
        back_populates="prior_authorizations",
        lazy="selectin",
    )
    
    # Self-referential for appeals
    original_pa: Mapped[Optional["PriorAuthorization"]] = relationship(
        "PriorAuthorization",
        remote_side=[id],
        foreign_keys=[original_pa_id],
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return (
            f"<PriorAuthorization(id={self.id}, "
            f"status={self.status.value}, "
            f"type={self.pa_type.value})>"
        )
    
    @property
    def is_active(self) -> bool:
        """Check if PA is in an active state."""
        return self.status in [
            PAStatus.SUBMITTED,
            PAStatus.UNDER_REVIEW,
            PAStatus.PENDING_INFO,
        ]
    
    @property
    def is_completed(self) -> bool:
        """Check if PA has reached a final state."""
        return self.status in [
            PAStatus.APPROVED,
            PAStatus.DENIED,
            PAStatus.APPEAL_APPROVED,
            PAStatus.APPEAL_DENIED,
            PAStatus.CANCELLED,
            PAStatus.EXPIRED,
        ]
    
    @property
    def days_since_submission(self) -> Optional[int]:
        """Calculate days since submission."""
        if self.submitted_at:
            return (datetime.utcnow() - self.submitted_at).days
        return None
    
    @property
    def is_overdue(self) -> bool:
        """
        Check if PA is overdue based on urgency.
        
        Routine: 14 days
        Urgent: 7 days
        Expedited: 3 days
        Emergency: 1 day
        """
        if not self.is_active or not self.submitted_at:
            return False
        
        days = self.days_since_submission
        if days is None:
            return False
        
        thresholds = {
            PAUrgency.ROUTINE: 14,
            PAUrgency.URGENT: 7,
            PAUrgency.EXPEDITED: 3,
            PAUrgency.EMERGENCY: 1,
        }
        
        return days > thresholds.get(self.urgency, 14)


class PAStatusHistory(Base):
    """
    Track status changes for prior authorizations.
    
    Maintains audit trail of all status transitions.
    """
    
    __tablename__ = "pa_status_history"
    
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    
    prior_authorization_id: Mapped[UUID] = mapped_column(
        ForeignKey("prior_authorizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    from_status: Mapped[Optional[PAStatus]] = mapped_column(
        SQLEnum(PAStatus),
        nullable=True,
    )
    
    to_status: Mapped[PAStatus] = mapped_column(
        SQLEnum(PAStatus),
        nullable=False,
    )
    
    changed_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    
    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    
    # Relationships
    prior_authorization: Mapped["PriorAuthorization"] = relationship(
        "PriorAuthorization",
        back_populates="status_history",
    )
    
    changed_by: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return (
            f"<PAStatusHistory(pa_id={self.prior_authorization_id}, "
            f"from={self.from_status}, to={self.to_status})>"
        )