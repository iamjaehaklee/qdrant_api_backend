"""
Document AI OCR Models
Pydantic models for Google Document AI OCR integration
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


# === Document AI Response Structure ===

class DocumentAIBlock(BaseModel):
    """Document AI block structure"""
    layout: Dict[str, Any]


class DocumentAIPage(BaseModel):
    """Document AI page structure"""
    pageNumber: int = Field(..., description="1-based page number")
    dimension: Dict[str, float] = Field(..., description="Page dimensions {width, height}")
    blocks: List[DocumentAIBlock] = Field(default_factory=list, description="Text blocks in page")
    detected_languages: Optional[List[Dict[str, Any]]] = Field(None, description="Detected languages")


class DocumentAIResult(BaseModel):
    """Google Document AI OCR result"""
    text: str = Field(..., description="Full document text (source of truth)")
    pages: List[DocumentAIPage] = Field(..., description="Page-by-page OCR results")


# === Request/Response Models ===

class FileMetadata(BaseModel):
    """File metadata for OCR processing"""
    file_id: int
    project_id: int
    storage_file_name: str
    original_file_name: str
    mime_type: str
    total_pages: int


class DocumentAIStoreChunksRequest(BaseModel):
    """Request to store Document AI OCR results as Qdrant chunks"""
    document_ai_result: DocumentAIResult = Field(..., description="Document AI OCR response")
    file_metadata: FileMetadata = Field(..., description="File metadata")


class ProcessingSummary(BaseModel):
    """Processing summary statistics"""
    total_pages: int
    total_paragraphs: int
    total_windows: int
    language: str


class DocumentAIStoreChunksResponse(BaseModel):
    """Response after storing Document AI OCR results"""
    success: bool
    chunk_ids: List[str] = Field(..., description="List of created chunk IDs")
    total_chunks: int = Field(..., description="Total number of chunks created")
    processing_time: float = Field(..., description="Processing time in seconds")
    summary: ProcessingSummary = Field(..., description="Processing summary")
