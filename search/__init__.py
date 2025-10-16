#!/usr/bin/env python3
"""
UDS3 Search Module

High-level search APIs for Vector, Graph and Relational backends.

Usage:
    from uds3.search import UDS3SearchAPI, SearchQuery, SearchResult, SearchType
    
    # Option 1: Direct instantiation
    search_api = UDS3SearchAPI(strategy)
    results = await search_api.hybrid_search(query)
    
    # Option 2: Via UnifiedDatabaseStrategy property (RECOMMENDED)
    strategy = get_optimized_unified_strategy()
    results = await strategy.search_api.hybrid_search(query)
"""

from search.search_api import (
    UDS3SearchAPI,
    SearchQuery,
    SearchResult,
    SearchType,
)

__all__ = [
    "UDS3SearchAPI",
    "SearchQuery",
    "SearchResult",
    "SearchType",
]
