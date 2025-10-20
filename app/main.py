"""
Qdrant API Backend
FastAPI application for OCR chunks CRUD and search operations
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import points, health, documentai_ocr, summaries, search_chunks, search_summaries
from app.config import settings

# Create FastAPI application
app = FastAPI(
    title="Qdrant OCR API",
    description="FastAPI server for OCR chunks CRUD and search operations with Qdrant",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - allow all origins for development
# TODO: Configure appropriate origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(points.router)
app.include_router(search_chunks.router)
app.include_router(search_summaries.router)
app.include_router(summaries.router)
app.include_router(documentai_ocr.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Qdrant OCR API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "collections": ["ocr_chunks", "ocr_summaries"]
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    print("=" * 50)
    print("Qdrant OCR API Starting...")
    print(f"Collections: ocr_chunks, ocr_summaries")
    print(f"Qdrant URL: {settings.qdrant_url}")
    print("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    print("Qdrant OCR API Shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
