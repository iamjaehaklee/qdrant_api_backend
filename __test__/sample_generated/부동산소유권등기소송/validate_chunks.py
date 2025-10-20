#!/usr/bin/env python3
"""
Validate generated OCR chunk files for structure and 3-page window logic.
"""

import json
from pathlib import Path
from collections import defaultdict

CHUNKS_DIR = Path(__file__).parent / "ocr_chunks"

def validate_chunk_structure(chunk_data: dict, filename: str) -> list:
    """Validate chunk structure and return list of issues."""
    issues = []

    # Required fields
    required_fields = [
        "chunk_id", "file_id", "project_id", "storage_file_name",
        "original_file_name", "mime_type", "total_pages", "language",
        "pages", "chunk_number", "paragraph_texts", "chunk_content",
        "page_dimensions", "created_at"
    ]

    for field in required_fields:
        if field not in chunk_data:
            issues.append(f"Missing required field: {field}")

    # Validate pages is a list
    if "pages" in chunk_data:
        pages = chunk_data["pages"]
        if not isinstance(pages, list):
            issues.append(f"'pages' must be a list, got {type(pages)}")
        elif len(pages) > 3:
            issues.append(f"Window should have max 3 pages, got {len(pages)}")
        elif len(pages) < 1:
            issues.append(f"Window should have at least 1 page, got {len(pages)}")
        else:
            # Check pages are sequential
            for i in range(len(pages) - 1):
                if pages[i+1] != pages[i] + 1:
                    issues.append(f"Pages not sequential: {pages}")
                    break

    # Validate paragraph_texts is a list
    if "paragraph_texts" in chunk_data:
        if not isinstance(chunk_data["paragraph_texts"], list):
            issues.append(f"'paragraph_texts' must be a list")

    # Validate chunk_content has paragraphs
    if "chunk_content" in chunk_data:
        if "paragraphs" not in chunk_data["chunk_content"]:
            issues.append(f"'chunk_content' missing 'paragraphs'")
        else:
            paragraphs = chunk_data["chunk_content"]["paragraphs"]
            if not isinstance(paragraphs, list):
                issues.append(f"'paragraphs' must be a list")
            else:
                # Validate paragraph structure
                for i, para in enumerate(paragraphs):
                    required_para_fields = ["paragraph_id", "text", "page", "bbox", "type", "confidence_score"]
                    for field in required_para_fields:
                        if field not in para:
                            issues.append(f"Paragraph {i} missing field: {field}")
                            break

    # Validate page_dimensions
    if "page_dimensions" in chunk_data:
        dims = chunk_data["page_dimensions"]
        if not isinstance(dims, list):
            issues.append(f"'page_dimensions' must be a list")
        elif "pages" in chunk_data:
            if len(dims) != len(chunk_data["pages"]):
                issues.append(f"page_dimensions count ({len(dims)}) != pages count ({len(chunk_data['pages'])})")

    return issues


def validate_window_overlap(doc_chunks: list) -> list:
    """Validate 3-page window overlap logic for a document."""
    issues = []

    # Sort chunks by chunk_number
    sorted_chunks = sorted(doc_chunks, key=lambda c: c["chunk_number"])

    # Check window overlap
    for i in range(len(sorted_chunks) - 1):
        current_pages = sorted_chunks[i]["pages"]
        next_pages = sorted_chunks[i+1]["pages"]

        # Check if there's 1-page overlap
        if len(current_pages) >= 2 and len(next_pages) >= 2:
            # Normal case: should have 1-page overlap
            if current_pages[-1] != next_pages[0]:
                issues.append(
                    f"Chunk {sorted_chunks[i]['chunk_number']} and {sorted_chunks[i+1]['chunk_number']} "
                    f"should have 1-page overlap: {current_pages} vs {next_pages}"
                )

    return issues


def main():
    print("="*60)
    print("OCR Chunk Validation")
    print("="*60)
    print(f"Checking directory: {CHUNKS_DIR}\n")

    # Group chunks by document
    chunks_by_doc = defaultdict(list)
    all_issues = []
    total_files = 0

    # Load all chunks
    for chunk_file in CHUNKS_DIR.glob("*.json"):
        total_files += 1

        # Parse document name from filename
        filename = chunk_file.stem
        # Remove page range suffix (e.g., "_p1-3")
        doc_name = "_".join(filename.split("_")[:-1])

        try:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                chunk_data = json.load(f)
                chunks_by_doc[doc_name].append(chunk_data)

                # Validate structure
                issues = validate_chunk_structure(chunk_data, chunk_file.name)
                if issues:
                    all_issues.append((chunk_file.name, issues))

        except Exception as e:
            all_issues.append((chunk_file.name, [f"Error loading file: {e}"]))

    # Validate window overlap for each document
    print(f"📊 Total files: {total_files}")
    print(f"📄 Unique documents: {len(chunks_by_doc)}\n")

    overlap_issues = []
    for doc_name, chunks in chunks_by_doc.items():
        issues = validate_window_overlap(chunks)
        if issues:
            overlap_issues.append((doc_name, issues))

    # Report results
    if all_issues:
        print(f"❌ Structure Issues Found ({len(all_issues)} files):")
        print("="*60)
        for filename, issues in all_issues[:10]:  # Show first 10
            print(f"\n📄 {filename}")
            for issue in issues:
                print(f"  - {issue}")
        if len(all_issues) > 10:
            print(f"\n... and {len(all_issues) - 10} more files with issues")
    else:
        print("✅ All chunks have valid structure!")

    print()

    if overlap_issues:
        print(f"❌ Window Overlap Issues Found ({len(overlap_issues)} docs):")
        print("="*60)
        for doc_name, issues in overlap_issues[:10]:  # Show first 10
            print(f"\n📄 {doc_name}")
            for issue in issues:
                print(f"  - {issue}")
        if len(overlap_issues) > 10:
            print(f"\n... and {len(overlap_issues) - 10} more documents with issues")
    else:
        print("✅ All documents have valid 3-page window overlap!")

    print("\n" + "="*60)
    print("Sample Document Window Analysis")
    print("="*60)

    # Show examples of window logic
    sample_docs = list(chunks_by_doc.keys())[:3]
    for doc_name in sample_docs:
        chunks = sorted(chunks_by_doc[doc_name], key=lambda c: c["chunk_number"])
        total_pages = chunks[0]["total_pages"]

        print(f"\n📄 {doc_name}")
        print(f"   Total pages: {total_pages}")
        print(f"   Chunks generated: {len(chunks)}")
        print(f"   Window sequence:")

        for chunk in chunks:
            pages_str = f"[{','.join(map(str, chunk['pages']))}]"
            print(f"     Chunk {chunk['chunk_number']}: pages {pages_str}")

    print("\n" + "="*60)
    if not all_issues and not overlap_issues:
        print("✅ Validation Complete - All Checks Passed!")
    else:
        print("⚠️  Validation Complete - Issues Found")
    print("="*60)


if __name__ == "__main__":
    main()
