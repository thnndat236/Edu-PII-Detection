from pydantic import BaseModel
from typing import List

class DetectRequest(BaseModel):
    text: str

class Entity(BaseModel):
    entity_group: str
    score: float
    word: str
    start: int
    end: int

class DetectionResponse(BaseModel):
    text: str
    entities: List[Entity]

class MaskRequest(BaseModel):
    text: str

class MaskResponse(BaseModel):
    original_text: str
    masked_text: str