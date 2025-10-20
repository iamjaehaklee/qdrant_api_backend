"""
Qdrant Service
Handles all interactions with Qdrant vector database
"""

import uuid
import asyncio
from typing import Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    MatchText,
    Range,
    ScoredPoint,
    NamedVector,
    SparseVector
)

from app.config import settings
from app.models import (
    OCRChunkCreate,
    OCRChunkPayload,
    OCRChunkUpdate,
    OCRChunkResponse
)
from app.embeddings import (
    generate_dense_embedding_from_paragraphs,
    generate_sparse_embedding_from_paragraphs,
    generate_query_dense_embedding,
    generate_query_sparse_embedding,
    batch_generate_dense_embeddings
)


class QdrantService:
    """Service class for Qdrant operations"""

    def __init__(self, collection_name: str = "ocr_chunks"):
        """
        Initialize Qdrant async client

        Args:
            collection_name: Name of the Qdrant collection to use (default: "ocr_chunks")
        """
        self.client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_master_api_key,
            timeout=30.0
        )
        self.collection_name = collection_name

    @staticmethod
    def _validate_or_generate_uuid(chunk_id: Optional[str]) -> str:
        """
        Validate if chunk_id is a valid UUID, otherwise generate new one

        Args:
            chunk_id: Chunk ID to validate

        Returns:
            Valid UUID string
        """
        if chunk_id:
            try:
                # Attempt to parse as UUID to validate format
                uuid.UUID(chunk_id)
                return chunk_id
            except (ValueError, AttributeError):
                # Invalid UUID format, generate new one
                pass

        # Generate new UUID if None or invalid
        return str(uuid.uuid4())

    async def check_health(self) -> dict:
        """Check Qdrant connection and collection status"""
        try:
            collections = await self.client.get_collections()
            collection_exists = any(
                col.name == self.collection_name
                for col in collections.collections
            )
            return {
                "connected": True,
                "collection_exists": collection_exists
            }
        except Exception as e:
            return {
                "connected": False,
                "collection_exists": False,
                "error": str(e)
            }

    async def get_collection_info(self) -> dict:
        """Get collection information"""
        try:
            info = await self.client.get_collection(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "vectors_count": info.vectors_count or 0,
                "indexed_vectors_count": info.indexed_vectors_count or 0,
                "points_count": info.points_count or 0,
                "segments_count": info.segments_count,
                "status": info.status,
                "config": info.config.dict() if info.config else {}
            }
        except Exception as e:
            raise ValueError(f"Failed to get collection info: {str(e)}")

    async def create_point(self, chunk: OCRChunkCreate) -> str:
        """
        Create a single point in Qdrant

        Args:
            chunk: OCR chunk data

        Returns:
            Point ID (chunk_id)
        """
        # Generate chunk_id if not provided or invalid UUID
        point_id = self._validate_or_generate_uuid(chunk.chunk_id)

        # Generate embeddings
        dense_vector = await generate_dense_embedding_from_paragraphs(chunk.paragraph_texts)
        sparse_vector_dict = await generate_sparse_embedding_from_paragraphs(chunk.paragraph_texts)

        # Convert sparse vector dict to NamedSparseVector format
        sparse_indices = list(sparse_vector_dict.keys())
        sparse_values = list(sparse_vector_dict.values())

        # Prepare payload
        payload = OCRChunkPayload(
            chunk_id=point_id,
            **chunk.model_dump(exclude={"chunk_id"})
        ).model_dump()

        # Create point with named vectors
        point = PointStruct(
            id=point_id,
            vector={
                settings.dense_vector_name: dense_vector,
                settings.sparse_vector_name: SparseVector(
                    indices=sparse_indices,
                    values=sparse_values
                )
            },
            payload=payload
        )

        # Upsert to Qdrant
        await self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )

        return point_id

    async def batch_create_points(self, chunks: list[OCRChunkCreate]) -> list[str]:
        """
        Create multiple points in batch with optimized embedding generation

        Uses batch API for dense embeddings (1 API call instead of N calls)
        and asyncio.gather for sparse embeddings (parallel processing).

        Args:
            chunks: List of OCR chunk data

        Returns:
            List of point IDs
        """
        if not chunks:
            return []

        point_ids = []
        for chunk in chunks:
            point_id = self._validate_or_generate_uuid(chunk.chunk_id)
            point_ids.append(point_id)

        # Optimize: Batch generate dense embeddings in single API call
        all_combined_texts = ["\n".join(chunk.paragraph_texts) for chunk in chunks]
        dense_vectors = await batch_generate_dense_embeddings(
            all_combined_texts,
            task_type="RETRIEVAL_DOCUMENT"
        )

        # Optimize: Generate sparse embeddings in parallel
        sparse_vector_dicts = await asyncio.gather(*[
            generate_sparse_embedding_from_paragraphs(chunk.paragraph_texts)
            for chunk in chunks
        ])

        # Create points with generated embeddings
        points = []
        for idx, chunk in enumerate(chunks):
            # Convert sparse vector dict to SparseVector format
            sparse_indices = list(sparse_vector_dicts[idx].keys())
            sparse_values = list(sparse_vector_dicts[idx].values())

            # Prepare payload
            payload = OCRChunkPayload(
                chunk_id=point_ids[idx],
                **chunk.model_dump(exclude={"chunk_id"})
            ).model_dump()

            # Create point
            point = PointStruct(
                id=point_ids[idx],
                vector={
                    settings.dense_vector_name: dense_vectors[idx],
                    settings.sparse_vector_name: SparseVector(
                        indices=sparse_indices,
                        values=sparse_values
                    )
                },
                payload=payload
            )
            points.append(point)

        # Batch upsert
        await self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

        return point_ids

    async def get_point(self, point_id: str) -> Optional[OCRChunkResponse]:
        """
        Retrieve a point by ID

        Args:
            point_id: Point ID to retrieve

        Returns:
            OCR chunk response or None if not found
        """
        try:
            point = await self.client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id],
                with_payload=True,
                with_vectors=False
            )

            if not point:
                return None

            return OCRChunkResponse(
                point_id=str(point[0].id),
                payload=OCRChunkPayload(**point[0].payload)
            )
        except Exception as e:
            raise ValueError(f"Failed to retrieve point: {str(e)}")

    async def update_point(self, point_id: str, update: OCRChunkUpdate) -> bool:
        """
        Update a point's payload

        Args:
            point_id: Point ID to update
            update: Update data

        Returns:
            True if successful
        """
        # Get existing point
        existing = await self.get_point(point_id)
        if not existing:
            raise ValueError(f"Point {point_id} not found")

        # Merge updates
        update_dict = update.model_dump(exclude_unset=True)

        # If paragraph_texts updated, regenerate embeddings
        if "paragraph_texts" in update_dict:
            dense_vector = await generate_dense_embedding_from_paragraphs(update_dict["paragraph_texts"])
            sparse_vector_dict = await generate_sparse_embedding_from_paragraphs(update_dict["paragraph_texts"])

            # Convert sparse vector dict to SparseVector format
            sparse_indices = list(sparse_vector_dict.keys())
            sparse_values = list(sparse_vector_dict.values())

            # Update vectors
            await self.client.update_vectors(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector={
                            settings.dense_vector_name: dense_vector,
                            settings.sparse_vector_name: SparseVector(
                                indices=sparse_indices,
                                values=sparse_values
                            )
                        }
                    )
                ]
            )

        # Update payload
        await self.client.set_payload(
            collection_name=self.collection_name,
            payload=update_dict,
            points=[point_id]
        )

        return True

    async def delete_point(self, point_id: str) -> bool:
        """
        Delete a point

        Args:
            point_id: Point ID to delete

        Returns:
            True if successful
        """
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=[point_id]
        )
        return True

    async def batch_delete_points(self, point_ids: list[str]) -> bool:
        """
        Delete multiple points

        Args:
            point_ids: List of point IDs to delete

        Returns:
            True if successful
        """
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=point_ids
        )
        return True

    async def vector_search(
        self,
        query_text: str,
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_project_id: Optional[int] = None,
        filter_file_id: Optional[int] = None
    ) -> list[OCRChunkResponse]:
        """
        Vector similarity search

        Args:
            query_text: Query text
            limit: Maximum results
            score_threshold: Minimum score threshold
            filter_project_id: Filter by project ID
            filter_file_id: Filter by file ID

        Returns:
            List of search results
        """
        # Generate query embedding
        query_vector = await generate_query_dense_embedding(query_text)

        # Build filter
        filter_conditions = []
        if filter_project_id is not None:
            filter_conditions.append(
                FieldCondition(key="project_id", match=MatchValue(value=filter_project_id))
            )
        if filter_file_id is not None:
            filter_conditions.append(
                FieldCondition(key="file_id", match=MatchValue(value=filter_file_id))
            )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Search
        results = await self.client.search(
            collection_name=self.collection_name,
            query_vector=(settings.dense_vector_name, query_vector),
            limit=limit,
            score_threshold=score_threshold,
            query_filter=search_filter,
            with_payload=True,
            with_vectors=False
        )

        # Convert to response
        return [
            OCRChunkResponse(
                point_id=str(result.id),
                payload=OCRChunkPayload(**result.payload),
                score=result.score
            )
            for result in results
        ]

    async def keyword_search(
        self,
        keyword: str,
        limit: int = 10,
        filter_project_id: Optional[int] = None,
        filter_file_id: Optional[int] = None
    ) -> list[OCRChunkResponse]:
        """
        Full-text keyword search using Qdrant's text index

        Args:
            keyword: Keyword to search
            limit: Maximum results
            filter_project_id: Filter by project ID
            filter_file_id: Filter by file ID

        Returns:
            List of search results
        """
        # Build filter with text matching
        filter_conditions = []

        # Add text match condition using MatchText for full-text search
        filter_conditions.append(
            FieldCondition(key="paragraph_texts", match=MatchText(text=keyword))
        )

        if filter_project_id is not None:
            filter_conditions.append(
                FieldCondition(key="project_id", match=MatchValue(value=filter_project_id))
            )
        if filter_file_id is not None:
            filter_conditions.append(
                FieldCondition(key="file_id", match=MatchValue(value=filter_file_id))
            )

        search_filter = Filter(must=filter_conditions)

        # Scroll (filter-based retrieval)
        results, _ = await self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=search_filter,
            limit=limit,
            with_payload=True,
            with_vectors=False
        )

        # Convert to response
        return [
            OCRChunkResponse(
                point_id=str(result.id),
                payload=OCRChunkPayload(**result.payload)
            )
            for result in results
        ]

    async def filter_search(
        self,
        project_id: Optional[int] = None,
        file_id: Optional[int] = None,
        pages: Optional[list[int]] = None,
        language: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> tuple[list[OCRChunkResponse], Optional[str]]:
        """
        Metadata filter search

        Args:
            project_id: Filter by project ID
            file_id: Filter by file ID
            pages: Filter by page numbers
            language: Filter by language
            limit: Maximum results
            offset: Offset for pagination

        Returns:
            Tuple of (results, next_page_offset)
        """
        filter_conditions = []

        if project_id is not None:
            filter_conditions.append(
                FieldCondition(key="project_id", match=MatchValue(value=project_id))
            )
        if file_id is not None:
            filter_conditions.append(
                FieldCondition(key="file_id", match=MatchValue(value=file_id))
            )
        if language is not None:
            filter_conditions.append(
                FieldCondition(key="language", match=MatchValue(value=language))
            )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Scroll with offset
        results, next_offset = await self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=search_filter,
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )

        # Convert to response
        responses = [
            OCRChunkResponse(
                point_id=str(result.id),
                payload=OCRChunkPayload(**result.payload)
            )
            for result in results
        ]

        return responses, next_offset

    async def get_all_by_project_id(self, project_id: int) -> list[OCRChunkResponse]:
        """
        Retrieve all chunks for a given project ID

        Args:
            project_id: Project ID to filter by

        Returns:
            List of all OCR chunks for the project
        """
        all_results = []
        offset = None
        batch_size = 100

        # Build filter for project_id
        search_filter = Filter(
            must=[FieldCondition(key="project_id", match=MatchValue(value=project_id))]
        )

        # Scroll through all results in batches
        while True:
            results, next_offset = await self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=search_filter,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )

            # Convert and accumulate results
            all_results.extend([
                OCRChunkResponse(
                    point_id=str(result.id),
                    payload=OCRChunkPayload(**result.payload)
                )
                for result in results
            ])

            # Check if we've reached the end
            if next_offset is None or len(results) == 0:
                break

            offset = next_offset

        return all_results

    async def vector_search_with_filter(
        self,
        query_text: str,
        limit: int = 10,
        score_threshold: Optional[float] = None,
        custom_filter: Optional[Filter] = None
    ) -> list[OCRChunkResponse]:
        """
        Vector similarity search with custom filter support

        Provides more flexible filtering compared to vector_search(),
        allowing complex filter combinations for hybrid search scenarios.

        Args:
            query_text: Query text
            limit: Maximum results
            score_threshold: Minimum score threshold
            custom_filter: Custom Filter object with any combination of conditions

        Returns:
            List of search results
        """
        # Generate query embedding
        query_vector = await generate_query_dense_embedding(query_text)

        # Search with custom filter
        results = await self.client.search(
            collection_name=self.collection_name,
            query_vector=(settings.dense_vector_name, query_vector),
            limit=limit,
            score_threshold=score_threshold,
            query_filter=custom_filter,
            with_payload=True,
            with_vectors=False
        )

        # Convert to response
        return [
            OCRChunkResponse(
                point_id=str(result.id),
                payload=OCRChunkPayload(**result.payload),
                score=result.score
            )
            for result in results
        ]


    # === New Search Methods ===

    async def dense_search(
        self,
        query_text: str,
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_project_id: Optional[int] = None,
        filter_file_id: Optional[int] = None
    ) -> list[OCRChunkResponse]:
        """
        Dense vector search using Gemini embeddings

        Args:
            query_text: Query text to search
            limit: Maximum number of results
            score_threshold: Minimum score threshold
            filter_project_id: Filter by project ID
            filter_file_id: Filter by file ID

        Returns:
            List of search results with scores
        """
        # Generate dense query embedding
        query_vector = await generate_query_dense_embedding(query_text)

        # Build filter
        filter_conditions = []
        if filter_project_id is not None:
            filter_conditions.append(
                FieldCondition(key="project_id", match=MatchValue(value=filter_project_id))
            )
        if filter_file_id is not None:
            filter_conditions.append(
                FieldCondition(key="file_id", match=MatchValue(value=filter_file_id))
            )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Dense vector search
        results = await self.client.search(
            collection_name=self.collection_name,
            query_vector=(settings.dense_vector_name, query_vector),
            limit=limit,
            score_threshold=score_threshold,
            query_filter=search_filter,
            with_payload=True,
            with_vectors=False
        )

        # Convert to response
        return [
            OCRChunkResponse(
                point_id=str(result.id),
                payload=OCRChunkPayload(**result.payload),
                score=result.score
            )
            for result in results
        ]

    async def sparse_search(
        self,
        query_text: str,
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_project_id: Optional[int] = None,
        filter_file_id: Optional[int] = None
    ) -> list[OCRChunkResponse]:
        """
        Sparse vector search using Kiwi (Korean) or FastEmbed BM25

        Args:
            query_text: Query text to search
            limit: Maximum number of results
            score_threshold: Minimum score threshold
            filter_project_id: Filter by project ID
            filter_file_id: Filter by file ID

        Returns:
            List of search results with scores
        """
        # Generate sparse query embedding
        sparse_embedding_dict = await generate_query_sparse_embedding(query_text)

        # Convert to SparseVector format
        sparse_indices = list(sparse_embedding_dict.keys())
        sparse_values = list(sparse_embedding_dict.values())

        # Build filter
        filter_conditions = []
        if filter_project_id is not None:
            filter_conditions.append(
                FieldCondition(key="project_id", match=MatchValue(value=filter_project_id))
            )
        if filter_file_id is not None:
            filter_conditions.append(
                FieldCondition(key="file_id", match=MatchValue(value=filter_file_id))
            )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Sparse vector search
        results = await self.client.search(
            collection_name=self.collection_name,
            query_vector=(
                settings.sparse_vector_name,
                SparseVector(indices=sparse_indices, values=sparse_values)
            ),
            limit=limit,
            score_threshold=score_threshold,
            query_filter=search_filter,
            with_payload=True,
            with_vectors=False
        )

        # Convert to response
        return [
            OCRChunkResponse(
                point_id=str(result.id),
                payload=OCRChunkPayload(**result.payload),
                score=result.score
            )
            for result in results
        ]

    async def matchtext_search(
        self,
        query_text: str,
        limit: int = 10,
        filter_project_id: Optional[int] = None,
        filter_file_id: Optional[int] = None
    ) -> list[OCRChunkResponse]:
        """
        Full-text search using MatchText (no morphological analysis)

        Args:
            query_text: Query text to match
            limit: Maximum number of results
            filter_project_id: Filter by project ID
            filter_file_id: Filter by file ID

        Returns:
            List of search results (no scores for MatchText)
        """
        # Build filter with MatchText
        filter_conditions = []

        filter_conditions.append(
            FieldCondition(key="paragraph_texts", match=MatchText(text=query_text))
        )

        if filter_project_id is not None:
            filter_conditions.append(
                FieldCondition(key="project_id", match=MatchValue(value=filter_project_id))
            )
        if filter_file_id is not None:
            filter_conditions.append(
                FieldCondition(key="file_id", match=MatchValue(value=filter_file_id))
            )

        search_filter = Filter(must=filter_conditions)

        # Scroll with MatchText filter
        results, _ = await self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=search_filter,
            limit=limit,
            with_payload=True,
            with_vectors=False
        )

        # Convert to response
        return [
            OCRChunkResponse(
                point_id=str(result.id),
                payload=OCRChunkPayload(**result.payload)
            )
            for result in results
        ]

    async def dense_sparse_rrf_search(
        self,
        query_text: str,
        limit: int = 10,
        score_threshold: Optional[float] = None,
        rrf_k: int = 60,
        filter_project_id: Optional[int] = None,
        filter_file_id: Optional[int] = None
    ) -> list[OCRChunkResponse]:
        """
        Hybrid search combining dense + sparse using Reciprocal Rank Fusion

        Args:
            query_text: Query text to search
            limit: Maximum number of results
            score_threshold: Minimum score threshold
            rrf_k: RRF constant k (default: 60)
            filter_project_id: Filter by project ID
            filter_file_id: Filter by file ID

        Returns:
            List of search results with RRF scores
        """
        from app.services.rrf_fusion import reciprocal_rank_fusion

        # Run dense and sparse searches in parallel
        dense_task = self.dense_search(
            query_text=query_text,
            limit=limit * 2,  # Get more results for better fusion
            score_threshold=score_threshold,
            filter_project_id=filter_project_id,
            filter_file_id=filter_file_id
        )

        sparse_task = self.sparse_search(
            query_text=query_text,
            limit=limit * 2,
            score_threshold=score_threshold,
            filter_project_id=filter_project_id,
            filter_file_id=filter_file_id
        )

        dense_results, sparse_results = await asyncio.gather(dense_task, sparse_task)

        # Apply RRF fusion
        fused_results = reciprocal_rank_fusion(
            dense_results=dense_results,
            sparse_results=sparse_results,
            k=rrf_k,
            id_key="point_id"
        )

        # Take top results and convert to OCRChunkResponse with RRF score
        return [
            OCRChunkResponse(
                point_id=result.point_id,
                payload=result.payload,
                score=rrf_score
            )
            for result, rrf_score in fused_results[:limit]
        ]

    async def recommend_search(
        self,
        positive_ids: list[str],
        negative_ids: list[str],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        strategy: str = "average_vector",
        filter_project_id: Optional[int] = None,
        filter_file_id: Optional[int] = None
    ) -> list[OCRChunkResponse]:
        """
        Recommendation search using positive and negative examples

        Args:
            positive_ids: List of positive example point IDs
            negative_ids: List of negative example point IDs
            limit: Maximum number of results
            score_threshold: Minimum score threshold
            strategy: Recommendation strategy ('average_vector' or 'best_score')
            filter_project_id: Filter by project ID
            filter_file_id: Filter by file ID

        Returns:
            List of recommended results with scores
        """
        # Build filter
        filter_conditions = []
        if filter_project_id is not None:
            filter_conditions.append(
                FieldCondition(key="project_id", match=MatchValue(value=filter_project_id))
            )
        if filter_file_id is not None:
            filter_conditions.append(
                FieldCondition(key="file_id", match=MatchValue(value=filter_file_id))
            )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Recommendation search
        results = await self.client.recommend(
            collection_name=self.collection_name,
            positive=positive_ids,
            negative=negative_ids,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=search_filter,
            using=settings.dense_vector_name,
            strategy=strategy,
            with_payload=True,
            with_vectors=False
        )

        # Convert to response
        return [
            OCRChunkResponse(
                point_id=str(result.id),
                payload=OCRChunkPayload(**result.payload),
                score=result.score
            )
            for result in results
        ]

    async def discover_search(
        self,
        target_text: str,
        context_pairs: list[tuple[str, str]],
        limit: int = 10,
        filter_project_id: Optional[int] = None,
        filter_file_id: Optional[int] = None
    ) -> list[OCRChunkResponse]:
        """
        Discovery search using context pairs to explore vector space

        Args:
            target_text: Target text to discover similar items
            context_pairs: List of (positive_id, negative_id) tuples
            limit: Maximum number of results
            filter_project_id: Filter by project ID
            filter_file_id: Filter by file ID

        Returns:
            List of discovered results with scores
        """
        from qdrant_client.models import ContextExamplePair

        # Generate target embedding
        target_vector = await generate_query_dense_embedding(target_text)

        # Build context pairs
        context = [
            ContextExamplePair(positive=pos_id, negative=neg_id)
            for pos_id, neg_id in context_pairs
        ]

        # Build filter
        filter_conditions = []
        if filter_project_id is not None:
            filter_conditions.append(
                FieldCondition(key="project_id", match=MatchValue(value=filter_project_id))
            )
        if filter_file_id is not None:
            filter_conditions.append(
                FieldCondition(key="file_id", match=MatchValue(value=filter_file_id))
            )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Discovery search
        results = await self.client.discover(
            collection_name=self.collection_name,
            target=(settings.dense_vector_name, target_vector),
            context=context,
            limit=limit,
            query_filter=search_filter,
            with_payload=True,
            with_vectors=False
        )

        # Convert to response
        return [
            OCRChunkResponse(
                point_id=str(result.id),
                payload=OCRChunkPayload(**result.payload),
                score=result.score
            )
            for result in results
        ]

    async def scroll_search(
        self,
        limit: int = 100,
        offset: Optional[str] = None,
        filter_project_id: Optional[int] = None,
        filter_file_id: Optional[int] = None,
        filter_language: Optional[str] = None,
        filter_pages: Optional[list[int]] = None
    ) -> tuple[list[OCRChunkResponse], Optional[str]]:
        """
        Scroll search for paginated large result sets

        Args:
            limit: Number of results per page
            offset: Pagination offset from previous response
            filter_project_id: Filter by project ID
            filter_file_id: Filter by file ID
            filter_language: Filter by language
            filter_pages: Filter by page numbers

        Returns:
            Tuple of (results, next_offset)
        """
        filter_conditions = []

        if filter_project_id is not None:
            filter_conditions.append(
                FieldCondition(key="project_id", match=MatchValue(value=filter_project_id))
            )
        if filter_file_id is not None:
            filter_conditions.append(
                FieldCondition(key="file_id", match=MatchValue(value=filter_file_id))
            )
        if filter_language is not None:
            filter_conditions.append(
                FieldCondition(key="language", match=MatchValue(value=filter_language))
            )
        if filter_pages is not None and len(filter_pages) > 0:
            for page in filter_pages:
                filter_conditions.append(
                    FieldCondition(key="pages", match=MatchValue(value=page))
                )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Scroll
        results, next_offset = await self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=search_filter,
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )

        # Convert to response
        responses = [
            OCRChunkResponse(
                point_id=str(result.id),
                payload=OCRChunkPayload(**result.payload)
            )
            for result in results
        ]

        return responses, next_offset


# Global service instances
qdrant_service = QdrantService(collection_name="ocr_chunks")
qdrant_summaries_service = QdrantService(collection_name="ocr_summaries")
