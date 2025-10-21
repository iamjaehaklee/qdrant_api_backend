# Qdrant OCR API - Overview

## Introduction

FastAPI backend for OCR chunks CRUD and semantic search operations using Qdrant vector database. Integrates with Google Gemini for embeddings and Google Document AI for OCR processing.

**Version**: 0.1.0

## Core Purpose

Store OCR-processed document chunks with dual embeddings (dense + sparse) and provide semantic/hybrid search capabilities across two collections:
- `ocr_chunks`: OCR chunk data with 3-page sliding windows
- `ocr_summaries`: Document summary data

## Base URL

```
http://localhost:8000
```

## Architecture

### Collections

**ocr_chunks**
- Stores OCR-processed document chunks
- 3-page sliding windows with 1-page overlap
- Dual embeddings: dense (Gemini) + sparse (TF-IDF-like)

**ocr_summaries**
- Stores document summaries
- Dense and sparse embeddings on summary_text field

### Embedding Strategy

**Dense Embeddings**
- Model: Gemini `embedding-001`
- Dimensions: 1536 (truncated from 3072)
- Task type: `retrieval_document` for documents, `retrieval_query` for queries
- Use case: Semantic similarity search

**Sparse Embeddings**
- Method: TF-IDF-like token frequency
- Hash-based indexing (modulo 100,000)
- Normalized frequency values
- Use case: Keyword matching

## Authentication & Security

**Current State**: Development mode
- No authentication required
- CORS: Allows all origins (`*`)
- **Production Warning**: Add authentication and configure CORS before deployment

## Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Quick Start

### 1. Start the Server

```bash
# Development mode (auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode (multi-worker)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. Check Health

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "qdrant_connected": true,
  "collection_exists": true,
  "message": null
}
```

### 3. Explore API

Visit http://localhost:8000/docs for interactive API exploration.

## API Organization

### Health & Info
- Health checks
- Collection information

### OCR Chunks (ocr_chunks collection)
- **Points**: CRUD operations for chunks
- **Document AI**: Process Google Document AI results
- **Search**: 8 search types (dense, sparse, matchtext, RRF, recommend, discover, scroll, filter)

### Summaries (ocr_summaries collection)
- **Summaries**: CRUD operations for summaries
- **Search**: 8 search types (same as chunks)

## Environment Variables

Required in `.env`:

```env
# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_MASTER_API_KEY=your_api_key

# Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key

# Vector Configuration
DENSE_VECTOR_NAME=ocr-dense-vector
SPARSE_VECTOR_NAME=ocr-sparse-vector
DENSE_MODEL=gemini-embedding-001
DENSE_DIMENSION=1536
```

## Common Response Codes

- `200 OK`: Successful GET/PUT/DELETE
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE (summaries)
- `400 Bad Request`: Invalid input data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Error Response Format

```json
{
  "detail": "Error description message"
}
```

## Next Steps

- [Health Endpoints](./02_health_endpoints.md)
- [Points Endpoints](./03_points_endpoints.md)
- [Document AI Endpoints](./04_documentai_endpoints.md)
- [Search Chunks Endpoints](./05_search_chunks_endpoints.md)
- [Summaries Endpoints](./06_summaries_endpoints.md)
- [Search Summaries Endpoints](./07_search_summaries_endpoints.md)
