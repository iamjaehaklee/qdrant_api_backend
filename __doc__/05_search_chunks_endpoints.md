# Search Chunks Endpoints

8 different search endpoints for the `ocr_chunks` collection, providing diverse search capabilities from semantic to keyword-based search.

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

Semantic similarity search using Gemini dense embeddings.

### Endpoint

```
POST /search/dense
```

### Best For
- Concept-based search
- Meaning similarity
- Cross-language semantic search

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
curl -X POST "http://localhost:8000/search/dense" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "부동산 매매 계약 조건",
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
        "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
        "file_id": 128,
        "project_id": 8,
        "storage_file_name": "doc_12345.pdf",
        "original_file_name": "contract.pdf",
        "language": "ko",
        "pages": [1, 2, 3],
        "chunk_number": 0,
        "paragraph_texts": [
          "부동산 매매계약서",
          "제1조 (목적물) 매도인과 매수인은 다음 부동산에 관하여 매매계약을 체결한다.",
          "제2조 (매매대금) 매매대금은 금 500,000,000원으로 한다."
        ],
        "chunk_content": {...},
        "created_at": "2025-10-21T12:30:45.123456+00:00"
      },
      "score": 0.89
    },
    ...
  ],
  "total": 5,
  "limit": 5,
  "offset": 0
}
```

### Status Codes

- `200 OK`: Search completed successfully
- `500 Internal Server Error`: Search failed

---

## Sparse Search

Keyword-based search using Kiwi (Korean) or FastEmbed BM25 sparse embeddings.

### Endpoint

```
POST /search/sparse
```

### Best For
- Exact term matching
- Keyword search
- Morphological analysis (Korean)

### Request Body

**SparseSearchRequest** (same structure as DenseSearchRequest)

### Example Request

```bash
curl -X POST "http://localhost:8000/search/sparse" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "매도인 홍길동",
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

Full-text search using MatchText (no morphological analysis).

### Endpoint

```
POST /search/matchtext
```

### Best For
- Phrase matching
- Exact text search
- Fast text matching without morphological analysis

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
curl -X POST "http://localhost:8000/search/matchtext" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "매매계약서",
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

Hybrid search combining dense and sparse vectors using Reciprocal Rank Fusion.

### Endpoint

```
POST /search/dense_sparse_rrf
```

### Best For
- Balanced search combining meaning and keywords
- Best overall search quality
- Combining semantic understanding with exact terms

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

Where:
- `k`: RRF constant (default: 60)
- `rank`: Position in individual search results (1-indexed)

### Example Request

```bash
curl -X POST "http://localhost:8000/search/dense_sparse_rrf" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "계약 조건 위반",
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

**Note**: RRF scores are typically smaller (0.01-0.05 range) than individual search scores.

### Status Codes

- `200 OK`: Search completed successfully
- `500 Internal Server Error`: Search failed

---

## Recommend Search

Recommendation search using positive and negative examples.

### Endpoint

```
POST /search/recommend
```

### Best For
- "More like this" searches
- "Less like that" searches
- Finding similar documents

### Request Body

**RecommendSearchRequest**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| positive_ids | array[string] | Yes | - | Positive example point IDs |
| negative_ids | array[string] | No | [] | Negative example point IDs |
| limit | integer | No | 10 | Max results (1-100) |
| score_threshold | float | No | null | Min score (0.0-1.0) |
| strategy | string | No | "average_vector" | Strategy: "average_vector" or "best_score" |
| filter_project_id | integer | No | null | Filter by project ID |
| filter_file_id | integer | No | null | Filter by file ID |

### Example Request

```bash
curl -X POST "http://localhost:8000/search/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "positive_ids": [
      "550e8400-e29b-41d4-a716-446655440000",
      "650e8400-e29b-41d4-a716-446655440001"
    ],
    "negative_ids": [
      "750e8400-e29b-41d4-a716-446655440002"
    ],
    "limit": 10,
    "strategy": "average_vector"
  }'
```

### Strategies

**average_vector** (default)
- Averages positive example vectors
- Subtracts negative example vectors
- More stable for multiple examples

**best_score**
- Uses best-scoring positive example
- Better for single best example

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
POST /search/discover
```

### Best For
- Exploratory search
- Context-aware discovery
- Finding items within specific context constraints

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
| positive | string | Positive example point ID |
| negative | string | Negative example point ID |

### Example Request

```bash
curl -X POST "http://localhost:8000/search/discover" \
  -H "Content-Type: application/json" \
  -d '{
    "target_text": "계약 위반 사례",
    "context_pairs": [
      {
        "positive": "550e8400-e29b-41d4-a716-446655440000",
        "negative": "650e8400-e29b-41d4-a716-446655440001"
      },
      {
        "positive": "750e8400-e29b-41d4-a716-446655440002",
        "negative": "850e8400-e29b-41d4-a716-446655440003"
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
POST /search/scroll
```

### Best For
- Bulk operations
- Data export
- Retrieving all matching records

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
curl -X POST "http://localhost:8000/search/scroll" \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 100,
    "filter_project_id": 8
  }'

# Next page (using offset from response)
curl -X POST "http://localhost:8000/search/scroll" \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 100,
    "offset": "next_offset_value_from_response",
    "filter_project_id": 8
  }'
```

### Example Response

```json
{
  "results": [...],
  "total": 100,
  "limit": 100,
  "next_offset": "550e8400-e29b-41d4-a716-446655440100"
}
```

**Note**: `next_offset` is `null` when no more results are available.

### Status Codes

- `200 OK`: Search completed successfully
- `500 Internal Server Error`: Search failed

---

## Filter Search

Metadata-only filter search (no vector search).

### Endpoint

```
POST /search/filter
```

### Best For
- Metadata-only queries
- Filtering by specific attributes
- No semantic or keyword search needed

### Request Body

**FilterSearchRequest**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| project_id | integer | No | null | Filter by project ID |
| file_id | integer | No | null | Filter by file ID |
| pages | array[integer] | No | null | Filter by page numbers |
| language | string | No | null | Filter by language |
| limit | integer | No | 10 | Max results (1-100) |
| offset | integer | No | 0 | Result offset |

### Example Request

```bash
curl -X POST "http://localhost:8000/search/filter" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 8,
    "file_id": 128,
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

## Search Type Comparison

| Search Type | Use Case | Speed | Accuracy | Requires Vector |
|-------------|----------|-------|----------|-----------------|
| Dense | Semantic similarity | Medium | High | Yes (dense) |
| Sparse | Keyword matching | Fast | Medium | Yes (sparse) |
| MatchText | Exact text match | Fast | High | No |
| RRF | Best overall quality | Slow | Highest | Both |
| Recommend | Similar documents | Medium | High | Yes (dense) |
| Discover | Context exploration | Medium | Medium | Yes (dense) |
| Scroll | Bulk retrieval | Fast | N/A | No |
| Filter | Metadata only | Fastest | N/A | No |

---

## Use Cases

### 1. Semantic Search

```python
import requests

def semantic_search(query, project_id):
    """Find semantically similar chunks"""
    response = requests.post(
        "http://localhost:8000/search/dense",
        json={
            "query_text": query,
            "limit": 10,
            "filter_project_id": project_id
        }
    )
    return response.json()["results"]
```

### 2. Hybrid Search (Best Quality)

```python
def hybrid_search(query, project_id):
    """Best overall search quality using RRF"""
    response = requests.post(
        "http://localhost:8000/search/dense_sparse_rrf",
        json={
            "query_text": query,
            "limit": 10,
            "rrf_k": 60,
            "filter_project_id": project_id
        }
    )
    return response.json()["results"]
```

### 3. Find Similar Documents

```python
def find_similar(point_id, limit=10):
    """Find documents similar to given chunk"""
    response = requests.post(
        "http://localhost:8000/search/recommend",
        json={
            "positive_ids": [point_id],
            "limit": limit,
            "strategy": "average_vector"
        }
    )
    return response.json()["results"]
```

### 4. Export All Project Data

```python
def export_project_chunks(project_id):
    """Export all chunks for a project"""
    all_chunks = []
    offset = None

    while True:
        response = requests.post(
            "http://localhost:8000/search/scroll",
            json={
                "limit": 100,
                "offset": offset,
                "filter_project_id": project_id
            }
        )

        data = response.json()
        all_chunks.extend(data["results"])

        offset = data.get("next_offset")
        if offset is None:
            break

    return all_chunks
```

### 5. Filter by Page Range

```python
def search_by_pages(project_id, pages):
    """Find all chunks containing specific pages"""
    response = requests.post(
        "http://localhost:8000/search/filter",
        json={
            "project_id": project_id,
            "pages": pages,
            "limit": 100
        }
    )
    return response.json()["results"]
```

---

## Important Notes

1. **Embedding Generation**: Query embeddings are generated automatically
2. **Score Interpretation**:
   - Dense/Sparse: Higher is better (0.0-1.0 typical range)
   - RRF: Lower scores (0.01-0.05 typical)
3. **Filters**: All search types support project_id and file_id filters
4. **Pagination**: Only Scroll and Filter searches support pagination
5. **No Scores**: MatchText and Filter searches don't return scores

---

## Related Endpoints

- [Overview](./01_overview.md)
- [Points Endpoints](./03_points_endpoints.md)
- [Document AI Endpoints](./04_documentai_endpoints.md)
