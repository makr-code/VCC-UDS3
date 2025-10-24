#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rag_async.py

UDS3 RAG Async Layer
Asynchrone RAG-Pipeline mit parallelen Multi-DB Queries

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from .rag_pipeline import UDS3GenericRAG, QueryType, RAGContext
from .rag_cache import RAGCache


@dataclass
class AsyncRAGResult:
    """Ergebnis einer asynchronen RAG-Query"""
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    query_type: QueryType
    execution_time_ms: float
    cache_hit: bool
    databases_queried: List[str]


class UDS3AsyncRAG:
    """
    Asynchrone RAG-Pipeline mit:
    - Parallelen Multi-DB Queries
    - Cache Integration
    - Thread Pool für Sync-Operationen
    - Context Aggregation
    
    Optimiert für hohe Durchsatzraten und niedrige Latenz.
    """
    
    def __init__(
        self,
        polyglot_manager,
        llm_client,
        embeddings,
        max_workers: int = 4,
        enable_cache: bool = True,
        cache_ttl_minutes: int = 60
    ):
        """
        Args:
            polyglot_manager: UDS3PolyglotManager Instanz
            llm_client: OllamaClient Instanz
            embeddings: UDS3GermanEmbeddings Instanz
            max_workers: Anzahl Threads für parallele DB-Queries
            enable_cache: Cache aktivieren
            cache_ttl_minutes: TTL für Cache-Einträge
        """
        # Basis RAG-Pipeline
        self.rag = UDS3GenericRAG(
            polyglot_manager=polyglot_manager,
            llm_client=llm_client,
            embeddings=embeddings
        )
        
        # Thread Pool für Sync-Operationen
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Cache
        self.enable_cache = enable_cache
        if enable_cache:
            self.cache = RAGCache(max_size=1000, default_ttl_minutes=cache_ttl_minutes)
        else:
            self.cache = None
        
        # Statistiken
        self.stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'avg_execution_time_ms': 0.0,
            'parallel_queries_executed': 0
        }
    
    async def answer_query_async(
        self,
        query: str,
        app_domain: str = "vpb",
        context_params: Optional[Dict] = None
    ) -> AsyncRAGResult:
        """
        Asynchrone RAG-Query mit Cache-Support.
        
        Args:
            query: User-Query
            app_domain: Anwendungsdomäne
            context_params: Zusätzliche Kontext-Parameter
        
        Returns:
            AsyncRAGResult mit Antwort und Metadaten
        """
        import time
        start_time = time.time()
        
        self.stats['total_queries'] += 1
        cache_hit = False
        
        # Cache-Lookup
        if self.enable_cache and self.cache:
            cached = self.cache.get(query, context_params)
            if cached:
                self.stats['cache_hits'] += 1
                cache_hit = True
                
                execution_time = (time.time() - start_time) * 1000
                
                return AsyncRAGResult(
                    answer=cached['answer'],
                    confidence=cached['confidence'],
                    sources=cached['sources'],
                    query_type=QueryType(cached['query_type']),
                    execution_time_ms=execution_time,
                    cache_hit=True,
                    databases_queried=[]
                )
        
        # Führe RAG-Query asynchron aus (in Thread Pool)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            self.rag.answer_query,
            query,
            app_domain
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        # Update Stats
        self._update_avg_execution_time(execution_time)
        
        # Cache Result
        if self.enable_cache and self.cache:
            self.cache.put(
                query=query,
                answer=result['answer'],
                confidence=result['confidence'],
                sources=result['sources'],
                query_type=result['query_type'].value,
                context_params=context_params
            )
        
        return AsyncRAGResult(
            answer=result['answer'],
            confidence=result['confidence'],
            sources=result['sources'],
            query_type=result['query_type'],
            execution_time_ms=execution_time,
            cache_hit=cache_hit,
            databases_queried=list(result.get('databases_used', {}).keys())
        )
    
    async def batch_query_async(
        self,
        queries: List[str],
        app_domain: str = "vpb"
    ) -> List[AsyncRAGResult]:
        """
        Führt mehrere Queries parallel aus.
        
        Args:
            queries: Liste von User-Queries
            app_domain: Anwendungsdomäne
        
        Returns:
            Liste von AsyncRAGResult
        """
        tasks = [
            self.answer_query_async(query, app_domain)
            for query in queries
        ]
        
        results = await asyncio.gather(*tasks)
        self.stats['parallel_queries_executed'] += len(queries)
        
        return results
    
    async def parallel_multi_db_search(
        self,
        query: str,
        databases: List[str],
        top_k: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parallele Suche über mehrere Datenbanken.
        
        Args:
            query: Suchquery
            databases: Liste von DB-Namen (z.B. ['chromadb', 'neo4j', 'postgresql'])
            top_k: Anzahl Ergebnisse pro DB
        
        Returns:
            Dictionary {db_name: [results]}
        """
        # Erstelle Tasks für jede DB
        tasks = {
            db_name: self._search_database_async(query, db_name, top_k)
            for db_name in databases
        }
        
        # Führe parallel aus
        results = {}
        for db_name, task in tasks.items():
            try:
                results[db_name] = await task
            except Exception as e:
                print(f"⚠️  Fehler bei DB {db_name}: {e}")
                results[db_name] = []
        
        return results
    
    async def _search_database_async(
        self,
        query: str,
        database: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Asynchrone Suche in einer spezifischen Datenbank.
        
        Args:
            query: Suchquery
            database: DB-Name
            top_k: Anzahl Ergebnisse
        
        Returns:
            Liste von Ergebnissen
        """
        loop = asyncio.get_event_loop()
        
        # Führe Sync-Operation in Thread Pool aus
        result = await loop.run_in_executor(
            self.executor,
            self._search_database_sync,
            query,
            database,
            top_k
        )
        
        return result
    
    def _search_database_sync(
        self,
        query: str,
        database: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Synchrone DB-Suche (wird in Thread Pool ausgeführt).
        
        Args:
            query: Suchquery
            database: DB-Name
            top_k: Anzahl Ergebnisse
        
        Returns:
            Liste von Ergebnissen
        """
        # Nutze semantic_search der RAG-Pipeline
        results = self.rag.semantic_search(
            query=query,
            target_database=database,
            top_k=top_k
        )
        
        return results.get('results', [])
    
    def _update_avg_execution_time(self, execution_time_ms: float):
        """Aktualisiert durchschnittliche Ausführungszeit"""
        current_avg = self.stats['avg_execution_time_ms']
        total = self.stats['total_queries']
        
        # Berechne neuen Durchschnitt
        new_avg = ((current_avg * (total - 1)) + execution_time_ms) / total
        self.stats['avg_execution_time_ms'] = new_avg
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt Statistiken zurück.
        
        Returns:
            Dictionary mit Stats
        """
        base_stats = {
            'total_queries': self.stats['total_queries'],
            'cache_hits': self.stats['cache_hits'],
            'cache_hit_rate_percent': (
                (self.stats['cache_hits'] / self.stats['total_queries'] * 100)
                if self.stats['total_queries'] > 0 else 0
            ),
            'avg_execution_time_ms': round(self.stats['avg_execution_time_ms'], 2),
            'parallel_queries_executed': self.stats['parallel_queries_executed']
        }
        
        # Cache-Stats hinzufügen
        if self.cache:
            base_stats['cache_stats'] = self.cache.get_stats()
        
        # RAG-Pipeline-Stats hinzufügen
        base_stats['rag_pipeline_stats'] = self.rag.get_stats()
        
        return base_stats
    
    def clear_cache(self):
        """Leert den Cache"""
        if self.cache:
            self.cache.clear()
    
    def shutdown(self):
        """Fährt Thread Pool herunter"""
        self.executor.shutdown(wait=True)
    
    def __del__(self):
        """Cleanup bei Destruktion"""
        try:
            self.shutdown()
        except:
            pass
    
    def __repr__(self) -> str:
        return (
            f"UDS3AsyncRAG("
            f"queries={self.stats['total_queries']}, "
            f"cache_hits={self.stats['cache_hits']}, "
            f"avg_time={round(self.stats['avg_execution_time_ms'], 1)}ms)"
        )


# Convenience Functions

async def create_async_rag(
    polyglot_manager,
    llm_client,
    embeddings,
    **kwargs
) -> UDS3AsyncRAG:
    """
    Factory-Funktion zum Erstellen einer AsyncRAG-Instanz.
    
    Args:
        polyglot_manager: UDS3PolyglotManager
        llm_client: OllamaClient
        embeddings: UDS3GermanEmbeddings
        **kwargs: Zusätzliche Argumente für UDS3AsyncRAG
    
    Returns:
        UDS3AsyncRAG Instanz
    """
    return UDS3AsyncRAG(
        polyglot_manager=polyglot_manager,
        llm_client=llm_client,
        embeddings=embeddings,
        **kwargs
    )


async def batch_answer_queries(
    rag: UDS3AsyncRAG,
    queries: List[str],
    app_domain: str = "vpb"
) -> List[AsyncRAGResult]:
    """
    Convenience-Funktion für Batch-Queries.
    
    Args:
        rag: UDS3AsyncRAG Instanz
        queries: Liste von Queries
        app_domain: Anwendungsdomäne
    
    Returns:
        Liste von AsyncRAGResult
    """
    return await rag.batch_query_async(queries, app_domain)
