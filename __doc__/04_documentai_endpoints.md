# Document AI OCR Endpoints

API endpoints for processing Google Document AI OCR results and storing them as Qdrant chunks.

## Table of Contents
- [Store Document AI OCR Chunks](#store-document-ai-ocr-chunks)
- [Health Check](#health-check)
- [Processing Pipeline](#processing-pipeline)
- [Window Strategy](#window-strategy)

---

## Store Document AI OCR Chunks

Process Google Document AI OCR results and store them as chunks in Qdrant.

### Endpoint

```
POST /api/documentai-ocr/store-chunks
```

### Process Overview

1. Extracts paragraphs from Document AI pages
2. Creates 3-page sliding windows (with 1-page overlap)
3. Generates dense and sparse embeddings for each chunk
4. Stores chunks in Qdrant `ocr_chunks` collection

### Request Body

**DocumentAIStoreChunksRequest**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| document_ai_result | DocumentAIResult | Yes | Google Document AI processing result |
| file_metadata | FileMetadata | Yes | File metadata information |

**DocumentAIResult** structure:

| Field | Type | Description |
|-------|------|-------------|
| pages | array[Page] | Array of page objects |
| text | string | Full document text |

**Page** structure:

| Field | Type | Description |
|-------|------|-------------|
| pageNumber | integer | Page number (1-indexed) |
| dimension | Dimension | Page dimensions |
| blocks | array[Block] | Text blocks on page |

**FileMetadata** structure:

| Field | Type | Description |
|-------|------|-------------|
| file_id | integer | File identifier |
| project_id | integer | Project identifier |
| storage_file_name | string | Storage file name |
| original_file_name | string | Original file name |
| mime_type | string | MIME type |
| total_pages | integer | Total page count |
| processing_duration_seconds | integer | Processing duration |
| language | string | ISO language code |

### Example Request

```bash
curl -X POST "http://localhost:8000/api/documentai-ocr/store-chunks" \
  -H "Content-Type: application/json" \
  -d '{
    "document_ai_result": {
      "pages": [
        {
          "pageNumber": 1,
          "dimension": {
            "width": 595,
            "height": 842,
            "unit": "PIXEL"
          },
          "blocks": [
            {
              "layout": {
                "textAnchor": {
                  "textSegments": [
                    {"startIndex": "0", "endIndex": "15"}
                  ]
                },
                "confidence": 0.98,
                "boundingPoly": {
                  "normalizedVertices": [
                    {"x": 0.1, "y": 0.05},
                    {"x": 0.9, "y": 0.05},
                    {"x": 0.9, "y": 0.1},
                    {"x": 0.1, "y": 0.1}
                  ]
                }
              },
              "type": "heading"
            }
          ],
          "detectedLanguages": [
            {
              "languageCode": "ko",
              "confidence": 0.99
            }
          ]
        }
      ],
      "text": "부동산 매매계약서\\n매도인: 홍길동\\n매수인: 김철수\\n"
    },
    "file_metadata": {
      "file_id": 128,
      "project_id": 8,
      "storage_file_name": "doc_12345.pdf",
      "original_file_name": "부동산계약서.pdf",
      "mime_type": "application/pdf",
      "total_pages": 14,
      "processing_duration_seconds": 45,
      "language": "ko"
    }
  }'
```

### Example Response

```json
{
  "message": "Successfully processed 5 chunks",
  "chunk_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "650e8400-e29b-41d4-a716-446655440001",
    "750e8400-e29b-41d4-a716-446655440002",
    "850e8400-e29b-41d4-a716-446655440003",
    "950e8400-e29b-41d4-a716-446655440004"
  ],
  "total_chunks": 5,
  "file_id": 128,
  "project_id": 8,
  "total_pages": 14,
  "language": "ko"
}
```

### Status Codes

- `201 Created`: Chunks created successfully
- `400 Bad Request`: Invalid Document AI result or metadata
- `500 Internal Server Error`: Processing or storage failed

### Error Response

```json
{
  "detail": "Processing error: Invalid page structure at page 5"
}
```

---

## Health Check

Check if the Document AI OCR processing service is operational.

### Endpoint

```
GET /api/documentai-ocr/health
```

### Example Request

```bash
curl -X GET "http://localhost:8000/api/documentai-ocr/health"
```

### Example Response

**Healthy**

```json
{
  "status": "healthy",
  "service": "Document AI OCR Processor",
  "qdrant_connected": true,
  "collection_exists": true
}
```

**Unhealthy**

```json
{
  "status": "unhealthy",
  "service": "Document AI OCR Processor",
  "error": "Qdrant connection failed"
}
```

### Status Codes

- `200 OK`: Health check completed

---

## Processing Pipeline

### 1. Paragraph Extraction

**DocumentAITransformer** extracts paragraphs from Document AI pages:

- Converts normalized bounding boxes to pixel coordinates
- Creates `Paragraph` objects with text, bbox, page, type, confidence
- Assigns unique `paragraph_id` to each paragraph

### 2. Window Generation

**OCRWindowGenerator** creates 3-page sliding windows:

```
14-page document → Windows:
[1-3], [3-5], [5-7], [7-9], [9-11], [11-13], [13-14]
```

**Rules**:
- Window size: 3 pages (configurable)
- Overlap: 1 page
- Last window may have fewer pages

### 3. Embedding Generation

For each window:
- **Dense embedding**: Gemini `embedding-001` (1536 dimensions)
  - Concatenates all paragraph texts with `\n`
  - Task type: `retrieval_document`
- **Sparse embedding**: TF-IDF-like token frequency
  - Hash-based indexing (modulo 100,000)
  - Normalized frequency values

### 4. Storage

Stores each window as a point in Qdrant:
- Point ID: UUID string
- Named vectors: `ocr-dense-vector`, `ocr-sparse-vector`
- Payload: Complete chunk metadata and content

---

## Window Strategy

### Why 3-Page Windows?

**Context Preservation**
- Maintains semantic context across page boundaries
- Reduces fragmentation of multi-page concepts

**Overlap Benefits**
- 1-page overlap ensures no information gaps
- Pages at window boundaries appear in 2 chunks
- Improves search recall for cross-page content

### Window Examples

**Example 1: 14-Page Document**

```
Total pages: 14
Window size: 3
Overlap: 1

Windows:
Chunk 0: Pages [1, 2, 3]
Chunk 1: Pages [3, 4, 5]    ← Page 3 overlaps
Chunk 2: Pages [5, 6, 7]    ← Page 5 overlaps
Chunk 3: Pages [7, 8, 9]    ← Page 7 overlaps
Chunk 4: Pages [9, 10, 11]  ← Page 9 overlaps
Chunk 5: Pages [11, 12, 13] ← Page 11 overlaps
Chunk 6: Pages [13, 14]     ← Last chunk (2 pages)
```

**Example 2: 5-Page Document**

```
Total pages: 5
Window size: 3
Overlap: 1

Windows:
Chunk 0: Pages [1, 2, 3]
Chunk 1: Pages [3, 4, 5]    ← Page 3 overlaps
```

**Example 3: 2-Page Document**

```
Total pages: 2
Window size: 3
Overlap: 1

Windows:
Chunk 0: Pages [1, 2]       ← Single chunk (< window size)
```

---

## Use Cases

### 1. Process Single Document

```python
import requests
import json

def process_documentai_result(docai_result, file_metadata):
    """Process Document AI result and store chunks"""
    response = requests.post(
        "http://localhost:8000/api/documentai-ocr/store-chunks",
        json={
            "document_ai_result": docai_result,
            "file_metadata": file_metadata
        }
    )

    if response.status_code == 201:
        data = response.json()
        print(f"Created {data['total_chunks']} chunks")
        return data["chunk_ids"]
    else:
        print(f"Error: {response.json()['detail']}")
        return None
```

### 2. Batch Document Processing

```python
def process_multiple_documents(documents):
    """Process multiple documents sequentially"""
    results = []

    for doc in documents:
        chunk_ids = process_documentai_result(
            doc["docai_result"],
            doc["file_metadata"]
        )
        results.append({
            "file_id": doc["file_metadata"]["file_id"],
            "chunk_ids": chunk_ids
        })

    return results
```

### 3. Error Handling

```python
def safe_process_document(docai_result, file_metadata, max_retries=3):
    """Process document with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "http://localhost:8000/api/documentai-ocr/store-chunks",
                json={
                    "document_ai_result": docai_result,
                    "file_metadata": file_metadata
                },
                timeout=60
            )

            if response.status_code == 201:
                return response.json()
            elif response.status_code == 400:
                # Validation error - don't retry
                print(f"Validation error: {response.json()['detail']}")
                return None
            else:
                # Server error - retry
                print(f"Attempt {attempt + 1} failed, retrying...")
                continue

        except requests.exceptions.Timeout:
            print(f"Timeout on attempt {attempt + 1}")
            continue

    return None
```

---

## Important Notes

1. **Input Format**: Must match Google Document AI output structure exactly
2. **Page Numbering**: Document AI uses 1-indexed page numbers
3. **Language Detection**: Uses first page's detected language for all chunks
4. **Async Processing**: Embedding generation is synchronous (rate-limited by Gemini API)
5. **Window Overlap**: Pages at window boundaries appear in multiple chunks
6. **Empty Pages**: Pages without blocks are still included in windows

---

## Related Endpoints

- [Overview](./01_overview.md)
- [Points Endpoints](./03_points_endpoints.md)
- [Search Chunks Endpoints](./05_search_chunks_endpoints.md)
