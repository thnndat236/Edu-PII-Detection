from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Education PII Detector"
    VERSION: str = "1.0.0"
    MODEL_REPO_ID: str = "2phonebabykeem/pii-deberta-v3-base"
    THRESHOLD: float = 0.8

settings = Settings()