"""
Provider Database Model

Represents healthcare providers (physicians, facilities, practices).

Author: Prior Auth AI Team
Version: 1.0.0
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Date, DateTime, JSON, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db import Base


class ProviderType(str, Enum):
    """Type of healthcare provider."""
    PHYSICIAN = "physician"
    NURSE_PRACTITIONER = "nurse_practitioner"
    PHYSICIAN_ASSISTANT = "physician_assistant"
    FACILITY = "facility"
    PHARMACY = "pharmacy"
    DME_SUPPLIER = "dme_supplier"
    HOME_HEALTH = "home_health"
    LABORATORY = "laboratory"
    IMAGING_CENTER = "imaging_center"
    OTHER = "other"


class ProviderSpecialty(str, Enum):
    """Medical specialties."""
    CARDIOLOGY = "cardiology"
    DERMATOLOGY = "dermatology"
    ENDOCRINOLOGY = "endocrinology"
    GASTROENTEROLOGY = "gastroenterology"
    HEMATOLOGY = "hematology"
    INFECTIOUS_DISEASE = "infectious_disease"
    NEPHROLOGY = "nephrology"
    NEUROLOGY = "neurology"
    ONCOLOGY = "oncology"
    OPHTHALMOLOGY = "ophthalmology"
    ORTHOPEDICS = "orthopedics"
    PEDIATRICS = "pediatrics"
    PSYCHIATRY = "psychiatry"
    PULMONOLOGY = "pulmonology"
    RADIOLOGY = "radiology"
    RHEUMATOLOGY = "rheumatology"
    SURGERY = "surgery"
    UROLOGY = "urology"
    PRIMARY_CARE = "primary_care"
    FAMILY_MEDICINE = "family_medicine"
    INTERNAL_MEDICINE = "internal_medicine"
    EMERGENCY_MEDICINE = "emergency_medicine"
    OTHER = "other"


class Provider(Base):
    """
    Healthcare provider information.
    
    Represents physicians, facilities, or other entities that
    request prior authorizations for their patients.
    """
    
    __tablename__ = "providers"
    
    # Primary identification
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True,
    )
    
    # Provider identifiers
    npi: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        unique=True,
        index=True,
        comment="National Provider Identifier",
    )
    
    tax_id: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Tax Identification Number (EIN/SSN)",
    )
    
    license_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    license_state: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
    )
    
    dea_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="DEA number for controlled substances",
    )
    
    external_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        index=True,
    )
    
    # Provider type and specialty
    provider_type: Mapped[ProviderType] = mapped_column(
        SQLEnum(ProviderType),
        nullable=False,
        index=True,
    )
    
    specialty: Mapped[Optional[ProviderSpecialty]] = mapped_column(
        SQLEnum(ProviderSpecialty),
        nullable=True,
        index=True,
    )
    
    subspecialties: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    
    # Individual provider info (for physicians, NPs, PAs)
    first_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    last_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    
    middle_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    credentials: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="MD, DO, NP, PA-C, etc.",
    )
    
    # Organization info (for facilities)
    organization_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    
    doing_business_as: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    # Contact information
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    fax: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    website: Mapped[Optional[str]] = mapped_column(
        String(255),
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
    
    # Practice information
    accepts_new_patients: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )
    
    hospital_affiliations: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    
    languages_spoken: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    
    # Insurance and network participation
    insurance_networks: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="List of insurance networks provider participates in",
    )
    
    # Credentialing
    board_certified: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    
    board_certification_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    
    board_certification_expiry: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    
    medical_school: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    graduation_year: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )
    
    # License status
    license_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )
    
    license_expiry_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    
    # Performance metrics (for analytics)
    total_pa_requests: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    
    approved_pa_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    
    denied_pa_count: Mapped[int] = mapped_column(
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
    
    is_verified: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="Has provider information been verified",
    )
    
    verification_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
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
    
    # Relationships
    prior_authorizations: Mapped[list["PriorAuthorization"]] = relationship(
        "PriorAuthorization",
        back_populates="provider",
    )
    
    def __repr__(self) -> str:
        name = self.full_name or self.organization_name or "Unknown"
        return f"<Provider(id={self.id}, npi={self.npi}, name={name})>"
    
    @property
    def full_name(self) -> Optional[str]:
        """Get provider's full name (for individual providers)."""
        if not self.first_name or not self.last_name:
            return None
        
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        
        name = " ".join(parts)
        if self.credentials:
            name += f", {self.credentials}"
        
        return name
    
    @property
    def display_name(self) -> str:
        """Get the display name (individual name or organization)."""
        return self.full_name or self.organization_name or f"Provider {self.npi}"
    
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
        total = self.total_pa_requests
        if total == 0:
            return None
        
        return (self.approved_pa_count / total) * 100
    
    @property
    def needs_credentialing_update(self) -> bool:
        """Check if provider credentials need updating."""
        if not self.is_active:
            return False
        
        # Check license expiry
        if self.license_expiry_date:
            if self.license_expiry_date < date.today():
                return True
        
        # Check board certification expiry
        if self.board_certified and self.board_certification_expiry:
            if self.board_certification_expiry < date.today():
                return True
        
        return False