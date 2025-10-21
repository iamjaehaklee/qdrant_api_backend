#!/usr/bin/env python3
"""
Fix OCR chunk files for KakaoTalk conversations (갑14호증, 갑15호증)
- Remove repetition across pages
- Create realistic progressive conversation flow
- Ensure 3-page window structure
"""

import json
from pathlib import Path
from datetime import datetime, timedelta


BASE_DIR = Path(__file__).parent.parent / "__test__" / "sample_generated" / "부동산소유권등기소송" / "ocr_chunks"


def generate_kakao_conversation_갑14호증():
    """Generate realistic KakaoTalk conversation for 갑14호증 (계약논의)"""
    conversation = [
        # Initial contact and property interest
        ("2024-02-20 14:30", "원고", "안녕하세요. 테헤란로 아크로타워 매물 보고 연락드립니다."),
        ("2024-02-20 14:32", "피고", "네, 안녕하세요. 관심 가져주셔서 감사합니다."),
        ("2024-02-20 14:35", "원고", "현재 전세 들어가 있나요?"),
        ("2024-02-20 14:37", "피고", "네, 현재 전세 임차인 있는데 3월 초 계약 만료됩니다."),
        ("2024-02-20 14:40", "원고", "그럼 3월 중순쯤 인도 가능하겠네요?"),
        ("2024-02-20 14:42", "피고", "네, 임차인이 이미 이사 준비 중이라 3월 15일경 가능합니다."),

        # Price negotiation
        ("2024-02-22 10:15", "원고", "매매가는 얼마로 생각하세요?"),
        ("2024-02-22 10:20", "피고", "5억5천에 내놨습니다."),
        ("2024-02-22 10:25", "원고", "조금 높은 것 같은데 5억 안 되나요?"),
        ("2024-02-22 10:30", "피고", "음... 5억은 너무 낮은 것 같고요."),
        ("2024-02-22 10:35", "원고", "요즘 시세가 많이 내렸잖아요."),
        ("2024-02-22 10:40", "피고", "그래도 이 건물은 역세권이고 학군도 좋아서..."),

        # Agreement approaching
        ("2024-02-25 09:10", "원고", "5억2천 어떠세요?"),
        ("2024-02-25 09:15", "피고", "좀 더 생각해보겠습니다."),
        ("2024-02-26 16:20", "피고", "5억으로 하시죠."),
        ("2024-02-26 16:22", "원고", "네? 정말요?"),
        ("2024-02-26 16:25", "피고", "네, 빨리 정리하고 싶어서요."),
        ("2024-02-26 16:27", "원고", "감사합니다! 그럼 언제 계약할까요?"),

        # Tenant status
        ("2024-02-28 15:30", "피고", "임차인이 완전히 이사 나갔습니다."),
        ("2024-02-28 15:32", "원고", "그럼 이번 주말에 한번 더 보러 가도 될까요?"),
        ("2024-02-28 15:35", "피고", "네, 토요일 오전 괜찮으세요?"),
        ("2024-02-28 15:37", "원고", "네, 10시에 뵙겠습니다."),

        # Contract preparation
        ("2024-03-02 11:00", "원고", "집 잘 봤습니다. 계약 진행하고 싶은데요."),
        ("2024-03-02 11:05", "피고", "네, 좋습니다. 공인중개사 통하시나요?"),
        ("2024-03-02 11:10", "원고", "네, 제가 아는 분 계십니다."),
        ("2024-03-02 11:15", "피고", "그럼 그분 통해서 진행하시죠."),

        # Final price confirmation
        ("2024-03-10 10:15", "원고", "매매대금은 5억 맞죠?"),
        ("2024-03-10 10:17", "피고", "네, 5억 맞습니다."),
        ("2024-03-10 10:20", "원고", "계약금 10%, 중도금 60%, 잔금 30% 이렇게 하면 될까요?"),
        ("2024-03-10 10:25", "피고", "네, 그렇게 하시죠."),
        ("2024-03-10 10:30", "원고", "중도금은 2회 분할해도 될까요?"),
        ("2024-03-10 10:32", "피고", "네, 괜찮습니다."),

        # Contract date setting
        ("2024-03-12 14:00", "원고", "3월 15일 계약 가능하세요?"),
        ("2024-03-12 14:05", "피고", "네, 가능합니다."),
        ("2024-03-12 14:10", "원고", "오전 10시에 공인중개사 사무실에서 뵙겠습니다."),
        ("2024-03-12 14:12", "피고", "네, 알겠습니다. 인감증명서 준비해 가겠습니다."),
        ("2024-03-12 14:15", "원고", "네, 저도 신분증하고 도장 챙겨가겠습니다."),

        # Registration documents
        ("2024-03-13 16:30", "피고", "등기부등본 보내드립니다. (사진)"),
        ("2024-03-13 16:35", "원고", "감사합니다. 근저당 설정된 것 보이는데 이거 말소하시는 거죠?"),
        ("2024-03-13 16:40", "피고", "네, 잔금 받으면 바로 말소하겠습니다."),
        ("2024-03-13 16:45", "원고", "알겠습니다. 그럼 내일 뵙겠습니다."),
        ("2024-03-13 16:47", "피고", "네, 내일 뵙겠습니다."),
    ]
    return conversation


def generate_kakao_conversation_갑15호증():
    """Generate realistic KakaoTalk conversation for 갑15호증 (이행요구)"""
    conversation = [
        # After contract - payment confirmation
        ("2024-03-15 11:30", "원고", "계약 잘 마쳤습니다. 계약금 5천만원 송금했습니다."),
        ("2024-03-15 11:35", "피고", "네, 확인했습니다. 감사합니다."),

        # First interim payment
        ("2024-04-20 10:00", "원고", "중도금 1차 1억5천 송금했습니다."),
        ("2024-04-20 10:05", "피고", "네, 확인했습니다."),

        # Second interim payment
        ("2024-05-20 09:30", "원고", "중도금 2차 1억5천 송금했습니다."),
        ("2024-05-20 09:35", "피고", "네, 확인했습니다."),

        # Final payment approaching
        ("2024-06-10 14:00", "원고", "잔금일 6월 15일 맞죠?"),
        ("2024-06-10 14:05", "피고", "네, 맞습니다."),
        ("2024-06-10 14:10", "원고", "등기 서류 준비되셨나요?"),
        ("2024-06-10 14:15", "피고", "네, 준비 중입니다."),

        # Final payment day
        ("2024-06-15 09:00", "원고", "오늘 잔금 2억 송금하겠습니다."),
        ("2024-06-15 09:05", "피고", "네, 확인 후 연락드리겠습니다."),
        ("2024-06-15 10:30", "원고", "송금 완료했습니다. 확인 부탁드립니다."),
        ("2024-06-15 10:35", "피고", "확인했습니다."),

        # Request for documents (no response)
        ("2024-06-15 10:40", "원고", "등기 서류 언제 주시나요?"),
        ("2024-06-15 14:00", "원고", "서류 준비되셨나요?"),
        ("2024-06-15 17:00", "원고", "연락 부탁드립니다."),

        # Next day - still no response
        ("2024-06-16 09:00", "원고", "어제 연락 못 받으셨나요?"),
        ("2024-06-16 12:00", "원고", "등기 서류 언제 받을 수 있을까요?"),
        ("2024-06-16 16:00", "원고", "답변 부탁드립니다."),

        # Urgent requests
        ("2024-06-18 10:00", "원고", "이틀째 연락이 안 되는데 무슨 일 있으신가요?"),
        ("2024-06-18 14:00", "원고", "법적 조치 취하기 전에 연락 주시기 바랍니다."),
        ("2024-06-18 18:00", "원고", "내일까지 서류 안 주시면 변호사 통해 진행하겠습니다."),

        # Final demands
        ("2024-06-22 09:00", "원고", "더 이상 기다릴 수 없습니다. 서류 즉시 주십시오."),
        ("2024-06-22 12:00", "원고", "오늘 중으로 연락 없으면 내용증명 발송하겠습니다."),
        ("2024-06-22 17:00", "원고", "연락 주시기 바랍니다."),
    ]
    return conversation


def create_paragraph_texts_from_conversation(conversations, start_idx, end_idx, page_numbers):
    """Create paragraph_texts from conversation slice"""
    texts = []
    for page_num in page_numbers:
        texts.append(f"카카오톡 대화 내역 - {page_num}페이지")
        texts.append("")  # Empty line

    for conv in conversations[start_idx:end_idx]:
        timestamp, sender, message = conv
        texts.append(f"[{timestamp}] {sender}: {message}")

    return texts


def create_paragraph_objects_from_conversation(conversations, start_idx, end_idx, pages, file_id, chunk_num):
    """Create paragraph objects from conversation slice"""
    paragraphs = []
    para_idx = 0

    for page_idx, page_num in enumerate(pages):
        # Page header
        paragraphs.append({
            "paragraph_id": f"para-{file_id:03d}-{chunk_num:03d}-{page_num:03d}-{para_idx}",
            "idx_in_page": para_idx,
            "text": f"카카오톡 대화 내역 - {page_num}페이지",
            "page": page_num,
            "bbox": {"x": 200, "y": 100, "width": 1200, "height": 40},
            "type": "header",
            "confidence_score": 0.98
        })
        para_idx += 1

        # Calculate messages for this page
        messages_per_page = (end_idx - start_idx) // len(pages)
        page_start = start_idx + (page_idx * messages_per_page)
        page_end = start_idx + ((page_idx + 1) * messages_per_page) if page_idx < len(pages) - 1 else end_idx

        y_pos = 150
        for conv in conversations[page_start:page_end]:
            timestamp, sender, message = conv
            paragraphs.append({
                "paragraph_id": f"para-{file_id:03d}-{chunk_num:03d}-{page_num:03d}-{para_idx}",
                "idx_in_page": para_idx,
                "text": f"[{timestamp}] {sender}: {message}",
                "page": page_num,
                "bbox": {"x": 220, "y": y_pos, "width": 1300, "height": 35},
                "type": "body",
                "confidence_score": 0.94
            })
            para_idx += 1
            y_pos += 50

        # Page footer
        paragraphs.append({
            "paragraph_id": f"para-{file_id:03d}-{chunk_num:03d}-{page_num:03d}-{para_idx}",
            "idx_in_page": para_idx,
            "text": f"페이지 {page_num}/{{total_pages}}",
            "page": page_num,
            "bbox": {"x": 600, "y": 2300, "width": 200, "height": 30},
            "type": "footer",
            "confidence_score": 0.98
        })
        para_idx = 0  # Reset for next page

    return paragraphs


def fix_kakao_chunks():
    """Fix all KakaoTalk chunk files"""

    # 갑14호증 (15 pages)
    conv_14 = generate_kakao_conversation_갑14호증()
    messages_per_chunk_14 = len(conv_14) // 5  # 5 chunks for 15 pages

    for chunk_num in range(1, 6):
        pages = []
        if chunk_num == 1:
            pages = [1, 2, 3]
        elif chunk_num == 2:
            pages = [3, 4, 5]
        elif chunk_num == 3:
            pages = [5, 6, 7]
        elif chunk_num == 4:
            pages = [7, 8, 9]
        else:
            pages = [9, 10, 11] if chunk_num == 5 else [11, 12, 13]

        pattern = f"갑14호증_카카오톡대화_계약논의_p{pages[0]}-{pages[-1]}.json"
        file_path = list(BASE_DIR.glob(pattern))

        if file_path:
            file_path = file_path[0]
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            start_idx = (chunk_num - 1) * messages_per_chunk_14
            end_idx = min(chunk_num * messages_per_chunk_14 + 5, len(conv_14))  # +5 for overlap

            data["paragraph_texts"] = create_paragraph_texts_from_conversation(conv_14, start_idx, end_idx, pages)
            data["chunk_content"]["paragraphs"] = create_paragraph_objects_from_conversation(
                conv_14, start_idx, end_idx, pages, 25, chunk_num
            )

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"✅ Fixed: {file_path.name}")

    # 갑15호증 (12 pages)
    conv_15 = generate_kakao_conversation_갑15호증()
    messages_per_chunk_15 = len(conv_15) // 4  # 4 chunks for 12 pages

    for chunk_num in range(1, 5):
        pages = []
        if chunk_num == 1:
            pages = [1, 2, 3]
        elif chunk_num == 2:
            pages = [3, 4, 5]
        elif chunk_num == 3:
            pages = [5, 6, 7]
        else:
            pages = [7, 8, 9]

        pattern = f"갑15호증_카카오톡대화_이행요구_p{pages[0]}-{pages[-1]}.json"
        file_path = list(BASE_DIR.glob(pattern))

        if file_path:
            file_path = file_path[0]
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            start_idx = (chunk_num - 1) * messages_per_chunk_15
            end_idx = min(chunk_num * messages_per_chunk_15 + 5, len(conv_15))

            data["paragraph_texts"] = create_paragraph_texts_from_conversation(conv_15, start_idx, end_idx, pages)
            data["chunk_content"]["paragraphs"] = create_paragraph_objects_from_conversation(
                conv_15, start_idx, end_idx, pages, 26, chunk_num
            )

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"✅ Fixed: {file_path.name}")


def main():
    print("=" * 60)
    print("Fix KakaoTalk Conversation Chunks")
    print("=" * 60)
    fix_kakao_chunks()
    print("\n✨ All KakaoTalk chunks fixed successfully!")


if __name__ == "__main__":
    main()
