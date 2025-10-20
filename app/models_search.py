"""
Search Request and Response Models
Models for 8 different search types across chunks and summaries
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


# === Common Models ===

class ContextPair(BaseModel):
    """Context pair for discovery search"""
    positive: str = Field(description="Positive example point ID")
    negative: str = Field(description="Negative example point ID")


# === Search Request Models ===

class DenseSearchRequest(BaseModel):
    """Dense vector search request using Gemini embeddings"""
    query_text: str = Field(description="Query text to search")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    score_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Minimum score threshold")
    filter_project_id: Optional[int] = Field(default=None, description="Filter by project ID")
    filter_file_id: Optional[int] = Field(default=None, description="Filter by file ID")


class SparseSearchRequest(BaseModel):
    """Sparse vector search request using Kiwi (Korean) or FastEmbed BM25"""
    query_text: str = Field(description="Query text to search")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    score_threshold: Optional[float] = Field(default=None, ge=0.0, description="Minimum score threshold")
    filter_project_id: Optional[int] = Field(default=None, description="Filter by project ID")
    filter_file_id: Optional[int] = Field(default=None, description="Filter by file ID")


class MatchTextSearchRequest(BaseModel):
    """Full-text search using MatchText (no morphological analysis)"""
    query_text: str = Field(description="Query text to match")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    filter_project_id: Optional[int] = Field(default=None, description="Filter by project ID")
    filter_file_id: Optional[int] = Field(default=None, description="Filter by file ID")


class DenseSparseRRFRequest(BaseModel):
    """Hybrid search combining dense + sparse vectors using Reciprocal Rank Fusion"""
    query_text: str = Field(description="Query text to search")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    score_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Minimum score threshold")
    rrf_k: int = Field(default=60, ge=1, le=100, description="RRF constant k (default: 60)")
    filter_project_id: Optional[int] = Field(default=None, description="Filter by project ID")
    filter_file_id: Optional[int] = Field(default=None, description="Filter by file ID")


class RecommendSearchRequest(BaseModel):
    """Recommendation search using positive and negative examples"""
    positive_ids: list[str] = Field(description="List of positive example point IDs")
    negative_ids: list[str] = Field(default_factory=list, description="List of negative example point IDs")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    score_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Minimum score threshold")
    strategy: Literal["average_vector", "best_score"] = Field(
        default="average_vector",
        description="Recommendation strategy"
    )
    filter_project_id: Optional[int] = Field(default=None, description="Filter by project ID")
    filter_file_id: Optional[int] = Field(default=None, description="Filter by file ID")


class DiscoverSearchRequest(BaseModel):
    """Discovery search using context pairs to explore vector space"""
    target_text: str = Field(description="Target text to discover similar items")
    context_pairs: list[ContextPair] = Field(description="List of positive-negative context pairs")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    filter_project_id: Optional[int] = Field(default=None, description="Filter by project ID")
    filter_file_id: Optional[int] = Field(default=None, description="Filter by file ID")


class ScrollSearchRequest(BaseModel):
    """Scroll search for paginated large result sets"""
    limit: int = Field(default=100, ge=1, le=1000, description="Number of results per page")
    offset: Optional[str] = Field(default=None, description="Pagination offset from previous response")
    filter_project_id: Optional[int] = Field(default=None, description="Filter by project ID")
    filter_file_id: Optional[int] = Field(default=None, description="Filter by file ID")
    filter_language: Optional[str] = Field(default=None, description="Filter by language")
    filter_pages: Optional[list[int]] = Field(default=None, description="Filter by page numbers")


class FilterSearchRequest(BaseModel):
    """Metadata filter-based search (existing model, kept for compatibility)"""
    project_id: Optional[int] = None
    file_id: Optional[int] = None
    pages: Optional[list[int]] = None
    language: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# === Search Response Models ===

class SearchResponse(BaseModel):
    """Common search response model"""
    results: list
    total: int
    limit: int
    offset: int = 0


class ScrollSearchResponse(BaseModel):
    """Scroll search response with next_offset"""
    results: list
    total: int
    limit: int
    next_offset: Optional[str] = Field(default=None, description="Offset for next page, None if last page")
