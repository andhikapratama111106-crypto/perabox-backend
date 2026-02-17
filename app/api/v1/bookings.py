from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.models.models import Booking, Service, Payment, User, Technician
from app.schemas.schemas import BookingCreate, BookingResponse, BookingDetailResponse
from app.api.dependencies import get_current_user, get_current_customer, get_current_admin
import uuid
from pydantic import BaseModel
from datetime import date

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Create a new booking (WORKING EXAMPLE).
    
    This endpoint demonstrates:
    - JWT authentication (customer only)
    - Request validation with Pydantic
    - Database transaction
    - Business logic (price calculation)
    - Response serialization
    """
    # Validate service exists
    service = db.query(Service).filter(
        Service.id == booking_data.service_id,
        Service.is_active == True
    ).first()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )
    
    # Create booking
    booking_total = booking_data.total_price if booking_data.total_price is not None else service.base_price
    
    new_booking = Booking(
        customer_id=current_user.id,
        service_id=booking_data.service_id,
        technician_id=booking_data.technician_id,
        scheduled_date=booking_data.scheduled_date,
        scheduled_time=booking_data.scheduled_time,
        address=booking_data.address,
        notes=booking_data.notes,
        total_price=booking_total,
        status="pending",
    )
    
    db.add(new_booking)
    db.flush()  # Get booking ID without committing
    
    # Create associated payment record
    payment = Payment(
        booking_id=new_booking.id,
        amount=booking_total,
        status="pending",
    )
    
    db.add(payment)
    
    # Commit transaction
    try:
        db.commit()
        db.refresh(new_booking)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create booking",
        )
    
    # Reload booking to include payments relationship if needed by from_orm
    db.refresh(new_booking)
    
    return BookingResponse.from_orm(new_booking)


@router.get("", response_model=List[BookingDetailResponse])
async def get_user_bookings(
    status: Optional[str] = None,
    date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all bookings for the current user."""
    query = db.query(Booking)

    if current_user.role == "customer":
        query = query.filter(Booking.customer_id == current_user.id)
    elif current_user.role == "technician":
        # Get technician ID
        technician = db.query(Technician).filter(
            Technician.user_id == current_user.id
        ).first()
        if not technician:
            return []
        query = query.filter(Booking.technician_id == technician.id)
    else:  # admin
        # Admin sees all, applies filters
        pass
    
    if status:
        query = query.filter(Booking.status == status)
    
    if date:
        query = query.filter(Booking.scheduled_date == date)

    bookings = query.order_by(Booking.created_at.desc()).all()
    
    return [BookingDetailResponse.from_orm(booking) for booking in bookings]


@router.get("/{booking_id}", response_model=BookingDetailResponse)
async def get_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get booking details by ID."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    
    # Check authorization
    if current_user.role == "customer" and booking.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this booking",
        )
    
    return BookingDetailResponse.from_orm(booking)


@router.patch("/{booking_id}/status")
async def update_booking_status(
    booking_id: uuid.UUID,
    new_status: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update booking status."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    
    # Validate status
    valid_statuses = ["pending", "confirmed", "in_progress", "completed", "cancelled"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )
    
    # Authorization check
    if current_user.role == "customer":
        # Customers can only cancel their own bookings
        if booking.customer_id != current_user.id or new_status != "cancelled":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )
    
    booking.status = new_status
    
    if new_status == "completed":
        from datetime import datetime
        booking.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(booking)
    
    return BookingResponse.from_orm(booking)

class AssignTechnicianRequest(BaseModel):
    technician_id: uuid.UUID

@router.patch("/{booking_id}/assign")
async def assign_technician(
    booking_id: uuid.UUID,
    request: AssignTechnicianRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Assign a technician to a booking. Admin only."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    
    technician = db.query(Technician).filter(Technician.id == request.technician_id).first()
    if not technician:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technician not found",
        )
        
    booking.technician_id = request.technician_id
    booking.status = "confirmed" # Auto confirm when tech is assigned
    
    db.commit()
    db.refresh(booking)
    
    return BookingResponse.from_orm(booking)
