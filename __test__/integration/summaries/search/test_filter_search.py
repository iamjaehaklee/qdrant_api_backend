"""
Test Suite: Filter Search (POST /summaries/search/filter)
Tests for metadata-based filtering without vector search
"""

import pytest
from httpx import AsyncClient

from __test__.integration.summaries.conftest import (
    create_test_summary,
    assert_search_response,
    cleanup_summaries
)


@pytest.mark.asyncio
class TestFilterSearch:
    """Test cases for POST /summaries/search/filter endpoint"""

    async def test_filter_by_project_id_only(self, client: AsyncClient):
        """Test: Filter by project_id only"""
        created_ids = []
        for project_id in [1001, 2002, 3003]:
            for i in range(2):
                payload = create_test_summary(
                    project_id=project_id,
                    file_id=21 + i,
                    summary_text=f"프로젝트 {project_id} 요약"
                )
                response = await client.post("/summaries", json=payload)
                created_ids.append(response.json()["point_id"])

        search_payload = {"project_id": 1001, "limit": 100}
        response = await client.post("/summaries/search/filter", json=search_payload)

        assert response.status_code == 200
        data = response.json()
        assert_search_response(data, min_results=2)

        for result in data["results"]:
            assert result["payload"]["project_id"] == 1001

        await cleanup_summaries(client, created_ids)

    async def test_filter_by_file_id_only(self, client: AsyncClient):
        """Test: Filter by file_id only"""
        created_ids = []
        for file_id in [100, 101, 102]:
            payload = create_test_summary(project_id=1001, file_id=file_id, summary_text=f"파일 {file_id}")
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        search_payload = {"file_id": 100, "limit": 100}
        response = await client.post("/summaries/search/filter", json=search_payload)

        assert response.status_code == 200
        for result in response.json()["results"]:
            assert result["payload"]["file_id"] == 100

        await cleanup_summaries(client, created_ids)

    async def test_filter_by_language(self, client: AsyncClient):
        """Test: Filter by language field"""
        created_ids = []
        for lang in ["ko", "en"]:
            payload = {
                "project_id": 1001,
                "file_id": 30,
                "summary_text": f"Language {lang} summary"
            }
            # Note: SummaryCreate doesn't have language field, skipping this test
            # This would require actual data with language field

        # Skip this test as SummaryPayload doesn't have language field
        pytest.skip("Language field not in SummaryPayload schema")

    async def test_filter_combined_project_and_file(self, client: AsyncClient):
        """Test: Filter by both project_id and file_id"""
        created_ids = []

        # Create combinations
        combinations = [(1001, 200), (1001, 201), (2002, 200), (2002, 201)]
        for project_id, file_id in combinations:
            payload = create_test_summary(
                project_id=project_id,
                file_id=file_id,
                summary_text=f"P{project_id}-F{file_id}"
            )
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        search_payload = {"project_id": 1001, "file_id": 200, "limit": 100}
        response = await client.post("/summaries/search/filter", json=search_payload)

        assert response.status_code == 200
        for result in response.json()["results"]:
            assert result["payload"]["project_id"] == 1001
            assert result["payload"]["file_id"] == 200

        await cleanup_summaries(client, created_ids)

    async def test_filter_with_limit(self, client: AsyncClient):
        """Test: Filter with limit parameter"""
        created_ids = []
        for i in range(10):
            payload = create_test_summary(project_id=5005, file_id=40 + i, summary_text=f"리미트 테스트 {i}")
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        search_payload = {"project_id": 5005, "limit": 5}
        response = await client.post("/summaries/search/filter", json=search_payload)

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 5

        await cleanup_summaries(client, created_ids)

    async def test_filter_with_offset(self, client: AsyncClient):
        """Test: Filter with offset for pagination"""
        created_ids = []
        for i in range(10):
            payload = create_test_summary(project_id=6006, file_id=50 + i, summary_text=f"오프셋 테스트 {i}")
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        # First page
        search_payload1 = {"project_id": 6006, "limit": 5, "offset": 0}
        response1 = await client.post("/summaries/search/filter", json=search_payload1)
        assert response1.status_code == 200
        page1_results = response1.json()["results"]

        # Second page
        search_payload2 = {"project_id": 6006, "limit": 5, "offset": 5}
        response2 = await client.post("/summaries/search/filter", json=search_payload2)
        assert response2.status_code == 200
        page2_results = response2.json()["results"]

        # Verify different results
        page1_ids = {r["point_id"] for r in page1_results}
        page2_ids = {r["point_id"] for r in page2_results}
        assert page1_ids.isdisjoint(page2_ids)  # No overlap

        await cleanup_summaries(client, created_ids)

    async def test_filter_no_matching_results(self, client: AsyncClient):
        """Test: Filter with no matching results"""
        search_payload = {"project_id": 99999, "limit": 100}
        response = await client.post("/summaries/search/filter", json=search_payload)

        assert response.status_code == 200
        data = response.json()
        assert_search_response(data, min_results=0, max_results=0)
        assert data["results"] == []

    async def test_filter_empty_filters(self, client: AsyncClient):
        """Test: Filter with no filter parameters (returns all)"""
        created_ids = []
        for i in range(3):
            payload = create_test_summary(project_id=1001, file_id=60 + i, summary_text=f"빈 필터 {i}")
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        search_payload = {"limit": 100}
        response = await client.post("/summaries/search/filter", json=search_payload)

        assert response.status_code == 200
        data = response.json()
        assert "results" in data

        await cleanup_summaries(client, created_ids)
