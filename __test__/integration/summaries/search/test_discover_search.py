"""
Test Suite: Discovery Search (POST /summaries/search/discover)
Tests for discovery search using context pairs to explore vector space
"""

import pytest
from httpx import AsyncClient

from __test__.integration.summaries.conftest import (
    create_test_summary,
    assert_search_response,
    cleanup_summaries
)


@pytest.mark.asyncio
class TestDiscoverSearch:
    """Test cases for POST /summaries/search/discover endpoint"""

    async def test_basic_discover_search(self, client: AsyncClient):
        """Test: Basic discovery search with context pairs"""
        created_ids = []
        texts = [
            "원고는 부동산 매매계약을 체결하였습니다.",
            "피고는 계약금을 수령하였습니다.",
            "소유권이전등기 청구소송입니다.",
            "날씨가 맑고 화창합니다."
        ]

        for i, text in enumerate(texts):
            payload = create_test_summary(project_id=1001, file_id=21 + i, summary_text=text)
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        search_payload = {
            "target_text": "부동산 계약 관련 문서",
            "context_pairs": [
                {"positive": created_ids[0], "negative": created_ids[3]}
            ],
            "limit": 10
        }
        response = await client.post("/summaries/search/discover", json=search_payload)

        assert response.status_code == 200
        assert_search_response(response.json(), min_results=1)

        await cleanup_summaries(client, created_ids)

    async def test_discover_multiple_context_pairs(self, client: AsyncClient):
        """Test: Discovery with multiple context pairs"""
        created_ids = []
        for i in range(6):
            payload = create_test_summary(
                project_id=1001,
                file_id=30 + i,
                summary_text=f"문서 {i + 1}번입니다."
            )
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        search_payload = {
            "target_text": "관련 문서 찾기",
            "context_pairs": [
                {"positive": created_ids[0], "negative": created_ids[5]},
                {"positive": created_ids[1], "negative": created_ids[4]},
                {"positive": created_ids[2], "negative": created_ids[3]}
            ],
            "limit": 10
        }
        response = await client.post("/summaries/search/discover", json=search_payload)

        assert response.status_code == 200
        await cleanup_summaries(client, created_ids)

    async def test_discover_with_filters(self, client: AsyncClient):
        """Test: Discovery search with project_id filter"""
        created_ids = []
        for project_id in [1001, 2002]:
            for i in range(2):
                payload = create_test_summary(
                    project_id=project_id,
                    file_id=40 + i,
                    summary_text=f"프로젝트 {project_id} 문서 {i + 1}"
                )
                response = await client.post("/summaries", json=payload)
                created_ids.append(response.json()["point_id"])

        search_payload = {
            "target_text": "문서 탐색",
            "context_pairs": [{"positive": created_ids[0], "negative": created_ids[1]}],
            "filter_project_id": 1001,
            "limit": 10
        }
        response = await client.post("/summaries/search/discover", json=search_payload)

        assert response.status_code == 200
        for result in response.json()["results"]:
            assert result["payload"]["project_id"] == 1001

        await cleanup_summaries(client, created_ids)

    async def test_discover_missing_target_text(self, client: AsyncClient):
        """Test: Error case - missing target_text"""
        import uuid
        search_payload = {
            "context_pairs": [{"positive": str(uuid.uuid4()), "negative": str(uuid.uuid4())}],
            "limit": 10
        }
        response = await client.post("/summaries/search/discover", json=search_payload)
        assert response.status_code == 422

    async def test_discover_missing_context_pairs(self, client: AsyncClient):
        """Test: Error case - missing context_pairs"""
        response = await client.post("/summaries/search/discover", json={"target_text": "테스트"})
        assert response.status_code == 422
