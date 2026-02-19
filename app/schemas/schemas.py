from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime, date, time
from decimal import Decimal
import uuid


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: str


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role: str = Field(default="customer")
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['customer', 'technician', 'admin']:
            raise ValueError('Invalid role')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: uuid.UUID
    role: str
    avatar_url: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


# Service schemas
class ServiceCategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str]
    icon_url: Optional[str]
    display_order: int
    
    class Config:
        from_attributes = True


class ServiceResponse(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    name: str
    slug: str
    description: Optional[str]
    base_price: Decimal
    duration_minutes: int
    image_url: Optional[str]
    
    class Config:
        from_attributes = True


# Booking schemas
class BookingCreate(BaseModel):
    service_id: uuid.UUID
    technician_id: Optional[uuid.UUID] = None
    scheduled_date: date
    scheduled_time: time
    address: str
    notes: Optional[str] = None
    total_price: Optional[Decimal] = None
    
    @validator('scheduled_date')
    def validate_date(cls, v):
        if v < date.today():
            raise ValueError('Scheduled date cannot be in the past')
        return v


# Technician schemas
class TechnicianResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    specializations: List[str]
    experience_years: int
    rating_average: Decimal
    total_jobs: int
    is_available: bool
    
    # Background Check & Details
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    parent_name: Optional[str] = None
    has_signed_contract: bool = False
    contract_url: Optional[str] = None
    bio: Optional[str] = None
    
    class Config:
        from_attributes = True


class TechnicianUpdate(BaseModel):
    is_available: Optional[bool] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    parent_name: Optional[str] = None
    has_signed_contract: Optional[bool] = None
    contract_url: Optional[str] = None
    bio: Optional[str] = None
    specializations: Optional[List[str]] = None
    experience_years: Optional[int] = None
    avatar_url: Optional[str] = None


# Payment schemas
class PaymentCreate(BaseModel):
    booking_id: uuid.UUID
    payment_method: str


class PaymentResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    amount: Decimal
    status: str
    payment_method: Optional[str]
    transaction_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Booking response schemas (must be after PaymentResponse)
class BookingResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    service_id: uuid.UUID
    technician_id: Optional[uuid.UUID]
    scheduled_date: date
    scheduled_time: time
    status: str
    address: str
    notes: Optional[str]
    total_price: Decimal
    payments: List[PaymentResponse] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BookingDetailResponse(BookingResponse):
    service: ServiceResponse
    customer: UserResponse
    payments: List[PaymentResponse] = []
    
    class Config:
        from_attributes = True


# Rating schemas
class RatingCreate(BaseModel):
    booking_id: uuid.UUID
    rating: int = Field(..., ge=1, le=5)
    review_text: Optional[str] = None


class RatingResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    customer_id: uuid.UUID
    technician_id: uuid.UUID
    rating: int
    review_text: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Article schemas
class ArticleResponse(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    excerpt: Optional[str]
    featured_image: Optional[str]
    published_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ArticleDetailResponse(ArticleResponse):
    content: str
    author_id: Optional[uuid.UUID]
    
    class Config:
        from_attributes = True


# Testimonial schemas
class TestimonialResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    content: str
    rating: int
    created_at: datetime
    
    class Config:
        from_attributes = True
# Payment Response extras
class QRISResponse(BaseModel):
    payment_id: uuid.UUID
    qris_string: str
    qr_url: str
    amount: Decimal
    expiry_time: int


class PaymentStatusResponse(BaseModel):
    payment_id: uuid.UUID
    status: str
    transaction_id: Optional[str]
