#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reranker.py

UDS3 Cross-Encoder Reranking - Two-Stage Retrieval Enhancement
Provides Cross-Encoder based reranking for improved search relevance.

v1.6.0 Implementation:
- Cross-Encoder model for semantic reranking
- Support for German legal text (German BERT models)
- ONNX optimization for low-latency inference
- Configurable candidate count and batch processing

Two-Stage Retrieval Architecture:
1. Stage 1 (Bi-Encoder): Fast retrieval with BM25/Vector/Graph (top-k * multiplier)
2. Stage 2 (Cross-Encoder): Precise reranking of candidates (final top-k)

Models Supported:
- cross-encoder/ms-marco-MiniLM-L-6-v2 (English, fast)
- cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 (Multilingual)
- deutsche-telekom/gbert-large-paraphrase-euclidean (German)
- Custom fine-tuned models

Usage:
    from search.reranker import CrossEncoderReranker
    
    reranker = CrossEncoderReranker(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
    reranked = await reranker.rerank(query="§ 58 LBO", candidates=results, top_k=10)

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

import logging
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Import metrics if available
try:
    from core.metrics import metrics
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

# Check for sentence-transformers (Cross-Encoder support)
try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
    logger.info("✅ CrossEncoder (sentence-transformers) available")
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    logger.warning("⚠️ sentence-transformers not installed - CrossEncoder reranking disabled")

# Check for ONNX Runtime optimization
try:
    import onnxruntime
    ONNX_AVAILABLE = True
    logger.info("✅ ONNX Runtime available for optimized inference")
except ImportError:
    ONNX_AVAILABLE = False
    logger.debug("ONNX Runtime not available - using standard PyTorch inference")


# ============================================================================
# Reranker Configuration
# ============================================================================

@dataclass
class RerankerConfig:
    """
    Configuration for Cross-Encoder reranking
    
    Attributes:
        model_name: HuggingFace model name or path
        max_length: Maximum token length for model input
        batch_size: Batch size for inference
        use_onnx: Use ONNX Runtime for optimization
        device: Device for inference ('cpu', 'cuda', 'mps')
        score_threshold: Minimum score threshold for results
    """
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    max_length: int = 512
    batch_size: int = 32
    use_onnx: bool = False
    device: str = "cpu"
    score_threshold: float = 0.0
    
    # German-optimized models
    GERMAN_MODELS = [
        "deutsche-telekom/gbert-large-paraphrase-euclidean",
        "deepset/gbert-base-germandpr",
        "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",  # Multilingual
    ]
    
    # Fast models for low-latency requirements
    FAST_MODELS = [
        "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "cross-encoder/ms-marco-TinyBERT-L-2-v2",
    ]


# ============================================================================
# Abstract Reranker Interface
# ============================================================================

class BaseReranker(ABC):
    """Abstract base class for rerankers"""
    
    @abstractmethod
    async def rerank(
        self,
        query: str,
        candidates: List[Any],
        top_k: int = 10
    ) -> List[Any]:
        """
        Rerank candidates based on query relevance
        
        Args:
            query: Search query text
            candidates: List of candidate results (SearchResult or dict)
            top_k: Number of top results to return
            
        Returns:
            Reranked list of results
        """
        pass
    
    @abstractmethod
    def get_scores(
        self,
        query: str,
        documents: List[str]
    ) -> List[float]:
        """
        Get relevance scores for query-document pairs
        
        Args:
            query: Search query text
            documents: List of document texts
            
        Returns:
            List of relevance scores
        """
        pass


# ============================================================================
# Cross-Encoder Reranker Implementation
# ============================================================================

class CrossEncoderReranker(BaseReranker):
    """
    Cross-Encoder based reranker using sentence-transformers
    
    Two-stage retrieval:
    1. Fast first-stage retrieval (BM25/Vector) returns top-k * multiplier candidates
    2. Cross-Encoder reranks candidates for precise relevance ordering
    
    Benefits:
    - More accurate relevance scoring than bi-encoders
    - Handles semantic nuances in legal text
    - Can capture query-document interactions
    
    Trade-offs:
    - Higher latency than bi-encoders (O(n) vs O(1) per candidate)
    - Best used with limited candidate set (50-200 documents)
    """
    
    def __init__(
        self,
        config: Optional[RerankerConfig] = None,
        model_name: Optional[str] = None
    ):
        """
        Initialize Cross-Encoder reranker
        
        Args:
            config: RerankerConfig instance
            model_name: Override model name (shortcut for config.model_name)
        """
        self.config = config or RerankerConfig()
        if model_name:
            self.config.model_name = model_name
        
        self.model = None
        self._initialized = False
        
        if CROSS_ENCODER_AVAILABLE:
            self._load_model()
        else:
            logger.warning("CrossEncoder not available - reranking will be skipped")
    
    def _load_model(self):
        """Load the Cross-Encoder model"""
        try:
            start_time = time.time()
            
            self.model = CrossEncoder(
                self.config.model_name,
                max_length=self.config.max_length,
                device=self.config.device
            )
            
            load_time = time.time() - start_time
            self._initialized = True
            
            logger.info(
                f"✅ CrossEncoder loaded: {self.config.model_name} "
                f"(device={self.config.device}, time={load_time:.2f}s)"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to load CrossEncoder model: {e}")
            self._initialized = False
    
    def is_available(self) -> bool:
        """Check if reranker is available and initialized"""
        return CROSS_ENCODER_AVAILABLE and self._initialized
    
    def get_scores(
        self,
        query: str,
        documents: List[str]
    ) -> List[float]:
        """
        Get relevance scores for query-document pairs
        
        Uses Cross-Encoder to compute semantic similarity scores.
        Processes in batches for efficiency.
        
        Args:
            query: Search query text
            documents: List of document texts
            
        Returns:
            List of relevance scores (higher = more relevant)
        """
        if not self.is_available():
            logger.warning("CrossEncoder not available - returning uniform scores")
            return [0.5] * len(documents)
        
        if not documents:
            return []
        
        try:
            start_time = time.time()
            
            # Create query-document pairs
            pairs = [[query, doc] for doc in documents]
            
            # Get scores from Cross-Encoder
            scores = self.model.predict(
                pairs,
                batch_size=self.config.batch_size,
                show_progress_bar=False
            )
            
            # Convert numpy array to list if needed
            if hasattr(scores, 'tolist'):
                scores = scores.tolist()
            
            inference_time = time.time() - start_time
            
            # Track metrics
            if METRICS_AVAILABLE:
                metrics.search_latency.labels(
                    search_type="rerank",
                    fusion_method="cross_encoder"
                ).observe(inference_time)
            
            logger.debug(
                f"CrossEncoder scoring: {len(documents)} docs in {inference_time:.3f}s "
                f"({len(documents)/inference_time:.1f} docs/s)"
            )
            
            return scores
            
        except Exception as e:
            logger.error(f"❌ CrossEncoder scoring failed: {e}")
            return [0.5] * len(documents)
    
    async def rerank(
        self,
        query: str,
        candidates: List[Any],
        top_k: int = 10,
        content_field: str = "content"
    ) -> List[Any]:
        """
        Rerank candidates using Cross-Encoder
        
        Args:
            query: Search query text
            candidates: List of SearchResult objects or dicts
            top_k: Number of top results to return
            content_field: Field name containing document text
            
        Returns:
            Reranked list of candidates (top_k)
        """
        if not self.is_available():
            logger.warning("CrossEncoder not available - returning original order")
            return candidates[:top_k]
        
        if not candidates:
            return []
        
        try:
            start_time = time.time()
            
            # Extract document texts from candidates
            documents = []
            for candidate in candidates:
                if hasattr(candidate, content_field):
                    text = getattr(candidate, content_field)
                elif isinstance(candidate, dict):
                    text = candidate.get(content_field, "")
                else:
                    text = str(candidate)
                
                # Truncate very long documents
                if len(text) > 2000:
                    text = text[:2000] + "..."
                
                documents.append(text)
            
            # Get Cross-Encoder scores
            scores = self.get_scores(query, documents)
            
            # Pair candidates with scores
            scored_candidates = list(zip(candidates, scores))
            
            # Sort by score (descending)
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            
            # Apply score threshold
            if self.config.score_threshold > 0:
                scored_candidates = [
                    (c, s) for c, s in scored_candidates 
                    if s >= self.config.score_threshold
                ]
            
            # Extract reranked candidates
            reranked = [c for c, s in scored_candidates[:top_k]]
            
            # Update scores in results
            for i, (candidate, score) in enumerate(scored_candidates[:top_k]):
                if hasattr(candidate, 'score'):
                    candidate.score = float(score)
                elif isinstance(candidate, dict):
                    candidate['rerank_score'] = float(score)
            
            rerank_time = time.time() - start_time
            
            # Track metrics
            if METRICS_AVAILABLE:
                metrics.search_requests.labels(
                    search_type="rerank",
                    status="success",
                    fusion_method="cross_encoder"
                ).inc()
            
            logger.info(
                f"✅ CrossEncoder reranking: {len(candidates)} → {len(reranked)} "
                f"in {rerank_time:.3f}s"
            )
            
            return reranked
            
        except Exception as e:
            logger.error(f"❌ CrossEncoder reranking failed: {e}")
            if METRICS_AVAILABLE:
                metrics.search_errors.labels(
                    search_type="rerank",
                    error_type=type(e).__name__
                ).inc()
            return candidates[:top_k]


# ============================================================================
# No-Op Reranker (Fallback)
# ============================================================================

class NoOpReranker(BaseReranker):
    """
    No-operation reranker - returns candidates unchanged
    
    Used when Cross-Encoder is not available or disabled.
    """
    
    async def rerank(
        self,
        query: str,
        candidates: List[Any],
        top_k: int = 10
    ) -> List[Any]:
        """Return candidates unchanged (no reranking)"""
        logger.debug("NoOpReranker: returning original order")
        return candidates[:top_k]
    
    def get_scores(
        self,
        query: str,
        documents: List[str]
    ) -> List[float]:
        """Return uniform scores"""
        return [0.5] * len(documents)


# ============================================================================
# Factory Functions
# ============================================================================

def create_reranker(
    model_name: Optional[str] = None,
    config: Optional[RerankerConfig] = None,
    fallback_to_noop: bool = True
) -> BaseReranker:
    """
    Factory function to create appropriate reranker
    
    Args:
        model_name: HuggingFace model name
        config: RerankerConfig instance
        fallback_to_noop: Return NoOpReranker if CrossEncoder unavailable
        
    Returns:
        BaseReranker instance (CrossEncoderReranker or NoOpReranker)
    """
    if CROSS_ENCODER_AVAILABLE:
        return CrossEncoderReranker(config=config, model_name=model_name)
    elif fallback_to_noop:
        logger.warning("CrossEncoder not available - using NoOpReranker")
        return NoOpReranker()
    else:
        raise RuntimeError("CrossEncoder not available and fallback disabled")


def get_german_reranker() -> BaseReranker:
    """
    Get reranker optimized for German legal text
    
    Returns:
        CrossEncoderReranker with German model or NoOpReranker
    """
    config = RerankerConfig(
        model_name="cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",  # Multilingual
        max_length=512,
        batch_size=16
    )
    return create_reranker(config=config)


def get_fast_reranker() -> BaseReranker:
    """
    Get fast reranker for low-latency requirements
    
    Returns:
        CrossEncoderReranker with fast model or NoOpReranker
    """
    config = RerankerConfig(
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        max_length=256,
        batch_size=64
    )
    return create_reranker(config=config)


# ============================================================================
# Utility Functions
# ============================================================================

def check_reranker_available() -> bool:
    """Check if Cross-Encoder reranking is available"""
    return CROSS_ENCODER_AVAILABLE


def list_available_models() -> List[str]:
    """List recommended Cross-Encoder models"""
    return [
        # Fast models
        "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "cross-encoder/ms-marco-TinyBERT-L-2-v2",
        # Multilingual
        "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        # German
        "deutsche-telekom/gbert-large-paraphrase-euclidean",
        "deepset/gbert-base-germandpr",
    ]


# ============================================================================
# Module Test
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    print(f"Cross-Encoder available: {CROSS_ENCODER_AVAILABLE}")
    print(f"ONNX Runtime available: {ONNX_AVAILABLE}")
    print(f"Available models: {list_available_models()}")
    
    if CROSS_ENCODER_AVAILABLE:
        # Test reranking
        async def test_rerank():
            reranker = create_reranker()
            
            # Mock candidates
            candidates = [
                {"content": "§ 58 LBO regelt die Abstandsflächen in Baden-Württemberg.", "id": "1"},
                {"content": "Das Baurecht in Deutschland ist Ländersache.", "id": "2"},
                {"content": "Abstandsflächen dienen dem Brandschutz und der Belichtung.", "id": "3"},
            ]
            
            query = "Was sind Abstandsflächen nach § 58 LBO?"
            
            reranked = await reranker.rerank(
                query=query,
                candidates=candidates,
                top_k=3,
                content_field="content"
            )
            
            print(f"\nQuery: {query}")
            print(f"Reranked results:")
            for i, r in enumerate(reranked):
                print(f"  {i+1}. {r.get('content', '')[:50]}... (score: {r.get('rerank_score', 'N/A')})")
        
        asyncio.run(test_rerank())
