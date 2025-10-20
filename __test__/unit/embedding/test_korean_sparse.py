"""
Unit tests for Korean Sparse Embedding
Tests tokenization, POS filtering, and mathematical correctness
"""

import pytest
import numpy as np
from app.korean_sparse_embedding import KoreanSparseEmbedding, create_korean_sparse_embedding


class TestKoreanTokenization:
    """Test Kiwi tokenization and POS filtering"""

    def setup_method(self):
        """Initialize embedder for each test"""
        self.embedder = KoreanSparseEmbedding()

    def test_tokenization_basic(self):
        """Test basic Korean tokenization"""
        text = "개인정보보호법을 위반했습니다"
        tokens = self.embedder._tokenize(text)

        # Should extract meaningful morphemes (nouns, verbs)
        assert "개인" in tokens or "개인정보" in tokens
        assert "보호" in tokens or "보호법" in tokens
        assert "법" in tokens
        assert "위반" in tokens

    def test_tokenization_pos_filtering(self):
        """Test that particles and endings are filtered out"""
        text = "개인정보보호법을 위반했습니다"
        tokens = self.embedder._tokenize(text)

        # Particles (조사) should be filtered: "을"
        assert "을" not in tokens

        # Endings (어미) should be filtered: "습니다", "었"
        assert "습니다" not in tokens
        assert "었" not in tokens

    def test_tokenization_띄어쓰기_variation(self):
        """Test that spacing variations are normalized"""
        text1 = "개인정보보호법"
        text2 = "개인정보 보호 법"

        tokens1 = self.embedder._tokenize(text1)
        tokens2 = self.embedder._tokenize(text2)

        # Both should extract similar morphemes
        assert "개인" in tokens1 or "개인정보" in tokens1
        assert "개인" in tokens2 or "개인정보" in tokens2

    def test_tokenization_empty_text(self):
        """Test empty text handling"""
        tokens = self.embedder._tokenize("")
        assert tokens == []

        tokens = self.embedder._tokenize("   ")
        assert tokens == []

    def test_tokenization_english_text(self):
        """Test English text handling (foreign words)"""
        text = "This is a test with API endpoint"
        tokens = self.embedder._tokenize(text)

        # English words should be lowercased
        assert "api" in tokens or "test" in tokens


class TestSparseEmbeddingMath:
    """Test mathematical correctness of sparse embeddings"""

    def setup_method(self):
        """Initialize embedder for each test"""
        self.embedder = KoreanSparseEmbedding()

    def test_sparse_embedding_structure(self):
        """Test sparse embedding output structure"""
        text = "개인정보보호법을 위반했습니다"
        sparse_dict = self.embedder.transform(text)

        # Should return non-empty dictionary
        assert isinstance(sparse_dict, dict)
        assert len(sparse_dict) > 0

        # Keys should be integers (hash indices)
        for key in sparse_dict.keys():
            assert isinstance(key, int)
            assert 0 <= key < 2**31  # Index space: 0 ~ 2^31-1

        # Values should be floats
        for value in sparse_dict.values():
            assert isinstance(value, float)
            assert 0.0 <= value <= 1.0  # After L2 normalization

    def test_l2_normalization(self):
        """Test L2 normalization (vector length should be ~1.0)"""
        text = "개인정보보호법을 위반했습니다"
        sparse_dict = self.embedder.transform(text)

        # Calculate L2 norm
        values = list(sparse_dict.values())
        l2_norm = np.linalg.norm(values)

        # Should be approximately 1.0 (within floating point precision)
        assert 0.99 <= l2_norm <= 1.01

    def test_sublinear_tf_scaling(self):
        """Test sublinear TF scaling (1 + log(freq))"""
        # Text with repeated term
        text = "개인정보 개인정보 개인정보"
        sparse_dict = self.embedder.transform(text)

        # Should have non-zero values
        assert len(sparse_dict) > 0
        assert all(v > 0 for v in sparse_dict.values())

    def test_empty_text_handling(self):
        """Test empty text returns empty dict"""
        sparse_dict = self.embedder.transform("")
        assert sparse_dict == {}

        sparse_dict = self.embedder.transform("   ")
        assert sparse_dict == {}

    def test_consistency(self):
        """Test same text produces same embedding"""
        text = "개인정보보호법을 위반했습니다"

        sparse1 = self.embedder.transform(text)
        sparse2 = self.embedder.transform(text)

        # Should be identical
        assert sparse1.keys() == sparse2.keys()
        for key in sparse1.keys():
            assert abs(sparse1[key] - sparse2[key]) < 1e-6


class TestBatchProcessing:
    """Test batch transformation"""

    def setup_method(self):
        """Initialize embedder for each test"""
        self.embedder = KoreanSparseEmbedding()

    def test_batch_transform(self):
        """Test batch processing returns correct number of results"""
        texts = [
            "개인정보보호법을 위반했습니다",
            "손해배상을 청구합니다",
            "계약을 해지하겠습니다"
        ]

        results = self.embedder.batch_transform(texts)

        assert len(results) == len(texts)
        for result in results:
            assert isinstance(result, dict)
            assert len(result) > 0

    def test_batch_empty_texts(self):
        """Test batch with empty texts"""
        texts = ["", "개인정보", ""]
        results = self.embedder.batch_transform(texts)

        assert len(results) == 3
        assert results[0] == {}  # Empty text
        assert len(results[1]) > 0  # Has content
        assert results[2] == {}  # Empty text


class TestSingletonFunction:
    """Test convenience singleton function"""

    def test_singleton_creation(self):
        """Test singleton instance creation"""
        sparse1 = create_korean_sparse_embedding("테스트")
        sparse2 = create_korean_sparse_embedding("테스트")

        # Should use same instance (same results)
        assert sparse1 == sparse2

    def test_singleton_output(self):
        """Test singleton function output"""
        sparse = create_korean_sparse_embedding("개인정보보호법")

        assert isinstance(sparse, dict)
        assert len(sparse) > 0


class TestRealWorldExamples:
    """Test with real-world Korean legal text examples"""

    def setup_method(self):
        """Initialize embedder for each test"""
        self.embedder = KoreanSparseEmbedding()

    def test_legal_text(self):
        """Test with legal document text"""
        text = "피고는 2020년 6월경 원고와 사이에 유박 단미사료 펠렛 및 자동포장 생산라인 설비시스템 설치 공사에 관한 도급계약을 체결하였다"
        sparse = self.embedder.transform(text)

        # Should extract key legal terms
        tokens = self.embedder._tokenize(text)
        assert any("피고" in t for t in tokens)
        assert any("원고" in t for t in tokens)
        assert any("계약" in t for t in tokens)

        # Should produce valid sparse vector
        assert len(sparse) > 0
        values = list(sparse.values())
        l2_norm = np.linalg.norm(values)
        assert 0.99 <= l2_norm <= 1.01

    def test_mixed_korean_english(self):
        """Test with mixed Korean and English text"""
        text = "API 서버에서 JSON 데이터를 받았습니다"
        sparse = self.embedder.transform(text)

        tokens = self.embedder._tokenize(text)

        # Korean terms should be present
        assert any("서버" in t for t in tokens)
        assert any("데이터" in t for t in tokens)

        # English terms should be lowercased
        assert "api" in tokens or "json" in tokens

        # Valid sparse vector
        assert len(sparse) > 0
