from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv


load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Education PII Detector"
    VERSION: str = "1.0.0"
    MODEL_REPO_ID: str = "2phonebabykeem/pii-deberta-v3-base"
    THRESHOLD: float = 0.8

    # Direct connect to Jaeger Collector
    JAEGER_COLLECTOR_ENDPOINT: str = os.getenv("JAEGER_COLLECTOR_ENDPOINT", "http://localhost:4317")
    JAEGER_COLLECTOR_INSECURE: str = os.getenv("JAEGER_COLLECTOR_INSECURE", "True")
    OTEL_SERVICE_NAME: str = os.getenv("OTEL_SERVICE_NAME", "edu-pii-detection-service")
    JAEGER_HOSTNAME: str = os.getenv("JAEGER_HOSTNAME", "edu-pii-detection-service")

settings = Settings()
