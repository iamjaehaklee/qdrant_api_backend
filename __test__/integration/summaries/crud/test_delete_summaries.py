"""
Test Suite: Summary Deletion (DELETE /summaries/{summary_id})
Tests for deleting OCR summaries from Qdrant collection
"""

import pytest
import uuid
from httpx import AsyncClient

from __test__.integration.summaries.conftest import (
    create_test_summary,
    cleanup_summary
)


@pytest.mark.asyncio
class TestDeleteSummaries:
    """Test cases for DELETE /summaries/{summary_id} endpoint"""

    async def test_delete_single_summary(self, client: AsyncClient):
        """
        Test: Create summary and delete it
        Expected: 204 No Content
        """
        # Create summary
        payload = create_test_summary(
            project_id=1001,
            file_id=21,
            summary_text="삭제 테스트용 요약입니다."
        )

        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Delete
        delete_response = await client.delete(f"/summaries/{summary_id}")

        assert delete_response.status_code == 204

    async def test_delete_then_read_returns_404(self, client: AsyncClient):
        """
        Test: Delete summary then attempt to read it
        Expected: GET returns 404 Not Found
        """
        # Create
        payload = create_test_summary(
            project_id=1001,
            file_id=22,
            summary_text="삭제 후 조회 테스트입니다."
        )

        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Delete
        delete_response = await client.delete(f"/summaries/{summary_id}")
        assert delete_response.status_code == 204

        # Attempt to read
        read_response = await client.get(f"/summaries/{summary_id}")
        assert read_response.status_code == 404

    async def test_delete_multiple_summaries_sequentially(self, client: AsyncClient):
        """
        Test: Create 5 summaries and delete them one by one
        Expected: All deletions successful
        """
        created_ids = []

        # Create 5 summaries
        for i in range(5):
            payload = create_test_summary(
                project_id=1001,
                file_id=30 + i,
                summary_text=f"배치 삭제 테스트 {i + 1}번 요약입니다."
            )

            create_response = await client.post("/summaries", json=payload)
            created_ids.append(create_response.json()["point_id"])

        # Delete each one
        for summary_id in created_ids:
            delete_response = await client.delete(f"/summaries/{summary_id}")
            assert delete_response.status_code == 204

        # Verify all deleted
        for summary_id in created_ids:
            read_response = await client.get(f"/summaries/{summary_id}")
            assert read_response.status_code == 404

    async def test_delete_already_deleted_summary(self, client: AsyncClient):
        """
        Test: Delete summary twice
        Expected: First delete 204, second delete no error (idempotent)
        """
        # Create
        payload = create_test_summary(
            project_id=1001,
            file_id=40,
            summary_text="중복 삭제 테스트입니다."
        )

        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # First delete
        delete1_response = await client.delete(f"/summaries/{summary_id}")
        assert delete1_response.status_code == 204

        # Second delete (already deleted)
        delete2_response = await client.delete(f"/summaries/{summary_id}")
        # Should be idempotent (204 or no error)
        assert delete2_response.status_code in [204, 404]

    async def test_delete_then_search_not_found(self, client: AsyncClient):
        """
        Test: Delete summary, then verify it doesn't appear in search results
        Expected: Deleted summary not in search results
        """
        # Create with unique searchable text
        payload = create_test_summary(
            project_id=1001,
            file_id=41,
            summary_text="삭제될검색대상요약12345"
        )

        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Verify searchable before deletion
        search_payload = {
            "query_text": "삭제될검색대상요약12345",
            "limit": 10
        }
        search_before = await client.post("/summaries/search/dense", json=search_payload)
        results_before = search_before.json()["results"]
        found_ids_before = [r["point_id"] for r in results_before]
        assert summary_id in found_ids_before

        # Delete
        delete_response = await client.delete(f"/summaries/{summary_id}")
        assert delete_response.status_code == 204

        # Search again
        search_after = await client.post("/summaries/search/dense", json=search_payload)
        results_after = search_after.json()["results"]
        found_ids_after = [r["point_id"] for r in results_after]

        # Verify not in search results
        assert summary_id not in found_ids_after

    async def test_delete_with_long_text_summary(self, client: AsyncClient):
        """
        Test: Delete summary with very long text
        Expected: Deletion successful regardless of text length
        """
        long_text = "부동산 소유권이전등기 청구소송 요약. " * 200

        payload = create_test_summary(
            project_id=1001,
            file_id=50,
            summary_text=long_text
        )

        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Delete
        delete_response = await client.delete(f"/summaries/{summary_id}")
        assert delete_response.status_code == 204

    async def test_delete_with_special_characters(self, client: AsyncClient):
        """
        Test: Delete summary containing special Korean characters
        Expected: Deletion successful
        """
        special_text = "원고 김철수 vs 피고 이영희: 부동산 매매계약 이행청구소송 (2024년도)"

        payload = create_test_summary(
            project_id=1001,
            file_id=51,
            summary_text=special_text
        )

        create_response = await client.post("/summaries", json=payload)
        summary_id = create_response.json()["point_id"]

        # Delete
        delete_response = await client.delete(f"/summaries/{summary_id}")
        assert delete_response.status_code == 204

    # === Error Cases ===

    async def test_delete_nonexistent_summary(self, client: AsyncClient):
        """
        Test: Attempt to delete non-existent summary
        Expected: 204 (idempotent) or 404
        """
        fake_id = str(uuid.uuid4())

        response = await client.delete(f"/summaries/{fake_id}")

        # Delete should be idempotent
        assert response.status_code in [204, 404]

    async def test_delete_invalid_uuid_format(self, client: AsyncClient):
        """
        Test: Attempt to delete with invalid UUID format
        Expected: 422 or 404 or 500
        """
        invalid_id = "not-a-valid-uuid"

        response = await client.delete(f"/summaries/{invalid_id}")

        # Validation error expected
        assert response.status_code in [404, 422, 500]

    async def test_delete_empty_id(self, client: AsyncClient):
        """
        Test: Attempt to delete with empty ID
        Expected: 404 or 405
        """
        response = await client.delete("/summaries/")

        assert response.status_code in [404, 405]

    # === Integration Scenarios ===

    async def test_create_update_delete_workflow(self, client: AsyncClient):
        """
        Test: Complete CRUD workflow: Create → Update → Delete
        Expected: All operations successful
        """
        # Create
        payload = create_test_summary(
            project_id=1001,
            file_id=60,
            summary_text="전체 워크플로우 테스트입니다."
        )

        create_response = await client.post("/summaries", json=payload)
        assert create_response.status_code == 201
        summary_id = create_response.json()["point_id"]

        # Update
        update_payload = {"summary_text": "수정된 텍스트입니다."}
        update_response = await client.put(f"/summaries/{summary_id}", json=update_payload)
        assert update_response.status_code == 200

        # Delete
        delete_response = await client.delete(f"/summaries/{summary_id}")
        assert delete_response.status_code == 204

        # Verify deleted
        read_response = await client.get(f"/summaries/{summary_id}")
        assert read_response.status_code == 404

    async def test_bulk_cleanup_scenario(self, client: AsyncClient):
        """
        Test: Create 10 summaries, delete all at once
        Expected: Clean batch deletion
        """
        created_ids = []

        # Create 10 summaries
        for i in range(10):
            payload = create_test_summary(
                project_id=1001,
                file_id=70 + i,
                summary_text=f"대량 정리 테스트 {i + 1}번입니다."
            )

            create_response = await client.post("/summaries", json=payload)
            created_ids.append(create_response.json()["point_id"])

        # Delete all
        for summary_id in created_ids:
            delete_response = await client.delete(f"/summaries/{summary_id}")
            assert delete_response.status_code == 204

        # Verify all deleted
        for summary_id in created_ids:
            read_response = await client.get(f"/summaries/{summary_id}")
            assert read_response.status_code == 404

    async def test_delete_preserves_other_summaries(self, client: AsyncClient):
        """
        Test: Delete one summary, verify others remain
        Expected: Only deleted summary removed, others intact
        """
        # Create 3 summaries
        summaries = []
        for i in range(3):
            payload = create_test_summary(
                project_id=1001,
                file_id=80 + i,
                summary_text=f"격리 테스트 {i + 1}번 요약입니다."
            )

            create_response = await client.post("/summaries", json=payload)
            summaries.append({
                "id": create_response.json()["point_id"],
                "text": payload["summary_text"]
            })

        # Delete middle one
        delete_id = summaries[1]["id"]
        delete_response = await client.delete(f"/summaries/{delete_id}")
        assert delete_response.status_code == 204

        # Verify deleted one is gone
        read_deleted = await client.get(f"/summaries/{delete_id}")
        assert read_deleted.status_code == 404

        # Verify others still exist
        for i in [0, 2]:
            read_response = await client.get(f"/summaries/{summaries[i]['id']}")
            assert read_response.status_code == 200
            data = read_response.json()
            assert data["payload"]["summary_text"] == summaries[i]["text"]

        # Cleanup remaining
        for i in [0, 2]:
            await cleanup_summary(client, summaries[i]["id"])

    async def test_delete_does_not_affect_search_count(self, client: AsyncClient):
        """
        Test: Create 5 summaries, delete 2, verify search count changes
        Expected: Search returns only remaining 3
        """
        project_id = 9999  # Unique project for isolation
        created_ids = []

        # Create 5 summaries
        for i in range(5):
            payload = create_test_summary(
                project_id=project_id,
                file_id=90 + i,
                summary_text=f"카운트 테스트 {i + 1}번 요약입니다."
            )

            create_response = await client.post("/summaries", json=payload)
            created_ids.append(create_response.json()["point_id"])

        # Search before deletion
        search_payload = {
            "project_id": project_id,
            "limit": 100
        }
        search_before = await client.post("/summaries/search/filter", json=search_payload)
        count_before = len(search_before.json()["results"])
        assert count_before == 5

        # Delete 2 summaries
        for summary_id in created_ids[:2]:
            delete_response = await client.delete(f"/summaries/{summary_id}")
            assert delete_response.status_code == 204

        # Search after deletion
        search_after = await client.post("/summaries/search/filter", json=search_payload)
        count_after = len(search_after.json()["results"])
        assert count_after == 3

        # Cleanup remaining
        for summary_id in created_ids[2:]:
            await cleanup_summary(client, summary_id)
