"""
Search Router for OCR Summaries
8 different search endpoints for ocr_summaries collection
"""

import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
    MatchText,
    SparseVector,
    NamedSparseVector,
    ContextExamplePair
)

from app.config import settings
from app.models import SummaryPayload, SummaryResponse
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
from app.embeddings import (
    generate_query_dense_embedding,
    generate_query_sparse_embedding
)
from app.services.rrf_fusion import reciprocal_rank_fusion

router = APIRouter(prefix="/summaries/search", tags=["Search - Summaries"])

# Create Qdrant client for ocr_summaries collection
qdrant_client = AsyncQdrantClient(
    url=settings.qdrant_url,
    api_key=settings.qdrant_master_api_key,
    timeout=30.0
)
COLLECTION_NAME = "ocr_summaries"


@router.post("/dense", response_model=SearchResponse)
async def dense_search(request: DenseSearchRequest):
    """
    Dense vector search using Gemini embeddings on summary_text

    - Semantic similarity search
    - Uses Gemini embedding-001 (1536 dimensions)
    - Best for: concept-based search, meaning similarity
    """
    try:
        # Generate dense query embedding
        query_vector = await generate_query_dense_embedding(request.query_text)

        # Build filter
        filter_conditions = []
        if request.filter_project_id is not None:
            filter_conditions.append(
                FieldCondition(key="project_id", match=MatchValue(value=request.filter_project_id))
            )
        if request.filter_file_id is not None:
            filter_conditions.append(
                FieldCondition(key="file_id", match=MatchValue(value=request.filter_file_id))
            )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Dense vector search
        results = await qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=(settings.dense_vector_name, query_vector),
            limit=request.limit,
            score_threshold=request.score_threshold,
            query_filter=search_filter,
            with_payload=True,
            with_vectors=False
        )

        # Convert to response
        response_results = [
            SummaryResponse(
                point_id=str(result.id),
                payload=SummaryPayload(**result.payload),
                score=result.score
            )
            for result in results
        ]

        return SearchResponse(
            results=response_results,
            total=len(response_results),
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
    Sparse vector search using Kiwi (Korean) or FastEmbed BM25 on summary_text

    - Keyword-based search with morphological analysis
    - Korean: Kiwi morphological analyzer
    - Non-Korean: FastEmbed BM25
    - Best for: exact term matching, keyword search
    """
    try:
        # Generate sparse query embedding
        sparse_embedding_dict = await generate_query_sparse_embedding(request.query_text)

        # Convert to SparseVector format with explicit type conversion
        sparse_indices = [int(k) for k in sparse_embedding_dict.keys()]
        sparse_values = [float(v) for v in sparse_embedding_dict.values()]

        # Build filter
        filter_conditions = []
        if request.filter_project_id is not None:
            filter_conditions.append(
                FieldCondition(key="project_id", match=MatchValue(value=request.filter_project_id))
            )
        if request.filter_file_id is not None:
            filter_conditions.append(
                FieldCondition(key="file_id", match=MatchValue(value=request.filter_file_id))
            )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Sparse vector search
        results = await qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=NamedSparseVector(
                name=settings.sparse_vector_name,
                vector=SparseVector(indices=sparse_indices, values=sparse_values)
            ),
            limit=request.limit,
            score_threshold=request.score_threshold,
            query_filter=search_filter,
            with_payload=True,
            with_vectors=False
        )

        # Convert to response
        response_results = [
            SummaryResponse(
                point_id=str(result.id),
                payload=SummaryPayload(**result.payload),
                score=result.score
            )
            for result in results
        ]

        return SearchResponse(
            results=response_results,
            total=len(response_results),
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
    Full-text search using MatchText (no morphological analysis) on summary_text

    - Fast text matching
    - No Kiwi analysis (searches as-is)
    - Requires text index on summary_text field
    - Best for: phrase matching, exact text search
    """
    try:
        # Build filter with MatchText
        filter_conditions = []

        filter_conditions.append(
            FieldCondition(key="summary_text", match=MatchText(text=request.query_text))
        )

        if request.filter_project_id is not None:
            filter_conditions.append(
                FieldCondition(key="project_id", match=MatchValue(value=request.filter_project_id))
            )
        if request.filter_file_id is not None:
            filter_conditions.append(
                FieldCondition(key="file_id", match=MatchValue(value=request.filter_file_id))
            )

        search_filter = Filter(must=filter_conditions)

        # Scroll with MatchText filter
        results, _ = await qdrant_client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=search_filter,
            limit=request.limit,
            with_payload=True,
            with_vectors=False
        )

        # Convert to response
        response_results = [
            SummaryResponse(
                point_id=str(result.id),
                payload=SummaryPayload(**result.payload)
            )
            for result in results
        ]

        return SearchResponse(
            results=response_results,
            total=len(response_results),
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
    Hybrid search combining dense + sparse using Reciprocal Rank Fusion on summary_text

    - Combines semantic (dense) and keyword (sparse) search
    - Uses RRF algorithm to merge results
    - Formula: RRF_score = Σ(1 / (k + rank))
    - Best for: balanced search combining meaning and keywords
    """
    try:
        # Run dense and sparse searches in parallel
        async def _dense_search():
            query_vector = await generate_query_dense_embedding(request.query_text)
            filter_conditions = []
            if request.filter_project_id is not None:
                filter_conditions.append(
                    FieldCondition(key="project_id", match=MatchValue(value=request.filter_project_id))
                )
            if request.filter_file_id is not None:
                filter_conditions.append(
                    FieldCondition(key="file_id", match=MatchValue(value=request.filter_file_id))
                )
            search_filter = Filter(must=filter_conditions) if filter_conditions else None

            results = await qdrant_client.search(
                collection_name=COLLECTION_NAME,
                query_vector=(settings.dense_vector_name, query_vector),
                limit=request.limit * 2,
                score_threshold=request.score_threshold,
                query_filter=search_filter,
                with_payload=True,
                with_vectors=False
            )

            return [
                SummaryResponse(
                    point_id=str(result.id),
                    payload=SummaryPayload(**result.payload),
                    score=result.score
                )
                for result in results
            ]

        async def _sparse_search():
            sparse_embedding_dict = await generate_query_sparse_embedding(request.query_text)
            sparse_indices = [int(k) for k in sparse_embedding_dict.keys()]
            sparse_values = [float(v) for v in sparse_embedding_dict.values()]

            filter_conditions = []
            if request.filter_project_id is not None:
                filter_conditions.append(
                    FieldCondition(key="project_id", match=MatchValue(value=request.filter_project_id))
                )
            if request.filter_file_id is not None:
                filter_conditions.append(
                    FieldCondition(key="file_id", match=MatchValue(value=request.filter_file_id))
                )
            search_filter = Filter(must=filter_conditions) if filter_conditions else None

            results = await qdrant_client.search(
                collection_name=COLLECTION_NAME,
                query_vector=NamedSparseVector(
                    name=settings.sparse_vector_name,
                    vector=SparseVector(indices=sparse_indices, values=sparse_values)
                ),
                limit=request.limit * 2,
                score_threshold=request.score_threshold,
                query_filter=search_filter,
                with_payload=True,
                with_vectors=False
            )

            return [
                SummaryResponse(
                    point_id=str(result.id),
                    payload=SummaryPayload(**result.payload),
                    score=result.score
                )
                for result in results
            ]

        dense_results, sparse_results = await asyncio.gather(_dense_search(), _sparse_search())

        # Apply RRF fusion
        fused_results = reciprocal_rank_fusion(
            dense_results=dense_results,
            sparse_results=sparse_results,
            k=request.rrf_k,
            id_key="point_id"
        )

        # Take top results and convert to SummaryResponse with RRF score
        response_results = [
            SummaryResponse(
                point_id=result.point_id,
                payload=result.payload,
                score=rrf_score
            )
            for result, rrf_score in fused_results[:request.limit]
        ]

        return SearchResponse(
            results=response_results,
            total=len(response_results),
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

    - Find similar summaries to positive examples
    - Avoid summaries similar to negative examples
    - Strategies: average_vector, best_score
    - Best for: "more like this", "less like that" searches
    """
    try:
        # Build filter
        filter_conditions = []
        if request.filter_project_id is not None:
            filter_conditions.append(
                FieldCondition(key="project_id", match=MatchValue(value=request.filter_project_id))
            )
        if request.filter_file_id is not None:
            filter_conditions.append(
                FieldCondition(key="file_id", match=MatchValue(value=request.filter_file_id))
            )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Recommendation search
        results = await qdrant_client.recommend(
            collection_name=COLLECTION_NAME,
            positive=request.positive_ids,
            negative=request.negative_ids,
            limit=request.limit,
            score_threshold=request.score_threshold,
            query_filter=search_filter,
            using=settings.dense_vector_name,
            strategy=request.strategy,
            with_payload=True,
            with_vectors=False
        )

        # Convert to response
        response_results = [
            SummaryResponse(
                point_id=str(result.id),
                payload=SummaryPayload(**result.payload),
                score=result.score
            )
            for result in results
        ]

        return SearchResponse(
            results=response_results,
            total=len(response_results),
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
    - Finds summaries similar to target within context constraints
    - Best for: exploratory search, context-aware discovery
    """
    try:
        # Generate target embedding
        target_vector = await generate_query_dense_embedding(request.target_text)

        # Build context pairs
        context = [
            ContextExamplePair(positive=pair.positive, negative=pair.negative)
            for pair in request.context_pairs
        ]

        # Build filter
        filter_conditions = []
        if request.filter_project_id is not None:
            filter_conditions.append(
                FieldCondition(key="project_id", match=MatchValue(value=request.filter_project_id))
            )
        if request.filter_file_id is not None:
            filter_conditions.append(
                FieldCondition(key="file_id", match=MatchValue(value=request.filter_file_id))
            )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Discovery search
        try:
            results = await qdrant_client.discover(
                collection_name=COLLECTION_NAME,
                target=target_vector,
                context=context,
                using=settings.dense_vector_name,
                limit=request.limit,
                query_filter=search_filter,
                with_payload=True,
                with_vectors=False
            )
        except Exception as discover_err:
            # Enhanced error logging for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                f"Qdrant discover() failed: {str(discover_err)}, "
                f"context_pairs={[{'pos':p.positive,'neg':p.negative} for p in request.context_pairs]}, "
                f"vector_name={settings.dense_vector_name}, "
                f"collection={COLLECTION_NAME}"
            )
            raise

        # Convert to response
        response_results = [
            SummaryResponse(
                point_id=str(result.id),
                payload=SummaryPayload(**result.payload),
                score=result.score
            )
            for result in results
        ]

        return SearchResponse(
            results=response_results,
            total=len(response_results),
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
        filter_conditions = []

        if request.filter_project_id is not None:
            filter_conditions.append(
                FieldCondition(key="project_id", match=MatchValue(value=request.filter_project_id))
            )
        if request.filter_file_id is not None:
            filter_conditions.append(
                FieldCondition(key="file_id", match=MatchValue(value=request.filter_file_id))
            )
        if request.filter_language is not None:
            filter_conditions.append(
                FieldCondition(key="language", match=MatchValue(value=request.filter_language))
            )
        if request.filter_pages is not None and len(request.filter_pages) > 0:
            for page in request.filter_pages:
                filter_conditions.append(
                    FieldCondition(key="pages", match=MatchValue(value=page))
                )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Scroll
        results, next_offset = await qdrant_client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=search_filter,
            limit=request.limit,
            offset=request.offset,
            with_payload=True,
            with_vectors=False
        )

        # Convert to response
        response_results = [
            SummaryResponse(
                point_id=str(result.id),
                payload=SummaryPayload(**result.payload)
            )
            for result in results
        ]

        return ScrollSearchResponse(
            results=response_results,
            total=len(response_results),
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
        filter_conditions = []

        if request.project_id is not None:
            filter_conditions.append(
                FieldCondition(key="project_id", match=MatchValue(value=request.project_id))
            )
        if request.file_id is not None:
            filter_conditions.append(
                FieldCondition(key="file_id", match=MatchValue(value=request.file_id))
            )
        if request.language is not None:
            filter_conditions.append(
                FieldCondition(key="language", match=MatchValue(value=request.language))
            )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Scroll with numeric offset support
        # Note: Qdrant scroll() offset is point ID-based, so we fetch extra and skip manually
        fetch_limit = request.limit + request.offset
        results, next_offset = await qdrant_client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=search_filter,
            limit=fetch_limit,
            with_payload=True,
            with_vectors=False
        )

        # Apply numeric offset by skipping first N results
        paginated_results = results[request.offset:request.offset + request.limit]

        # Convert to response
        response_results = [
            SummaryResponse(
                point_id=str(result.id),
                payload=SummaryPayload(**result.payload)
            )
            for result in paginated_results
        ]

        return SearchResponse(
            results=response_results,
            total=len(response_results),
            limit=request.limit,
            offset=request.offset
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Filter search failed: {str(e)}"
        )
