"""
Test Suite: Summary Creation (POST /summaries)
Tests for creating OCR summaries with automatic embedding generation
"""

import pytest
import uuid
from httpx import AsyncClient

from __test__.integration.summaries.conftest import (
    create_test_summary,
    load_sample_summaries,
    assert_summary_response,
    cleanup_summary
)


@pytest.mark.asyncio
class TestCreateSummaries:
    """Test cases for POST /summaries endpoint"""

    async def test_create_single_summary_basic(self, client: AsyncClient):
        """
        Test: Create single summary with minimal required fields
        Expected: 201 Created, valid response structure, embeddings generated
        """
        payload = create_test_summary(
            project_id=1001,
            file_id=21,
            summary_text="원고 김철수가 피고 이영희를 상대로 제기한 부동산 소유권이전등기 청구소송입니다."
        )

        response = await client.post("/summaries", json=payload)

        assert response.status_code == 201
        data = response.json()

        # Validate response structure
        assert_summary_response(data, expected_payload=payload)

        # Validate summary_id is valid UUID
        assert uuid.UUID(data["point_id"])
        assert uuid.UUID(data["payload"]["summary_id"])

        # Cleanup
        await cleanup_summary(client, data["point_id"])

    async def test_create_summary_with_uuid(self, client: AsyncClient):
        """
        Test: Create summary with manually specified UUID
        Expected: Uses provided UUID instead of auto-generating
        """
        custom_uuid = str(uuid.uuid4())
        payload = create_test_summary(
            summary_id=custom_uuid,
            project_id=1001,
            file_id=22,
            summary_text="테스트 요약 내용입니다."
        )

        response = await client.post("/summaries", json=payload)

        assert response.status_code == 201
        data = response.json()

        # Verify custom UUID was used
        assert data["point_id"] == custom_uuid
        assert data["payload"]["summary_id"] == custom_uuid

        # Cleanup
        await cleanup_summary(client, custom_uuid)

    async def test_create_summary_without_uuid(self, client: AsyncClient):
        """
        Test: Create summary without summary_id (auto-generation)
        Expected: UUID automatically generated
        """
        payload = {
            "project_id": 1001,
            "file_id": 23,
            "summary_text": "UUID가 자동으로 생성되어야 합니다."
        }

        response = await client.post("/summaries", json=payload)

        assert response.status_code == 201
        data = response.json()

        # Verify UUID was auto-generated
        generated_uuid = data["point_id"]
        assert uuid.UUID(generated_uuid)

        # Cleanup
        await cleanup_summary(client, generated_uuid)

    async def test_create_summary_with_optional_file_id(self, client: AsyncClient):
        """
        Test: Create summary with optional file_id
        Expected: file_id properly stored
        """
        payload = create_test_summary(
            project_id=1001,
            file_id=100,
            summary_text="파일 ID가 포함된 요약입니다."
        )

        response = await client.post("/summaries", json=payload)

        assert response.status_code == 201
        data = response.json()

        assert data["payload"]["file_id"] == 100

        # Cleanup
        await cleanup_summary(client, data["point_id"])

    async def test_create_summary_without_file_id(self, client: AsyncClient):
        """
        Test: Create summary without file_id (optional field)
        Expected: Summary created with file_id as None
        """
        payload = {
            "project_id": 1001,
            "summary_text": "파일 ID가 없는 요약입니다."
        }

        response = await client.post("/summaries", json=payload)

        assert response.status_code == 201
        data = response.json()

        assert data["payload"]["file_id"] is None

        # Cleanup
        await cleanup_summary(client, data["point_id"])

    async def test_create_batch_summaries_sequential(self, client: AsyncClient):
        """
        Test: Create 10 summaries sequentially
        Expected: All 10 created successfully with unique IDs
        """
        created_ids = []

        for i in range(10):
            payload = create_test_summary(
                project_id=1001,
                file_id=30 + i,
                summary_text=f"배치 생성 테스트 요약 {i + 1}번입니다."
            )

            response = await client.post("/summaries", json=payload)
            assert response.status_code == 201

            data = response.json()
            created_ids.append(data["point_id"])

        # Verify all IDs are unique
        assert len(created_ids) == len(set(created_ids))

        # Cleanup
        for summary_id in created_ids:
            await cleanup_summary(client, summary_id)

    async def test_create_from_sample_data(self, client: AsyncClient):
        """
        Test: Create summaries from actual sample data files
        Expected: Real legal document summaries created successfully
        """
        samples = load_sample_summaries(limit=5)
        created_ids = []

        for sample in samples:
            # Remove summary_id to let server generate new ones
            payload = {
                "project_id": sample["project_id"],
                "file_id": sample["file_id"],
                "summary_text": sample["summary_text"]
            }

            response = await client.post("/summaries", json=payload)
            assert response.status_code == 201

            data = response.json()
            created_ids.append(data["point_id"])

            # Verify summary_text matches
            assert data["payload"]["summary_text"] == sample["summary_text"]

        # Cleanup
        for summary_id in created_ids:
            await cleanup_summary(client, summary_id)

    async def test_create_long_summary_text(self, client: AsyncClient):
        """
        Test: Create summary with very long text (>1000 characters)
        Expected: Long text handled correctly, embeddings generated
        """
        long_text = "부동산 소유권이전등기 청구소송. " * 100  # ~3000 characters

        payload = create_test_summary(
            project_id=1001,
            file_id=40,
            summary_text=long_text
        )

        response = await client.post("/summaries", json=payload)

        assert response.status_code == 201
        data = response.json()

        # Verify long text stored correctly
        assert data["payload"]["summary_text"] == long_text

        # Cleanup
        await cleanup_summary(client, data["point_id"])

    async def test_create_korean_text_summary(self, client: AsyncClient):
        """
        Test: Create summary with Korean legal terminology
        Expected: Korean text handled correctly, Kiwi sparse embeddings work
        """
        korean_legal_text = (
            "원고는 2024년 3월 15일 피고와 부동산 매매계약을 체결하였으며, "
            "계약금, 중도금, 잔금을 모두 지급하였으나 피고는 소유권이전등기에 "
            "필요한 서류를 교부하지 않아 본 소송을 제기합니다."
        )

        payload = create_test_summary(
            project_id=1001,
            file_id=41,
            summary_text=korean_legal_text
        )

        response = await client.post("/summaries", json=payload)

        assert response.status_code == 201
        data = response.json()

        assert data["payload"]["summary_text"] == korean_legal_text

        # Cleanup
        await cleanup_summary(client, data["point_id"])

    # === Error Cases ===

    async def test_create_missing_required_field_project_id(self, client: AsyncClient):
        """
        Test: Create summary without required project_id
        Expected: 422 Unprocessable Entity
        """
        payload = {
            "file_id": 50,
            "summary_text": "project_id가 누락되었습니다."
        }

        response = await client.post("/summaries", json=payload)

        assert response.status_code == 422

    async def test_create_missing_required_field_summary_text(self, client: AsyncClient):
        """
        Test: Create summary without required summary_text
        Expected: 422 Unprocessable Entity
        """
        payload = {
            "project_id": 1001,
            "file_id": 51
        }

        response = await client.post("/summaries", json=payload)

        assert response.status_code == 422

    async def test_create_invalid_data_type_project_id(self, client: AsyncClient):
        """
        Test: Create summary with invalid data type for project_id
        Expected: 422 Unprocessable Entity
        """
        payload = {
            "project_id": "invalid_string",
            "summary_text": "잘못된 데이터 타입 테스트"
        }

        response = await client.post("/summaries", json=payload)

        assert response.status_code == 422

    async def test_create_empty_summary_text(self, client: AsyncClient):
        """
        Test: Create summary with empty summary_text
        Expected: 201 Created (empty string is valid, but embeddings may be trivial)
        """
        payload = create_test_summary(
            project_id=1001,
            file_id=52,
            summary_text=""
        )

        response = await client.post("/summaries", json=payload)

        # Empty string is technically valid
        assert response.status_code == 201

        data = response.json()
        assert data["payload"]["summary_text"] == ""

        # Cleanup
        await cleanup_summary(client, data["point_id"])

    async def test_create_invalid_uuid_format(self, client: AsyncClient):
        """
        Test: Create summary with invalid UUID format
        Expected: Server generates new UUID (invalid UUID ignored)
        """
        payload = {
            "summary_id": "not-a-valid-uuid",
            "project_id": 1001,
            "summary_text": "잘못된 UUID 포맷 테스트"
        }

        response = await client.post("/summaries", json=payload)

        assert response.status_code == 201
        data = response.json()

        # Server should generate valid UUID
        generated_uuid = data["point_id"]
        assert uuid.UUID(generated_uuid)
        assert generated_uuid != "not-a-valid-uuid"

        # Cleanup
        await cleanup_summary(client, generated_uuid)
