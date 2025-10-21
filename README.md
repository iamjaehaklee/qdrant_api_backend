# Qdrant OCR API Backend

FastAPI server for OCR chunks CRUD and search operations with Qdrant vector database.

## Features

- **CRUD Operations**: Create, Read, Update, Delete OCR chunk points
- **Vector Search**: Semantic search using Gemini embeddings (dense + sparse)
- **Keyword Search**: Full-text search in paragraph texts
- **Hybrid Search**: Combined vector and keyword search
- **Filter Search**: Metadata-based filtering (project_id, file_id, pages, language)
- **Batch Operations**: Bulk create and delete
- **Auto Embeddings**: Automatic embedding generation from text
- **🆕 Document AI OCR Integration**: Process Google Document AI OCR results with automatic chunking

## Tech Stack

- **FastAPI**: Modern Python web framework
- **Qdrant**: Vector database for similarity search
- **Gemini API**: Google's embedding models
  - `gemini-embedding-001`: Dense embeddings (1536 dim via Matryoshka Representation Learning)
  - **Sparse embeddings**: Hash-based token frequency (custom implementation: tokenization → frequency count → hash indexing → normalization)

## Project Structure

```
qdrant_api_backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application
│   ├── config.py                  # Settings and configuration
│   ├── models.py                  # Pydantic models
│   ├── models_documentai.py       # Document AI models
│   ├── embeddings.py              # Gemini embedding generation
│   ├── qdrant_service.py          # Qdrant client wrapper
│   ├── routers/
│   │   ├── points.py              # CRUD endpoints
│   │   ├── search.py              # Search endpoints
│   │   ├── health.py              # Health check
│   │   └── documentai_ocr.py      # Document AI OCR endpoint
│   └── services/
│       ├── ocr_window_generator.py       # 3-page window generation
│       ├── documentai_transformer.py     # Document AI data transformation
│       └── documentai_ocr_processor.py   # Main OCR processor
├── __test__/
│   ├── unit/
│   │   ├── test_api.py            # API integration tests
│   │   ├── test_data.json         # Test data
│   │   └── create/
│   │       ├── test_documentai_api.py      # Document AI test script
│   │       └── test_documentai_sample.json # Document AI test data
├── .env                           # Environment variables
├── requirements.txt
├── CLAUDE.md                      # Developer documentation
└── README.md
```

## Installation

### 1. Clone the repository

```bash
cd /Users/jaehaklee/qdrant_api_backend
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Edit `.env` file and add your Gemini API key:

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

The Qdrant configuration is already set up in `.env`.

## Running the Server

### Development Mode

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 6030
```

uvicorn app.main:app --host 0.0.0.0 --port 6030 --workers 3 --loop uvloop --http httptools --timeout-keep-alive 10 --backlog 2048



#### If port 6030 is already in use

Before starting the server on port 6030, you can stop any existing process using that port:

```bash
# macOS/Linux (graceful stop)
kill -15 $(lsof -ti:6030) 2>/dev/null || true

# If it’s still occupied (force kill)
kill -9 $(lsof -ti:6030) 2>/dev/null || true
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health & Info

- `GET /health` - Check service health and Qdrant connection
- `GET /collection/info` - Get Qdrant collection information
- `GET /` - Root endpoint with API info

### CRUD Operations

- `POST /points` - Create a single OCR chunk point
- `POST /points/batch` - Create multiple points in batch
- `GET /points/{point_id}` - Retrieve a point by ID
- `PUT /points/{point_id}` - Update a point
- `DELETE /points/{point_id}` - Delete a point
- `DELETE /points/batch/delete` - Delete multiple points

### Search Operations

- `POST /search/vector` - Vector similarity search
- `POST /search/keyword` - Full-text keyword search
- `POST /search/hybrid` - Combined vector + keyword search
- `POST /search/filter` - Metadata filter search

### Document AI OCR Integration

- `POST /api/documentai-ocr/store-chunks` - Process and store Document AI OCR results
- `GET /api/documentai-ocr/health` - Health check for Document AI OCR service

## Usage Examples

### 1. Health Check

```bash
curl http://localhost:8000/health
```

### 2. Create OCR Chunk

```bash
curl -X POST http://localhost:8000/points \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": 128,
    "project_id": 8,
    "storage_file_name": "example.pdf",
    "original_file_name": "example.pdf",
    "mime_type": "application/pdf",
    "total_pages": 10,
    "language": "ko",
    "pages": [1, 2],
    "chunk_number": 1,
    "paragraph_texts": ["텍스트 내용 1", "텍스트 내용 2"],
    "chunk_content": {
      "paragraphs": [...]
    },
    "page_dimensions": [...]
  }'
```

### 3. Vector Search

```bash
curl -X POST http://localhost:8000/search/vector \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "계약 내용",
    "limit": 10,
    "filter_project_id": 8
  }'
```

### 4. Keyword Search

```bash
curl -X POST http://localhost:8000/search/keyword \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "판결",
    "limit": 10,
    "filter_project_id": 8
  }'
```

### 5. Hybrid Search

```bash
curl -X POST http://localhost:8000/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "계약 조건",
    "keyword": "판결",
    "limit": 10
  }'
```

### 6. Filter Search

```bash
curl -X POST http://localhost:8000/search/filter \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 8,
    "file_id": 128,
    "language": "ko",
    "limit": 10
  }'
```

## Data Model

### OCR Chunk Structure

```python
{
  "chunk_id": "uuid",
  "file_id": 128,
  "project_id": 8,
  "storage_file_name": "example.pdf",
  "original_file_name": "example.pdf",
  "mime_type": "application/pdf",
  "total_pages": 10,
  "language": "ko",
  "pages": [1, 2, 3],
  "chunk_number": 1,
  "paragraph_texts": ["text1", "text2"],
  "chunk_content": {
    "paragraphs": [
      {
        "paragraph_id": "uuid",
        "idx_in_page": 0,
        "text": "paragraph text",
        "page": 1,
        "bbox": {"x": 0, "y": 0, "width": 100, "height": 50},
        "type": "body",
        "confidence_score": 0.95
      }
    ]
  },
  "page_dimensions": [
    {"page": 1, "width": 1680, "height": 2379}
  ],
  "created_at": "2025-08-24T17:05:48.767817+00:00"
}
```

## Configuration

All configuration is managed through environment variables in `.env`:

- `QDRANT_URL`: Qdrant server URL
- `QDRANT_MASTER_API_KEY`: Qdrant master API key
- `GEMINI_API_KEY`: Google Gemini API key
- `DENSE_VECTOR_NAME`: Dense vector name (ocr-dense-vector)
- `SPARSE_VECTOR_NAME`: Sparse vector name (ocr-sparse-vector)

## Document AI OCR Integration

### Overview

The Document AI OCR integration allows you to process Google Document AI OCR results and automatically store them as chunks in Qdrant with proper embeddings.

### Features

- **Automatic Paragraph Extraction**: Extracts text blocks from Document AI pages
- **3-Page Sliding Windows**: Creates overlapping chunks (e.g., [1-3], [3-5], [5-7])
- **1-Page Overlap**: Ensures context continuity across chunks
- **Automatic Embeddings**: Generates dense and sparse embeddings for each chunk
- **Coordinate Transformation**: Converts normalized coordinates to pixel coordinates

### Usage

#### 1. Prepare Document AI Result

Get OCR results from Google Document AI (handled by external service):

```json
{
  "text": "Full document text...",
  "pages": [
    {
      "pageNumber": 1,
      "dimension": {"width": 1681, "height": 2379},
      "blocks": [...],
      "detected_languages": [{"languageCode": "ko"}]
    }
  ]
}
```

#### 2. Send to API

```bash
curl -X POST http://localhost:8000/api/documentai-ocr/store-chunks \
  -H "Content-Type: application/json" \
  -d @request_payload.json
```

#### 3. Response

```json
{
  "success": true,
  "chunk_ids": ["uuid1", "uuid2", ...],
  "total_chunks": 7,
  "processing_time": 2.34,
  "summary": {
    "total_pages": 14,
    "total_paragraphs": 156,
    "total_windows": 7,
    "language": "ko"
  }
}
```

### Window Strategy

For a 14-page document, chunks are created as:
- Chunk 1: Pages [1, 2, 3]
- Chunk 2: Pages [3, 4, 5]
- Chunk 3: Pages [5, 6, 7]
- Chunk 4: Pages [7, 8, 9]
- Chunk 5: Pages [9, 10, 11]
- Chunk 6: Pages [11, 12, 13]
- Chunk 7: Pages [13, 14]

The 1-page overlap ensures that content spanning page boundaries is captured in multiple chunks.

### Testing

Run the test script to verify the integration:

```bash
# Make sure server is running
uvicorn app.main:app --reload

# In another terminal, run the test
python __test__/unit/create/test_documentai_api.py
```

The test script will:
1. Check the health endpoint
2. Send sample Document AI data
3. Verify chunk creation
4. Display results

## Development

### Install dev dependencies

```bash
pip install pytest pytest-asyncio httpx
```

### Run tests

```bash
pytest
```

### Test Document AI OCR Endpoint

```bash
python __test__/unit/create/test_documentai_api.py
```

## Notes

- The API currently has no authentication (development mode)
- CORS is configured to allow all origins (configure for production)
- Embeddings are generated automatically from `paragraph_texts`
- Both dense and sparse vectors are stored for hybrid search

## License

MIT

## Support

For issues and questions, please open an issue in the repository.
