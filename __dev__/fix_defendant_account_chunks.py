#!/usr/bin/env python3
"""
Fix 을2호증_피고계좌거래내역 chunk files to align with summary.

Issues fixed:
- Same text repetition across pages within chunks
- Misalignment with summary (should be 3-6월, not 4-9월)
- Unrealistic paragraph counts (2 per page -> 8-12 per page)
- 3-page window overlap inconsistency
- Unnatural content (missing transaction details)
"""

import json
from pathlib import Path
from datetime import datetime

# Base directory
BASE_DIR = Path(__file__).parent.parent / "__test__/sample_generated/부동산소유권등기소송/ocr_chunks"

# Summary alignment: 3-6월, 4 major transactions
# Page structure: 13 pages total
# - Pages 1-3: March transactions (계약금 50M on 3/15)
# - Pages 4-6: April transactions (중도금1차 150M on 4/15)
# - Pages 7-9: May transactions (중도금2차 150M on 5/15)
# - Pages 10-13: June transactions (잔금 150M on 6/15)

def generate_realistic_transactions(page_num, month, is_major_payment=False, major_amount=None):
    """Generate realistic bank transaction entries for a page."""
    base_balance = 5000000  # Starting balance

    transactions = []

    # Page header
    transactions.append({
        "text": "국민은행 계좌거래내역",
        "type": "header"
    })
    transactions.append({
        "text": "계좌번호: 123-45-678901 (예금주: 이영희)",
        "type": "header"
    })
    transactions.append({
        "text": f"조회기간: 2024년 {month}월 01일 ~ 2024년 {month}월 {28 if month==2 else 30}일",
        "type": "header"
    })
    transactions.append({
        "text": "거래일시\t구분\t거래내용\t입금액\t출금액\t잔액",
        "type": "table_header"
    })

    # Generate 8-12 transaction rows
    import random
    random.seed(page_num)  # Consistent per page

    num_transactions = random.randint(8, 12)
    current_balance = base_balance

    for i in range(num_transactions):
        day = random.randint(1, 28)
        hour = random.randint(9, 17)
        minute = random.randint(0, 59)

        # Major payment on specific day (always insert at position 5)
        if is_major_payment and i == 5:
            transactions.append({
                "text": f"2024.{month:02d}.15 14:30\t입금\t김철수 (매매대금)\t{major_amount:,}원\t\t{current_balance + major_amount:,}원",
                "type": "table_row_major"
            })
            current_balance += major_amount
        else:
            # Regular transactions
            is_deposit = random.choice([True, False])
            amount = random.randint(10000, 500000)

            if is_deposit:
                current_balance += amount
                transactions.append({
                    "text": f"2024.{month:02d}.{day:02d} {hour:02d}:{minute:02d}\t입금\t{'ATM입금' if random.random() > 0.5 else '계좌이체'}\t{amount:,}원\t\t{current_balance:,}원",
                    "type": "table_row"
                })
            else:
                if current_balance > amount:
                    current_balance -= amount
                    transactions.append({
                        "text": f"2024.{month:02d}.{day:02d} {hour:02d}:{minute:02d}\t출금\t{'ATM출금' if random.random() > 0.5 else '계좌이체'}\t\t{amount:,}원\t{current_balance:,}원",
                        "type": "table_row"
                    })

    return transactions

def create_paragraphs(page, transactions, chunk_number, para_offset):
    """Create paragraph objects from transactions."""
    paragraphs = []

    y_position = 120.0
    idx_in_page = 0

    for trans in transactions:
        height = 35 if trans["type"] == "table_row" else 50
        width_base = 1200 if trans["type"].startswith("header") else 1400

        paragraphs.append({
            "paragraph_id": f"para-034-{chunk_number:03d}-{page-1:03d}-{idx_in_page}",
            "idx_in_page": idx_in_page,
            "text": trans["text"],
            "page": page,
            "bbox": {
                "x": 180.0 + (idx_in_page % 3) * 5,
                "y": y_position,
                "width": width_base - (idx_in_page % 5) * 10,
                "height": height
            },
            "type": "header" if trans["type"].startswith("header") else "body",
            "confidence_score": round(0.90 + (idx_in_page % 10) * 0.01, 2)
        })

        y_position += height + 10
        idx_in_page += 1

    return paragraphs

def generate_chunk_data(chunk_number, pages_range, month_mapping):
    """Generate complete chunk data."""

    chunk_id_map = {
        1: "31becbc9-4c82-4617-80af-e290e527a7e1",
        2: "fc07bdcd-a271-4b88-8fc7-23b706e30647",
        3: "581eb308-cc8d-420e-91ff-59fb78f7ad0a",
        4: "b078894b-f030-4b8a-af96-4c876575e7db",
        5: "e0c9769a-85dc-494b-861d-c0d3c3142b82",
        6: "bc56fa7b-8a1d-4f4f-bec6-9b6190feedc6"
    }

    all_paragraphs = []
    paragraph_texts = []
    page_dimensions = []

    for page in pages_range:
        month = month_mapping.get(page, 3)

        # Determine if major payment page
        is_major = False
        major_amount = None

        if page == 2:  # March major payment (50M)
            is_major = True
            major_amount = 50000000
        elif page == 5:  # April major payment (150M)
            is_major = True
            major_amount = 150000000
        elif page == 8:  # May major payment (150M)
            is_major = True
            major_amount = 150000000
        elif page == 11:  # June major payment (150M)
            is_major = True
            major_amount = 150000000

        transactions = generate_realistic_transactions(page, month, is_major, major_amount)
        paragraphs = create_paragraphs(page, transactions, chunk_number, len(all_paragraphs))

        all_paragraphs.extend(paragraphs)

        # Extract text for paragraph_texts
        for para in paragraphs:
            paragraph_texts.append(para["text"])

        page_dimensions.append({
            "page": page,
            "width": 1681,
            "height": 2379
        })

    created_dates = {
        1: "2024-08-02T00:00:00+00:00",
        2: "2024-08-03T00:00:00+00:00",
        3: "2024-08-04T00:00:00+00:00",
        4: "2024-08-05T00:00:00+00:00",
        5: "2024-08-06T00:00:00+00:00",
        6: "2024-08-07T00:00:00+00:00"
    }

    return {
        "chunk_id": chunk_id_map[chunk_number],
        "file_id": 34,
        "project_id": 1001,
        "storage_file_name": "exhibit_b2_defendant_account.pdf",
        "original_file_name": "을2호증_피고계좌거래내역.pdf",
        "mime_type": "application/pdf",
        "total_pages": 13,
        "processing_duration_seconds": 0,
        "language": "ko",
        "pages": list(pages_range),
        "chunk_number": chunk_number,
        "paragraph_texts": paragraph_texts,
        "chunk_content": {
            "paragraphs": all_paragraphs
        },
        "page_dimensions": page_dimensions,
        "created_at": created_dates[chunk_number]
    }

def main():
    """Generate all 6 chunk files."""

    # Month mapping: pages to months
    month_mapping = {
        1: 3, 2: 3, 3: 3,      # March
        4: 4, 5: 4, 6: 4,      # April
        7: 5, 8: 5, 9: 5,      # May
        10: 6, 11: 6, 12: 6, 13: 6  # June
    }

    # 3-page sliding window with 1-page overlap
    chunk_configs = [
        (1, range(1, 4)),    # pages 1-3
        (2, range(3, 6)),    # pages 3-5
        (3, range(5, 8)),    # pages 5-7
        (4, range(7, 10)),   # pages 7-9
        (5, range(9, 12)),   # pages 9-11
        (6, range(11, 14))   # pages 11-13
    ]

    for chunk_num, pages in chunk_configs:
        chunk_data = generate_chunk_data(chunk_num, pages, month_mapping)

        # Determine filename
        page_start = min(pages)
        page_end = max(pages)
        filename = f"을2호증_피고계좌거래내역_p{page_start}-{page_end}.json"
        filepath = BASE_DIR / filename

        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Updated: {filename}")
        print(f"   Pages: {list(pages)}, Paragraphs: {len(chunk_data['chunk_content']['paragraphs'])}")

if __name__ == "__main__":
    main()
    print("\n✅ All 을2호증_피고계좌거래내역 chunks fixed successfully!")
