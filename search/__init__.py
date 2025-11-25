#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
__init__.py

__init__.py
UDS3 Search Module
High-level search APIs for Vector, Graph and Relational backends.

v1.6.0 Features:
- BM25 Keyword Search (PostgreSQL full-text)
- Reciprocal Rank Fusion (RRF) for hybrid search
- Enhanced result merging and scoring

Usage:
from uds3.search import UDS3SearchAPI, SearchQuery, SearchResult, SearchType, FusionMethod
# Option 1: Direct instantiation
search_api = UDS3SearchAPI(strategy)
results = await search_api.hybrid_search(query)
# Option 2: Via UnifiedDatabaseStrategy property (RECOMMENDED)
strategy = get_optimized_unified_strategy()
results = await strategy.search_api.hybrid_search(query)

# v1.6.0: RRF Hybrid Search
query = SearchQuery(
    query_text="§ 58 LBO Abstandsflächen",
    search_types=["vector", "graph", "keyword"],
    fusion_method="rrf"
)
results = await search_api.hybrid_search(query)

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

from search.search_api import (
    UDS3SearchAPI,
    SearchQuery,
    SearchResult,
    SearchType,
    FusionMethod,
)

__all__ = [
    "UDS3SearchAPI",
    "SearchQuery",
    "SearchResult",
    "SearchType",
    "FusionMethod",
]
