from fastapi import APIRouter

from app.api.v1.endpoints import processing

api_router = APIRouter()
api_router.include_router(processing.router, prefix="/processing", tags=["processing"])