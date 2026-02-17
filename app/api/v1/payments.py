from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Payment, Booking
from app.api.dependencies import get_current_user
import uuid
from pydantic import BaseModel
from typing import Optional
import time

router = APIRouter(prefix="/payments", tags=["Payments"])

class QRISResponse(BaseModel):
    payment_id: uuid.UUID
    qris_string: str
    qr_url: str
    amount: float
    expiry_time: int  # Unix timestamp

class PaymentStatusResponse(BaseModel):
    payment_id: uuid.UUID
    status: str
    transaction_id: Optional[str] = None

@router.get("/{payment_id}/qris", response_model=QRISResponse)
async def get_qris_code(
    payment_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate mock QRIS code for a payment.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Check if user owns the booking associated with this payment
    booking = db.query(Booking).filter(Booking.id == payment.booking_id).first()
    if not booking or (booking.customer_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this payment"
        )

    # Mock QRIS generation
    # Real QRIS string format is complex (EMVCo), here using a dummy one
    qris_string = f"00020101021126670014ID.CO.QRIS.WWW01189360052200000302065204000053033605802ID5911PERABOX.INC6007JAKARTA61051234562070703A016304ABCD"
    
    # Using a placeholder image service for QR
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={qris_string}"
    
    return QRISResponse(
        payment_id=payment.id,
        qris_string=qris_string,
        qr_url=qr_url,
        amount=payment.amount,
        expiry_time=int(time.time()) + 900  # 15 minutes expiry
    )

@router.post("/{payment_id}/verify", response_model=PaymentStatusResponse)
async def verify_payment(
    payment_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify payment status (Mock implementation).
    Always returns 'success' for demonstration if called.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    # Mock logic: Update status to success
    payment.status = "success"
    payment.payment_method = "qris"
    
    # Update associated booking status to confirmed if it was pending
    booking = db.query(Booking).filter(Booking.id == payment.booking_id).first()
    if booking and booking.status == "pending":
        booking.status = "confirmed"
    
    db.commit()
    db.refresh(payment)
    
    return PaymentStatusResponse(
        payment_id=payment.id,
        status=payment.status,
        transaction_id=f"TRX-{uuid.uuid4().hex[:8].upper()}"
    )
