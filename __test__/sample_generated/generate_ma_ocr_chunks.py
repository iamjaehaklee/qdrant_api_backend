#!/usr/bin/env python3
"""
Generate OCR chunk JSON files from summary files for M&A legal advisory case.
Creates 3-page window chunks with 1-page overlap.
"""

import json
import uuid
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Base directories
BASE_DIR = Path(__file__).parent / "기업인수합병_법률자문"
SUMMARIES_DIR = BASE_DIR / "ocr_summaries"
CHUNKS_DIR = BASE_DIR / "ocr_chunks"

# Project configuration
PROJECT_ID = 5001
BASE_FILE_ID = 1

# Page dimensions (standard A4 in pixels at 150 DPI)
PAGE_WIDTH = 1681
PAGE_HEIGHT = 2379


def generate_paragraph_id() -> str:
    """Generate UUID for paragraph."""
    return str(uuid.uuid4())


def generate_chunk_id() -> str:
    """Generate UUID for chunk."""
    return str(uuid.uuid4())


def create_bbox(page_num: int, idx_in_page: int, text_length: int) -> Dict[str, float]:
    """Generate realistic bounding box coordinates."""
    # Header area for first paragraph
    if idx_in_page == 0:
        return {
            "x": 36.0,
            "y": 51.0,
            "width": 1357.0,
            "height": 29.0
        }

    # Calculate vertical position based on index
    base_y = 100.0 + (idx_in_page * 150.0)
    # Vary height based on text length (roughly)
    height = min(max(50.0, text_length / 3.0), 800.0)

    return {
        "x": 189.0 + random.uniform(-10, 10),
        "y": base_y + random.uniform(-20, 20),
        "width": 1302.0 + random.uniform(-50, 50),
        "height": height
    }


def generate_paragraph_content(summary_text: str, doc_name: str, page: int, idx: int, total_in_page: int) -> str:
    """Generate realistic Korean legal document paragraph content."""

    # Header paragraph (always on page 1, idx 0)
    if page == 1 and idx == 0:
        return f"[문서번호: MA-2024-{random.randint(1000, 9999)}] {doc_name}"

    # Extract key phrases from summary
    summary_sentences = summary_text.split(". ")

    # Select content type based on index
    content_types = [
        "정의조항",
        "당사자정보",
        "거래조건",
        "진술보증",
        "계약해제사유",
        "손해배상",
        "일반조항",
        "법적근거",
        "부칙"
    ]

    content_type = content_types[idx % len(content_types)]

    # Generate paragraph based on type and summary
    if content_type == "정의조항":
        return f"본 계약에서 사용하는 용어의 정의는 다음과 같다. {random.choice(summary_sentences)}"
    elif content_type == "당사자정보":
        return f"제{idx}조 (당사자) {random.choice(summary_sentences)} 양 당사자는 본 계약에 정한 권리와 의무를 성실히 이행한다."
    elif content_type == "거래조건":
        return f"제{idx}조 (거래조건) {random.choice(summary_sentences)} 본 거래의 세부 조건은 별첨 자료에 명시된 바와 같다."
    elif content_type == "진술보증":
        return f"제{idx}조 (진술 및 보증) {random.choice(summary_sentences)} 각 당사자는 상기 진술 및 보증이 진실하고 정확함을 확인한다."
    elif content_type == "계약해제사유":
        return f"제{idx}조 (계약의 해제) 다음 각 호의 사유가 발생한 경우 상대방은 본 계약을 해제할 수 있다. {random.choice(summary_sentences)}"
    elif content_type == "손해배상":
        return f"제{idx}조 (손해배상) {random.choice(summary_sentences)} 손해배상의 범위는 통상손해 및 특별손해를 포함한다."
    elif content_type == "법적근거":
        return f"본 조항은 상법 제{random.randint(100, 900)}조, 민법 제{random.randint(100, 900)}조의 규정에 따른다. {random.choice(summary_sentences)}"
    elif content_type == "부칙":
        return f"부칙 제{idx}조: {random.choice(summary_sentences)} 본 계약은 양 당사자의 서명날인으로 효력이 발생한다."
    else:
        return f"제{idx}조 (일반조항) {random.choice(summary_sentences)}"


def create_paragraph(
    paragraph_text: str,
    page: int,
    idx_in_page: int
) -> Dict[str, Any]:
    """Create a paragraph object with all required fields."""
    return {
        "paragraph_id": generate_paragraph_id(),
        "idx_in_page": idx_in_page,
        "text": paragraph_text,
        "page": page,
        "bbox": create_bbox(page, idx_in_page, len(paragraph_text)),
        "type": "body",
        "confidence_score": round(random.uniform(0.94, 0.98), 10)
    }


def create_chunk_data(
    file_id: int,
    doc_name: str,
    total_pages: int,
    pages: List[int],
    chunk_number: int,
    summary_text: str,
    created_at: str
) -> Dict[str, Any]:
    """Create a complete OCR chunk data structure."""

    # Generate paragraphs for each page
    paragraphs = []
    paragraph_texts = []

    for page_idx, page in enumerate(pages):
        # Random number of paragraphs per page (3-8)
        num_paragraphs = random.randint(3, 8)

        for idx in range(num_paragraphs):
            para_text = generate_paragraph_content(summary_text, doc_name, page, idx, num_paragraphs)
            paragraph_texts.append(para_text)
            paragraphs.append(create_paragraph(para_text, page, idx))

    # Create page dimensions
    page_dimensions = [
        {"page": page, "width": PAGE_WIDTH, "height": PAGE_HEIGHT}
        for page in pages
    ]

    # Storage filename (UUID pattern)
    storage_filename = f"{uuid.uuid4()}-{random.randint(1700000000000, 1800000000000)}.pdf"

    return {
        "chunk_id": generate_chunk_id(),
        "file_id": file_id,
        "project_id": PROJECT_ID,
        "storage_file_name": storage_filename,
        "original_file_name": f"{doc_name}.pdf",
        "mime_type": "application/pdf",
        "total_pages": total_pages,
        "processing_duration_seconds": random.randint(0, 5),
        "language": "ko",
        "pages": pages,
        "chunk_number": chunk_number,
        "paragraph_texts": paragraph_texts,
        "chunk_content": {
            "paragraphs": paragraphs
        },
        "page_dimensions": page_dimensions,
        "created_at": created_at
    }


def generate_3page_windows(total_pages: int) -> List[List[int]]:
    """
    Generate 3-page sliding windows with 1-page overlap.
    Example: 14 pages -> [1-3], [3-5], [5-7], [7-9], [9-11], [11-13], [13-14]
    """
    windows = []
    start = 1

    while start <= total_pages:
        end = min(start + 2, total_pages)  # 3 pages: start, start+1, start+2
        windows.append(list(range(start, end + 1)))

        # Move forward by 2 pages (1-page overlap)
        start += 2

    return windows


def process_summary_file(summary_path: Path, file_id: int) -> int:
    """Process a single summary file and generate chunk files."""

    # Load summary
    with open(summary_path, 'r', encoding='utf-8') as f:
        summary_data = json.load(f)

    summary_text = summary_data["summary_text"]
    doc_name = summary_path.stem  # Filename without extension
    created_at = summary_data["created_at"]

    # Random page count (5-20)
    total_pages = random.randint(5, 20)

    # Generate 3-page windows
    windows = generate_3page_windows(total_pages)

    # Create chunks
    chunks_created = 0
    for chunk_number, pages in enumerate(windows, start=1):
        chunk_data = create_chunk_data(
            file_id=file_id,
            doc_name=doc_name,
            total_pages=total_pages,
            pages=pages,
            chunk_number=chunk_number,
            summary_text=summary_text,
            created_at=created_at
        )

        # Generate filename
        page_range = f"p{pages[0]}-{pages[-1]}"
        chunk_filename = f"{doc_name}_{page_range}.json"
        chunk_path = CHUNKS_DIR / chunk_filename

        # Write chunk file
        with open(chunk_path, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, ensure_ascii=False, indent=2)

        chunks_created += 1
        print(f"  Created: {chunk_filename} (pages {pages}, chunk {chunk_number}/{len(windows)})")

    return chunks_created


def main():
    """Main function to process all summary files."""

    print(f"Starting OCR chunk generation...")
    print(f"Source: {SUMMARIES_DIR}")
    print(f"Target: {CHUNKS_DIR}")
    print()

    # Get all summary files
    summary_files = sorted(SUMMARIES_DIR.glob("*.json"))

    print(f"Found {len(summary_files)} summary files")
    print()

    # Process each summary file
    total_chunks = 0
    file_id = BASE_FILE_ID

    for idx, summary_path in enumerate(summary_files, start=1):
        print(f"[{idx}/{len(summary_files)}] Processing: {summary_path.name}")
        chunks_created = process_summary_file(summary_path, file_id)
        total_chunks += chunks_created
        file_id += 1
        print()

    print(f"✓ Generation complete!")
    print(f"  Total documents: {len(summary_files)}")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Output directory: {CHUNKS_DIR}")


if __name__ == "__main__":
    main()
