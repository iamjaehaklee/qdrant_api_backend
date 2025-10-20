"""
Search Router for OCR Chunks
8 different search endpoints for ocr_chunks collection
"""

from fastapi import APIRouter, HTTPException, status

from app.models_search import (
    DenseSearchRequest,
    SparseSearchRequest,
    MatchTextSearchRequest,
    DenseSparseRRFRequest,
    RecommendSearchRequest,
    DiscoverSearchRequest,
    ScrollSearchRequest,
    FilterSearchRequest,
    SearchResponse,
    ScrollSearchResponse
)
from app.qdrant_service import qdrant_service

router = APIRouter(prefix="/search", tags=["Search - Chunks"])


@router.post("/dense", response_model=SearchResponse)
async def dense_search(request: DenseSearchRequest):
    """
    Dense vector search using Gemini embeddings

    - Semantic similarity search
    - Uses Gemini embedding-001 (1536 dimensions)
    - Best for: concept-based search, meaning similarity
    """
    try:
        results = await qdrant_service.dense_search(
            query_text=request.query_text,
            limit=request.limit,
            score_threshold=request.score_threshold,
            filter_project_id=request.filter_project_id,
            filter_file_id=request.filter_file_id
        )

        return SearchResponse(
            results=results,
            total=len(results),
            limit=request.limit,
            offset=0
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dense search failed: {str(e)}"
        )


@router.post("/sparse", response_model=SearchResponse)
async def sparse_search(request: SparseSearchRequest):
    """
    Sparse vector search using Kiwi (Korean) or FastEmbed BM25

    - Keyword-based search with morphological analysis
    - Korean: Kiwi morphological analyzer
    - Non-Korean: FastEmbed BM25
    - Best for: exact term matching, keyword search
    """
    try:
        results = await qdrant_service.sparse_search(
            query_text=request.query_text,
            limit=request.limit,
            score_threshold=request.score_threshold,
            filter_project_id=request.filter_project_id,
            filter_file_id=request.filter_file_id
        )

        return SearchResponse(
            results=results,
            total=len(results),
            limit=request.limit,
            offset=0
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sparse search failed: {str(e)}"
        )


@router.post("/matchtext", response_model=SearchResponse)
async def matchtext_search(request: MatchTextSearchRequest):
    """
    Full-text search using MatchText (no morphological analysis)

    - Fast text matching
    - No Kiwi analysis (searches as-is)
    - Requires text index on paragraph_texts field
    - Best for: phrase matching, exact text search
    """
    try:
        results = await qdrant_service.matchtext_search(
            query_text=request.query_text,
            limit=request.limit,
            filter_project_id=request.filter_project_id,
            filter_file_id=request.filter_file_id
        )

        return SearchResponse(
            results=results,
            total=len(results),
            limit=request.limit,
            offset=0
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MatchText search failed: {str(e)}"
        )


@router.post("/dense_sparse_rrf", response_model=SearchResponse)
async def dense_sparse_rrf_search(request: DenseSparseRRFRequest):
    """
    Hybrid search combining dense + sparse using Reciprocal Rank Fusion

    - Combines semantic (dense) and keyword (sparse) search
    - Uses RRF algorithm to merge results
    - Formula: RRF_score = Σ(1 / (k + rank))
    - Best for: balanced search combining meaning and keywords
    """
    try:
        results = await qdrant_service.dense_sparse_rrf_search(
            query_text=request.query_text,
            limit=request.limit,
            score_threshold=request.score_threshold,
            rrf_k=request.rrf_k,
            filter_project_id=request.filter_project_id,
            filter_file_id=request.filter_file_id
        )

        return SearchResponse(
            results=results,
            total=len(results),
            limit=request.limit,
            offset=0
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dense+Sparse RRF search failed: {str(e)}"
        )


@router.post("/recommend", response_model=SearchResponse)
async def recommend_search(request: RecommendSearchRequest):
    """
    Recommendation search using positive and negative examples

    - Find similar items to positive examples
    - Avoid items similar to negative examples
    - Strategies: average_vector, best_score
    - Best for: "more like this", "less like that" searches
    """
    try:
        results = await qdrant_service.recommend_search(
            positive_ids=request.positive_ids,
            negative_ids=request.negative_ids,
            limit=request.limit,
            score_threshold=request.score_threshold,
            strategy=request.strategy,
            filter_project_id=request.filter_project_id,
            filter_file_id=request.filter_file_id
        )

        return SearchResponse(
            results=results,
            total=len(results),
            limit=request.limit,
            offset=0
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation search failed: {str(e)}"
        )


@router.post("/discover", response_model=SearchResponse)
async def discover_search(request: DiscoverSearchRequest):
    """
    Discovery search using context pairs to explore vector space

    - Uses positive-negative context pairs to define search space
    - Finds items similar to target within context constraints
    - Best for: exploratory search, context-aware discovery
    """
    try:
        # Convert context pairs from model to tuples
        context_pairs = [(pair.positive, pair.negative) for pair in request.context_pairs]

        results = await qdrant_service.discover_search(
            target_text=request.target_text,
            context_pairs=context_pairs,
            limit=request.limit,
            filter_project_id=request.filter_project_id,
            filter_file_id=request.filter_file_id
        )

        return SearchResponse(
            results=results,
            total=len(results),
            limit=request.limit,
            offset=0
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Discovery search failed: {str(e)}"
        )


@router.post("/scroll", response_model=ScrollSearchResponse)
async def scroll_search(request: ScrollSearchRequest):
    """
    Scroll search for paginated large result sets

    - Efficiently retrieve large numbers of results
    - Pagination support with offset
    - Supports metadata filtering
    - Best for: bulk operations, data export
    """
    try:
        results, next_offset = await qdrant_service.scroll_search(
            limit=request.limit,
            offset=request.offset,
            filter_project_id=request.filter_project_id,
            filter_file_id=request.filter_file_id,
            filter_language=request.filter_language,
            filter_pages=request.filter_pages
        )

        return ScrollSearchResponse(
            results=results,
            total=len(results),
            limit=request.limit,
            next_offset=next_offset
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scroll search failed: {str(e)}"
        )


@router.post("/filter", response_model=SearchResponse)
async def filter_search(request: FilterSearchRequest):
    """
    Metadata filter-based search (no vector search)

    - Filter by project_id, file_id, language, pages
    - No semantic or keyword search
    - Best for: metadata-only queries
    """
    try:
        results, next_offset = await qdrant_service.filter_search(
            project_id=request.project_id,
            file_id=request.file_id,
            pages=request.pages,
            language=request.language,
            limit=request.limit,
            offset=request.offset
        )

        return SearchResponse(
            results=results,
            total=len(results),
            limit=request.limit,
            offset=request.offset
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Filter search failed: {str(e)}"
        )
