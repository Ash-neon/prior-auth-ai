"""
API Dependencies
================

Shared dependencies for FastAPI endpoints including:
- Database session injection
- Authentication and authorization
- Current user retrieval
- Permission checking

Author: Prior Auth AI Team
Version: 1.0.0
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.security import decode_token
from backend.core.exceptions import AuthenticationError, AuthorizationError
from backend.db.session import SessionLocal
from backend.models import User, UserRole, AuditLog, AuditAction


# Security scheme for JWT tokens
security = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    
    Yields:
        Database session
        
    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP bearer token
        db: Database session
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If token is invalid or user not found
        
    Example:
        @app.get("/profile")
        def get_profile(current_user: User = Depends(get_current_user)):
            return current_user.to_dict()
    """
    try:
        # Decode token
        token = credentials.credentials
        payload = decode_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise AuthenticationError("Invalid token payload")
        
        # Get user from database
        user = User.get_by_id(db, user_id)
        
        if user is None:
            raise AuthenticationError("User not found")
        
        if not user.can_login:
            raise AuthenticationError("User account is not active")
        
        return user
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is active.
    
    Args:
        current_user: Current user from token
        
    Returns:
        Active user
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return current_user


def require_role(required_role: UserRole):
    """
    Dependency factory to check if user has required role.
    
    Args:
        required_role: Minimum required role
        
    Returns:
        Dependency function
        
    Example:
        @app.post("/admin/settings")
        def update_settings(
            current_user: User = Depends(require_role(UserRole.ADMIN))
        ):
            # Only admins can access
            pass
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not current_user.has_permission(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role.value} role or higher"
            )
        return current_user
    
    return role_checker


# Convenience dependencies for specific roles

async def get_admin_user(
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> User:
    """Dependency to require admin role."""
    return current_user


async def get_clinician_user(
    current_user: User = Depends(require_role(UserRole.CLINICIAN))
) -> User:
    """Dependency to require clinician role or higher."""
    return current_user


async def get_staff_user(
    current_user: User = Depends(require_role(UserRole.STAFF))
) -> User:
    """Dependency to require staff role or higher."""
    return current_user


# Audit logging helper

async def log_api_call(
    endpoint: str,
    current_user: Optional[User] = None,
    db: Session = Depends(get_db),
    success: bool = True,
    error_message: Optional[str] = None,
    details: Optional[dict] = None
):
    """
    Log API call to audit log.
    
    Args:
        endpoint: API endpoint path
        current_user: Current user (if authenticated)
        db: Database session
        success: Whether call succeeded
        error_message: Error message if failed
        details: Additional details
    """
    if settings.ENABLE_AUDIT_LOGGING:
        AuditLog.log(
            db=db,
            action=AuditAction.API_CALL,
            description=f"API call: {endpoint}",
            user_id=str(current_user.id) if current_user else None,
            clinic_id=str(current_user.clinic_id) if current_user and current_user.clinic_id else None,
            success=success,
            error_message=error_message,
            details=details or {}
        )


# Pagination helper

class PaginationParams:
    """
    Reusable pagination parameters.
    
    Example:
        @app.get("/items")
        def get_items(
            pagination: PaginationParams = Depends(),
            db: Session = Depends(get_db)
        ):
            items = db.query(Item).offset(pagination.skip).limit(pagination.limit).all()
            return items
    """
    
    def __init__(
        self,
        page: int = 1,
        per_page: int = 20,
        max_per_page: int = 100
    ):
        self.page = max(1, page)
        self.per_page = min(per_page, max_per_page)
        self.skip = (self.page - 1) * self.per_page
        self.limit = self.per_page
    
    @property
    def offset(self) -> int:
        """Get offset for SQL query."""
        return self.skip


# Clinic access checker

async def verify_clinic_access(
    clinic_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> bool:
    """
    Verify user has access to clinic resources.
    
    Args:
        clinic_id: Clinic ID to check
        current_user: Current user
        db: Database session
        
    Returns:
        True if user has access
        
    Raises:
        HTTPException: If user doesn't have access
    """
    # Admins can access any clinic
    if current_user.role == UserRole.ADMIN:
        return True
    
    # Users can only access their own clinic
    if str(current_user.clinic_id) != clinic_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this clinic's resources"
        )
    
    return True


# Optional authentication (for public endpoints)

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    
    Useful for endpoints that have different behavior for authenticated vs anonymous users.
    
    Args:
        credentials: Optional HTTP bearer token
        db: Database session
        
    Returns:
        User if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        payload = decode_token(token)
        user_id = payload.get("sub")
        
        if user_id:
            user = User.get_by_id(db, user_id)
            if user and user.can_login:
                return user
    except Exception:
        pass
    
    return None