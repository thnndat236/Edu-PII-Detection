from fastapi import APIRouter, Request
from services.model_service import ModelService
from api.models.schemas import MaskRequest, MaskResponse

router = APIRouter()

@router.post("/mask", response_model=MaskResponse)
def mask_text(request: Request, body: MaskRequest):
    service = ModelService(request)
    return service.mask_text(body)
