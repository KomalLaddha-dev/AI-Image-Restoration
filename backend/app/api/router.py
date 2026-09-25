"""
API Router — aggregates all endpoint routers.
"""

from fastapi import APIRouter

from app.api.restore import router as restore_router
from app.api.identify import router as identify_router
from app.api.history import router as history_router
from app.api.combined import router as combined_router

api_router = APIRouter()
api_router.include_router(restore_router)
api_router.include_router(identify_router)
api_router.include_router(history_router)
api_router.include_router(combined_router)
