#!/usr/bin/env python3
"""
계좌거래내역 OCR 청크 파일 수정 스크립트

문제점:
1. 모든 페이지에서 같은 거래 반복
2. 한 페이지당 거래 수가 너무 적음 (비현실적)
3. 마지막 청크의 청킹 구조 문제

수정사항:
1. 각 페이지에 현실적인 거래 내역 추가 (다양한 날짜/시간)
2. 페이지당 4-5건의 거래로 현실감 부여
3. 잔액 변동 반영
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import random

# 거래 템플릿
TRANSACTION_TYPES = [
    ("급여이체 (주)테크컴퍼니", None, 4500000, "salary"),
    ("ATM출금 강남역점", 500000, None, "withdraw"),
    ("ATM출금 역삼역점", 300000, None, "withdraw"),
    ("카드대금 신한카드", 1850000, None, "card"),
    ("카드대금 현대카드", 920000, None, "card"),
    ("이체 국민은행 (통신비)", 89000, None, "transfer"),
    ("이체 우리은행 (보험료)", 450000, None, "transfer"),
    ("이체 하나은행 (학원비)", 680000, None, "transfer"),
    ("자동이체 (아파트관리비)", 320000, None, "auto"),
    ("ATM입금", None, 2000000, "deposit"),
    ("급여보너스 (주)테크컴퍼니", None, 5000000, "bonus"),
]


def generate_realistic_transactions(page_num, start_date, start_balance, num_transactions=4, include_main_transaction=False):
    """페이지에 표시될 현실적인 거래 내역 생성"""
    transactions = []
    current_balance = start_balance
    current_date = start_date

    for i in range(num_transactions):
        # 거래 타입 선택
        trans_type = random.choice(TRANSACTION_TYPES)
        desc, withdraw, deposit, _ = trans_type

        # 시간 증가 (0.5~3시간)
        current_date += timedelta(hours=random.uniform(0.5, 3))

        # 잔액 계산
        if withdraw:
            current_balance -= withdraw
        if deposit:
            current_balance += deposit

        transactions.append({
            "datetime": current_date,
            "description": desc,
            "withdraw": withdraw,
            "deposit": deposit,
            "balance": current_balance
        })

    # 주요 거래 추가 (계약금/중도금/잔금)
    if include_main_transaction:
        main_trans = include_main_transaction
        current_date += timedelta(hours=random.uniform(0.5, 2))
        current_balance -= main_trans["amount"]

        transactions.append({
            "datetime": current_date,
            "description": f"즉시이체 국민은행 123-45-678901 (이영희)",
            "withdraw": main_trans["amount"],
            "deposit": None,
            "balance": current_balance
        })

        # 적요 추가
        transactions.append({
            "datetime": current_date + timedelta(seconds=2),
            "description": f"적요: {main_trans['memo']}",
            "withdraw": None,
            "deposit": None,
            "balance": None  # 적요 행에는 잔액 표시 안 함
        })

    return transactions, current_balance


def create_paragraph_texts(transactions):
    """거래 내역에서 paragraph_texts 생성"""
    texts = []

    # 테이블 헤더
    texts.extend(["거래일시", "거래내용", "출금액", "입금액", "잔액"])

    # 거래 데이터
    for trans in transactions:
        dt = trans["datetime"].strftime("%Y.%m.%d %H:%M:%S")
        texts.append(dt)
        texts.append(trans["description"])
        texts.append(str(trans["withdraw"]) if trans["withdraw"] else "")
        texts.append(str(trans["deposit"]) if trans["deposit"] else "")
        texts.append(str(trans["balance"]) if trans["balance"] else "")

    return texts


def create_paragraph_objects(transactions, page_num, file_id, chunk_num):
    """거래 내역에서 paragraph 객체 리스트 생성"""
    paragraphs = []
    y_offset = 100
    idx = 0

    # 테이블 헤더
    headers = ["거래일시", "거래내용", "출금액", "입금액", "잔액"]
    x_positions = [200, 450, 700, 850, 1000]
    widths = [250, 250, 150, 150, 200]

    for i, header in enumerate(headers):
        paragraphs.append({
            "paragraph_id": f"para-{file_id:03d}-{chunk_num:03d}-{page_num:03d}-{idx}",
            "idx_in_page": idx,
            "text": header,
            "page": page_num,
            "bbox": {
                "x": x_positions[i],
                "y": y_offset,
                "width": widths[i],
                "height": 30
            },
            "type": "table_header",
            "confidence_score": 0.95
        })
        idx += 1

    y_offset = 140

    # 거래 데이터
    for trans in transactions:
        dt = trans["datetime"].strftime("%Y.%m.%d %H:%M:%S")
        row_data = [
            dt,
            trans["description"],
            f"{trans['withdraw']:,}" if trans['withdraw'] else "",
            f"{trans['deposit']:,}" if trans['deposit'] else "",
            f"{trans['balance']:,}" if trans['balance'] else ""
        ]

        for i, data in enumerate(row_data):
            paragraphs.append({
                "paragraph_id": f"para-{file_id:03d}-{chunk_num:03d}-{page_num:03d}-{idx}",
                "idx_in_page": idx,
                "text": data,
                "page": page_num,
                "bbox": {
                    "x": x_positions[i],
                    "y": y_offset,
                    "width": widths[i],
                    "height": 28
                },
                "type": "body",
                "confidence_score": round(random.uniform(0.90, 0.97), 2)
            })
            idx += 1

        y_offset += 35

    # 페이지 푸터
    paragraphs.append({
        "paragraph_id": f"para-{file_id:03d}-{chunk_num:03d}-{page_num:03d}-{idx}",
        "idx_in_page": idx,
        "text": f"페이지 {page_num}/{8 if file_id == 17 else (9 if file_id == 18 else (8 if file_id == 19 else 10))}",
        "page": page_num,
        "bbox": {
            "x": 600,
            "y": 2300,
            "width": 200,
            "height": 30
        },
        "type": "footer",
        "confidence_score": 0.98
    })

    return paragraphs


def fix_account_chunk_file(file_path, main_transaction_info):
    """계좌거래내역 청크 파일 수정"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    file_id = data["file_id"]
    chunk_num = data["chunk_number"]
    pages = data["pages"]

    # 시작 날짜와 잔액 설정
    if file_id == 17:  # 갑6호증 (계약금)
        start_date = datetime(2024, 3, 1, 9, 0, 0)
        start_balance = 179230000
        main_trans = {"amount": 50000000, "memo": "서울특별시 강남구 테헤란로 123, 아크로타워 456동 789호 매매 계약금", "page": 2}
    elif file_id == 18:  # 갑7호증 (중도금1차)
        start_date = datetime(2024, 4, 1, 9, 0, 0)
        start_balance = 165000000
        main_trans = {"amount": 150000000, "memo": "서울특별시 강남구 테헤란로 123, 아크로타워 456동 789호 매매 중도금1차", "page": 2}
    elif file_id == 19:  # 갑8호증 (중도금2차)
        start_date = datetime(2024, 5, 1, 9, 0, 0)
        start_balance = 155000000
        main_trans = {"amount": 150000000, "memo": "서울특별시 강남구 테헤란로 123, 아크로타워 456동 789호 매매 중도금2차", "page": 2}
    elif file_id == 20:  # 갑9호증 (잔금)
        start_date = datetime(2024, 6, 1, 9, 0, 0)
        start_balance = 160000000
        main_trans = {"amount": 150000000, "memo": "서울특별시 강남구 테헤란로 123, 아크로타워 456동 789호 매매 잔금", "page": 2}
    else:
        return  # 알 수 없는 file_id

    # 헤더 생성
    all_paragraph_texts = [
        "신한은행 계좌거래내역",
        "계좌번호: 110-987-654321",
        "예금주: 김철수",
        f"조회기간: {start_date.strftime('%Y년 %m월 1일')} ~ {start_date.strftime('%Y년 %m월 %d일')}"
    ]

    all_paragraphs = [
        {
            "paragraph_id": f"para-{file_id:03d}-{chunk_num:03d}-000-0",
            "idx_in_page": 0,
            "text": "신한은행 계좌거래내역",
            "page": pages[0],
            "bbox": {"x": 180, "y": 100, "width": 1200, "height": 45},
            "type": "header",
            "confidence_score": 0.98
        },
        {
            "paragraph_id": f"para-{file_id:03d}-{chunk_num:03d}-000-1",
            "idx_in_page": 1,
            "text": "계좌번호: 110-987-654321",
            "page": pages[0],
            "bbox": {"x": 200, "y": 160, "width": 800, "height": 35},
            "type": "body",
            "confidence_score": 0.97
        },
        {
            "paragraph_id": f"para-{file_id:03d}-{chunk_num:03d}-000-2",
            "idx_in_page": 2,
            "text": "예금주: 김철수",
            "page": pages[0],
            "bbox": {"x": 200, "y": 200, "width": 400, "height": 35},
            "type": "body",
            "confidence_score": 0.97
        },
        {
            "paragraph_id": f"para-{file_id:03d}-{chunk_num:03d}-000-3",
            "idx_in_page": 3,
            "text": f"조회기간: {start_date.strftime('%Y년 %m월 1일')} ~ {start_date.strftime('%Y년 %m월 %d일')}",
            "page": pages[0],
            "bbox": {"x": 200, "y": 240, "width": 900, "height": 35},
            "type": "body",
            "confidence_score": 0.96
        }
    ]

    current_balance = start_balance
    current_date = start_date

    # 각 페이지 처리
    for page_idx, page_num in enumerate(pages):
        include_main = main_trans if page_num == main_trans["page"] else False

        # 해당 페이지의 거래 생성
        transactions, current_balance = generate_realistic_transactions(
            page_num, current_date, current_balance,
            num_transactions=4,
            include_main_transaction=include_main
        )

        # paragraph_texts 추가
        page_texts = create_paragraph_texts(transactions)
        all_paragraph_texts.extend(page_texts)
        all_paragraph_texts.append(f"페이지 {page_num}/{data['total_pages']}")

        # paragraph 객체 추가 (첫 페이지는 헤더 제외)
        page_paragraphs = create_paragraph_objects(transactions, page_num, file_id, chunk_num)
        all_paragraphs.extend(page_paragraphs)

        # 다음 페이지를 위한 날짜 업데이트
        if transactions:
            current_date = transactions[-1]["datetime"] + timedelta(hours=random.uniform(2, 6))

    # 데이터 업데이트
    data["paragraph_texts"] = all_paragraph_texts
    data["chunk_content"]["paragraphs"] = all_paragraphs

    # 파일 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Fixed: {file_path.name}")


def main():
    """메인 실행 함수"""
    chunk_dir = Path("/Users/jaehaklee/qdrant_api_backend/__test__/sample_generated/부동산소유권등기소송/ocr_chunks")

    # 수정할 파일 패턴
    file_patterns = [
        "갑6호증_계좌거래내역_계약금_*.json",
        "갑7호증_계좌거래내역_중도금1차_*.json",
        "갑8호증_계좌거래내역_중도금2차_*.json",
        "갑9호증_계좌거래내역_잔금_*.json"
    ]

    main_trans_info = {
        "갑6호증": {"amount": 50000000, "memo": "서울특별시 강남구 테헤란로 123, 아크로타워 456동 789호 매매 계약금"},
        "갑7호증": {"amount": 150000000, "memo": "서울특별시 강남구 테헤란로 123, 아크로타워 456동 789호 매매 중도금1차"},
        "갑8호증": {"amount": 150000000, "memo": "서울특별시 강남구 테헤란로 123, 아크로타워 456동 789호 매매 중도금2차"},
        "갑9호증": {"amount": 150000000, "memo": "서울특별시 강남구 테헤란로 123, 아크로타워 456동 789호 매매 잔금"}
    }

    for pattern in file_patterns:
        files = sorted(chunk_dir.glob(pattern))
        for file_path in files:
            try:
                fix_account_chunk_file(file_path, main_trans_info)
            except Exception as e:
                print(f"❌ Error fixing {file_path.name}: {e}")

    print("\n✨ All account chunk files have been fixed!")


if __name__ == "__main__":
    main()
