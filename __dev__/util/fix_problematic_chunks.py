#!/usr/bin/env python3
"""
Fix problematic OCR chunks by generating realistic content based on summaries
"""

import json
import sys
import random
import re
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

CHUNKS_DIR = Path('/Users/jaehaklee/qdrant_api_backend/__test__/sample_generated/부동산소유권등기소송/ocr_chunks')
SUMMARIES_DIR = Path('/Users/jaehaklee/qdrant_api_backend/__test__/sample_generated/부동산소유권등기소송/ocr_summaries')
VALIDATION_REPORT = Path('/Users/jaehaklee/qdrant_api_backend/__test__/sample_generated/부동산소유권등기소송/advanced_validation_report.json')

# Document type templates for realistic content generation
DOCUMENT_TEMPLATES = {
    '내용증명': {
        'sections': ['수신인 정보', '발신인 정보', '제목', '본문 - 사실관계', '본문 - 요구사항', '법적 경고', '발송일자'],
        'avg_paragraphs_per_page': 5
    },
    '등기부등본': {
        'sections': ['표제부', '갑구(소유권사항)', '을구(소유권 외 권리)', '발급정보'],
        'avg_paragraphs_per_page': 4
    },
    '건축물대장': {
        'sections': ['일반사항', '토지정보', '건축물 현황', '층별 현황', '발급정보'],
        'avg_paragraphs_per_page': 5
    },
    '카카오톡대화': {
        'sections': ['대화 메타데이터', '대화 내용'],
        'avg_paragraphs_per_page': 8
    },
    '문자메시지': {
        'sections': ['메시지 메타데이터', '메시지 내용'],
        'avg_paragraphs_per_page': 10
    },
    '공인중개사확인서': {
        'sections': ['확인서 제목', '부동산 정보', '거래 정보', '중개사무소 정보', '확인 내용', '날인'],
        'avg_paragraphs_per_page': 5
    },
    '부동산감정평가서': {
        'sections': ['표지', '의뢰인 정보', '평가 대상', '평가 방법', '시장 분석', '평가 결과', '부록'],
        'avg_paragraphs_per_page': 6
    },
    '영수증': {
        'sections': ['영수증 제목', '수령인', '지급인', '금액', '내역', '날인'],
        'avg_paragraphs_per_page': 6
    },
    '거래내역': {
        'sections': ['계좌정보', '거래내역 테이블', '발급정보'],
        'avg_paragraphs_per_page': 20  # 거래내역은 많은 항목
    },
    '인감증명서': {
        'sections': ['증명서 제목', '인적사항', '인감 정보', '발급 정보'],
        'avg_paragraphs_per_page': 4
    },
    '주민등록등본': {
        'sections': ['등본 제목', '세대주 정보', '세대원 정보', '주소 이력', '발급 정보'],
        'avg_paragraphs_per_page': 5
    },
    '대출약정서': {
        'sections': ['약정서 제목', '대출 조건', '이자 및 수수료', '담보 정보', '상환 조건', '특약사항', '서명란'],
        'avg_paragraphs_per_page': 6
    },
    '준비서면': {
        'sections': ['사건번호', '당사자', '주문', '청구취지', '사실관계', '주장', '증거', '결론'],
        'avg_paragraphs_per_page': 7
    },
    '답변서': {
        'sections': ['사건번호', '당사자', '답변취지', '원고 주장 인정/부인', '피고 주장', '증거', '결론'],
        'avg_paragraphs_per_page': 7
    },
    '변론녹취록': {
        'sections': ['사건정보', '출석 확인', '재판장 발언', '원고 측 발언', '피고 측 발언', '다음 기일 지정'],
        'avg_paragraphs_per_page': 10
    },
    '증인신문조서': {
        'sections': ['사건정보', '증인 정보', '선서', '신문 내용', '확인 서명'],
        'avg_paragraphs_per_page': 12
    },
    '필적감정서': {
        'sections': ['감정 의뢰', '감정 대상', '감정 방법', '비교 분석', '감정 결과', '감정인 서명'],
        'avg_paragraphs_per_page': 8
    }
}

def detect_document_type(filename: str) -> str:
    """Detect document type from filename"""
    for doc_type in DOCUMENT_TEMPLATES.keys():
        if doc_type in filename:
            return doc_type
    return 'default'

def extract_key_info_from_summary(summary_text: str) -> Dict:
    """Extract key information from summary"""
    info = {
        'dates': re.findall(r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일', summary_text),
        'amounts': re.findall(r'금\s*[\d,]+원', summary_text),
        'names': re.findall(r'[가-힣]{2,4}(?:\s+[가-힣]{2,4})?', summary_text),
        'addresses': re.findall(r'서울특별시[^.。\n]+', summary_text),
        'numbers': re.findall(r'\d{6}-\d{7}', summary_text),  # 주민번호
        'phone_numbers': re.findall(r'010-\d{4}-\d{4}', summary_text),
    }
    return info

def generate_realistic_content(
    doc_type: str,
    page_num: int,
    total_pages: int,
    summary_info: Dict,
    summary_text: str
) -> List[str]:
    """Generate realistic paragraph content for a specific page"""

    template = DOCUMENT_TEMPLATES.get(doc_type, DOCUMENT_TEMPLATES['default'] if 'default' in DOCUMENT_TEMPLATES else {'sections': ['내용'], 'avg_paragraphs_per_page': 5})
    paragraphs = []

    # Calculate which sections belong to this page
    sections_per_page = max(1, len(template['sections']) // total_pages)
    start_idx = (page_num - 1) * sections_per_page
    end_idx = min(start_idx + sections_per_page + 1, len(template['sections']))

    page_sections = template['sections'][start_idx:end_idx]

    # Generate paragraphs for each section
    for section in page_sections:
        # Add section header
        paragraphs.append(f"[{section}]")

        # Add content based on section type and summary info
        if '날짜' in section or '발급' in section or '일자' in section:
            if summary_info['dates']:
                paragraphs.append(f"{section}: {random.choice(summary_info['dates'])}")

        elif '금액' in section or '대금' in section:
            if summary_info['amounts']:
                paragraphs.append(f"{section}: {random.choice(summary_info['amounts'])}")

        elif '주소' in section or '소재지' in section:
            if summary_info['addresses']:
                paragraphs.append(f"{section}: {summary_info['addresses'][0]}")

        else:
            # Extract relevant snippet from summary for this section
            sentences = summary_text.split('.')
            if sentences:
                relevant_content = '. '.join(random.sample(sentences[:5], min(2, len(sentences))))
                paragraphs.append(relevant_content.strip())

    return paragraphs

def fix_chunk_file(chunk_path: Path, summary_data: dict, doc_type: str):
    """Fix a single chunk file"""
    with open(chunk_path, 'r', encoding='utf-8') as f:
        chunk_data = json.load(f)

    summary_text = summary_data.get('summary_text', '')
    summary_info = extract_key_info_from_summary(summary_text)

    total_pages = chunk_data['total_pages']
    chunk_pages = chunk_data['pages']

    # Generate new paragraph texts and content
    new_paragraph_texts = []
    new_paragraphs = []

    para_id_counter = 0

    for page_num in chunk_pages:
        # Generate realistic content for this page
        page_paragraphs = generate_realistic_content(
            doc_type,
            page_num,
            total_pages,
            summary_info,
            summary_text
        )

        # Create paragraph objects
        for idx, text in enumerate(page_paragraphs):
            new_paragraph_texts.append(text)

            # Create paragraph object
            para_obj = {
                "paragraph_id": f"para-{chunk_data['file_id']:03d}-{chunk_data['chunk_number']:03d}-{page_num:03d}-{idx}",
                "idx_in_page": idx,
                "text": text,
                "page": page_num,
                "bbox": {
                    "x": 180 + random.uniform(-10, 10),
                    "y": 100 + idx * 150 + random.uniform(-20, 20),
                    "width": 1200 + random.uniform(-100, 100),
                    "height": 45 + random.uniform(-5, 15)
                },
                "type": "title" if idx == 0 and '[' in text else "body",
                "confidence_score": round(0.90 + random.uniform(0, 0.09), 2)
            }
            new_paragraphs.append(para_obj)
            para_id_counter += 1

    # Update chunk data
    chunk_data['paragraph_texts'] = new_paragraph_texts
    chunk_data['chunk_content']['paragraphs'] = new_paragraphs

    # Write back
    with open(chunk_path, 'w', encoding='utf-8') as f:
        json.dump(chunk_data, f, ensure_ascii=False, indent=2)

    return len(new_paragraph_texts)

def main():
    """Main fix function"""
    print("=" * 80)
    print("FIXING PROBLEMATIC OCR CHUNKS")
    print("=" * 80)
    print()

    # Load validation report
    if not VALIDATION_REPORT.exists():
        print(f"Error: Validation report not found: {VALIDATION_REPORT}")
        sys.exit(1)

    with open(VALIDATION_REPORT, 'r', encoding='utf-8') as f:
        report = json.load(f)

    problematic_docs = {doc['base_name']: doc for doc in report['problematic_details']}

    print(f"Found {len(problematic_docs)} problematic documents to fix\n")

    fixed_count = 0
    error_count = 0

    for base_name, doc_info in sorted(problematic_docs.items()):
        print(f"Processing: {base_name}")

        # Load summary
        summary_path = SUMMARIES_DIR / f"{base_name}.json"
        if not summary_path.exists():
            print(f"  ⚠️  No summary found, skipping")
            continue

        with open(summary_path, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)

        # Detect document type
        doc_type = detect_document_type(base_name)
        print(f"  Type: {doc_type}")

        # Fix all chunk files for this document
        chunk_files = sorted(CHUNKS_DIR.glob(f"{base_name}_p*.json"))

        total_paragraphs_fixed = 0
        for chunk_path in chunk_files:
            try:
                para_count = fix_chunk_file(chunk_path, summary_data, doc_type)
                total_paragraphs_fixed += para_count
                print(f"    ✅ {chunk_path.name}: {para_count} paragraphs")
            except Exception as e:
                print(f"    ❌ {chunk_path.name}: Error - {e}")
                error_count += 1

        fixed_count += 1
        print(f"  Total paragraphs: {total_paragraphs_fixed}\n")

    print("=" * 80)
    print(f"Summary: Fixed {fixed_count} documents, {error_count} errors")
    print("=" * 80)

if __name__ == '__main__':
    main()
