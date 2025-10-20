#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transformer-Based Embeddings for UDS3
======================================

Provides real semantic embeddings using sentence-transformers.

Features:
- sentence-transformers integration (384-dim multilingual)
- Lazy loading (model loaded only when needed)
- Thread-safe initialization with double-check locking
- GPU acceleration with automatic CUDA detection
- Fallback to hash-based vectors on error
- Configurable model selection via ENV

Default Model: all-MiniLM-L6-v2
- Dimensions: 384
- Languages: Multilingual (Deutsch, Englisch, 50+ languages)
- Speed: ~40ms per chunk (CPU), ~10ms (GPU)
- Quality: High semantic similarity accuracy

Author: UDS3 Framework
Date: Oktober 2025
Version: 2.1.0
"""

import os
import logging
import threading
import hashlib
from typing import List, Union, Optional
import numpy as np

logger = logging.getLogger(__name__)

# ================================================================
# HELPER FUNCTIONS
# ================================================================

def _cuda_available() -> bool:
    """Check if CUDA is available for GPU acceleration"""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


# ================================================================
# ENVIRONMENT CONFIGURATION
# ================================================================

# Enable/Disable Real Embeddings
ENABLE_REAL_EMBEDDINGS = os.getenv("ENABLE_REAL_EMBEDDINGS", "true").lower() == "true"

# Model Configuration
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cuda" if _cuda_available() else "cpu")

logger.info(f"[CONFIG] Real Embeddings: {'ENABLED' if ENABLE_REAL_EMBEDDINGS else 'DISABLED'}")
logger.info(f"[CONFIG] Model: {EMBEDDING_MODEL_NAME} (device: {EMBEDDING_DEVICE})")


# ================================================================
# GLOBAL MODEL INSTANCE (LAZY LOADING)
# ================================================================

_EMBEDDING_MODEL = None
_EMBEDDING_MODEL_LOCK = threading.Lock()


def load_embedding_model(model_name: Optional[str] = None, device: Optional[str] = None):
    """
    Thread-safe lazy loading of embedding model
    
    Uses double-check locking pattern for performance:
    1. Fast path: Return immediately if already loaded (no lock)
    2. Slow path: Acquire lock and load model (thread-safe)
    3. Double-check: Verify another thread didn't load while waiting
    
    Args:
        model_name: Model identifier (default: ENV EMBEDDING_MODEL_NAME)
        device: Device to use ('cpu' or 'cuda', default: auto-detect)
    
    Returns:
        SentenceTransformer model or "FALLBACK" string on error
    """
    global _EMBEDDING_MODEL
    
    # Fast path: Model already loaded (no lock needed)
    if _EMBEDDING_MODEL is not None:
        return _EMBEDDING_MODEL
    
    # Slow path: Need to load model (acquire lock)
    with _EMBEDDING_MODEL_LOCK:
        # Double-check: Another thread might have loaded it while we waited
        if _EMBEDDING_MODEL is not None:
            return _EMBEDDING_MODEL
        
        # Use provided args or fall back to ENV/defaults
        model_name = model_name or EMBEDDING_MODEL_NAME
        device = device or EMBEDDING_DEVICE
        
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"[LOADING] Embedding model: {model_name} (device: {device})...")
            print(f"\n[UDS3] [EMBEDDINGS] Loading {model_name}...\n", flush=True)
            
            # Load model with device specification
            _EMBEDDING_MODEL = SentenceTransformer(model_name, device=device)
            
            logger.info(f"[SUCCESS] Embedding model loaded: {model_name} (384-dim)")
            print(f"\n[UDS3] [EMBEDDINGS] Loaded successfully! (384-dim, {device})\n", flush=True)
            
        except ImportError:
            logger.warning("[WARNING] sentence-transformers not installed - using hash-based fallback")
            print("\n[UDS3] [EMBEDDINGS] WARNING: sentence-transformers not found, using fallback\n", flush=True)
            _EMBEDDING_MODEL = "FALLBACK"
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to load embedding model: {e}")
            print(f"\n[UDS3] [EMBEDDINGS] ERROR: Loading failed: {e}\n", flush=True)
            _EMBEDDING_MODEL = "FALLBACK"
    
    return _EMBEDDING_MODEL


def _hash_based_fallback(text: str, dimensions: int = 384) -> List[float]:
    """
    Hash-based fallback embedding (NO semantic meaning)
    
    Used when sentence-transformers is not available.
    Generates deterministic pseudo-random vector from text hash.
    
    ⚠️ WARNING: These embeddings have NO semantic similarity!
    
    Args:
        text: Input text
        dimensions: Vector dimensions (default: 384 to match all-MiniLM-L6-v2)
    
    Returns:
        List of floats (normalized to [0, 1])
    """
    text_hash = hashlib.md5(text.encode()).hexdigest()
    
    # Generate vector from hash (deterministic, but no semantic meaning)
    vector = []
    hash_len = len(text_hash)
    for i in range(0, dimensions * 2, 2):
        # Wrap around hash if needed
        idx = i % hash_len
        hex_pair = text_hash[idx:idx+2] if idx+1 < hash_len else text_hash[idx] + text_hash[0]
        value = float(int(hex_pair, 16)) / 255.0
        vector.append(value)
    
    return vector[:dimensions]


# ================================================================
# TRANSFORMER EMBEDDINGS CLASS
# ================================================================

class TransformerEmbeddings:
    """
    Transformer-based embedding generator
    
    Provides real semantic embeddings using sentence-transformers.
    Supports batch processing, GPU acceleration, and fallback mode.
    
    Usage:
        embedder = TransformerEmbeddings()
        vector = embedder.embed("Hello world")
        vectors = embedder.embed_batch(["Text 1", "Text 2", "Text 3"])
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        enable_fallback: bool = True
    ):
        """
        Initialize transformer embeddings
        
        Args:
            model_name: Model identifier (default: ENV EMBEDDING_MODEL_NAME)
            device: Device to use ('cpu' or 'cuda', default: auto-detect)
            enable_fallback: Enable hash-based fallback on error (default: True)
        """
        self.model_name = model_name or EMBEDDING_MODEL_NAME
        self.device = device or EMBEDDING_DEVICE
        self.enable_fallback = enable_fallback
        self.dimensions = 384  # all-MiniLM-L6-v2 dimensions
        
        # Lazy load model (only loaded when first embedding is generated)
        self._model = None
        
        logger.debug(f"[INIT] TransformerEmbeddings created (model: {self.model_name}, device: {self.device})")
    
    def _get_model(self):
        """Get or load embedding model (lazy loading)"""
        if self._model is None:
            self._model = load_embedding_model(self.model_name, self.device)
        return self._model
    
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for single text
        
        Args:
            text: Input text
        
        Returns:
            List of floats (384-dim vector)
        """
        model = self._get_model()
        
        # Check if fallback mode
        if model == "FALLBACK":
            if self.enable_fallback:
                logger.debug(f"[FALLBACK] Using hash-based embedding for text: {text[:50]}...")
                return _hash_based_fallback(text, self.dimensions)
            else:
                raise RuntimeError("Embedding model not available and fallback disabled")
        
        # Generate real embedding
        try:
            vector = model.encode(text, convert_to_numpy=True).tolist()
            return vector
        except Exception as e:
            logger.error(f"[ERROR] Embedding generation failed: {e}")
            
            if self.enable_fallback:
                logger.warning("[FALLBACK] Using hash-based embedding due to error")
                return _hash_based_fallback(text, self.dimensions)
            else:
                raise
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing)
        
        Batch processing is ~2-5x faster than sequential embedding.
        
        Args:
            texts: List of input texts
        
        Returns:
            List of vectors (each 384-dim)
        """
        model = self._get_model()
        
        # Check if fallback mode
        if model == "FALLBACK":
            if self.enable_fallback:
                logger.debug(f"[FALLBACK] Using hash-based embeddings for {len(texts)} texts")
                return [_hash_based_fallback(text, self.dimensions) for text in texts]
            else:
                raise RuntimeError("Embedding model not available and fallback disabled")
        
        # Generate real embeddings (batch)
        try:
            vectors = model.encode(texts, convert_to_numpy=True).tolist()
            return vectors
        except Exception as e:
            logger.error(f"[ERROR] Batch embedding generation failed: {e}")
            
            if self.enable_fallback:
                logger.warning("[FALLBACK] Using hash-based embeddings due to error")
                return [_hash_based_fallback(text, self.dimensions) for text in texts]
            else:
                raise
    
    def is_fallback_mode(self) -> bool:
        """Check if embedder is in fallback mode (hash-based)"""
        model = self._get_model()
        return model == "FALLBACK"
    
    def get_dimensions(self) -> int:
        """Get embedding dimensions"""
        return self.dimensions


# ================================================================
# CONVENIENCE FUNCTIONS
# ================================================================

# Global default embedder (lazy initialized)
_DEFAULT_EMBEDDER = None


def get_default_embeddings() -> TransformerEmbeddings:
    """
    Get default transformer embeddings instance (singleton)
    
    Returns:
        TransformerEmbeddings instance
    """
    global _DEFAULT_EMBEDDER
    
    if _DEFAULT_EMBEDDER is None:
        _DEFAULT_EMBEDDER = TransformerEmbeddings()
    
    return _DEFAULT_EMBEDDER


# ================================================================
# MAIN (TESTING)
# ================================================================

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("UDS3 Transformer Embeddings - Test")
    print("="*60 + "\n")
    
    # Test single embedding
    embedder = TransformerEmbeddings()
    
    text = "Hello world, this is a test"
    print(f"Input: {text}")
    
    vector = embedder.embed(text)
    print(f"Output: {len(vector)}-dim vector")
    print(f"First 5 values: {vector[:5]}")
    print(f"Fallback mode: {embedder.is_fallback_mode()}")
    
    # Test batch embedding
    texts = [
        "First document",
        "Second document",
        "Third document"
    ]
    print(f"\nBatch input: {len(texts)} texts")
    
    vectors = embedder.embed_batch(texts)
    print(f"Batch output: {len(vectors)} vectors")
    print(f"Each vector: {len(vectors[0])}-dim")
    
    print("\n" + "="*60)
    print("Test complete!")
    print("="*60 + "\n")
