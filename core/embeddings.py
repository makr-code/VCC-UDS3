#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
embeddings.py

embeddings.py
UDS3 German Embeddings - Optimiert für deutsche Verwaltungssprache
Nutzt German BERT Modelle für semantische Embeddings:
- deutsche-telekom/gbert-base (primär)
- deutsche-telekom/gbert-large (optional, höhere Qualität)
- deepset/gbert-base (fallback)
Features:
- Batch Processing
- Memory + Disk Caching (SHA256)
- 768-dim Vektoren
- Optimiert für deutsche Verwaltungstexte
Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

import logging
import hashlib
import pickle
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("⚠️ sentence-transformers nicht verfügbar. Installiere: pip install sentence-transformers")


class UDS3GermanEmbeddings:
    """
    German BERT Embeddings für UDS3
    
    Beispiel:
    ```python
    embedder = UDS3GermanEmbeddings()
    
    # Einzelner Text
    embedding = embedder.embed_text("Baugenehmigung beantragen")
    
    # Batch Processing
    embeddings = embedder.embed_batch([
        "Baugenehmigung beantragen",
        "Personalausweis verlängern",
        "Führerschein beantragen"
    ])
    ```
    """
    
    # Verfügbare Modelle (Priorität absteigend)
    AVAILABLE_MODELS = [
        "deutsche-telekom/gbert-base",      # 768-dim, schnell, gute Balance
        "deepset/gbert-base",                # 768-dim, fallback
        "deutsche-telekom/gbert-large",     # 1024-dim, langsam, beste Qualität
    ]
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        cache_dir: Optional[Path] = None,
        device: str = "cpu",
        use_disk_cache: bool = True,
        use_memory_cache: bool = True,
        memory_cache_size: int = 1000
    ):
        """
        Initialisiert German BERT Embeddings
        
        Args:
            model_name: Name des Modells (default: deutsche-telekom/gbert-base)
            cache_dir: Verzeichnis für Disk-Cache (default: ~/.uds3/embeddings_cache)
            device: "cpu" oder "cuda" (GPU)
            use_disk_cache: Disk-Cache aktivieren
            use_memory_cache: Memory-Cache aktivieren (LRU)
            memory_cache_size: Maximale Anzahl gecachter Embeddings im RAM
        """
        self.logger = logging.getLogger('UDS3GermanEmbeddings')
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers nicht verfügbar. "
                "Installiere: pip install sentence-transformers"
            )
        
        # Model Selection
        self.model_name = model_name or self.AVAILABLE_MODELS[0]
        self.device = device
        
        # Cache Configuration
        self.use_disk_cache = use_disk_cache
        self.use_memory_cache = use_memory_cache
        self.memory_cache_size = memory_cache_size
        
        # Cache Directory
        if cache_dir is None:
            cache_dir = Path.home() / ".uds3" / "embeddings_cache"
        self.cache_dir = Path(cache_dir)
        if self.use_disk_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Memory Cache (LRU via OrderedDict)
        from collections import OrderedDict
        self._memory_cache: OrderedDict = OrderedDict()
        
        # Load Model
        self.logger.info(f"🧠 Lade German BERT Model: {self.model_name}")
        try:
            self.model = SentenceTransformer(self.model_name, device=device)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            self.logger.info(f"✅ Model geladen: {self.embedding_dim}-dim Vektoren")
        except Exception as e:
            self.logger.error(f"❌ Model-Loading fehlgeschlagen: {e}")
            # Fallback to next model
            if model_name is None and len(self.AVAILABLE_MODELS) > 1:
                self.logger.info(f"🔄 Versuche Fallback-Model: {self.AVAILABLE_MODELS[1]}")
                self.model_name = self.AVAILABLE_MODELS[1]
                self.model = SentenceTransformer(self.model_name, device=device)
                self.embedding_dim = self.model.get_sentence_embedding_dimension()
            else:
                raise
        
        # Statistics
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "embeddings_generated": 0,
            "disk_cache_reads": 0,
            "memory_cache_reads": 0
        }
    
    def embed_text(
        self,
        text: str,
        normalize: bool = True,
        show_progress_bar: bool = False
    ) -> np.ndarray:
        """
        Erstellt Embedding für einzelnen Text
        
        Args:
            text: Input-Text (deutsch)
            normalize: L2-Normalisierung (für Cosine Similarity)
            show_progress_bar: Fortschrittsbalken anzeigen
        
        Returns:
            numpy array mit Embedding (768-dim oder 1024-dim)
        """
        # Check Cache
        cache_key = self._generate_cache_key(text, normalize)
        
        # 1. Memory Cache
        if self.use_memory_cache and cache_key in self._memory_cache:
            self.stats["cache_hits"] += 1
            self.stats["memory_cache_reads"] += 1
            return self._memory_cache[cache_key]
        
        # 2. Disk Cache
        if self.use_disk_cache:
            cached_embedding = self._load_from_disk_cache(cache_key)
            if cached_embedding is not None:
                self.stats["cache_hits"] += 1
                self.stats["disk_cache_reads"] += 1
                # Update Memory Cache
                if self.use_memory_cache:
                    self._update_memory_cache(cache_key, cached_embedding)
                return cached_embedding
        
        # 3. Generate Embedding
        self.stats["cache_misses"] += 1
        self.stats["embeddings_generated"] += 1
        
        embedding = self.model.encode(
            text,
            normalize_embeddings=normalize,
            show_progress_bar=show_progress_bar,
            convert_to_numpy=True
        )
        
        # Cache Embedding
        if self.use_memory_cache:
            self._update_memory_cache(cache_key, embedding)
        if self.use_disk_cache:
            self._save_to_disk_cache(cache_key, embedding)
        
        return embedding
    
    def embed_batch(
        self,
        texts: List[str],
        normalize: bool = True,
        batch_size: int = 32,
        show_progress_bar: bool = True
    ) -> np.ndarray:
        """
        Erstellt Embeddings für Liste von Texten (Batch Processing)
        
        Args:
            texts: Liste von Input-Texten
            normalize: L2-Normalisierung
            batch_size: Batch-Größe für Verarbeitung
            show_progress_bar: Fortschrittsbalken anzeigen
        
        Returns:
            numpy array mit Embeddings (N x 768 oder N x 1024)
        """
        if not texts:
            return np.array([])
        
        embeddings = []
        texts_to_embed = []
        text_indices = []
        
        # Check Cache für alle Texte
        for idx, text in enumerate(texts):
            cache_key = self._generate_cache_key(text, normalize)
            
            # Memory Cache
            if self.use_memory_cache and cache_key in self._memory_cache:
                self.stats["cache_hits"] += 1
                self.stats["memory_cache_reads"] += 1
                embeddings.append((idx, self._memory_cache[cache_key]))
                continue
            
            # Disk Cache
            if self.use_disk_cache:
                cached_embedding = self._load_from_disk_cache(cache_key)
                if cached_embedding is not None:
                    self.stats["cache_hits"] += 1
                    self.stats["disk_cache_reads"] += 1
                    if self.use_memory_cache:
                        self._update_memory_cache(cache_key, cached_embedding)
                    embeddings.append((idx, cached_embedding))
                    continue
            
            # Muss generiert werden
            texts_to_embed.append(text)
            text_indices.append(idx)
        
        # Generate missing embeddings
        if texts_to_embed:
            self.stats["cache_misses"] += len(texts_to_embed)
            self.stats["embeddings_generated"] += len(texts_to_embed)
            
            new_embeddings = self.model.encode(
                texts_to_embed,
                normalize_embeddings=normalize,
                batch_size=batch_size,
                show_progress_bar=show_progress_bar,
                convert_to_numpy=True
            )
            
            # Cache new embeddings
            for text, embedding in zip(texts_to_embed, new_embeddings):
                cache_key = self._generate_cache_key(text, normalize)
                if self.use_memory_cache:
                    self._update_memory_cache(cache_key, embedding)
                if self.use_disk_cache:
                    self._save_to_disk_cache(cache_key, embedding)
            
            # Add to results
            for idx, embedding in zip(text_indices, new_embeddings):
                embeddings.append((idx, embedding))
        
        # Sort by original index
        embeddings.sort(key=lambda x: x[0])
        
        return np.array([emb for _, emb in embeddings])
    
    def similarity(
        self,
        text1: str,
        text2: str,
        metric: str = "cosine"
    ) -> float:
        """
        Berechnet Ähnlichkeit zwischen zwei Texten
        
        Args:
            text1: Erster Text
            text2: Zweiter Text
            metric: "cosine" (default) oder "euclidean"
        
        Returns:
            Ähnlichkeits-Score (0.0 - 1.0 für cosine)
        """
        emb1 = self.embed_text(text1, normalize=True)
        emb2 = self.embed_text(text2, normalize=True)
        
        if metric == "cosine":
            # Cosine Similarity (da normalisiert: Dot Product)
            similarity = np.dot(emb1, emb2)
            return float(similarity)
        elif metric == "euclidean":
            # Euclidean Distance → Similarity
            distance = np.linalg.norm(emb1 - emb2)
            similarity = 1.0 / (1.0 + distance)
            return float(similarity)
        else:
            raise ValueError(f"Unbekannte Metrik: {metric}")
    
    def _generate_cache_key(self, text: str, normalize: bool) -> str:
        """Generiert Cache-Key via SHA256"""
        content = f"{self.model_name}|{text}|{normalize}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _update_memory_cache(self, key: str, embedding: np.ndarray):
        """Updated Memory Cache mit LRU-Eviction"""
        # Evict oldest if cache full
        if len(self._memory_cache) >= self.memory_cache_size:
            self._memory_cache.popitem(last=False)
        
        # Add to cache (move to end)
        self._memory_cache[key] = embedding
        self._memory_cache.move_to_end(key)
    
    def _load_from_disk_cache(self, cache_key: str) -> Optional[np.ndarray]:
        """Lädt Embedding aus Disk-Cache"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    embedding = pickle.load(f)
                return embedding
            except Exception as e:
                self.logger.warning(f"⚠️ Disk-Cache-Read fehlgeschlagen: {e}")
                return None
        return None
    
    def _save_to_disk_cache(self, cache_key: str, embedding: np.ndarray):
        """Speichert Embedding in Disk-Cache"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(embedding, f)
        except Exception as e:
            self.logger.warning(f"⚠️ Disk-Cache-Write fehlgeschlagen: {e}")
    
    def clear_cache(self, memory: bool = True, disk: bool = False):
        """
        Löscht Cache
        
        Args:
            memory: Memory-Cache löschen
            disk: Disk-Cache löschen (VORSICHT!)
        """
        if memory:
            self._memory_cache.clear()
            self.logger.info("🧹 Memory-Cache gelöscht")
        
        if disk:
            import shutil
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                self.logger.warning("🧹 Disk-Cache gelöscht!")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt Cache-Statistiken zurück
        
        Returns:
            Dict mit Statistiken
        """
        cache_hit_rate = 0.0
        total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        if total_requests > 0:
            cache_hit_rate = self.stats["cache_hits"] / total_requests
        
        return {
            **self.stats,
            "cache_hit_rate": cache_hit_rate,
            "memory_cache_size": len(self._memory_cache),
            "memory_cache_max_size": self.memory_cache_size,
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim,
            "device": self.device
        }
    
    def __repr__(self):
        stats = self.get_stats()
        return (
            f"UDS3GermanEmbeddings("
            f"model={self.model_name}, "
            f"dim={self.embedding_dim}, "
            f"cache_hits={stats['cache_hits']}, "
            f"cache_hit_rate={stats['cache_hit_rate']:.2%})"
        )


# Convenience Function
def create_german_embeddings(**kwargs) -> UDS3GermanEmbeddings:
    """Factory Function für UDS3GermanEmbeddings"""
    return UDS3GermanEmbeddings(**kwargs)


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing UDS3GermanEmbeddings...")
    
    embedder = UDS3GermanEmbeddings()
    
    # Test 1: Single Embedding
    text = "Baugenehmigung für Einfamilienhaus beantragen"
    embedding = embedder.embed_text(text)
    print(f"✅ Embedding Shape: {embedding.shape}")
    
    # Test 2: Batch Embeddings
    texts = [
        "Baugenehmigung beantragen",
        "Personalausweis verlängern",
        "Führerschein beantragen"
    ]
    embeddings = embedder.embed_batch(texts)
    print(f"✅ Batch Embeddings Shape: {embeddings.shape}")
    
    # Test 3: Similarity
    sim = embedder.similarity(
        "Baugenehmigung beantragen",
        "Bauantrag einreichen"
    )
    print(f"✅ Similarity: {sim:.4f}")
    
    # Test 4: Statistics
    stats = embedder.get_stats()
    print(f"✅ Stats: {stats}")
    
    print(f"\n{embedder}")
