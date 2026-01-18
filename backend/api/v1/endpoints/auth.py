"""
Authentication Endpoints
========================

Endpoints for user authentication including:
- Login
- Logout
- Token refresh
- Password reset

Author: Prior Auth AI Team
Version: 1.0.0
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db, get_current_user
from backend.core.config import settings
from backend.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key
)
from backend.core.exceptions import AuthenticationError, ValidationError
from backend.models import User, AuditLog, AuditAction
from backend.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    LogoutResponse
)

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    User login endpoint.
    
    Authenticates user and returns JWT tokens.
    
    - **email**: User email address
    - **password**: User password
    - **mfa_code**: MFA code (if MFA is enabled)
    
    Returns access token, refresh token, and user info.
    """
    # Get user by email
    user = User.get_active_by_email(db, credentials.email)
    
    if not user:
        # Log failed attempt
        AuditLog.log(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            description=f"Failed login attempt for {credentials.email}",
            success=False,
            error_message="User not found or inactive"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not user.verify_password(credentials.password):
        # Record failed login
        user.record_login_failure()
        db.commit()
        
        # Log failed attempt
        AuditLog.log(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            description=f"Failed login attempt for {user.email}",
            user_id=str(user.id),
            success=False,
            error_message="Invalid password"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if account is locked
    if user.is_locked:
        AuditLog.log(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            description=f"Login attempt for locked account: {user.email}",
            user_id=str(user.id),
            success=False,
            error_message="Account locked"
        )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked due to too many failed login attempts. Please try again later."
        )
    
    # TODO: Verify MFA code if MFA is enabled
    # if user.mfa_enabled and not verify_mfa_code(user.mfa_secret, credentials.mfa_code):
    #     raise HTTPException(status_code=401, detail="Invalid MFA code")
    
    # Create tokens
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    
    # Record successful login
    user.record_login_success()
    db.commit()
    
    # Log successful login
    AuditLog.log(
        db=db,
        action=AuditAction.LOGIN,
        description=f"User logged in: {user.email}",
        user_id=str(user.id),
        clinic_id=str(user.clinic_id) if user.clinic_id else None
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user.to_dict()
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token.
    
    Exchanges a valid refresh token for a new access token.
    
    - **refresh_token**: Valid refresh token
    
    Returns new access token.
    """
    try:
        # Decode refresh token
        payload = decode_token(request.refresh_token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise AuthenticationError("Invalid token")
        
        # Verify user still exists and is active
        user = User.get_by_id(db, user_id)
        
        if not user or not user.can_login:
            raise AuthenticationError("User not found or inactive")
        
        # Create new access token
        access_token = create_access_token(subject=str(user.id))
        
        return RefreshTokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    User logout endpoint.
    
    Logs out the current user.
    Note: With JWT, actual token invalidation would require a token blacklist.
    This endpoint primarily logs the logout event for audit purposes.
    """
    # Log logout event
    AuditLog.log(
        db=db,
        action=AuditAction.LOGOUT,
        description=f"User logged out: {current_user.email}",
        user_id=str(current_user.id),
        clinic_id=str(current_user.clinic_id) if current_user.clinic_id else None
    )
    
    return LogoutResponse(
        message="Logged out successfully."
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset.
    
    Sends password reset email to user.
    
    - **email**: User email address
    
    Always returns success message for security (doesn't reveal if email exists).
    """
    # Get user by email
    user = User.get_by_email(db, request.email)
    
    if user and user.is_active:
        # Generate password reset token
        reset_token = generate_api_key()
        
        # Save reset token (expires in 1 hour)
        from datetime import datetime, timedelta
        user.password_reset_token = reset_token
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        
        # TODO: Send password reset email
        # send_password_reset_email(user.email, reset_token)
        
        # Log password reset request
        AuditLog.log(
            db=db,
            action=AuditAction.PASSWORD_RESET,
            description=f"Password reset requested for {user.email}",
            user_id=str(user.id)
        )
    
    # Always return same message for security
    return ForgotPasswordResponse(
        message="If an account exists with this email, a password reset link has been sent."
    )


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password with token.
    
    Resets user password using reset token from email.
    
    - **token**: Password reset token
    - **new_password**: New password
    """
    from datetime import datetime
    
    # Find user with this reset token
    user = db.query(User).filter(
        User.password_reset_token == request.token,
        User.password_reset_expires > datetime.utcnow(),
        User.is_deleted == False
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Set new password
    user.set_password(request.new_password)
    
    # Clear reset token
    user.password_reset_token = None
    user.password_reset_expires = None
    
    # Reset failed login attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    
    db.commit()
    
    # Log password reset
    AuditLog.log(
        db=db,
        action=AuditAction.PASSWORD_RESET,
        description=f"Password reset completed for {user.email}",
        user_id=str(user.id)
    )
    
    return ResetPasswordResponse(
        message="Password has been reset successfully."
    )


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change password for authenticated user.
    
    - **current_password**: Current password
    - **new_password**: New password
    """
    # Verify current password
    if not current_user.verify_password(request.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Set new password
    current_user.set_password(request.new_password)
    db.commit()
    
    # Log password change
    AuditLog.log(
        db=db,
        action=AuditAction.PASSWORD_RESET,
        description=f"Password changed for {current_user.email}",
        user_id=str(current_user.id),
        clinic_id=str(current_user.clinic_id) if current_user.clinic_id else None
    )
    
    return ChangePasswordResponse(
        message="Password changed successfully."
    )