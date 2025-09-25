from fastapi import APIRouter, Request
from services.model_service import ModelService
from api.models.schemas import DetectRequest, DetectionResponse

router = APIRouter()

@router.post("/detect", response_model=DetectionResponse)
def detect_text(request: Request, body: DetectRequest):
    service = ModelService(request)
    return service.run_ner(body)
