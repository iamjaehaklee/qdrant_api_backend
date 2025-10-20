"""
Search Service
Common utilities for search operations
"""

from typing import Optional
from qdrant_client.models import Filter, FieldCondition, MatchValue


def build_search_filter(
    project_id: Optional[int] = None,
    file_id: Optional[int] = None,
    language: Optional[str] = None,
    pages: Optional[list[int]] = None
) -> Optional[Filter]:
    """
    Build Qdrant filter from search parameters

    Args:
        project_id: Filter by project ID
        file_id: Filter by file ID
        language: Filter by language
        pages: Filter by page numbers

    Returns:
        Qdrant Filter object or None if no filters
    """
    filter_conditions = []

    if project_id is not None:
        filter_conditions.append(
            FieldCondition(key="project_id", match=MatchValue(value=project_id))
        )

    if file_id is not None:
        filter_conditions.append(
            FieldCondition(key="file_id", match=MatchValue(value=file_id))
        )

    if language is not None:
        filter_conditions.append(
            FieldCondition(key="language", match=MatchValue(value=language))
        )

    if pages is not None and len(pages) > 0:
        # Match any of the page numbers
        for page in pages:
            filter_conditions.append(
                FieldCondition(key="pages", match=MatchValue(value=page))
            )

    return Filter(must=filter_conditions) if filter_conditions else None


def convert_qdrant_result_to_response(result, include_score: bool = True):
    """
    Convert Qdrant search result to response format

    Args:
        result: Qdrant search result object
        include_score: Whether to include score in response

    Returns:
        Dictionary with point_id, payload, and optional score
    """
    response = {
        "point_id": str(result.id),
        "payload": result.payload
    }

    if include_score and hasattr(result, 'score') and result.score is not None:
        response["score"] = result.score

    return response
