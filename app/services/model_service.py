from fastapi import Request, HTTPException, status
from api.models.schemas import (
    DetectRequest, 
    Entity, 
    DetectionResponse, 
    MaskRequest, 
    MaskResponse
)
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

class ModelService:
    def __init__(self, request: Request):
        if not hasattr(request.app.state, "ner_pipeline"):
            logger.error("NER pipeline not initialized")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="NER pipeline is not initialized"
            )
        self.ner_pipeline = request.app.state.ner_pipeline


    def run_ner(self, data: DetectRequest) -> DetectionResponse:
        try:
            if not data.text.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Input text cannot be empty"
                )
            raw_preds = self.ner_pipeline(data.text)
        except HTTPException as e:
            raise e
        
        except Exception as e:
            logger.exception(f"NER pipeline failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal error while running NER"
            )
        
        entities = [
            Entity(
                entity_group=pred["entity_group"],
                score=pred["score"],
                word=pred["word"],
                start=pred["start"],
                end=pred["end"]
            )
            for pred in raw_preds
        ]
        
        logger.info(f"Detected {len(entities)} entities in text")
        return DetectionResponse(text=data.text, entities=entities)

    def mask_text(self, data: MaskRequest) -> MaskResponse:
        try:
            if not data.text.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Input text cannot be empty"
                )
            entities = self.ner_pipeline(data.text)
        except HTTPException as e:
            raise e
        
        except Exception as e:
            logger.exception(f"Masking failed in pipeline: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal error while masking text"
            )
        

        masked_text = data.text
        for ent in sorted(entities, key=lambda x: x["start"], reverse=True):
            label = ent.get("entity_group", ent.get("entity", "PII"))

            prefix = "" if (ent["start"] > 0 and masked_text[ent["start"]-1].isspace()) else " "
            suffix = "" if (ent["end"] < len(masked_text) and masked_text[ent["end"]].isspace()) else " "

            replacement = f"{prefix}[{label}]{suffix}"
            masked_text = masked_text[:ent["start"]] + replacement + masked_text[ent["end"]:]
        
        logger.info("Masking successful")
        return MaskResponse(original_text=data.text, masked_text=masked_text)