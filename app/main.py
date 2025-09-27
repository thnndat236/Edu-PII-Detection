from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from transformers import pipeline
from api.routes import api_router
import logging
from utils.tracer import setup_tracing, remove_tracing
from prometheus_fastapi_instrumentator import Instrumentator


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

global tracer

@asynccontextmanager
async def lifespan(app: FastAPI):
    global tracer

    logger.info("Starting Education PII Detection API...")
    
    # Setup tracing on startup
    logger.info("OpenTelemetry tracing configuring...")
    tracer = setup_tracing()
    logger.info("OpenTelemetry tracing configured successfully")

    # Expose metrics on startup
    logger.info("Exposing metrics with Prometheus Fastapi Instrumentator...")
    instrumentator.expose(app)
    logger.info("Exposing metrics successfully")

    # Setup NER pipeline on startup
    logger.info("Starting NER pipeline...")
    ner_pipeline = pipeline(
        "ner",
        model=settings.MODEL_REPO_ID, 
        tokenizer=settings.MODEL_REPO_ID,
        aggregation_strategy="first" 
    )
    app.state.ner_pipeline = ner_pipeline
    logger.info("NER pipeline loaded")

    yield

    # Shutdown
    logger.info("Cleaning up resources...")
    remove_tracing()
    print("Telemetry resources cleaned up")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    root_path="/api"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics endpoint
instrumentator = Instrumentator(excluded_handlers=["/metrics"]).instrument(app)

@app.get("/")
def main():
    return {"message": "Welcome to Education PII Detection"}

@app.get("/health")
async def health_check():
    global tracer
    if tracer:
        with tracer.start_as_current_span("health_check") as span:
            span.set_attribute("health.status", "ok")
            span.set_attribute("tracing", "enable")
        return {"status": "healthy", "tracing": "enable"}
    return {"status": "healthy", "tracing": "disable"}

app.include_router(api_router)