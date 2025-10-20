#!/usr/bin/env python3
"""
Improve OCR chunk files by splitting single-paragraph pages into multiple paragraphs
"""
import json
import re
from pathlib import Path
from typing import List, Dict
import random

def split_paragraph_into_natural_parts(text: str, min_parts: int = 2, max_parts: int = 5) -> List[str]:
    """Split a paragraph into natural parts based on sentence boundaries"""

    # Split by sentence-ending punctuation
    sentences = re.split(r'([.!?\n]+)', text)

    # Reconstruct sentences with their punctuation
    full_sentences = []
    for i in range(0, len(sentences) - 1, 2):
        if i + 1 < len(sentences):
            full_sentences.append(sentences[i] + sentences[i + 1])
        else:
            full_sentences.append(sentences[i])

    # Filter out empty sentences
    full_sentences = [s.strip() for s in full_sentences if s.strip()]

    if len(full_sentences) <= 1:
        # Can't split, return as is
        return [text]

    # Determine how many parts to create
    num_parts = min(max(min_parts, len(full_sentences) // 3), max_parts, len(full_sentences))

    # Distribute sentences evenly across parts
    parts = []
    sentences_per_part = len(full_sentences) // num_parts
    remainder = len(full_sentences) % num_parts

    start_idx = 0
    for i in range(num_parts):
        end_idx = start_idx + sentences_per_part + (1 if i < remainder else 0)
        part = ' '.join(full_sentences[start_idx:end_idx])
        if part.strip():
            parts.append(part.strip())
        start_idx = end_idx

    return parts if parts else [text]

def calculate_bbox(page_num: int, idx_in_page: int, total_in_page: int, text_length: int) -> Dict:
    """Calculate realistic bounding box for a paragraph"""

    # Page dimensions (A4 size in pixels at 150 DPI)
    page_width = 1681
    page_height = 2379

    # Margins
    margin_x = 200
    margin_y = 100
    content_width = page_width - (2 * margin_x)

    # Vertical spacing
    available_height = page_height - (2 * margin_y)
    avg_height_per_para = available_height / max(total_in_page, 1)

    # Calculate y position
    y = margin_y + (idx_in_page * avg_height_per_para)

    # Height varies by text length (roughly 50 pixels per 100 chars)
    height = min(max(50, text_length * 0.5), avg_height_per_para * 0.9)

    # Add some randomness for natural appearance
    x = margin_x + random.uniform(-20, 20)
    y = y + random.uniform(-10, 10)
    width = content_width + random.uniform(-50, 50)

    return {
        "x": round(x, 2),
        "y": round(y, 2),
        "width": round(width, 2),
        "height": round(height, 2)
    }

def improve_chunk_file(file_path: Path) -> bool:
    """Improve a single chunk file by splitting paragraphs"""

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Track if we made any changes
        changed = False

        # Group paragraphs by page
        pages = {}
        for para in data['chunk_content']['paragraphs']:
            page_num = para['page']
            if page_num not in pages:
                pages[page_num] = []
            pages[page_num].append(para)

        # Check each page - if it has only 1 paragraph, split it
        new_paragraphs = []
        new_paragraph_texts = []

        for page_num in sorted(pages.keys()):
            page_paras = pages[page_num]

            if len(page_paras) == 1:
                # Single paragraph - needs splitting
                original_para = page_paras[0]
                original_text = original_para['text']

                # Split into multiple parts
                split_texts = split_paragraph_into_natural_parts(original_text, min_parts=2, max_parts=4)

                # Create new paragraphs for each split
                for idx, split_text in enumerate(split_texts):
                    new_para = {
                        "paragraph_id": f"{original_para['paragraph_id']}-{idx}",
                        "idx_in_page": idx,
                        "text": split_text,
                        "page": page_num,
                        "bbox": calculate_bbox(page_num, idx, len(split_texts), len(split_text)),
                        "type": original_para.get('type', 'body'),
                        "confidence_score": round(original_para.get('confidence_score', 0.95) - random.uniform(0, 0.05), 2)
                    }
                    new_paragraphs.append(new_para)
                    new_paragraph_texts.append(split_text)

                changed = True
            else:
                # Multiple paragraphs - fix idx_in_page and keep as is
                for idx, para in enumerate(page_paras):
                    para['idx_in_page'] = idx
                    new_paragraphs.append(para)
                    new_paragraph_texts.append(para['text'])
                changed = True  # Changed idx_in_page

        if changed:
            # Update the data
            data['chunk_content']['paragraphs'] = new_paragraphs
            data['paragraph_texts'] = new_paragraph_texts

            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True

        return False

    except Exception as e:
        print(f"Error processing {file_path.name}: {e}")
        return False

def main():
    base_dir = Path('/Users/jaehaklee/qdrant_api_backend/__test__/sample_generated/부동산소유권등기소송/ocr_chunks')

    if not base_dir.exists():
        print(f"Error: Directory not found: {base_dir}")
        return 1

    chunk_files = sorted(base_dir.glob('*.json'))
    print(f"Found {len(chunk_files)} chunk files")
    print("Processing...\n")

    improved_count = 0
    failed_count = 0

    for idx, chunk_file in enumerate(chunk_files, 1):
        if idx % 10 == 0:
            print(f"Progress: {idx}/{len(chunk_files)}")

        if improve_chunk_file(chunk_file):
            improved_count += 1
        else:
            failed_count += 1

    print(f"\n{'='*80}")
    print(f"IMPROVEMENT COMPLETE")
    print(f"{'='*80}")
    print(f"Total files: {len(chunk_files)}")
    print(f"Improved: {improved_count}")
    print(f"Failed: {failed_count}")
    print(f"Unchanged: {len(chunk_files) - improved_count - failed_count}")

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
