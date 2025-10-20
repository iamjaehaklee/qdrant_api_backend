"""
Points Router
CRUD endpoints for OCR chunk points
"""

from fastapi import APIRouter, HTTPException, status

from app.models import (
    OCRChunkCreate,
    OCRChunkUpdate,
    OCRChunkResponse,
    BatchCreateRequest,
    BatchDeleteRequest,
    ProjectChunksResponse
)
from app.qdrant_service import qdrant_service

router = APIRouter(prefix="/points", tags=["Points"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_point(chunk: OCRChunkCreate):
    """
    Create a single OCR chunk point

    Automatically generates embeddings from paragraph_texts
    """
    try:
        point_id = await qdrant_service.create_point(chunk)
        return {
            "message": "Point created successfully",
            "point_id": point_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create point: {str(e)}"
        )


@router.post("/batch", response_model=dict, status_code=status.HTTP_201_CREATED)
async def batch_create_points(request: BatchCreateRequest):
    """
    Create multiple OCR chunk points in batch

    Automatically generates embeddings for all chunks
    """
    try:
        point_ids = await qdrant_service.batch_create_points(request.chunks)
        return {
            "message": f"Created {len(point_ids)} points successfully",
            "point_ids": point_ids,
            "count": len(point_ids)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create points: {str(e)}"
        )


@router.get("/{point_id}", response_model=OCRChunkResponse)
async def get_point(point_id: str):
    """
    Retrieve an OCR chunk point by ID
    """
    try:
        result = await qdrant_service.get_point(point_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Point {point_id} not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve point: {str(e)}"
        )


@router.put("/{point_id}", response_model=dict)
async def update_point(point_id: str, update: OCRChunkUpdate):
    """
    Update an OCR chunk point

    If paragraph_texts is updated, embeddings will be regenerated
    """
    try:
        success = await qdrant_service.update_point(point_id, update)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Point {point_id} not found"
            )
        return {
            "message": "Point updated successfully",
            "point_id": point_id
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update point: {str(e)}"
        )


@router.delete("/{point_id}", response_model=dict)
async def delete_point(point_id: str):
    """
    Delete an OCR chunk point by ID
    """
    try:
        success = await qdrant_service.delete_point(point_id)
        return {
            "message": "Point deleted successfully",
            "point_id": point_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete point: {str(e)}"
        )


@router.delete("/batch/delete", response_model=dict)
async def batch_delete_points(request: BatchDeleteRequest):
    """
    Delete multiple OCR chunk points in batch
    """
    try:
        success = await qdrant_service.batch_delete_points(request.point_ids)
        return {
            "message": f"Deleted {len(request.point_ids)} points successfully",
            "count": len(request.point_ids)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete points: {str(e)}"
        )


@router.get("/project/{project_id}", response_model=ProjectChunksResponse)
async def get_all_chunks_by_project(project_id: int):
    """
    Retrieve all OCR chunks for a given project ID

    Returns all chunks without pagination limit
    """
    try:
        chunks = await qdrant_service.get_all_by_project_id(project_id)
        return ProjectChunksResponse(
            project_id=project_id,
            total_count=len(chunks),
            chunks=chunks
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chunks for project {project_id}: {str(e)}"
        )
