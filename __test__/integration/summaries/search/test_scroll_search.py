"""
Test Suite: Scroll Search (POST /summaries/search/scroll)
Tests for scroll search with pagination for large result sets
"""

import pytest
from httpx import AsyncClient

from __test__.integration.summaries.conftest import (
    create_test_summary,
    cleanup_summaries
)


@pytest.mark.asyncio
class TestScrollSearch:
    """Test cases for POST /summaries/search/scroll endpoint"""

    async def test_basic_scroll_search(self, client: AsyncClient):
        """Test: Basic scroll search without filters"""
        created_ids = []
        for i in range(10):
            payload = create_test_summary(
                project_id=1001,
                file_id=21 + i,
                summary_text=f"스크롤 테스트 문서 {i + 1}번입니다."
            )
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        search_payload = {"limit": 100}
        response = await client.post("/summaries/search/scroll", json=search_payload)

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "next_offset" in data

        await cleanup_summaries(client, created_ids)

    async def test_scroll_with_limit(self, client: AsyncClient):
        """Test: Scroll search with custom limit"""
        created_ids = []
        for i in range(10):
            payload = create_test_summary(project_id=1001, file_id=30 + i, summary_text=f"문서 {i + 1}")
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        search_payload = {"limit": 5}
        response = await client.post("/summaries/search/scroll", json=search_payload)

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 5

        await cleanup_summaries(client, created_ids)

    async def test_scroll_with_project_filter(self, client: AsyncClient):
        """Test: Scroll with project_id filter"""
        created_ids = []
        for project_id in [1001, 2002]:
            for i in range(3):
                payload = create_test_summary(
                    project_id=project_id,
                    file_id=40 + i,
                    summary_text=f"프로젝트 {project_id} 문서"
                )
                response = await client.post("/summaries", json=payload)
                created_ids.append(response.json()["point_id"])

        search_payload = {"filter_project_id": 1001, "limit": 100}
        response = await client.post("/summaries/search/scroll", json=search_payload)

        assert response.status_code == 200
        for result in response.json()["results"]:
            assert result["payload"]["project_id"] == 1001

        await cleanup_summaries(client, created_ids)

    async def test_scroll_with_file_filter(self, client: AsyncClient):
        """Test: Scroll with file_id filter"""
        created_ids = []
        for file_id in [100, 101]:
            payload = create_test_summary(project_id=1001, file_id=file_id, summary_text=f"파일 {file_id}")
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        search_payload = {"filter_file_id": 100, "limit": 100}
        response = await client.post("/summaries/search/scroll", json=search_payload)

        assert response.status_code == 200
        for result in response.json()["results"]:
            assert result["payload"]["file_id"] == 100

        await cleanup_summaries(client, created_ids)

    async def test_scroll_pagination_with_offset(self, client: AsyncClient):
        """Test: Pagination using offset"""
        created_ids = []
        for i in range(10):
            payload = create_test_summary(project_id=1001, file_id=50 + i, summary_text=f"페이지 {i + 1}")
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        # First page
        search_payload = {"limit": 5}
        response = await client.post("/summaries/search/scroll", json=search_payload)
        assert response.status_code == 200
        first_page = response.json()
        next_offset = first_page.get("next_offset")

        # Second page if offset available
        if next_offset:
            search_payload["offset"] = next_offset
            response2 = await client.post("/summaries/search/scroll", json=search_payload)
            assert response2.status_code == 200

        await cleanup_summaries(client, created_ids)

    async def test_scroll_invalid_limit(self, client: AsyncClient):
        """Test: Error case - invalid limit (>1000)"""
        response = await client.post("/summaries/search/scroll", json={"limit": 2000})
        assert response.status_code == 422
