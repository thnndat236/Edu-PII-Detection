from fastapi import APIRouter
from . import detection, masking, health


api_router = APIRouter()
api_router.include_router(detection.router, prefix="/detection", tags=["Detection"])
api_router.include_router(masking.router, prefix="/masking", tags=["Masking"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])