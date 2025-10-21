"""
Fix script for 갑19호증_원고인감증명서 OCR chunks.
Adds realistic content based on the summary file.
"""

import json
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent / "__test__" / "sample_generated" / "부동산소유권등기소송" / "ocr_chunks"

# File metadata
FILE_ID = 30
TOTAL_PAGES = 5

# Realistic content for 인감증명서
def generate_seal_certificate_content(page_num):
    """Generate realistic content for each page of the seal certificate."""

    if page_num == 1:
        return [
            {
                "text": "인감증명서",
                "type": "title",
                "confidence": 0.98
            },
            {
                "text": "발급번호: 2024-서울-123456",
                "type": "body",
                "confidence": 0.96
            },
            {
                "text": "성명: 김철수",
                "type": "body",
                "confidence": 0.97
            },
            {
                "text": "주민등록번호: 850322-1******",
                "type": "body",
                "confidence": 0.95
            },
            {
                "text": "주소: 서울특별시 서초구 반포대로 45, 101동 202호",
                "type": "body",
                "confidence": 0.96
            },
            {
                "text": "용도: 부동산 매매계약",
                "type": "body",
                "confidence": 0.97
            }
        ]
    elif page_num == 2:
        return [
            {
                "text": "인감",
                "type": "title",
                "confidence": 0.98
            },
            {
                "text": "[인감 날인]",
                "type": "body",
                "confidence": 0.92
            },
            {
                "text": "위와 같이 인감을 등록하였음을 증명합니다.",
                "type": "body",
                "confidence": 0.96
            },
            {
                "text": "2024년 3월 14일",
                "type": "body",
                "confidence": 0.97
            },
            {
                "text": "서울특별시 서초구청장 [직인]",
                "type": "body",
                "confidence": 0.95
            }
        ]
    elif page_num == 3:
        return [
            {
                "text": "인감증명서 사용 안내",
                "type": "title",
                "confidence": 0.98
            },
            {
                "text": "1. 본 증명서는 발급일로부터 3개월간 유효합니다.",
                "type": "body",
                "confidence": 0.96
            },
            {
                "text": "2. 용도 외 사용을 금지합니다.",
                "type": "body",
                "confidence": 0.95
            },
            {
                "text": "3. 위조 또는 변조 시 법적 책임을 지게 됩니다.",
                "type": "body",
                "confidence": 0.97
            },
            {
                "text": "4. 타인에게 양도하거나 대여할 수 없습니다.",
                "type": "body",
                "confidence": 0.96
            },
            {
                "text": "5. 본 증명서는 전자서명법에 따라 전자적으로도 발급 가능합니다.",
                "type": "body",
                "confidence": 0.94
            }
        ]
    elif page_num == 4:
        return [
            {
                "text": "인감 등록 정보",
                "type": "title",
                "confidence": 0.98
            },
            {
                "text": "등록일자: 2020년 5월 15일",
                "type": "body",
                "confidence": 0.96
            },
            {
                "text": "최종 변경일: 2020년 5월 15일",
                "type": "body",
                "confidence": 0.97
            },
            {
                "text": "등록 방법: 본인 직접 방문",
                "type": "body",
                "confidence": 0.95
            },
            {
                "text": "신분증 확인: 주민등록증",
                "type": "body",
                "confidence": 0.96
            },
            {
                "text": "비고: 해당 인감은 본인이 직접 등록한 것으로 확인됨",
                "type": "body",
                "confidence": 0.94
            }
        ]
    elif page_num == 5:
        return [
            {
                "text": "열람 및 재발급 안내",
                "type": "title",
                "confidence": 0.98
            },
            {
                "text": "인감증명서 재발급: 주민센터 또는 정부24 온라인 신청",
                "type": "body",
                "confidence": 0.95
            },
            {
                "text": "수수료: 600원 (온라인 발급 시 무료)",
                "type": "body",
                "confidence": 0.96
            },
            {
                "text": "문의: 서울특별시 서초구청 민원실 (02-2155-6000)",
                "type": "body",
                "confidence": 0.97
            },
            {
                "text": "본 증명서는 행정정보 공동이용을 통해 발급되었습니다.",
                "type": "body",
                "confidence": 0.94
            }
        ]

    return []


def create_paragraphs(page_num, chunk_id, chunk_number):
    """Create paragraph objects for a given page."""
    content = generate_seal_certificate_content(page_num)
    paragraphs = []

    for idx, item in enumerate(content):
        paragraph = {
            "paragraph_id": f"para-{FILE_ID:03d}-{chunk_number:03d}-{page_num-1:03d}-{idx}",
            "idx_in_page": idx,
            "text": item["text"],
            "page": page_num,
            "bbox": {
                "x": 190 + (idx * 5) % 30,
                "y": 100 + (idx * 180),
                "width": 1200 + (idx * 10) % 100,
                "height": 40 + (idx % 3) * 5
            },
            "type": item["type"],
            "confidence_score": item["confidence"]
        }
        paragraphs.append(paragraph)

    return paragraphs


def fix_chunk_file(file_path, pages, chunk_number):
    """Fix a single chunk file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Generate all paragraphs for all pages in this chunk
    all_paragraphs = []
    for page in pages:
        page_paragraphs = create_paragraphs(page, data["chunk_id"], chunk_number)
        all_paragraphs.extend(page_paragraphs)

    # Update paragraph_texts
    data["paragraph_texts"] = [p["text"] for p in all_paragraphs]

    # Update chunk_content
    data["chunk_content"]["paragraphs"] = all_paragraphs

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✓ Fixed {file_path.name}: {len(all_paragraphs)} paragraphs across pages {pages}")


def main():
    """Fix all chunk files for 갑19호증_원고인감증명서."""

    chunks = [
        {
            "file": "갑19호증_원고인감증명서_p1-3.json",
            "pages": [1, 2, 3],
            "chunk_number": 1
        },
        {
            "file": "갑19호증_원고인감증명서_p3-5.json",
            "pages": [3, 4, 5],
            "chunk_number": 2
        }
    ]

    print(f"Fixing 갑19호증_원고인감증명서 OCR chunks...\n")

    for chunk_info in chunks:
        file_path = BASE_DIR / chunk_info["file"]
        if file_path.exists():
            fix_chunk_file(file_path, chunk_info["pages"], chunk_info["chunk_number"])
        else:
            print(f"✗ File not found: {file_path.name}")

    print("\n✓ All chunks fixed successfully!")


if __name__ == "__main__":
    main()
