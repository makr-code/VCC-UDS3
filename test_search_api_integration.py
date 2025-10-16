#!/usr/bin/env python3
"""
Test UDS3 Search API Integration in Core

Tests both old and new import methods to verify backward compatibility.
"""

import sys
import warnings

print("=" * 80)
print("UDS3 Search API Integration Test")
print("=" * 80)

# Test 1: Old import (should show deprecation warning)
print("\n1️⃣ Test OLD import (uds3.uds3_search_api):")
print("-" * 80)
try:
    # Capture deprecation warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from uds3.uds3_search_api import UDS3SearchAPI as OldSearchAPI
        
        if len(w) > 0:
            print(f"✅ Deprecation warning shown (expected):")
            print(f"   {w[0].message}")
        else:
            print("⚠️ No deprecation warning (unexpected)")
        
        print(f"✅ Old import successful: {OldSearchAPI}")
except Exception as e:
    print(f"❌ Old import failed: {e}")
    sys.exit(1)

# Test 2: New import from search module
print("\n2️⃣ Test NEW import (uds3.search):")
print("-" * 80)
try:
    from uds3.search import UDS3SearchAPI, SearchQuery, SearchResult, SearchType
    print(f"✅ New import successful:")
    print(f"   UDS3SearchAPI: {UDS3SearchAPI}")
    print(f"   SearchQuery: {SearchQuery}")
    print(f"   SearchResult: {SearchResult}")
    print(f"   SearchType: {SearchType}")
except Exception as e:
    print(f"❌ New import failed: {e}")
    sys.exit(1)

# Test 3: Import from top-level uds3 module
print("\n3️⃣ Test TOP-LEVEL import (uds3):")
print("-" * 80)
try:
    from uds3 import UDS3SearchAPI as TopLevelSearchAPI, SearchQuery as TopLevelQuery
    print(f"✅ Top-level import successful:")
    print(f"   UDS3SearchAPI: {TopLevelSearchAPI}")
    print(f"   SearchQuery: {TopLevelQuery}")
except Exception as e:
    print(f"❌ Top-level import failed: {e}")
    sys.exit(1)

# Test 4: Property access (this is the RECOMMENDED way)
print("\n4️⃣ Test PROPERTY access (strategy.search_api) - RECOMMENDED:")
print("-" * 80)
try:
    from uds3 import get_optimized_unified_strategy
    
    strategy = get_optimized_unified_strategy()
    print(f"✅ Strategy created: {strategy}")
    
    # Access search_api property (lazy-loaded)
    search_api = strategy.search_api
    print(f"✅ Search API property accessed: {search_api}")
    print(f"   Type: {type(search_api)}")
    print(f"   Has vector_search: {hasattr(search_api, 'vector_search')}")
    print(f"   Has graph_search: {hasattr(search_api, 'graph_search')}")
    print(f"   Has hybrid_search: {hasattr(search_api, 'hybrid_search')}")
except Exception as e:
    print(f"❌ Property access failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Verify both ways return same class
print("\n5️⃣ Test CLASS identity:")
print("-" * 80)
try:
    assert OldSearchAPI == TopLevelSearchAPI, "Old and top-level should be same class"
    assert type(search_api).__name__ == "UDS3SearchAPI", "Property should return UDS3SearchAPI"
    print(f"✅ All import methods return the same class")
except AssertionError as e:
    print(f"❌ Class identity check failed: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED!")
print("=" * 80)
print("\n📋 Summary:")
print("   ✅ Old import (uds3.uds3_search_api) - DEPRECATED but works")
print("   ✅ New import (uds3.search) - Works")
print("   ✅ Top-level import (uds3) - Works")
print("   ✅ Property access (strategy.search_api) - RECOMMENDED ⭐")
print("\n🎯 Recommended Usage:")
print("   from uds3 import get_optimized_unified_strategy")
print("   strategy = get_optimized_unified_strategy()")
print("   results = await strategy.search_api.hybrid_search(query)")
print("\n✅ Phase 2: UDS3 Core Integration COMPLETE!")
