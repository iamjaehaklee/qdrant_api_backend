#!/usr/bin/env python3
"""
변론녹취록 OCR 청크 파일 수정 스크립트

문제점:
1. 같은 문자열 반복
2. 한 페이지당 2개 문단만 존재 (비현실적)
3. 요약본과 내용 불일치

해결:
- 요약본 내용에 맞춰 현실적인 법정 녹취록 생성
- 페이지당 8-15개 문단으로 증가
- 실제 변론 과정 반영 (개회, 진술, 증거제출, 쟁점정리, 폐회)
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
import random

# 변론녹취록 템플릿 - 실제 법정 진행 순서대로
HEARING_TEMPLATES = {
    "1회_0903": {
        "case_number": "2024가단123456",
        "date": "2024년 9월 3일 14:00",
        "court": "서울중앙지방법원 민사12단독",
        "judge": "정재판 판사",
        "plaintiff": "김철수",
        "plaintiff_attorney": "김변호사",
        "defendant": "이영희",
        "defendant_attorney": "이변호사",
        "phases": [
            {
                "title": "개정 및 출석 확인",
                "content": [
                    "재판장: 제1회 변론기일을 개정하겠습니다.",
                    "재판장: 원고 본인 김철수님, 소송대리인 김변호사님 출석하셨습니까?",
                    "원고 소송대리인: 예, 출석하였습니다.",
                    "재판장: 피고 본인 이영희님, 소송대리인 이변호사님은?",
                    "피고 소송대리인: 예, 모두 출석하였습니다."
                ]
            },
            {
                "title": "소장 진술 요지",
                "content": [
                    "재판장: 원고 측에서 소장 진술 요지를 간략히 설명해 주시기 바랍니다.",
                    "원고 소송대리인: 예, 말씀드리겠습니다. 원고는 2023년 5월 15일 피고와 서울시 강남구 소재 부동산에 대한 매매계약을 체결하였습니다.",
                    "원고 소송대리인: 매매대금은 총 5억원으로, 계약금 5천만원은 계약 당일, 중도금 2억원은 2023년 7월 15일, 잔금 2억5천만원은 2023년 9월 15일 각 지급하였습니다.",
                    "원고 소송대리인: 그러나 피고는 소유권이전등기 및 부동산 인도를 거부하고 있어, 이에 등기이전 및 인도를 구하는 소를 제기하게 되었습니다.",
                    "재판장: 알겠습니다. 매매대금 지급 사실을 입증할 증거는 제출하셨습니까?",
                    "원고 소송대리인: 예, 갑 제6호증부터 갑 제9호증까지 계좌거래내역을 제출하였습니다.",
                ]
            },
            {
                "title": "답변서 진술 요지",
                "content": [
                    "재판장: 피고 측 답변서 진술 요지를 설명해 주시기 바랍니다.",
                    "피고 소송대리인: 예, 말씀드리겠습니다. 매매계약 체결 사실 및 대금 수령 사실은 인정합니다.",
                    "피고 소송대리인: 다만, 쌍방은 2023년 6월 1일 보충합의서를 작성하였고, 그 특약사항에서 원고가 기존 임차인을 퇴거시킬 것을 조건으로 하였습니다.",
                    "피고 소송대리인: 그러나 원고는 임차인 퇴거를 완료하지 못하였고, 이는 계약의 중요한 부분이므로 등기이전을 거부할 권리가 있습니다.",
                    "재판장: 보충합의서는 증거로 제출하셨습니까?",
                    "피고 소송대리인: 아직 제출하지 못했습니다. 다음 기일까지 제출하겠습니다.",
                ]
            },
            {
                "title": "원고 측 반박",
                "content": [
                    "재판장: 원고 측에서 피고 주장에 대해 의견 있으십니까?",
                    "원고 소송대리인: 예, 피고가 주장하는 보충합의서는 원고가 작성하거나 서명한 사실이 없습니다.",
                    "원고 소송대리인: 또한 매매계약서에는 그러한 특약사항이 전혀 기재되어 있지 않습니다.",
                    "원고 소송대리인: 피고의 주장은 사후에 조작된 것으로 보이며, 이는 신의성실의 원칙에도 반합니다.",
                ]
            },
            {
                "title": "쟁점 정리",
                "content": [
                    "재판장: 양측 주장을 들어보니 이 사건의 핵심 쟁점은 보충합의서의 진정성립 여부로 보입니다.",
                    "재판장: 피고 측에서는 다음 기일까지 보충합의서 원본을 제출하시고, 원고 측에서는 이에 대한 의견을 준비서면으로 제출해 주시기 바랍니다.",
                    "재판장: 또한 계약 당시 교환된 문자메시지나 카카오톡 대화 내용이 있다면 함께 제출해 주시기 바랍니다.",
                ]
            },
            {
                "title": "다음 기일 지정 및 폐정",
                "content": [
                    "재판장: 다음 변론기일은 2024년 10월 8일 오후 2시로 지정하겠습니다.",
                    "재판장: 양측 모두 준비서면을 기일 7일 전까지 제출해 주시기 바랍니다.",
                    "재판장: 더 하실 말씀 있으십니까?",
                    "원고 소송대리인: 없습니다.",
                    "피고 소송대리인: 없습니다.",
                    "재판장: 그럼 오늘 변론기일을 마치겠습니다.",
                ]
            }
        ]
    },
    "2회_1008": {
        "case_number": "2024가단123456",
        "date": "2024년 10월 8일 14:00",
        "court": "서울중앙지방법원 민사12단독",
        "judge": "정재판 판사",
        "plaintiff": "김철수",
        "plaintiff_attorney": "김변호사",
        "defendant": "이영희",
        "defendant_attorney": "이변호사",
        "phases": [
            {
                "title": "개정 및 출석 확인",
                "content": [
                    "재판장: 제2회 변론기일을 개정하겠습니다.",
                    "재판장: 양측 모두 출석하셨습니까?",
                    "원고 소송대리인: 예, 출석하였습니다.",
                    "피고 소송대리인: 예, 출석하였습니다.",
                ]
            },
            {
                "title": "피고 측 증거 제출",
                "content": [
                    "재판장: 피고 측에서 보충합의서를 제출하셨습니까?",
                    "피고 소송대리인: 예, 을 제1호증으로 보충합의서 원본을 제출하였습니다.",
                    "재판장: 원고 측에서 이 서면의 진정성립을 인정하십니까?",
                    "원고 소송대리인: 아니요, 부인합니다. 해당 서면에 있는 서명은 원고의 것이 아닙니다.",
                    "원고 소송대리인: 필적 감정을 신청하고자 합니다.",
                ]
            },
            {
                "title": "피고 측 추가 주장",
                "content": [
                    "피고 소송대리인: 재판장님, 보충합의서는 원고가 직접 서명한 것이 맞습니다.",
                    "피고 소송대리인: 또한 을 제2호증 내지 을 제5호증으로 카카오톡 대화 내용을 제출하였는데, 이를 보시면 원고가 임차인 퇴거에 대해 논의한 사실을 확인할 수 있습니다.",
                    "피고 소송대리인: 특히 2023년 6월 5일 대화에서 원고가 '임차인 문제는 제가 해결하겠습니다'라고 명시하였습니다.",
                ]
            },
            {
                "title": "원고 측 반박 및 증거 제출",
                "content": [
                    "원고 소송대리인: 재판장님, 피고가 제출한 카카오톡 대화는 맥락이 왜곡되었습니다.",
                    "원고 소송대리인: 갑 제14호증부터 갑 제15호증으로 전체 카카오톡 대화 내용을 제출합니다.",
                    "원고 소송대리인: 이를 보시면 원고는 단순히 임차인과 인사를 나누겠다는 의미였지, 퇴거시키겠다는 의미가 아니었습니다.",
                    "원고 소송대리인: 또한 갑 제16호증 문자메시지를 보시면, 피고가 '등기는 잔금 입금 즉시 이전하겠다'고 명시하였습니다.",
                ]
            },
            {
                "title": "필적 감정 신청 및 증인 신청",
                "content": [
                    "재판장: 원고 측에서 필적 감정을 신청하셨는데, 피고 측 의견은 어떠십니까?",
                    "피고 소송대리인: 필적 감정은 불필요하다고 생각하나, 재판부 판단에 따르겠습니다.",
                    "재판장: 필적 감정은 이 사건 쟁점 해결에 필요하다고 보이므로, 서울지방법원 감정인 명부에서 필적 감정인을 선정하도록 하겠습니다.",
                    "원고 소송대리인: 감사합니다. 또한 계약 당시 중개인이었던 박공인을 증인으로 신청합니다.",
                    "피고 소송대리인: 저희도 증인으로 신청하려던 참이었습니다. 이의 없습니다.",
                ]
            },
            {
                "title": "다음 기일 지정 및 폐정",
                "content": [
                    "재판장: 필적 감정에 시간이 소요되므로, 다음 변론기일은 2024년 11월 5일 오후 2시로 지정하겠습니다.",
                    "재판장: 증인 박공인은 차기 기일에 출석하도록 조치해 주시기 바랍니다.",
                    "재판장: 감정 결과가 나오는 대로 양측에 통지하겠습니다.",
                    "재판장: 더 하실 말씀 있으십니까?",
                    "원고 소송대리인: 없습니다.",
                    "피고 소송대리인: 없습니다.",
                    "재판장: 제2회 변론기일을 마치겠습니다.",
                ]
            }
        ]
    },
    "3회_1105": {
        "case_number": "2024가단123456",
        "date": "2024년 11월 5일 14:00",
        "court": "서울중앙지방법원 민사12단독",
        "judge": "정재판 판사",
        "plaintiff": "김철수",
        "plaintiff_attorney": "김변호사",
        "defendant": "이영희",
        "defendant_attorney": "이변호사",
        "phases": [
            {
                "title": "개정 및 출석 확인",
                "content": [
                    "재판장: 제3회 변론기일을 개정하겠습니다.",
                    "재판장: 양측 본인 및 소송대리인 모두 출석하셨습니까?",
                    "원고 소송대리인: 예, 출석하였습니다.",
                    "피고 소송대리인: 예, 출석하였습니다.",
                    "재판장: 증인 박공인님도 출석하셨습니까?",
                    "증인 박공인: 예, 출석하였습니다.",
                ]
            },
            {
                "title": "필적 감정 결과 확인",
                "content": [
                    "재판장: 먼저 필적 감정 결과를 확인하겠습니다. 감정인 김감정 전문가의 감정서가 제출되었습니다.",
                    "재판장: 감정 결과, 보충합의서상 서명은 원고 김철수의 필적과 상이하다는 결론입니다.",
                    "재판장: 피고 측에서 이 감정 결과에 대해 의견 있으십니까?",
                    "피고 소송대리인: 재판장님, 감정 결과를 존중하나, 원고가 의도적으로 필체를 바꿔 서명했을 가능성도 있습니다.",
                    "원고 소송대리인: 그러한 주장은 근거가 없습니다. 저희는 애초에 그 서면에 서명한 적이 없습니다.",
                ]
            },
            {
                "title": "증인 신문 - 박공인",
                "content": [
                    "재판장: 증인 박공인님, 선서해 주시기 바랍니다.",
                    "증인 박공인: 양심에 따라 숨김과 보탬이 없이 사실 그대로 말하고 만일 거짓말이 있으면 위증의 벌을 받기로 맹세합니다.",
                    "재판장: 증인은 이 사건 매매계약 중개를 담당하셨습니까?",
                    "증인 박공인: 예, 그렇습니다.",
                    "재판장: 보충합의서 작성 과정을 목격하셨습니까?",
                    "증인 박공인: 아니요, 보충합의서는 본 적이 없습니다. 저는 최초 매매계약서 작성 시에만 입회하였습니다.",
                    "원고 소송대리인: 증인께서는 계약 당시 임차인 퇴거에 관한 특약이 논의되었습니까?",
                    "증인 박공인: 아니요, 그런 논의는 없었습니다. 매매계약서에 기재된 내용이 전부였습니다.",
                    "피고 소송대리인: 증인은 계약 이후에도 당사자들과 연락하셨습니까?",
                    "증인 박공인: 예, 몇 차례 연락은 받았으나 모두 등기이전 일정에 관한 것이었습니다.",
                ]
            },
            {
                "title": "최종 변론",
                "content": [
                    "재판장: 양측에서 최종 변론해 주시기 바랍니다.",
                    "원고 소송대리인: 재판장님, 필적 감정 결과와 증인 증언을 통해 피고 주장의 보충합의서가 허위임이 명백히 드러났습니다.",
                    "원고 소송대리인: 원고는 매매대금을 모두 지급하였고, 피고는 아무런 정당한 사유 없이 등기이전을 거부하고 있습니다.",
                    "원고 소송대리인: 청구 취지대로 판결해 주실 것을 간곡히 요청드립니다.",
                    "피고 소송대리인: 재판장님, 비록 필적 감정 결과는 그러하나, 카카오톡 대화 내용을 보면 원고가 임차인 문제를 해결하기로 했음이 분명합니다.",
                    "피고 소송대리인: 원고의 의무 불이행이 있었으므로, 피고의 이행 거부는 정당합니다.",
                ]
            },
            {
                "title": "변론 종결 및 선고일 지정",
                "content": [
                    "재판장: 양측 주장과 제출된 증거를 충분히 검토하였습니다.",
                    "재판장: 더 이상 심리할 사항이 없다고 보이므로, 변론을 종결하겠습니다.",
                    "재판장: 판결 선고일은 2024년 11월 26일 오후 2시로 지정합니다.",
                    "재판장: 판결문은 선고일에 당사자에게 송달됩니다.",
                    "재판장: 더 하실 말씀 있으십니까?",
                    "원고 소송대리인: 없습니다.",
                    "피고 소송대리인: 없습니다.",
                    "재판장: 제3회 변론기일을 마치겠습니다.",
                ]
            }
        ]
    }
}


def generate_realistic_paragraphs(
    hearing_key: str,
    start_page: int,
    end_page: int,
    file_id: int
) -> List[Dict]:
    """페이지 범위에 맞는 현실적인 문단 생성"""

    template = HEARING_TEMPLATES[hearing_key]
    total_pages = 20 if "1회" in hearing_key else (18 if "2회" in hearing_key else 19)

    paragraphs = []
    para_global_idx = 0

    # 각 페이지에 배치할 내용 결정
    for page_num in range(start_page, end_page + 1):
        page_idx = page_num - 1
        idx_in_page = 0

        # 첫 페이지: 사건 정보
        if page_num == 1:
            paragraphs.append({
                "paragraph_id": f"para-{file_id:03d}-{para_global_idx:03d}-{page_idx:03d}-{idx_in_page}",
                "idx_in_page": idx_in_page,
                "text": f"사건번호: {template['case_number']}",
                "page": page_num,
                "bbox": {"x": 200 + random.uniform(-20, 20), "y": 100 + random.uniform(-10, 10),
                        "width": 1200 + random.uniform(-50, 50), "height": 40},
                "type": "header",
                "confidence_score": round(random.uniform(0.92, 0.98), 2)
            })
            idx_in_page += 1
            para_global_idx += 1

            paragraphs.append({
                "paragraph_id": f"para-{file_id:03d}-{para_global_idx:03d}-{page_idx:03d}-{idx_in_page}",
                "idx_in_page": idx_in_page,
                "text": f"재판부: {template['court']} {template['judge']}",
                "page": page_num,
                "bbox": {"x": 200 + random.uniform(-20, 20), "y": 150 + random.uniform(-10, 10),
                        "width": 1200 + random.uniform(-50, 50), "height": 40},
                "type": "body",
                "confidence_score": round(random.uniform(0.92, 0.98), 2)
            })
            idx_in_page += 1
            para_global_idx += 1

            paragraphs.append({
                "paragraph_id": f"para-{file_id:03d}-{para_global_idx:03d}-{page_idx:03d}-{idx_in_page}",
                "idx_in_page": idx_in_page,
                "text": f"일시: {template['date']}",
                "page": page_num,
                "bbox": {"x": 200 + random.uniform(-20, 20), "y": 200 + random.uniform(-10, 10),
                        "width": 1200 + random.uniform(-50, 50), "height": 40},
                "type": "body",
                "confidence_score": round(random.uniform(0.92, 0.98), 2)
            })
            idx_in_page += 1
            para_global_idx += 1

            paragraphs.append({
                "paragraph_id": f"para-{file_id:03d}-{para_global_idx:03d}-{page_idx:03d}-{idx_in_page}",
                "idx_in_page": idx_in_page,
                "text": f"원고: {template['plaintiff']} (대리인: {template['plaintiff_attorney']})",
                "page": page_num,
                "bbox": {"x": 200 + random.uniform(-20, 20), "y": 250 + random.uniform(-10, 10),
                        "width": 1200 + random.uniform(-50, 50), "height": 40},
                "type": "body",
                "confidence_score": round(random.uniform(0.92, 0.98), 2)
            })
            idx_in_page += 1
            para_global_idx += 1

            paragraphs.append({
                "paragraph_id": f"para-{file_id:03d}-{para_global_idx:03d}-{page_idx:03d}-{idx_in_page}",
                "idx_in_page": idx_in_page,
                "text": f"피고: {template['defendant']} (대리인: {template['defendant_attorney']})",
                "page": page_num,
                "bbox": {"x": 200 + random.uniform(-20, 20), "y": 300 + random.uniform(-10, 10),
                        "width": 1200 + random.uniform(-50, 50), "height": 40},
                "type": "body",
                "confidence_score": round(random.uniform(0.92, 0.98), 2)
            })
            idx_in_page += 1
            para_global_idx += 1

        # 각 페이지에 단계별 내용 배치
        phase_idx = min((page_num - 1) // 3, len(template['phases']) - 1)
        phase = template['phases'][phase_idx]

        # 단계 제목
        if page_num % 3 == 1 or page_num == 1:
            paragraphs.append({
                "paragraph_id": f"para-{file_id:03d}-{para_global_idx:03d}-{page_idx:03d}-{idx_in_page}",
                "idx_in_page": idx_in_page,
                "text": f"[{phase['title']}]",
                "page": page_num,
                "bbox": {"x": 200 + random.uniform(-20, 20), "y": 350 + idx_in_page * 60 + random.uniform(-10, 10),
                        "width": 1200 + random.uniform(-50, 50), "height": 45},
                "type": "body",
                "confidence_score": round(random.uniform(0.90, 0.97), 2)
            })
            idx_in_page += 1
            para_global_idx += 1

        # 해당 단계의 대화 내용 (페이지당 8-12개 문단)
        content_start = ((page_num - 1) % 3) * 4
        content_end = min(content_start + random.randint(8, 12), len(phase['content']))

        for content_text in phase['content'][content_start:content_end]:
            y_pos = 400 + idx_in_page * 55
            if y_pos > 2200:  # 페이지 넘김
                break

            paragraphs.append({
                "paragraph_id": f"para-{file_id:03d}-{para_global_idx:03d}-{page_idx:03d}-{idx_in_page}",
                "idx_in_page": idx_in_page,
                "text": content_text,
                "page": page_num,
                "bbox": {"x": 200 + random.uniform(-20, 20), "y": y_pos + random.uniform(-10, 10),
                        "width": 1200 + random.uniform(-50, 50), "height": 50 + random.uniform(-5, 5)},
                "type": "body",
                "confidence_score": round(random.uniform(0.88, 0.97), 2)
            })
            idx_in_page += 1
            para_global_idx += 1

    return paragraphs


def fix_hearing_transcript_file(file_path: str) -> bool:
    """변론녹취록 청크 파일 수정"""

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 파일명에서 hearing 키 추출
        filename = os.path.basename(file_path)
        if "1회_0903" in filename:
            hearing_key = "1회_0903"
        elif "2회_1008" in filename:
            hearing_key = "2회_1008"
        elif "3회_1105" in filename:
            hearing_key = "3회_1105"
        else:
            print(f"Unknown hearing type: {filename}")
            return False

        # 페이지 범위 추출
        pages = data['pages']
        start_page = pages[0]
        end_page = pages[-1]
        file_id = data['file_id']

        # 새로운 문단 생성
        new_paragraphs = generate_realistic_paragraphs(hearing_key, start_page, end_page, file_id)

        # paragraph_texts 업데이트
        data['paragraph_texts'] = [p['text'] for p in new_paragraphs]

        # chunk_content 업데이트
        data['chunk_content']['paragraphs'] = new_paragraphs

        # 파일 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ Fixed: {filename} ({len(new_paragraphs)} paragraphs)")
        return True

    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False


def main():
    """모든 변론녹취록 파일 수정"""

    base_dir = Path("/Users/jaehaklee/qdrant_api_backend/__test__/sample_generated/부동산소유권등기소송/ocr_chunks")

    # 변론녹취록 파일만 필터링
    hearing_files = list(base_dir.glob("변론녹취록*.json"))

    print(f"Found {len(hearing_files)} hearing transcript files")

    success_count = 0
    for file_path in sorted(hearing_files):
        if fix_hearing_transcript_file(str(file_path)):
            success_count += 1

    print(f"\n{'='*60}")
    print(f"✅ Successfully fixed: {success_count}/{len(hearing_files)} files")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
