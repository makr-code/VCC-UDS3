"""
UDS3 RAG Caching Layer
Performance-optimierter Cache mit LRU-Strategie und TTL
"""

import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
from pathlib import Path


@dataclass
class CachedRAGResult:
    """Gecachtes RAG-Ergebnis mit Metadaten"""
    answer: str
    confidence: float
    sources: list
    query_type: str
    timestamp: float
    ttl_minutes: int
    
    def is_valid(self) -> bool:
        """Prüft ob Cache-Eintrag noch gültig ist"""
        age_minutes = (time.time() - self.timestamp) / 60
        return age_minutes < self.ttl_minutes
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        return asdict(self)


class RAGCache:
    """
    LRU Cache für RAG-Queries mit TTL Support.
    
    Features:
    - LRU Eviction (Least Recently Used)
    - TTL (Time To Live) pro Cache-Eintrag
    - Query-Hash-basierter Schlüssel
    - Cache Hit/Miss Statistics
    """
    
    def __init__(self, max_size: int = 1000, default_ttl_minutes: int = 60):
        """
        Args:
            max_size: Maximale Anzahl gecachter Queries
            default_ttl_minutes: Standard TTL in Minuten
        """
        self.max_size = max_size
        self.default_ttl_minutes = default_ttl_minutes
        self._cache: OrderedDict[str, CachedRAGResult] = OrderedDict()
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expired': 0
        }
    
    def _generate_cache_key(self, query: str, context_params: Optional[Dict] = None) -> str:
        """
        Generiert Cache-Key aus Query und Kontext-Parametern.
        
        Args:
            query: User-Query
            context_params: Zusätzliche Parameter (domain, filters, etc.)
        
        Returns:
            SHA256 Hash als Cache-Key
        """
        # Normalisiere Query (lowercase, strip whitespace)
        normalized_query = query.lower().strip()
        
        # Kombiniere mit Context-Parametern
        cache_input = {
            'query': normalized_query,
            'context': context_params or {}
        }
        
        # JSON-Serialisierung + SHA256 Hash
        cache_str = json.dumps(cache_input, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()
    
    def get(self, query: str, context_params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Holt Ergebnis aus Cache (wenn vorhanden und gültig).
        
        Args:
            query: User-Query
            context_params: Kontext-Parameter
        
        Returns:
            Gecachtes Ergebnis oder None
        """
        cache_key = self._generate_cache_key(query, context_params)
        
        if cache_key in self._cache:
            cached_result = self._cache[cache_key]
            
            # Prüfe TTL
            if cached_result.is_valid():
                # Move to end (LRU)
                self._cache.move_to_end(cache_key)
                self.stats['hits'] += 1
                return cached_result.to_dict()
            else:
                # Expired - entfernen
                del self._cache[cache_key]
                self.stats['expired'] += 1
        
        self.stats['misses'] += 1
        return None
    
    def put(
        self, 
        query: str, 
        answer: str, 
        confidence: float, 
        sources: list,
        query_type: str,
        context_params: Optional[Dict] = None,
        ttl_minutes: Optional[int] = None
    ):
        """
        Speichert RAG-Ergebnis im Cache.
        
        Args:
            query: User-Query
            answer: LLM-Antwort
            confidence: Konfidenz-Score
            sources: Liste von Quellen
            query_type: Typ der Query (z.B. 'PROCESS_SEARCH')
            context_params: Kontext-Parameter
            ttl_minutes: Custom TTL (optional)
        """
        cache_key = self._generate_cache_key(query, context_params)
        
        cached_result = CachedRAGResult(
            answer=answer,
            confidence=confidence,
            sources=sources,
            query_type=query_type,
            timestamp=time.time(),
            ttl_minutes=ttl_minutes or self.default_ttl_minutes
        )
        
        # LRU: Entferne ältesten Eintrag wenn voll
        if len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)  # FIFO
            self.stats['evictions'] += 1
        
        self._cache[cache_key] = cached_result
    
    def clear(self):
        """Leert den gesamten Cache"""
        self._cache.clear()
    
    def remove_expired(self) -> int:
        """
        Entfernt alle abgelaufenen Cache-Einträge.
        
        Returns:
            Anzahl entfernter Einträge
        """
        expired_keys = [
            key for key, value in self._cache.items()
            if not value.is_valid()
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        removed = len(expired_keys)
        self.stats['expired'] += removed
        return removed
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Cache-Statistiken.
        
        Returns:
            Dictionary mit Statistiken
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate_percent': round(hit_rate, 2),
            'evictions': self.stats['evictions'],
            'expired': self.stats['expired'],
            'total_requests': total_requests
        }
    
    def __repr__(self) -> str:
        stats = self.get_stats()
        return (
            f"RAGCache(size={stats['size']}/{stats['max_size']}, "
            f"hit_rate={stats['hit_rate_percent']}%, "
            f"hits={stats['hits']}, misses={stats['misses']})"
        )


class PersistentRAGCache(RAGCache):
    """
    Erweiterter RAG-Cache mit Disk-Persistence.
    
    Speichert Cache-Einträge auf Disk für Session-übergreifende Nutzung.
    """
    
    def __init__(
        self, 
        cache_dir: str = ".rag_cache",
        max_size: int = 1000, 
        default_ttl_minutes: int = 60
    ):
        super().__init__(max_size, default_ttl_minutes)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Lade existierenden Cache
        self._load_from_disk()
    
    def _get_cache_file(self) -> Path:
        """Pfad zur Cache-Datei"""
        return self.cache_dir / "rag_cache.json"
    
    def _load_from_disk(self):
        """Lädt Cache von Disk"""
        cache_file = self._get_cache_file()
        
        if not cache_file.exists():
            return
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            for key, entry in cache_data.items():
                cached_result = CachedRAGResult(**entry)
                if cached_result.is_valid():
                    self._cache[key] = cached_result
        
        except Exception as e:
            print(f"⚠️  Fehler beim Laden des Cache: {e}")
    
    def _save_to_disk(self):
        """Speichert Cache auf Disk"""
        cache_file = self._get_cache_file()
        
        # Nur gültige Einträge speichern
        valid_cache = {
            key: value.to_dict()
            for key, value in self._cache.items()
            if value.is_valid()
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(valid_cache, f, indent=2)
        
        except Exception as e:
            print(f"⚠️  Fehler beim Speichern des Cache: {e}")
    
    def put(self, *args, **kwargs):
        """Überschreibt put() um nach jedem Eintrag zu speichern"""
        super().put(*args, **kwargs)
        self._save_to_disk()
    
    def clear(self):
        """Überschreibt clear() um auch Disk-Cache zu löschen"""
        super().clear()
        cache_file = self._get_cache_file()
        if cache_file.exists():
            cache_file.unlink()
