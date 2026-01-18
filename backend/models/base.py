"""
Extended Base Model with Utilities
===================================

Provides additional model utilities beyond db/base.py for all models.

Author: Prior Auth AI Team
Version: 1.0.0
"""

from typing import Any, Dict, List, Optional, Type, TypeVar
from datetime import datetime
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from backend.db.base import Base as DBBase


T = TypeVar("T", bound="BaseModel")


class BaseModel(DBBase):
    """
    Extended base class for all models with additional utilities.
    
    Inherits from db.base.Base which provides:
    - UUID primary keys (id)
    - Timestamps (created_at, updated_at)
    - Soft delete (is_deleted, deleted_at)
    - Audit fields (created_by, updated_by)
    - Multi-tenant (clinic_id for scoped models)
    - Metadata (metadata_ JSONB field)
    
    This class adds:
    - to_dict() serialization
    - from_dict() deserialization
    - update() helper
    - Query helpers
    """
    
    __abstract__ = True
    
    def to_dict(
        self,
        exclude: Optional[List[str]] = None,
        include_relationships: bool = False
    ) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Args:
            exclude: List of field names to exclude
            include_relationships: Whether to include relationship data
            
        Returns:
            Dictionary representation of the model
            
        Example:
            user = User(email="test@example.com", first_name="John")
            data = user.to_dict(exclude=["password_hash"])
        """
        exclude = exclude or []
        result = {}
        
        # Get mapper for this model
        mapper = inspect(self.__class__)
        
        # Add column attributes
        for column in mapper.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                
                # Handle datetime serialization
                if isinstance(value, datetime):
                    result[column.name] = value.isoformat()
                else:
                    result[column.name] = value
        
        # Optionally add relationships
        if include_relationships:
            for relationship in mapper.relationships:
                if relationship.key not in exclude:
                    value = getattr(self, relationship.key)
                    
                    if value is None:
                        result[relationship.key] = None
                    elif isinstance(value, list):
                        # One-to-many relationship
                        result[relationship.key] = [
                            item.to_dict() if hasattr(item, 'to_dict') else str(item)
                            for item in value
                        ]
                    else:
                        # Many-to-one relationship
                        result[relationship.key] = (
                            value.to_dict() if hasattr(value, 'to_dict') else str(value)
                        )
        
        return result
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create model instance from dictionary.
        
        Args:
            data: Dictionary with model field data
            
        Returns:
            New model instance
            
        Example:
            user_data = {"email": "test@example.com", "first_name": "John"}
            user = User.from_dict(user_data)
        """
        # Filter to only include valid columns
        mapper = inspect(cls)
        valid_columns = {col.name for col in mapper.columns}
        filtered_data = {k: v for k, v in data.items() if k in valid_columns}
        
        return cls(**filtered_data)
    
    def update(self, data: Dict[str, Any], exclude: Optional[List[str]] = None) -> None:
        """
        Update model instance with dictionary data.
        
        Args:
            data: Dictionary with fields to update
            exclude: List of field names to exclude from update
            
        Example:
            user.update({"first_name": "Jane", "last_name": "Doe"})
        """
        exclude = exclude or []
        
        # Get valid columns
        mapper = inspect(self.__class__)
        valid_columns = {col.name for col in mapper.columns}
        
        # Update fields
        for key, value in data.items():
            if key in valid_columns and key not in exclude:
                setattr(self, key, value)
    
    @classmethod
    def get_by_id(cls: Type[T], db: Session, id: str) -> Optional[T]:
        """
        Get model instance by ID.
        
        Args:
            db: Database session
            id: UUID string
            
        Returns:
            Model instance or None if not found
        """
        return db.query(cls).filter(cls.id == id, cls.is_deleted == False).first()
    
    @classmethod
    def get_all(
        cls: Type[T],
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """
        Get all instances with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional dict of field: value filters
            
        Returns:
            List of model instances
        """
        query = db.query(cls).filter(cls.is_deleted == False)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(cls, field):
                    query = query.filter(getattr(cls, field) == value)
        
        return query.offset(skip).limit(limit).all()
    
    @classmethod
    def count(cls: Type[T], db: Session, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count instances matching filters.
        
        Args:
            db: Database session
            filters: Optional dict of field: value filters
            
        Returns:
            Count of matching records
        """
        query = db.query(cls).filter(cls.is_deleted == False)
        
        if filters:
            for field, value in filters.items():
                if hasattr(cls, field):
                    query = query.filter(getattr(cls, field) == value)
        
        return query.count()
    
    def soft_delete(self, deleted_by: Optional[str] = None) -> None:
        """
        Soft delete this instance.
        
        Args:
            deleted_by: UUID of user performing deletion
        """
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        if deleted_by:
            self.updated_by = deleted_by
    
    def __repr__(self) -> str:
        """String representation of model."""
        return f"<{self.__class__.__name__}(id={self.id})>"