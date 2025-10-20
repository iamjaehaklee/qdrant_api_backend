#!/usr/bin/env python3
"""
Advanced validation: Check for content repetition and summary consistency
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher

CHUNKS_DIR = Path('/Users/jaehaklee/qdrant_api_backend/__test__/sample_generated/부동산소유권등기소송/ocr_chunks')
SUMMARIES_DIR = Path('/Users/jaehaklee/qdrant_api_backend/__test__/sample_generated/부동산소유권등기소송/ocr_summaries')

def similarity_ratio(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two texts"""
    return SequenceMatcher(None, text1, text2).ratio()

def extract_base_name(filename: str) -> str:
    """Extract base filename without page range suffix"""
    # Remove _p1-3.json pattern
    if '_p' in filename:
        parts = filename.rsplit('_p', 1)
        return parts[0]
    return filename.replace('.json', '')

def check_page_repetition(chunk_data: dict) -> dict:
    """Check if content repeats across pages in a chunk"""
    issues = []

    # Group paragraphs by page
    page_texts = defaultdict(list)
    for para in chunk_data['chunk_content']['paragraphs']:
        page_texts[para['page']].append(para['text'])

    if len(page_texts) < 2:
        return {'has_issue': False, 'details': []}

    # Compare each page's content
    pages = sorted(page_texts.keys())
    page_contents = {p: '\n'.join(texts) for p, texts in page_texts.items()}

    similarities = []
    for i in range(len(pages) - 1):
        p1, p2 = pages[i], pages[i+1]
        sim = similarity_ratio(page_contents[p1], page_contents[p2])
        similarities.append((p1, p2, sim))

        if sim > 0.9:  # 90% similarity is suspicious
            issues.append({
                'type': 'high_page_similarity',
                'pages': [p1, p2],
                'similarity': round(sim, 3),
                'severity': 'critical'
            })

    # Check if ALL pages are identical
    unique_contents = set(page_contents.values())
    if len(unique_contents) == 1 and len(pages) > 1:
        issues.append({
            'type': 'identical_pages',
            'page_count': len(pages),
            'severity': 'critical'
        })

    return {
        'has_issue': len(issues) > 0,
        'details': issues,
        'similarities': similarities
    }

def check_summary_consistency(base_name: str, all_chunk_texts: list) -> dict:
    """Check if chunk content is consistent with summary"""
    summary_path = SUMMARIES_DIR / f"{base_name}.json"

    if not summary_path.exists():
        return {'has_issue': False, 'details': [{'type': 'no_summary', 'severity': 'info'}]}

    with open(summary_path, 'r', encoding='utf-8') as f:
        summary_data = json.load(f)

    summary_text = summary_data.get('summary_text', '')
    combined_chunks = ' '.join(all_chunk_texts)

    issues = []

    # Check 1: Summary mentions specific details that should appear in chunks
    # Extract key information patterns
    import re

    # Look for numbers/dates/amounts in summary
    summary_numbers = re.findall(r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일', summary_text)
    summary_amounts = re.findall(r'금\s*[\d,]+원', summary_text)
    summary_numbers.extend(re.findall(r'\d{6}-\d{7}', summary_text))  # 주민번호 패턴

    # Check if these appear in chunks
    missing_dates = [d for d in summary_numbers if d not in combined_chunks]
    missing_amounts = [a for a in summary_amounts if a not in combined_chunks]

    if missing_dates:
        issues.append({
            'type': 'missing_dates',
            'count': len(missing_dates),
            'examples': missing_dates[:3],
            'severity': 'high'
        })

    if missing_amounts:
        issues.append({
            'type': 'missing_amounts',
            'count': len(missing_amounts),
            'examples': missing_amounts[:3],
            'severity': 'high'
        })

    # Check 2: Length ratio (chunks should have more content than summary)
    if len(combined_chunks) > 0 and len(summary_text) > 100:
        ratio = len(combined_chunks) / len(summary_text)
        if ratio < 0.5:  # Chunks are less than half the summary length
            issues.append({
                'type': 'insufficient_content',
                'summary_length': len(summary_text),
                'chunks_length': len(combined_chunks),
                'ratio': round(ratio, 2),
                'severity': 'medium'
            })

    return {
        'has_issue': len(issues) > 0,
        'details': issues
    }

def validate_document(base_name: str, chunk_files: list) -> dict:
    """Validate all chunks of a document"""
    all_issues = []
    all_chunk_texts = []

    # Validate each chunk
    for chunk_path in chunk_files:
        with open(chunk_path, 'r', encoding='utf-8') as f:
            chunk_data = json.load(f)

        all_chunk_texts.extend(chunk_data.get('paragraph_texts', []))

        # Check page repetition
        repetition_check = check_page_repetition(chunk_data)
        if repetition_check['has_issue']:
            all_issues.extend([
                {**issue, 'file': chunk_path.name}
                for issue in repetition_check['details']
            ])

    # Check summary consistency
    summary_check = check_summary_consistency(base_name, all_chunk_texts)
    if summary_check['has_issue']:
        all_issues.extend(summary_check['details'])

    return {
        'base_name': base_name,
        'chunk_count': len(chunk_files),
        'total_paragraphs': len(all_chunk_texts),
        'has_issues': len(all_issues) > 0,
        'issues': all_issues
    }

def main():
    """Main validation function"""
    print("=" * 80)
    print("ADVANCED OCR CHUNK VALIDATION")
    print("=" * 80)
    print()

    # Group chunks by base name
    chunk_groups = defaultdict(list)
    for chunk_file in sorted(CHUNKS_DIR.glob('*.json')):
        base_name = extract_base_name(chunk_file.name)
        chunk_groups[base_name].append(chunk_file)

    print(f"Found {len(chunk_groups)} documents with {sum(len(v) for v in chunk_groups.values())} total chunks\n")

    # Validate each document
    results = []
    problematic_docs = []

    for base_name, chunk_files in sorted(chunk_groups.items()):
        result = validate_document(base_name, chunk_files)
        results.append(result)

        if result['has_issues']:
            problematic_docs.append(result)

    # Summary
    print("=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print(f"Total documents: {len(chunk_groups)}")
    print(f"Problematic documents: {len(problematic_docs)}")
    print(f"Clean documents: {len(chunk_groups) - len(problematic_docs)}")
    print()

    # Issue breakdown
    issue_types = defaultdict(int)
    for doc in problematic_docs:
        for issue in doc['issues']:
            issue_types[issue['type']] += 1

    print("Issue Types:")
    for issue_type, count in sorted(issue_types.items(), key=lambda x: -x[1]):
        print(f"  {issue_type}: {count}")
    print()

    # Show problematic documents
    if problematic_docs:
        print("=" * 80)
        print(f"PROBLEMATIC DOCUMENTS (showing first 15)")
        print("=" * 80)
        print()

        for doc in problematic_docs[:15]:
            print(f"📄 {doc['base_name']}")
            print(f"   Chunks: {doc['chunk_count']}, Paragraphs: {doc['total_paragraphs']}")

            for issue in doc['issues']:
                severity_emoji = {'critical': '🔴', 'high': '🟡', 'medium': '🟠', 'info': '🔵'}
                emoji = severity_emoji.get(issue['severity'], '⚪')

                if issue['type'] == 'identical_pages':
                    print(f"   {emoji} {issue['type']}: All {issue['page_count']} pages identical")
                    if 'file' in issue:
                        print(f"      File: {issue['file']}")

                elif issue['type'] == 'high_page_similarity':
                    print(f"   {emoji} {issue['type']}: Pages {issue['pages']} are {issue['similarity']*100:.1f}% similar")
                    if 'file' in issue:
                        print(f"      File: {issue['file']}")

                elif issue['type'] == 'missing_dates':
                    print(f"   {emoji} {issue['type']}: {issue['count']} dates from summary not in chunks")
                    print(f"      Examples: {', '.join(issue['examples'])}")

                elif issue['type'] == 'missing_amounts':
                    print(f"   {emoji} {issue['type']}: {issue['count']} amounts from summary not in chunks")
                    print(f"      Examples: {', '.join(issue['examples'])}")

                elif issue['type'] == 'insufficient_content':
                    print(f"   {emoji} {issue['type']}: Chunks {issue['chunks_length']} chars vs Summary {issue['summary_length']} chars (ratio: {issue['ratio']})")

                elif issue['type'] == 'no_summary':
                    print(f"   {emoji} {issue['type']}: No corresponding summary file")

            print()

    # Save report
    report_path = CHUNKS_DIR.parent / 'advanced_validation_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total_documents': len(chunk_groups),
            'problematic_documents': len(problematic_docs),
            'clean_documents': len(chunk_groups) - len(problematic_docs),
            'issue_types': dict(issue_types),
            'problematic_details': problematic_docs
        }, f, ensure_ascii=False, indent=2)

    print(f"Full report saved to: {report_path}")

    return 0 if len(problematic_docs) == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
