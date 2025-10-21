# Points Endpoints (OCR Chunks)

CRUD endpoints for managing OCR chunk points in the `ocr_chunks` collection.

## Table of Contents
- [Create Point](#create-point)
- [Batch Create Points](#batch-create-points)
- [Get Point](#get-point)
- [Update Point](#update-point)
- [Delete Point](#delete-point)
- [Batch Delete Points](#batch-delete-points)
- [Get All Chunks by Project](#get-all-chunks-by-project)

---

## Create Point

Create a single OCR chunk point with automatic embedding generation.

### Endpoint

```
POST /points
```

### Request Body

**OCRChunkCreate** model

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| chunk_id | string \| null | No | UUID string (auto-generated if not provided) |
| file_id | integer | Yes | File identifier |
| project_id | integer | Yes | Project identifier |
| storage_file_name | string | Yes | Storage file name |
| original_file_name | string | Yes | Original file name |
| mime_type | string | Yes | MIME type (e.g., "application/pdf") |
| total_pages | integer | Yes | Total pages in document |
| processing_duration_seconds | integer | No | Processing time (default: 0) |
| language | string | Yes | ISO language code (e.g., "ko", "en") |
| pages | array[integer] | Yes | Page numbers in this chunk |
| chunk_number | integer | Yes | Sequential chunk index |
| paragraph_texts | array[string] | Yes | Text content (used for embeddings) |
| chunk_content | ChunkContent | Yes | Detailed paragraph data |
| page_dimensions | array[PageDimension] | Yes | Page width/height info |

### Example Request

```bash
curl -X POST "http://localhost:8000/points" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": 128,
    "project_id": 8,
    "storage_file_name": "doc_12345.pdf",
    "original_file_name": "contract.pdf",
    "mime_type": "application/pdf",
    "total_pages": 14,
    "processing_duration_seconds": 45,
    "language": "ko",
    "pages": [1, 2, 3],
    "chunk_number": 0,
    "paragraph_texts": [
      "부동산 매매계약서",
      "매도인: 홍길동",
      "매수인: 김철수"
    ],
    "chunk_content": {
      "paragraphs": [
        {
          "paragraph_id": "p1",
          "idx_in_page": 0,
          "text": "부동산 매매계약서",
          "page": 1,
          "bbox": {"x": 100, "y": 50, "width": 400, "height": 30},
          "type": "heading",
          "confidence_score": 0.98
        }
      ]
    },
    "page_dimensions": [
      {"page": 1, "width": 595, "height": 842},
      {"page": 2, "width": 595, "height": 842},
      {"page": 3, "width": 595, "height": 842}
    ]
  }'
```

### Example Response

```json
{
  "message": "Point created successfully",
  "point_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Status Codes

- `201 Created`: Point created successfully
- `500 Internal Server Error`: Failed to create point

---

## Batch Create Points

Create multiple OCR chunk points in a single request.

### Endpoint

```
POST /points/batch
```

### Request Body

**BatchCreateRequest**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| chunks | array[OCRChunkCreate] | Yes | Array of chunks to create |

### Example Request

```bash
curl -X POST "http://localhost:8000/points/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "chunks": [
      {
        "file_id": 128,
        "project_id": 8,
        "storage_file_name": "doc_12345.pdf",
        "original_file_name": "contract.pdf",
        "mime_type": "application/pdf",
        "total_pages": 14,
        "language": "ko",
        "pages": [1, 2, 3],
        "chunk_number": 0,
        "paragraph_texts": ["Text chunk 1"],
        "chunk_content": {"paragraphs": []},
        "page_dimensions": []
      },
      {
        "file_id": 128,
        "project_id": 8,
        "storage_file_name": "doc_12345.pdf",
        "original_file_name": "contract.pdf",
        "mime_type": "application/pdf",
        "total_pages": 14,
        "language": "ko",
        "pages": [3, 4, 5],
        "chunk_number": 1,
        "paragraph_texts": ["Text chunk 2"],
        "chunk_content": {"paragraphs": []},
        "page_dimensions": []
      }
    ]
  }'
```

### Example Response

```json
{
  "message": "Created 2 points successfully",
  "point_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "650e8400-e29b-41d4-a716-446655440001"
  ],
  "count": 2
}
```

### Status Codes

- `201 Created`: Points created successfully
- `500 Internal Server Error`: Failed to create points

---

## Get Point

Retrieve an OCR chunk point by ID.

### Endpoint

```
GET /points/{point_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| point_id | string | Yes | UUID of the point |

### Example Request

```bash
curl -X GET "http://localhost:8000/points/550e8400-e29b-41d4-a716-446655440000"
```

### Example Response

```json
{
  "point_id": "550e8400-e29b-41d4-a716-446655440000",
  "payload": {
    "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
    "file_id": 128,
    "project_id": 8,
    "storage_file_name": "doc_12345.pdf",
    "original_file_name": "contract.pdf",
    "mime_type": "application/pdf",
    "total_pages": 14,
    "processing_duration_seconds": 45,
    "language": "ko",
    "pages": [1, 2, 3],
    "chunk_number": 0,
    "paragraph_texts": ["부동산 매매계약서", "매도인: 홍길동"],
    "chunk_content": {
      "paragraphs": [...]
    },
    "page_dimensions": [...],
    "created_at": "2025-10-21T12:30:45.123456+00:00"
  },
  "score": null
}
```

### Status Codes

- `200 OK`: Point retrieved successfully
- `404 Not Found`: Point does not exist
- `500 Internal Server Error`: Failed to retrieve point

---

## Update Point

Update an OCR chunk point. If `paragraph_texts` is updated, embeddings will be regenerated.

### Endpoint

```
PUT /points/{point_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| point_id | string | Yes | UUID of the point |

### Request Body

**OCRChunkUpdate** (all fields optional)

| Field | Type | Description |
|-------|------|-------------|
| file_id | integer | Update file ID |
| project_id | integer | Update project ID |
| storage_file_name | string | Update storage file name |
| original_file_name | string | Update original file name |
| paragraph_texts | array[string] | Update texts (triggers embedding regeneration) |
| chunk_content | ChunkContent | Update chunk content |

### Example Request

```bash
curl -X PUT "http://localhost:8000/points/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "paragraph_texts": ["Updated text content"],
    "storage_file_name": "updated_doc.pdf"
  }'
```

### Example Response

```json
{
  "message": "Point updated successfully",
  "point_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Status Codes

- `200 OK`: Point updated successfully
- `404 Not Found`: Point does not exist
- `500 Internal Server Error`: Failed to update point

---

## Delete Point

Delete an OCR chunk point by ID.

### Endpoint

```
DELETE /points/{point_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| point_id | string | Yes | UUID of the point |

### Example Request

```bash
curl -X DELETE "http://localhost:8000/points/550e8400-e29b-41d4-a716-446655440000"
```

### Example Response

```json
{
  "message": "Point deleted successfully",
  "point_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Status Codes

- `200 OK`: Point deleted successfully
- `500 Internal Server Error`: Failed to delete point

---

## Batch Delete Points

Delete multiple OCR chunk points in a single request.

### Endpoint

```
DELETE /points/batch/delete
```

### Request Body

**BatchDeleteRequest**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| point_ids | array[string] | Yes | Array of point IDs to delete |

### Example Request

```bash
curl -X DELETE "http://localhost:8000/points/batch/delete" \
  -H "Content-Type: application/json" \
  -d '{
    "point_ids": [
      "550e8400-e29b-41d4-a716-446655440000",
      "650e8400-e29b-41d4-a716-446655440001"
    ]
  }'
```

### Example Response

```json
{
  "message": "Deleted 2 points successfully",
  "count": 2
}
```

### Status Codes

- `200 OK`: Points deleted successfully
- `500 Internal Server Error`: Failed to delete points

---

## Get All Chunks by Project

Retrieve all OCR chunks for a given project ID.

### Endpoint

```
GET /points/project/{project_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| project_id | integer | Yes | Project identifier |

### Example Request

```bash
curl -X GET "http://localhost:8000/points/project/8"
```

### Example Response

```json
{
  "project_id": 8,
  "total_count": 15,
  "chunks": [
    {
      "point_id": "550e8400-e29b-41d4-a716-446655440000",
      "payload": {
        "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
        "file_id": 128,
        "project_id": 8,
        "storage_file_name": "doc_12345.pdf",
        "original_file_name": "contract.pdf",
        "mime_type": "application/pdf",
        "total_pages": 14,
        "language": "ko",
        "pages": [1, 2, 3],
        "chunk_number": 0,
        "paragraph_texts": ["..."],
        "chunk_content": {...},
        "page_dimensions": [...],
        "created_at": "2025-10-21T12:30:45.123456+00:00"
      },
      "score": null
    },
    ...
  ]
}
```

### Status Codes

- `200 OK`: Chunks retrieved successfully (may return empty array)
- `500 Internal Server Error`: Failed to retrieve chunks

---

## Use Cases

### 1. Single Document Upload

```python
import requests

def upload_ocr_chunk(chunk_data):
    """Upload single OCR chunk"""
    response = requests.post(
        "http://localhost:8000/points",
        json=chunk_data
    )
    return response.json()["point_id"]
```

### 2. Batch Document Processing

```python
def upload_document_chunks(chunks):
    """Upload all chunks from a document at once"""
    response = requests.post(
        "http://localhost:8000/points/batch",
        json={"chunks": chunks}
    )
    return response.json()["point_ids"]
```

### 3. Update Chunk Text

```python
def update_chunk_text(point_id, new_texts):
    """Update chunk text and regenerate embeddings"""
    response = requests.put(
        f"http://localhost:8000/points/{point_id}",
        json={"paragraph_texts": new_texts}
    )
    return response.json()
```

### 4. Get All Project Documents

```python
def get_project_chunks(project_id):
    """Retrieve all chunks for a project"""
    response = requests.get(
        f"http://localhost:8000/points/project/{project_id}"
    )
    data = response.json()
    return data["chunks"]
```

### 5. Delete Document

```python
def delete_document(project_id, file_id):
    """Delete all chunks for a specific file"""
    # First, get all chunks
    chunks = requests.get(
        f"http://localhost:8000/points/project/{project_id}"
    ).json()["chunks"]

    # Filter by file_id
    point_ids = [
        chunk["point_id"]
        for chunk in chunks
        if chunk["payload"]["file_id"] == file_id
    ]

    # Batch delete
    response = requests.delete(
        "http://localhost:8000/points/batch/delete",
        json={"point_ids": point_ids}
    )
    return response.json()
```

---

## Important Notes

1. **Automatic Embedding Generation**: Embeddings are automatically generated from `paragraph_texts` field
2. **UUID Format**: Point IDs are UUID strings, not integers
3. **3-Page Windows**: Each chunk typically contains 3 pages with 1-page overlap
4. **No Pagination**: `GET /points/project/{project_id}` returns all chunks without limit
5. **Embedding Regeneration**: Updating `paragraph_texts` triggers embedding regeneration

---

## Related Endpoints

- [Overview](./01_overview.md)
- [Document AI Endpoints](./04_documentai_endpoints.md)
- [Search Chunks Endpoints](./05_search_chunks_endpoints.md)
