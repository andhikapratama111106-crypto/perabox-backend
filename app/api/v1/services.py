from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.models import ServiceCategory, Service
from app.schemas.schemas import ServiceCategoryResponse, ServiceResponse
import uuid

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("/categories", response_model=List[ServiceCategoryResponse])
async def get_service_categories(db: Session = Depends(get_db)):
    """Get all active service categories."""
    categories = db.query(ServiceCategory).filter(
        ServiceCategory.is_active == True
    ).order_by(ServiceCategory.display_order).all()
    
    return [ServiceCategoryResponse.from_orm(cat) for cat in categories]


@router.get("", response_model=List[ServiceResponse])
async def get_services(
    category_id: uuid.UUID = None,
    db: Session = Depends(get_db)
):
    """Get all active services, optionally filtered by category."""
    query = db.query(Service).filter(Service.is_active == True)
    
    if category_id:
        query = query.filter(Service.category_id == category_id)
    
    services = query.all()
    return [ServiceResponse.from_orm(service) for service in services]


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(service_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get service details by ID."""
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.is_active == True
    ).first()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )
    
    return ServiceResponse.from_orm(service)
