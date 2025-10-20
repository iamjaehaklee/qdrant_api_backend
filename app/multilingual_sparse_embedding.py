"""
Multilingual Sparse Embedding Module
Dual embedder system: Korean (Kiwi) + Non-Korean (FastEmbed BM25)
"""

from typing import List, Dict
import logging
from app.korean_sparse_embedding import KoreanSparseEmbedding

logger = logging.getLogger(__name__)


class MultilingualSparseEmbedding:
    """Multilingual sparse embedding with language-specific embedders"""

    def __init__(self):
        """Initialize both Korean and FastEmbed sparse embedders"""
        # Initialize Korean sparse embedder
        try:
            self.korean_embedder = KoreanSparseEmbedding()
            logger.info("Initialized Korean sparse embedder (Kiwi)")
        except Exception as e:
            logger.warning(f"Failed to initialize Korean sparse embedder: {e}")
            self.korean_embedder = None

        # Initialize FastEmbed as fallback for non-Korean text
        try:
            from fastembed import SparseTextEmbedding
            # Using Qdrant BM25 model for sparse embeddings
            self.fastembed_embedder = SparseTextEmbedding(model_name="Qdrant/bm25")
            logger.info("Initialized FastEmbed BM25 sparse embedder")
        except ImportError:
            logger.warning("fastembed not installed. Fallback sparse embedding unavailable.")
            self.fastembed_embedder = None
        except Exception as e:
            logger.warning(f"Failed to initialize FastEmbed: {e}")
            self.fastembed_embedder = None

    def _is_korean_text(self, text: str) -> bool:
        """
        Detect if text is primarily Korean

        Args:
            text: Input text

        Returns:
            True if text contains >= 30% Korean characters
        """
        if not text:
            return False

        korean_chars = sum(1 for c in text if '\uac00' <= c <= '\ud7af')
        total_chars = len(text.replace(' ', ''))

        if total_chars == 0:
            return False

        korean_ratio = korean_chars / total_chars
        return korean_ratio >= 0.3

    def transform(self, text: str) -> Dict[int, float]:
        """
        Generate sparse embedding using appropriate embedder based on language detection

        Args:
            text: Input text

        Returns:
            Dictionary with indices as keys and values as weights
        """
        if not text or not text.strip():
            return {}

        try:
            # Detect language and choose appropriate embedder
            is_korean = self._is_korean_text(text)

            # Use Korean embedder for Korean text
            if is_korean and self.korean_embedder:
                sparse_dict = self.korean_embedder.transform(text)
                if sparse_dict:
                    logger.debug(f"Generated Korean sparse embedding with {len(sparse_dict)} indices")
                    return sparse_dict

            # Fallback to FastEmbed for non-Korean text or if Korean embedder fails
            if self.fastembed_embedder:
                embeddings = list(self.fastembed_embedder.embed([text]))

                if embeddings and len(embeddings) > 0:
                    sparse_embedding = embeddings[0]

                    if hasattr(sparse_embedding, 'indices') and hasattr(sparse_embedding, 'values'):
                        sparse_dict = {}
                        for idx, val in zip(sparse_embedding.indices, sparse_embedding.values):
                            sparse_dict[int(idx)] = float(val)
                        logger.debug(f"Generated FastEmbed sparse embedding with {len(sparse_dict)} indices")
                        return sparse_dict

            logger.warning("No sparse embedder available")
            return {}

        except Exception as e:
            logger.error(f"Failed to generate sparse embedding: {e}")
            return {}

    def batch_transform(self, texts: List[str]) -> List[Dict[int, float]]:
        """
        Generate sparse embeddings for multiple texts in batch
        Optimized: separates Korean/non-Korean texts, processes in parallel, merges in order

        Args:
            texts: List of texts to embed

        Returns:
            List of sparse embedding dictionaries
        """
        if not texts:
            return []

        try:
            # Separate Korean and non-Korean texts
            korean_indices = []
            korean_texts = []
            non_korean_indices = []
            non_korean_texts = []

            for i, text in enumerate(texts):
                if self._is_korean_text(text):
                    korean_indices.append(i)
                    korean_texts.append(text)
                else:
                    non_korean_indices.append(i)
                    non_korean_texts.append(text)

            # Process Korean texts with Kiwi
            korean_results = []
            if korean_texts and self.korean_embedder:
                korean_results = self.korean_embedder.batch_transform(korean_texts)
                logger.debug(f"Generated {len(korean_results)} Korean sparse embeddings")

            # Process non-Korean texts with FastEmbed
            non_korean_results = []
            if non_korean_texts and self.fastembed_embedder:
                embeddings_list = list(self.fastembed_embedder.embed(non_korean_texts))
                for sparse_embedding in embeddings_list:
                    if hasattr(sparse_embedding, 'indices') and hasattr(sparse_embedding, 'values'):
                        sparse_dict = {}
                        for idx, val in zip(sparse_embedding.indices, sparse_embedding.values):
                            sparse_dict[int(idx)] = float(val)
                        non_korean_results.append(sparse_dict)
                    else:
                        non_korean_results.append({})
                logger.debug(f"Generated {len(non_korean_results)} FastEmbed sparse embeddings")

            # Combine results in original order
            result = [{}] * len(texts)
            for i, idx in enumerate(korean_indices):
                if i < len(korean_results):
                    result[idx] = korean_results[i]
            for i, idx in enumerate(non_korean_indices):
                if i < len(non_korean_results):
                    result[idx] = non_korean_results[i]

            return result

        except Exception as e:
            logger.error(f"Failed to generate batch sparse embeddings: {e}")
            return [{} for _ in texts]


# Singleton instance for efficient reuse
_multilingual_sparse_instance = None


def create_multilingual_sparse_embedding(text: str) -> Dict[int, float]:
    """
    Create sparse embedding for text using singleton multilingual instance

    Args:
        text: Input text (any language)

    Returns:
        Dictionary with indices as keys and values as weights
    """
    global _multilingual_sparse_instance

    if _multilingual_sparse_instance is None:
        _multilingual_sparse_instance = MultilingualSparseEmbedding()

    return _multilingual_sparse_instance.transform(text)


def create_multilingual_sparse_embeddings(texts: List[str]) -> List[Dict[int, float]]:
    """
    Create sparse embeddings for multiple texts using singleton instance

    Args:
        texts: List of input texts (any language)

    Returns:
        List of sparse embedding dictionaries
    """
    global _multilingual_sparse_instance

    if _multilingual_sparse_instance is None:
        _multilingual_sparse_instance = MultilingualSparseEmbedding()

    return _multilingual_sparse_instance.batch_transform(texts)
