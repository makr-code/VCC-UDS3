#!/usr/bin/env python3
"""
UDS3 Search API - Backward Compatibility Wrapper

DEPRECATED: This import path is deprecated and will be removed in UDS3 v1.5.0 (~ 3 months).

OLD WAY (DEPRECATED):
    from uds3.uds3_search_api import UDS3SearchAPI
    search_api = UDS3SearchAPI(strategy)

NEW WAY (RECOMMENDED):
    from uds3 import get_optimized_unified_strategy
    strategy = get_optimized_unified_strategy()
    results = await strategy.search_api.hybrid_search(query)

ALTERNATIVE (if you need explicit import):
    from uds3.search import UDS3SearchAPI
    search_api = UDS3SearchAPI(strategy)

Migration Guide:
    See docs/UDS3_SEARCH_API_MIGRATION.md for complete migration instructions.
"""

import warnings
from search.search_api import (
    UDS3SearchAPI,
    SearchQuery,
    SearchResult,
    SearchType,
)

# Show deprecation warning
warnings.warn(
    "Importing from 'uds3.uds3_search_api' is deprecated. "
    "Use 'strategy.search_api' property instead: "
    "'strategy = get_optimized_unified_strategy(); results = await strategy.search_api.hybrid_search(query)' "
    "or import from 'uds3.search': 'from uds3.search import UDS3SearchAPI'. "
    "See docs/UDS3_SEARCH_API_MIGRATION.md for details. "
    "This compatibility wrapper will be removed in UDS3 v1.5.0 (~3 months).",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    "UDS3SearchAPI",
    "SearchQuery",
    "SearchResult",
    "SearchType",
]
