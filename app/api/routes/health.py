from fastapi import APIRouter, Request
from datetime import datetime, timezone

router = APIRouter()

@router.get("/health")
async def health_check(request: Request):
    ready = hasattr(request.app.state, "ner_pipeline")
    return {
        "status": "healthy" if ready else "not_ready",
        "model_initialized": ready,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }