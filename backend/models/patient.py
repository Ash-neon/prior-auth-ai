"""
Patient Database Model

Represents a patient with demographics, insurance, and medical history.

Author: Prior Auth AI Team
Version: 1.0.0
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Date, DateTime, JSON, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class Gender(str, Enum):
    """Patient gender."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class Patient(Base):
    """
    Patient demographic and insurance information.
    
    Core entity representing individuals requiring prior authorizations.
    Contains PHI - must be handled according to HIPAA requirements.
    """
    
    __tablename__ = "patients"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True,
    )
    
    # External identifiers
    mrn: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        unique=True,
        index=True,
        comment="Medical Record Number",
    )
    
    external_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        index=True,
        comment="External system identifier",
    )
    
    # Demographics
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    
    middle_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    
    gender: Mapped[Gender] = mapped_column(
        SQLEnum(Gender),
        nullable=False,
    )
    
    ssn: Mapped[Optional[str]] = mapped_column(
        String(11),
        nullable=True,
        comment="Encrypted SSN",
    )
    
    # Contact information
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    phone_primary: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    phone_secondary: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
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
    
    # Insurance - Primary
    insurance_primary_member_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    
    insurance_primary_group_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    insurance_primary_payer_id: Mapped[Optional[UUID]] = mapped_column(
        nullable=True,
        comment="Link to Payer table when available",
    )
    
    insurance_primary_payer_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    
    insurance_primary_plan_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    
    insurance_primary_effective_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    
    insurance_primary_termination_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    
    # Insurance - Secondary (optional)
    insurance_secondary_member_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    insurance_secondary_group_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    insurance_secondary_payer_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    
    # Medical information
    primary_diagnosis_codes: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="Primary ICD-10 codes",
    )
    
    allergies: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    
    current_medications: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    
    medical_history: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Emergency contact
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    emergency_contact_relationship: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    # Consent and preferences
    consent_to_treat: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    
    consent_to_share_info: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    
    preferred_language: Mapped[str] = mapped_column(
        String(10),
        default="en",
        nullable=False,
    )
    
    communication_preferences: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        index=True,
    )
    
    is_deceased: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    
    deceased_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    
    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(
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
        index=True,
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
        comment="Last time patient info was verified",
    )
    
    # Relationships
    prior_authorizations: Mapped[list["PriorAuthorization"]] = relationship(
        "PriorAuthorization",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return (
            f"<Patient(id={self.id}, "
            f"name={self.first_name} {self.last_name}, "
            f"dob={self.date_of_birth})>"
        )
    
    @property
    def full_name(self) -> str:
        """Get patient's full name."""
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return " ".join(parts)
    
    @property
    def age(self) -> int:
        """Calculate patient's current age."""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < 
            (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def has_active_insurance(self) -> bool:
        """Check if patient has active primary insurance."""
        if not self.insurance_primary_member_id:
            return False
        
        today = date.today()
        
        # Check effective date
        if self.insurance_primary_effective_date:
            if today < self.insurance_primary_effective_date:
                return False
        
        # Check termination date
        if self.insurance_primary_termination_date:
            if today > self.insurance_primary_termination_date:
                return False
        
        return True
    
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