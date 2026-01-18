"""
User Model
==========

User authentication and authorization model for the PA platform.

Roles:
- admin: Full system access
- clinician: Can create/manage PAs, view analytics
- staff: Can create/edit PAs, limited analytics
- viewer: Read-only access

Author: Prior Auth AI Team
Version: 1.0.0
"""

from enum import Enum
from typing import Optional, List
from datetime import datetime

from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Index, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID

from backend.models.base import BaseModel
from backend.core.security import verify_password, get_password_hash


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    CLINICIAN = "clinician"
    STAFF = "staff"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(BaseModel):
    """
    User model for authentication and authorization.
    
    Attributes:
        email: Unique email address
        password_hash: Bcrypt hashed password
        first_name: User's first name
        last_name: User's last name
        role: User role (admin, clinician, staff, viewer)
        status: Account status (active, inactive, suspended, pending)
        clinic_id: Foreign key to clinic (inherited from BaseModel)
        is_active: Quick check for active status
        mfa_enabled: Whether MFA is enabled
        mfa_secret: TOTP secret for MFA (encrypted)
        last_login_at: Timestamp of last successful login
        failed_login_attempts: Counter for failed logins
        locked_until: Timestamp until which account is locked
        email_verified: Whether email is verified
        email_verification_token: Token for email verification
        password_reset_token: Token for password reset
        password_reset_expires: Expiration for reset token
        preferences: User preferences (JSONB)
    """
    
    __tablename__ = "users"
    
    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile fields
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    
    # Authorization
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.STAFF)
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.PENDING)
    
    # Clinic relationship (clinic_id inherited from BaseModel)
    clinic_id = Column(UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=True)
    clinic = relationship("Clinic", back_populates="users")
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # MFA
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255), nullable=True)  # Encrypted TOTP secret
    
    # Security tracking
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Email verification
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String(255), nullable=True)
    
    # Password reset
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    
    # User preferences (notifications, UI settings, etc.)
    preferences = Column(JSONB, default={}, nullable=False)
    
    # Relationships
    created_pas = relationship(
        "PriorAuthorization",
        back_populates="creator",
        foreign_keys="PriorAuthorization.created_by"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_user_email_active", "email", "is_active"),
        Index("idx_user_clinic_role", "clinic_id", "role"),
        Index("idx_user_status", "status"),
    )
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
    
    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False
    
    @property
    def can_login(self) -> bool:
        """Check if user can currently log in."""
        return (
            self.is_active
            and self.status == UserStatus.ACTIVE
            and not self.is_locked
            and not self.is_deleted
        )
    
    def verify_password(self, password: str) -> bool:
        """
        Verify password against stored hash.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        return verify_password(password, self.password_hash)
    
    def set_password(self, password: str) -> None:
        """
        Set user password (hashed).
        
        Args:
            password: Plain text password to hash and store
        """
        self.password_hash = get_password_hash(password)
    
    def record_login_success(self) -> None:
        """Record successful login."""
        self.last_login_at = datetime.utcnow()
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def record_login_failure(self) -> None:
        """Record failed login attempt and lock if necessary."""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
    
    def has_permission(self, required_role: UserRole) -> bool:
        """
        Check if user has at least the required role level.
        
        Role hierarchy: admin > clinician > staff > viewer
        
        Args:
            required_role: Minimum required role
            
        Returns:
            True if user has sufficient permissions
        """
        role_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.STAFF: 2,
            UserRole.CLINICIAN: 3,
            UserRole.ADMIN: 4,
        }
        
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)
    
    def to_dict(self, exclude: Optional[List[str]] = None, **kwargs) -> dict:
        """
        Convert to dictionary, always excluding sensitive fields.
        
        Args:
            exclude: Additional fields to exclude
            **kwargs: Passed to BaseModel.to_dict()
            
        Returns:
            Dictionary representation
        """
        # Always exclude sensitive fields
        default_exclude = [
            "password_hash",
            "mfa_secret",
            "email_verification_token",
            "password_reset_token"
        ]
        
        if exclude:
            default_exclude.extend(exclude)
        
        return super().to_dict(exclude=default_exclude, **kwargs)
    
    @classmethod
    def get_by_email(cls, db: Session, email: str) -> Optional["User"]:
        """
        Get user by email address.
        
        Args:
            db: Database session
            email: Email address to search for
            
        Returns:
            User instance or None
        """
        return db.query(cls).filter(
            cls.email == email.lower(),
            cls.is_deleted == False
        ).first()
    
    @classmethod
    def get_active_by_email(cls, db: Session, email: str) -> Optional["User"]:
        """
        Get active user by email.
        
        Args:
            db: Database session
            email: Email address
            
        Returns:
            User instance or None
        """
        return db.query(cls).filter(
            cls.email == email.lower(),
            cls.is_active == True,
            cls.status == UserStatus.ACTIVE,
            cls.is_deleted == False
        ).first()
    
    @classmethod
    def get_by_clinic(cls, db: Session, clinic_id: str) -> List["User"]:
        """
        Get all users for a clinic.
        
        Args:
            db: Database session
            clinic_id: Clinic UUID
            
        Returns:
            List of users
        """
        return db.query(cls).filter(
            cls.clinic_id == clinic_id,
            cls.is_deleted == False
        ).all()
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


# Import after model definition to avoid circular imports
from sqlalchemy import Integer, JSONB
from datetime import timedelta