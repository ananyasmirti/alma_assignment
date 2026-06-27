from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alma_assignment.api.dependencies import get_db
from alma_assignment.core.security import create_access_token, hash_password, verify_password
from alma_assignment.db.models import Attorney
from alma_assignment.schemas.auth import AttorneyLogin, AttorneyRegister, AttorneyResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AttorneyResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: AttorneyRegister, db: AsyncSession = Depends(get_db)) -> Attorney:
    existing = await db.execute(select(Attorney).where(Attorney.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    attorney = Attorney(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        name=payload.name,
    )
    db.add(attorney)
    await db.commit()
    await db.refresh(attorney)
    return attorney


@router.post("/login", response_model=TokenResponse)
async def login(payload: AttorneyLogin, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    result = await db.execute(select(Attorney).where(Attorney.email == payload.email))
    attorney = result.scalar_one_or_none()

    if not attorney or not verify_password(payload.password, attorney.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    token = create_access_token(str(attorney.id))
    return TokenResponse(access_token=token)
