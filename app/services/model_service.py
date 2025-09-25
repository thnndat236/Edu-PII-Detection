from fastapi import Request, HTTPException, status
from api.models.schemas import (
    DetectRequest, 
    Entity, 
    DetectionResponse, 
    MaskRequest, 
    MaskResponse
)
import logging
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import time
from datetime import datetime, timezone


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

class ModelService:
    def __init__(self, request: Request):
        self.tracer = trace.get_tracer(__name__)
        
        with self.tracer.start_as_current_span("pii_model_initialization") as span:
            # Load PII NER pipeline
            if not hasattr(request.app.state, "ner_pipeline"):
                logger.error("NER pipeline not initialized")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="NER pipeline is not initialized"
                )
            self.ner_pipeline = request.app.state.ner_pipeline
            span.set_attribute("model.type", "pii_token_classification_pipeline")
            span.set_attribute("model.initialization.success", True)
            span.set_attribute("model.config.id2label", self.ner_pipeline.model.config.id2label)
            span.set_attribute("model.config.label2id", self.ner_pipeline.model.config.label2id)

    def detect_text(self, data: DetectRequest) -> DetectionResponse:
        with self.tracer.start_as_current_span("pii_detection") as span:
            start_time = time.process_time()
            span.set_attribute("detection.input.text_length", len(data.text.strip()))
            span.set_attribute("detection.timestamp", datetime.now(timezone.utc).isoformat())

            try:
                if not data.text.strip():
                    span.set_attribute("detection.error", "empty_text")
                    span.set_attribute("detection.error.expected", "more_than_one_character")
                    span.set_attribute("detection.error.actual", f"{data.text.strip()}_character")
                    span.set_status(Status(StatusCode.ERROR, "Invalid empty input text"))
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Input text cannot be empty"
                    )
                
                with self.tracer.start_as_current_span("ner_pipeline_run") as model_span:
                    raw_preds = self.ner_pipeline(data.text)
                    model_span.set_attribute("ner.prediction.count", len(raw_preds))

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
                
                processing_time_ms = (time.process_time() - start_time) * 1000
                span.set_attribute("detection.processing_time_ms", processing_time_ms)
                span.set_attribute("detection.success", True)
                
                logger.info(f"Detected {len(entities)} entities in text")
                return DetectionResponse(text=data.text, entities=entities)
            except HTTPException as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR), str(e.detail))
                span.set_attribute("detection.success", False)
                raise e
            
            except Exception as e:
                logger.exception(f"NER pipeline failed: {str(e)}")
                processing_time_ms = (time.process_time() - start_time) * 1000

                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("detection.success", False)
                span.set_attribute("detection.processing_time_ms", processing_time_ms)

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Internal error while running NER: {str(e)}"
                )

    # def mask_text(self, data: MaskRequest) -> MaskResponse:
    #     try:
    #         if not data.text.strip():
    #             raise HTTPException(
    #                 status_code=status.HTTP_400_BAD_REQUEST,
    #                 detail="Input text cannot be empty"
    #             )
    #         entities = self.ner_pipeline(data.text)
    #     except HTTPException as e:
    #         raise e
        
    #     except Exception as e:
    #         logger.exception(f"Masking failed in pipeline: {str(e)}")
    #         raise HTTPException(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             detail="Internal error while masking text"
    #         )
        

    #     masked_text = data.text
    #     for ent in sorted(entities, key=lambda x: x["start"], reverse=True):
    #         label = ent.get("entity_group", ent.get("entity", "PII"))

    #         prefix = "" if (ent["start"] > 0 and masked_text[ent["start"]-1].isspace()) else " "
    #         suffix = "" if (ent["end"] < len(masked_text) and masked_text[ent["end"]].isspace()) else " "

    #         replacement = f"{prefix}[{label}]{suffix}"
    #         masked_text = masked_text[:ent["start"]] + replacement + masked_text[ent["end"]:]
        
    #     logger.info("Masking successful")
    #     return MaskResponse(original_text=data.text, masked_text=masked_text)
    

    def mask_text(self, data: MaskRequest) -> MaskResponse:
        with self.tracer.start_as_current_span("pii_masking") as span:
            start_time = time.process_time()
            span.set_attribute("masking.input.text_length", len(data.text.strip()))
            span.set_attribute("masking.timestamp", datetime.now(timezone.utc).isoformat())

            try:
                if not data.text.strip():
                    span.set_attribute("masking.error", "empty_text")
                    span.set_status(Status(StatusCode.ERROR, "Invalid empty input text"))
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Input text cannot be empty"
                    )
                
                # Trace pipeline run
                with self.tracer.start_as_current_span("ner_pipeline_run") as model_span:
                    entities = self.ner_pipeline(data.text)
                    model_span.set_attribute("ner.prediction.count", len(entities))

                masked_text = data.text
                for ent in sorted(entities, key=lambda x: x["start"], reverse=True):
                    label = ent.get("entity_group", ent.get("entity", "PII"))

                    prefix = "" if (ent["start"] > 0 and masked_text[ent["start"]-1].isspace()) else " "
                    suffix = "" if (ent["end"] < len(masked_text) and masked_text[ent["end"]].isspace()) else " "

                    replacement = f"{prefix}[{label}]{suffix}"
                    masked_text = masked_text[:ent["start"]] + replacement + masked_text[ent["end"]:]

                processing_time_ms = (time.process_time() - start_time) * 1000
                span.set_attribute("masking.processing_time_ms", processing_time_ms)
                span.set_attribute("masking.success", True)

                logger.info(f"Masking successful, replaced {len(entities)} entities")
                return MaskResponse(original_text=data.text, masked_text=masked_text)

            except HTTPException as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR), str(e.detail))
                span.set_attribute("masking.success", False)
                raise e
            
            except Exception as e:
                logger.exception(f"Masking failed in pipeline: {str(e)}")
                processing_time_ms = (time.process_time() - start_time) * 1000

                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("masking.success", False)
                span.set_attribute("masking.processing_time_ms", processing_time_ms)

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal error while masking text"
                )