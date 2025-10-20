"""
Korean Sparse Embedding Module
Based on OCR v4 Qdrant implementation with Kiwi morphological analyzer
"""

from typing import List, Dict
import numpy as np
from kiwipiepy import Kiwi
import logging

logger = logging.getLogger(__name__)


class KoreanSparseEmbedding:
    """Korean-specific sparse embedding generator using Kiwi morphological analyzer"""

    def __init__(self):
        """Initialize Korean sparse embedding generator with Kiwi tokenizer"""
        try:
            self.kiwi = Kiwi()
            logger.info("Initialized Korean Sparse Embedding with Kiwi tokenizer")
        except Exception as e:
            logger.error(f"Failed to initialize Kiwi: {e}")
            raise

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize Korean text using Kiwi morphological analyzer

        Args:
            text: Input text

        Returns:
            List of morpheme tokens (filtered by POS tags)
        """
        if not text or not text.strip():
            return []

        try:
            # Analyze text with Kiwi
            result = self.kiwi.tokenize(text)

            if not result:
                return []

            tokens = []
            for token in result:
                # Extract meaningful morphemes
                form = token.form  # 표면형 (surface form)
                tag = token.tag    # 품사 태그 (POS tag)

                # Filter by POS tags (only meaningful morphemes)
                if tag.startswith(('NN', 'VV', 'VA', 'MM', 'MAG', 'XR')):
                    # NN*: 명사류 (nouns)
                    # VV: 동사 (verbs)
                    # VA: 형용사 (adjectives)
                    # MM: 관형사 (determiners)
                    # MAG: 부사 (adverbs)
                    # XR: 어근 (root)
                    tokens.append(form)
                elif tag.startswith('SL'):  # 외국어 (foreign words)
                    tokens.append(form.lower())  # lowercase for English

            return tokens

        except Exception as e:
            logger.warning(f"Tokenization failed for text: {text[:50]}... - {e}")
            # Fallback to simple space splitting
            return text.split()

    def transform(self, text: str) -> Dict[int, float]:
        """
        Transform text to sparse embedding (Qdrant compatible format)
        Uses sublinear TF scaling + L2 normalization

        Args:
            text: Input text

        Returns:
            Dictionary with indices as keys and values as weights
            Format: {index: weight} for Qdrant SparseVector
        """
        tokens = self._tokenize(text)

        if not tokens:
            return {}

        # Count term frequencies
        term_freq = {}
        for token in tokens:
            term_freq[token] = term_freq.get(token, 0) + 1

        # Calculate document length for normalization
        doc_length = len(tokens)

        sparse_dict = {}

        for term, freq in term_freq.items():
            # Create hash index for term (large index space to minimize collisions)
            term_hash = abs(hash(term)) % (2**31)  # ~2.1 billion index space

            # Apply sublinear TF scaling: 1 + log(tf)
            # This reduces the impact of high-frequency terms
            tf_value = 1.0 + np.log(freq) if freq > 0 else 0.0

            # Normalize by document length (sqrt normalization)
            value = tf_value / np.sqrt(doc_length)

            sparse_dict[term_hash] = float(value)

        # L2 normalize the sparse vector
        if sparse_dict:
            values = list(sparse_dict.values())
            norm = np.linalg.norm(values)
            if norm > 0:
                sparse_dict = {k: v / norm for k, v in sparse_dict.items()}

        return sparse_dict

    def batch_transform(self, texts: List[str]) -> List[Dict[int, float]]:
        """
        Transform multiple texts to sparse embeddings

        Args:
            texts: List of input texts

        Returns:
            List of sparse embedding dictionaries
        """
        results = []
        for text in texts:
            sparse_dict = self.transform(text)
            results.append(sparse_dict)
        return results


# Singleton instance for efficient reuse
_korean_sparse_instance = None


def create_korean_sparse_embedding(text: str) -> Dict[int, float]:
    """
    Create sparse embedding for Korean text using singleton instance

    Args:
        text: Input text

    Returns:
        Dictionary with indices as keys and values as weights
    """
    global _korean_sparse_instance

    if _korean_sparse_instance is None:
        _korean_sparse_instance = KoreanSparseEmbedding()

    return _korean_sparse_instance.transform(text)
