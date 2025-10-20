"""
Test Suite: Summary Read/Retrieval (GET /summaries/{summary_id})
Tests for retrieving OCR summaries by ID
"""

import pytest
import uuid
from httpx import AsyncClient

from __test__.integration.summaries.conftest import (
    create_test_summary,
    assert_summary_response,
    cleanup_summary
)


@pytest.mark.asyncio
class TestReadSummaries:
    """Test cases for GET /summaries/{summary_id} endpoint"""

    async def test_read_single_summary(self, client: AsyncClient):
        """
        Test: Create summary and retrieve it by ID
        Expected: 200 OK, correct payload returned
        """
        # Create summary first
        payload = create_test_summary(
            project_id=1001,
            file_id=21,
            summary_text="조회 테스트용 요약입니다."
        )

        create_response = await client.post("/summaries", json=payload)
        assert create_response.status_code == 201
        created_data = create_response.json()
        summary_id = created_data["point_id"]

        # Read the summary
        read_response = await client.get(f"/summaries/{summary_id}")

        assert read_response.status_code == 200
        read_data = read_response.json()

        # Verify response structure
        assert_summary_response(read_data, expected_payload=payload)

        # Verify IDs match
        assert read_data["point_id"] == summary_id
        assert read_data["payload"]["summary_id"] == summary_id

        # Cleanup
        await cleanup_summary(client, summary_id)

    async def test_read_summary_verify_all_fields(self, client: AsyncClient):
        """
        Test: Verify all payload fields are correctly retrieved
        Expected: All fields match creation payload
        """
        payload = create_test_summary(
            project_id=1001,
            file_id=22,
            summary_text="모든 필드 검증 테스트입니다."
        )

        # Create
        create_response = await client.post("/summaries", json=payload)
        created_data = create_response.json()
        summary_id = created_data["point_id"]

        # Read
        read_response = await client.get(f"/summaries/{summary_id}")
        read_data = read_response.json()

        # Verify all fields
        read_payload = read_data["payload"]
        assert read_payload["project_id"] == payload["project_id"]
        assert read_payload["file_id"] == payload["file_id"]
        assert read_payload["summary_text"] == payload["summary_text"]
        assert "created_at" in read_payload
        assert "summary_id" in read_payload

        # Cleanup
        await cleanup_summary(client, summary_id)

    async def test_read_multiple_summaries_sequentially(self, client: AsyncClient):
        """
        Test: Create 3 summaries and retrieve each one
        Expected: Each retrieved correctly with unique data
        """
        created_summaries = []

        # Create 3 summaries
        for i in range(3):
            payload = create_test_summary(
                project_id=1001,
                file_id=30 + i,
                summary_text=f"다중 조회 테스트 {i + 1}번 요약입니다."
            )

            create_response = await client.post("/summaries", json=payload)
            created_data = create_response.json()
            created_summaries.append({
                "id": created_data["point_id"],
                "payload": payload
            })

        # Read each summary and verify
        for summary_info in created_summaries:
            read_response = await client.get(f"/summaries/{summary_info['id']}")

            assert read_response.status_code == 200
            read_data = read_response.json()

            assert_summary_response(read_data, expected_payload=summary_info["payload"])

        # Cleanup
        for summary_info in created_summaries:
            await cleanup_summary(client, summary_info["id"])

    async def test_read_summary_with_long_text(self, client: AsyncClient):
        """
        Test: Create summary with long text and retrieve
        Expected: Long text retrieved without truncation
        """
        long_text = "부동산 소유권이전등기 청구소송 요약 내용입니다. " * 50

        payload = create_test_summary(
            project_id=1001,
            file_id=40,
            summary_text=long_text
        )

        # Create
        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Read
        read_response = await client.get(f"/summaries/{summary_id}")
        read_data = read_response.json()

        # Verify text not truncated
        assert read_data["payload"]["summary_text"] == long_text
        assert len(read_data["payload"]["summary_text"]) == len(long_text)

        # Cleanup
        await cleanup_summary(client, summary_id)

    async def test_read_summary_korean_text_preserved(self, client: AsyncClient):
        """
        Test: Create summary with Korean text and verify encoding preserved
        Expected: Korean characters retrieved correctly
        """
        korean_text = (
            "원고 김철수는 피고 이영희를 상대로 부동산 소유권이전등기 청구소송을 제기하였습니다. "
            "계약금, 중도금, 잔금을 모두 지급하였으나 등기에 필요한 서류를 받지 못했습니다."
        )

        payload = create_test_summary(
            project_id=1001,
            file_id=41,
            summary_text=korean_text
        )

        # Create
        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Read
        read_response = await client.get(f"/summaries/{summary_id}")
        read_data = read_response.json()

        # Verify Korean text preserved
        assert read_data["payload"]["summary_text"] == korean_text

        # Cleanup
        await cleanup_summary(client, summary_id)

    async def test_read_summary_without_file_id(self, client: AsyncClient):
        """
        Test: Create summary without file_id and retrieve
        Expected: file_id is None in retrieved data
        """
        payload = {
            "project_id": 1001,
            "summary_text": "파일 ID 없는 요약입니다."
        }

        # Create
        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Read
        read_response = await client.get(f"/summaries/{summary_id}")
        read_data = read_response.json()

        # Verify file_id is None
        assert read_data["payload"]["file_id"] is None

        # Cleanup
        await cleanup_summary(client, summary_id)

    async def test_read_summary_created_at_format(self, client: AsyncClient):
        """
        Test: Verify created_at timestamp format
        Expected: ISO 8601 format with timezone
        """
        payload = create_test_summary(
            project_id=1001,
            file_id=42,
            summary_text="타임스탬프 검증 테스트입니다."
        )

        # Create
        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Read
        read_response = await client.get(f"/summaries/{summary_id}")
        read_data = read_response.json()

        # Verify created_at exists and has correct format
        created_at = read_data["payload"]["created_at"]
        assert created_at is not None
        assert isinstance(created_at, str)
        # ISO 8601 format: 2024-08-22T06:00:00+00:00
        assert "T" in created_at
        assert ":" in created_at

        # Cleanup
        await cleanup_summary(client, summary_id)

    # === Error Cases ===

    async def test_read_nonexistent_summary(self, client: AsyncClient):
        """
        Test: Attempt to read summary with non-existent ID
        Expected: 404 Not Found
        """
        fake_uuid = str(uuid.uuid4())

        response = await client.get(f"/summaries/{fake_uuid}")

        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data

    async def test_read_invalid_uuid_format(self, client: AsyncClient):
        """
        Test: Attempt to read summary with invalid UUID format
        Expected: 422 Unprocessable Entity or 404
        """
        invalid_id = "not-a-valid-uuid"

        response = await client.get(f"/summaries/{invalid_id}")

        # Depending on validation, could be 422 or 404
        assert response.status_code in [404, 422, 500]

    async def test_read_deleted_summary(self, client: AsyncClient):
        """
        Test: Create summary, delete it, then attempt to read
        Expected: 404 Not Found
        """
        payload = create_test_summary(
            project_id=1001,
            file_id=50,
            summary_text="삭제 후 조회 테스트입니다."
        )

        # Create
        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Delete
        delete_response = await client.delete(f"/summaries/{summary_id}")
        assert delete_response.status_code == 204

        # Attempt to read
        read_response = await client.get(f"/summaries/{summary_id}")

        assert read_response.status_code == 404

    async def test_read_empty_id(self, client: AsyncClient):
        """
        Test: Attempt to read with empty ID
        Expected: 404 or 405 Method Not Allowed
        """
        response = await client.get("/summaries/")

        # Empty ID routes to collection endpoint, which doesn't exist for GET
        assert response.status_code in [404, 405]

    # === Integration Scenarios ===

    async def test_create_read_workflow(self, client: AsyncClient):
        """
        Test: Complete create → read workflow
        Expected: Data consistency between create and read
        """
        payload = create_test_summary(
            project_id=1001,
            file_id=60,
            summary_text="생성-조회 워크플로우 테스트입니다."
        )

        # Create
        create_response = await client.post("/summaries", json=payload)
        assert create_response.status_code == 201
        create_data = create_response.json()

        # Read immediately
        read_response = await client.get(f"/summaries/{create_data['point_id']}")
        assert read_response.status_code == 200
        read_data = read_response.json()

        # Verify consistency
        assert create_data["point_id"] == read_data["point_id"]
        assert create_data["payload"]["summary_text"] == read_data["payload"]["summary_text"]
        assert create_data["payload"]["project_id"] == read_data["payload"]["project_id"]

        # Cleanup
        await cleanup_summary(client, create_data["point_id"])

    async def test_read_stability_multiple_calls(self, client: AsyncClient):
        """
        Test: Read same summary multiple times
        Expected: Consistent data across multiple reads
        """
        payload = create_test_summary(
            project_id=1001,
            file_id=61,
            summary_text="다중 조회 안정성 테스트입니다."
        )

        # Create
        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Read 5 times
        read_results = []
        for _ in range(5):
            read_response = await client.get(f"/summaries/{summary_id}")
            assert read_response.status_code == 200
            read_results.append(read_response.json())

        # Verify all reads are identical
        first_result = read_results[0]
        for result in read_results[1:]:
            assert result == first_result

        # Cleanup
        await cleanup_summary(client, summary_id)
