"""
User Management API Endpoints

Provides user CRUD operations with RBAC enforcement.
Regular users can view/update their own profile.
Admins can manage all users.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.security import get_password_hash
from backend.models.user import User, UserRole
from backend.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
)
from backend.api.dependencies import (
    get_current_user,
    require_role,
)
from backend.utils.audit import AuditLogger

router = APIRouter()
audit_logger = AuditLogger()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current authenticated user's profile.
    
    Returns:
        Current user's profile information
    """
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="profile_view",
        resource_type="user",
        resource_id=str(current_user.id),
        details={"endpoint": "/users/me"},
    )
    
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Update current authenticated user's profile.
    
    Users can update:
    - email (must be unique)
    - full_name
    - preferences
    
    Users CANNOT update:
    - role (requires admin)
    - is_active (requires admin)
    - is_superuser (requires admin)
    
    Args:
        user_update: Fields to update
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Updated user profile
        
    Raises:
        HTTPException: If email already exists or invalid update
    """
    # Prevent non-admins from escalating privileges
    if user_update.role is not None and user_update.role != current_user.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own role",
        )
    
    if user_update.is_active is not None and user_update.is_active != current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own active status",
        )
    
    if user_update.is_superuser is not None and user_update.is_superuser != current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own superuser status",
        )
    
    # Check email uniqueness if being updated
    if user_update.email and user_update.email != current_user.email:
        stmt = select(User).where(User.email == user_update.email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
    
    # Apply updates
    update_data = user_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="profile_update",
        resource_type="user",
        resource_id=str(current_user.id),
        details={
            "updated_fields": list(update_data.keys()),
        },
    )
    
    return UserResponse.model_validate(current_user)


@router.get("", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by email or full name"),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> UserListResponse:
    """
    List all users with filtering and pagination.
    
    **Admin only endpoint.**
    
    Args:
        skip: Number of records to skip
        limit: Maximum records to return
        role: Filter by user role
        is_active: Filter by active status
        search: Search in email and full_name fields
        current_user: Admin user
        db: Database session
        
    Returns:
        Paginated list of users with total count
    """
    # Build base query
    query = select(User)
    count_query = select(func.count()).select_from(User)
    
    # Apply filters
    if role is not None:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (User.email.ilike(search_pattern)) | 
            (User.full_name.ilike(search_pattern))
        )
        count_query = count_query.where(
            (User.email.ilike(search_pattern)) | 
            (User.full_name.ilike(search_pattern))
        )
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Apply pagination and ordering
    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()
    
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="user_list",
        resource_type="user",
        details={
            "filters": {
                "role": role.value if role else None,
                "is_active": is_active,
                "search": search,
            },
            "pagination": {"skip": skip, "limit": limit},
            "result_count": len(users),
        },
    )
    
    return UserListResponse(
        users=[UserResponse.model_validate(user) for user in users],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Create a new user.
    
    **Admin only endpoint.**
    
    Only super admins can create other admins or super admins.
    Regular admins can only create regular users and analysts.
    
    Args:
        user_in: User creation data
        current_user: Admin user
        db: Database session
        
    Returns:
        Created user
        
    Raises:
        HTTPException: If email exists or insufficient permissions
    """
    # Check if email already exists
    stmt = select(User).where(User.email == user_in.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Permission check: only super admin can create admin/super_admin users
    if user_in.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        if current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admins can create admin users",
            )
    
    # Only super admin can create superuser accounts
    if user_in.is_superuser and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can create superuser accounts",
        )
    
    # Hash password
    hashed_password = get_password_hash(user_in.password)
    
    # Create user
    user_data = user_in.model_dump(exclude={"password"})
    new_user = User(**user_data, hashed_password=hashed_password)
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="user_create",
        resource_type="user",
        resource_id=str(new_user.id),
        details={
            "created_user_email": new_user.email,
            "created_user_role": new_user.role.value,
        },
    )
    
    return UserResponse.model_validate(new_user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Update any user's profile.
    
    **Admin only endpoint.**
    
    Only super admins can:
    - Update admin or super admin users
    - Change user roles to admin/super_admin
    - Set is_superuser flag
    
    Args:
        user_id: User ID to update
        user_update: Fields to update
        current_user: Admin user
        db: Database session
        
    Returns:
        Updated user
        
    Raises:
        HTTPException: If user not found or insufficient permissions
    """
    # Get target user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Permission checks
    # Only super admin can modify admin/super_admin users
    if user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        if current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admins can modify admin users",
            )
    
    # Only super admin can change role to admin/super_admin
    if user_update.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        if current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admins can assign admin roles",
            )
    
    # Only super admin can set is_superuser
    if user_update.is_superuser is not None:
        if current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admins can modify superuser status",
            )
    
    # Check email uniqueness if being updated
    if user_update.email and user_update.email != user.email:
        stmt = select(User).where(User.email == user_update.email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
    
    # Apply updates
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Handle password update separately
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="user_update",
        resource_type="user",
        resource_id=str(user.id),
        details={
            "target_user_email": user.email,
            "updated_fields": list(update_data.keys()),
        },
    )
    
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a user.
    
    **Super admin only endpoint.**
    
    Users cannot delete themselves.
    
    Args:
        user_id: User ID to delete
        current_user: Super admin user
        db: Database session
        
    Raises:
        HTTPException: If user not found or attempting self-deletion
    """
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )
    
    # Get target user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="user_delete",
        resource_type="user",
        resource_id=str(user.id),
        details={
            "deleted_user_email": user.email,
            "deleted_user_role": user.role.value,
        },
    )
    
    await db.delete(user)
    await db.commit()