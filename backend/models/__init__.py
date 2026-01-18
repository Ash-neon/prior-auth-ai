"""
Database Models Package
=======================

Centralizes all SQLAlchemy models for the Prior Authorization AI Platform.

This package contains all database models organized by domain:
- User and authentication models
- Clinic and organization models
- Audit logging models
- (Future: PA, Patient, Document models in subsequent phases)

All models inherit from backend.db.base.Base which provides:
- UUID primary keys
- Automatic timestamps
- Soft delete functionality
- Audit trail fields
- Multi-tenant support
- JSONB metadata

Author: Prior Auth AI Team
Version: 1.0.0
"""

from backend.db.base import Base
from backend.models.user import User, UserRole, UserStatus
from backend.models.clinic import Clinic, ClinicStatus
from backend.models.audit_log import AuditLog, AuditAction

# Export all models for Alembic auto-detection and easy imports
__all__ = [
    "Base",
    "User",
    "UserRole",
    "UserStatus",
    "Clinic",
    "ClinicStatus",
    "AuditLog",
    "AuditAction",
]
