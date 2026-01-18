"""
Provider API Endpoints

Handles provider CRUD operations.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models.user import User
from backend.models.provider import Provider, ProviderType, ProviderSpecialty
from backend.schemas.provider import (
    ProviderCreate,
    ProviderUpdate,
    ProviderResponse,
    ProviderSummaryResponse,
    ProviderListResponse,
)
from backend.api.dependencies import get_current_user
from backend.utils.audit import AuditLogger

router = APIRouter()
audit_logger = AuditLogger()


@router.post("", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    provider_data: ProviderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProviderResponse:
    """Create a new provider."""
    # Check for duplicate NPI
    stmt = select(Provider).where(Provider.npi == provider_data.npi)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="NPI already exists",
        )
    
    provider_dict = provider_data.model_dump()
    provider = Provider(**provider_dict)
    
    db.add(provider)
    await db.commit()
    await db.refresh(provider)
    
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="provider_create",
        resource_type="provider",
        resource_id=str(provider.id),
    )
    
    return ProviderResponse.model_validate(provider)


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProviderResponse:
    """Get a specific provider by ID."""
    stmt = select(Provider).where(Provider.id == provider_id)
    result = await db.execute(stmt)
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found",
        )
    
    return ProviderResponse.model_validate(provider)


@router.get("", response_model=ProviderListResponse)
async def list_providers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    provider_type: Optional[ProviderType] = None,
    specialty: Optional[ProviderSpecialty] = None,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProviderListResponse:
    """List providers with filtering and pagination."""
    query = select(Provider)
    count_query = select(func.count()).select_from(Provider)
    
    if provider_type:
        query = query.where(Provider.provider_type == provider_type)
        count_query = count_query.where(Provider.provider_type == provider_type)
    
    if specialty:
        query = query.where(Provider.specialty == specialty)
        count_query = count_query.where(Provider.specialty == specialty)
    
    if is_active is not None:
        query = query.where(Provider.is_active == is_active)
        count_query = count_query.where(Provider.is_active == is_active)
    
    if is_verified is not None:
        query = query.where(Provider.is_verified == is_verified)
        count_query = count_query.where(Provider.is_verified == is_verified)
    
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                Provider.first_name.ilike(pattern),
                Provider.last_name.ilike(pattern),
                Provider.organization_name.ilike(pattern),
                Provider.npi.ilike(pattern),
            )
        )
        count_query = count_query.where(
            or_(
                Provider.first_name.ilike(pattern),
                Provider.last_name.ilike(pattern),
                Provider.organization_name.ilike(pattern),
                Provider.npi.ilike(pattern),
            )
        )
    
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    query = query.order_by(Provider.last_name, Provider.organization_name).offset(skip).limit(limit)
    result = await db.execute(query)
    providers = result.scalars().all()
    
    return ProviderListResponse(
        items=[ProviderSummaryResponse.model_validate(p) for p in providers],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.patch("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: UUID,
    provider_update: ProviderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProviderResponse:
    """Update a provider."""
    stmt = select(Provider).where(Provider.id == provider_id)
    result = await db.execute(stmt)
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found",
        )
    
    update_data = provider_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(provider, field, value)
    
    await db.commit()
    await db.refresh(provider)
    
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="provider_update",
        resource_type="provider",
        resource_id=str(provider.id),
    )
    
    return ProviderResponse.model_validate(provider)


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    provider_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a provider (admin only)."""
    from backend.models.user import UserRole
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete providers",
        )
    
    stmt = select(Provider).where(Provider.id == provider_id)
    result = await db.execute(stmt)
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found",
        )
    
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="provider_delete",
        resource_type="provider",
        resource_id=str(provider.id),
    )
    
    await db.delete(provider)
    await db.commit()