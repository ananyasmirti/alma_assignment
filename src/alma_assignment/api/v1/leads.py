import math
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from alma_assignment.api.dependencies import get_current_attorney, get_db
from alma_assignment.db.models import Attorney, Lead, LeadState
from alma_assignment.schemas.lead import LeadResponse, LeadStateUpdate, PaginatedLeads
from alma_assignment.services import email as email_service
from alma_assignment.services.storage import ALLOWED_MIME_TYPES, get_resume_path, save_resume

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    background_tasks: BackgroundTasks,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    resume: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> Lead:
    if resume.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Resume must be a PDF or DOCX file",
        )

    lead = Lead(first_name=first_name, last_name=last_name, email=email)
    db.add(lead)
    await db.flush()  # get lead.id before saving file

    try:
        resume_path = await save_resume(lead.id, resume)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    lead.resume_path = resume_path
    await db.commit()
    await db.refresh(lead)

    background_tasks.add_task(
        email_service.send_prospect_confirmation, lead.first_name, lead.email
    )
    background_tasks.add_task(
        email_service.send_attorney_notification,
        lead.first_name,
        lead.last_name,
        lead.email,
        str(lead.id),
        lead.created_at.isoformat(),
    )

    return lead


@router.get("", response_model=PaginatedLeads)
async def list_leads(
    page: int = 1,
    page_size: int = 20,
    state: Optional[LeadState] = None,
    db: AsyncSession = Depends(get_db),
    _attorney: Attorney = Depends(get_current_attorney),
) -> PaginatedLeads:
    query = select(Lead)
    count_query = select(func.count()).select_from(Lead)

    if state:
        query = query.where(Lead.state == state)
        count_query = count_query.where(Lead.state == state)

    total = (await db.execute(count_query)).scalar_one()
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size

    result = await db.execute(query.order_by(Lead.created_at.desc()).offset(offset).limit(page_size))
    items = list(result.scalars().all())

    return PaginatedLeads(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _attorney: Attorney = Depends(get_current_attorney),
) -> Lead:
    return await _get_lead_or_404(lead_id, db)


@router.patch("/{lead_id}/state", response_model=LeadResponse)
async def update_lead_state(
    lead_id: uuid.UUID,
    payload: LeadStateUpdate,
    db: AsyncSession = Depends(get_db),
    _attorney: Attorney = Depends(get_current_attorney),
) -> Lead:
    lead = await _get_lead_or_404(lead_id, db)

    if lead.state == LeadState.REACHED_OUT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lead is already in REACHED_OUT state",
        )
    if payload.state != LeadState.REACHED_OUT:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only PENDING → REACHED_OUT transition is allowed",
        )

    lead.state = LeadState.REACHED_OUT
    await db.commit()
    await db.refresh(lead)
    return lead


@router.get("/{lead_id}/resume")
async def download_resume(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _attorney: Attorney = Depends(get_current_attorney),
) -> FileResponse:
    lead = await _get_lead_or_404(lead_id, db)
    file_path = get_resume_path(lead.resume_path)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume file not found")
    return FileResponse(path=str(file_path), filename=file_path.name)


async def _get_lead_or_404(lead_id: uuid.UUID, db: AsyncSession) -> Lead:
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return lead
