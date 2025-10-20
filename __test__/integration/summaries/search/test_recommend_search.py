"""
Test Suite: Recommendation Search (POST /summaries/search/recommend)
Tests for recommendation search using positive and negative examples
"""

import pytest
from httpx import AsyncClient

from __test__.integration.summaries.conftest import (
    create_test_summary,
    assert_search_response,
    cleanup_summaries
)


@pytest.mark.asyncio
class TestRecommendSearch:
    """Test cases for POST /summaries/search/recommend endpoint"""

    async def test_recommend_with_positive_examples_only(self, client: AsyncClient):
        """Test: Recommendation with positive examples only"""
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

        # Use first summary as positive example
        search_payload = {
            "positive_ids": [created_ids[0]],
            "limit": 10,
            "strategy": "average_vector"
        }
        response = await client.post("/summaries/search/recommend", json=search_payload)

        assert response.status_code == 200
        assert_search_response(response.json(), min_results=1)

        await cleanup_summaries(client, created_ids)

    async def test_recommend_with_positive_and_negative(self, client: AsyncClient):
        """Test: Recommendation with both positive and negative examples"""
        created_ids = []
        for i in range(5):
            payload = create_test_summary(
                project_id=1001,
                file_id=30 + i,
                summary_text=f"요약 {i + 1}번 문서입니다."
            )
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        search_payload = {
            "positive_ids": [created_ids[0], created_ids[1]],
            "negative_ids": [created_ids[4]],
            "limit": 10,
            "strategy": "average_vector"
        }
        response = await client.post("/summaries/search/recommend", json=search_payload)

        assert response.status_code == 200
        await cleanup_summaries(client, created_ids)

    async def test_recommend_strategy_average_vector(self, client: AsyncClient):
        """Test: Recommendation with average_vector strategy"""
        created_ids = []
        for i in range(3):
            payload = create_test_summary(project_id=1001, file_id=40 + i, summary_text="테스트 문서")
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        search_payload = {
            "positive_ids": [created_ids[0]],
            "strategy": "average_vector",
            "limit": 10
        }
        response = await client.post("/summaries/search/recommend", json=search_payload)
        assert response.status_code == 200

        await cleanup_summaries(client, created_ids)

    async def test_recommend_strategy_best_score(self, client: AsyncClient):
        """Test: Recommendation with best_score strategy"""
        created_ids = []
        for i in range(3):
            payload = create_test_summary(project_id=1001, file_id=50 + i, summary_text="테스트 문서")
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        search_payload = {
            "positive_ids": [created_ids[0]],
            "strategy": "best_score",
            "limit": 10
        }
        response = await client.post("/summaries/search/recommend", json=search_payload)
        assert response.status_code == 200

        await cleanup_summaries(client, created_ids)

    async def test_recommend_with_filters(self, client: AsyncClient):
        """Test: Recommendation with project_id filter"""
        created_ids = []
        for project_id in [1001, 2002]:
            payload = create_test_summary(project_id=project_id, file_id=60, summary_text="필터 테스트")
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        search_payload = {
            "positive_ids": [created_ids[0]],
            "filter_project_id": 1001,
            "limit": 10
        }
        response = await client.post("/summaries/search/recommend", json=search_payload)

        assert response.status_code == 200
        for result in response.json()["results"]:
            assert result["payload"]["project_id"] == 1001

        await cleanup_summaries(client, created_ids)

    async def test_recommend_missing_positive_ids(self, client: AsyncClient):
        """Test: Error case - missing positive_ids"""
        response = await client.post("/summaries/search/recommend", json={"limit": 10})
        assert response.status_code == 422
