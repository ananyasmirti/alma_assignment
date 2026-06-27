from __future__ import annotations

import uuid
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alma_assignment.core.security import decode_access_token
from alma_assignment.db.models import Attorney
from alma_assignment.db.session import AsyncSessionLocal

bearer_scheme = HTTPBearer(auto_error=True)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_attorney(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Attorney:
    token = credentials.credentials
    attorney_id = decode_access_token(token)
    if not attorney_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        attorney_uuid = uuid.UUID(attorney_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(Attorney).where(Attorney.id == attorney_uuid))
    attorney = result.scalar_one_or_none()
    if not attorney:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Attorney not found")

    return attorney
