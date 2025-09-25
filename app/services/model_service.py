from fastapi import Request
from api.models.schemas import (
    DetectRequest, 
    Entity, 
    DetectionResponse, 
    MaskRequest, 
    MaskResponse
)

class ModelService:
    def __init__(self, request: Request):
        self.ner_pipeline = request.app.state.ner_pipeline

    def run_ner(self, data: DetectRequest) -> DetectionResponse:
        raw_preds = self.ner_pipeline(data.text)
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
        return DetectionResponse(text=data.text, entities=entities)

    def mask_text(self, data: MaskRequest) -> MaskResponse:
        entities = self.ner_pipeline(data.text)

        masked_text = data.text
        for ent in sorted(entities, key=lambda x: x["start"], reverse=True):
            label = ent.get("entity_group", ent.get("entity", "PII"))

            prefix = "" if (ent["start"] > 0 and masked_text[ent["start"]-1].isspace()) else " "
            suffix = "" if (ent["end"] < len(masked_text) and masked_text[ent["end"]].isspace()) else " "

            replacement = f"{prefix}[{label}]{suffix}"
            masked_text = masked_text[:ent["start"]] + replacement + masked_text[ent["end"]:]

        return MaskResponse(original_text=data.text, masked_text=masked_text)