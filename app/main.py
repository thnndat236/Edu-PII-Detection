from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from transformers import pipeline
from api.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Startup: Loading NER pipeline...")
    ner_pipeline = pipeline(
        "ner",
        model=settings.MODEL_REPO_ID, 
        tokenizer=settings.MODEL_REPO_ID,
        aggregation_strategy="first" 
    )
    app.state.ner_pipeline = ner_pipeline
    print("NER pipeline loaded")

    yield

    print("Cleaning up resources...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def main():
    return {"message": "Welcome to Education PII Detection"}

app.include_router(api_router, prefix="/api")