# UDS3 Transformer Embeddings

**Version:** 2.1.0  
**Erstellt:** 20. Oktober 2025  
**Status:** ✅ Production Ready

---

## 📋 Overview

UDS3 v2.1.0 introduces **real semantic embeddings** using `sentence-transformers`. This replaces hash-based fake vectors with true semantic representations for ChromaDB vector storage.

**Key Features:**
- ✅ **Real Semantic Embeddings** (384-dim, multilingual)
- ✅ **Lazy Loading** (model loaded only when needed)
- ✅ **Thread-Safe** (double-check locking pattern)
- ✅ **GPU Acceleration** (CUDA auto-detect)
- ✅ **Fallback Mode** (hash-based vectors if model fails)
- ✅ **Batch Processing** (2-5x faster than sequential)
- ✅ **ENV Configuration** (model selection, device control)

---

## 🚀 Quick Start

### Basic Usage

```python
from uds3.embeddings import TransformerEmbeddings

# Create embedder (lazy loading)
embedder = TransformerEmbeddings()

# Generate single embedding
text = "This is a legal contract for software development."
vector = embedder.embed(text)  # Returns List[float] (384-dim)

# Batch processing (2-5x faster)
texts = ["Contract text 1", "Contract text 2", "Contract text 3"]
vectors = embedder.embed_batch(texts)  # Returns List[List[float]]

# Check dimensions
dims = embedder.get_dimensions()  # Returns 384

# Check fallback mode
if embedder.is_fallback_mode():
    print("⚠️ Using hash-based fallback")
```

### Singleton Pattern

```python
from uds3.embeddings import get_default_embeddings

# Get global singleton instance
embedder = get_default_embeddings()
vector = embedder.embed("Some text")
```

### ChromaDB Integration

```python
from uds3.database.database_api_chromadb_remote import ChromaRemoteVectorBackend

# ChromaDB backend with auto-embedding
chromadb = ChromaRemoteVectorBackend(config)

# Add vector WITH auto-embedding from text
chromadb.add_vector(
    vector=None,  # Will be generated from text!
    metadata={"doc_id": "123", "chunk_index": 0},
    doc_id="chunk_123_0",
    text="Legal contract text..."  # ← Auto-embedded!
)

# Or provide pre-computed vector (backward compatible)
chromadb.add_vector(
    vector=[0.1, 0.2, ...],  # Pre-computed
    metadata={"doc_id": "123"},
    doc_id="chunk_123_0"
)
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Enable/Disable Real Embeddings (default: true)
ENABLE_REAL_EMBEDDINGS=true

# Model Selection (default: all-MiniLM-L6-v2)
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
# Alternatives:
# - all-mpnet-base-v2 (768-dim, higher quality, slower)
# - paraphrase-multilingual-MiniLM-L12-v2 (384-dim, better multilingual)
# - distilbert-base-nli-mean-tokens (768-dim, fast)

# Device Selection (default: auto-detect)
EMBEDDING_DEVICE=auto
# Options: auto, cuda, cpu
# auto → uses CUDA if available, else CPU
```

### Configuration in Code

```python
import os

# Disable real embeddings (use hash fallback)
os.environ['ENABLE_REAL_EMBEDDINGS'] = 'false'

# Force CPU (even if CUDA available)
os.environ['EMBEDDING_DEVICE'] = 'cpu'

# Use different model
os.environ['EMBEDDING_MODEL_NAME'] = 'all-mpnet-base-v2'

from uds3.embeddings import TransformerEmbeddings
embedder = TransformerEmbeddings()  # Will use ENV config
```

---

## 📊 Performance

### Benchmarks (Intel i7, 16GB RAM)

**Single Embedding:**
```
CPU (all-MiniLM-L6-v2):    ~40ms per text
GPU (CUDA):                ~10ms per text
Hash Fallback:             ~1ms per text
```

**Batch Embedding (10 texts):**
```
Sequential CPU:  ~400ms  (10x ~40ms)
Batch CPU:       ~160ms  (2.5x speedup)
Batch GPU:       ~50ms   (8x speedup)
```

**Model Loading (First Use):**
```
all-MiniLM-L6-v2:          ~2.2s (one-time, lazy)
all-mpnet-base-v2:         ~5.0s (one-time, lazy)
```

### Memory Usage

```
Model in RAM (CPU):        ~90MB
Model in VRAM (GPU):       ~120MB
Per 384-dim vector:        ~1.5KB (float32)
```

---

## 🧪 Testing

### Run All Tests

```bash
cd /path/to/uds3
python -m pytest tests/test_transformer_embeddings.py -v
```

**Expected Output:**
```
tests/test_transformer_embeddings.py::TestTransformerEmbeddings::test_lazy_loading PASSED
tests/test_transformer_embeddings.py::TestTransformerEmbeddings::test_thread_safe_loading PASSED
... (17 tests total)
============================= 17 passed in 10.08s =============================
```

### Test Coverage

**17 Test Cases (100% PASS):**
- ✅ Lazy loading (model not loaded until first use)
- ✅ Thread-safe initialization (10 concurrent threads)
- ✅ 384-dim vector generation
- ✅ Deterministic embeddings (same text → same vector)
- ✅ Different texts → different vectors
- ✅ Batch embedding (3 documents)
- ✅ Batch performance (1.5x faster)
- ✅ Fallback mode detection
- ✅ Hash-based fallback (384-dim normalized [0,1])
- ✅ get_dimensions() returns 384
- ✅ Semantic similarity (cat/mat > cat/python)
- ✅ Singleton pattern
- ✅ Empty text handling
- ✅ Long text handling (10,000 chars)
- ✅ Special characters (äöü ß €@#$%)
- ✅ Unicode support (English, Deutsch, 中文, 日本語, 한국어)

---

## 🔍 API Reference

### TransformerEmbeddings Class

```python
class TransformerEmbeddings:
    """
    Sentence Transformer embeddings with lazy loading and fallback
    
    Features:
    - Lazy loading (model loaded on first use)
    - Thread-safe initialization
    - GPU acceleration (CUDA auto-detect)
    - Fallback to hash-based vectors on error
    - Batch processing support
    
    Examples:
        >>> embedder = TransformerEmbeddings()
        >>> vector = embedder.embed("Some text")
        >>> len(vector)
        384
    """
    
    def __init__(
        self,
        model_name: str = None,
        device: str = None
    ):
        """
        Initialize embedder (model NOT loaded yet - lazy!)
        
        Args:
            model_name: Model name (default: from ENV or all-MiniLM-L6-v2)
            device: Device to use (default: from ENV or auto-detect)
        """
    
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for single text
        
        Args:
            text: Input text (any length)
        
        Returns:
            384-dim vector (List[float])
            
        Note:
            First call loads model (lazy loading, ~2s overhead)
            Subsequent calls are fast (~40ms CPU, ~10ms GPU)
        """
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (faster!)
        
        Args:
            texts: List of input texts
        
        Returns:
            List of 384-dim vectors
            
        Performance:
            2-5x faster than sequential embed() calls
            Recommended for >3 texts
        """
    
    def get_dimensions(self) -> int:
        """
        Get embedding dimensions
        
        Returns:
            384 (for all-MiniLM-L6-v2)
            768 (for all-mpnet-base-v2)
        """
    
    def is_fallback_mode(self) -> bool:
        """
        Check if using hash-based fallback
        
        Returns:
            True if fallback active (no semantic meaning!)
            False if using real model
        """
```

### Helper Functions

```python
def load_embedding_model(
    model_name: str = None,
    device: str = None
) -> Optional[SentenceTransformer]:
    """
    Load sentence transformer model (thread-safe)
    
    Args:
        model_name: Model name (default: all-MiniLM-L6-v2)
        device: Device (default: auto-detect CUDA)
    
    Returns:
        SentenceTransformer instance or None on error
        
    Note:
        Uses double-check locking for thread safety
        First call downloads model (~90MB)
        Subsequent calls load from cache
    """

def get_default_embeddings() -> TransformerEmbeddings:
    """
    Get global singleton embedder
    
    Returns:
        TransformerEmbeddings instance (shared across app)
        
    Use Case:
        When multiple components need same embedder
        Avoids loading model multiple times
    """
```

---

## 🛠️ Advanced Usage

### Custom Model

```python
from uds3.embeddings import TransformerEmbeddings

# Use larger, more accurate model (768-dim)
embedder = TransformerEmbeddings(
    model_name="all-mpnet-base-v2",
    device="cuda"  # Force GPU
)

vector = embedder.embed("Legal text")
print(len(vector))  # 768 (not 384!)
```

### Fallback Detection

```python
from uds3.embeddings import TransformerEmbeddings

embedder = TransformerEmbeddings()
vector = embedder.embed("Some text")

if embedder.is_fallback_mode():
    print("⚠️ WARNING: Using hash-based fallback!")
    print("→ No semantic similarity search possible")
    print("→ Check logs for model loading error")
else:
    print("✅ Using real semantic embeddings")
```

### Semantic Similarity

```python
from uds3.embeddings import TransformerEmbeddings
import numpy as np

embedder = TransformerEmbeddings()

# Compare two texts
text1 = "The cat sat on the mat"
text2 = "A feline rested on the rug"
text3 = "Python is a programming language"

v1 = embedder.embed(text1)
v2 = embedder.embed(text2)
v3 = embedder.embed(text3)

# Cosine similarity
def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

print(f"cat/mat vs feline/rug: {cosine_sim(v1, v2):.3f}")  # ~0.85 (high!)
print(f"cat/mat vs Python:     {cosine_sim(v1, v3):.3f}")  # ~0.15 (low)
```

### Batch Processing Best Practices

```python
from uds3.embeddings import TransformerEmbeddings

embedder = TransformerEmbeddings()

# ✅ GOOD: Batch processing for multiple texts
chunks = ["chunk1", "chunk2", "chunk3", ...]  # 100 chunks
vectors = embedder.embed_batch(chunks)  # ~2s (CPU)

# ❌ BAD: Sequential processing
vectors = []
for chunk in chunks:
    vectors.append(embedder.embed(chunk))  # ~4s (CPU) - 2x slower!
```

---

## 🔒 Thread Safety

**TransformerEmbeddings is fully thread-safe:**

```python
from uds3.embeddings import get_default_embeddings
from concurrent.futures import ThreadPoolExecutor

# Shared embedder across threads
embedder = get_default_embeddings()

def process_document(doc_text):
    return embedder.embed(doc_text)

# Parallel processing (safe!)
with ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(process_document, document_list)
```

**Locking Strategy:**
- Model loading uses double-check locking
- embed() is thread-safe (no shared state)
- embed_batch() is thread-safe

---

## ⚠️ Troubleshooting

### Model Download Fails

**Problem:** First run fails with network error

**Solution:**
```bash
# Pre-download model manually
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
"
```

### CUDA Out of Memory

**Problem:** GPU runs out of memory with large batches

**Solution:**
```python
# Reduce batch size or force CPU
os.environ['EMBEDDING_DEVICE'] = 'cpu'
```

### Fallback Mode Always Active

**Problem:** `is_fallback_mode()` always returns True

**Check:**
```python
# 1. Check if sentence-transformers installed
pip list | grep sentence-transformers

# 2. Check ENV variable
print(os.getenv('ENABLE_REAL_EMBEDDINGS'))  # Should be 'true'

# 3. Check logs for error
# Look for: "⚠️ sentence-transformers not available"
```

### Poor Semantic Search Quality

**Problem:** Similar texts get low similarity scores

**Check:**
1. Verify NOT in fallback mode: `embedder.is_fallback_mode()` → False
2. Try larger model: `all-mpnet-base-v2` (better quality)
3. Check language: Use multilingual model for non-English texts

---

## 📝 Migration Guide (from Hash-Based)

### Before (Hash-Based Fake Vectors)

```python
# OLD: ingestion_backend.py
chunk_hash = hashlib.md5(chunk.encode()).hexdigest()
fake_vector = [float(int(chunk_hash[i:i+2], 16)) / 255.0 
               for i in range(0, 384*2, 2)]
# → No semantic meaning!
```

### After (Real Embeddings)

```python
# NEW: Using UDS3 embeddings
from uds3.embeddings import get_default_embeddings

embedder = get_default_embeddings()
real_vector = embedder.embed(chunk)  # ✅ Real semantic meaning!
```

### ChromaDB Backend Update

```python
# Automatic embedding generation
chromadb.add_vector(
    vector=None,  # Don't provide vector
    metadata=metadata,
    doc_id=chunk_id,
    text=chunk_text  # Provide text instead!
)
# → Backend generates embedding automatically
```

---

## 🎯 Best Practices

1. **Use Singleton for Multiple Components:**
   ```python
   from uds3.embeddings import get_default_embeddings
   embedder = get_default_embeddings()  # Shared instance
   ```

2. **Batch Process When Possible:**
   ```python
   # ✅ Batch (2-5x faster)
   vectors = embedder.embed_batch(texts)
   
   # ❌ Sequential (slower)
   vectors = [embedder.embed(t) for t in texts]
   ```

3. **Check Fallback Mode in Production:**
   ```python
   if embedder.is_fallback_mode():
       logger.error("❌ CRITICAL: Semantic search unavailable!")
   ```

4. **GPU for High Throughput:**
   ```bash
   export EMBEDDING_DEVICE=cuda  # If CUDA available
   ```

5. **Monitor Model Loading:**
   ```python
   import time
   start = time.time()
   vector = embedder.embed("first text")  # Triggers lazy load
   print(f"Model loaded in {time.time() - start:.2f}s")
   ```

---

## 📚 References

- **sentence-transformers:** https://www.sbert.net/
- **all-MiniLM-L6-v2:** https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- **CUDA Setup:** https://pytorch.org/get-started/locally/

---

## 📞 Support

**Issues:** UDS3 GitHub Issues  
**Questions:** UDS3 Team  
**Performance:** Load Testing Team

---

**Status:** ✅ **PRODUCTION READY** (v2.1.0)
