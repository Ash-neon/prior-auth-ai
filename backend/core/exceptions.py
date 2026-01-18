"""
Custom Exceptions Module
=========================

Defines custom exceptions for the application with proper
HTTP status codes and error messages.

Author: Prior Auth AI Team
Version: 1.0.0
"""

from typing import Any, Dict, Optional


class PriorAuthException(Exception):
    """
    Base exception class for all custom exceptions.
    
    Attributes:
        message: Error message
        status_code: HTTP status code
        error_code: Application-specific error code
        details: Additional error details
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details
            }
        }


# Authentication & Authorization Exceptions

class AuthenticationException(PriorAuthException):
    """Raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_FAILED",
            details=details
        )


class InvalidCredentialsException(AuthenticationException):
    """Raised when login credentials are invalid."""
    
    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message=message)


class TokenExpiredException(AuthenticationException):
    """Raised when JWT token has expired."""
    
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message=message, details={"error_type": "token_expired"})


class InvalidTokenException(AuthenticationException):
    """Raised when JWT token is invalid."""
    
    def __init__(self, message: str = "Invalid token"):
        super().__init__(message=message, details={"error_type": "invalid_token"})


class AuthorizationException(PriorAuthException):
    """Raised when user lacks required permissions."""
    
    def __init__(
        self,
        message: str = "Insufficient permissions",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=403,
            error_code="FORBIDDEN",
            details=details
        )


# Resource Exceptions

class ResourceNotFoundException(PriorAuthException):
    """Raised when a requested resource is not found."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        message: Optional[str] = None
    ):
        if not message:
            message = f"{resource_type} with ID '{resource_id}' not found"
        
        super().__init__(
            message=message,
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        )


class ResourceAlreadyExistsException(PriorAuthException):
    """Raised when attempting to create a duplicate resource."""
    
    def __init__(
        self,
        resource_type: str,
        identifier: str,
        message: Optional[str] = None
    ):
        if not message:
            message = f"{resource_type} with identifier '{identifier}' already exists"
        
        super().__init__(
            message=message,
            status_code=409,
            error_code="RESOURCE_ALREADY_EXISTS",
            details={
                "resource_type": resource_type,
                "identifier": identifier
            }
        )


class InvalidStateTransitionException(PriorAuthException):
    """Raised when attempting an invalid state transition."""
    
    def __init__(
        self,
        resource_type: str,
        current_state: str,
        target_state: str,
        message: Optional[str] = None
    ):
        if not message:
            message = (
                f"Cannot transition {resource_type} from "
                f"'{current_state}' to '{target_state}'"
            )
        
        super().__init__(
            message=message,
            status_code=400,
            error_code="INVALID_STATE_TRANSITION",
            details={
                "resource_type": resource_type,
                "current_state": current_state,
                "target_state": target_state
            }
        )


# Validation Exceptions

class ValidationException(PriorAuthException):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str = "Validation error",
        errors: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details={"errors": errors or {}}
        )


class MissingFieldException(ValidationException):
    """Raised when a required field is missing."""
    
    def __init__(self, field_name: str):
        super().__init__(
            message=f"Required field '{field_name}' is missing",
            errors={field_name: "This field is required"}
        )


class InvalidFormatException(ValidationException):
    """Raised when a field has an invalid format."""
    
    def __init__(self, field_name: str, expected_format: str):
        super().__init__(
            message=f"Field '{field_name}' has invalid format",
            errors={
                field_name: f"Expected format: {expected_format}"
            }
        )


# Business Logic Exceptions

class PANotFoundException(ResourceNotFoundException):
    """Raised when a PA request is not found."""
    
    def __init__(self, pa_id: str):
        super().__init__(
            resource_type="Prior Authorization",
            resource_id=pa_id
        )


class PatientNotFoundException(ResourceNotFoundException):
    """Raised when a patient is not found."""
    
    def __init__(self, patient_id: str):
        super().__init__(
            resource_type="Patient",
            resource_id=patient_id
        )


class DocumentNotFoundException(ResourceNotFoundException):
    """Raised when a document is not found."""
    
    def __init__(self, document_id: str):
        super().__init__(
            resource_type="Document",
            resource_id=document_id
        )


class ClinicNotFoundException(ResourceNotFoundException):
    """Raised when a clinic is not found."""
    
    def __init__(self, clinic_id: str):
        super().__init__(
            resource_type="Clinic",
            resource_id=clinic_id
        )


class UserNotFoundException(ResourceNotFoundException):
    """Raised when a user is not found."""
    
    def __init__(self, user_id: str):
        super().__init__(
            resource_type="User",
            resource_id=user_id
        )


# External Service Exceptions

class ExternalServiceException(PriorAuthException):
    """Raised when an external service call fails."""
    
    def __init__(
        self,
        service_name: str,
        message: str,
        status_code: int = 503,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"{service_name} error: {message}",
            status_code=status_code,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={
                "service_name": service_name,
                **(details or {})
            }
        )


class AIServiceException(ExternalServiceException):
    """Raised when AI service (Claude API) fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            service_name="AI Service (Claude)",
            message=message,
            details=details
        )


class OCRException(ExternalServiceException):
    """Raised when OCR processing fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            service_name="OCR Service",
            message=message,
            details=details
        )


class FaxServiceException(ExternalServiceException):
    """Raised when fax service fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            service_name="Fax Service",
            message=message,
            details=details
        )


class PayerAPIException(ExternalServiceException):
    """Raised when payer API call fails."""
    
    def __init__(
        self,
        payer_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            service_name=f"Payer API ({payer_name})",
            message=message,
            details=details
        )


# Rate Limiting Exception

class RateLimitExceededException(PriorAuthException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, retry_after: int):
        super().__init__(
            message=f"Rate limit exceeded. Please retry after {retry_after} seconds.",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after}
        )


# File/Storage Exceptions

class FileUploadException(PriorAuthException):
    """Raised when file upload fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="FILE_UPLOAD_ERROR",
            details=details
        )


class FileTooLargeException(FileUploadException):
    """Raised when uploaded file exceeds size limit."""
    
    def __init__(self, max_size_mb: int):
        super().__init__(
            message=f"File size exceeds maximum allowed size of {max_size_mb}MB",
            details={"max_size_mb": max_size_mb}
        )


class UnsupportedFileTypeException(FileUploadException):
    """Raised when uploaded file type is not supported."""
    
    def __init__(self, file_type: str, allowed_types: list):
        super().__init__(
            message=f"File type '{file_type}' is not supported",
            details={
                "file_type": file_type,
                "allowed_types": allowed_types
            }
        )


class StorageException(PriorAuthException):
    """Raised when storage operation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="STORAGE_ERROR",
            details=details
        )


# Agent/Workflow Exceptions

class WorkflowException(PriorAuthException):
    """Raised when agent workflow fails."""
    
    def __init__(
        self,
        workflow_id: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=500,
            error_code="WORKFLOW_ERROR",
            details={
                "workflow_id": workflow_id,
                **(details or {})
            }
        )


class AgentExecutionException(PriorAuthException):
    """Raised when agent execution fails."""
    
    def __init__(
        self,
        agent_role: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"Agent '{agent_role}' execution failed: {message}",
            status_code=500,
            error_code="AGENT_EXECUTION_ERROR",
            details={
                "agent_role": agent_role,
                **(details or {})
            }
        )


# Database Exceptions

class DatabaseException(PriorAuthException):
    """Raised when database operation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR",
            details=details
        )


class IntegrityException(DatabaseException):
    """Raised when database integrity constraint is violated."""
    
    def __init__(self, message: str, constraint: Optional[str] = None):
        super().__init__(
            message=message,
            details={"constraint": constraint} if constraint else None
        )


# Configuration Exception

class ConfigurationException(PriorAuthException):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="CONFIGURATION_ERROR",
            details=details
        )