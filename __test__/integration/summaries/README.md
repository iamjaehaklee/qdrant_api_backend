# OCR Summaries Collection - Integration Test Suite

종합 테스트 suite for `ocr_summaries` Qdrant collection CRUD and Search operations.

## 📁 Test Structure

```
__test__/integration/summaries/
├── conftest.py                          # Pytest fixtures and utilities
├── README.md                            # This file
├── crud/
│   ├── test_create_summaries.py        # POST /summaries
│   ├── test_read_summaries.py          # GET /summaries/{id}
│   ├── test_update_summaries.py        # PUT /summaries/{id}
│   └── test_delete_summaries.py        # DELETE /summaries/{id}
└── search/
    ├── test_dense_search.py            # POST /summaries/search/dense
    ├── test_sparse_search.py           # POST /summaries/search/sparse
    ├── test_matchtext_search.py        # POST /summaries/search/matchtext
    ├── test_hybrid_rrf_search.py       # POST /summaries/search/dense_sparse_rrf
    ├── test_recommend_search.py        # POST /summaries/search/recommend
    ├── test_discover_search.py         # POST /summaries/search/discover
    ├── test_scroll_search.py           # POST /summaries/search/scroll
    └── test_filter_search.py           # POST /summaries/search/filter
```

## 🎯 Test Coverage

### CRUD Operations (4 endpoints)

#### 1. `test_create_summaries.py`
- ✅ Single summary creation with basic fields
- ✅ UUID auto-generation vs manual specification
- ✅ Optional file_id handling
- ✅ Batch creation (10 summaries)
- ✅ Real sample data creation
- ✅ Long text handling (>1000 characters)
- ✅ Korean legal terminology
- ❌ Error cases: missing fields, invalid types, empty text

**Test Count**: 15 tests

#### 2. `test_read_summaries.py`
- ✅ Single summary retrieval
- ✅ All payload fields verification
- ✅ Multiple summaries sequential read
- ✅ Long text preservation
- ✅ Korean text encoding preservation
- ✅ Optional field handling (file_id=None)
- ✅ Timestamp format validation
- ❌ Error cases: non-existent ID, invalid UUID, deleted summary

**Test Count**: 13 tests

#### 3. `test_update_summaries.py`
- ✅ Metadata-only updates (no embedding regeneration)
- ✅ Summary_text updates (automatic embedding regeneration)
- ✅ Combined metadata + text updates
- ✅ Partial field updates
- ✅ Long text updates
- ✅ Korean legal terminology updates
- ✅ Multiple sequential updates
- ❌ Error cases: non-existent summary, invalid types, empty payload

**Test Count**: 13 tests

#### 4. `test_delete_summaries.py`
- ✅ Single summary deletion
- ✅ Delete → Read returns 404
- ✅ Batch deletion (5 summaries)
- ✅ Idempotent deletion (delete twice)
- ✅ Delete → Search not found
- ✅ Long text summary deletion
- ✅ Special character handling
- ❌ Error cases: non-existent ID, invalid UUID

**Test Count**: 11 tests

### Search Operations (8 endpoints)

#### 5. `test_dense_search.py` - Semantic Similarity Search
- ✅ Basic semantic search with Korean queries
- ✅ Score threshold filtering
- ✅ Limit control (5, 10, 20 results)
- ✅ Project_id filtering
- ✅ File_id filtering
- ✅ Combined filters (project + file)
- ✅ Semantic similarity verification (different words, similar meaning)
- ✅ Real sample data search
- ✅ Empty results handling
- ❌ Error cases: missing query_text, invalid limit, invalid threshold

**Test Count**: 12 tests

#### 6. `test_sparse_search.py` - Keyword-Based Search
- ✅ Basic keyword search with Korean
- ✅ Korean morphological analysis (Kiwi)
- ✅ Project_id and file_id filters
- ✅ Score threshold filtering
- ❌ Error case: missing query_text

**Test Count**: 5 tests

#### 7. `test_matchtext_search.py` - Full-Text Matching
- ✅ Basic full-text matching
- ✅ Exact phrase matching
- ✅ Project_id and file_id filters
- ✅ No results handling
- ❌ Error case: missing query_text

**Test Count**: 5 tests

#### 8. `test_hybrid_rrf_search.py` - Hybrid Dense+Sparse RRF
- ✅ Basic hybrid search combining semantic + keyword
- ✅ RRF k parameter variation (30, 60, 100)
- ✅ Project_id and file_id filters
- ✅ Score threshold filtering
- ❌ Error cases: missing query_text, invalid k value

**Test Count**: 6 tests

#### 9. `test_recommend_search.py` - Recommendation System
- ✅ Positive examples only
- ✅ Positive + negative examples
- ✅ Strategy: average_vector
- ✅ Strategy: best_score
- ✅ Project_id filtering
- ❌ Error case: missing positive_ids

**Test Count**: 6 tests

#### 10. `test_discover_search.py` - Context-Based Discovery
- ✅ Basic discovery with context pairs
- ✅ Multiple context pairs (3 pairs)
- ✅ Project_id filtering
- ❌ Error cases: missing target_text, missing context_pairs

**Test Count**: 5 tests

#### 11. `test_scroll_search.py` - Paginated Large Result Sets
- ✅ Basic scroll without filters
- ✅ Custom limit control
- ✅ Project_id filtering
- ✅ File_id filtering
- ✅ Pagination with offset
- ❌ Error case: invalid limit (>1000)

**Test Count**: 6 tests

#### 12. `test_filter_search.py` - Metadata-Only Filtering
- ✅ Filter by project_id only
- ✅ Filter by file_id only
- ✅ Combined project_id + file_id filters
- ✅ Limit parameter
- ✅ Offset parameter for pagination
- ✅ No matching results
- ✅ Empty filters (returns all)

**Test Count**: 8 tests

## 📊 Total Test Statistics

- **Total Test Files**: 12
- **Total Test Cases**: ~100+ tests
- **Endpoints Covered**: 12/12 (100%)
- **Test Data**: 51 real legal document summaries from `부동산소유권등기소송`

## 🛠️ Test Data

### Sample Data Location
```
__test__/sample_generated/부동산소유권등기소송/ocr_summaries/
```

### Sample Data Structure
```json
{
  "summary_id": "de21465d-c1d5-4fd2-a0d4-4e2159136c41",
  "project_id": 1001,
  "file_id": 21,
  "summary_text": "원고 김철수이 피고 이영희에게 발송한 내용증명...",
  "created_at": "2024-08-22T06:00:00+00:00"
}
```

### Data Files (51 files)
- 갑1호증 ~ 갑21호증 (원고 증거)
- 을1호증 ~ 을8호증 (피고 증거)
- 소장, 답변서, 준비서면
- 변론녹취록, 증인신문조서
- 감정서, 계약서, 영수증, 등기부등본 등

## 🚀 Running Tests

### Prerequisites
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install test dependencies
pip install pytest pytest-asyncio httpx

# 3. Start FastAPI server (REQUIRED)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run All Tests
```bash
# All summaries tests
pytest __test__/integration/summaries/ -v

# CRUD tests only
pytest __test__/integration/summaries/crud/ -v

# Search tests only
pytest __test__/integration/summaries/search/ -v
```

### Run Specific Test Files
```bash
# Create tests
pytest __test__/integration/summaries/crud/test_create_summaries.py -v

# Dense search tests
pytest __test__/integration/summaries/search/test_dense_search.py -v

# Hybrid RRF tests
pytest __test__/integration/summaries/search/test_hybrid_rrf_search.py -v
```

### Run Specific Test Cases
```bash
# Single test method
pytest __test__/integration/summaries/crud/test_create_summaries.py::TestCreateSummaries::test_create_single_summary_basic -v

# All tests in a class
pytest __test__/integration/summaries/search/test_dense_search.py::TestDenseSearch -v
```

## 🔧 Test Utilities (conftest.py)

### Fixtures
- `client`: AsyncClient for HTTP requests
- `sample_summaries`: 5 sample summaries
- `single_sample_summary`: 1 sample summary
- `all_sample_summaries`: All 51 sample summaries
- `cleanup_test_summaries`: Auto-cleanup created summaries

### Helper Functions
- `load_sample_summaries(limit)`: Load sample data from JSON files
- `load_single_summary(filename)`: Load specific file
- `create_test_summary(...)`: Generate test summary payload
- `cleanup_summary(client, id)`: Delete single summary
- `cleanup_summaries(client, ids)`: Delete multiple summaries
- `assert_summary_response(data, expected)`: Validate response structure
- `assert_search_response(data, min, max)`: Validate search results
- `assert_scores_descending(results)`: Verify score ordering

## 📝 Test Scenarios

### Workflow Tests
Each test file includes integration scenarios:

1. **Create → Read → Update → Delete** (CRUD workflow)
2. **Create → Search → Verify** (Search workflow)
3. **Update Text → Search → Find New Content** (Embedding regeneration)
4. **Delete → Search → Not Found** (Deletion verification)
5. **Batch Operations** (Multiple summaries handling)

### Edge Cases
- Empty strings
- Very long texts (>1000 characters)
- Korean special characters
- Invalid UUIDs
- Non-existent IDs
- Invalid data types
- Missing required fields
- Out-of-range parameters

### Performance Tests
- Batch creation (10+ summaries)
- Large result sets (scroll search)
- Pagination efficiency
- Multiple sequential operations

## ✅ Validation Checks

Each test validates:
1. **HTTP Status Codes**: 200, 201, 204, 404, 422, 500
2. **Response Schema**: Pydantic model compliance
3. **Data Accuracy**: Input values match output
4. **Embedding Generation**: Vector search returns results
5. **Filter Accuracy**: Filtered results meet criteria
6. **Score Ordering**: Search results sorted by relevance
7. **Pagination**: Offset and limit work correctly

## 🔍 Test Methodology

### Test Structure
```python
async def test_scenario_name(self, client: AsyncClient):
    """Test: Description
    Expected: Expected outcome
    """
    # 1. Setup: Create test data
    created_ids = []
    payload = create_test_summary(...)
    response = await client.post("/summaries", json=payload)
    created_ids.append(response.json()["point_id"])

    # 2. Execute: Perform operation
    search_payload = {...}
    response = await client.post("/summaries/search/dense", json=search_payload)

    # 3. Assert: Verify results
    assert response.status_code == 200
    assert_search_response(response.json())

    # 4. Cleanup: Remove test data
    await cleanup_summaries(client, created_ids)
```

## 🚨 Important Notes

### Server Requirement
**CRITICAL**: FastAPI server MUST be running before executing tests.
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Test Isolation
- Each test creates its own data
- Cleanup after each test (no pollution)
- Uses unique project_ids/file_ids to avoid conflicts

### Embedding Generation
- Dense embeddings: Gemini `embedding-001` (1536 dimensions)
- Sparse embeddings: Kiwi (Korean) or FastEmbed BM25
- Automatic generation on create/update

### Real Data Usage
Tests use actual legal document summaries from `부동산소유권등기소송` case files for realistic validation.

## 📚 Related Documentation

- FastAPI Server: `/app/main.py`
- Summaries Router: `/app/routers/summaries.py`
- Search Router: `/app/routers/search_summaries.py`
- Data Models: `/app/models.py`, `/app/models_search.py`
- Project README: `/CLAUDE.md`

## 🐛 Troubleshooting

### Tests Fail with Connection Error
→ Ensure FastAPI server is running on `localhost:8000`

### Tests Fail with 404 on Search
→ Verify Qdrant collection `ocr_summaries` exists

### Embedding Errors
→ Check `GEMINI_API_KEY` in `.env` file

### Cleanup Not Working
→ Check Qdrant connection and API key permissions
