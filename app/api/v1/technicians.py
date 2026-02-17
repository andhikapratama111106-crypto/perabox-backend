from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.models import Technician, User
from app.schemas.schemas import TechnicianResponse, TechnicianUpdate
from app.api.dependencies import get_current_admin
import uuid
from pydantic import BaseModel
from decimal import Decimal

router = APIRouter(prefix="/technicians", tags=["Technicians"])

# Extended response model to include user details
class TechnicianDetailResponse(TechnicianResponse):
    user_name: str
    user_email: str
    user_phone: str
    avatar_url: str | None
    bio: str | None = None

    class Config:
        from_attributes = True
@router.get("/", response_model=List[TechnicianDetailResponse])
async def get_technicians(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get all technicians with details. Admin access required.
    """
    technicians = db.query(Technician).join(User).all()
    
    results = []
    for tech in technicians:
        results.append(TechnicianDetailResponse(
            id=tech.id,
            user_id=tech.user_id,
            specializations=tech.specializations,
            experience_years=tech.experience_years,
            rating_average=tech.rating_average,
            total_jobs=tech.total_jobs,
            is_available=tech.is_available,
            user_name=tech.user.full_name,
            user_email=tech.user.email,
            user_phone=tech.user.phone,
            avatar_url=tech.user.avatar_url,
            # Background Check Fields
            address=tech.address,
            emergency_contact_name=tech.emergency_contact_name,
            emergency_contact_phone=tech.emergency_contact_phone,
            date_of_birth=tech.date_of_birth,
            parent_name=tech.parent_name,
            has_signed_contract=tech.has_signed_contract,
            contract_url=tech.contract_url,
            bio=tech.bio
        ))
        
    return results

@router.get("/available", response_model=List[TechnicianDetailResponse])
async def get_available_technicians(
    db: Session = Depends(get_db)
):
    """
    Get available technicians for booking. Public access.
    """
    technicians = db.query(Technician).join(User).filter(
        Technician.is_available == True,
        User.is_active == True
    ).all()
    
    results = []
    for tech in technicians:
        results.append(TechnicianDetailResponse(
            id=tech.id,
            user_id=tech.user_id,
            specializations=tech.specializations,
            experience_years=tech.experience_years,
            rating_average=tech.rating_average,
            total_jobs=tech.total_jobs,
            is_available=tech.is_available,
            user_name=tech.user.full_name,
            user_email=tech.user.email,
            user_phone=tech.user.phone,
            avatar_url=tech.user.avatar_url,
            # Background Check Fields
            address=tech.address,
            emergency_contact_name=tech.emergency_contact_name,
            emergency_contact_phone=tech.emergency_contact_phone,
            date_of_birth=tech.date_of_birth,
            parent_name=tech.parent_name,
            has_signed_contract=tech.has_signed_contract,
            contract_url=tech.contract_url,
            bio=tech.bio
        ))
    
    return results


@router.patch("/{technician_id}", response_model=TechnicianResponse)
async def update_technician(
    technician_id: uuid.UUID,
    data: TechnicianUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update technician details and availability. Admin only.
    """
    tech = db.query(Technician).filter(Technician.id == technician_id).first()
    if not tech:
        raise HTTPException(status_code=404, detail="Technician not found")
        
    # Update fields if provided
    if data.is_available is not None:
        tech.is_available = data.is_available
    if data.address is not None:
        tech.address = data.address
    if data.emergency_contact_name is not None:
        tech.emergency_contact_name = data.emergency_contact_name
    if data.emergency_contact_phone is not None:
        tech.emergency_contact_phone = data.emergency_contact_phone
    if data.date_of_birth is not None:
        tech.date_of_birth = data.date_of_birth
    if data.parent_name is not None:
        tech.parent_name = data.parent_name
    if data.has_signed_contract is not None:
        tech.has_signed_contract = data.has_signed_contract
    if data.contract_url is not None:
        tech.contract_url = data.contract_url
    if data.bio is not None:
        tech.bio = data.bio
    if data.specializations is not None:
        tech.specializations = data.specializations
    if data.experience_years is not None:
        tech.experience_years = data.experience_years
    if data.avatar_url is not None:
        tech.user.avatar_url = data.avatar_url
        
    db.commit()
    db.refresh(tech)
    return TechnicianResponse.from_orm(tech)
