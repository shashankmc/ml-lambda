from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import summarize, segment
from app.config import settings
from loguru import logger

app = FastAPI(
    title="ML Lambda — Summarization Service",
    version="1.0.0",
    description="FastAPI service for legal case summarization and segmentation"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(summarize.router, tags=["summarize"])
app.include_router(segment.router, tags=["segment"])

@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "model": settings.summarization_model,
        "database": "connected"
    }

@app.on_event("startup")
def preload_models():
    """Preload models on startup."""
    from app.services.generator import get_summarizer, get_embedder
    logger.info("Preloading models on startup...")
    get_summarizer()
    get_embedder()
    logger.info("Models ready.")

@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "ML Lambda",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "summarize": "/summarize (POST)",
            "segment": "/segment/ml (POST)",
            "docs": "/docs",
        }
    }
