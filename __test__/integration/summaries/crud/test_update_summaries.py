"""
Test Suite: Summary Update (PUT /summaries/{summary_id})
Tests for updating OCR summaries with conditional embedding regeneration
"""

import pytest
from httpx import AsyncClient

from __test__.integration.summaries.conftest import (
    create_test_summary,
    assert_summary_response,
    cleanup_summary
)


@pytest.mark.asyncio
class TestUpdateSummaries:
    """Test cases for PUT /summaries/{summary_id} endpoint"""

    async def test_update_metadata_only(self, client: AsyncClient):
        """
        Test: Update project_id and file_id without changing summary_text
        Expected: Metadata updated, embeddings NOT regenerated
        """
        # Create summary
        payload = create_test_summary(
            project_id=1001,
            file_id=21,
            summary_text="메타데이터 업데이트 테스트입니다."
        )

        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Update metadata only
        update_payload = {
            "project_id": 2002,
            "file_id": 99
        }

        update_response = await client.put(f"/summaries/{summary_id}", json=update_payload)

        assert update_response.status_code == 200
        updated_data = update_response.json()

        # Verify metadata updated
        assert updated_data["payload"]["project_id"] == 2002
        assert updated_data["payload"]["file_id"] == 99

        # Verify summary_text unchanged
        assert updated_data["payload"]["summary_text"] == payload["summary_text"]

        # Cleanup
        await cleanup_summary(client, summary_id)

    async def test_update_summary_text_regenerates_embeddings(self, client: AsyncClient):
        """
        Test: Update summary_text
        Expected: Text updated, embeddings automatically regenerated
        """
        # Create summary
        original_text = "원본 요약 텍스트입니다."
        payload = create_test_summary(
            project_id=1001,
            file_id=22,
            summary_text=original_text
        )

        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Update summary_text
        new_text = "수정된 요약 텍스트입니다. 완전히 다른 내용으로 변경되었습니다."
        update_payload = {
            "summary_text": new_text
        }

        update_response = await client.put(f"/summaries/{summary_id}", json=update_payload)

        assert update_response.status_code == 200
        updated_data = update_response.json()

        # Verify text updated
        assert updated_data["payload"]["summary_text"] == new_text
        assert updated_data["payload"]["summary_text"] != original_text

        # Cleanup
        await cleanup_summary(client, summary_id)

    async def test_update_summary_text_and_metadata(self, client: AsyncClient):
        """
        Test: Update both summary_text and metadata together
        Expected: All fields updated, embeddings regenerated
        """
        # Create summary
        payload = create_test_summary(
            project_id=1001,
            file_id=23,
            summary_text="복합 업데이트 전 텍스트입니다."
        )

        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Update everything
        update_payload = {
            "project_id": 3003,
            "file_id": 88,
            "summary_text": "복합 업데이트 후 텍스트입니다."
        }

        update_response = await client.put(f"/summaries/{summary_id}", json=update_payload)

        assert update_response.status_code == 200
        updated_data = update_response.json()

        # Verify all updates
        assert updated_data["payload"]["project_id"] == 3003
        assert updated_data["payload"]["file_id"] == 88
        assert updated_data["payload"]["summary_text"] == "복합 업데이트 후 텍스트입니다."

        # Cleanup
        await cleanup_summary(client, summary_id)

    async def test_update_partial_field_only(self, client: AsyncClient):
        """
        Test: Update only file_id, leave other fields unchanged
        Expected: Only file_id updated, other fields preserved
        """
        # Create summary
        payload = create_test_summary(
            project_id=1001,
            file_id=24,
            summary_text="부분 업데이트 테스트입니다."
        )

        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]
        original_data = create_response.json()

        # Update only file_id
        update_payload = {
            "file_id": 100
        }

        update_response = await client.put(f"/summaries/{summary_id}", json=update_payload)

        assert update_response.status_code == 200
        updated_data = update_response.json()

        # Verify only file_id changed
        assert updated_data["payload"]["file_id"] == 100
        assert updated_data["payload"]["project_id"] == original_data["payload"]["project_id"]
        assert updated_data["payload"]["summary_text"] == original_data["payload"]["summary_text"]

        # Cleanup
        await cleanup_summary(client, summary_id)

    async def test_update_project_id_only(self, client: AsyncClient):
        """
        Test: Update only project_id
        Expected: Only project_id updated
        """
        # Create summary
        payload = create_test_summary(
            project_id=1001,
            file_id=25,
            summary_text="프로젝트 ID 업데이트 테스트입니다."
        )

        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Update only project_id
        update_payload = {
            "project_id": 4004
        }

        update_response = await client.put(f"/summaries/{summary_id}", json=update_payload)

        assert update_response.status_code == 200
        updated_data = update_response.json()

        # Verify only project_id changed
        assert updated_data["payload"]["project_id"] == 4004
        assert updated_data["payload"]["file_id"] == payload["file_id"]
        assert updated_data["payload"]["summary_text"] == payload["summary_text"]

        # Cleanup
        await cleanup_summary(client, summary_id)

    async def test_update_long_summary_text(self, client: AsyncClient):
        """
        Test: Update to very long summary_text
        Expected: Long text handled correctly, embeddings generated
        """
        # Create summary
        payload = create_test_summary(
            project_id=1001,
            file_id=30,
            summary_text="짧은 원본 텍스트"
        )

        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Update to long text
        long_text = "부동산 소유권이전등기 청구소송 상세 요약입니다. " * 100

        update_payload = {
            "summary_text": long_text
        }

        update_response = await client.put(f"/summaries/{summary_id}", json=update_payload)

        assert update_response.status_code == 200
        updated_data = update_response.json()

        # Verify long text stored
        assert updated_data["payload"]["summary_text"] == long_text
        assert len(updated_data["payload"]["summary_text"]) == len(long_text)

        # Cleanup
        await cleanup_summary(client, summary_id)

    async def test_update_korean_legal_terminology(self, client: AsyncClient):
        """
        Test: Update summary_text with Korean legal terms
        Expected: Korean text updated correctly, Kiwi embeddings regenerated
        """
        # Create summary
        payload = create_test_summary(
            project_id=1001,
            file_id=31,
            summary_text="원본 한글 텍스트"
        )

        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Update with legal Korean text
        legal_text = (
            "원고는 피고를 상대로 부동산 매매계약 이행청구소송을 제기하였으며, "
            "계약금, 중도금, 잔금을 모두 지급하였으나 피고가 소유권이전등기에 "
            "필요한 등기필증과 인감증명서를 교부하지 않아 소송을 진행합니다."
        )

        update_payload = {
            "summary_text": legal_text
        }

        update_response = await client.put(f"/summaries/{summary_id}", json=update_payload)

        assert update_response.status_code == 200
        updated_data = update_response.json()

        assert updated_data["payload"]["summary_text"] == legal_text

        # Cleanup
        await cleanup_summary(client, summary_id)

    async def test_update_to_empty_summary_text(self, client: AsyncClient):
        """
        Test: Update summary_text to empty string
        Expected: Empty string accepted (embeddings may be trivial)
        """
        # Create summary
        payload = create_test_summary(
            project_id=1001,
            file_id=32,
            summary_text="비어있지 않은 텍스트"
        )

        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Update to empty
        update_payload = {
            "summary_text": ""
        }

        update_response = await client.put(f"/summaries/{summary_id}", json=update_payload)

        assert update_response.status_code == 200
        updated_data = update_response.json()

        assert updated_data["payload"]["summary_text"] == ""

        # Cleanup
        await cleanup_summary(client, summary_id)

    async def test_update_multiple_times(self, client: AsyncClient):
        """
        Test: Update same summary multiple times
        Expected: Each update applies correctly
        """
        # Create summary
        payload = create_test_summary(
            project_id=1001,
            file_id=40,
            summary_text="버전 1"
        )

        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Update 1: Change text
        update1_response = await client.put(f"/summaries/{summary_id}", json={"summary_text": "버전 2"})
        assert update1_response.status_code == 200
        assert update1_response.json()["payload"]["summary_text"] == "버전 2"

        # Update 2: Change project_id
        update2_response = await client.put(f"/summaries/{summary_id}", json={"project_id": 2002})
        assert update2_response.status_code == 200
        data2 = update2_response.json()["payload"]
        assert data2["project_id"] == 2002
        assert data2["summary_text"] == "버전 2"  # Previous update preserved

        # Update 3: Change text again
        update3_response = await client.put(f"/summaries/{summary_id}", json={"summary_text": "버전 3"})
        assert update3_response.status_code == 200
        data3 = update3_response.json()["payload"]
        assert data3["summary_text"] == "버전 3"
        assert data3["project_id"] == 2002  # Previous update preserved

        # Cleanup
        await cleanup_summary(client, summary_id)

    # === Error Cases ===

    async def test_update_nonexistent_summary(self, client: AsyncClient):
        """
        Test: Attempt to update non-existent summary
        Expected: 404 Not Found
        """
        import uuid
        fake_id = str(uuid.uuid4())

        update_payload = {
            "project_id": 9999,
            "summary_text": "존재하지 않는 요약 업데이트"
        }

        response = await client.put(f"/summaries/{fake_id}", json=update_payload)

        assert response.status_code == 404

    async def test_update_invalid_data_type(self, client: AsyncClient):
        """
        Test: Update with invalid data type
        Expected: 422 Unprocessable Entity
        """
        # Create summary
        payload = create_test_summary(
            project_id=1001,
            file_id=50,
            summary_text="타입 검증 테스트"
        )

        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Invalid type for project_id
        update_payload = {
            "project_id": "invalid_string_not_int"
        }

        update_response = await client.put(f"/summaries/{summary_id}", json=update_payload)

        assert update_response.status_code == 422

        # Cleanup
        await cleanup_summary(client, summary_id)

    async def test_update_empty_payload(self, client: AsyncClient):
        """
        Test: Update with empty payload (no fields)
        Expected: 200 OK, no changes made
        """
        # Create summary
        payload = create_test_summary(
            project_id=1001,
            file_id=51,
            summary_text="빈 페이로드 테스트"
        )

        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]
        original_data = create_response.json()

        # Update with empty payload
        update_response = await client.put(f"/summaries/{summary_id}", json={})

        assert update_response.status_code == 200
        updated_data = update_response.json()

        # Verify no changes
        assert updated_data["payload"]["project_id"] == original_data["payload"]["project_id"]
        assert updated_data["payload"]["summary_text"] == original_data["payload"]["summary_text"]

        # Cleanup
        await cleanup_summary(client, summary_id)

    # === Integration Scenarios ===

    async def test_create_update_read_workflow(self, client: AsyncClient):
        """
        Test: Create → Update → Read workflow
        Expected: Updates persist across read operations
        """
        # Create
        payload = create_test_summary(
            project_id=1001,
            file_id=60,
            summary_text="워크플로우 테스트 원본"
        )

        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Update
        update_payload = {
            "project_id": 5005,
            "summary_text": "워크플로우 테스트 수정본"
        }

        update_response = await client.put(f"/summaries/{summary_id}", json=update_payload)
        assert update_response.status_code == 200

        # Read
        read_response = await client.get(f"/summaries/{summary_id}")
        assert read_response.status_code == 200
        read_data = read_response.json()

        # Verify updates persisted
        assert read_data["payload"]["project_id"] == 5005
        assert read_data["payload"]["summary_text"] == "워크플로우 테스트 수정본"

        # Cleanup
        await cleanup_summary(client, summary_id)

    async def test_update_then_search_finds_new_content(self, client: AsyncClient):
        """
        Test: Update summary_text then verify search finds new content
        Expected: Dense/sparse embeddings regenerated, searchable
        """
        # Create
        payload = create_test_summary(
            project_id=1001,
            file_id=61,
            summary_text="검색되지 않을 원본 내용"
        )

        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Update with unique searchable term
        update_payload = {
            "summary_text": "부동산매매계약이행청구소송 특수검색어12345"
        }

        update_response = await client.put(f"/summaries/{summary_id}", json=update_payload)
        assert update_response.status_code == 200

        # Search for new content
        search_payload = {
            "query_text": "특수검색어12345",
            "limit": 10
        }

        search_response = await client.post("/summaries/search/dense", json=search_payload)
        assert search_response.status_code == 200

        search_results = search_response.json()["results"]

        # Verify updated summary is found
        found_ids = [r["point_id"] for r in search_results]
        assert summary_id in found_ids

        # Cleanup
        await cleanup_summary(client, summary_id)
