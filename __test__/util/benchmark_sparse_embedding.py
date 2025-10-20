"""
Performance Benchmarks for Sparse Embedding
Compares legacy vs new implementation in terms of speed and quality
"""

import time
from typing import List, Dict
import statistics
from app.multilingual_sparse_embedding import create_multilingual_sparse_embedding


# Sample test texts (Korean and English)
KOREAN_TEXTS = [
    "개인정보보호법을 위반했습니다",
    "손해배상을 청구합니다",
    "계약을 해지하겠습니다",
    "피고는 2020년 6월경 원고와 사이에 도급계약을 체결하였다",
    "API 서버에서 JSON 데이터를 받았습니다",
    "사용자 인증을 처리하는 함수입니다",
    "데이터베이스 연결이 실패했습니다",
    "파일을 업로드하고 처리합니다",
    "검색 결과가 표시됩니다",
    "로그인 페이지로 리다이렉트됩니다"
]

ENGLISH_TEXTS = [
    "The API server received the request successfully",
    "Database connection failed with timeout error",
    "User authentication has been completed",
    "File upload and processing pipeline started",
    "Search results are displayed on the page",
    "Redirect to login page required",
    "Data validation error occurred",
    "JSON response sent to client",
    "Query execution time exceeded threshold",
    "Cache invalidation triggered automatically"
]


def legacy_sparse_embedding(text: str) -> Dict[int, float]:
    """
    Legacy sparse embedding implementation (for comparison)
    Simple hash-based tokenization with max normalization
    """
    # Simple tokenization and frequency counting
    tokens = text.lower().split()
    token_freq: Dict[str, float] = {}

    for token in tokens:
        token_freq[token] = token_freq.get(token, 0) + 1.0

    # Convert to sparse vector format (hash-based indexing)
    sparse_vector: Dict[int, float] = {}
    for token, freq in token_freq.items():
        # Use hash for stable indexing
        idx = hash(token) % 100000  # Limit index space
        sparse_vector[idx] = sparse_vector.get(idx, 0) + freq

    # Normalize
    max_val = max(sparse_vector.values()) if sparse_vector else 1.0
    sparse_vector = {k: v / max_val for k, v in sparse_vector.items()}

    return sparse_vector


def benchmark_single_embedding(texts: List[str], implementation_name: str, func):
    """
    Benchmark single embedding generation speed

    Args:
        texts: List of texts to embed
        implementation_name: Name of implementation for display
        func: Embedding function to benchmark

    Returns:
        Average time per embedding in milliseconds
    """
    times = []

    for text in texts:
        start = time.time()
        _ = func(text)
        elapsed = (time.time() - start) * 1000  # Convert to ms
        times.append(elapsed)

    avg_time = statistics.mean(times)
    std_time = statistics.stdev(times) if len(times) > 1 else 0

    print(f"\n{implementation_name}:")
    print(f"  Average: {avg_time:.2f}ms")
    print(f"  Std Dev: {std_time:.2f}ms")
    print(f"  Min: {min(times):.2f}ms")
    print(f"  Max: {max(times):.2f}ms")

    return avg_time


def benchmark_embedding_quality(texts: List[str], implementation_name: str, func):
    """
    Analyze embedding quality metrics

    Args:
        texts: List of texts to embed
        implementation_name: Name of implementation for display
        func: Embedding function to benchmark

    Returns:
        Quality metrics dict
    """
    embeddings = [func(text) for text in texts]

    # Calculate metrics
    avg_indices = statistics.mean([len(emb) for emb in embeddings])
    avg_sparsity = statistics.mean([
        1 - (len(emb) / 10000) for emb in embeddings  # Assuming 10k possible indices
    ])

    print(f"\n{implementation_name} Quality:")
    print(f"  Avg indices per embedding: {avg_indices:.1f}")
    print(f"  Avg sparsity: {avg_sparsity*100:.1f}%")

    # Check for hash collisions (only applicable if index space info available)
    total_unique_indices = len(set(
        idx for emb in embeddings for idx in emb.keys()
    ))
    total_indices = sum(len(emb) for emb in embeddings)
    collision_rate = (1 - total_unique_indices / total_indices) * 100 if total_indices > 0 else 0

    print(f"  Hash collision rate: {collision_rate:.2f}%")

    return {
        "avg_indices": avg_indices,
        "avg_sparsity": avg_sparsity,
        "collision_rate": collision_rate
    }


def main():
    """Run all benchmarks"""
    print("=" * 80)
    print("Sparse Embedding Performance Benchmarks")
    print("=" * 80)

    print("\n" + "=" * 80)
    print("SPEED BENCHMARK - Korean Texts")
    print("=" * 80)

    legacy_time_korean = benchmark_single_embedding(
        KOREAN_TEXTS,
        "Legacy Implementation",
        legacy_sparse_embedding
    )

    new_time_korean = benchmark_single_embedding(
        KOREAN_TEXTS,
        "New Implementation (Kiwi)",
        create_multilingual_sparse_embedding
    )

    speedup_korean = legacy_time_korean / new_time_korean if new_time_korean > 0 else 0
    print(f"\nSpeedup (Korean): {speedup_korean:.2f}x")
    if speedup_korean < 1:
        slowdown = 1 / speedup_korean
        print(f"  (Note: New implementation is {slowdown:.2f}x slower)")

    print("\n" + "=" * 80)
    print("SPEED BENCHMARK - English Texts")
    print("=" * 80)

    legacy_time_english = benchmark_single_embedding(
        ENGLISH_TEXTS,
        "Legacy Implementation",
        legacy_sparse_embedding
    )

    new_time_english = benchmark_single_embedding(
        ENGLISH_TEXTS,
        "New Implementation (FastEmbed)",
        create_multilingual_sparse_embedding
    )

    speedup_english = legacy_time_english / new_time_english if new_time_english > 0 else 0
    print(f"\nSpeedup (English): {speedup_english:.2f}x")
    if speedup_english < 1:
        slowdown = 1 / speedup_english
        print(f"  (Note: New implementation is {slowdown:.2f}x slower)")

    print("\n" + "=" * 80)
    print("QUALITY BENCHMARK - Korean Texts")
    print("=" * 80)

    benchmark_embedding_quality(
        KOREAN_TEXTS,
        "Legacy Implementation",
        legacy_sparse_embedding
    )

    benchmark_embedding_quality(
        KOREAN_TEXTS,
        "New Implementation (Kiwi)",
        create_multilingual_sparse_embedding
    )

    print("\n" + "=" * 80)
    print("QUALITY BENCHMARK - English Texts")
    print("=" * 80)

    benchmark_embedding_quality(
        ENGLISH_TEXTS,
        "Legacy Implementation",
        legacy_sparse_embedding
    )

    benchmark_embedding_quality(
        ENGLISH_TEXTS,
        "New Implementation (FastEmbed)",
        create_multilingual_sparse_embedding
    )

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\nExpected Results:")
    print("  - Korean: New implementation may be slower due to morphological analysis")
    print("    but provides better quality (accurate tokenization)")
    print("  - English: New implementation (FastEmbed BM25) should be competitive")
    print("  - Hash collision rate: Should be ~0% for new implementation (2^31 space)")
    print("    vs potential collisions in legacy (100K space)")
    print("\nTrade-off:")
    print("  - Legacy: Fast but inaccurate (simple split)")
    print("  - New: Slightly slower but accurate (morphological analysis + BM25)")
    print("=" * 80)


if __name__ == "__main__":
    main()
