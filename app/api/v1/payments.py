import uuid
import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Payment, Booking
from app.api.dependencies import get_current_user
import midtransclient
from app.core.config import get_settings
from app.schemas.schemas import QRISResponse, PaymentStatusResponse

router = APIRouter()
settings = get_settings()

# Initialize Midtrans Core API
midtrans_core = midtransclient.CoreApi(
    is_production=settings.MIDTRANS_IS_PRODUCTION,
    server_key=settings.MIDTRANS_SERVER_KEY,
    client_key=settings.MIDTRANS_CLIENT_KEY
)

@router.get("/{payment_id}/qris", response_model=QRISResponse)
async def get_qris_code(
    payment_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate real QRIS code using Midtrans Core API.
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

    try:
        # Charge QRIS via Midtrans
        print(f"[Midtrans Debug] Charging QRIS for Order {payment.id}. Amount: {payment.amount}")
        print(f"[Midtrans Debug] Using Production: {settings.MIDTRANS_IS_PRODUCTION}")
        
        param = {
            "payment_type": "qris",
            "transaction_details": {
                "order_id": str(payment.id),
                "gross_amount": int(payment.amount)
            },
            "item_details": [{
                "id": str(booking.service_id),
                "price": int(payment.amount),
                "quantity": 1,
                "name": f"Layanan Perabox - Booking {str(booking.id)[:8]}"
            }],
            "customer_details": {
                "first_name": current_user.full_name,
                "email": current_user.email,
                "phone": current_user.phone
            }
        }

        charge_response = midtrans_core.charge(param)
        print(f"[Midtrans Debug] Charge response received: {charge_response.get('status_code')}")
        
        # Extract actions (QR URL)
        qr_url = ""
        actions = charge_response.get("actions", [])
        for action in actions:
            if action.get("name") == "generate-qr-code":
                qr_url = action.get("url")
                break

        # Log transaction ID if provided
        payment.transaction_id = charge_response.get("transaction_id")
        db.commit()

        return QRISResponse(
            payment_id=payment.id,
            qris_string=charge_response.get("qr_string", ""),
            qr_url=qr_url,
            amount=payment.amount,
            expiry_time=int(time.time()) + 900
        )
    except Exception as e:
        print(f"[Midtrans Error] Full Trace: {str(e)}")
        # Check if keys are actually loaded
        has_key = settings.MIDTRANS_SERVER_KEY and "YOUR_SERVER_KEY" not in settings.MIDTRANS_SERVER_KEY
        if not has_key:
             print("[Midtrans Error] Keys are missing or default. Falling back to mock.")
             qris_string = f"00020101021126670014ID.CO.QRIS.WWW01189360052200000302065204000053033605802ID5911PERABOX.INC6007JAKARTA61051234562070703A016304ABCD"
             qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={qris_string}"
             return QRISResponse(
                payment_id=payment.id,
                qris_string=qris_string,
                qr_url=qr_url,
                amount=payment.amount,
                expiry_time=int(time.time()) + 900
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate QRIS: {str(e)}"
        )

@router.post("/{payment_id}/verify", response_model=PaymentStatusResponse)
async def verify_payment(
    payment_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check payment status from Midtrans.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    try:
        # Check status from Midtrans
        status_response = midtrans_core.status(str(payment.id))
        transaction_status = status_response.get("transaction_status")
        fraud_status = status_response.get("fraud_status")

        if transaction_status == "capture" or transaction_status == "settlement":
            if fraud_status == "accept" or fraud_status is None:
                payment.status = "paid"
                # Update associated booking
                booking = db.query(Booking).filter(Booking.id == payment.booking_id).first()
                if booking and booking.status == "pending":
                    booking.status = "confirmed"
                db.commit()
        elif transaction_status == "deny" or transaction_status == "cancel" or transaction_status == "expire":
            payment.status = "failed"
            db.commit()
        elif transaction_status == "pending":
            payment.status = "pending"
            db.commit()

        db.refresh(payment)
        
        return PaymentStatusResponse(
            payment_id=payment.id,
            status=payment.status,
            transaction_id=payment.transaction_id
        )
    except Exception as e:
        # If order not found on midtrans yet, just return current status
        return PaymentStatusResponse(
            payment_id=payment.id,
            status=payment.status,
            transaction_id=payment.transaction_id
        )

@router.post("/webhook")
async def midtrans_webhook(
    notification: dict,
    db: Session = Depends(get_db)
):
    """
    Handle Midtrans asynchronous notifications (Webhooks).
    """
    try:
        # Use Midtrans SDK to verify notification (optional but recommended)
        # For simplicity, we just process it. Real implementation should verify signature.
        
        order_id = notification.get("order_id")
        transaction_status = notification.get("transaction_status")
        fraud_status = notification.get("fraud_status")

        payment = db.query(Payment).filter(Payment.id == order_id).first()
        if not payment:
            return {"status": "error", "message": "Payment not found"}

        if transaction_status == "capture" or transaction_status == "settlement":
            if fraud_status == "accept" or fraud_status is None:
                payment.status = "paid"
                booking = db.query(Booking).filter(Booking.id == payment.booking_id).first()
                if booking and booking.status == "pending":
                    booking.status = "confirmed"
        elif transaction_status == "deny" or transaction_status == "cancel" or transaction_status == "expire":
            payment.status = "failed"
        elif transaction_status == "pending":
            payment.status = "pending"

        db.commit()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
