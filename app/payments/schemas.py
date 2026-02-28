import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

from app.payments.models import PaymentStatus


class PaymentPlanOut(BaseModel):
    id: int
    name_kk: str
    name_ru: str
    price: Decimal
    currency: str
    max_guests: Optional[int] = None
    max_photos: int
    validity_days: int
    features: Optional[dict] = None
    is_active: bool
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None

    model_config = {"from_attributes": True}


class PaymentCreateRequest(BaseModel):
    invitation_id: uuid.UUID
    plan_id: int


class PaymentOut(BaseModel):
    id: uuid.UUID
    invitation_id: Optional[uuid.UUID] = None
    plan_id: Optional[int] = None
    amount: Decimal
    currency: str
    status: PaymentStatus
    payment_method: str
    kaspi_phone: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentCreateResponse(BaseModel):
    payment: PaymentOut
    kaspi_phone: str
    amount: Decimal
    currency: str
    description: str
    message: str
