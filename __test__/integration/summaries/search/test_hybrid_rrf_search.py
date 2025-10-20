"""
Test Suite: Hybrid RRF Search (POST /summaries/search/dense_sparse_rrf)
Tests for hybrid search combining dense + sparse using Reciprocal Rank Fusion
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
class TestHybridRRFSearch:
    """Test cases for POST /summaries/search/dense_sparse_rrf endpoint"""

    async def test_basic_hybrid_rrf_search(self, client: AsyncClient):
        """Test: Basic hybrid search combining semantic and keyword search"""
        created_ids = []
        texts = [
            "원고는 부동산 매매계약을 체결하고 대금을 지급하였습니다.",
            "피고는 소유권이전등기에 필요한 서류를 교부하지 않았습니다.",
            "계약금, 중도금, 잔금을 모두 납부한 상태입니다."
        ]

        for i, text in enumerate(texts):
            payload = create_test_summary(project_id=1001, file_id=21 + i, summary_text=text)
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        search_payload = {
            "query_text": "부동산 매매계약",
            "limit": 10,
            "rrf_k": 60
        }
        response = await client.post("/summaries/search/dense_sparse_rrf", json=search_payload)

        assert response.status_code == 200
        data = response.json()
        assert_search_response(data, min_results=1)
        assert_scores_descending(data["results"])

        await cleanup_summaries(client, created_ids)

    async def test_rrf_k_parameter_variation(self, client: AsyncClient):
        """Test: Different RRF k values (30, 60, 100)"""
        created_ids = []
        for i in range(5):
            payload = create_test_summary(
                project_id=1001,
                file_id=30 + i,
                summary_text=f"부동산 계약 관련 요약 {i + 1}번입니다."
            )
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        for k_value in [30, 60, 100]:
            search_payload = {
                "query_text": "부동산 계약",
                "limit": 5,
                "rrf_k": k_value
            }
            response = await client.post("/summaries/search/dense_sparse_rrf", json=search_payload)
            assert response.status_code == 200

        await cleanup_summaries(client, created_ids)

    async def test_hybrid_rrf_with_filters(self, client: AsyncClient):
        """Test: Hybrid RRF search with project_id and file_id filters"""
        created_ids = []
        for project_id in [1001, 2002]:
            payload = create_test_summary(
                project_id=project_id,
                file_id=40,
                summary_text="하이브리드 검색 필터 테스트"
            )
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        search_payload = {
            "query_text": "하이브리드",
            "filter_project_id": 1001,
            "limit": 10,
            "rrf_k": 60
        }
        response = await client.post("/summaries/search/dense_sparse_rrf", json=search_payload)

        assert response.status_code == 200
        for result in response.json()["results"]:
            assert result["payload"]["project_id"] == 1001

        await cleanup_summaries(client, created_ids)

    async def test_hybrid_rrf_score_threshold(self, client: AsyncClient):
        """Test: RRF search with score threshold"""
        created_ids = []
        payload = create_test_summary(
            project_id=1001,
            file_id=50,
            summary_text="RRF 점수 임계값 테스트를 위한 요약입니다."
        )
        response = await client.post("/summaries", json=payload)
        created_ids.append(response.json()["point_id"])

        search_payload = {
            "query_text": "RRF",
            "score_threshold": 0.1,
            "limit": 10,
            "rrf_k": 60
        }
        response = await client.post("/summaries/search/dense_sparse_rrf", json=search_payload)

        assert response.status_code == 200
        await cleanup_summaries(client, created_ids)

    async def test_hybrid_rrf_missing_query_text(self, client: AsyncClient):
        """Test: Error case - missing query_text"""
        response = await client.post("/summaries/search/dense_sparse_rrf", json={"limit": 10})
        assert response.status_code == 422

    async def test_hybrid_rrf_invalid_k_value(self, client: AsyncClient):
        """Test: Error case - invalid RRF k value"""
        search_payload = {
            "query_text": "테스트",
            "rrf_k": 1000  # Max is 100
        }
        response = await client.post("/summaries/search/dense_sparse_rrf", json=search_payload)
        assert response.status_code == 422
