"""
Clinic Model
============

Organization/clinic model for multi-tenant support.

Each clinic represents a healthcare organization using the platform.
Users, PAs, and other resources are scoped to clinics.

Author: Prior Auth AI Team
Version: 1.0.0
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy import (
    Column, String, Boolean, DateTime, Index, Enum as SQLEnum, Text, Integer
)
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import JSONB

from backend.models.base import BaseModel


class ClinicStatus(str, Enum):
    """Clinic account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRIAL = "trial"
    SUSPENDED = "suspended"


class Clinic(BaseModel):
    """
    Clinic/Organization model for multi-tenant support.
    
    Attributes:
        name: Clinic name
        npi: National Provider Identifier (10 digits)
        tax_id: Tax ID / EIN
        address: Physical address (JSONB)
        phone: Primary phone number
        fax: Primary fax number
        email: Primary email address
        website: Website URL
        status: Account status (active, inactive, trial, suspended)
        is_active: Quick active check
        settings: Clinic-specific settings (JSONB)
        subscription_tier: Subscription level (future use)
        subscription_expires_at: Subscription expiration
        max_users: Maximum allowed users
        max_pas_per_month: Maximum PAs per month
        features_enabled: List of enabled features
        billing_contact: Billing contact info (JSONB)
        technical_contact: Technical contact info (JSONB)
    """
    
    __tablename__ = "clinics"
    
    # Basic info
    name = Column(String(255), nullable=False, index=True)
    
    # Identifiers
    npi = Column(String(10), unique=True, nullable=True, index=True)
    tax_id = Column(String(20), nullable=True)
    
    # Contact info
    address = Column(JSONB, default={}, nullable=False)
    phone = Column(String(20))
    fax = Column(String(20))
    email = Column(String(255))
    website = Column(String(255))
    
    # Status
    status = Column(SQLEnum(ClinicStatus), nullable=False, default=ClinicStatus.TRIAL)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Settings and configuration
    settings = Column(JSONB, default={}, nullable=False)
    
    # Subscription info
    subscription_tier = Column(String(50), default="trial")
    subscription_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Limits
    max_users = Column(Integer, default=10, nullable=False)
    max_pas_per_month = Column(Integer, default=100, nullable=False)
    
    # Feature flags (list of enabled feature names)
    features_enabled = Column(JSONB, default=[], nullable=False)
    
    # Contacts
    billing_contact = Column(JSONB, default={}, nullable=False)
    technical_contact = Column(JSONB, default={}, nullable=False)
    
    # Notes
    notes = Column(Text)
    
    # Relationships
    users = relationship("User", back_populates="clinic")
    patients = relationship("Patient", back_populates="clinic")
    prior_authorizations = relationship("PriorAuthorization", back_populates="clinic")
    
    # Indexes
    __table_args__ = (
        Index("idx_clinic_name_active", "name", "is_active"),
        Index("idx_clinic_npi", "npi"),
        Index("idx_clinic_status", "status"),
    )
    
    @property
    def is_trial(self) -> bool:
        """Check if clinic is in trial period."""
        return self.status == ClinicStatus.TRIAL
    
    @property
    def subscription_active(self) -> bool:
        """Check if subscription is currently active."""
        if not self.subscription_expires_at:
            return False
        return datetime.utcnow() < self.subscription_expires_at
    
    @property
    def days_until_expiration(self) -> Optional[int]:
        """Get days until subscription expires."""
        if not self.subscription_expires_at:
            return None
        delta = self.subscription_expires_at - datetime.utcnow()
        return max(0, delta.days)
    
    def has_feature(self, feature_name: str) -> bool:
        """
        Check if clinic has a specific feature enabled.
        
        Args:
            feature_name: Name of the feature to check
            
        Returns:
            True if feature is enabled
        """
        return feature_name in self.features_enabled
    
    def enable_feature(self, feature_name: str) -> None:
        """
        Enable a feature for this clinic.
        
        Args:
            feature_name: Name of the feature to enable
        """
        if feature_name not in self.features_enabled:
            self.features_enabled.append(feature_name)
    
    def disable_feature(self, feature_name: str) -> None:
        """
        Disable a feature for this clinic.
        
        Args:
            feature_name: Name of the feature to disable
        """
        if feature_name in self.features_enabled:
            self.features_enabled.remove(feature_name)
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a clinic setting value.
        
        Args:
            key: Setting key
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """
        Set a clinic setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
        self.settings[key] = value
    
    def get_address_string(self) -> str:
        """
        Get formatted address string.
        
        Returns:
            Formatted address
        """
        if not self.address:
            return ""
        
        parts = []
        if self.address.get("street"):
            parts.append(self.address["street"])
        if self.address.get("city"):
            parts.append(self.address["city"])
        if self.address.get("state"):
            parts.append(self.address["state"])
        if self.address.get("zip"):
            parts.append(self.address["zip"])
        
        return ", ".join(parts)
    
    @classmethod
    def get_by_npi(cls, db: Session, npi: str) -> Optional["Clinic"]:
        """
        Get clinic by NPI number.
        
        Args:
            db: Database session
            npi: NPI number (10 digits)
            
        Returns:
            Clinic instance or None
        """
        return db.query(cls).filter(
            cls.npi == npi,
            cls.is_deleted == False
        ).first()
    
    @classmethod
    def get_active_clinics(cls, db: Session) -> List["Clinic"]:
        """
        Get all active clinics.
        
        Args:
            db: Database session
            
        Returns:
            List of active clinics
        """
        return db.query(cls).filter(
            cls.is_active == True,
            cls.status == ClinicStatus.ACTIVE,
            cls.is_deleted == False
        ).all()
    
    @classmethod
    def search_by_name(cls, db: Session, name: str) -> List["Clinic"]:
        """
        Search clinics by name (case-insensitive).
        
        Args:
            db: Database session
            name: Search term
            
        Returns:
            List of matching clinics
        """
        return db.query(cls).filter(
            cls.name.ilike(f"%{name}%"),
            cls.is_deleted == False
        ).all()
    
    def get_user_count(self, db: Session) -> int:
        """
        Get count of active users in this clinic.
        
        Args:
            db: Database session
            
        Returns:
            Number of active users
        """
        from backend.models.user import User
        return db.query(User).filter(
            User.clinic_id == self.id,
            User.is_active == True,
            User.is_deleted == False
        ).count()
    
    def can_add_user(self, db: Session) -> bool:
        """
        Check if clinic can add another user.
        
        Args:
            db: Database session
            
        Returns:
            True if under user limit
        """
        return self.get_user_count(db) < self.max_users
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<Clinic(id={self.id}, name={self.name}, npi={self.npi})>"