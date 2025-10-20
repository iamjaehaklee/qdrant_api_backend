"""
Document AI OCR Router
API endpoints for processing Google Document AI OCR results
"""

from fastapi import APIRouter, HTTPException, status

from app.models_documentai import (
    DocumentAIStoreChunksRequest,
    DocumentAIStoreChunksResponse
)
from app.services.documentai_ocr_processor import DocumentAIOCRProcessor
from app.qdrant_service import qdrant_service


router = APIRouter(
    prefix="/api/documentai-ocr",
    tags=["Document AI OCR"]
)


@router.post(
    "/store-chunks",
    response_model=DocumentAIStoreChunksResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store Document AI OCR Results as Qdrant Chunks",
    description="""
    Process Google Document AI OCR results and store them as chunks in Qdrant.

    **Process:**
    1. Extracts paragraphs from Document AI pages
    2. Creates 3-page sliding windows (with 1-page overlap)
    3. Generates dense and sparse embeddings for each chunk
    4. Stores chunks in Qdrant ocr_chunks collection

    **Window Strategy:**
    - For a 14-page document: [1-3], [3-5], [5-7], [7-9], [9-11], [11-13], [13-14]
    - 1-page overlap ensures context continuity across chunks

    **Embedding Generation:**
    - Dense vectors: Gemini embedding-001 (1536 dimensions)
    - Sparse vectors: TF-IDF-based token frequency
    """
)
async def store_documentai_ocr_chunks(
    request: DocumentAIStoreChunksRequest
) -> DocumentAIStoreChunksResponse:
    """
    Store Google Document AI OCR results as Qdrant chunks

    Args:
        request: Document AI result and file metadata

    Returns:
        Response with created chunk IDs and processing summary

    Raises:
        HTTPException: If processing or storage fails
    """
    try:
        # Initialize processor with existing Qdrant service
        processor = DocumentAIOCRProcessor(qdrant_service=qdrant_service)

        # Process and store
        response = await processor.process_and_store(
            document_ai_result=request.document_ai_result,
            file_metadata=request.file_metadata
        )

        return response

    except ValueError as e:
        # Validation or processing error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Processing error: {str(e)}"
        )
    except Exception as e:
        # Unexpected error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process Document AI result: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health Check for Document AI OCR Service",
    description="Check if the Document AI OCR processing service is operational"
)
async def health_check():
    """
    Health check endpoint for Document AI OCR service

    Returns:
        Service status and Qdrant connection info
    """
    try:
        # Check Qdrant connection
        health = await qdrant_service.check_health()

        return {
            "status": "healthy" if health["connected"] else "unhealthy",
            "service": "Document AI OCR Processor",
            "qdrant_connected": health["connected"],
            "collection_exists": health.get("collection_exists", False)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "Document AI OCR Processor",
            "error": str(e)
        }
