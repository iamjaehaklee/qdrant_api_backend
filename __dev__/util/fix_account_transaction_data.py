#!/usr/bin/env python3
"""
Fix account transaction OCR chunk data to be realistic and consistent with summaries.
"""

import json
import os
from pathlib import Path
from datetime import datetime
import uuid

# Transaction details from summaries
TRANSACTIONS = {
    "갑6호증_계좌거래내역_계약금": {
        "file_id": 17,
        "total_pages": 8,
        "date": "2024년 3월 15일",
        "time": "10:23:15",
        "amount": "50,000,000",
        "amount_formatted": "50,000,000원",
        "type": "계약금",
        "from_account": "신한은행 110-987-654321",
        "from_name": "김철수",
        "to_account": "국민은행 123-45-678901",
        "to_name": "이영희",
        "balance_after": "125,430,000",
        "property": "서울특별시 강남구 테헤란로 123, 아크로타워 456동 789호"
    },
    "갑7호증_계좌거래내역_중도금1차": {
        "file_id": 18,
        "total_pages": 9,
        "date": "2024년 4월 15일",
        "time": "14:05:42",
        "amount": "150,000,000",
        "amount_formatted": "150,000,000원",
        "type": "중도금1차",
        "from_account": "신한은행 110-987-654321",
        "from_name": "김철수",
        "to_account": "국민은행 123-45-678901",
        "to_name": "이영희",
        "balance_after": "8,920,000",
        "property": "서울특별시 강남구 테헤란로 123, 아크로타워 456동 789호",
        "note": "대출 금 120,000,000원 + 자기자금 금 30,000,000원"
    },
    "갑8호증_계좌거래내역_중도금2차": {
        "file_id": 19,
        "total_pages": 8,
        "date": "2024년 5월 15일",
        "time": "09:47:33",
        "amount": "150,000,000",
        "amount_formatted": "150,000,000원",
        "type": "중도금2차",
        "from_account": "신한은행 110-987-654321",
        "from_name": "김철수",
        "to_account": "국민은행 123-45-678901",
        "to_name": "이영희",
        "balance_after": "1,230,000",
        "property": "서울특별시 강남구 테헤란로 123, 아크로타워 456동 789호",
        "note": "대출 금 140,000,000원 + 친척 차용 금 10,000,000원"
    },
    "갑9호증_계좌거래내역_잔금": {
        "file_id": 20,
        "total_pages": 10,
        "date": "2024년 6월 15일",
        "time": "15:32:18",
        "amount": "150,000,000",
        "amount_formatted": "150,000,000원",
        "type": "잔금",
        "from_account": "신한은행 110-987-654321",
        "from_name": "김철수",
        "to_account": "국민은행 123-45-678901",
        "to_name": "이영희",
        "balance_after": "520,000",
        "property": "서울특별시 강남구 테헤란로 123, 아크로타워 456동 789호",
        "note": "대출 금 150,000,000원"
    }
}

def generate_page_content(trans_info, page_num):
    """Generate realistic bank transaction page content"""
    paragraphs = []
    y_pos = 100

    # Header section
    if page_num == 1:
        paragraphs.extend([
            {
                "text": "신한은행 계좌거래내역",
                "type": "header",
                "y": y_pos
            },
            {
                "text": f"계좌번호: {trans_info['from_account'].replace('신한은행 ', '')}",
                "type": "body",
                "y": y_pos + 60
            },
            {
                "text": f"예금주: {trans_info['from_name']}",
                "type": "body",
                "y": y_pos + 120
            },
            {
                "text": f"조회기간: {trans_info['date']}",
                "type": "body",
                "y": y_pos + 180
            }
        ])
        y_pos += 280

    # Transaction detail
    paragraphs.extend([
        {
            "text": f"거래일시: {trans_info['date']} {trans_info['time']}",
            "type": "body",
            "y": y_pos
        },
        {
            "text": "거래구분: 즉시이체",
            "type": "body",
            "y": y_pos + 60
        },
        {
            "text": f"출금액: {trans_info['amount_formatted']}",
            "type": "body",
            "y": y_pos + 120
        },
        {
            "text": f"입금계좌: {trans_info['to_account']} ({trans_info['to_name']})",
            "type": "body",
            "y": y_pos + 180
        },
        {
            "text": f"거래 후 잔액: {trans_info['balance_after']}원",
            "type": "body",
            "y": y_pos + 240
        },
        {
            "text": f"적요: {trans_info['property']} 매매 {trans_info['type']}",
            "type": "body",
            "y": y_pos + 300
        }
    ])

    if trans_info.get('note'):
        paragraphs.append({
            "text": f"비고: {trans_info['note']}",
            "type": "body",
            "y": y_pos + 360
        })

    # Footer
    if page_num >= 2:
        paragraphs.append({
            "text": f"페이지 {page_num}/{trans_info['total_pages']}",
            "type": "footer",
            "y": 2300
        })

    return paragraphs

def create_chunk_data(doc_key, pages, chunk_num, created_at):
    """Create chunk data structure"""
    trans_info = TRANSACTIONS[doc_key]

    # Generate paragraphs for all pages in chunk
    all_paragraphs = []
    paragraph_texts = []

    for page in pages:
        page_paras = generate_page_content(trans_info, page)
        for idx, para in enumerate(page_paras):
            para_id = f"para-{trans_info['file_id']:03d}-{chunk_num:03d}-{page-1:03d}-{idx}"
            paragraph_texts.append(para['text'])
            all_paragraphs.append({
                "paragraph_id": para_id,
                "idx_in_page": idx,
                "text": para['text'],
                "page": page,
                "bbox": {
                    "x": 180 + (idx * 5) % 40,
                    "y": para['y'],
                    "width": 1200 + (idx * 10) % 150,
                    "height": 45
                },
                "type": para['type'],
                "confidence_score": round(0.90 + (idx % 10) * 0.01, 2)
            })

    page_dimensions = [
        {"page": p, "width": 1681, "height": 2379} for p in pages
    ]

    original_file_name = f"{doc_key}.pdf"

    # Map file_id to exhibit number (file_id 17 = exhibit a6, etc.)
    exhibit_num = {17: 6, 18: 7, 19: 8, 20: 9}[trans_info['file_id']]
    storage_file_name = f"exhibit_a{exhibit_num}_" + {
        17: "account_deposit",
        18: "account_interim1",
        19: "account_interim2",
        20: "account_balance"
    }[trans_info['file_id']] + ".pdf"

    return {
        "chunk_id": str(uuid.uuid4()),
        "file_id": trans_info['file_id'],
        "project_id": 1001,
        "storage_file_name": storage_file_name,
        "original_file_name": original_file_name,
        "mime_type": "application/pdf",
        "total_pages": trans_info['total_pages'],
        "processing_duration_seconds": 0,
        "language": "ko",
        "pages": pages,
        "chunk_number": chunk_num,
        "paragraph_texts": paragraph_texts,
        "chunk_content": {
            "paragraphs": all_paragraphs
        },
        "page_dimensions": page_dimensions,
        "created_at": created_at
    }

def generate_chunks_for_document(doc_key, base_dir):
    """Generate all chunks for a document using 3-page windows with 1-page overlap"""
    trans_info = TRANSACTIONS[doc_key]
    total_pages = trans_info['total_pages']

    # Calculate 3-page windows with 1-page overlap
    chunks = []
    page = 1
    chunk_num = 1

    while page <= total_pages:
        if total_pages - page >= 2:
            # Full 3-page window
            pages = [page, page+1, page+2]
            page += 2  # Overlap by 1
        elif total_pages - page == 1:
            # Last 2 pages
            pages = [page, page+1]
            page += 2
        else:
            # Last page
            pages = [page]
            page += 1

        created_at = f"2024-08-{1 + chunk_num:02d}T00:00:00+00:00"
        chunk_data = create_chunk_data(doc_key, pages, chunk_num, created_at)

        # Build filename
        if len(pages) == 1:
            filename = f"{doc_key}_p{pages[0]}.json"
        elif len(pages) == 2:
            filename = f"{doc_key}_p{pages[0]}-{pages[1]}.json"
        else:
            filename = f"{doc_key}_p{pages[0]}-{pages[2]}.json"

        filepath = base_dir / filename
        chunks.append((filepath, chunk_data))
        chunk_num += 1

    return chunks

def main():
    base_dir = Path("/Users/jaehaklee/qdrant_api_backend/__test__/sample_generated/부동산소유권등기소송/ocr_chunks")

    for doc_key in TRANSACTIONS.keys():
        print(f"\n🔧 Generating chunks for {doc_key}...")
        chunks = generate_chunks_for_document(doc_key, base_dir)

        for filepath, chunk_data in chunks:
            print(f"  ✏️  {filepath.name}")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, ensure_ascii=False, indent=2)

    print("\n✅ All files fixed successfully!")

if __name__ == "__main__":
    main()
