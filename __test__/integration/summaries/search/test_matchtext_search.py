"""
Test Suite: MatchText Search (POST /summaries/search/matchtext)
Tests for full-text search using MatchText (no morphological analysis)
"""

import pytest
from httpx import AsyncClient

from __test__.integration.summaries.conftest import (
    create_test_summary,
    assert_search_response,
    cleanup_summaries
)


@pytest.mark.asyncio
class TestMatchTextSearch:
    """Test cases for POST /summaries/search/matchtext endpoint"""

    async def test_basic_matchtext_search(self, client: AsyncClient):
        """Test: Basic full-text matching without morphological analysis"""
        created_ids = []
        texts = [
            "원고는 부동산 매매계약을 체결하였습니다.",
            "피고는 소유권이전등기 서류를 교부하지 않았습니다.",
            "계약금, 중도금, 잔금을 모두 지급하였습니다."
        ]

        for i, text in enumerate(texts):
            payload = create_test_summary(project_id=1001, file_id=21 + i, summary_text=text)
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        search_payload = {"query_text": "매매계약", "limit": 10}
        response = await client.post("/summaries/search/matchtext", json=search_payload)

        assert response.status_code == 200
        assert_search_response(response.json(), min_results=1)

        await cleanup_summaries(client, created_ids)

    async def test_matchtext_phrase_matching(self, client: AsyncClient):
        """Test: Match exact phrase in summary_text"""
        created_ids = []
        payload = create_test_summary(
            project_id=1001,
            file_id=30,
            summary_text="소유권이전등기 청구소송에 관한 사건입니다."
        )
        response = await client.post("/summaries", json=payload)
        created_ids.append(response.json()["point_id"])

        search_payload = {"query_text": "소유권이전등기", "limit": 10}
        response = await client.post("/summaries/search/matchtext", json=search_payload)

        assert response.status_code == 200
        assert_search_response(response.json(), min_results=1)

        await cleanup_summaries(client, created_ids)

    async def test_matchtext_with_filters(self, client: AsyncClient):
        """Test: MatchText with project_id and file_id filters"""
        created_ids = []
        for project_id in [1001, 2002]:
            payload = create_test_summary(
                project_id=project_id,
                file_id=40,
                summary_text="필터 테스트 문서입니다."
            )
            response = await client.post("/summaries", json=payload)
            created_ids.append(response.json()["point_id"])

        search_payload = {
            "query_text": "문서",
            "filter_project_id": 1001,
            "limit": 10
        }
        response = await client.post("/summaries/search/matchtext", json=search_payload)

        assert response.status_code == 200
        for result in response.json()["results"]:
            assert result["payload"]["project_id"] == 1001

        await cleanup_summaries(client, created_ids)

    async def test_matchtext_no_results(self, client: AsyncClient):
        """Test: MatchText with no matching results"""
        search_payload = {"query_text": "존재하지않는검색어99999", "limit": 10}
        response = await client.post("/summaries/search/matchtext", json=search_payload)

        assert response.status_code == 200
        data = response.json()
        assert_search_response(data, min_results=0, max_results=0)

    async def test_matchtext_missing_query_text(self, client: AsyncClient):
        """Test: Error case - missing query_text"""
        response = await client.post("/summaries/search/matchtext", json={"limit": 10})
        assert response.status_code == 422
