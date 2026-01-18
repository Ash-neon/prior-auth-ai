"""
Audit Log Model
===============

Comprehensive audit trail for HIPAA compliance and security monitoring.

Tracks all significant actions in the system:
- User authentication events
- PHI access (view, edit, delete)
- PA workflow actions
- Administrative changes
- API calls

Author: Prior Auth AI Team
Version: 1.0.0
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Index, Enum as SQLEnum, Text
)
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET

from backend.models.base import BaseModel


class AuditAction(str, Enum):
    """Audit action types."""
    
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_RESET = "password_reset"
    
    # User management
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"
    
    # PHI Access (HIPAA-critical)
    PATIENT_VIEWED = "patient_viewed"
    PATIENT_CREATED = "patient_created"
    PATIENT_UPDATED = "patient_updated"
    PATIENT_DELETED = "patient_deleted"
    
    # PA Actions
    PA_CREATED = "pa_created"
    PA_VIEWED = "pa_viewed"
    PA_UPDATED = "pa_updated"
    PA_SUBMITTED = "pa_submitted"
    PA_APPROVED = "pa_approved"
    PA_DENIED = "pa_denied"
    PA_DELETED = "pa_deleted"
    
    # Document Actions
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_VIEWED = "document_viewed"
    DOCUMENT_DOWNLOADED = "document_downloaded"
    DOCUMENT_DELETED = "document_deleted"
    
    # Administrative
    CLINIC_CREATED = "clinic_created"
    CLINIC_UPDATED = "clinic_updated"
    SETTING_CHANGED = "setting_changed"
    
    # Agent Actions
    AGENT_WORKFLOW_STARTED = "agent_workflow_started"
    AGENT_WORKFLOW_COMPLETED = "agent_workflow_completed"
    AGENT_WORKFLOW_FAILED = "agent_workflow_failed"
    
    # System
    API_CALL = "api_call"
    EXPORT = "export"
    BULK_ACTION = "bulk_action"


class AuditLog(BaseModel):
    """
    Audit log for comprehensive activity tracking.
    
    Attributes:
        action: Action type (enum)
        user_id: User who performed the action
        clinic_id: Clinic context (inherited from BaseModel)
        resource_type: Type of resource affected (e.g., "patient", "pa")
        resource_id: ID of affected resource
        description: Human-readable description
        details: Additional details (JSONB)
        ip_address: IP address of request
        user_agent: Browser/client user agent
        session_id: Session identifier
        request_id: Request tracking ID
        success: Whether action succeeded
        error_message: Error message if failed
        duration_ms: Action duration in milliseconds
    """
    
    __tablename__ = "audit_logs"
    
    # Action details
    action = Column(SQLEnum(AuditAction), nullable=False, index=True)
    
    # Actor
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Clinic context (inherited from BaseModel but important for auditing)
    # clinic_id already defined in BaseModel
    
    # Resource affected
    resource_type = Column(String(50), nullable=True, index=True)
    resource_id = Column(String(255), nullable=True, index=True)
    
    # Action details
    description = Column(Text, nullable=False)
    details = Column(JSONB, default={}, nullable=False)
    
    # Request context
    ip_address = Column(INET, nullable=True)
    user_agent = Column(String(500), nullable=True)
    session_id = Column(String(255), nullable=True)
    request_id = Column(String(255), nullable=True, index=True)
    
    # Result
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    
    # Timestamp (created_at inherited from BaseModel)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_audit_action_time", "action", "created_at"),
        Index("idx_audit_user_time", "user_id", "created_at"),
        Index("idx_audit_clinic_time", "clinic_id", "created_at"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        Index("idx_audit_request", "request_id"),
    )
    
    @classmethod
    def log(
        cls,
        db: Session,
        action: AuditAction,
        description: str,
        user_id: Optional[str] = None,
        clinic_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> "AuditLog":
        """
        Create an audit log entry.
        
        Args:
            db: Database session
            action: Action type
            description: Human-readable description
            user_id: User who performed action
            clinic_id: Clinic context
            resource_type: Type of resource
            resource_id: ID of resource
            details: Additional details
            ip_address: Client IP address
            user_agent: Client user agent
            session_id: Session ID
            request_id: Request tracking ID
            success: Whether action succeeded
            error_message: Error message if failed
            duration_ms: Action duration
            
        Returns:
            Created audit log entry
            
        Example:
            AuditLog.log(
                db=db,
                action=AuditAction.PA_CREATED,
                description="Created PA #PA-2026-001",
                user_id=current_user.id,
                clinic_id=clinic.id,
                resource_type="prior_authorization",
                resource_id=pa.id,
                details={"pa_number": pa.pa_number}
            )
        """
        log_entry = cls(
            action=action,
            description=description,
            user_id=user_id,
            clinic_id=clinic_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            request_id=request_id,
            success=success,
            error_message=error_message,
            duration_ms=duration_ms
        )
        
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        
        return log_entry
    
    @classmethod
    def get_by_user(
        cls,
        db: Session,
        user_id: str,
        limit: int = 100,
        skip: int = 0
    ) -> List["AuditLog"]:
        """
        Get audit logs for a specific user.
        
        Args:
            db: Database session
            user_id: User UUID
            limit: Maximum records to return
            skip: Number of records to skip
            
        Returns:
            List of audit logs
        """
        return db.query(cls).filter(
            cls.user_id == user_id
        ).order_by(
            cls.created_at.desc()
        ).limit(limit).offset(skip).all()
    
    @classmethod
    def get_by_resource(
        cls,
        db: Session,
        resource_type: str,
        resource_id: str,
        limit: int = 100
    ) -> List["AuditLog"]:
        """
        Get audit logs for a specific resource.
        
        Args:
            db: Database session
            resource_type: Type of resource
            resource_id: Resource UUID
            limit: Maximum records
            
        Returns:
            List of audit logs
        """
        return db.query(cls).filter(
            cls.resource_type == resource_type,
            cls.resource_id == resource_id
        ).order_by(
            cls.created_at.desc()
        ).limit(limit).all()
    
    @classmethod
    def get_phi_access_logs(
        cls,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        clinic_id: Optional[str] = None
    ) -> List["AuditLog"]:
        """
        Get PHI access logs for compliance reporting.
        
        Args:
            db: Database session
            start_date: Start of date range
            end_date: End of date range
            clinic_id: Optional clinic filter
            
        Returns:
            List of PHI access logs
        """
        phi_actions = [
            AuditAction.PATIENT_VIEWED,
            AuditAction.PATIENT_CREATED,
            AuditAction.PATIENT_UPDATED,
            AuditAction.PA_VIEWED,
            AuditAction.DOCUMENT_VIEWED,
            AuditAction.DOCUMENT_DOWNLOADED
        ]
        
        query = db.query(cls).filter(
            cls.action.in_(phi_actions),
            cls.created_at >= start_date,
            cls.created_at <= end_date
        )
        
        if clinic_id:
            query = query.filter(cls.clinic_id == clinic_id)
        
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_failed_actions(
        cls,
        db: Session,
        hours: int = 24,
        clinic_id: Optional[str] = None
    ) -> List["AuditLog"]:
        """
        Get failed actions in the last N hours.
        
        Args:
            db: Database session
            hours: Number of hours to look back
            clinic_id: Optional clinic filter
            
        Returns:
            List of failed audit logs
        """
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        query = db.query(cls).filter(
            cls.success == False,
            cls.created_at >= cutoff
        )
        
        if clinic_id:
            query = query.filter(cls.clinic_id == clinic_id)
        
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_security_events(
        cls,
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> List["AuditLog"]:
        """
        Get security-related events.
        
        Args:
            db: Database session
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of security events
        """
        security_actions = [
            AuditAction.LOGIN,
            AuditAction.LOGIN_FAILED,
            AuditAction.PASSWORD_RESET,
            AuditAction.USER_CREATED,
            AuditAction.USER_DELETED,
            AuditAction.USER_DEACTIVATED
        ]
        
        return db.query(cls).filter(
            cls.action.in_(security_actions),
            cls.created_at >= start_date,
            cls.created_at <= end_date
        ).order_by(cls.created_at.desc()).all()
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<AuditLog(action={self.action}, user_id={self.user_id}, resource={self.resource_type}:{self.resource_id})>"


# Import after model definition
from sqlalchemy import Boolean, Integer