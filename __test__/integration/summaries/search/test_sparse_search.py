"""
Test Suite: Sparse Vector Search (POST /summaries/search/sparse)
Tests for keyword-based search using Kiwi (Korean) or FastEmbed BM25
"""

import pytest
from httpx import AsyncClient

from __test__.integration.summaries.conftest import (
    create_test_summary,
    assert_search_response,
    assert_scores_descending,
    cleanup_summaries
)


@pytest.mark.asyncio
class TestSparseSearch:
    """Test cases for POST /summaries/search/sparse endpoint"""

    async def test_basic_sparse_search(self, client: AsyncClient):
        """Test: Basic keyword search with Korean morphological analysis"""
        created_ids = []
        texts = [
            "원고는 부동산 매매계약을 체결하였습니다.",
            "피고는 계약금을 수령하였습니다.",
            "소유권이전등기 청구소송입니다."
        ]

        for i, text in enumerate(texts):
            payload = create_test_summary(project_id=1001, file_id=21 + i, summary_text=text)
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        search_payload = {"query_text": "매매계약", "limit": 10}
        response = await client.post("/summaries/search/sparse", json=search_payload)

        assert response.status_code == 200
        assert_search_response(response.json(), min_results=1)

        await cleanup_summaries(client, created_ids)

    async def test_sparse_search_korean_morphology(self, client: AsyncClient):
        """Test: Korean morphological analysis (Kiwi)"""
        created_ids = []
        payload = create_test_summary(
            project_id=1001,
            file_id=30,
            summary_text="원고는 부동산소유권이전등기를 청구하였습니다."
        )
        response = await client.post("/summaries", json=payload)
        created_ids.append(response.json()["point_id"])

        search_payload = {"query_text": "소유권", "limit": 10}
        response = await client.post("/summaries/search/sparse", json=search_payload)

        assert response.status_code == 200
        await cleanup_summaries(client, created_ids)

    async def test_sparse_search_with_filters(self, client: AsyncClient):
        """Test: Sparse search with project_id and file_id filters"""
        created_ids = []
        for project_id in [1001, 2002]:
            payload = create_test_summary(
                project_id=project_id,
                file_id=40,
                summary_text="필터링 테스트 요약"
            )
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        search_payload = {
            "query_text": "필터링",
            "filter_project_id": 1001,
            "limit": 10
        }
        response = await client.post("/summaries/search/sparse", json=search_payload)

        assert response.status_code == 200
        for result in response.json()["results"]:
            assert result["payload"]["project_id"] == 1001

        await cleanup_summaries(client, created_ids)

    async def test_sparse_search_score_threshold(self, client: AsyncClient):
        """Test: Score threshold filtering for sparse search"""
        created_ids = []
        payload = create_test_summary(
            project_id=1001,
            file_id=50,
            summary_text="점수 임계값 테스트를 위한 요약입니다."
        )
        response = await client.post("/summaries", json=payload)
        created_ids.append(response.json()["point_id"])

        search_payload = {
            "query_text": "임계값",
            "score_threshold": 0.1,
            "limit": 10
        }
        response = await client.post("/summaries/search/sparse", json=search_payload)

        assert response.status_code == 200
        for result in response.json()["results"]:
            if result.get("score"):
                assert result["score"] >= 0.1

        await cleanup_summaries(client, created_ids)

    async def test_sparse_search_missing_query_text(self, client: AsyncClient):
        """Test: Error case - missing query_text"""
        response = await client.post("/summaries/search/sparse", json={"limit": 10})
        assert response.status_code == 422
