from fastapi import APIRouter, Depends
from services.model_service import ModelService
from api.models.schemas import DetectRequest, DetectionResponse, MaskRequest, MaskResponse
from datetime import datetime, timezone

router = APIRouter()

_model_service = None

def get_model_service() -> ModelService:
    global _model_service
    if _model_service is None:
        _model_service = ModelService()
    return _model_service

@router.post("/detect", response_model=DetectionResponse)
def detect_text(body: DetectRequest, 
                model_service: ModelService = Depends(get_model_service)):
    return model_service.detect_text(body)

@router.post("/mask", response_model=MaskResponse)
def mask_text(body: MaskRequest, 
                model_service: ModelService = Depends(get_model_service)):
    return model_service.mask_text(body)

@router.get("/health")
async def health_check(model_service: ModelService = Depends(get_model_service)):
    ready = model_service.is_ready()
    return {
        "status": "healthy" if ready else "not_ready",
        "model_initialized": ready,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
