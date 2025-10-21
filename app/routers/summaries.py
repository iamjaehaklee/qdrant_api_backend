"""
Summaries Router
CRUD and search endpoints for OCR summaries
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from qdrant_client import AsyncQdrantClient

logger = logging.getLogger(__name__)
from qdrant_client.models import (
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    MatchText,
    SparseVector
)

from app.config import settings
from app.models import (
    SummaryCreate,
    SummaryUpdate,
    SummaryResponse,
    SummaryPayload,
    SummaryVectorSearchRequest,
    SummaryKeywordSearchRequest,
    SummaryHybridSearchRequest,
    SummarySearchResponse
)
from app.embeddings import (
    generate_dense_embedding,
    generate_sparse_embedding,
    generate_query_dense_embedding
)

router = APIRouter(prefix="/summaries", tags=["Summaries"])

# Create Qdrant client for ocr_summaries collection
qdrant_client = AsyncQdrantClient(
    url=settings.qdrant_url,
    api_key=settings.qdrant_master_api_key,
    timeout=30.0
)
COLLECTION_NAME = "ocr_summaries"


def _validate_or_generate_uuid(summary_id: Optional[str]) -> str:
    """Validate or generate UUID for summary"""
    if summary_id:
        try:
            uuid.UUID(summary_id)
            return summary_id
        except (ValueError, AttributeError):
            pass
    return str(uuid.uuid4())


@router.post("", response_model=SummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_summary(summary: SummaryCreate):
    """
    Create a new summary with automatic embedding generation

    Embeddings are generated from summary_text field
    """
    try:
        # Auto-generate tracing fields if not provided
        if summary.correlation_id is None:
            summary.correlation_id = str(uuid.uuid4())
        if summary.request_timestamp is None:
            summary.request_timestamp = datetime.now(timezone.utc).isoformat()

        logger.info(
            f"Create summary request: correlation_id={summary.correlation_id}, "
            f"file_id={summary.file_id}, project_id={summary.project_id}, "
            f"user_id={summary.user_id}, queue_id={summary.queue_id}, "
            f"original_file_name={summary.original_file_name}, "
            f"request_timestamp={summary.request_timestamp}"
        )

        # Generate summary_id
        point_id = _validate_or_generate_uuid(summary.summary_id)

        # Generate embeddings from summary_text
        dense_vector = await generate_dense_embedding(summary.summary_text)
        sparse_vector_dict = await generate_sparse_embedding(summary.summary_text)

        # Convert sparse vector dict to SparseVector format with explicit type conversion
        sparse_indices = [int(k) for k in sparse_vector_dict.keys()]
        sparse_values = [float(v) for v in sparse_vector_dict.values()]

        # Prepare payload
        payload = SummaryPayload(
            summary_id=point_id,
            **summary.model_dump(exclude={"summary_id"})
        ).model_dump()

        # Create point
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
        await qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=[point]
        )

        return SummaryResponse(
            point_id=point_id,
            payload=SummaryPayload(**payload)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create summary: {str(e)}"
        )


@router.get("/{summary_id}", response_model=SummaryResponse)
async def get_summary(summary_id: str):
    """Retrieve a summary by ID"""
    try:
        points = await qdrant_client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[summary_id],
            with_payload=True,
            with_vectors=False
        )

        if not points:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Summary {summary_id} not found"
            )

        return SummaryResponse(
            point_id=str(points[0].id),
            payload=SummaryPayload(**points[0].payload)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve summary: {str(e)}"
        )


@router.put("/{summary_id}", response_model=SummaryResponse)
async def update_summary(summary_id: str, update: SummaryUpdate):
    """Update a summary's payload and regenerate embeddings if summary_text changes"""
    try:
        # Get existing summary
        existing = await qdrant_client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[summary_id],
            with_payload=True,
            with_vectors=False
        )

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Summary {summary_id} not found"
            )

        # Merge updates
        update_dict = update.model_dump(exclude_unset=True)

        # If summary_text updated, regenerate embeddings and upsert entire point
        if "summary_text" in update_dict:
            dense_vector = await generate_dense_embedding(update_dict["summary_text"])
            sparse_vector_dict = await generate_sparse_embedding(update_dict["summary_text"])

            # Convert sparse vector dict to SparseVector format
            sparse_indices = list(sparse_vector_dict.keys())
            sparse_values = list(sparse_vector_dict.values())

            # Merge existing payload with updates
            updated_payload = {**existing[0].payload, **update_dict}

            # Upsert entire point with new vectors and updated payload
            await qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    PointStruct(
                        id=summary_id,
                        vector={
                            settings.dense_vector_name: dense_vector,
                            settings.sparse_vector_name: SparseVector(
                                indices=sparse_indices,
                                values=sparse_values
                            )
                        },
                        payload=updated_payload
                    )
                ]
            )
        else:
            # Update payload only
            await qdrant_client.set_payload(
                collection_name=COLLECTION_NAME,
                payload=update_dict,
                points=[summary_id]
            )

        # Retrieve updated summary
        updated_points = await qdrant_client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[summary_id],
            with_payload=True,
            with_vectors=False
        )

        return SummaryResponse(
            point_id=str(updated_points[0].id),
            payload=SummaryPayload(**updated_points[0].payload)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update summary: {str(e)}"
        )


@router.delete("/{summary_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_summary(summary_id: str):
    """Delete a summary"""
    try:
        await qdrant_client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=[summary_id]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete summary: {str(e)}"
        )
