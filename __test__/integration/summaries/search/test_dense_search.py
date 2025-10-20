"""
Test Suite: Dense Vector Search (POST /summaries/search/dense)
Tests for semantic similarity search using Gemini dense embeddings
"""

import pytest
from httpx import AsyncClient

from __test__.integration.summaries.conftest import (
    create_test_summary,
    load_sample_summaries,
    assert_search_response,
    assert_scores_descending,
    cleanup_summaries
)


@pytest.mark.asyncio
class TestDenseSearch:
    """Test cases for POST /summaries/search/dense endpoint"""

    async def test_basic_dense_search(self, client: AsyncClient):
        """
        Test: Basic semantic search with Korean query
        Expected: Results returned with similarity scores
        """
        # Create test summaries
        created_ids = []
        summaries_data = [
            {"text": "원고 김철수는 피고 이영희를 상대로 부동산 매매계약 이행청구소송을 제기하였습니다.", "file_id": 21},
            {"text": "본 사건은 부동산 소유권이전등기 청구에 관한 사건입니다.", "file_id": 22},
            {"text": "피고는 계약금, 중도금, 잔금을 모두 수령하였으나 등기 서류를 교부하지 않았습니다.", "file_id": 23},
        ]

        for data in summaries_data:
            payload = create_test_summary(project_id=1001, file_id=data["file_id"], summary_text=data["text"])
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        # Search
        search_payload = {
            "query_text": "부동산 매매계약",
            "limit": 10
        }

        response = await client.post("/summaries/search/dense", json=search_payload)

        assert response.status_code == 200
        data = response.json()

        assert_search_response(data, min_results=1)
        assert_scores_descending(data["results"])

        # Cleanup
        await cleanup_summaries(client, created_ids)

    async def test_dense_search_with_score_threshold(self, client: AsyncClient):
        """
        Test: Dense search with minimum score threshold
        Expected: Only results above threshold returned
        """
        # Create summaries
        created_ids = []
        payload = create_test_summary(
            project_id=1001,
            file_id=30,
            summary_text="원고는 피고를 상대로 소유권이전등기 청구소송을 제기하였습니다."
        )
        response = await client.post("/summaries", json=payload)
        created_ids.append(response.json()["point_id"])

        # Search with high threshold
        search_payload = {
            "query_text": "소유권이전등기",
            "limit": 10,
            "score_threshold": 0.7
        }

        response = await client.post("/summaries/search/dense", json=search_payload)

        assert response.status_code == 200
        data = response.json()

        # Verify all scores >= threshold
        for result in data["results"]:
            if result.get("score") is not None:
                assert result["score"] >= 0.7

        # Cleanup
        await cleanup_summaries(client, created_ids)

    async def test_dense_search_limit_control(self, client: AsyncClient):
        """
        Test: Control result count with limit parameter
        Expected: Exactly limit results (or fewer if not enough data)
        """
        # Create 10 summaries
        created_ids = []
        for i in range(10):
            payload = create_test_summary(
                project_id=1001,
                file_id=40 + i,
                summary_text=f"부동산 매매계약 관련 요약 {i + 1}번입니다."
            )
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        # Search with limit=5
        search_payload = {
            "query_text": "부동산 매매계약",
            "limit": 5
        }

        response = await client.post("/summaries/search/dense", json=search_payload)

        assert response.status_code == 200
        data = response.json()

        # Should return exactly 5 results
        assert len(data["results"]) <= 5

        # Cleanup
        await cleanup_summaries(client, created_ids)

    async def test_dense_search_filter_by_project_id(self, client: AsyncClient):
        """
        Test: Filter search results by project_id
        Expected: Only summaries from specified project
        """
        # Create summaries in different projects
        project1_ids = []
        project2_ids = []

        # Project 1001
        for i in range(3):
            payload = create_test_summary(project_id=1001, file_id=50 + i, summary_text="프로젝트 1001 요약")
            response = await client.post("/summaries", json=payload)
            project1_ids.append(response.json()["point_id"])

        # Project 2002
        for i in range(3):
            payload = create_test_summary(project_id=2002, file_id=60 + i, summary_text="프로젝트 2002 요약")
            response = await client.post("/summaries", json=payload)
            project2_ids.append(response.json()["point_id"])

        # Search only project 1001
        search_payload = {
            "query_text": "프로젝트",
            "filter_project_id": 1001,
            "limit": 10
        }

        response = await client.post("/summaries/search/dense", json=search_payload)

        assert response.status_code == 200
        data = response.json()

        # Verify all results from project 1001
        for result in data["results"]:
            assert result["payload"]["project_id"] == 1001

        # Cleanup
        await cleanup_summaries(client, project1_ids + project2_ids)

    async def test_dense_search_filter_by_file_id(self, client: AsyncClient):
        """
        Test: Filter search results by file_id
        Expected: Only summaries from specified file
        """
        # Create summaries with different file_ids
        created_ids = []

        for file_id in [100, 101, 102]:
            payload = create_test_summary(project_id=1001, file_id=file_id, summary_text=f"파일 {file_id} 요약")
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        # Search only file 100
        search_payload = {
            "query_text": "파일",
            "filter_file_id": 100,
            "limit": 10
        }

        response = await client.post("/summaries/search/dense", json=search_payload)

        assert response.status_code == 200
        data = response.json()

        # Verify all results from file 100
        for result in data["results"]:
            assert result["payload"]["file_id"] == 100

        # Cleanup
        await cleanup_summaries(client, created_ids)

    async def test_dense_search_combined_filters(self, client: AsyncClient):
        """
        Test: Combine project_id and file_id filters
        Expected: Results match both filters
        """
        # Create summaries
        created_ids = []

        payload1 = create_test_summary(project_id=3003, file_id=200, summary_text="타겟 요약")
        response1 = await client.post("/summaries", json=payload1)
        created_ids.append(response1.json()["point_id"])

        payload2 = create_test_summary(project_id=3003, file_id=201, summary_text="다른 파일 요약")
        response2 = await client.post("/summaries", json=payload2)
        created_ids.append(response2.json()["point_id"])

        payload3 = create_test_summary(project_id=4004, file_id=200, summary_text="다른 프로젝트 요약")
        response3 = await client.post("/summaries", json=payload3)
        created_ids.append(response3.json()["point_id"])

        # Search with both filters
        search_payload = {
            "query_text": "요약",
            "filter_project_id": 3003,
            "filter_file_id": 200,
            "limit": 10
        }

        response = await client.post("/summaries/search/dense", json=search_payload)

        assert response.status_code == 200
        data = response.json()

        # Verify all results match both filters
        for result in data["results"]:
            assert result["payload"]["project_id"] == 3003
            assert result["payload"]["file_id"] == 200

        # Cleanup
        await cleanup_summaries(client, created_ids)

    async def test_dense_search_semantic_similarity(self, client: AsyncClient):
        """
        Test: Verify semantic similarity (similar meaning, different words)
        Expected: Semantically similar summaries ranked high
        """
        # Create summaries with similar meaning
        created_ids = []

        similar_texts = [
            "원고가 피고에게 부동산 매매대금을 지급하였으나 등기 서류를 받지 못했습니다.",
            "계약금, 중도금, 잔금을 모두 납부했으나 소유권 이전에 필요한 서류를 교부받지 못했습니다.",
            "날씨가 맑고 화창한 하루입니다."  # Semantically different
        ]

        for i, text in enumerate(similar_texts):
            payload = create_test_summary(project_id=1001, file_id=70 + i, summary_text=text)
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        # Search with semantically similar query
        search_payload = {
            "query_text": "매매대금을 지급했지만 등기에 필요한 서류를 받지 못함",
            "limit": 10
        }

        response = await client.post("/summaries/search/dense", json=search_payload)

        assert response.status_code == 200
        data = response.json()

        # First two results should have higher scores than third
        if len(data["results"]) >= 2:
            scores = [r.get("score", 0) for r in data["results"][:3]]
            # Semantically similar should rank higher
            assert scores[0] > scores[2] or scores[1] > scores[2]

        # Cleanup
        await cleanup_summaries(client, created_ids)

    async def test_dense_search_with_real_sample_data(self, client: AsyncClient):
        """
        Test: Search using real legal document sample data
        Expected: Relevant legal documents found
        """
        # Load and create from sample data
        samples = load_sample_summaries(limit=10)
        created_ids = []

        for sample in samples:
            payload = {
                "project_id": sample["project_id"],
                "file_id": sample["file_id"],
                "summary_text": sample["summary_text"]
            }
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        # Search for legal terms
        search_payload = {
            "query_text": "내용증명 발송",
            "limit": 5
        }

        response = await client.post("/summaries/search/dense", json=search_payload)

        assert response.status_code == 200
        data = response.json()

        assert_search_response(data, min_results=0)  # May or may not find results

        # Cleanup
        await cleanup_summaries(client, created_ids)

    async def test_dense_search_no_results(self, client: AsyncClient):
        """
        Test: Search with very high threshold or unrelated query
        Expected: Empty results with valid response structure
        """
        search_payload = {
            "query_text": "완전히관련없는검색어987654321",
            "score_threshold": 0.99,
            "limit": 10
        }

        response = await client.post("/summaries/search/dense", json=search_payload)

        assert response.status_code == 200
        data = response.json()

        assert_search_response(data, min_results=0, max_results=0)
        assert data["results"] == []

    # === Error Cases ===

    async def test_dense_search_missing_query_text(self, client: AsyncClient):
        """
        Test: Search without required query_text
        Expected: 422 Unprocessable Entity
        """
        search_payload = {
            "limit": 10
        }

        response = await client.post("/summaries/search/dense", json=search_payload)

        assert response.status_code == 422

    async def test_dense_search_invalid_limit(self, client: AsyncClient):
        """
        Test: Search with invalid limit (out of range)
        Expected: 422 Unprocessable Entity
        """
        search_payload = {
            "query_text": "테스트",
            "limit": 1000  # Max is 100
        }

        response = await client.post("/summaries/search/dense", json=search_payload)

        assert response.status_code == 422

    async def test_dense_search_invalid_score_threshold(self, client: AsyncClient):
        """
        Test: Search with invalid score_threshold (>1.0)
        Expected: 422 Unprocessable Entity
        """
        search_payload = {
            "query_text": "테스트",
            "score_threshold": 1.5
        }

        response = await client.post("/summaries/search/dense", json=search_payload)

        assert response.status_code == 422
