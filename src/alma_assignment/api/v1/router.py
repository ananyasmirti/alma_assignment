from fastapi import APIRouter

from alma_assignment.api.v1 import auth, leads

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(leads.router)
