from fastapi import APIRouter
from . import pii_router


api_router = APIRouter()
api_router.include_router(pii_router.router, prefix="/pii", tags=["Detection"])