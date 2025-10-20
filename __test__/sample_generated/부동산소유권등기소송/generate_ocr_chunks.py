#!/usr/bin/env python3
"""
Generate OCR chunk JSON files with 3-page sliding windows for test data.
Each chunk represents a 3-page window with 1-page overlap for context preservation.
"""

import json
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
import os

# Base directories
SCRIPT_DIR = Path(__file__).parent
SUMMARIES_DIR = SCRIPT_DIR / "ocr_summaries"
CHUNKS_OUTPUT_DIR = SCRIPT_DIR / "ocr_chunks"

# Ensure output directory exists
CHUNKS_OUTPUT_DIR.mkdir(exist_ok=True)

# Korean legal text samples for realistic paragraph generation
LEGAL_TEXT_SAMPLES = [
    "원고는 피고를 상대로 부동산 소유권이전등기 청구의 소를 제기하였습니다.",
    "매매계약서에 따르면 매매대금은 총 5억원으로 계약금, 중도금, 잔금으로 구성됩니다.",
    "피고는 계약 당시 해당 부동산의 소유권이 본인에게 있음을 확인하였습니다.",
    "원고가 제출한 증거에 의하면 계약금 5천만원이 2024년 3월 15일 지급되었습니다.",
    "부동산 등기부등본상 근저당권 설정 사실이 확인됩니다.",
    "법원은 당사자들의 주장을 검토한 결과 다음과 같이 판단합니다.",
    "계약서 제5조에 따르면 잔금은 소유권이전등기와 동시에 지급하기로 약정하였습니다.",
    "원고는 계약상 의무를 모두 이행하였으나 피고가 등기를 해주지 않고 있습니다.",
    "증인 신문 결과 계약 당시 쌍방의 진정한 의사는 매매계약 체결에 있었던 것으로 인정됩니다.",
    "감정평가서에 의하면 해당 부동산의 시가는 약 4억 8천만원으로 평가됩니다.",
]

LEGAL_HEADERS = [
    "1. 청구취지",
    "2. 청구원인",
    "가. 계약 체결 경위",
    "나. 대금 지급 사실",
    "다. 피고의 의무 불이행",
    "3. 증거방법",
    "4. 법원의 판단",
    "가. 인정사실",
    "나. 법률적 검토",
    "5. 결론",
]


def generate_paragraph(text: str, page: int, idx_in_page: int) -> Dict[str, Any]:
    """Generate a paragraph object with realistic Korean legal text."""
    return {
        "paragraph_id": str(uuid.uuid4()),
        "idx_in_page": idx_in_page,
        "text": text,
        "page": page,
        "bbox": {
            "x": random.uniform(50, 100),
            "y": random.uniform(100, 200) + (idx_in_page * 150),
            "width": random.uniform(1200, 1400),
            "height": random.uniform(80, 150)
        },
        "type": "body" if idx_in_page > 0 else "heading",
        "confidence_score": random.uniform(0.92, 0.99)
    }


def generate_paragraphs_for_page(page: int, num_paragraphs: int = None) -> List[Dict[str, Any]]:
    """Generate realistic paragraphs for a single page."""
    if num_paragraphs is None:
        num_paragraphs = random.randint(3, 8)

    paragraphs = []
    for idx in range(num_paragraphs):
        if idx == 0 and random.random() < 0.3:  # 30% chance of header
            text = random.choice(LEGAL_HEADERS)
        else:
            text = random.choice(LEGAL_TEXT_SAMPLES)

        paragraphs.append(generate_paragraph(text, page, idx))

    return paragraphs


def calculate_windows(total_pages: int) -> List[List[int]]:
    """
    Calculate 3-page sliding windows with 1-page overlap.

    Examples:
    - 5 pages: [1,2,3], [3,4,5]
    - 10 pages: [1,2,3], [3,4,5], [5,6,7], [7,8,9], [9,10]
    - 14 pages: [1,2,3], [3,4,5], [5,6,7], [7,8,9], [9,10,11], [11,12,13], [13,14]
    """
    windows = []
    start = 1

    while start <= total_pages:
        if start + 2 <= total_pages:
            # Full 3-page window
            windows.append([start, start + 1, start + 2])
            start += 2  # Move by 2 for 1-page overlap
        elif start + 1 <= total_pages:
            # 2-page window at the end
            windows.append([start, start + 1])
            break
        else:
            # Single page at the end
            windows.append([start])
            break

    return windows


def generate_chunk(
    summary_data: Dict[str, Any],
    window_pages: List[int],
    chunk_number: int,
    total_pages: int,
    doc_name: str
) -> Dict[str, Any]:
    """Generate a single OCR chunk for a page window."""

    # Generate paragraphs for all pages in the window
    all_paragraphs = []
    for page in window_pages:
        page_paragraphs = generate_paragraphs_for_page(page)
        all_paragraphs.extend(page_paragraphs)

    # Extract paragraph texts
    paragraph_texts = [p["text"] for p in all_paragraphs]

    # Create page dimensions
    page_dimensions = []
    for page in window_pages:
        page_dimensions.append({
            "page": page,
            "width": 1681,
            "height": 2379
        })

    # Build chunk data
    chunk_id = str(uuid.uuid4())

    chunk = {
        "chunk_id": chunk_id,
        "file_id": summary_data["file_id"],
        "project_id": summary_data["project_id"],
        "storage_file_name": f"{uuid.uuid4()}-{int(datetime.now().timestamp() * 1000)}.pdf",
        "original_file_name": f"{doc_name}.pdf",
        "mime_type": "application/pdf",
        "total_pages": total_pages,
        "processing_duration_seconds": 0,
        "language": "ko",
        "pages": window_pages,
        "chunk_number": chunk_number,
        "paragraph_texts": paragraph_texts,
        "chunk_content": {
            "paragraphs": all_paragraphs
        },
        "page_dimensions": page_dimensions,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    return chunk


def process_summary_file(summary_path: Path, total_pages: int = None) -> List[Dict[str, Any]]:
    """Process a single summary file and generate all its chunks."""

    # Read summary data
    with open(summary_path, 'r', encoding='utf-8') as f:
        summary_data = json.load(f)

    # Assign random page count if not provided
    if total_pages is None:
        total_pages = random.randint(5, 20)

    # Calculate windows
    windows = calculate_windows(total_pages)

    # Generate chunks
    doc_name = summary_path.stem
    chunks = []

    for chunk_number, window_pages in enumerate(windows, start=1):
        chunk = generate_chunk(
            summary_data,
            window_pages,
            chunk_number,
            total_pages,
            doc_name
        )
        chunks.append(chunk)

        # Save chunk to file
        page_range = f"p{window_pages[0]}-{window_pages[-1]}"
        output_filename = f"{doc_name}_{page_range}.json"
        output_path = CHUNKS_OUTPUT_DIR / output_filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)

        print(f"  ✓ Generated: {output_filename}")

    return chunks


def process_batch(batch_name: str, summary_files: List[str], total_pages_override: Dict[str, int] = None):
    """Process a batch of summary files."""
    print(f"\n{'='*60}")
    print(f"Processing {batch_name}")
    print(f"{'='*60}")

    total_override = total_pages_override or {}

    for filename in summary_files:
        summary_path = SUMMARIES_DIR / filename

        if not summary_path.exists():
            print(f"  ⚠️  File not found: {filename}")
            continue

        print(f"\n📄 {filename}")

        # Get page count override if specified
        total_pages = total_override.get(filename)

        try:
            chunks = process_summary_file(summary_path, total_pages)
            print(f"  → Generated {len(chunks)} chunks")
        except Exception as e:
            print(f"  ❌ Error: {e}")


def main():
    """Main execution function."""

    print("\n" + "="*60)
    print("OCR Chunk Generator for 부동산소유권등기소송 Case")
    print("="*60)
    print(f"Summaries directory: {SUMMARIES_DIR}")
    print(f"Output directory: {CHUNKS_OUTPUT_DIR}")

    # Batch 1: Core litigation documents (15 docs)
    batch1_files = [
        "소장.json",
        "답변서.json",
        "원고_준비서면_1차.json",
        "피고_준비서면_1차.json",
        "원고_준비서면_2차.json",
        "피고_준비서면_2차.json",
        "원고_준비서면_3차_최종.json",
        "피고_준비서면_3차_최종.json",
        "부동산_매매계약서_원본.json",
        "보충계약서_0318.json",
        "중개업자_거래확인서.json",
        "갑1호증_매매계약서.json",
        "갑2호증_계약금영수증.json",
        "갑3호증_중도금1차영수증.json",
        "갑4호증_중도금2차영수증.json",
    ]

    # Batch 2: 갑 series evidence (15 docs)
    batch2_files = [
        "갑5호증_잔금입금확인증.json",
        "갑6호증_계좌거래내역_계약금.json",
        "갑7호증_계좌거래내역_중도금1차.json",
        "갑8호증_계좌거래내역_중도금2차.json",
        "갑9호증_계좌거래내역_잔금.json",
        "갑10호증_내용증명_1차_이행촉구.json",
        "갑11호증_내용증명_2차_최고.json",
        "갑12호증_등기부등본.json",
        "갑13호증_건축물대장.json",
        "갑14호증_카카오톡대화_계약논의.json",
        "갑15호증_카카오톡대화_이행요구.json",
        "갑16호증_문자메시지.json",
        "갑17호증_공인중개사확인서.json",
        "갑18호증_부동산감정평가서.json",
        "갑19호증_원고인감증명서.json",
    ]

    # Batch 3: More 갑 and 을 series evidence (10 docs)
    batch3_files = [
        "갑20호증_원고주민등록등본.json",
        "갑21호증_대출약정서.json",
        "을1호증_보충합의서_위조의심.json",
        "을2호증_피고계좌거래내역.json",
        "을3호증_피고문자메시지_악의적의도.json",
        "을4호증_부동산담보대출서류.json",
        "을5호증_피고주민등록등본.json",
        "을6호증_피고진술서.json",
        "을7호증_감정평가서_피고제출.json",
        "을8호증_제3자진술서.json",
    ]

    # Batch 4: Hearing transcripts and expert reports (10 docs)
    batch4_files = [
        "증인신문조서_원고본인.json",
        "증인신문조서_피고본인.json",
        "증인신문조서_공인중개사.json",
        "증인신문조서_제3자목격자.json",
        "변론녹취록_1회_0903.json",
        "변론녹취록_2회_1008.json",
        "변론녹취록_3회_1105.json",
        "증거조사기일녹취록_1112.json",
        "최종변론기일녹취록_1210.json",
        "국과수필적감정서.json",
    ]

    # Process batches
    process_batch("Batch 1: Core Litigation Documents", batch1_files)
    process_batch("Batch 2: 갑 Series Evidence", batch2_files)
    process_batch("Batch 3: 을 Series Evidence", batch3_files)
    process_batch("Batch 4: Hearing Transcripts & Expert Reports", batch4_files)

    # Summary
    print("\n" + "="*60)
    print("Generation Complete!")
    print("="*60)

    total_files = len(list(CHUNKS_OUTPUT_DIR.glob("*.json")))
    print(f"Total chunk files generated: {total_files}")
    print(f"Output location: {CHUNKS_OUTPUT_DIR}")


if __name__ == "__main__":
    main()
