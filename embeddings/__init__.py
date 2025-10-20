#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UDS3 Embeddings Module
======================

Provides embedding generation for semantic search and vector databases.

Features:
- Transformer-based embeddings (sentence-transformers)
- GPU acceleration (CUDA support)
- Lazy loading (model loaded only when needed)
- Thread-safe initialization
- Fallback to hash-based vectors

Author: UDS3 Framework
Date: Oktober 2025
Version: 2.1.0
"""

from uds3.embeddings.transformer_embeddings import (
    TransformerEmbeddings,
    get_default_embeddings,
    load_embedding_model
)

__all__ = [
    'TransformerEmbeddings',
    'get_default_embeddings',
    'load_embedding_model'
]
