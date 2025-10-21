# Summaries Endpoints (OCR Summaries)

CRUD endpoints for managing document summaries in the `ocr_summaries` collection.

## Table of Contents
- [Create Summary](#create-summary)
- [Get Summary](#get-summary)
- [Update Summary](#update-summary)
- [Delete Summary](#delete-summary)

---

## Create Summary

Create a new summary with automatic embedding generation.

### Endpoint

```
POST /summaries
```

### Request Body

**SummaryCreate** model

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| summary_id | string \| null | No | UUID string (auto-generated if not provided) |
| file_id | integer | Yes | File identifier |
| project_id | integer | Yes | Project identifier |
| storage_file_name | string | Yes | Storage file name |
| original_file_name | string | Yes | Original file name |
| mime_type | string | Yes | MIME type |
| total_pages | integer | Yes | Total pages in document |
| language | string | Yes | ISO language code |
| summary_text | string | Yes | Summary content (used for embeddings) |
| user_id | integer \| null | No | User who requested summary |
| queue_id | integer \| null | No | Queue identifier |
| correlation_id | string \| null | No | Auto-generated UUID for tracing |
| request_timestamp | string \| null | No | Auto-generated ISO timestamp |

### Auto-Generated Fields

If not provided, the following fields are auto-generated:
- `summary_id`: UUID string
- `correlation_id`: UUID string for request tracing
- `request_timestamp`: Current UTC timestamp in ISO format

### Example Request

```bash
curl -X POST "http://localhost:8000/summaries" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": 128,
    "project_id": 8,
    "storage_file_name": "doc_12345.pdf",
    "original_file_name": "부동산계약서.pdf",
    "mime_type": "application/pdf",
    "total_pages": 14,
    "language": "ko",
    "summary_text": "이 문서는 부동산 매매계약서로, 매도인 홍길동과 매수인 김철수 간의 계약 내용을 담고 있습니다. 매매대금은 5억원이며, 계약금, 중도금, 잔금으로 나누어 지급됩니다.",
    "user_id": 42,
    "queue_id": 101
  }'
```

### Example Response

```json
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
    "summary_text": "이 문서는 부동산 매매계약서로...",
    "user_id": 42,
    "queue_id": 101,
    "correlation_id": "650e8400-e29b-41d4-a716-446655440001",
    "request_timestamp": "2025-10-21T12:30:45.123456+00:00"
  }
}
```

### Status Codes

- `201 Created`: Summary created successfully
- `500 Internal Server Error`: Failed to create summary

---

## Get Summary

Retrieve a summary by ID.

### Endpoint

```
GET /summaries/{summary_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| summary_id | string | Yes | UUID of the summary |

### Example Request

```bash
curl -X GET "http://localhost:8000/summaries/550e8400-e29b-41d4-a716-446655440000"
```

### Example Response

```json
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
    "summary_text": "이 문서는 부동산 매매계약서로...",
    "user_id": 42,
    "queue_id": 101,
    "correlation_id": "650e8400-e29b-41d4-a716-446655440001",
    "request_timestamp": "2025-10-21T12:30:45.123456+00:00"
  },
  "score": null
}
```

### Status Codes

- `200 OK`: Summary retrieved successfully
- `404 Not Found`: Summary does not exist
- `500 Internal Server Error`: Failed to retrieve summary

---

## Update Summary

Update a summary's payload and regenerate embeddings if `summary_text` changes.

### Endpoint

```
PUT /summaries/{summary_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| summary_id | string | Yes | UUID of the summary |

### Request Body

**SummaryUpdate** (all fields optional)

| Field | Type | Description |
|-------|------|-------------|
| file_id | integer | Update file ID |
| project_id | integer | Update project ID |
| storage_file_name | string | Update storage file name |
| original_file_name | string | Update original file name |
| mime_type | string | Update MIME type |
| total_pages | integer | Update total pages |
| language | string | Update language |
| summary_text | string | Update summary text (triggers embedding regeneration) |
| user_id | integer | Update user ID |
| queue_id | integer | Update queue ID |

### Example Request

```bash
curl -X PUT "http://localhost:8000/summaries/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "summary_text": "이 문서는 부동산 매매계약서입니다. 주요 내용으로는 매도인과 매수인 정보, 매매대금 5억원, 지급 조건 등이 포함되어 있습니다.",
    "total_pages": 15
  }'
```

### Example Response

```json
{
  "point_id": "550e8400-e29b-41d4-a716-446655440000",
  "payload": {
    "summary_id": "550e8400-e29b-41d4-a716-446655440000",
    "file_id": 128,
    "project_id": 8,
    "storage_file_name": "doc_12345.pdf",
    "original_file_name": "부동산계약서.pdf",
    "mime_type": "application/pdf",
    "total_pages": 15,
    "language": "ko",
    "summary_text": "이 문서는 부동산 매매계약서입니다...",
    "user_id": 42,
    "queue_id": 101,
    "correlation_id": "650e8400-e29b-41d4-a716-446655440001",
    "request_timestamp": "2025-10-21T12:30:45.123456+00:00"
  },
  "score": null
}
```

### Embedding Regeneration

**When summary_text is updated**:
- Dense embedding is regenerated using Gemini
- Sparse embedding is regenerated using TF-IDF
- Entire point is upserted with new vectors

**When other fields are updated**:
- Only payload is updated
- Embeddings remain unchanged

### Status Codes

- `200 OK`: Summary updated successfully
- `404 Not Found`: Summary does not exist
- `500 Internal Server Error`: Failed to update summary

---

## Delete Summary

Delete a summary by ID.

### Endpoint

```
DELETE /summaries/{summary_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| summary_id | string | Yes | UUID of the summary |

### Example Request

```bash
curl -X DELETE "http://localhost:8000/summaries/550e8400-e29b-41d4-a716-446655440000"
```

### Example Response

**Success (204 No Content)**

No response body.

### Status Codes

- `204 No Content`: Summary deleted successfully
- `500 Internal Server Error`: Failed to delete summary

---

## Use Cases

### 1. Create Document Summary

```python
import requests

def create_summary(file_id, project_id, summary_text, **metadata):
    """Create a document summary"""
    data = {
        "file_id": file_id,
        "project_id": project_id,
        "summary_text": summary_text,
        **metadata
    }

    response = requests.post(
        "http://localhost:8000/summaries",
        json=data
    )

    if response.status_code == 201:
        result = response.json()
        print(f"Summary created: {result['point_id']}")
        return result
    else:
        print(f"Error: {response.json()['detail']}")
        return None
```

### 2. Get Summary with Error Handling

```python
def get_summary(summary_id):
    """Retrieve a summary by ID"""
    response = requests.get(
        f"http://localhost:8000/summaries/{summary_id}"
    )

    if response.status_code == 200:
        return response.json()["payload"]
    elif response.status_code == 404:
        print(f"Summary {summary_id} not found")
        return None
    else:
        print(f"Error: {response.json()['detail']}")
        return None
```

### 3. Update Summary Text

```python
def update_summary_text(summary_id, new_text):
    """Update summary text and regenerate embeddings"""
    response = requests.put(
        f"http://localhost:8000/summaries/{summary_id}",
        json={"summary_text": new_text}
    )

    if response.status_code == 200:
        print("Summary updated successfully")
        return response.json()
    elif response.status_code == 404:
        print(f"Summary {summary_id} not found")
        return None
    else:
        print(f"Error: {response.json()['detail']}")
        return None
```

### 4. Update Metadata Only

```python
def update_summary_metadata(summary_id, **metadata):
    """Update summary metadata without regenerating embeddings"""
    response = requests.put(
        f"http://localhost:8000/summaries/{summary_id}",
        json=metadata
    )

    return response.json() if response.status_code == 200 else None
```

### 5. Delete Summary

```python
def delete_summary(summary_id):
    """Delete a summary"""
    response = requests.delete(
        f"http://localhost:8000/summaries/{summary_id}"
    )

    if response.status_code == 204:
        print(f"Summary {summary_id} deleted successfully")
        return True
    else:
        print(f"Error: {response.json()['detail']}")
        return False
```

### 6. Batch Create Summaries

```python
def create_summaries_batch(summaries):
    """Create multiple summaries sequentially"""
    created_ids = []

    for summary_data in summaries:
        response = requests.post(
            "http://localhost:8000/summaries",
            json=summary_data
        )

        if response.status_code == 201:
            point_id = response.json()["point_id"]
            created_ids.append(point_id)
        else:
            print(f"Failed to create summary: {response.json()['detail']}")

    return created_ids
```

### 7. Tracing with Correlation ID

```python
def create_summary_with_tracing(file_id, project_id, summary_text, correlation_id):
    """Create summary with explicit correlation ID for tracing"""
    data = {
        "file_id": file_id,
        "project_id": project_id,
        "summary_text": summary_text,
        "correlation_id": correlation_id,
        "request_timestamp": datetime.utcnow().isoformat() + "+00:00"
    }

    response = requests.post(
        "http://localhost:8000/summaries",
        json=data
    )

    return response.json() if response.status_code == 201 else None
```

---

## Comparison with Chunks

| Feature | Summaries | Chunks |
|---------|-----------|--------|
| Collection | ocr_summaries | ocr_chunks |
| Purpose | Document summaries | OCR content chunks |
| Content Field | summary_text | paragraph_texts |
| Windowing | No | 3-page windows |
| Tracing Fields | correlation_id, request_timestamp | No |
| User Context | user_id, queue_id | No |
| Delete Response | 204 No Content | 200 OK with message |

---

## Important Notes

1. **Automatic Embedding Generation**: Embeddings are generated from `summary_text` field
2. **UUID Format**: Summary IDs are UUID strings
3. **Tracing Support**: `correlation_id` and `request_timestamp` for request tracing
4. **Embedding Regeneration**: Only updating `summary_text` triggers embedding regeneration
5. **Delete Response**: Returns 204 No Content (no response body)
6. **No Batch Endpoints**: Unlike chunks, summaries don't have batch create/delete endpoints

---

## Related Endpoints

- [Overview](./01_overview.md)
- [Search Summaries Endpoints](./07_search_summaries_endpoints.md)
- [Points Endpoints](./03_points_endpoints.md)
