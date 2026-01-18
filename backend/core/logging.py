"""
Logging Configuration Module
============================

Configures structured logging for the application with:
- JSON formatting for production
- PHI redaction for HIPAA compliance
- Request ID tracking
- Performance metrics
- Different log levels per environment

Author: Prior Auth AI Team
Version: 1.0.0
"""

import logging
import sys
import json
import re
from typing import Any, Dict, Optional
from datetime import datetime
from pythonjsonlogger import jsonlogger

from core.config import settings


# PHI patterns to redact from logs
PHI_PATTERNS = [
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '[SSN]'),  # SSN
    (re.compile(r'\b\d{2}/\d{2}/\d{4}\b'), '[DOB]'),  # Date of birth
    (re.compile(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'), '[NAME]'),  # Names (basic)
    (re.compile(r'\b\d{10}\b'), '[PHONE]'),  # Phone numbers
    (re.compile(r'\b[A-Z]\d{5,}\b'), '[MRN]'),  # Medical record numbers
]


class PHIRedactingFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that redacts PHI from log messages.
    Used in production to ensure HIPAA compliance.
    """
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """
        Add custom fields to log record and redact PHI.
        
        Args:
            log_record: The log record dictionary
            record: The logging.LogRecord instance
            message_dict: Additional message data
        """
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add logger name
        log_record['logger'] = record.name
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        
        if hasattr(record, 'clinic_id'):
            log_record['clinic_id'] = record.clinic_id
        
        # Redact PHI from message
        if 'message' in log_record:
            log_record['message'] = self._redact_phi(str(log_record['message']))
        
        # Redact PHI from any string fields
        for key, value in log_record.items():
            if isinstance(value, str):
                log_record[key] = self._redact_phi(value)
    
    def _redact_phi(self, text: str) -> str:
        """
        Redact PHI patterns from text.
        
        Args:
            text: Text that may contain PHI
            
        Returns:
            Text with PHI redacted
        """
        for pattern, replacement in PHI_PATTERNS:
            text = pattern.sub(replacement, text)
        return text


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for development environments.
    Makes logs easier to read in console.
    """
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Format message
        message = super().format(record)
        
        # Add color
        colored_level = f"{log_color}{record.levelname:8}{reset_color}"
        colored_message = f"{log_color}{message}{reset_color}"
        
        return f"{timestamp} | {colored_level} | {record.name:30} | {colored_message}"


class RequestContextFilter(logging.Filter):
    """
    Filter that adds request context to log records.
    Context is stored in context variables (e.g., from FastAPI middleware).
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add request context to log record if available.
        
        Args:
            record: Log record to augment
            
        Returns:
            True (always pass the record through)
        """
        # Try to get context from context variables
        # (These would be set by FastAPI middleware)
        try:
            from contextvars import copy_context
            ctx = copy_context()
            
            # Add request ID if available
            if hasattr(ctx, 'request_id'):
                record.request_id = ctx.request_id
            
            # Add user ID if available
            if hasattr(ctx, 'user_id'):
                record.user_id = ctx.user_id
            
            # Add clinic ID if available
            if hasattr(ctx, 'clinic_id'):
                record.clinic_id = ctx.clinic_id
                
        except Exception:
            # Context not available, skip
            pass
        
        return True


def setup_logging() -> None:
    """
    Configure logging for the application.
    
    Sets up:
    - Root logger
    - Console handler
    - File handler (if configured)
    - Formatters based on environment
    - Log level based on configuration
    """
    # Get root logger
    root_logger = logging.getLogger()
    
    # Set log level from config
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Choose formatter based on environment
    if settings.APP_ENV == "production":
        # Use JSON formatter with PHI redaction in production
        formatter = PHIRedactingFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Use colored formatter in development
        formatter = ColoredFormatter(
            '%(message)s'
        )
    
    console_handler.setFormatter(formatter)
    
    # Add request context filter
    console_handler.addFilter(RequestContextFilter())
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Optionally add file handler
    if settings.LOG_FILE:
        file_handler = logging.FileHandler(settings.LOG_FILE)
        file_handler.setLevel(log_level)
        
        # Always use JSON format for file logs
        file_formatter = PHIRedactingFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(RequestContextFilter())
        
        root_logger.addHandler(file_handler)
    
    # Set log levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.INFO)
    
    # Log startup message
    root_logger.info(
        f"Logging configured: level={settings.LOG_LEVEL}, "
        f"env={settings.APP_ENV}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
        
    Example:
        logger = get_logger(__name__)
        logger.info("Processing PA request", extra={"pa_id": "123"})
    """
    return logging.getLogger(name)


class AuditLogger:
    """
    Specialized logger for audit trail.
    
    All PHI access and modifications must be logged through this logger
    for HIPAA compliance.
    """
    
    def __init__(self):
        self.logger = get_logger("audit")
    
    def log_phi_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log PHI access event.
        
        Args:
            user_id: ID of user accessing PHI
            resource_type: Type of resource (patient, pa, document, etc.)
            resource_id: ID of specific resource
            action: Action performed (read, write, delete)
            ip_address: IP address of request
            metadata: Additional context
        """
        self.logger.info(
            f"PHI Access: {action} {resource_type}",
            extra={
                "event_type": "phi_access",
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": action,
                "ip_address": ip_address,
                "metadata": metadata or {}
            }
        )
    
    def log_authentication(
        self,
        user_id: Optional[str],
        success: bool,
        ip_address: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> None:
        """
        Log authentication attempt.
        
        Args:
            user_id: User ID (if known)
            success: Whether authentication succeeded
            ip_address: IP address of attempt
            failure_reason: Reason for failure (if applicable)
        """
        level = logging.INFO if success else logging.WARNING
        
        self.logger.log(
            level,
            f"Authentication {'succeeded' if success else 'failed'}",
            extra={
                "event_type": "authentication",
                "user_id": user_id,
                "success": success,
                "ip_address": ip_address,
                "failure_reason": failure_reason
            }
        )
    
    def log_data_modification(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        operation: str,
        changes: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log data modification event.
        
        Args:
            user_id: User making the change
            resource_type: Type of resource modified
            resource_id: ID of resource
            operation: create, update, or delete
            changes: Dict of changed fields (PHI will be redacted)
        """
        self.logger.info(
            f"Data modification: {operation} {resource_type}",
            extra={
                "event_type": "data_modification",
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "operation": operation,
                "changes": changes or {}
            }
        )


# Global audit logger instance
audit_logger = AuditLogger()


# Convenience function for performance logging
class PerformanceLogger:
    """
    Logger for tracking performance metrics.
    """
    
    def __init__(self):
        self.logger = get_logger("performance")
    
    def log_duration(
        self,
        operation: str,
        duration_ms: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log operation duration.
        
        Args:
            operation: Name of operation
            duration_ms: Duration in milliseconds
            metadata: Additional context
        """
        self.logger.info(
            f"{operation} completed in {duration_ms:.2f}ms",
            extra={
                "event_type": "performance",
                "operation": operation,
                "duration_ms": duration_ms,
                "metadata": metadata or {}
            }
        )


# Global performance logger instance
performance_logger = PerformanceLogger()


# Initialize logging on module import
setup_logging()