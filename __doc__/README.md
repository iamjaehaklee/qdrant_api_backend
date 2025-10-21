# Qdrant OCR API Documentation

Complete API documentation for the Qdrant OCR backend server.

## Quick Links

- **Interactive Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)
- **OpenAPI Spec**: [openapi.json](./openapi.json)

## Documentation Index

### 1. [Overview](./01_overview.md)
- Project introduction and architecture
- Quick start guide
- Environment setup
- API organization

### 2. [Health Endpoints](./02_health_endpoints.md)
- Health check
- Collection information
- Service monitoring

### 3. [Points Endpoints](./03_points_endpoints.md)
CRUD operations for OCR chunks (`ocr_chunks` collection):
- Create point (single/batch)
- Get point
- Update point
- Delete point (single/batch)
- Get all chunks by project

### 4. [Document AI Endpoints](./04_documentai_endpoints.md)
Process Google Document AI OCR results:
- Store chunks from Document AI
- 3-page window strategy
- Processing pipeline
- Embedding generation

### 5. [Search Chunks Endpoints](./05_search_chunks_endpoints.md)
8 search types for `ocr_chunks` collection:
- Dense search (semantic)
- Sparse search (keyword)
- MatchText search (full-text)
- Dense+Sparse RRF (hybrid)
- Recommend search (similar items)
- Discover search (context-aware)
- Scroll search (pagination)
- Filter search (metadata)

### 6. [Summaries Endpoints](./06_summaries_endpoints.md)
CRUD operations for summaries (`ocr_summaries` collection):
- Create summary
- Get summary
- Update summary
- Delete summary

### 7. [Search Summaries Endpoints](./07_search_summaries_endpoints.md)
8 search types for `ocr_summaries` collection:
- Dense search
- Sparse search
- MatchText search
- Dense+Sparse RRF
- Recommend search
- Discover search
- Scroll search
- Filter search

## Collections

### ocr_chunks
- **Purpose**: OCR-processed document chunks
- **Content**: 3-page sliding windows with 1-page overlap
- **Embeddings**: Dense (Gemini 1536d) + Sparse (TF-IDF)
- **Endpoints**: `/points`, `/search/*`

### ocr_summaries
- **Purpose**: Document summaries
- **Content**: Full document summaries
- **Embeddings**: Dense (Gemini 1536d) + Sparse (TF-IDF)
- **Endpoints**: `/summaries`, `/summaries/search/*`

## API Categories

### Health & Monitoring
- `GET /health`
- `GET /collection/info`
- `GET /api/documentai-ocr/health`

### OCR Chunks Management
- `POST /points` - Create chunk
- `POST /points/batch` - Batch create
- `GET /points/{point_id}` - Get chunk
- `PUT /points/{point_id}` - Update chunk
- `DELETE /points/{point_id}` - Delete chunk
- `DELETE /points/batch/delete` - Batch delete
- `GET /points/project/{project_id}` - Get all by project

### Document AI Processing
- `POST /api/documentai-ocr/store-chunks` - Process Document AI result

### Chunks Search
- `POST /search/dense` - Semantic search
- `POST /search/sparse` - Keyword search
- `POST /search/matchtext` - Full-text search
- `POST /search/dense_sparse_rrf` - Hybrid search
- `POST /search/recommend` - Recommendation
- `POST /search/discover` - Discovery
- `POST /search/scroll` - Pagination
- `POST /search/filter` - Metadata filter

### Summaries Management
- `POST /summaries` - Create summary
- `GET /summaries/{summary_id}` - Get summary
- `PUT /summaries/{summary_id}` - Update summary
- `DELETE /summaries/{summary_id}` - Delete summary

### Summaries Search
- `POST /summaries/search/dense`
- `POST /summaries/search/sparse`
- `POST /summaries/search/matchtext`
- `POST /summaries/search/dense_sparse_rrf`
- `POST /summaries/search/recommend`
- `POST /summaries/search/discover`
- `POST /summaries/search/scroll`
- `POST /summaries/search/filter`

## Quick Examples

### Health Check
```bash
curl http://localhost:8000/health
```

### Create OCR Chunk
```bash
curl -X POST "http://localhost:8000/points" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": 128,
    "project_id": 8,
    "paragraph_texts": ["Sample text"],
    ...
  }'
```

### Search Chunks
```bash
curl -X POST "http://localhost:8000/search/dense" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "계약 조건",
    "limit": 10,
    "filter_project_id": 8
  }'
```

### Create Summary
```bash
curl -X POST "http://localhost:8000/summaries" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": 128,
    "project_id": 8,
    "summary_text": "Document summary",
    ...
  }'
```

### Search Summaries
```bash
curl -X POST "http://localhost:8000/summaries/search/dense" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "계약서 요약",
    "limit": 10
  }'
```

## Development

### Start Server
```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Generate OpenAPI JSON
```bash
python generate_openapi.py
```

### Run Tests
```bash
pytest
pytest -v  # Verbose output
```

## Environment Variables

Required in `.env`:
```env
QDRANT_URL=http://localhost:6333
QDRANT_MASTER_API_KEY=your_api_key
GEMINI_API_KEY=your_gemini_api_key
DENSE_VECTOR_NAME=ocr-dense-vector
SPARSE_VECTOR_NAME=ocr-sparse-vector
DENSE_MODEL=gemini-embedding-001
DENSE_DIMENSION=1536
```

## Architecture Overview

```
FastAPI Application
├── Collections
│   ├── ocr_chunks (3-page windows)
│   └── ocr_summaries (document summaries)
├── Embeddings
│   ├── Dense: Gemini embedding-001 (1536d)
│   └── Sparse: TF-IDF-like (100k indices)
└── Search Types
    ├── Vector: Dense, Sparse, RRF
    ├── Recommendation: Recommend, Discover
    └── Filtering: MatchText, Filter, Scroll
```

## Common Status Codes

- `200 OK` - Successful GET/PUT/DELETE
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE (summaries)
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Support

- **GitHub Issues**: Report bugs and feature requests
- **Interactive Docs**: http://localhost:8000/docs
- **Project Documentation**: See [CLAUDE.md](../CLAUDE.md)

---

**Version**: 0.1.0
**Last Updated**: 2025-10-21
