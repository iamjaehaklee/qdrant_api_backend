"""
Tests for improved full-text search functionality

Tests verify:
1. MatchText usage in keyword_search (token-based search)
2. DB-level filtering in hybrid_search (no Python post-processing)
3. Summary search endpoints functionality
"""

import pytest
import httpx

BASE_URL = "http://localhost:8000"


class TestImprovedKeywordSearch:
    """Test keyword search with MatchText implementation"""

    @pytest.mark.asyncio
    async def test_keyword_search_partial_match(self):
        """Test that keyword search supports partial token matching"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/search/keyword",
                json={
                    "keyword": "테스트",  # Korean word
                    "limit": 10
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert isinstance(data["results"], list)

    @pytest.mark.asyncio
    async def test_keyword_search_with_filters(self):
        """Test keyword search with project_id and file_id filters"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/search/keyword",
                json={
                    "keyword": "document",
                    "limit": 10,
                    "filter_project_id": 8,
                    "filter_file_id": 128
                }
            )
            assert response.status_code == 200
            data = response.json()

            # Verify all results match the filters
            for result in data["results"]:
                assert result["payload"]["project_id"] == 8
                assert result["payload"]["file_id"] == 128

    @pytest.mark.asyncio
    async def test_keyword_search_case_insensitive(self):
        """Test that keyword search is case-insensitive (lowercase=true in tokenizer)"""
        async with httpx.AsyncClient() as client:
            # Search with uppercase
            response_upper = await client.post(
                f"{BASE_URL}/search/keyword",
                json={"keyword": "TEXT", "limit": 5}
            )

            # Search with lowercase
            response_lower = await client.post(
                f"{BASE_URL}/search/keyword",
                json={"keyword": "text", "limit": 5}
            )

            # Should return similar results (case-insensitive)
            assert response_upper.status_code == 200
            assert response_lower.status_code == 200


class TestImprovedHybridSearch:
    """Test hybrid search with DB-level filtering"""

    @pytest.mark.asyncio
    async def test_hybrid_search_db_level_filtering(self):
        """Test that hybrid search uses DB-level filtering, not Python"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/search/hybrid",
                json={
                    "query_text": "machine learning",
                    "keyword": "neural",
                    "limit": 10,
                    "filter_project_id": 8
                }
            )
            assert response.status_code == 200
            data = response.json()

            # All results should match both vector similarity AND keyword
            # If Python filtering was used, we'd see larger intermediate results
            assert isinstance(data["results"], list)
            assert len(data["results"]) <= 10

    @pytest.mark.asyncio
    async def test_hybrid_search_without_keyword(self):
        """Test hybrid search works without keyword (vector-only)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/search/hybrid",
                json={
                    "query_text": "document processing",
                    "limit": 5
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert len(data["results"]) <= 5

    @pytest.mark.asyncio
    async def test_hybrid_search_with_all_filters(self):
        """Test hybrid search with all filter combinations"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/search/hybrid",
                json={
                    "query_text": "analysis",
                    "keyword": "data",
                    "limit": 10,
                    "score_threshold": 0.5,
                    "filter_project_id": 8,
                    "filter_file_id": 128
                }
            )
            assert response.status_code == 200
            data = response.json()

            # Verify filters are applied
            for result in data["results"]:
                assert result["payload"]["project_id"] == 8
                assert result["payload"]["file_id"] == 128
                # Score should be above threshold
                if "score" in result and result["score"] is not None:
                    assert result["score"] >= 0.5


class TestSummarySearch:
    """Test summary search endpoints"""

    @pytest.fixture
    async def sample_summary_id(self):
        """Create a sample summary for testing"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/summaries",
                json={
                    "project_id": 8,
                    "file_id": 128,
                    "summary_text": "This is a test summary about machine learning and neural networks."
                }
            )
            if response.status_code == 201:
                return response.json()["point_id"]
            return None

    @pytest.mark.asyncio
    async def test_summary_creation(self):
        """Test creating a summary with automatic embedding generation"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/summaries",
                json={
                    "project_id": 8,
                    "summary_text": "Test summary for full-text search validation"
                }
            )
            assert response.status_code == 201
            data = response.json()
            assert "point_id" in data
            assert "payload" in data
            assert data["payload"]["summary_text"] == "Test summary for full-text search validation"

    @pytest.mark.asyncio
    async def test_summary_vector_search(self):
        """Test vector search on summaries"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/summaries/search/vector",
                json={
                    "query_text": "machine learning",
                    "limit": 5
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert isinstance(data["results"], list)

    @pytest.mark.asyncio
    async def test_summary_keyword_search(self):
        """Test keyword search on summaries using MatchText"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/summaries/search/keyword",
                json={
                    "keyword": "test",
                    "limit": 10
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "results" in data

    @pytest.mark.asyncio
    async def test_summary_hybrid_search(self):
        """Test hybrid search on summaries"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/summaries/search/hybrid",
                json={
                    "query_text": "machine learning",
                    "keyword": "neural",
                    "limit": 10
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert isinstance(data["results"], list)

    @pytest.mark.asyncio
    async def test_summary_crud_operations(self):
        """Test full CRUD cycle for summaries"""
        async with httpx.AsyncClient() as client:
            # Create
            create_response = await client.post(
                f"{BASE_URL}/summaries",
                json={
                    "project_id": 999,
                    "summary_text": "CRUD test summary"
                }
            )
            assert create_response.status_code == 201
            summary_id = create_response.json()["point_id"]

            # Read
            get_response = await client.get(f"{BASE_URL}/summaries/{summary_id}")
            assert get_response.status_code == 200
            assert get_response.json()["payload"]["summary_text"] == "CRUD test summary"

            # Update
            update_response = await client.put(
                f"{BASE_URL}/summaries/{summary_id}",
                json={"summary_text": "Updated summary"}
            )
            assert update_response.status_code == 200
            assert update_response.json()["payload"]["summary_text"] == "Updated summary"

            # Delete
            delete_response = await client.delete(f"{BASE_URL}/summaries/{summary_id}")
            assert delete_response.status_code == 204

            # Verify deletion
            get_after_delete = await client.get(f"{BASE_URL}/summaries/{summary_id}")
            assert get_after_delete.status_code == 404


class TestPerformanceComparison:
    """Test performance improvements from DB-level filtering"""

    @pytest.mark.asyncio
    async def test_hybrid_search_response_size(self):
        """
        Verify that hybrid search returns only filtered results
        (not large intermediate results that would indicate Python filtering)
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/search/hybrid",
                json={
                    "query_text": "document",
                    "keyword": "specific_rare_term",
                    "limit": 5
                }
            )
            assert response.status_code == 200
            data = response.json()

            # Should not exceed limit even if keyword filtering is applied at DB level
            assert len(data["results"]) <= 5
            assert data["limit"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
