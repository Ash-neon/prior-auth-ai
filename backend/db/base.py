"""
Database Base Classes
=====================

Defines the declarative base and common model mixins.

Author: Prior Auth AI Team
Version: 1.0.0
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import Session


# Create declarative base
Base = declarative_base()


class TimestampMixin:
    """
    Mixin that adds timestamp columns to models.
    
    Adds:
        - created_at: Timestamp when record was created
        - updated_at: Timestamp when record was last updated
    """
    
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Timestamp when record was created"
    )
    
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Timestamp when record was last updated"
    )


class SoftDeleteMixin:
    """
    Mixin that adds soft delete support to models.
    
    Adds:
        - deleted_at: Timestamp when record was soft-deleted (NULL if active)
    """
    
    deleted_at = Column(
        DateTime,
        nullable=True,
        default=None,
        comment="Timestamp when record was soft-deleted"
    )
    
    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted."""
        return self.deleted_at is not None
    
    def soft_delete(self, db: Session) -> None:
        """
        Soft delete the record.
        
        Args:
            db: Database session
        """
        self.deleted_at = datetime.utcnow()
        db.add(self)
        db.commit()
    
    def restore(self, db: Session) -> None:
        """
        Restore a soft-deleted record.
        
        Args:
            db: Database session
        """
        self.deleted_at = None
        db.add(self)
        db.commit()


class UUIDMixin:
    """
    Mixin that adds UUID primary key to models.
    
    Uses PostgreSQL's UUID type for better performance.
    """
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier"
    )


class AuditMixin:
    """
    Mixin that adds audit fields to models.
    
    Tracks who created and last modified the record.
    """
    
    @declared_attr
    def created_by_id(cls):
        """ID of user who created the record."""
        return Column(
            UUID(as_uuid=True),
            nullable=True,
            comment="ID of user who created this record"
        )
    
    @declared_attr
    def updated_by_id(cls):
        """ID of user who last updated the record."""
        return Column(
            UUID(as_uuid=True),
            nullable=True,
            comment="ID of user who last updated this record"
        )


class BaseModel(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Base model class that all models should inherit from.
    
    Provides:
        - UUID primary key
        - Timestamp tracking (created_at, updated_at)
        - Soft delete support (deleted_at)
        - Common utility methods
    """
    
    __abstract__ = True
    
    def to_dict(self) -> dict:
        """
        Convert model instance to dictionary.
        
        Returns:
            Dictionary representation of model
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            
            # Convert UUID to string
            if isinstance(value, uuid.UUID):
                value = str(value)
            
            # Convert datetime to ISO format
            elif isinstance(value, datetime):
                value = value.isoformat()
            
            result[column.name] = value
        
        return result
    
    def update_from_dict(self, data: dict, exclude: set = None) -> None:
        """
        Update model attributes from dictionary.
        
        Args:
            data: Dictionary of attributes to update
            exclude: Set of attribute names to exclude from update
        """
        exclude = exclude or set()
        exclude.update({'id', 'created_at', 'deleted_at'})
        
        for key, value in data.items():
            if key not in exclude and hasattr(self, key):
                setattr(self, key, value)
        
        # Update timestamp
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def create(cls, db: Session, **kwargs) -> "BaseModel":
        """
        Create a new instance and save to database.
        
        Args:
            db: Database session
            **kwargs: Model attributes
            
        Returns:
            Created model instance
        """
        instance = cls(**kwargs)
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance
    
    def save(self, db: Session) -> None:
        """
        Save changes to database.
        
        Args:
            db: Database session
        """
        db.add(self)
        db.commit()
        db.refresh(self)
    
    def delete(self, db: Session, hard: bool = False) -> None:
        """
        Delete the record.
        
        Args:
            db: Database session
            hard: If True, perform hard delete. Otherwise soft delete.
        """
        if hard:
            db.delete(self)
        else:
            self.soft_delete(db)
        db.commit()
    
    @classmethod
    def get_by_id(cls, db: Session, record_id: uuid.UUID) -> "BaseModel":
        """
        Get record by ID (excluding soft-deleted).
        
        Args:
            db: Database session
            record_id: Record UUID
            
        Returns:
            Model instance or None
        """
        return db.query(cls).filter(
            cls.id == record_id,
            cls.deleted_at.is_(None)
        ).first()
    
    @classmethod
    def get_all(cls, db: Session, include_deleted: bool = False) -> list:
        """
        Get all records.
        
        Args:
            db: Database session
            include_deleted: If True, include soft-deleted records
            
        Returns:
            List of model instances
        """
        query = db.query(cls)
        
        if not include_deleted:
            query = query.filter(cls.deleted_at.is_(None))
        
        return query.all()
    
    def __repr__(self) -> str:
        """String representation of model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


class MetadataMixin:
    """
    Mixin that adds a JSONB metadata column to models.
    
    Useful for storing flexible, schema-less data.
    """
    
    @declared_attr
    def metadata_(cls):
        """JSONB metadata column."""
        from sqlalchemy.dialects.postgresql import JSONB
        
        return Column(
            'metadata',
            JSONB,
            nullable=True,
            default={},
            comment="Additional metadata (JSONB)"
        )


class ClinicScopedMixin:
    """
    Mixin for models that belong to a specific clinic.
    
    Adds clinic_id foreign key and utility methods for
    multi-tenant data access.
    """
    
    @declared_attr
    def clinic_id(cls):
        """Foreign key to clinic."""
        from sqlalchemy import ForeignKey
        
        return Column(
            UUID(as_uuid=True),
            ForeignKey('clinics.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
            comment="ID of clinic this record belongs to"
        )
    
    @classmethod
    def get_by_clinic(
        cls,
        db: Session,
        clinic_id: uuid.UUID,
        include_deleted: bool = False
    ) -> list:
        """
        Get all records for a specific clinic.
        
        Args:
            db: Database session
            clinic_id: Clinic UUID
            include_deleted: Include soft-deleted records
            
        Returns:
            List of model instances
        """
        query = db.query(cls).filter(cls.clinic_id == clinic_id)
        
        if not include_deleted:
            query = query.filter(cls.deleted_at.is_(None))
        
        return query.all()


# Import all models here so Base.metadata has them all
# This will be populated as we create model files in Phase 2.3
def import_models():
    """
    Import all models to register them with Base.
    
    This ensures all tables are created when Base.metadata.create_all()
    is called.
    """
    try:
        # These imports will be added as models are created
        # from models.user import User
        # from models.clinic import Clinic
        # from models.patient import Patient
        # from models.prior_authorization import PriorAuthorization
        # ... etc
        pass
    except ImportError:
        # Models not yet created
        pass