"""
Document AI OCR Processor
Main processor for converting Document AI OCR results into Qdrant chunks
"""

import time
from typing import List, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4

from app.models_documentai import (
    DocumentAIResult,
    FileMetadata,
    DocumentAIStoreChunksResponse,
    ProcessingSummary
)
from app.models import OCRChunkCreate, ChunkContent, Paragraph, BBox, PageDimension
from app.qdrant_service import QdrantService
from app.services.documentai_transformer import DocumentAITransformer
from app.services.ocr_window_generator import OCRWindowGenerator


class DocumentAIOCRProcessor:
    """
    Processes Google Document AI OCR results and stores them in Qdrant

    Flow:
    1. Extract paragraphs from Document AI result (page-by-page)
    2. Create 3-page sliding windows (with 1-page overlap)
    3. Generate OCRChunkCreate objects for each window
    4. Use existing QdrantService to batch upload (handles embeddings automatically)
    """

    def __init__(self, qdrant_service: QdrantService = None):
        """
        Initialize processor

        Args:
            qdrant_service: Optional QdrantService instance (creates new if not provided)
        """
        self.qdrant_service = qdrant_service or QdrantService()
        self.transformer = DocumentAITransformer()
        self.window_generator = OCRWindowGenerator()

    async def process_and_store(
        self,
        document_ai_result: DocumentAIResult,
        file_metadata: FileMetadata
    ) -> DocumentAIStoreChunksResponse:
        """
        Process Document AI OCR result and store as Qdrant chunks

        Args:
            document_ai_result: Google Document AI OCR result
            file_metadata: File metadata

        Returns:
            Response with chunk IDs and processing summary
        """
        start_time = time.time()

        # Step 1: Extract paragraphs from all pages
        print(f"📄 Processing Document AI result for: {file_metadata.original_file_name}")
        print(f"   Total pages: {file_metadata.total_pages}")

        paragraphs_by_page = self.transformer.extract_all_paragraphs(
            document_ai_result
        )

        total_paragraphs = sum(len(paragraphs) for paragraphs in paragraphs_by_page.values())
        print(f"   ✅ Extracted {total_paragraphs} paragraphs from {len(paragraphs_by_page)} pages")

        # Step 2: Detect language
        language = self.transformer.detect_language(
            paragraphs_by_page,
            document_ai_result
        )
        print(f"   🌐 Detected language: {language}")

        # Step 3: Create 3-page windows
        windows = self.window_generator.create_windows(file_metadata.total_pages)
        print(f"   📑 Created {len(windows)} windows (3-page sliding with 1-page overlap)")

        # Step 4: Create OCRChunkCreate objects for each window
        chunk_creates = []
        for chunk_number, window_pages in enumerate(windows, 1):
            chunk_create = self._create_chunk_for_window(
                window_pages=window_pages,
                chunk_number=chunk_number,
                paragraphs_by_page=paragraphs_by_page,
                file_metadata=file_metadata,
                language=language
            )
            chunk_creates.append(chunk_create)

        print(f"   ✅ Prepared {len(chunk_creates)} chunks for storage")

        # Step 5: Store to Qdrant using existing service
        # QdrantService will handle:
        # - Dense embedding generation (Gemini API - optimized with batch API)
        # - Sparse embedding generation (parallel processing)
        # - Batch upsert to Qdrant
        print(f"   💾 Storing chunks to Qdrant...")
        chunk_ids = await self.qdrant_service.batch_create_points(chunk_creates)

        processing_time = time.time() - start_time
        print(f"   ✅ Successfully stored {len(chunk_ids)} chunks in {processing_time:.2f}s")

        # Create response
        return DocumentAIStoreChunksResponse(
            success=True,
            chunk_ids=chunk_ids,
            total_chunks=len(chunk_ids),
            processing_time=processing_time,
            summary=ProcessingSummary(
                total_pages=file_metadata.total_pages,
                total_paragraphs=total_paragraphs,
                total_windows=len(windows),
                language=language
            )
        )

    def _create_chunk_for_window(
        self,
        window_pages: List[int],
        chunk_number: int,
        paragraphs_by_page: Dict[int, List[Dict]],
        file_metadata: FileMetadata,
        language: str
    ) -> OCRChunkCreate:
        """
        Create OCRChunkCreate object for a single window

        Args:
            window_pages: List of page numbers in this window (e.g., [1, 2, 3])
            chunk_number: Sequential chunk number
            paragraphs_by_page: Dict mapping page_num -> list of paragraph dicts
            file_metadata: File metadata
            language: Detected language code

        Returns:
            OCRChunkCreate object ready for Qdrant storage
        """
        # Collect all paragraphs for this window
        window_paragraphs = []
        for page_num in window_pages:
            if page_num in paragraphs_by_page:
                window_paragraphs.extend(paragraphs_by_page[page_num])

        # Extract paragraph texts for embedding generation
        paragraph_texts = [p["text"] for p in window_paragraphs]

        # Convert paragraphs to Pydantic models
        chunk_content_paragraphs = []
        for p in window_paragraphs:
            paragraph = Paragraph(
                paragraph_id=p["paragraph_id"],
                idx_in_page=p["idx_in_page"],
                text=p["text"],
                page=p["page"],
                bbox=BBox(**p["bbox"]),
                type=p["type"],
                confidence_score=p["confidence_score"]
            )
            chunk_content_paragraphs.append(paragraph)

        # Create ChunkContent
        chunk_content = ChunkContent(paragraphs=chunk_content_paragraphs)

        # Collect page dimensions
        page_dimensions = []
        for page_num in window_pages:
            if page_num in paragraphs_by_page and paragraphs_by_page[page_num]:
                # Get dimensions from first paragraph of page
                first_para = paragraphs_by_page[page_num][0]
                page_dim = PageDimension(
                    page=page_num,
                    width=int(first_para.get("page_width", 595)),
                    height=int(first_para.get("page_height", 842))
                )
            else:
                # Default dimensions if no paragraphs
                page_dim = PageDimension(
                    page=page_num,
                    width=595,
                    height=842
                )
            page_dimensions.append(page_dim)

        # Create OCRChunkCreate
        return OCRChunkCreate(
            chunk_id=str(uuid4()),
            file_id=file_metadata.file_id,
            project_id=file_metadata.project_id,
            storage_file_name=file_metadata.storage_file_name,
            original_file_name=file_metadata.original_file_name,
            mime_type=file_metadata.mime_type,
            total_pages=file_metadata.total_pages,
            processing_duration_seconds=0,  # Will be set by API
            language=language,
            pages=window_pages,
            chunk_number=chunk_number,
            paragraph_texts=paragraph_texts,
            chunk_content=chunk_content,
            page_dimensions=page_dimensions
        )
