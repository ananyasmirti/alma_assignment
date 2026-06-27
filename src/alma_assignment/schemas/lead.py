import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from alma_assignment.db.models import LeadState


class LeadCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr


class LeadResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    state: LeadState
    resume_path: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadStateUpdate(BaseModel):
    state: LeadState


class PaginatedLeads(BaseModel):
    items: list[LeadResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
