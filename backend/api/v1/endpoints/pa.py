"""
Prior Authorization API Endpoints

Handles PA CRUD operations, submissions, and status management.

Author: Prior Auth AI Team
Version: 1.0.0
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models.user import User, UserRole
from backend.models.prior_authorization import (
    PriorAuthorization,
    PAStatus,
    PAUrgency,
    PAType,
    PAStatusHistory,
)
from backend.models.patient import Patient
from backend.models.provider import Provider
from backend.models.payer import Payer
from backend.schemas.prior_authorization import (
    PACreate,
    PAUpdate,
    PAStatusUpdate,
    PAResponse,
    PADetailResponse,
    PAListResponse,
    PAStatsResponse,
    PASubmitRequest,
    PASubmitResponse,
)
from backend.api.dependencies import get_current_user, require_role
from backend.utils.audit import AuditLogger

router = APIRouter()
audit_logger = AuditLogger()


@router.post("", response_model=PAResponse, status_code=status.HTTP_201_CREATED)
async def create_prior_authorization(
    pa_data: PACreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PAResponse:
    """
    Create a new prior authorization request.
    
    Validates patient and provider exist before creation.
    Sets initial status to DRAFT.
    """
    # Verify patient exists
    patient_stmt = select(Patient).where(Patient.id == pa_data.patient_id)
    patient_result = await db.execute(patient_stmt)
    patient = patient_result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {pa_data.patient_id} not found",
        )
    
    if not patient.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create PA for inactive patient",
        )
    
    # Verify provider exists
    provider_stmt = select(Provider).where(Provider.id == pa_data.provider_id)
    provider_result = await db.execute(provider_stmt)
    provider = provider_result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider {pa_data.provider_id} not found",
        )
    
    if not provider.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create PA for inactive provider",
        )
    
    # Verify payer if provided
    if pa_data.payer_id:
        payer_stmt = select(Payer).where(Payer.id == pa_data.payer_id)
        payer_result = await db.execute(payer_stmt)
        payer = payer_result.scalar_one_or_none()
        
        if not payer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payer {pa_data.payer_id} not found",
            )
    
    # Create PA
    pa_dict = pa_data.model_dump()
    pa = PriorAuthorization(
        **pa_dict,
        created_by_id=current_user.id,
        status=PAStatus.DRAFT,
    )
    
    db.add(pa)
    await db.commit()
    await db.refresh(pa)
    
    # Create status history entry
    status_history = PAStatusHistory(
        prior_authorization_id=pa.id,
        from_status=None,
        to_status=PAStatus.DRAFT,
        changed_by_id=current_user.id,
        reason="PA created",
    )
    db.add(status_history)
    await db.commit()
    
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="pa_create",
        resource_type="prior_authorization",
        resource_id=str(pa.id),
        details={
            "pa_type": pa.pa_type.value,
            "patient_id": str(pa.patient_id),
            "provider_id": str(pa.provider_id),
        },
    )
    
    return PAResponse.model_validate(pa)


@router.get("/{pa_id}", response_model=PADetailResponse)
async def get_prior_authorization(
    pa_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PADetailResponse:
    """
    Get a specific prior authorization by ID.
    
    Returns detailed PA information including related entities.
    """
    stmt = select(PriorAuthorization).where(PriorAuthorization.id == pa_id)
    result = await db.execute(stmt)
    pa = result.scalar_one_or_none()
    
    if not pa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prior authorization {pa_id} not found",
        )
    
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="pa_view",
        resource_type="prior_authorization",
        resource_id=str(pa.id),
    )
    
    return PADetailResponse.model_validate(pa)


@router.get("", response_model=PAListResponse)
async def list_prior_authorizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[PAStatus] = None,
    urgency: Optional[PAUrgency] = None,
    pa_type: Optional[PAType] = None,
    patient_id: Optional[UUID] = None,
    provider_id: Optional[UUID] = None,
    payer_id: Optional[UUID] = None,
    assigned_to_id: Optional[UUID] = None,
    search: Optional[str] = None,
    is_overdue: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PAListResponse:
    """
    List prior authorizations with filtering and pagination.
    
    Regular users see only their assigned PAs.
    Admins and analysts see all PAs.
    """
    # Build base query
    query = select(PriorAuthorization)
    count_query = select(func.count()).select_from(PriorAuthorization)
    
    # Access control: regular users only see assigned PAs
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.ANALYST]:
        query = query.where(
            or_(
                PriorAuthorization.created_by_id == current_user.id,
                PriorAuthorization.assigned_to_id == current_user.id,
            )
        )
        count_query = count_query.where(
            or_(
                PriorAuthorization.created_by_id == current_user.id,
                PriorAuthorization.assigned_to_id == current_user.id,
            )
        )
    
    # Apply filters
    if status:
        query = query.where(PriorAuthorization.status == status)
        count_query = count_query.where(PriorAuthorization.status == status)
    
    if urgency:
        query = query.where(PriorAuthorization.urgency == urgency)
        count_query = count_query.where(PriorAuthorization.urgency == urgency)
    
    if pa_type:
        query = query.where(PriorAuthorization.pa_type == pa_type)
        count_query = count_query.where(PriorAuthorization.pa_type == pa_type)
    
    if patient_id:
        query = query.where(PriorAuthorization.patient_id == patient_id)
        count_query = count_query.where(PriorAuthorization.patient_id == patient_id)
    
    if provider_id:
        query = query.where(PriorAuthorization.provider_id == provider_id)
        count_query = count_query.where(PriorAuthorization.provider_id == provider_id)
    
    if payer_id:
        query = query.where(PriorAuthorization.payer_id == payer_id)
        count_query = count_query.where(PriorAuthorization.payer_id == payer_id)
    
    if assigned_to_id:
        query = query.where(PriorAuthorization.assigned_to_id == assigned_to_id)
        count_query = count_query.where(PriorAuthorization.assigned_to_id == assigned_to_id)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                PriorAuthorization.external_reference.ilike(search_pattern),
                PriorAuthorization.service_description.ilike(search_pattern),
                PriorAuthorization.medication_name.ilike(search_pattern),
            )
        )
        count_query = count_query.where(
            or_(
                PriorAuthorization.external_reference.ilike(search_pattern),
                PriorAuthorization.service_description.ilike(search_pattern),
                PriorAuthorization.medication_name.ilike(search_pattern),
            )
        )
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Apply pagination and ordering
    query = query.order_by(PriorAuthorization.created_at.desc()).offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    pas = result.scalars().all()
    
    # Filter by is_overdue if requested (post-query since it's a computed property)
    if is_overdue is not None:
        pas = [pa for pa in pas if pa.is_overdue == is_overdue]
    
    return PAListResponse(
        items=[PAResponse.model_validate(pa) for pa in pas],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.patch("/{pa_id}", response_model=PAResponse)
async def update_prior_authorization(
    pa_id: UUID,
    pa_update: PAUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PAResponse:
    """
    Update a prior authorization.
    
    Users can update PAs they created or are assigned to.
    Admins can update any PA.
    """
    # Get PA
    stmt = select(PriorAuthorization).where(PriorAuthorization.id == pa_id)
    result = await db.execute(stmt)
    pa = result.scalar_one_or_none()
    
    if not pa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prior authorization {pa_id} not found",
        )
    
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        if pa.created_by_id != current_user.id and pa.assigned_to_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this PA",
            )
    
    # Apply updates
    update_data = pa_update.model_dump(exclude_unset=True)
    old_status = pa.status
    
    for field, value in update_data.items():
        setattr(pa, field, value)
    
    await db.commit()
    await db.refresh(pa)
    
    # Create status history if status changed
    if "status" in update_data and update_data["status"] != old_status:
        status_history = PAStatusHistory(
            prior_authorization_id=pa.id,
            from_status=old_status,
            to_status=pa.status,
            changed_by_id=current_user.id,
            reason="PA updated",
        )
        db.add(status_history)
        await db.commit()
    
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="pa_update",
        resource_type="prior_authorization",
        resource_id=str(pa.id),
        details={"updated_fields": list(update_data.keys())},
    )
    
    return PAResponse.model_validate(pa)


@router.patch("/{pa_id}/status", response_model=PAResponse)
async def update_pa_status(
    pa_id: UUID,
    status_update: PAStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PAResponse:
    """
    Update PA status with reason tracking.
    
    Creates status history entry for audit trail.
    """
    # Get PA
    stmt = select(PriorAuthorization).where(PriorAuthorization.id == pa_id)
    result = await db.execute(stmt)
    pa = result.scalar_one_or_none()
    
    if not pa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prior authorization {pa_id} not found",
        )
    
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.ANALYST]:
        if pa.created_by_id != current_user.id and pa.assigned_to_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this PA status",
            )
    
    old_status = pa.status
    pa.status = status_update.status
    
    # Create status history
    status_history = PAStatusHistory(
        prior_authorization_id=pa.id,
        from_status=old_status,
        to_status=status_update.status,
        changed_by_id=current_user.id,
        reason=status_update.reason,
        notes=status_update.notes,
    )
    db.add(status_history)
    
    await db.commit()
    await db.refresh(pa)
    
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="pa_status_change",
        resource_type="prior_authorization",
        resource_id=str(pa.id),
        details={
            "from_status": old_status.value,
            "to_status": status_update.status.value,
            "reason": status_update.reason,
        },
    )
    
    return PAResponse.model_validate(pa)


@router.post("/{pa_id}/submit", response_model=PASubmitResponse)
async def submit_prior_authorization(
    pa_id: UUID,
    submit_request: PASubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PASubmitResponse:
    """
    Submit a prior authorization to the payer.
    
    Changes status from DRAFT to SUBMITTED.
    TODO: Integration with actual submission service/agents.
    """
    # Get PA
    stmt = select(PriorAuthorization).where(PriorAuthorization.id == pa_id)
    result = await db.execute(stmt)
    pa = result.scalar_one_or_none()
    
    if not pa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prior authorization {pa_id} not found",
        )
    
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        if pa.created_by_id != current_user.id and pa.assigned_to_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to submit this PA",
            )
    
    # Validate PA is in DRAFT status
    if pa.status != PAStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit PA with status {pa.status.value}",
        )
    
    # Validate required fields
    if not pa.payer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payer is required for submission",
        )
    
    if not pa.clinical_rationale:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Clinical rationale is required for submission",
        )
    
    # Update PA
    from datetime import datetime
    pa.status = PAStatus.SUBMITTED
    pa.submitted_at = datetime.utcnow()
    pa.submission_method = submit_request.submission_method
    
    # Create status history
    status_history = PAStatusHistory(
        prior_authorization_id=pa.id,
        from_status=PAStatus.DRAFT,
        to_status=PAStatus.SUBMITTED,
        changed_by_id=current_user.id,
        reason="PA submitted to payer",
        notes=submit_request.notes,
    )
    db.add(status_history)
    
    await db.commit()
    await db.refresh(pa)
    
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="pa_submit",
        resource_type="prior_authorization",
        resource_id=str(pa.id),
        details={
            "submission_method": submit_request.submission_method,
            "payer_id": str(pa.payer_id),
        },
    )
    
    # TODO: Trigger async agent workflow for submission
    # await orchestration_engine.submit_pa(pa.id)
    
    return PASubmitResponse(
        pa_id=pa.id,
        submitted_at=pa.submitted_at,
        submission_method=pa.submission_method,
        external_reference=pa.external_reference,
        status=pa.status,
        message="PA submitted successfully. Submission is being processed.",
    )


@router.delete("/{pa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prior_authorization(
    pa_id: UUID,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a prior authorization.
    
    Admin only. Should only be used for test data or errors.
    For real PAs, use status update to CANCELLED instead.
    """
    stmt = select(PriorAuthorization).where(PriorAuthorization.id == pa_id)
    result = await db.execute(stmt)
    pa = result.scalar_one_or_none()
    
    if not pa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prior authorization {pa_id} not found",
        )
    
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="pa_delete",
        resource_type="prior_authorization",
        resource_id=str(pa.id),
        details={
            "status": pa.status.value,
            "patient_id": str(pa.patient_id),
        },
    )
    
    await db.delete(pa)
    await db.commit()


@router.get("/stats/overview", response_model=PAStatsResponse)
async def get_pa_statistics(
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.ANALYST])),
    db: AsyncSession = Depends(get_db),
) -> PAStatsResponse:
    """
    Get PA statistics overview.
    
    Returns aggregated stats across all PAs.
    Admin/Analyst only.
    """
    # Total count
    total_stmt = select(func.count()).select_from(PriorAuthorization)
    total_result = await db.execute(total_stmt)
    total_count = total_result.scalar_one()
    
    # Count by status
    by_status = {}
    for status_value in PAStatus:
        status_stmt = select(func.count()).select_from(PriorAuthorization).where(
            PriorAuthorization.status == status_value
        )
        status_result = await db.execute(status_stmt)
        by_status[status_value.value] = status_result.scalar_one()
    
    # Count by urgency
    by_urgency = {}
    for urgency_value in PAUrgency:
        urgency_stmt = select(func.count()).select_from(PriorAuthorization).where(
            PriorAuthorization.urgency == urgency_value
        )
        urgency_result = await db.execute(urgency_stmt)
        by_urgency[urgency_value.value] = urgency_result.scalar_one()
    
    # Count by type
    by_type = {}
    for type_value in PAType:
        type_stmt = select(func.count()).select_from(PriorAuthorization).where(
            PriorAuthorization.pa_type == type_value
        )
        type_result = await db.execute(type_stmt)
        by_type[type_value.value] = type_result.scalar_one()
    
    # Overdue count
    overdue_pas_stmt = select(PriorAuthorization).where(
        PriorAuthorization.status.in_([
            PAStatus.SUBMITTED,
            PAStatus.UNDER_REVIEW,
            PAStatus.PENDING_INFO,
        ])
    )
    overdue_result = await db.execute(overdue_pas_stmt)
    all_active_pas = overdue_result.scalars().all()
    overdue_count = sum(1 for pa in all_active_pas if pa.is_overdue)
    
    # Calculate approval metrics
    approved_count = by_status.get(PAStatus.APPROVED.value, 0)
    denied_count = by_status.get(PAStatus.DENIED.value, 0)
    completed_count = approved_count + denied_count
    
    approval_rate = (
        (approved_count / completed_count * 100) if completed_count > 0 else None
    )
    
    # Average approval time - simplified for now
    # TODO: Calculate actual average from decision_date - submitted_at
    avg_approval_time_days = None
    
    return PAStatsResponse(
        total_count=total_count,
        by_status=by_status,
        by_urgency=by_urgency,
        by_type=by_type,
        avg_approval_time_days=avg_approval_time_days,
        approval_rate=approval_rate,
        overdue_count=overdue_count,
    )