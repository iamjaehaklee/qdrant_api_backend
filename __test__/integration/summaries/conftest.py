"""
Pytest Fixtures for OCR Summaries Integration Tests
Provides common test utilities, fixtures, and sample data loading
"""

import json
import pytest
import pytest_asyncio
from pathlib import Path
from typing import List, Dict
from httpx import AsyncClient

from app.main import app


# === Sample Data Paths ===

SAMPLE_DATA_DIR = Path(__file__).parent.parent.parent / "sample_generated" / "부동산소유권등기소송" / "ocr_summaries"


# === HTTP Client Fixture ===

@pytest_asyncio.fixture
async def client():
    """
    Async HTTP client for testing FastAPI endpoints
    Server must be running on localhost:6030
    """
    async with AsyncClient(base_url="http://localhost:6030") as ac:
        yield ac


# === Sample Data Loading ===

def load_sample_summaries(limit: int = None) -> List[Dict]:
    """
    Load sample summary JSON files from test data directory

    Args:
        limit: Maximum number of samples to load (None = all)

    Returns:
        List of summary dictionaries
    """
    if not SAMPLE_DATA_DIR.exists():
        raise FileNotFoundError(f"Sample data directory not found: {SAMPLE_DATA_DIR}")

    json_files = sorted(SAMPLE_DATA_DIR.glob("*.json"))

    if limit:
        json_files = json_files[:limit]

    summaries = []
    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as f:
            summary = json.load(f)
            summaries.append(summary)

    return summaries


def load_single_summary(filename: str) -> Dict:
    """
    Load a specific summary file by filename

    Args:
        filename: JSON filename (e.g., "갑1호증_매매계약서.json")

    Returns:
        Summary dictionary
    """
    file_path = SAMPLE_DATA_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Sample file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_summaries():
    """Fixture providing 5 sample summaries"""
    return load_sample_summaries(limit=5)


@pytest.fixture
def single_sample_summary():
    """Fixture providing single sample summary"""
    samples = load_sample_summaries(limit=1)
    return samples[0] if samples else None


@pytest.fixture
def all_sample_summaries():
    """Fixture providing all sample summaries (51 files)"""
    return load_sample_summaries()


# === Test Data Generators ===

def create_test_summary(
    summary_id: str = None,
    project_id: int = 1001,
    file_id: int = 21,
    summary_text: str = "테스트 요약 텍스트입니다.",
    correlation_id: str = "test-correlation-id",
    request_timestamp: str = "2025-01-20T00:00:00Z"
) -> Dict:
    """
    Create a test summary payload

    Args:
        summary_id: UUID string (auto-generated if None)
        project_id: Project ID
        file_id: File ID
        summary_text: Summary text content
        correlation_id: Distributed tracing correlation ID
        request_timestamp: Initial request timestamp (ISO 8601)

    Returns:
        Summary creation payload
    """
    payload = {
        "project_id": project_id,
        "file_id": file_id,
        "summary_text": summary_text,
        "correlation_id": correlation_id,
        "request_timestamp": request_timestamp
    }

    if summary_id:
        payload["summary_id"] = summary_id

    return payload


# === Cleanup Helpers ===

async def cleanup_summary(client: AsyncClient, summary_id: str) -> bool:
    """
    Delete a summary by ID (helper for test cleanup)

    Args:
        client: HTTP client
        summary_id: Summary ID to delete

    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        response = await client.delete(f"/summaries/{summary_id}")
        return response.status_code == 204
    except Exception:
        return False


async def cleanup_summaries(client: AsyncClient, summary_ids: List[str]) -> int:
    """
    Delete multiple summaries (batch cleanup)

    Args:
        client: HTTP client
        summary_ids: List of summary IDs to delete

    Returns:
        Number of successfully deleted summaries
    """
    deleted_count = 0
    for summary_id in summary_ids:
        if await cleanup_summary(client, summary_id):
            deleted_count += 1
    return deleted_count


@pytest_asyncio.fixture
async def cleanup_test_summaries(client):
    """
    Fixture that provides cleanup function for created summaries
    Usage: created_ids = []; cleanup_fn = cleanup_test_summaries; ... cleanup_fn(created_ids)
    """
    created_ids = []

    yield created_ids

    # Cleanup after test
    if created_ids:
        await cleanup_summaries(client, created_ids)


# === Assertion Helpers ===

def assert_summary_response(response_data: Dict, expected_payload: Dict = None):
    """
    Assert that summary response has correct structure

    Args:
        response_data: Response JSON data
        expected_payload: Expected payload values to check
    """
    assert "point_id" in response_data
    assert "payload" in response_data

    payload = response_data["payload"]
    assert "summary_id" in payload
    assert "project_id" in payload
    assert "summary_text" in payload
    assert "created_at" in payload

    if expected_payload:
        if "project_id" in expected_payload:
            assert payload["project_id"] == expected_payload["project_id"]
        if "file_id" in expected_payload:
            assert payload["file_id"] == expected_payload["file_id"]
        if "summary_text" in expected_payload:
            assert payload["summary_text"] == expected_payload["summary_text"]


def assert_search_response(response_data: Dict, min_results: int = 0, max_results: int = None):
    """
    Assert that search response has correct structure

    Args:
        response_data: Response JSON data
        min_results: Minimum expected results
        max_results: Maximum expected results
    """
    assert "results" in response_data
    assert "total" in response_data
    assert "limit" in response_data

    results = response_data["results"]
    assert isinstance(results, list)
    assert len(results) >= min_results

    if max_results is not None:
        assert len(results) <= max_results

    # Check each result structure
    for result in results:
        assert "point_id" in result
        assert "payload" in result


def assert_scores_descending(results: List[Dict]):
    """
    Assert that search results are sorted by score in descending order

    Args:
        results: List of search result dictionaries
    """
    scores = [r.get("score") for r in results if r.get("score") is not None]

    if len(scores) > 1:
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], f"Scores not descending: {scores}"
