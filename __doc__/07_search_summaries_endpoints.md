# Search Summaries Endpoints

8 different search endpoints for the `ocr_summaries` collection, providing diverse search capabilities for document summaries.

## Table of Contents
- [Dense Search](#dense-search)
- [Sparse Search](#sparse-search)
- [MatchText Search](#matchtext-search)
- [Dense+Sparse RRF Search](#densesparse-rrf-search)
- [Recommend Search](#recommend-search)
- [Discover Search](#discover-search)
- [Scroll Search](#scroll-search)
- [Filter Search](#filter-search)

---

## Dense Search

Semantic similarity search using Gemini dense embeddings on summary_text.

### Endpoint

```
POST /summaries/search/dense
```

### Best For
- Concept-based search in summaries
- Meaning similarity
- Finding thematically related documents

### Request Body

**DenseSearchRequest**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| query_text | string | Yes | - | Query text to search |
| limit | integer | No | 10 | Max results (1-100) |
| score_threshold | float | No | null | Min score (0.0-1.0) |
| filter_project_id | integer | No | null | Filter by project ID |
| filter_file_id | integer | No | null | Filter by file ID |

### Example Request

```bash
curl -X POST "http://localhost:8000/summaries/search/dense" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "부동산 매매 계약 조건 및 대금 지급",
    "limit": 5,
    "score_threshold": 0.7,
    "filter_project_id": 8
  }'
```

### Example Response

```json
{
  "results": [
    {
      "point_id": "550e8400-e29b-41d4-a716-446655440000",
      "payload": {
        "summary_id": "550e8400-e29b-41d4-a716-446655440000",
        "file_id": 128,
        "project_id": 8,
        "storage_file_name": "doc_12345.pdf",
        "original_file_name": "부동산계약서.pdf",
        "mime_type": "application/pdf",
        "total_pages": 14,
        "language": "ko",
        "summary_text": "이 문서는 부동산 매매계약서로, 매도인과 매수인 간의 계약 내용을 담고 있습니다. 매매대금은 5억원이며, 계약금, 중도금, 잔금으로 지급됩니다.",
        "user_id": 42,
        "queue_id": 101,
        "correlation_id": "650e8400-e29b-41d4-a716-446655440001",
        "request_timestamp": "2025-10-21T12:30:45.123456+00:00"
      },
      "score": 0.87
    }
  ],
  "total": 1,
  "limit": 5,
  "offset": 0
}
```

### Status Codes

- `200 OK`: Search completed successfully
- `500 Internal Server Error`: Search failed

---

## Sparse Search

Keyword-based search using Kiwi (Korean) or FastEmbed BM25 sparse embeddings on summary_text.

### Endpoint

```
POST /summaries/search/sparse
```

### Best For
- Exact term matching in summaries
- Keyword search
- Morphological analysis (Korean)

### Request Body

**SparseSearchRequest** (same structure as DenseSearchRequest)

### Example Request

```bash
curl -X POST "http://localhost:8000/summaries/search/sparse" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "계약금 중도금 잔금",
    "limit": 10,
    "filter_project_id": 8
  }'
```

### Example Response

Same structure as Dense Search response.

### Status Codes

- `200 OK`: Search completed successfully
- `500 Internal Server Error`: Search failed

---

## MatchText Search

Full-text search using MatchText (no morphological analysis) on summary_text.

### Endpoint

```
POST /summaries/search/matchtext
```

### Best For
- Phrase matching in summaries
- Exact text search
- Fast text matching without analysis

### Request Body

**MatchTextSearchRequest**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| query_text | string | Yes | - | Query text to match |
| limit | integer | No | 10 | Max results (1-100) |
| filter_project_id | integer | No | null | Filter by project ID |
| filter_file_id | integer | No | null | Filter by file ID |

### Example Request

```bash
curl -X POST "http://localhost:8000/summaries/search/matchtext" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "부동산 매매계약서",
    "limit": 10
  }'
```

### Example Response

```json
{
  "results": [
    {
      "point_id": "550e8400-e29b-41d4-a716-446655440000",
      "payload": {...},
      "score": null
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

**Note**: MatchText search does not return scores.

### Status Codes

- `200 OK`: Search completed successfully
- `500 Internal Server Error`: Search failed

---

## Dense+Sparse RRF Search

Hybrid search combining dense and sparse vectors using Reciprocal Rank Fusion on summary_text.

### Endpoint

```
POST /summaries/search/dense_sparse_rrf
```

### Best For
- Best overall search quality for summaries
- Combining semantic understanding with exact terms
- Balanced search results

### Request Body

**DenseSparseRRFRequest**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| query_text | string | Yes | - | Query text to search |
| limit | integer | No | 10 | Max results (1-100) |
| score_threshold | float | No | null | Min score (0.0-1.0) |
| rrf_k | integer | No | 60 | RRF constant k (1-100) |
| filter_project_id | integer | No | null | Filter by project ID |
| filter_file_id | integer | No | null | Filter by file ID |

### RRF Formula

```
RRF_score = Σ(1 / (k + rank))
```

### Example Request

```bash
curl -X POST "http://localhost:8000/summaries/search/dense_sparse_rrf" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "계약 위반 및 손해배상",
    "limit": 10,
    "rrf_k": 60,
    "filter_project_id": 8
  }'
```

### Example Response

```json
{
  "results": [
    {
      "point_id": "550e8400-e29b-41d4-a716-446655440000",
      "payload": {...},
      "score": 0.0327
    }
  ],
  "total": 10,
  "limit": 10,
  "offset": 0
}
```

### Status Codes

- `200 OK`: Search completed successfully
- `500 Internal Server Error`: Search failed

---

## Recommend Search

Recommendation search using positive and negative examples.

### Endpoint

```
POST /summaries/search/recommend
```

### Best For
- "More summaries like this" searches
- Finding similar document summaries
- Content-based recommendations

### Request Body

**RecommendSearchRequest**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| positive_ids | array[string] | Yes | - | Positive example summary IDs |
| negative_ids | array[string] | No | [] | Negative example summary IDs |
| limit | integer | No | 10 | Max results (1-100) |
| score_threshold | float | No | null | Min score (0.0-1.0) |
| strategy | string | No | "average_vector" | Strategy: "average_vector" or "best_score" |
| filter_project_id | integer | No | null | Filter by project ID |
| filter_file_id | integer | No | null | Filter by file ID |

### Example Request

```bash
curl -X POST "http://localhost:8000/summaries/search/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "positive_ids": [
      "550e8400-e29b-41d4-a716-446655440000",
      "650e8400-e29b-41d4-a716-446655440001"
    ],
    "limit": 10,
    "strategy": "average_vector"
  }'
```

### Example Response

Same structure as Dense Search response.

### Status Codes

- `200 OK`: Search completed successfully
- `500 Internal Server Error`: Search failed

---

## Discover Search

Discovery search using context pairs to explore vector space.

### Endpoint

```
POST /summaries/search/discover
```

### Best For
- Exploratory summary search
- Context-aware discovery
- Finding summaries within specific context

### Request Body

**DiscoverSearchRequest**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| target_text | string | Yes | - | Target text to discover similar items |
| context_pairs | array[ContextPair] | Yes | - | Positive-negative context pairs |
| limit | integer | No | 10 | Max results (1-100) |
| filter_project_id | integer | No | null | Filter by project ID |
| filter_file_id | integer | No | null | Filter by file ID |

**ContextPair** structure:

| Field | Type | Description |
|-------|------|-------------|
| positive | string | Positive example summary ID |
| negative | string | Negative example summary ID |

### Example Request

```bash
curl -X POST "http://localhost:8000/summaries/search/discover" \
  -H "Content-Type: application/json" \
  -d '{
    "target_text": "계약 위반 및 분쟁 해결",
    "context_pairs": [
      {
        "positive": "550e8400-e29b-41d4-a716-446655440000",
        "negative": "650e8400-e29b-41d4-a716-446655440001"
      }
    ],
    "limit": 10
  }'
```

### Example Response

Same structure as Dense Search response.

### Status Codes

- `200 OK`: Search completed successfully
- `500 Internal Server Error`: Search failed

---

## Scroll Search

Paginated search for efficiently retrieving large result sets.

### Endpoint

```
POST /summaries/search/scroll
```

### Best For
- Bulk operations on summaries
- Data export
- Retrieving all summaries

### Request Body

**ScrollSearchRequest**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| limit | integer | No | 100 | Results per page (1-1000) |
| offset | string | No | null | Pagination offset from previous response |
| filter_project_id | integer | No | null | Filter by project ID |
| filter_file_id | integer | No | null | Filter by file ID |
| filter_language | string | No | null | Filter by language |
| filter_pages | array[integer] | No | null | Filter by page numbers |

### Example Request

```bash
# First page
curl -X POST "http://localhost:8000/summaries/search/scroll" \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 100,
    "filter_project_id": 8
  }'

# Next page
curl -X POST "http://localhost:8000/summaries/search/scroll" \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 100,
    "offset": "550e8400-e29b-41d4-a716-446655440100",
    "filter_project_id": 8
  }'
```

### Example Response

```json
{
  "results": [...],
  "total": 100,
  "limit": 100,
  "next_offset": "650e8400-e29b-41d4-a716-446655440200"
}
```

**Note**: `next_offset` is `null` when no more results.

### Status Codes

- `200 OK`: Search completed successfully
- `500 Internal Server Error`: Search failed

---

## Filter Search

Metadata-only filter search (no vector search).

### Endpoint

```
POST /summaries/search/filter
```

### Best For
- Metadata-only queries
- Filtering summaries by attributes
- No semantic search needed

### Request Body

**FilterSearchRequest**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| project_id | integer | No | null | Filter by project ID |
| file_id | integer | No | null | Filter by file ID |
| language | string | No | null | Filter by language |
| limit | integer | No | 10 | Max results (1-100) |
| offset | integer | No | 0 | Result offset |

### Example Request

```bash
curl -X POST "http://localhost:8000/summaries/search/filter" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 8,
    "language": "ko",
    "limit": 20
  }'
```

### Example Response

Same structure as Dense Search response (without scores).

### Status Codes

- `200 OK`: Search completed successfully
- `500 Internal Server Error`: Search failed

---

## Use Cases

### 1. Find Related Summaries

```python
import requests

def find_related_summaries(query, project_id):
    """Find semantically related summaries"""
    response = requests.post(
        "http://localhost:8000/summaries/search/dense",
        json={
            "query_text": query,
            "limit": 10,
            "filter_project_id": project_id
        }
    )
    return response.json()["results"]
```

### 2. Best Quality Summary Search

```python
def search_summaries_hybrid(query, project_id):
    """Best quality search using RRF"""
    response = requests.post(
        "http://localhost:8000/summaries/search/dense_sparse_rrf",
        json={
            "query_text": query,
            "limit": 10,
            "rrf_k": 60,
            "filter_project_id": project_id
        }
    )
    return response.json()["results"]
```

### 3. Find Similar Document Summaries

```python
def find_similar_summaries(summary_id, limit=10):
    """Find summaries similar to given summary"""
    response = requests.post(
        "http://localhost:8000/summaries/search/recommend",
        json={
            "positive_ids": [summary_id],
            "limit": limit,
            "strategy": "average_vector"
        }
    )
    return response.json()["results"]
```

### 4. Export All Project Summaries

```python
def export_project_summaries(project_id):
    """Export all summaries for a project"""
    all_summaries = []
    offset = None

    while True:
        response = requests.post(
            "http://localhost:8000/summaries/search/scroll",
            json={
                "limit": 100,
                "offset": offset,
                "filter_project_id": project_id
            }
        )

        data = response.json()
        all_summaries.extend(data["results"])

        offset = data.get("next_offset")
        if offset is None:
            break

    return all_summaries
```

### 5. Get Summaries by Language

```python
def get_summaries_by_language(project_id, language):
    """Get all summaries in specific language"""
    response = requests.post(
        "http://localhost:8000/summaries/search/filter",
        json={
            "project_id": project_id,
            "language": language,
            "limit": 100
        }
    )
    return response.json()["results"]
```

### 6. Context-Aware Summary Discovery

```python
def discover_summaries_in_context(target_text, positive_id, negative_id):
    """Discover summaries similar to target within context"""
    response = requests.post(
        "http://localhost:8000/summaries/search/discover",
        json={
            "target_text": target_text,
            "context_pairs": [
                {
                    "positive": positive_id,
                    "negative": negative_id
                }
            ],
            "limit": 10
        }
    )
    return response.json()["results"]
```

---

## Search Type Comparison

| Search Type | Use Case | Speed | Accuracy | Requires Vector |
|-------------|----------|-------|----------|-----------------|
| Dense | Semantic similarity | Medium | High | Yes (dense) |
| Sparse | Keyword matching | Fast | Medium | Yes (sparse) |
| MatchText | Exact text match | Fast | High | No |
| RRF | Best overall quality | Slow | Highest | Both |
| Recommend | Similar summaries | Medium | High | Yes (dense) |
| Discover | Context exploration | Medium | Medium | Yes (dense) |
| Scroll | Bulk retrieval | Fast | N/A | No |
| Filter | Metadata only | Fastest | N/A | No |

---

## Differences from Chunks Search

| Feature | Summaries Search | Chunks Search |
|---------|------------------|---------------|
| Collection | ocr_summaries | ocr_chunks |
| Search Field | summary_text | paragraph_texts |
| Content Type | Summaries | OCR chunks |
| Typical Results | Fewer, document-level | More, chunk-level |
| Page Filtering | Less relevant | More relevant |

---

## Important Notes

1. **Embedding Source**: All searches use embeddings generated from `summary_text`
2. **Document-Level**: Summaries represent entire documents, not chunks
3. **Score Interpretation**: Same as chunks (Dense/Sparse: 0-1, RRF: 0.01-0.05)
4. **No Scores**: MatchText and Filter searches don't return scores
5. **Pagination**: Only Scroll and Filter support pagination
6. **Tracing Fields**: Results include `correlation_id` and `request_timestamp`

---

## Related Endpoints

- [Overview](./01_overview.md)
- [Summaries Endpoints](./06_summaries_endpoints.md)
- [Search Chunks Endpoints](./05_search_chunks_endpoints.md)
