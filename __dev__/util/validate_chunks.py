#!/usr/bin/env python3
"""
Validate OCR chunk files for natural structure
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

def validate_chunk_file(file_path: Path) -> dict:
    """Validate a single chunk file and return issues"""
    issues = []

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Check 1: Each page should have multiple paragraphs (realistic OCR)
    page_paragraph_count = defaultdict(int)
    for para in data['chunk_content']['paragraphs']:
        page_paragraph_count[para['page']] += 1

    # Flag pages with only 1 paragraph as suspicious
    single_para_pages = [page for page, count in page_paragraph_count.items() if count == 1]
    if single_para_pages:
        issues.append({
            'type': 'single_paragraph_page',
            'pages': single_para_pages,
            'severity': 'high'
        })

    # Check 2: paragraph_texts should match chunk_content paragraphs count
    para_texts_count = len(data['paragraph_texts'])
    para_content_count = len(data['chunk_content']['paragraphs'])

    if para_texts_count != para_content_count:
        issues.append({
            'type': 'paragraph_count_mismatch',
            'paragraph_texts': para_texts_count,
            'chunk_content': para_content_count,
            'severity': 'critical'
        })

    # Check 3: Each paragraph text should not be too long (>1000 chars suspicious)
    for idx, text in enumerate(data['paragraph_texts']):
        if len(text) > 1000:
            issues.append({
                'type': 'oversized_paragraph',
                'index': idx,
                'length': len(text),
                'severity': 'medium'
            })

    # Check 4: idx_in_page should restart from 0 for each page
    for page in set(para['page'] for para in data['chunk_content']['paragraphs']):
        page_paras = [p for p in data['chunk_content']['paragraphs'] if p['page'] == page]
        indices = [p['idx_in_page'] for p in page_paras]

        if indices != list(range(len(indices))):
            issues.append({
                'type': 'invalid_idx_in_page',
                'page': page,
                'expected': list(range(len(indices))),
                'actual': indices,
                'severity': 'medium'
            })

    return {
        'file': file_path.name,
        'issues': issues,
        'total_paragraphs': para_content_count,
        'pages': sorted(page_paragraph_count.keys()),
        'paragraphs_per_page': dict(page_paragraph_count)
    }

def main():
    base_dir = Path('/Users/jaehaklee/qdrant_api_backend/__test__/sample_generated/부동산소유권등기소송/ocr_chunks')

    if not base_dir.exists():
        print(f"Error: Directory not found: {base_dir}")
        sys.exit(1)

    chunk_files = sorted(base_dir.glob('*.json'))
    print(f"Found {len(chunk_files)} chunk files\n")

    results = []
    problematic_files = []

    for chunk_file in chunk_files:
        result = validate_chunk_file(chunk_file)
        results.append(result)

        if result['issues']:
            problematic_files.append(result)

    # Summary statistics
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total files: {len(chunk_files)}")
    print(f"Problematic files: {len(problematic_files)}")
    print(f"Clean files: {len(chunk_files) - len(problematic_files)}")
    print()

    # Issue breakdown
    issue_types = defaultdict(int)
    for result in problematic_files:
        for issue in result['issues']:
            issue_types[issue['type']] += 1

    print("Issue Breakdown:")
    for issue_type, count in sorted(issue_types.items()):
        print(f"  - {issue_type}: {count}")
    print()

    # Show first 10 problematic files in detail
    print("=" * 80)
    print("SAMPLE PROBLEMATIC FILES (first 10)")
    print("=" * 80)

    for result in problematic_files[:10]:
        print(f"\nFile: {result['file']}")
        print(f"  Pages: {result['pages']}")
        print(f"  Total paragraphs: {result['total_paragraphs']}")
        print(f"  Paragraphs per page: {result['paragraphs_per_page']}")

        for issue in result['issues']:
            severity = issue['severity'].upper()
            print(f"  [{severity}] {issue['type']}")

            if issue['type'] == 'single_paragraph_page':
                print(f"    Pages with only 1 paragraph: {issue['pages']}")
            elif issue['type'] == 'paragraph_count_mismatch':
                print(f"    paragraph_texts: {issue['paragraph_texts']}, chunk_content: {issue['chunk_content']}")
            elif issue['type'] == 'oversized_paragraph':
                print(f"    Paragraph {issue['index']}: {issue['length']} chars")
            elif issue['type'] == 'invalid_idx_in_page':
                print(f"    Page {issue['page']}: expected {issue['expected']}, got {issue['actual']}")

    # Export full report
    report_path = base_dir.parent / 'validation_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total_files': len(chunk_files),
            'problematic_files': len(problematic_files),
            'clean_files': len(chunk_files) - len(problematic_files),
            'issue_types': dict(issue_types),
            'details': problematic_files
        }, f, ensure_ascii=False, indent=2)

    print(f"\n\nFull report saved to: {report_path}")

    return 0 if len(problematic_files) == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
