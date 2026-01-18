"""
Models Package
==============

SQLAlchemy ORM models for the Prior Authorization AI platform.

Author: Prior Auth AI Team
Version: 1.0.0
"""

from models.base import Base
from models.user import User
from models.clinic import Clinic
from models.audit_log import AuditLog

# Import all models here to ensure they're registered with Base.metadata
# This is critical for Alembic migrations to detect all tables

__all__ = [
    "Base",
    "User",
    "Clinic",
    "AuditLog",
]