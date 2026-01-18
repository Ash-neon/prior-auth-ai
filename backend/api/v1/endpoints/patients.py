"""
Patient API Endpoints

Handles patient CRUD operations.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models.user import User
from backend.models.patient import Patient, Gender
from backend.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientSummaryResponse,
    PatientListResponse,
)
from backend.api.dependencies import get_current_user
from backend.utils.audit import AuditLogger

router = APIRouter()
audit_logger = AuditLogger()


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PatientResponse:
    """Create a new patient."""
    # Check for duplicate MRN
    if patient_data.mrn:
        stmt = select(Patient).where(Patient.mrn == patient_data.mrn)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MRN already exists",
            )
    
    # Check for duplicate external_id
    if patient_data.external_id:
        stmt = select(Patient).where(Patient.external_id == patient_data.external_id)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="External ID already exists",
            )
    
    patient_dict = patient_data.model_dump()
    patient = Patient(**patient_dict)
    
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="patient_create",
        resource_type="patient",
        resource_id=str(patient.id),
    )
    
    return PatientResponse.model_validate(patient)


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PatientResponse:
    """Get a specific patient by ID."""
    stmt = select(Patient).where(Patient.id == patient_id)
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    return PatientResponse.model_validate(patient)


@router.get("", response_model=PatientListResponse)
async def list_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    gender: Optional[Gender] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PatientListResponse:
    """List patients with filtering and pagination."""
    query = select(Patient)
    count_query = select(func.count()).select_from(Patient)
    
    if gender:
        query = query.where(Patient.gender == gender)
        count_query = count_query.where(Patient.gender == gender)
    
    if is_active is not None:
        query = query.where(Patient.is_active == is_active)
        count_query = count_query.where(Patient.is_active == is_active)
    
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                Patient.first_name.ilike(pattern),
                Patient.last_name.ilike(pattern),
                Patient.mrn.ilike(pattern),
                Patient.insurance_primary_member_id.ilike(pattern),
            )
        )
        count_query = count_query.where(
            or_(
                Patient.first_name.ilike(pattern),
                Patient.last_name.ilike(pattern),
                Patient.mrn.ilike(pattern),
                Patient.insurance_primary_member_id.ilike(pattern),
            )
        )
    
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    query = query.order_by(Patient.last_name, Patient.first_name).offset(skip).limit(limit)
    result = await db.execute(query)
    patients = result.scalars().all()
    
    return PatientListResponse(
        items=[PatientSummaryResponse.model_validate(p) for p in patients],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.patch("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: UUID,
    patient_update: PatientUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PatientResponse:
    """Update a patient."""
    stmt = select(Patient).where(Patient.id == patient_id)
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    update_data = patient_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)
    
    await db.commit()
    await db.refresh(patient)
    
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="patient_update",
        resource_type="patient",
        resource_id=str(patient.id),
    )
    
    return PatientResponse.model_validate(patient)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a patient (admin only)."""
    from backend.models.user import UserRole
    from backend.api.dependencies import require_role
    
    # Check admin permission
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete patients",
        )
    
    stmt = select(Patient).where(Patient.id == patient_id)
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    await audit_logger.log_user_action(
        user_id=current_user.id,
        action="patient_delete",
        resource_type="patient",
        resource_id=str(patient.id),
    )
    
    await db.delete(patient)
    await db.commit()