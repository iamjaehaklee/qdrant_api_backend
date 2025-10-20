"""
Pydantic Models
Data models for OCR chunks and API requests/responses
"""

from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# === Nested Models ===

class BBox(BaseModel):
    """Bounding box coordinates"""
    x: float
    y: float
    width: float
    height: float


class Paragraph(BaseModel):
    """Paragraph information within chunk content"""
    paragraph_id: str
    idx_in_page: int
    text: str
    page: int
    bbox: BBox
    type: str
    confidence_score: float


class PageDimension(BaseModel):
    """Page dimension information"""
    page: int
    width: int
    height: int


class ChunkContent(BaseModel):
    """Detailed chunk content with paragraphs"""
    paragraphs: list[Paragraph]


# === Core Models ===

class OCRChunkPayload(BaseModel):
    """
    Complete OCR chunk payload stored in Qdrant
    Based on actual data structure
    """
    chunk_id: str
    file_id: int
    project_id: int
    storage_file_name: str
    original_file_name: str
    mime_type: str
    total_pages: int
    processing_duration_seconds: int = 0
    language: str
    pages: list[int]
    chunk_number: int
    paragraph_texts: list[str]
    chunk_content: ChunkContent
    page_dimensions: list[PageDimension]
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "+00:00")


class OCRChunkCreate(BaseModel):
    """
    Request model for creating OCR chunk
    Embeddings will be generated automatically from paragraph_texts
    """
    chunk_id: Optional[str] = Field(
        default=None,
        description="UUID string for the chunk. Auto-generated if not provided or invalid.",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"}
    )
    file_id: int
    project_id: int
    storage_file_name: str
    original_file_name: str
    mime_type: str
    total_pages: int
    processing_duration_seconds: int = 0
    language: str
    pages: list[int]
    chunk_number: int
    paragraph_texts: list[str]
    chunk_content: ChunkContent
    page_dimensions: list[PageDimension]


class OCRChunkUpdate(BaseModel):
    """Request model for updating OCR chunk"""
    file_id: Optional[int] = None
    project_id: Optional[int] = None
    storage_file_name: Optional[str] = None
    original_file_name: Optional[str] = None
    paragraph_texts: Optional[list[str]] = None
    chunk_content: Optional[ChunkContent] = None


class OCRChunkResponse(BaseModel):
    """Response model for OCR chunk with point ID"""
    point_id: str
    payload: OCRChunkPayload
    score: Optional[float] = None  # For search results


# === Search Request Models ===

class VectorSearchRequest(BaseModel):
    """Vector similarity search request"""
    query_text: str
    limit: int = Field(default=10, ge=1, le=100)
    score_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    filter_project_id: Optional[int] = None
    filter_file_id: Optional[int] = None


class KeywordSearchRequest(BaseModel):
    """Full-text keyword search request"""
    keyword: str
    limit: int = Field(default=10, ge=1, le=100)
    filter_project_id: Optional[int] = None
    filter_file_id: Optional[int] = None


class HybridSearchRequest(BaseModel):
    """Hybrid search combining vector and keyword"""
    query_text: str
    keyword: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
    score_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    filter_project_id: Optional[int] = None
    filter_file_id: Optional[int] = None


class FilterSearchRequest(BaseModel):
    """Metadata filter search request"""
    project_id: Optional[int] = None
    file_id: Optional[int] = None
    pages: Optional[list[int]] = None
    language: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# === Batch Operations ===

class BatchCreateRequest(BaseModel):
    """Batch create request"""
    chunks: list[OCRChunkCreate]


class BatchDeleteRequest(BaseModel):
    """Batch delete request"""
    point_ids: list[str]


# === Response Models ===

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    qdrant_connected: bool
    collection_exists: bool
    message: Optional[str] = None


class CollectionInfoResponse(BaseModel):
    """Collection information response"""
    collection_name: str
    vectors_count: int
    indexed_vectors_count: int
    points_count: int
    segments_count: int
    status: str
    config: dict[str, Any]


class SearchResponse(BaseModel):
    """Search response with results"""
    results: list[OCRChunkResponse]
    total: int
    limit: int
    offset: int = 0


class ProjectChunksResponse(BaseModel):
    """Response for all chunks in a project"""
    project_id: int
    total_count: int
    chunks: list[OCRChunkResponse]


# === Summary Models ===

class SummaryPayload(BaseModel):
    """
    Complete summary payload stored in Qdrant ocr_summaries collection
    """
    summary_id: str
    project_id: int
    file_id: Optional[int] = None
    summary_text: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "+00:00")


class SummaryCreate(BaseModel):
    """
    Request model for creating summary
    Embeddings will be generated automatically from summary_text
    """
    summary_id: Optional[str] = Field(
        default=None,
        description="UUID string for the summary. Auto-generated if not provided or invalid.",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"}
    )
    project_id: int
    file_id: Optional[int] = None
    summary_text: str


class SummaryUpdate(BaseModel):
    """Request model for updating summary"""
    project_id: Optional[int] = None
    file_id: Optional[int] = None
    summary_text: Optional[str] = None


class SummaryResponse(BaseModel):
    """Response model for summary with optional score"""
    point_id: str
    payload: SummaryPayload
    score: Optional[float] = None


# === Summary Search Request Models ===

class SummaryVectorSearchRequest(BaseModel):
    """Vector similarity search request for summaries"""
    query_text: str
    limit: int = Field(default=10, ge=1, le=100)
    score_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    filter_project_id: Optional[int] = None
    filter_file_id: Optional[int] = None


class SummaryKeywordSearchRequest(BaseModel):
    """Full-text keyword search request for summaries"""
    keyword: str
    limit: int = Field(default=10, ge=1, le=100)
    filter_project_id: Optional[int] = None
    filter_file_id: Optional[int] = None


class SummaryHybridSearchRequest(BaseModel):
    """Hybrid search combining vector and keyword for summaries"""
    query_text: str
    keyword: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
    score_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    filter_project_id: Optional[int] = None
    filter_file_id: Optional[int] = None


class SummarySearchResponse(BaseModel):
    """Search response for summaries"""
    results: list[SummaryResponse]
    total: int
    limit: int
    offset: int = 0
