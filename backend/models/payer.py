"""
Payer Database Model

Represents insurance payers/companies and their PA requirements.

Author: Prior Auth AI Team
Version: 1.0.0
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, JSON, Text, Integer, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class PayerType(str, Enum):
    """Type of insurance payer."""
    COMMERCIAL = "commercial"
    MEDICARE = "medicare"
    MEDICAID = "medicaid"
    MEDICARE_ADVANTAGE = "medicare_advantage"
    TRICARE = "tricare"
    WORKERS_COMP = "workers_comp"
    AUTO = "auto"
    OTHER = "other"


class SubmissionMethod(str, Enum):
    """Method for submitting PAs to payer."""
    PORTAL = "portal"
    FAX = "fax"
    PHONE = "phone"
    EMAIL = "email"
    API = "api"
    EDI = "edi"
    MAIL = "mail"


class Payer(Base):
    """
    Insurance payer/company information.
    
    Stores payer details, submission requirements, and PA policies.
    """
    
    __tablename__ = "payers"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True,
    )
    
    # Payer identifiers
    payer_id: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        unique=True,
        index=True,
        comment="Standard payer ID (e.g., from NPPES)",
    )
    
    external_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        index=True,
    )
    
    # Basic information
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    
    legal_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    payer_type: Mapped[PayerType] = mapped_column(
        SQLEnum(PayerType),
        nullable=False,
        index=True,
    )
    
    # Contact information
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    fax: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    website: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    pa_portal_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="URL for PA submission portal",
    )
    
    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    address_line2: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    state: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
    )
    
    zip_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )
    
    country: Mapped[str] = mapped_column(
        String(2),
        default="US",
        nullable=False,
    )
    
    # PA submission requirements
    preferred_submission_method: Mapped[SubmissionMethod] = mapped_column(
        SQLEnum(SubmissionMethod),
        default=SubmissionMethod.PORTAL,
        nullable=False,
    )
    
    accepted_submission_methods: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    
    requires_electronic_signature: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    
    accepts_rush_requests: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    
    # Processing times (in business days)
    standard_processing_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Typical processing time for routine PAs",
    )
    
    urgent_processing_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Processing time for urgent PAs",
    )
    
    expedited_processing_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Processing time for expedited PAs",
    )
    
    # Required documentation
    required_documents: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="List of required document types",
    )
    
    optional_documents: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    
    # Coverage and policies
    covered_services: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="Services that require PA",
    )
    
    medical_policies: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="Medical necessity criteria by service type",
    )
    
    formulary_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="URL to drug formulary",
    )
    
    # API integration
    has_api_integration: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    
    api_endpoint: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    
    api_version: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    api_documentation_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    
    requires_api_authentication: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )
    
    # Portal credentials (encrypted)
    portal_username: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Encrypted portal credentials",
    )
    
    portal_password_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Encrypted portal password",
    )
    
    # Performance metrics
    total_submissions: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    
    approved_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    
    denied_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    
    average_approval_time_days: Mapped[Optional[float]] = mapped_column(
        nullable=True,
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        index=True,
    )
    
    accepts_new_submissions: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )
    
    # Notes and special instructions
    submission_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Special instructions for submissions",
    )
    
    appeal_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Special instructions for appeals",
    )
    
    internal_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    metadata: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Last time payer info was verified",
    )
    
    # Relationships
    prior_authorizations: Mapped[list["PriorAuthorization"]] = relationship(
        "PriorAuthorization",
        back_populates="payer",
    )
    
    def __repr__(self) -> str:
        return f"<Payer(id={self.id}, name={self.name}, type={self.payer_type.value})>"
    
    @property
    def full_address(self) -> Optional[str]:
        """Get formatted full address."""
        if not self.address_line1:
            return None
        
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        
        if self.city and self.state and self.zip_code:
            parts.append(f"{self.city}, {self.state} {self.zip_code}")
        
        return "\n".join(parts)
    
    @property
    def approval_rate(self) -> Optional[float]:
        """Calculate PA approval rate."""
        total = self.total_submissions
        if total == 0:
            return None
        
        return (self.approved_count / total) * 100
    
    @property
    def is_configured_for_api(self) -> bool:
        """Check if payer is ready for API submissions."""
        return (
            self.has_api_integration and
            self.api_endpoint is not None and
            self.accepts_new_submissions
        )
    
    @property
    def is_configured_for_portal(self) -> bool:
        """Check if payer is ready for portal submissions."""
        return (
            self.pa_portal_url is not None and
            self.portal_username is not None and
            self.portal_password_hash is not None and
            self.accepts_new_submissions
        )
    
    def supports_submission_method(self, method: SubmissionMethod) -> bool:
        """Check if payer supports a specific submission method."""
        return method.value in self.accepted_submission_methods