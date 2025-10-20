"""
Document AI Transformer
Transforms Google Document AI OCR results into Qdrant-compatible format
"""

from typing import List, Dict, Any
from uuid import uuid4

from app.models_documentai import DocumentAIResult, DocumentAIPage


class DocumentAITransformer:
    """
    Transforms Google Document AI OCR results into paragraph structures
    suitable for Qdrant storage
    """

    def extract_all_paragraphs(
        self,
        doc_result: DocumentAIResult
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Extract paragraphs from all pages in Document AI result

        Args:
            doc_result: Document AI OCR result

        Returns:
            Dictionary mapping page_number -> list of paragraph dicts

        Example paragraph dict:
            {
                "paragraph_id": "uuid",
                "idx_in_page": 0,
                "text": "paragraph text",
                "page": 1,
                "bbox": {"x": 36.0, "y": 50.9, "width": 1357.0, "height": 28.9},
                "type": "body",
                "confidence_score": 0.95,
                "page_width": 1681,
                "page_height": 2379
            }
        """
        paragraphs_by_page = {}

        for page in doc_result.pages:
            page_num = page.pageNumber
            page_width = page.dimension["width"]
            page_height = page.dimension["height"]

            paragraphs = []

            for idx, block in enumerate(page.blocks):
                # Extract text from block using textAnchor
                text = self._extract_text_from_block(
                    block.layout,
                    doc_result.text
                )

                # Skip empty blocks
                if not text.strip():
                    continue

                # Extract bounding box
                bbox = self._extract_bbox_from_layout(
                    block.layout,
                    page_width,
                    page_height
                )

                # Extract confidence score
                confidence = block.layout.get("confidence", 0.95)

                # Create paragraph dict
                paragraph = {
                    "paragraph_id": str(uuid4()),
                    "idx_in_page": idx,
                    "text": text,
                    "page": page_num,
                    "bbox": bbox,
                    "type": "body",  # Document AI doesn't classify types, default to body
                    "confidence_score": confidence,
                    "page_width": page_width,
                    "page_height": page_height
                }

                paragraphs.append(paragraph)

            paragraphs_by_page[page_num] = paragraphs

        return paragraphs_by_page

    def _extract_text_from_block(
        self,
        layout: Dict[str, Any],
        document_text: str
    ) -> str:
        """
        Extract text from Document AI block using textAnchor

        Args:
            layout: Block layout containing textAnchor
            document_text: Full document text

        Returns:
            Extracted text string
        """
        text_anchor = layout.get("textAnchor", {})
        text_segments = text_anchor.get("textSegments", [])

        if not text_segments:
            return ""

        # Concatenate all text segments
        texts = []
        for segment in text_segments:
            start_idx = segment.get("startIndex", 0)
            end_idx = segment.get("endIndex", 0)

            # Extract text slice
            if end_idx > start_idx:
                texts.append(document_text[start_idx:end_idx])

        return "".join(texts).strip()

    def _extract_bbox_from_layout(
        self,
        layout: Dict[str, Any],
        page_width: float,
        page_height: float
    ) -> Dict[str, float]:
        """
        Extract and convert bounding box from Document AI layout

        Document AI uses normalized coordinates (0-1 range).
        This method converts them to pixel coordinates.

        Args:
            layout: Block layout containing boundingPoly
            page_width: Page width in pixels
            page_height: Page height in pixels

        Returns:
            Bounding box dict with pixel coordinates:
            {"x": float, "y": float, "width": float, "height": float}
        """
        # Get bounding poly
        bounding_poly = layout.get("boundingPoly", {})
        normalized_vertices = bounding_poly.get("normalizedVertices", [])

        # Fallback bbox if no vertices
        if not normalized_vertices or len(normalized_vertices) < 4:
            return {
                "x": 0.0,
                "y": 0.0,
                "width": 100.0,
                "height": 20.0
            }

        # Extract min/max coordinates
        x_coords = [v.get("x", 0.0) for v in normalized_vertices]
        y_coords = [v.get("y", 0.0) for v in normalized_vertices]

        min_x = min(x_coords)
        max_x = max(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)

        # Convert normalized (0-1) to pixel coordinates
        return {
            "x": round(min_x * page_width, 1),
            "y": round(min_y * page_height, 1),
            "width": round((max_x - min_x) * page_width, 1),
            "height": round((max_y - min_y) * page_height, 1)
        }

    def detect_language(
        self,
        paragraphs_by_page: Dict[int, List[Dict]],
        doc_result: DocumentAIResult = None
    ) -> str:
        """
        Detect primary language from paragraphs or Document AI result

        Args:
            paragraphs_by_page: Extracted paragraphs
            doc_result: Optional Document AI result for language detection

        Returns:
            ISO 639-1 language code (e.g., "ko", "en")
        """
        # Try to detect from Document AI detected_languages
        if doc_result:
            language_counts = {}

            for page in doc_result.pages:
                if page.detected_languages:
                    for lang_info in page.detected_languages:
                        lang_code = lang_info.get("languageCode", "ko")
                        confidence = lang_info.get("confidence", 1.0)

                        if lang_code not in language_counts:
                            language_counts[lang_code] = 0
                        language_counts[lang_code] += confidence

            if language_counts:
                # Return language with highest confidence
                return max(language_counts, key=language_counts.get)

        # Default to Korean
        return "ko"
