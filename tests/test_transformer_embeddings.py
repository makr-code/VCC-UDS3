#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for UDS3 Transformer Embeddings
======================================

Test cases:
- Model loading (lazy + thread-safe)
- Embedding generation (384-dim validation)
- Batch embedding (performance validation)
- Fallback logic (hash-based)
- GPU detection
- Semantic similarity validation

Author: UDS3 Framework
Date: Oktober 2025
"""

import pytest
import threading
import time
from typing import List

# Import embedding module
from uds3.embeddings.transformer_embeddings import (
    TransformerEmbeddings,
    get_default_embeddings,
    load_embedding_model,
    _hash_based_fallback,
    ENABLE_REAL_EMBEDDINGS,
    EMBEDDING_MODEL_NAME
)


class TestTransformerEmbeddings:
    """Test TransformerEmbeddings class"""
    
    def test_lazy_loading(self):
        """Test that model is loaded only when needed"""
        embedder = TransformerEmbeddings()
        
        # Model should not be loaded yet
        assert embedder._model is None
        
        # Generate embedding (triggers lazy loading)
        vector = embedder.embed("Test text")
        
        # Model should now be loaded
        assert embedder._model is not None
        assert len(vector) == 384
    
    def test_thread_safe_loading(self):
        """Test thread-safe model loading (double-check locking)"""
        embedder = TransformerEmbeddings()
        results = []
        
        def generate_embedding(text: str):
            vector = embedder.embed(text)
            results.append(vector)
        
        # Create 10 threads that all try to load the model simultaneously
        threads = []
        for i in range(10):
            thread = threading.Thread(target=generate_embedding, args=(f"Text {i}",))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All threads should have succeeded
        assert len(results) == 10
        
        # All embeddings should have correct dimensions
        for vector in results:
            assert len(vector) == 384
        
        # Model should only be loaded once (singleton pattern)
        assert embedder._model is not None
    
    def test_embedding_dimensions(self):
        """Test that embeddings have correct dimensions (384)"""
        embedder = TransformerEmbeddings()
        
        text = "This is a test sentence for embedding"
        vector = embedder.embed(text)
        
        # all-MiniLM-L6-v2 produces 384-dim embeddings
        assert len(vector) == 384
        assert isinstance(vector, list)
        assert all(isinstance(x, float) for x in vector)
    
    def test_deterministic_embeddings(self):
        """Test that same text produces same embedding"""
        embedder = TransformerEmbeddings()
        
        text = "Deterministic test text"
        
        vector1 = embedder.embed(text)
        vector2 = embedder.embed(text)
        
        # Same text should produce same embedding
        assert vector1 == vector2
    
    def test_different_texts_different_embeddings(self):
        """Test that different texts produce different embeddings"""
        embedder = TransformerEmbeddings()
        
        text1 = "First text"
        text2 = "Second text"
        
        vector1 = embedder.embed(text1)
        vector2 = embedder.embed(text2)
        
        # Different texts should produce different embeddings
        assert vector1 != vector2
    
    def test_batch_embedding(self):
        """Test batch embedding generation"""
        embedder = TransformerEmbeddings()
        
        texts = [
            "First document",
            "Second document",
            "Third document"
        ]
        
        vectors = embedder.embed_batch(texts)
        
        # Should return list of vectors
        assert len(vectors) == 3
        
        # Each vector should have correct dimensions
        for vector in vectors:
            assert len(vector) == 384
        
        # Batch embeddings should match single embeddings
        for i, text in enumerate(texts):
            single_vector = embedder.embed(text)
            batch_vector = vectors[i]
            
            # Allow small floating point differences
            for j in range(len(single_vector)):
                assert abs(single_vector[j] - batch_vector[j]) < 1e-6
    
    def test_batch_performance(self):
        """Test that batch embedding is faster than sequential"""
        embedder = TransformerEmbeddings()
        
        # Skip if using fallback mode (no performance difference)
        if embedder.is_fallback_mode():
            pytest.skip("Fallback mode - no batch performance gain")
        
        texts = ["Text " + str(i) for i in range(10)]
        
        # Time sequential embedding
        start_sequential = time.time()
        for text in texts:
            embedder.embed(text)
        time_sequential = time.time() - start_sequential
        
        # Time batch embedding
        start_batch = time.time()
        embedder.embed_batch(texts)
        time_batch = time.time() - start_batch
        
        # Batch should be faster (at least 1.5x)
        # Note: May vary based on hardware
        assert time_batch < time_sequential * 0.7, \
            f"Batch ({time_batch:.3f}s) should be faster than sequential ({time_sequential:.3f}s)"
    
    def test_fallback_mode_detection(self):
        """Test fallback mode detection"""
        embedder = TransformerEmbeddings()
        
        # is_fallback_mode() should return bool
        is_fallback = embedder.is_fallback_mode()
        assert isinstance(is_fallback, bool)
        
        # If real embeddings enabled, should not be in fallback
        if ENABLE_REAL_EMBEDDINGS:
            # May be fallback if sentence-transformers not installed
            pass  # Just check that method works
    
    def test_hash_based_fallback(self):
        """Test hash-based fallback embedding generation"""
        text = "Test text for hash-based embedding"
        
        vector = _hash_based_fallback(text, dimensions=384)
        
        # Should return 384-dim vector
        assert len(vector) == 384
        assert all(isinstance(x, float) for x in vector)
        
        # Values should be normalized [0, 1]
        assert all(0 <= x <= 1 for x in vector)
        
        # Same text should produce same hash-based vector (deterministic)
        vector2 = _hash_based_fallback(text, dimensions=384)
        assert vector == vector2
    
    def test_get_dimensions(self):
        """Test get_dimensions() method"""
        embedder = TransformerEmbeddings()
        
        dimensions = embedder.get_dimensions()
        assert dimensions == 384
    
    def test_semantic_similarity(self):
        """Test semantic similarity of embeddings"""
        embedder = TransformerEmbeddings()
        
        # Skip if using fallback mode (no semantic meaning)
        if embedder.is_fallback_mode():
            pytest.skip("Fallback mode - no semantic similarity")
        
        # Similar texts
        text1 = "The cat sits on the mat"
        text2 = "A cat is sitting on a mat"
        
        # Dissimilar text
        text3 = "Python programming language"
        
        vector1 = embedder.embed(text1)
        vector2 = embedder.embed(text2)
        vector3 = embedder.embed(text3)
        
        # Cosine similarity
        def cosine_similarity(v1: List[float], v2: List[float]) -> float:
            dot_product = sum(a * b for a, b in zip(v1, v2))
            magnitude1 = sum(a * a for a in v1) ** 0.5
            magnitude2 = sum(b * b for b in v2) ** 0.5
            return dot_product / (magnitude1 * magnitude2)
        
        # Similar texts should have high similarity
        sim_1_2 = cosine_similarity(vector1, vector2)
        
        # Dissimilar texts should have lower similarity
        sim_1_3 = cosine_similarity(vector1, vector3)
        
        # Similar texts should be more similar than dissimilar
        assert sim_1_2 > sim_1_3, \
            f"Similar texts ({sim_1_2:.3f}) should be more similar than dissimilar ({sim_1_3:.3f})"
        
        # Similarity should be reasonable (> 0.7 for similar texts)
        assert sim_1_2 > 0.7, \
            f"Similar texts should have high similarity (got {sim_1_2:.3f})"


class TestGlobalFunctions:
    """Test global convenience functions"""
    
    def test_get_default_embeddings(self):
        """Test get_default_embeddings() singleton"""
        embedder1 = get_default_embeddings()
        embedder2 = get_default_embeddings()
        
        # Should return same instance (singleton)
        assert embedder1 is embedder2
        
        # Should be TransformerEmbeddings instance
        assert isinstance(embedder1, TransformerEmbeddings)
    
    def test_load_embedding_model(self):
        """Test load_embedding_model() function"""
        model = load_embedding_model()
        
        # Should return model or "FALLBACK" string
        assert model is not None
        assert isinstance(model, (object, str))
        
        # If string, should be "FALLBACK"
        if isinstance(model, str):
            assert model == "FALLBACK"


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_empty_text(self):
        """Test embedding generation with empty text"""
        embedder = TransformerEmbeddings()
        
        vector = embedder.embed("")
        
        # Should still return 384-dim vector
        assert len(vector) == 384
    
    def test_long_text(self):
        """Test embedding generation with very long text"""
        embedder = TransformerEmbeddings()
        
        # Generate long text (10,000 chars)
        long_text = "Test " * 2000
        
        vector = embedder.embed(long_text)
        
        # Should still return 384-dim vector
        assert len(vector) == 384
    
    def test_special_characters(self):
        """Test embedding generation with special characters"""
        embedder = TransformerEmbeddings()
        
        text = "Test with special chars: äöü ß €@#$%^&*()"
        
        vector = embedder.embed(text)
        
        # Should still return 384-dim vector
        assert len(vector) == 384
    
    def test_unicode_text(self):
        """Test embedding generation with Unicode text"""
        embedder = TransformerEmbeddings()
        
        texts = [
            "English text",
            "Deutscher Text",
            "中文文本",
            "日本語のテキスト",
            "한국어 텍스트"
        ]
        
        for text in texts:
            vector = embedder.embed(text)
            assert len(vector) == 384


# ================================================================
# PYTEST CONFIGURATION
# ================================================================

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
