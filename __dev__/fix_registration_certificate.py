"""
Fix script for 갑20호증_원고주민등록등본 OCR chunks.
Adds realistic content based on the summary file.
"""

import json
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent / "__test__" / "sample_generated" / "부동산소유권등기소송" / "ocr_chunks"

# File metadata
FILE_ID = 31
TOTAL_PAGES = 6

# Realistic content for 주민등록등본
def generate_registration_content(page_num):
    """Generate realistic content for each page of the registration certificate."""

    if page_num == 1:
        return [
            {
                "text": "주민등록등본",
                "type": "title",
                "confidence": 0.98
            },
            {
                "text": "발급번호: 2024-서울-654321",
                "type": "body",
                "confidence": 0.96
            },
            {
                "text": "발급일자: 2024년 3월 14일",
                "type": "body",
                "confidence": 0.97
            },
            {
                "text": "세대주 성명: 김철수",
                "type": "body",
                "confidence": 0.97
            },
            {
                "text": "주민등록번호: 850322-1******",
                "type": "body",
                "confidence": 0.95
            },
            {
                "text": "세대주 관계: 본인",
                "type": "body",
                "confidence": 0.96
            }
        ]
    elif page_num == 2:
        return [
            {
                "text": "주소 정보",
                "type": "title",
                "confidence": 0.98
            },
            {
                "text": "주소: 서울특별시 서초구 반포대로 45",
                "type": "body",
                "confidence": 0.97
            },
            {
                "text": "상세주소: 101동 202호",
                "type": "body",
                "confidence": 0.96
            },
            {
                "text": "전입일자: 2020년 5월 12일",
                "type": "body",
                "confidence": 0.95
            },
            {
                "text": "거주 기간: 3년 10개월",
                "type": "body",
                "confidence": 0.94
            },
            {
                "text": "주택 유형: 아파트",
                "type": "body",
                "confidence": 0.96
            },
            {
                "text": "전입 사유: 임차",
                "type": "body",
                "confidence": 0.95
            }
        ]
    elif page_num == 3:
        return [
            {
                "text": "세대원 정보",
                "type": "title",
                "confidence": 0.98
            },
            {
                "text": "1. 세대주: 김철수 (850322-1******)",
                "type": "body",
                "confidence": 0.96
            },
            {
                "text": "   전입일: 2020년 5월 12일",
                "type": "body",
                "confidence": 0.95
            },
            {
                "text": "   세대주 관계: 본인",
                "type": "body",
                "confidence": 0.96
            },
            {
                "text": "2. 배우자: 최영숙 (860515-2******)",
                "type": "body",
                "confidence": 0.96
            },
            {
                "text": "   전입일: 2020년 5월 12일",
                "type": "body",
                "confidence": 0.95
            },
            {
                "text": "   세대주 관계: 배우자",
                "type": "body",
                "confidence": 0.96
            }
        ]
    elif page_num == 4:
        return [
            {
                "text": "세대원 정보 (계속)",
                "type": "title",
                "confidence": 0.98
            },
            {
                "text": "3. 자녀: 김민준 (150803-3******)",
                "type": "body",
                "confidence": 0.96
            },
            {
                "text": "   전입일: 2020년 5월 12일",
                "type": "body",
                "confidence": 0.95
            },
            {
                "text": "   세대주 관계: 자녀",
                "type": "body",
                "confidence": 0.96
            },
            {
                "text": "세대 구성원 총 3명",
                "type": "body",
                "confidence": 0.97
            }
        ]
    elif page_num == 5:
        return [
            {
                "text": "전입 경력",
                "type": "title",
                "confidence": 0.98
            },
            {
                "text": "이전 주소: 서울특별시 강남구 삼성동 123-45 (2015.03.20 ~ 2020.05.11)",
                "type": "body",
                "confidence": 0.95
            },
            {
                "text": "이전 주소: 경기도 성남시 분당구 정자동 78-90 (2010.07.15 ~ 2015.03.19)",
                "type": "body",
                "confidence": 0.94
            },
            {
                "text": "이전 주소: 서울특별시 송파구 잠실동 45-67 (2005.02.01 ~ 2010.07.14)",
                "type": "body",
                "confidence": 0.94
            },
            {
                "text": "비고: 원고는 임차 계약 만료로 인해 새로운 주택 구입을 계획 중이었으며,",
                "type": "body",
                "confidence": 0.93
            },
            {
                "text": "이번 매매계약의 목적지인 강남구 테헤란로 123 아크로타워로 이전 예정이었음.",
                "type": "body",
                "confidence": 0.93
            }
        ]
    elif page_num == 6:
        return [
            {
                "text": "발급 기관 정보",
                "type": "title",
                "confidence": 0.98
            },
            {
                "text": "발급 기관: 서울특별시 서초구청",
                "type": "body",
                "confidence": 0.97
            },
            {
                "text": "담당자: 민원실 (02-2155-6000)",
                "type": "body",
                "confidence": 0.96
            },
            {
                "text": "발급 수수료: 무료 (온라인 발급)",
                "type": "body",
                "confidence": 0.95
            },
            {
                "text": "본 증명서는 행정정보 공동이용을 통해 발급되었습니다.",
                "type": "body",
                "confidence": 0.94
            },
            {
                "text": "용도: 법원 제출용",
                "type": "body",
                "confidence": 0.96
            },
            {
                "text": "서울특별시 서초구청장 [직인]",
                "type": "body",
                "confidence": 0.97
            }
        ]

    return []


def create_paragraphs(page_num, chunk_id, chunk_number):
    """Create paragraph objects for a given page."""
    content = generate_registration_content(page_num)
    paragraphs = []

    for idx, item in enumerate(content):
        paragraph = {
            "paragraph_id": f"para-{FILE_ID:03d}-{chunk_number:03d}-{page_num-1:03d}-{idx}",
            "idx_in_page": idx,
            "text": item["text"],
            "page": page_num,
            "bbox": {
                "x": 185 + (idx * 5) % 30,
                "y": 95 + (idx * 160),
                "width": 1220 + (idx * 10) % 100,
                "height": 38 + (idx % 3) * 5
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
    """Fix all chunk files for 갑20호증_원고주민등록등본."""

    chunks = [
        {
            "file": "갑20호증_원고주민등록등본_p1-3.json",
            "pages": [1, 2, 3],
            "chunk_number": 1
        },
        {
            "file": "갑20호증_원고주민등록등본_p3-5.json",
            "pages": [3, 4, 5],
            "chunk_number": 2
        },
        {
            "file": "갑20호증_원고주민등록등본_p5-6.json",
            "pages": [5, 6],
            "chunk_number": 3
        }
    ]

    print(f"Fixing 갑20호증_원고주민등록등본 OCR chunks...\n")

    for chunk_info in chunks:
        file_path = BASE_DIR / chunk_info["file"]
        if file_path.exists():
            fix_chunk_file(file_path, chunk_info["pages"], chunk_info["chunk_number"])
        else:
            print(f"✗ File not found: {file_path.name}")

    print("\n✓ All chunks fixed successfully!")


if __name__ == "__main__":
    main()
