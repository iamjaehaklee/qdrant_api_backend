"""
Reciprocal Rank Fusion (RRF) Service
Combines multiple ranked result lists using RRF algorithm
"""

from typing import Any, Dict, List


class RRFFusion:
    """
    Reciprocal Rank Fusion implementation for combining search results

    RRF Formula: RRF_score(d) = Σ(1 / (k + rank(d)))
    where:
    - d: document/result
    - k: constant (typically 60)
    - rank(d): rank position of document in result list (1-indexed)
    """

    def __init__(self, k: int = 60):
        """
        Initialize RRF with constant k

        Args:
            k: RRF constant, default 60 (common value in literature)
        """
        self.k = k

    def fuse(
        self,
        result_lists: List[List[Any]],
        id_key: str = "id"
    ) -> List[tuple[Any, float]]:
        """
        Fuse multiple ranked result lists using RRF

        Args:
            result_lists: List of result lists to fuse
            id_key: Key to extract unique identifier from result objects

        Returns:
            List of (result, rrf_score) tuples, sorted by RRF score descending

        Example:
            dense_results = [res1, res2, res3]  # from dense search
            sparse_results = [res2, res4, res1]  # from sparse search

            fuser = RRFFusion(k=60)
            fused = fuser.fuse([dense_results, sparse_results], id_key="point_id")
            # Returns: [(res2, 0.032), (res1, 0.031), (res4, 0.016), (res3, 0.016)]
        """
        # Calculate RRF scores
        rrf_scores: Dict[str, float] = {}
        result_map: Dict[str, Any] = {}

        for result_list in result_lists:
            for rank, result in enumerate(result_list, start=1):
                # Extract unique ID
                result_id = self._get_id(result, id_key)

                # Calculate RRF contribution: 1 / (k + rank)
                rrf_contribution = 1.0 / (self.k + rank)

                # Accumulate RRF score
                if result_id not in rrf_scores:
                    rrf_scores[result_id] = 0.0
                    result_map[result_id] = result

                rrf_scores[result_id] += rrf_contribution

        # Sort by RRF score descending
        sorted_results = sorted(
            rrf_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Return (result, score) tuples
        return [
            (result_map[result_id], score)
            for result_id, score in sorted_results
        ]

    def _get_id(self, result: Any, id_key: str) -> str:
        """
        Extract ID from result object

        Args:
            result: Result object (dict or Pydantic model)
            id_key: Key to extract ID

        Returns:
            String ID
        """
        if isinstance(result, dict):
            return str(result[id_key])
        else:
            # Pydantic model or object with attribute
            return str(getattr(result, id_key))


def reciprocal_rank_fusion(
    dense_results: List[Any],
    sparse_results: List[Any],
    k: int = 60,
    id_key: str = "id"
) -> List[tuple[Any, float]]:
    """
    Convenience function for fusing dense + sparse search results

    Args:
        dense_results: Results from dense vector search
        sparse_results: Results from sparse vector search
        k: RRF constant (default: 60)
        id_key: Key to extract unique identifier

    Returns:
        List of (result, rrf_score) tuples, sorted by RRF score descending

    Example:
        fused = reciprocal_rank_fusion(dense_results, sparse_results, k=60)
        top_10 = fused[:10]  # Get top 10 results
    """
    fuser = RRFFusion(k=k)
    return fuser.fuse([dense_results, sparse_results], id_key=id_key)
