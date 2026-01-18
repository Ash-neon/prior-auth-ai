"""
Payer API Endpoints

Handles payer CRUD operations.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models.user import User
from backend.models.payer import Payer, PayerType
from backend.schemas.payer import (
    PayerCreate,
    PayerUpdate,
    PayerResponse,
    PayerSummaryResponse,
    PayerListResponse,
)
from backend.api.dependencies import get_current_user
from backend.utils.audit import AuditLogger
from backend.core.security import get_password_hash

router = APIRouter()
audit_logger = AuditLogger()


@router.post("", response_model=PayerResponse, status_code=status.HTTP_201_CREATED)
async def create_payer(
    payer_data: PayerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PayerResponse:
    """Create a new payer."""
    # Check for duplicate payer_id
    stmt = select(Payer).where(Payer.payer_id == payer_data.payer_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payer ID already exists",
        )
    
    payer_dict = payer_data.model_dump(exclude={"portal_password"})
    
    # Hash portal password if provided
    if payer_data.portal_password:
        payer_dict["portal_password_hash"] = get_password_hash(payer_data.portal_password)
    
    payer = Payer(**payer_dict)
    
    db.add(payer)
    await db.commit()
    await db.refresh(payer)
    
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="payer_create",
        resource_type="payer",
        resource_id=str(payer.id),
    )
    
    return PayerResponse.model_validate(payer)


@router.get("/{payer_id}", response_model=PayerResponse)
async def get_payer(
    payer_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PayerResponse:
    """Get a specific payer by ID."""
    stmt = select(Payer).where(Payer.id == payer_id)
    result = await db.execute(stmt)
    payer = result.scalar_one_or_none()
    
    if not payer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payer not found",
        )
    
    return PayerResponse.model_validate(payer)


@router.get("", response_model=PayerListResponse)
async def list_payers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    payer_type: Optional[PayerType] = None,
    is_active: Optional[bool] = None,
    has_api_integration: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PayerListResponse:
    """List payers with filtering and pagination."""
    query = select(Payer)
    count_query = select(func.count()).select_from(Payer)
    
    if payer_type:
        query = query.where(Payer.payer_type == payer_type)
        count_query = count_query.where(Payer.payer_type == payer_type)
    
    if is_active is not None:
        query = query.where(Payer.is_active == is_active)
        count_query = count_query.where(Payer.is_active == is_active)
    
    if has_api_integration is not None:
        query = query.where(Payer.has_api_integration == has_api_integration)
        count_query = count_query.where(Payer.has_api_integration == has_api_integration)
    
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                Payer.name.ilike(pattern),
                Payer.payer_id.ilike(pattern),
            )
        )
        count_query = count_query.where(
            or_(
                Payer.name.ilike(pattern),
                Payer.payer_id.ilike(pattern),
            )
        )
    
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    query = query.order_by(Payer.name).offset(skip).limit(limit)
    result = await db.execute(query)
    payers = result.scalars().all()
    
    return PayerListResponse(
        items=[PayerSummaryResponse.model_validate(p) for p in payers],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.patch("/{payer_id}", response_model=PayerResponse)
async def update_payer(
    payer_id: UUID,
    payer_update: PayerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PayerResponse:
    """Update a payer."""
    stmt = select(Payer).where(Payer.id == payer_id)
    result = await db.execute(stmt)
    payer = result.scalar_one_or_none()
    
    if not payer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payer not found",
        )
    
    update_data = payer_update.model_dump(exclude_unset=True, exclude={"portal_password"})
    
    # Handle portal password update
    if payer_update.portal_password:
        update_data["portal_password_hash"] = get_password_hash(payer_update.portal_password)
    
    for field, value in update_data.items():
        setattr(payer, field, value)
    
    await db.commit()
    await db.refresh(payer)
    
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="payer_update",
        resource_type="payer",
        resource_id=str(payer.id),
    )
    
    return PayerResponse.model_validate(payer)


@router.delete("/{payer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payer(
    payer_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a payer (admin only)."""
    from backend.models.user import UserRole
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete payers",
        )
    
    stmt = select(Payer).where(Payer.id == payer_id)
    result = await db.execute(stmt)
    payer = result.scalar_one_or_none()
    
    if not payer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payer not found",
        )
    
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="payer_delete",
        resource_type="payer",
        resource_id=str(payer.id),
    )
    
    await db.delete(payer)
    await db.commit()