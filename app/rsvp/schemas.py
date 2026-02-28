import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel

from app.rsvp.models import QuestionType


class RSVPQuestionOut(BaseModel):
    id: uuid.UUID
    invitation_id: uuid.UUID
    question_text_kk: str
    question_text_ru: str
    question_type: QuestionType
    options: Optional[dict] = None
    is_required: bool
    sort_order: int

    model_config = {"from_attributes": True}


class RSVPQuestionCreate(BaseModel):
    question_text_kk: str
    question_text_ru: str
    question_type: QuestionType = QuestionType.text
    options: Optional[dict] = None
    is_required: bool = False
    sort_order: int = 0


class RSVPResponseCreate(BaseModel):
    guest_name: str
    guest_phone: Optional[str] = None
    will_attend: bool
    guest_count: int = 1
    message: Optional[str] = None
    answers: Optional[dict] = None


class RSVPResponseOut(BaseModel):
    id: uuid.UUID
    invitation_id: uuid.UUID
    guest_name: str
    guest_phone: Optional[str] = None
    will_attend: bool
    guest_count: int
    message: Optional[str] = None
    answers: Optional[dict] = None
    responded_at: datetime

    model_config = {"from_attributes": True}


class RSVPSummary(BaseModel):
    total_responses: int
    attending: int
    not_attending: int
    total_guests: int
    responses: list[RSVPResponseOut]
