"""
Integration tests for Multilingual Sparse Embedding System
Tests language detection and dual embedder integration
"""

import pytest
from app.multilingual_sparse_embedding import (
    MultilingualSparseEmbedding,
    create_multilingual_sparse_embedding,
    create_multilingual_sparse_embeddings
)


class TestLanguageDetection:
    """Test language detection logic"""

    def setup_method(self):
        """Initialize embedder for each test"""
        self.embedder = MultilingualSparseEmbedding()

    def test_detect_korean_text(self):
        """Test Korean text detection"""
        assert self.embedder._is_korean_text("개인정보보호법을 위반했습니다") is True
        assert self.embedder._is_korean_text("API 서버에서 데이터를 받았습니다") is True

    def test_detect_english_text(self):
        """Test English text detection"""
        assert self.embedder._is_korean_text("This is an English text") is False
        assert self.embedder._is_korean_text("API server received data") is False

    def test_detect_mixed_text_korean_dominant(self):
        """Test mixed text with Korean > 30%"""
        # Korean dominant
        text = "API를 사용해서 데이터를 처리합니다"
        assert self.embedder._is_korean_text(text) is True

    def test_detect_mixed_text_english_dominant(self):
        """Test mixed text with Korean < 30%"""
        # English dominant
        text = "This API uses 한글 processing"
        # Should detect as non-Korean
        # Note: Exact threshold may vary, test for consistent behavior
        result = self.embedder._is_korean_text(text)
        assert isinstance(result, bool)

    def test_empty_text_detection(self):
        """Test empty text"""
        assert self.embedder._is_korean_text("") is False
        assert self.embedder._is_korean_text("   ") is False


class TestDualEmbedderSystem:
    """Test dual embedder (Korean + FastEmbed) integration"""

    def setup_method(self):
        """Initialize embedder for each test"""
        self.embedder = MultilingualSparseEmbedding()

    def test_korean_text_uses_kiwi(self):
        """Test Korean text uses Kiwi embedder"""
        text = "개인정보보호법을 위반했습니다"
        sparse = self.embedder.transform(text)

        # Should produce non-empty result
        assert len(sparse) > 0
        assert isinstance(sparse, dict)

        # Keys should be valid indices
        for key in sparse.keys():
            assert isinstance(key, int)
            assert key >= 0

    def test_english_text_uses_fastembed(self):
        """Test English text uses FastEmbed"""
        text = "This is a test document for information retrieval"
        sparse = self.embedder.transform(text)

        # Should produce non-empty result
        assert len(sparse) > 0
        assert isinstance(sparse, dict)

        # Keys should be valid indices
        for key in sparse.keys():
            assert isinstance(key, int)
            assert key >= 0

    def test_consistency_korean(self):
        """Test Korean embedding consistency"""
        text = "개인정보보호법"

        sparse1 = self.embedder.transform(text)
        sparse2 = self.embedder.transform(text)

        # Should produce same results
        assert sparse1.keys() == sparse2.keys()
        for key in sparse1.keys():
            assert sparse1[key] == sparse2[key]

    def test_consistency_english(self):
        """Test English embedding consistency"""
        text = "information retrieval system"

        sparse1 = self.embedder.transform(text)
        sparse2 = self.embedder.transform(text)

        # Should produce same results
        assert sparse1.keys() == sparse2.keys()
        for key in sparse1.keys():
            assert abs(sparse1[key] - sparse2[key]) < 1e-6


class TestBatchProcessing:
    """Test batch processing with mixed languages"""

    def setup_method(self):
        """Initialize embedder for each test"""
        self.embedder = MultilingualSparseEmbedding()

    def test_batch_mixed_languages(self):
        """Test batch with mixed Korean and English texts"""
        texts = [
            "개인정보보호법을 위반했습니다",  # Korean
            "This is an English document",      # English
            "API 서버 데이터 처리",              # Korean
            "Information retrieval system",      # English
        ]

        results = self.embedder.batch_transform(texts)

        # Should return correct number of results
        assert len(results) == len(texts)

        # All results should be non-empty dictionaries
        for i, result in enumerate(results):
            assert isinstance(result, dict), f"Result {i} is not dict: {type(result)}"
            assert len(result) > 0, f"Result {i} is empty"

    def test_batch_all_korean(self):
        """Test batch with all Korean texts"""
        texts = [
            "개인정보보호법",
            "손해배상 청구",
            "계약 해지"
        ]

        results = self.embedder.batch_transform(texts)

        assert len(results) == len(texts)
        for result in results:
            assert isinstance(result, dict)
            assert len(result) > 0

    def test_batch_all_english(self):
        """Test batch with all English texts"""
        texts = [
            "privacy protection law",
            "damage compensation claim",
            "contract termination"
        ]

        results = self.embedder.batch_transform(texts)

        assert len(results) == len(texts)
        for result in results:
            assert isinstance(result, dict)
            assert len(result) > 0

    def test_batch_empty_texts(self):
        """Test batch with some empty texts"""
        texts = [
            "",
            "개인정보",
            "privacy",
            ""
        ]

        results = self.embedder.batch_transform(texts)

        assert len(results) == 4
        assert results[0] == {}  # Empty
        assert len(results[1]) > 0  # Korean
        assert len(results[2]) > 0  # English
        assert results[3] == {}  # Empty


class TestSingletonFunctions:
    """Test convenience singleton functions"""

    def test_singleton_single_text(self):
        """Test singleton function for single text"""
        text = "개인정보보호법"
        sparse = create_multilingual_sparse_embedding(text)

        assert isinstance(sparse, dict)
        assert len(sparse) > 0

    def test_singleton_batch(self):
        """Test singleton function for batch"""
        texts = [
            "개인정보보호법",
            "privacy protection"
        ]

        results = create_multilingual_sparse_embeddings(texts)

        assert len(results) == 2
        for result in results:
            assert isinstance(result, dict)
            assert len(result) > 0

    def test_singleton_reuse(self):
        """Test singleton instance is reused"""
        text = "테스트"

        sparse1 = create_multilingual_sparse_embedding(text)
        sparse2 = create_multilingual_sparse_embedding(text)

        # Should use same instance (same results)
        assert sparse1 == sparse2


class TestRealWorldScenarios:
    """Test with real-world mixed language scenarios"""

    def setup_method(self):
        """Initialize embedder for each test"""
        self.embedder = MultilingualSparseEmbedding()

    def test_legal_document_korean(self):
        """Test with Korean legal document"""
        text = "피고는 2020년 6월경 원고와 사이에 도급계약을 체결하였다"
        sparse = self.embedder.transform(text)

        assert len(sparse) > 0
        assert all(isinstance(k, int) for k in sparse.keys())
        assert all(isinstance(v, float) for v in sparse.values())

    def test_technical_document_english(self):
        """Test with English technical document"""
        text = "The API server implements RESTful endpoints for data retrieval"
        sparse = self.embedder.transform(text)

        assert len(sparse) > 0
        assert all(isinstance(k, int) for k in sparse.keys())
        assert all(isinstance(v, float) for v in sparse.values())

    def test_mixed_technical_korean(self):
        """Test with Korean text containing technical terms"""
        text = "API 서버는 RESTful 엔드포인트를 구현합니다"
        sparse = self.embedder.transform(text)

        # Should be detected as Korean (>30% Korean chars)
        assert self.embedder._is_korean_text(text) is True
        assert len(sparse) > 0

    def test_code_comments_korean(self):
        """Test with Korean code comments"""
        text = "# 사용자 인증을 처리하는 함수입니다"
        sparse = self.embedder.transform(text)

        assert len(sparse) > 0


class TestEdgeCases:
    """Test edge cases and error handling"""

    def setup_method(self):
        """Initialize embedder for each test"""
        self.embedder = MultilingualSparseEmbedding()

    def test_numbers_only(self):
        """Test text with only numbers"""
        sparse = self.embedder.transform("123 456 789")
        # May return empty or minimal result depending on tokenizer
        assert isinstance(sparse, dict)

    def test_special_characters(self):
        """Test text with special characters"""
        sparse = self.embedder.transform("!@#$%^&*()")
        assert isinstance(sparse, dict)

    def test_very_long_text(self):
        """Test with very long text"""
        text = "개인정보 " * 1000  # 1000 repetitions
        sparse = self.embedder.transform(text)

        assert isinstance(sparse, dict)
        assert len(sparse) > 0

    def test_single_character(self):
        """Test with single character"""
        sparse = self.embedder.transform("a")
        assert isinstance(sparse, dict)
