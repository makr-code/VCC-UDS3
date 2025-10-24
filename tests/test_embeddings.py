#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_embeddings.py

test_embeddings.py
Test Script für UDS3 German Embeddings
import sys
import logging
logging.basicConfig(level=logging.INFO)
print('🧪 Testing UDS3 German Embeddings...')
print()
from uds3.core.embeddings import UDS3GermanEmbeddings
# Test 1: Initialize
print('1️⃣ Initialisiere Embeddings...')
embedder = UDS3GermanEmbeddings()
print(f'   Model: {embedder.model_name}')
print(f'   Dim: {embedder.embedding_dim}')
print()
# Test 2: Single Embedding
print('2️⃣ Generiere Single Embedding...')
text = 'Baugenehmigung für Einfamilienhaus beantragen'
embedding = embedder.embed_text(text)
print(f'   Text: {text[:50]}...')
print(f'   Shape: {embedding.shape}')
print(f'   First 5 values: {embedding[:5]}')
print()
# Test 3: Batch Embeddings
Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

import sys
import logging
logging.basicConfig(level=logging.INFO)

print('🧪 Testing UDS3 German Embeddings...')
print()

from uds3.core.embeddings import UDS3GermanEmbeddings

# Test 1: Initialize
print('1️⃣ Initialisiere Embeddings...')
embedder = UDS3GermanEmbeddings()
print(f'   Model: {embedder.model_name}')
print(f'   Dim: {embedder.embedding_dim}')
print()

# Test 2: Single Embedding
print('2️⃣ Generiere Single Embedding...')
text = 'Baugenehmigung für Einfamilienhaus beantragen'
embedding = embedder.embed_text(text)
print(f'   Text: {text[:50]}...')
print(f'   Shape: {embedding.shape}')
print(f'   First 5 values: {embedding[:5]}')
print()

# Test 3: Batch Embeddings
print('3️⃣ Generiere Batch Embeddings...')
texts = [
    'Baugenehmigung beantragen',
    'Personalausweis verlängern',
    'Führerschein beantragen'
]
embeddings = embedder.embed_batch(texts, show_progress_bar=False)
print(f'   Texts: {len(texts)}')
print(f'   Shape: {embeddings.shape}')
print()

# Test 4: Similarity
print('4️⃣ Berechne Similarity...')
sim = embedder.similarity('Baugenehmigung beantragen', 'Bauantrag einreichen')
print(f'   Text 1: Baugenehmigung beantragen')
print(f'   Text 2: Bauantrag einreichen')
print(f'   Similarity: {sim:.4f}')
print()

# Test 5: Cache Statistics
print('5️⃣ Cache Statistics...')
stats = embedder.get_stats()
print(f'   Cache Hits: {stats["cache_hits"]}')
print(f'   Cache Misses: {stats["cache_misses"]}')
print(f'   Hit Rate: {stats["cache_hit_rate"]:.2%}')
print(f'   Memory Cache Size: {stats["memory_cache_size"]}/{stats["memory_cache_max_size"]}')
print()

print('✅ Alle Tests erfolgreich!')
print(f'📊 {embedder}')
