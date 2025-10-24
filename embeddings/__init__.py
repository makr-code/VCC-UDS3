#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
__init__.py

__init__.py
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
Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
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
