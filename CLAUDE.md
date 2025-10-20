# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI backend for OCR chunks CRUD and semantic search operations using Qdrant vector database. Integrates with Google Gemini for embeddings and Google Document AI for OCR processing.

**Core Purpose**: Store OCR-processed document chunks with dual embeddings (dense + sparse) and provide semantic/hybrid search capabilities.

## Development Commands

### Environment Setup

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install pytest pytest-asyncio httpx
```

### Running the Server

```bash
# Development mode (auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode (multi-worker)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Important**: Server must be running before executing tests.

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest __test__/unit/test_api.py

# Run with verbose output
pytest -v

# Test Document AI integration (requires running server)
python __test__/unit/create/test_documentai_api.py
```

### API Documentation

Access interactive docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Architecture

### Core Components

**FastAPI Application (`app/main.py`)**
- Entry point with router registration
- CORS middleware configured (currently allows all origins)
- Startup/shutdown event handlers

**Configuration (`app/config.py`)**
- Pydantic Settings for environment variable management
- Loads from `.env` file
- Validates required config on startup

**Qdrant Service (`app/qdrant_service.py`)**
- Single source of truth for Qdrant operations
- Global instance: `qdrant_service` (singleton pattern)
- Handles vector operations and query building
- Auto-generates embeddings on create/update

**Embedding Generation (`app/embeddings.py`)**
- **Dense embeddings**: Gemini `embedding-001` model
  - Returns 1536 to match collection schema
  - Uses `task_type="retrieval_document"` for documents
  - Uses `task_type="retrieval_query"` for search queries
- **Sparse embeddings**: TF-IDF-like token frequency
  - Hash-based indexing (modulo 100,000)
  - Normalized frequency values
  - Not using Gemini 2.5-flash-lite (config name is historical)

### Data Flow

**Document AI OCR Processing Pipeline**:
1. `documentai_ocr.py` router receives Document AI result
2. `DocumentAIOCRProcessor` orchestrates the pipeline
3. `DocumentAITransformer` extracts paragraphs from pages
4. `OCRWindowGenerator` creates 3-page sliding windows with 1-page overlap
5. `QdrantService` generates embeddings and stores chunks

**3-Page Window Strategy**:
- For 14-page document: `[1-3], [3-5], [5-7], [7-9], [9-11], [11-12], [13-14]`
- 1-page overlap ensures context continuity
- Each window becomes one chunk in Qdrant

**Search Operations**:
- **Vector search**: Dense embedding similarity using Gemini embeddings
- **Keyword search**: Text matching on `paragraph_texts` field
- **Hybrid search**: Combines vector + keyword with score fusion
- **Filter search**: Metadata filtering (project_id, file_id, pages, language)

### Data Models

**Key Pydantic Models** (`app/models.py`):
- `OCRChunkCreate`: Request model for creating chunks (embeddings auto-generated)
- `OCRChunkPayload`: Complete payload stored in Qdrant
- `OCRChunkResponse`: Response model with optional score
- `ChunkContent`: Nested structure with `Paragraph` list
- `Paragraph`: Text, bbox, page, type, confidence_score

**Document AI Models** (`app/models_documentai.py`):
- Input models matching Google Document AI output structure
- `DocumentAIStoreChunksRequest`: Combines DocumentAI result + file metadata
- `DocumentAIStoreChunksResponse`: Processing summary and chunk IDs

### Qdrant Collection Schema

**Collection**: `ocr_chunks` (configured in `.env`)

**Named Vectors**:
- `ocr-dense-vector`: 1536 dimensions (float32)
- `ocr-sparse-vector`: Sparse indices/values

**Payload Fields**:
- `chunk_id` (str): UUID identifier
- `file_id` (int): Foreign key to file
- `project_id` (int): Foreign key to project
- `storage_file_name`, `original_file_name` (str)
- `mime_type` (str)
- `total_pages` (int)
- `language` (str): ISO language code
- `pages` (list[int]): Page numbers in chunk
- `chunk_number` (int): Sequential chunk index
- `paragraph_texts` (list[str]): Extracted text for embedding
- `chunk_content` (dict): Full paragraph objects with bbox
- `page_dimensions` (list[dict]): Width/height per page
- `created_at` (str): ISO timestamp

## Development Guidelines

### Adding New Endpoints

1. Create router in `app/routers/` following existing pattern
2. Import and register in `app/main.py`: `app.include_router(your_router.router)`
3. Use dependency injection for `QdrantService` if needed
4. Follow Pydantic model pattern for request/response validation

### Modifying Embeddings

**Critical**: Dimension changes require Qdrant collection recreation
- Current: 1536 dimensions (truncated from Gemini's 3072)
- Changing dimensions breaks existing collection schema
- To change: Drop collection and recreate with new schema

**Embedding Functions**:
- `generate_dense_embedding(text)`: Raw dense vector
- `generate_dense_embedding_from_paragraphs(paragraphs)`: Joins with `\n`
- `generate_query_dense_embedding(query)`: Uses `retrieval_query` task type
- `generate_sparse_embedding(text)`: Token frequency sparse vector

### Environment Variables

Required in `.env`:
- `QDRANT_URL`: Qdrant server URL
- `QDRANT_MASTER_API_KEY`: Master API key for Qdrant authentication
- `GEMINI_API_KEY`: Google Gemini API key
- `DENSE_VECTOR_NAME`: Named vector for dense (default: `ocr-dense-vector`)
- `SPARSE_VECTOR_NAME`: Named vector for sparse (default: `ocr-sparse-vector`)
- `DENSE_MODEL`: Gemini model name (default: `gemini-embedding-001`)
- `DENSE_DIMENSION`: Vector dimension (default: 1536)

**Note**: The API works with two collections (`ocr_chunks` and `ocr_summaries`). The `QdrantService` can be instantiated with a specific collection name, defaulting to `ocr_chunks` for backward compatibility.

**Security Note**: `.env` file contains credentials - never commit to version control.

### Common Operations

**Creating a new chunk**:
```python
# Embeddings generated automatically from paragraph_texts
chunk = OCRChunkCreate(
    file_id=128,
    project_id=8,
    paragraph_texts=["text1", "text2"],
    chunk_content=ChunkContent(paragraphs=[...]),
    # ... other required fields
)
point_id = qdrant_service.create_point(chunk)
```

**Updating with new embeddings**:
```python
# Only updates if paragraph_texts changes
update = OCRChunkUpdate(paragraph_texts=["new text"])
qdrant_service.update_point(point_id, update)
```

**Vector search**:
```python
# Query embedding generated automatically
results = qdrant_service.vector_search(
    query_text="search term",
    limit=10,
    filter_project_id=8
)
```

### Testing Strategy

**Test Organization**:
- `__test__/unit/`: Unit and integration tests
- `__test__/sample/`: Sample data files
- Tests require running server on `localhost:8000`

**Running Specific Tests**:
```bash
# Document AI integration test
python __test__/unit/create/test_documentai_api.py

# API endpoints test
pytest __test__/unit/test_api.py -v
```

### Code Organization Patterns

**Router Pattern**:
- Each router file handles one domain (points, search, health, documentai_ocr)
- Uses `APIRouter` with prefix and tags
- Returns Pydantic models for response validation

**Service Pattern**:
- `QdrantService`: Database operations (singleton)
- `DocumentAIOCRProcessor`: Business logic for Document AI processing
- `DocumentAITransformer`: Data transformation
- `OCRWindowGenerator`: Window calculation logic

**Configuration Pattern**:
- Single `Settings` class with Pydantic validation
- Global `settings` instance imported where needed
- Case-insensitive env var loading

## Known Constraints

- **No authentication**: Development mode, add auth for production
- **CORS open**: Currently allows all origins
- **Embedding dimension fixed**: 1536 dimensions (collection schema)
- **Sparse vectors**: Simple TF-IDF, not using advanced models
- **Synchronous embedding calls**: No batch optimization for Gemini API
- **No pagination**: Search endpoints return fixed limit results
- **UUID-based point IDs**: Uses string UUIDs, not integers

## Performance Considerations

- Batch operations available: `batch_create_points`, `batch_delete_points`
- Embedding generation is synchronous and rate-limited by Gemini API
- Large documents (>100 pages) will create many chunks (~50 chunks)
- Consider batch processing for multiple documents

## Troubleshooting

**Server won't start**:
1. Check `.env` file exists with required variables
2. Verify virtual environment is activated
3. Confirm Qdrant URL is accessible
4. Test Gemini API key with embedding generation

**Embedding dimension errors**:
- Collection expects 1536 dimensions
- Verify truncation in `embeddings.py`: `[:settings.dense_dimension]`
- Check `DENSE_DIMENSION` in `.env`

**Search returns no results**:
- Verify collection has points: `GET /collection/info`
- Check filter parameters (project_id, file_id)
- Test with `GET /health` to verify Qdrant connection

**Document AI processing fails**:
- Validate input JSON matches `DocumentAIStoreChunksRequest` schema
- Check page structure has required fields: `pageNumber`, `dimension`, `blocks`
- Verify language detection data exists
