#!/usr/bin/env python3
"""
을4호증_부동산담보대출서류 청크 파일 수정 스크립트

요약 파일과 정합성 있는 현실적인 주택담보대출 서류 내용 생성
- 피고: 이영희
- 대출기관: 국민은행 강남지점
- 대출금액: 200,000,000원
- 담보물: 서울특별시 강남구 테헤란로 123, 아크로타워 456동 789호
- 대출일: 2018년 3월 10일
- 근저당권 말소 기한: 2024년 6월 15일
"""

import json
from pathlib import Path
from typing import List, Dict
import uuid

# 기본 경로
BASE_DIR = Path("/Users/jaehaklee/qdrant_api_backend/__test__/sample_generated/부동산소유권등기소송/ocr_chunks")

# 14페이지 담보대출 서류 내용 구성
MORTGAGE_CONTENT = {
    1: [  # 표지
        {"text": "주 택 담 보 대 출 계 약 서", "type": "heading"},
        {"text": "국민은행 강남지점", "type": "heading"},
        {"text": "대출번호: KB-GN-2018-00347", "type": "body"},
        {"text": "계약일자: 2018년 3월 10일", "type": "body"},
    ],
    2: [  # 대출 기본 정보
        {"text": "제1조 (대출의 목적)", "type": "heading"},
        {"text": "본 대출은 주택구입 자금 용도로 사용하며, 그 외의 용도로 사용할 수 없다.", "type": "body"},
        {"text": "제2조 (당사자)", "type": "heading"},
        {"text": "대출자(이하 '갑'): 국민은행 강남지점", "type": "body"},
        {"text": "차주(이하 '을'): 이영희 (주민등록번호: 750215-2******)", "type": "body"},
        {"text": "주소: 서울특별시 강남구 테헤란로 123, 아크로타워 456동 789호", "type": "body"},
    ],
    3: [  # 대출 조건
        {"text": "제3조 (대출금액 및 조건)", "type": "heading"},
        {"text": "1. 대출원금: 금 이억원정 (₩200,000,000)", "type": "body"},
        {"text": "2. 대출기간: 2018년 3월 10일 ~ 2038년 3월 9일 (20년)", "type": "body"},
        {"text": "3. 대출금리: 연 3.45% (변동금리, 3개월 CD금리 + 가산금리 1.2%)", "type": "body"},
        {"text": "4. 상환방법: 원리금균등분할상환", "type": "body"},
        {"text": "5. 월 상환액: 금 일백십칠만원정 (₩1,170,000)", "type": "body"},
    ],
    4: [  # 담보물 정보
        {"text": "제4조 (담보물건의 표시)", "type": "heading"},
        {"text": "소재지: 서울특별시 강남구 테헤란로 123", "type": "body"},
        {"text": "건물명: 아크로타워", "type": "body"},
        {"text": "동·호수: 456동 789호", "type": "body"},
        {"text": "전용면적: 84.92㎡ (약 25.69평)", "type": "body"},
        {"text": "공급면적: 118.33㎡ (약 35.79평)", "type": "body"},
        {"text": "구조: 철근콘크리트조", "type": "body"},
        {"text": "용도: 아파트", "type": "body"},
    ],
    5: [  # 근저당권 설정
        {"text": "제5조 (근저당권 설정)", "type": "heading"},
        {"text": "1. 채권최고액: 금 이억육천만원정 (₩260,000,000)", "type": "body"},
        {"text": "   (대출원금 2억원의 130%)", "type": "body"},
        {"text": "2. 채권자: 국민은행 강남지점", "type": "body"},
        {"text": "3. 채무자: 이영희", "type": "body"},
        {"text": "4. 설정일자: 2018년 3월 12일", "type": "body"},
        {"text": "5. 접수번호: 2018년 3월 12일 제12345호", "type": "body"},
    ],
    6: [  # 상환 조건
        {"text": "제6조 (대출금의 상환)", "type": "heading"},
        {"text": "1. 을은 매월 10일까지 원리금을 갑이 지정한 계좌로 입금하여야 한다.", "type": "body"},
        {"text": "2. 지정계좌: 국민은행 강남지점 012-34-5678-901 (예금주: 이영희)", "type": "body"},
        {"text": "3. 연체 시 연체이자율: 대출금리 + 3% (연 6.45%)", "type": "body"},
        {"text": "4. 중도상환수수료: 대출 후 3년 이내 중도상환 시 잔액의 1.5%", "type": "body"},
    ],
    7: [  # 상환 일정표 1
        {"text": "제7조 (상환일정표) - 1차년도~5차년도", "type": "heading"},
        {"text": "2018년 4월~2019년 3월: 월 1,170,000원 (원금 620,000원, 이자 550,000원)", "type": "body"},
        {"text": "2019년 4월~2020년 3월: 월 1,170,000원 (원금 638,000원, 이자 532,000원)", "type": "body"},
        {"text": "2020년 4월~2021년 3월: 월 1,170,000원 (원금 656,000원, 이자 514,000원)", "type": "body"},
        {"text": "2021년 4월~2022년 3월: 월 1,170,000원 (원금 674,000원, 이자 496,000원)", "type": "body"},
        {"text": "2022년 4월~2023년 3월: 월 1,170,000원 (원금 693,000원, 이자 477,000원)", "type": "body"},
    ],
    8: [  # 상환 일정표 2
        {"text": "제7조 (상환일정표) - 6차년도~10차년도", "type": "heading"},
        {"text": "2023년 4월~2024년 3월: 월 1,170,000원 (원금 712,000원, 이자 458,000원)", "type": "body"},
        {"text": "2024년 4월~2025년 3월: 월 1,170,000원 (원금 732,000원, 이자 438,000원)", "type": "body"},
        {"text": "2025년 4월~2026년 3월: 월 1,170,000원 (원금 752,000원, 이자 418,000원)", "type": "body"},
        {"text": "2026년 4월~2027년 3월: 월 1,170,000원 (원금 773,000원, 이자 397,000원)", "type": "body"},
        {"text": "2027년 4월~2028년 3월: 월 1,170,000원 (원금 795,000원, 이자 375,000원)", "type": "body"},
    ],
    9: [  # 대출 현황
        {"text": "제8조 (대출잔액 현황) - 2024년 6월 기준", "type": "heading"},
        {"text": "1. 대출원금: 200,000,000원", "type": "body"},
        {"text": "2. 기 상환원금: 20,000,000원", "type": "body"},
        {"text": "3. 현재 대출잔액: 180,000,000원", "type": "body"},
        {"text": "4. 연체횟수: 0회 (정상 상환 중)", "type": "body"},
        {"text": "5. 최종 상환일: 2024년 6월 10일", "type": "body"},
    ],
    10: [  # 특약 사항
        {"text": "제9조 (특약사항)", "type": "heading"},
        {"text": "1. 본 부동산을 제3자에게 매도할 경우, 을은 잔여 대출금을 일시 상환하여야 한다.", "type": "body"},
        {"text": "2. 매수인과의 합의에 따라 근저당권 말소 의무를 부담할 수 있다.", "type": "body"},
        {"text": "3. 근저당권 말소 시 을은 갑에게 서면으로 통지하고 말소등기 서류를 제출하여야 한다.", "type": "body"},
        {"text": "4. 을이 근저당권 말소 의무를 이행하지 않을 경우, 매수인은 매매대금 중 대출잔액 상당액의 지급을 거절할 수 있다.", "type": "body"},
    ],
    11: [  # 계약 불이행 조항
        {"text": "제10조 (기한의 이익 상실)", "type": "heading"},
        {"text": "다음 각 호의 사유가 발생한 경우, 을은 기한의 이익을 상실하고 즉시 대출원리금 전액을 상환하여야 한다:", "type": "body"},
        {"text": "1. 원리금을 2회 이상 연체한 경우", "type": "body"},
        {"text": "2. 담보물건에 대한 압류, 가압류, 가처분 등 강제집행이 개시된 경우", "type": "body"},
        {"text": "3. 을의 신용상태가 현저히 악화된 경우", "type": "body"},
        {"text": "4. 담보물건이 멸실 또는 훼손되어 담보가치가 현저히 감소한 경우", "type": "body"},
    ],
    12: [  # 근저당권 말소 관련
        {"text": "제11조 (근저당권 말소)", "type": "heading"},
        {"text": "1. 대출원리금이 전액 상환된 경우, 갑은 근저당권설정등기 말소에 필요한 서류를 을에게 교부한다.", "type": "body"},
        {"text": "2. 을은 매매계약에서 정한 근저당권 말소 기한(2024년 6월 15일)까지 대출잔액을 상환하고 근저당권 말소를 완료하여야 한다.", "type": "body"},
        {"text": "3. 말소 기한 경과 시 매수인은 매매계약을 해제하거나 대출잔액 상당의 매매대금 지급을 거절할 수 있다.", "type": "body"},
        {"text": "4. 이로 인한 손해는 전적으로 을이 부담한다.", "type": "body"},
    ],
    13: [  # 서명란
        {"text": "제12조 (관할법원)", "type": "heading"},
        {"text": "본 계약과 관련한 분쟁은 대출자의 본점 소재지 법원을 제1심 관할법원으로 한다.", "type": "body"},
        {"text": "", "type": "body"},
        {"text": "2018년 3월 10일", "type": "body"},
        {"text": "", "type": "body"},
        {"text": "대출자(갑): 국민은행 강남지점", "type": "body"},
        {"text": "            지점장: 박지영 (인)", "type": "body"},
    ],
    14: [  # 서명 완료
        {"text": "", "type": "body"},
        {"text": "차주(을):  이영희 (인)", "type": "body"},
        {"text": "          주민등록번호: 750215-2******", "type": "body"},
        {"text": "          주소: 서울특별시 강남구 테헤란로 123, 아크로타워 456동 789호", "type": "body"},
        {"text": "          연락처: 010-1234-5678", "type": "body"},
        {"text": "", "type": "body"},
        {"text": "[별첨]", "type": "heading"},
        {"text": "1. 주민등록등본 1부", "type": "body"},
        {"text": "2. 등기사항전부증명서(건물) 1부", "type": "body"},
        {"text": "3. 소득증빙서류 1부", "type": "body"},
    ],
}


def create_paragraph(para_id: str, idx: int, text: str, page: int, para_type: str) -> Dict:
    """문단 객체 생성"""
    import random

    # 문단 타입에 따른 y 좌표 범위
    if para_type == "heading":
        y_base = random.randint(100, 300)
        height = random.randint(60, 80)
    else:
        y_base = random.randint(200, 1100)
        height = random.randint(45, 55)

    return {
        "paragraph_id": para_id,
        "idx_in_page": idx,
        "text": text,
        "page": page,
        "bbox": {
            "x": round(random.uniform(180, 220), 2),
            "y": round(y_base + (idx * 80), 2),
            "width": round(random.uniform(1200, 1330), 2),
            "height": height
        },
        "type": para_type,
        "confidence_score": round(random.uniform(0.91, 0.98), 2)
    }


def generate_chunk_content(pages: List[int], chunk_number: int) -> tuple:
    """청크에 포함될 페이지들의 내용 생성"""
    import random

    paragraph_texts = []
    paragraphs = []

    for page in pages:
        page_content = MORTGAGE_CONTENT.get(page, [])

        for idx, item in enumerate(page_content):
            para_id = f"para-036-{chunk_number:03d}-{pages.index(page):03d}-{idx}"
            text = item["text"]
            para_type = item["type"]

            if text:  # 빈 문자열 제외
                paragraph_texts.append(text)
                paragraphs.append(create_paragraph(para_id, idx, text, page, para_type))

    return paragraph_texts, paragraphs


def create_chunk_file(pages: List[int], chunk_number: int, created_date: str):
    """청크 파일 생성"""
    paragraph_texts, paragraphs = generate_chunk_content(pages, chunk_number)

    chunk_data = {
        "chunk_id": str(uuid.uuid4()),
        "file_id": 36,
        "project_id": 1001,
        "storage_file_name": "exhibit_b4_mortgage_docs.pdf",
        "original_file_name": "을4호증_부동산담보대출서류.pdf",
        "mime_type": "application/pdf",
        "total_pages": 14,
        "processing_duration_seconds": 0,
        "language": "ko",
        "pages": pages,
        "chunk_number": chunk_number,
        "paragraph_texts": paragraph_texts,
        "chunk_content": {
            "paragraphs": paragraphs
        },
        "page_dimensions": [
            {
                "page": p,
                "width": 1681,
                "height": 2379
            }
            for p in pages
        ],
        "created_at": created_date
    }

    # 파일명 생성
    if len(pages) == 2:
        filename = f"을4호증_부동산담보대출서류_p{pages[0]}-{pages[1]}.json"
    else:
        filename = f"을4호증_부동산담보대출서류_p{pages[0]}-{pages[-1]}.json"

    filepath = BASE_DIR / filename

    # 파일 저장
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(chunk_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Created: {filename} (pages: {pages}, paragraphs: {len(paragraphs)})")


def main():
    """메인 실행 함수"""
    print("🔧 을4호증 담보대출서류 청크 파일 재생성 시작\n")

    # 3페이지 윈도우 청크 정의 (14페이지)
    chunks = [
        ([1, 2, 3], 1, "2024-08-02T00:00:00+00:00"),
        ([3, 4, 5], 2, "2024-08-03T00:00:00+00:00"),
        ([5, 6, 7], 3, "2024-08-04T00:00:00+00:00"),
        ([7, 8, 9], 4, "2024-08-05T00:00:00+00:00"),
        ([9, 10, 11], 5, "2024-08-06T00:00:00+00:00"),
        ([11, 12, 13], 6, "2024-08-07T00:00:00+00:00"),
        ([13, 14], 7, "2024-08-08T00:00:00+00:00"),  # 마지막 2페이지만
    ]

    for pages, chunk_num, created_at in chunks:
        create_chunk_file(pages, chunk_num, created_at)

    print("\n✨ 모든 청크 파일 재생성 완료!")
    print("\n📊 생성 요약:")
    print(f"  - 총 페이지: 14페이지")
    print(f"  - 총 청크: 7개")
    print(f"  - 윈도우 크기: 3페이지 (마지막 2페이지)")
    print(f"  - 겹침: 1페이지")


if __name__ == "__main__":
    main()
