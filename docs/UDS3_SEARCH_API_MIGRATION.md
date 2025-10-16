# UDS3 Search API Migration Guide

**From Manual Instantiation to Property-Based Access**

This guide helps you migrate from the old manual `UDS3SearchAPI()` instantiation to the new property-based access pattern introduced in UDS3 v1.4.0.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Why Migrate?](#why-migrate)
3. [Migration Steps](#migration-steps)
4. [Code Examples](#code-examples)
5. [Backward Compatibility](#backward-compatibility)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## Overview

**UDS3 v1.4.0** introduces a new, cleaner way to access the Search API via the `strategy.search_api` property. This eliminates manual instantiation and provides better IDE support.

### What Changed?

| Aspect | v1.3.x (Old) | v1.4.0 (New) |
|--------|--------------|--------------|
| **Import** | `from uds3.uds3_search_api import UDS3SearchAPI` | `from uds3 import get_optimized_unified_strategy` |
| **Instantiation** | `search_api = UDS3SearchAPI(strategy)` | `search_api = strategy.search_api` |
| **Lines of Code** | 3 LOC | 2 LOC (-33%) |
| **Number of Imports** | 2 imports | 1 import (-50%) |
| **IDE Support** | Manual class lookup | Autocomplete property |

---

## Why Migrate?

### ✅ Benefits

1. **Cleaner Code:** Less boilerplate (-33% LOC)
2. **Better DX:** IDE autocomplete shows `search_api` property
3. **Consistency:** Matches other UDS3 APIs (`saga_crud`, `identity_service`)
4. **Lazy Loading:** Efficient resource management (loaded only when accessed)
5. **Future-Proof:** Aligns with UDS3 v2.0 RAG Framework vision

### 📊 Code Comparison

**Before (v1.3.x):**
```python
from uds3.uds3_search_api import UDS3SearchAPI
from uds3.uds3_core import get_optimized_unified_strategy

strategy = get_optimized_unified_strategy()
search_api = UDS3SearchAPI(strategy)  # Manual instantiation
results = await search_api.hybrid_search(query)
```

**After (v1.4.0):**
```python
from uds3 import get_optimized_unified_strategy

strategy = get_optimized_unified_strategy()
results = await strategy.search_api.hybrid_search(query)  # Property access ⭐
```

**Savings:** -1 import, -1 LOC, +IDE autocomplete

---

## Migration Steps

### Step 1: Update Imports

**Old:**
```python
from uds3.uds3_search_api import UDS3SearchAPI
from uds3.uds3_core import get_optimized_unified_strategy
```

**New:**
```python
from uds3 import get_optimized_unified_strategy
```

**Note:** If you need type hints, import from `uds3.search`:
```python
from uds3 import get_optimized_unified_strategy
from uds3.search import SearchQuery, SearchResult  # For type hints
```

### Step 2: Remove Manual Instantiation

**Old:**
```python
strategy = get_optimized_unified_strategy()
search_api = UDS3SearchAPI(strategy)  # ❌ Remove this line
```

**New:**
```python
strategy = get_optimized_unified_strategy()
# No instantiation needed - use property directly
```

### Step 3: Use Property Access

**Old:**
```python
results = await search_api.hybrid_search(query)
```

**New:**
```python
results = await strategy.search_api.hybrid_search(query)
```

---

## Code Examples

### Example 1: Simple Search

**Old (v1.3.x):**
```python
from uds3.uds3_search_api import UDS3SearchAPI
from uds3.uds3_core import get_optimized_unified_strategy

strategy = get_optimized_unified_strategy()
search_api = UDS3SearchAPI(strategy)

results = await search_api.graph_search("Photovoltaik", top_k=10)
```

**New (v1.4.0):**
```python
from uds3 import get_optimized_unified_strategy

strategy = get_optimized_unified_strategy()
results = await strategy.search_api.graph_search("Photovoltaik", top_k=10)
```

### Example 2: Hybrid Search

**Old (v1.3.x):**
```python
from uds3.uds3_search_api import UDS3SearchAPI, SearchQuery
from uds3.uds3_core import get_optimized_unified_strategy

strategy = get_optimized_unified_strategy()
search_api = UDS3SearchAPI(strategy)

query = SearchQuery(
    query_text="Was regelt § 58 LBO BW?",
    top_k=10,
    search_types=["vector", "graph"],
    weights={"vector": 0.5, "graph": 0.5}
)
results = await search_api.hybrid_search(query)
```

**New (v1.4.0):**
```python
from uds3 import get_optimized_unified_strategy
from uds3.search import SearchQuery

strategy = get_optimized_unified_strategy()

query = SearchQuery(
    query_text="Was regelt § 58 LBO BW?",
    top_k=10,
    search_types=["vector", "graph"],
    weights={"vector": 0.5, "graph": 0.5}
)
results = await strategy.search_api.hybrid_search(query)
```

### Example 3: VERITAS Agent

**Old (v1.3.x):**
```python
class UDS3HybridSearchAgent:
    def __init__(self, strategy):
        self.strategy = strategy
        self.search_api = UDS3SearchAPI(strategy)  # Manual
    
    async def search(self, query):
        return await self.search_api.hybrid_search(query)
```

**New (v1.4.0):**
```python
class UDS3HybridSearchAgent:
    def __init__(self, strategy):
        self.strategy = strategy
        self.search_api = strategy.search_api  # Property ⭐
    
    async def search(self, query):
        return await self.search_api.hybrid_search(query)
```

---

## Backward Compatibility

### Deprecation Timeline

| Version | Status | Action |
|---------|--------|--------|
| **v1.3.x** | Old API | Manual `UDS3SearchAPI()` instantiation |
| **v1.4.0** | Deprecation | Old API works with warning |
| **v1.5.0** | Removal | Old API removed (~3 months) |

### Deprecation Warning

If you use the old import in v1.4.0, you'll see:

```python
DeprecationWarning: Importing from 'uds3.uds3_search_api' is deprecated. 
Use 'strategy.search_api' property instead: 
'strategy = get_optimized_unified_strategy(); results = await strategy.search_api.hybrid_search(query)' 
or import from 'uds3.search': 'from uds3.search import UDS3SearchAPI'. 
This compatibility wrapper will be removed in UDS3 v1.5.0 (~3 months).
```

### Both Ways Work

During the deprecation period (v1.4.0), **both** ways work:

```python
# OLD (deprecated but working):
from uds3.uds3_search_api import UDS3SearchAPI
search_api = UDS3SearchAPI(strategy)  # Shows warning

# NEW (recommended):
search_api = strategy.search_api  # No warning
```

This gives you time to migrate gradually.

---

## Troubleshooting

### Issue 1: "AttributeError: 'UnifiedDatabaseStrategy' has no attribute 'search_api'"

**Cause:** Using UDS3 v1.3.x or older

**Solution:** Update to v1.4.0 or newer:
```bash
cd /path/to/uds3
git pull
pip install -e . --upgrade
```

### Issue 2: "ImportError: cannot import name 'UDS3SearchAPI' from 'uds3.search'"

**Cause:** Old UDS3 version or broken installation

**Solution:** 
```bash
# Reinstall UDS3
pip uninstall uds3
pip install -e /path/to/uds3
```

### Issue 3: Deprecation Warning Not Showing

**Cause:** Warnings filtered by Python

**Solution:** Enable warnings:
```python
import warnings
warnings.simplefilter('always', DeprecationWarning)
```

### Issue 4: "search_api is None"

**Cause:** Strategy not fully initialized

**Solution:** Ensure `_resolve_database_manager()` is called:
```python
strategy = get_optimized_unified_strategy()
_ = strategy._resolve_database_manager()  # Explicit init
search_api = strategy.search_api
```

---

## FAQ

### Q1: Do I have to migrate immediately?

**A:** No, the old API works in v1.4.0 with a deprecation warning. You have ~3 months before removal in v1.5.0.

### Q2: Will my old code break?

**A:** No, v1.4.0 is fully backward compatible. Your old code will work, but show a warning.

### Q3: What's the benefit of migrating?

**A:** Cleaner code (-33% LOC), better IDE support (autocomplete), and consistency with other UDS3 APIs.

### Q4: Can I use both ways in the same codebase?

**A:** Yes, during the deprecation period (v1.4.0). But we recommend migrating fully to avoid confusion.

### Q5: How do I know if I'm using the old or new API?

**Old API indicators:**
- Import from `uds3.uds3_search_api`
- Manual `UDS3SearchAPI(strategy)` instantiation
- Deprecation warning in logs

**New API indicators:**
- Import from `uds3` or `uds3.search`
- Property access: `strategy.search_api`
- No warnings

### Q6: What if I need explicit type hints?

**A:** Import types from `uds3.search`:
```python
from uds3 import get_optimized_unified_strategy
from uds3.search import SearchQuery, SearchResult

def my_search(strategy, query: str) -> list[SearchResult]:
    results = await strategy.search_api.hybrid_search(query)
    return results
```

### Q7: Does this change affect performance?

**A:** No, performance is identical. The property uses lazy loading, which may even improve initialization time.

### Q8: What happens to `UDS3SearchAPI` class?

**A:** The class still exists in `uds3.search.search_api`, but you don't instantiate it manually anymore. The property handles it.

---

## Next Steps

1. **Update your code** using the examples above
2. **Test thoroughly** to ensure no regressions
3. **Remove old imports** to avoid deprecation warnings
4. **Update documentation** in your project

---

## Support

- **Documentation:** [UDS3_SEARCH_API_PRODUCTION_GUIDE.md](UDS3_SEARCH_API_PRODUCTION_GUIDE.md)
- **Architecture Decision:** [UDS3_SEARCH_API_INTEGRATION_DECISION.md](UDS3_SEARCH_API_INTEGRATION_DECISION.md)
- **Issue Tracker:** [Internal Jira]
- **Team Contact:** UDS3 Development Team

---

**Happy Migrating! 🚀**
