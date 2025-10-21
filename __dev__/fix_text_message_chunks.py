#!/usr/bin/env python3
"""
Fix OCR chunk files for text messages (갑16호증_문자메시지)
- Remove placeholder repetition across pages
- Create realistic text message conversation flow
- Ensure 3-page window structure
"""

import json
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent / "__test__" / "sample_generated" / "부동산소유권등기소송" / "ocr_chunks"


def generate_text_messages_갑16호증():
    """Generate realistic text message conversation for 갑16호증"""
    messages = [
        # Initial contact after contract
        ("2024-03-15 12:00", "010-1234-5678", "원고", "계약 감사합니다. 잔금일까지 잘 부탁드립니다."),
        ("2024-03-15 12:15", "010-9876-5432", "피고", "네, 저도 감사합니다."),

        # First interim payment notification
        ("2024-04-19 17:30", "010-1234-5678", "원고", "내일 중도금 1차 입금하겠습니다."),
        ("2024-04-19 17:45", "010-9876-5432", "피고", "네, 알겠습니다."),
        ("2024-04-20 10:05", "010-1234-5678", "원고", "중도금 1억5천 입금했습니다."),
        ("2024-04-20 10:10", "010-9876-5432", "피고", "확인했습니다. 감사합니다."),

        # Second interim payment notification
        ("2024-05-19 16:00", "010-1234-5678", "원고", "내일 중도금 2차 입금하겠습니다."),
        ("2024-05-19 16:20", "010-9876-5432", "피고", "네, 확인하겠습니다."),
        ("2024-05-20 09:35", "010-1234-5678", "원고", "중도금 1억5천 입금 완료했습니다."),
        ("2024-05-20 09:40", "010-9876-5432", "피고", "네, 확인했습니다."),

        # Final payment preparation
        ("2024-06-10 14:05", "010-1234-5678", "원고", "잔금일이 이번주 토요일이죠?"),
        ("2024-06-10 14:20", "010-9876-5432", "피고", "네, 15일 토요일입니다."),
        ("2024-06-12 10:00", "010-1234-5678", "원고", "등기 서류 준비 부탁드립니다."),
        ("2024-06-12 10:30", "010-9876-5432", "피고", "네, 준비하고 있습니다."),

        # Final payment day
        ("2024-06-15 09:10", "010-1234-5678", "원고", "오늘 잔금 2억 입금하겠습니다."),
        ("2024-06-15 09:25", "010-9876-5432", "피고", "네, 확인하겠습니다."),
        ("2024-06-15 10:35", "010-1234-5678", "원고", "입금 완료했습니다."),
        ("2024-06-15 10:40", "010-9876-5432", "피고", "확인했습니다."),
        ("2024-06-15 10:45", "010-1234-5678", "원고", "등기 서류 언제 받을 수 있나요?"),

        # No response - start of problem
        ("2024-06-15 14:00", "010-1234-5678", "원고", "서류 준비되셨나요?"),
        ("2024-06-15 17:00", "010-1234-5678", "원고", "연락 부탁드립니다."),
        ("2024-06-15 19:30", "010-1234-5678", "원고", "왜 연락이 안 되시나요?"),

        # Next day - continued attempts
        ("2024-06-16 09:00", "010-1234-5678", "원고", "어제 연락 못 받으셨나요?"),
        ("2024-06-16 12:00", "010-1234-5678", "원고", "등기 서류 언제 주실 건가요?"),
        ("2024-06-16 16:00", "010-1234-5678", "원고", "답변 없으시면 법적 조치 취하겠습니다."),
        ("2024-06-16 20:00", "010-1234-5678", "원고", "내일까지 연락 주시기 바랍니다."),

        # Third day - escalation
        ("2024-06-17 10:00", "010-1234-5678", "원고", "이틀째 연락이 안 됩니다."),
        ("2024-06-17 14:00", "010-1234-5678", "원고", "변호사 통해 진행하겠습니다."),
        ("2024-06-17 18:00", "010-1234-5678", "원고", "법적 책임 물을 것입니다."),

        # Fourth day
        ("2024-06-18 09:00", "010-1234-5678", "원고", "무슨 일 있으신가요?"),
        ("2024-06-18 12:00", "010-1234-5678", "원고", "정말 연락 안 되시네요."),
        ("2024-06-18 14:00", "010-1234-5678", "원고", "법적 조치 시작합니다."),
        ("2024-06-18 18:00", "010-1234-5678", "원고", "내일까지 서류 안 주시면 소송 제기합니다."),

        # Week later - final demands
        ("2024-06-22 09:00", "010-1234-5678", "원고", "일주일째 연락이 없습니다."),
        ("2024-06-22 12:00", "010-1234-5678", "원고", "더 이상 기다릴 수 없습니다."),
        ("2024-06-22 15:00", "010-1234-5678", "원고", "오늘 중 내용증명 발송합니다."),
        ("2024-06-22 17:00", "010-1234-5678", "원고", "마지막 통보입니다. 연락 주십시오."),
        ("2024-06-22 19:00", "010-1234-5678", "원고", "내일부터 법적 절차 진행합니다."),

        # Urgent final messages
        ("2024-06-23 10:00", "010-1234-5678", "원고", "내용증명 발송했습니다."),
        ("2024-06-24 10:00", "010-1234-5678", "원고", "소송 준비 중입니다."),
        ("2024-06-25 10:00", "010-1234-5678", "원고", "변호사와 상담 완료했습니다."),
        ("2024-06-26 10:00", "010-1234-5678", "원고", "소송 제기합니다."),
    ]
    return messages


def create_paragraph_texts_from_messages(messages, start_idx, end_idx, page_numbers):
    """Create paragraph_texts from message slice"""
    texts = []
    for page_num in page_numbers:
        texts.append(f"문자메시지 내역 - {page_num}페이지")
        texts.append("")

    for msg in messages[start_idx:end_idx]:
        timestamp, phone, sender, message = msg
        texts.append(f"[{timestamp}] {sender} ({phone})")
        texts.append(message)
        texts.append("")  # Blank line between messages

    return texts


def create_paragraph_objects_from_messages(messages, start_idx, end_idx, pages, file_id, chunk_num):
    """Create paragraph objects from message slice"""
    paragraphs = []
    para_idx = 0

    for page_idx, page_num in enumerate(pages):
        # Page header
        paragraphs.append({
            "paragraph_id": f"para-{file_id:03d}-{chunk_num:03d}-{page_num:03d}-{para_idx}",
            "idx_in_page": para_idx,
            "text": f"문자메시지 내역 - {page_num}페이지",
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
        for msg in messages[page_start:page_end]:
            timestamp, phone, sender, message = msg

            # Timestamp and sender
            paragraphs.append({
                "paragraph_id": f"para-{file_id:03d}-{chunk_num:03d}-{page_num:03d}-{para_idx}",
                "idx_in_page": para_idx,
                "text": f"[{timestamp}] {sender} ({phone})",
                "page": page_num,
                "bbox": {"x": 220, "y": y_pos, "width": 1000, "height": 30},
                "type": "body",
                "confidence_score": 0.95
            })
            para_idx += 1
            y_pos += 35

            # Message content
            paragraphs.append({
                "paragraph_id": f"para-{file_id:03d}-{chunk_num:03d}-{page_num:03d}-{para_idx}",
                "idx_in_page": para_idx,
                "text": message,
                "page": page_num,
                "bbox": {"x": 240, "y": y_pos, "width": 1200, "height": 30},
                "type": "body",
                "confidence_score": 0.94
            })
            para_idx += 1
            y_pos += 50

        # Page footer
        paragraphs.append({
            "paragraph_id": f"para-{file_id:03d}-{chunk_num:03d}-{page_num:03d}-{para_idx}",
            "idx_in_page": para_idx,
            "text": f"페이지 {page_num}/18",
            "page": page_num,
            "bbox": {"x": 600, "y": 2300, "width": 200, "height": 30},
            "type": "footer",
            "confidence_score": 0.98
        })
        para_idx = 0  # Reset for next page

    return paragraphs


def fix_text_message_chunks():
    """Fix all text message chunk files"""
    messages = generate_text_messages_갑16호증()
    total_pages = 18
    messages_per_chunk = len(messages) // 6  # 6 chunks for 18 pages

    chunk_patterns = [
        (1, [1, 2, 3]),
        (2, [3, 4, 5]),
        (3, [5, 6, 7]),
        (4, [7, 8, 9]),
        (5, [9, 10, 11]),
        (6, [11, 12, 13]),
    ]

    for chunk_num, pages in chunk_patterns:
        pattern = f"갑16호증_문자메시지_p{pages[0]}-{pages[-1]}.json"
        file_paths = list(BASE_DIR.glob(pattern))

        if file_paths:
            file_path = file_paths[0]
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            start_idx = (chunk_num - 1) * messages_per_chunk
            end_idx = min(chunk_num * messages_per_chunk + 3, len(messages))  # +3 for overlap

            data["paragraph_texts"] = create_paragraph_texts_from_messages(messages, start_idx, end_idx, pages)
            data["chunk_content"]["paragraphs"] = create_paragraph_objects_from_messages(
                messages, start_idx, end_idx, pages, 27, chunk_num
            )

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"✅ Fixed: {file_path.name}")


def main():
    print("=" * 60)
    print("Fix Text Message Chunks")
    print("=" * 60)
    fix_text_message_chunks()
    print("\n✨ All text message chunks fixed successfully!")


if __name__ == "__main__":
    main()
