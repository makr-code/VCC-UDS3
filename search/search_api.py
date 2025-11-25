#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
search_api.py

search_api.py
UDS3 Search API - High-Level Search Interface
Provides unified search APIs across Vector, Graph and Relational backends.

v1.6.0 Features:
- BM25 Keyword Search (PostgreSQL full-text)
- Reciprocal Rank Fusion (RRF) for hybrid search
- Prometheus metrics integration

Architecture:
- Layer 1: Database API (database_api_neo4j.py, database_api_chromadb_remote.py)
- Layer 2: Search API (THIS FILE - uds3_search_api.py) ✅
- Layer 3: Application (veritas_uds3_hybrid_agent.py)
Features:
- Vector Search (ChromaDB) - Semantic similarity
- Graph Search (Neo4j) - Text + Relationships
- Keyword Search (PostgreSQL) - Full-text search
- Hybrid Search - Weighted combination
- Error Handling - Retry logic, graceful degradation
- Type Safety - Dataclasses
Usage:
from uds3.legacy.core import get_optimized_unified_strategy
from uds3.uds3_search_api import UDS3SearchAPI, SearchQuery
strategy = get_optimized_unified_strategy()
search_api = UDS3SearchAPI(strategy)
# Vector search
results = await search_api.vector_search(embedding, top_k=10)
# Graph search
Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

import logging
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)

# Import Prometheus metrics (v1.6.0)
try:
    from core.metrics import metrics, measure_latency
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    logger.debug("Metrics not available - running without Prometheus integration")


class SearchType(Enum):
    """Available search types"""
    VECTOR = "vector"
    GRAPH = "graph"
    KEYWORD = "keyword"  # BM25 Full-Text Search
    HYBRID = "hybrid"


class FusionMethod(Enum):
    """Result fusion methods for hybrid search"""
    WEIGHTED = "weighted"  # Simple weighted sum (legacy)
    RRF = "rrf"  # Reciprocal Rank Fusion (v1.6.0)


@dataclass
class SearchResult:
    """
    Single search result with metadata
    
    Attributes:
        document_id: Unique document identifier
        content: Document content (text)
        metadata: Additional metadata (title, type, source, etc.)
        score: Relevance score (0.0-1.0, higher = more relevant)
        source: Search source ("vector", "graph", "keyword")
        related_docs: Related documents (for graph search)
    """
    document_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    source: str = "unknown"
    related_docs: List[Dict] = field(default_factory=list)
    
    def __repr__(self):
        return f"SearchResult(id={self.document_id}, score={self.score:.3f}, source={self.source})"
    
    def __lt__(self, other):
        """Sort by score (descending)"""
        return self.score > other.score


@dataclass
class SearchQuery:
    """
    Search query configuration
    
    Attributes:
        query_text: Query string
        top_k: Number of results to return
        filters: Optional filters (e.g., {"document_type": "regulation"})
        search_types: Search methods to use (["vector", "graph", "keyword"])
        weights: Score weights for hybrid search ({"vector": 0.5, "graph": 0.3, "keyword": 0.2})
        collection: Optional collection name (for vector search)
        fusion_method: Result fusion method ("weighted" or "rrf") - v1.6.0
        rrf_k: RRF constant (default: 60, industry standard)
        reranker: Reranker type ("none", "cross_encoder") - v1.6.0
        rerank_top_k_multiplier: Fetch multiplier for reranking candidates (default: 3)
    """
    query_text: str
    top_k: int = 10
    filters: Optional[Dict] = None
    search_types: List[str] = field(default_factory=lambda: ["vector", "graph", "keyword"])
    weights: Optional[Dict[str, float]] = None
    collection: Optional[str] = None
    fusion_method: str = "rrf"  # v1.6.0: Default to RRF
    rrf_k: int = 60  # RRF constant (standard value)
    reranker: str = "none"  # v1.6.0: Cross-Encoder reranking
    rerank_top_k_multiplier: int = 3  # Fetch top_k * multiplier for reranking
    
    def __post_init__(self):
        """Validate and set default weights"""
        if self.weights is None:
            # Default weights (used in weighted fusion, also for RRF source weighting)
            self.weights = {
                "vector": 0.4,
                "graph": 0.3,
                "keyword": 0.3
            }
        
        # Normalize weights to sum to 1.0
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v/total for k, v in self.weights.items()}


class UDS3SearchAPI:
    """
    High-Level Search API for UnifiedDatabaseStrategy
    
    Provides unified interface for Vector, Graph and Keyword search.
    Uses Database API Layer (database_api_*.py) for error handling and retry logic.
    
    v1.6.0 Features:
    - BM25 Keyword Search (PostgreSQL full-text)
    - Reciprocal Rank Fusion (RRF) for hybrid search
    - Cross-Encoder reranking for improved relevance
    - Prometheus metrics integration
    
    Architecture:
        Application → UDS3SearchAPI → Database API → Backend
        
    Example:
        strategy = get_optimized_unified_strategy()
        api = UDS3SearchAPI(strategy)
        results = await api.graph_search("Photovoltaik", top_k=10)
        
    Example with Reranking (v1.6.0):
        query = SearchQuery(
            query_text="§ 58 LBO Abstandsflächen",
            search_types=["vector", "graph", "keyword"],
            fusion_method="rrf",
            reranker="cross_encoder"
        )
        results = await api.hybrid_search(query)
    """
    
    def __init__(self, strategy):
        """
        Initialize Search API
        
        Args:
            strategy: UnifiedDatabaseStrategy instance
        """
        self.strategy = strategy
        self._embedding_model = None  # Lazy load sentence-transformers
        self._reranker = None  # Lazy load Cross-Encoder
        
        # Check backend availability
        self.has_vector = hasattr(strategy, 'vector_backend') and strategy.vector_backend is not None
        self.has_graph = hasattr(strategy, 'graph_backend') and strategy.graph_backend is not None
        self.has_relational = hasattr(strategy, 'relational_backend') and strategy.relational_backend is not None
        
        logger.info(f"✅ UDS3SearchAPI initialized (Vector={self.has_vector}, Graph={self.has_graph}, Relational={self.has_relational})")
    
    def _get_embedding_model(self):
        """Lazy load sentence-transformers model"""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ Embedding model loaded (all-MiniLM-L6-v2)")
            except ImportError:
                logger.warning("⚠️ sentence-transformers not installed - vector search disabled")
                return None
        return self._embedding_model
    
    def _get_reranker(self, reranker_type: str = "cross_encoder"):
        """
        Lazy load Cross-Encoder reranker (v1.6.0)
        
        Args:
            reranker_type: Type of reranker ("cross_encoder" or "none")
            
        Returns:
            BaseReranker instance or None
        """
        if reranker_type == "none":
            return None
        
        if self._reranker is None:
            try:
                from search.reranker import create_reranker
                self._reranker = create_reranker()
                logger.info("✅ Cross-Encoder reranker loaded")
            except ImportError:
                logger.warning("⚠️ Reranker not available")
                return None
            except Exception as e:
                logger.warning(f"⚠️ Failed to load reranker: {e}")
                return None
        
        return self._reranker
    
    async def vector_search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        collection: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Semantic vector search using ChromaDB
        
        Uses: strategy.vector_backend.search_similar()
        
        Args:
            query_embedding: Query vector (384D for all-MiniLM-L6-v2)
            top_k: Number of results to return
            collection: Optional collection name
            
        Returns:
            List of SearchResult objects
            
        Example:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embedding = model.encode("Photovoltaik").tolist()
            results = await api.vector_search(embedding, top_k=10)
        """
        if not self.has_vector:
            logger.warning("Vector backend not available")
            return []
        
        try:
            backend = self.strategy.vector_backend
            
            # Call Database API Layer (with error handling)
            raw_results = backend.search_similar(
                query_vector=query_embedding,
                n_results=top_k,
                collection=collection
            )
            
            # Normalize to SearchResult
            results = []
            
            # Handle different result formats
            if isinstance(raw_results, dict):
                # Format: {'ids': [...], 'distances': [...], 'metadatas': [...]}
                ids = raw_results.get('ids', [[]])[0] if raw_results.get('ids') else []
                distances = raw_results.get('distances', [[]])[0] if raw_results.get('distances') else []
                metadatas = raw_results.get('metadatas', [[]])[0] if raw_results.get('metadatas') else []
                documents = raw_results.get('documents', [[]])[0] if raw_results.get('documents') else []
                
                for i, doc_id in enumerate(ids):
                    distance = distances[i] if i < len(distances) else 0.5
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    content = documents[i] if i < len(documents) else metadata.get('content', '')
                    
                    # Convert distance to similarity score
                    similarity = 1.0 - min(distance, 1.0)
                    
                    results.append(SearchResult(
                        document_id=doc_id,
                        content=content,
                        metadata=metadata,
                        score=similarity,
                        source='vector'
                    ))
            
            elif isinstance(raw_results, list):
                # Format: [{'id': '...', 'distance': 0.5, 'metadata': {...}}]
                for raw in raw_results:
                    doc_id = raw.get('id', 'unknown')
                    distance = raw.get('distance', 0.5)
                    metadata = raw.get('metadata', {})
                    content = raw.get('content') or metadata.get('content', '')
                    
                    # Convert distance to similarity score
                    similarity = 1.0 - min(distance, 1.0)
                    
                    results.append(SearchResult(
                        document_id=doc_id,
                        content=content,
                        metadata=metadata,
                        score=similarity,
                        source='vector'
                    ))
            
            logger.info(f"✅ Vector search: {len(results)} results")
            return results
        
        except Exception as e:
            logger.error(f"❌ Vector search failed: {e}")
            return []
    
    async def graph_search(
        self,
        query_text: str,
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        Graph-based search using Neo4j
        
        Uses: strategy.graph_backend.execute_query()
        Features: Text search + Relationship traversal
        
        Args:
            query_text: Query string
            top_k: Number of results to return
            
        Returns:
            List of SearchResult objects
            
        Example:
            results = await api.graph_search("Photovoltaik", top_k=10)
        """
        if not self.has_graph:
            logger.warning("Graph backend not available")
            return []
        
        try:
            backend = self.strategy.graph_backend
            
            # Cypher query for text search with relationships
            cypher = """
            MATCH (d:Document)
            WHERE toLower(d.content) CONTAINS toLower($query)
               OR toLower(d.name) CONTAINS toLower($query)
            OPTIONAL MATCH (d)-[r:RELATED_TO]-(related:Document)
            RETURN d, collect(related) AS related_docs
            LIMIT $top_k
            """
            
            # Call Database API Layer (with retry logic and error handling!)
            raw_results = backend.execute_query(
                cypher,
                params={'query': query_text, 'top_k': top_k}
            )
            
            # Normalize to SearchResult
            results = []
            for record in raw_results:
                doc_node = record.get('d')
                related_nodes = record.get('related_docs', [])
                
                # Extract properties (handle Neo4j Node objects)
                if hasattr(doc_node, '_properties'):
                    props = doc_node._properties
                elif hasattr(doc_node, 'items'):
                    props = dict(doc_node.items())
                elif isinstance(doc_node, dict):
                    props = doc_node
                else:
                    logger.warning(f"Unknown node type: {type(doc_node)}")
                    continue
                
                # Extract related documents
                related_docs = []
                for rel_node in related_nodes:
                    if rel_node:
                        if hasattr(rel_node, '_properties'):
                            related_docs.append(rel_node._properties)
                        elif isinstance(rel_node, dict):
                            related_docs.append(rel_node)
                
                results.append(SearchResult(
                    document_id=props.get('document_id', 'unknown'),
                    content=props.get('content', ''),
                    metadata=props,
                    score=1.0,  # Default score (can be improved with ranking)
                    source='graph',
                    related_docs=related_docs
                ))
            
            logger.info(f"✅ Graph search: {len(results)} results")
            return results
        
        except Exception as e:
            logger.error(f"❌ Graph search failed: {e}")
            return []
    
    async def keyword_search(
        self,
        query_text: str,
        top_k: int = 10,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        BM25-style keyword search using PostgreSQL full-text search
        
        Uses PostgreSQL's ts_rank_cd for BM25-similar ranking with German stemming.
        Requires: setup_fulltext_search() to be called once before use.
        
        v1.6.0 Implementation:
        - Native PostgreSQL full-text search with GIN index
        - German language configuration for stemming
        - BM25-similar ranking using ts_rank_cd (Cover Density)
        
        Args:
            query_text: Query string (e.g., "§ 58 LBO Abstandsflächen")
            top_k: Number of results to return
            filters: Optional filters (e.g., {"document_type": "regulation"})
            
        Returns:
            List of SearchResult objects with BM25-style scores
        """
        if not self.has_relational:
            logger.warning("Relational backend not available")
            return []
        
        backend = self.strategy.relational_backend
        
        # Check for BM25 full-text search API (v1.6.0)
        if hasattr(backend, 'fulltext_search'):
            try:
                raw_results = backend.fulltext_search(
                    query_text=query_text,
                    top_k=top_k,
                    table="documents",
                    language="german"
                )
                
                results = []
                for raw in raw_results:
                    results.append(SearchResult(
                        document_id=raw.get('document_id', 'unknown'),
                        content=raw.get('snippet', ''),  # Highlighted snippet
                        metadata={
                            'file_path': raw.get('file_path', ''),
                            'classification': raw.get('classification', ''),
                            'content_length': raw.get('content_length', 0)
                        },
                        score=float(raw.get('score', 0.0)),
                        source='keyword_bm25'
                    ))
                
                logger.info(f"✅ BM25 Keyword search: {len(results)} results")
                return results
                
            except Exception as e:
                logger.error(f"❌ BM25 Keyword search failed: {e}")
                return []
        
        # Fallback: Check for generic execute_sql API
        elif hasattr(backend, 'execute_sql'):
            try:
                # Basic LIKE search as fallback
                sql = """
                    SELECT document_id, file_path, classification, content_length
                    FROM documents
                    WHERE file_path ILIKE %s OR document_id ILIKE %s
                    LIMIT %s
                """
                pattern = f"%{query_text}%"
                raw_results = backend.execute_sql(sql, (pattern, pattern, top_k))
                
                results = []
                for raw in raw_results:
                    results.append(SearchResult(
                        document_id=raw.get('document_id', 'unknown'),
                        content='',
                        metadata=raw,
                        score=0.5,  # Default score for LIKE search
                        source='keyword_like'
                    ))
                
                logger.info(f"✅ LIKE Keyword search (fallback): {len(results)} results")
                return results
                
            except Exception as e:
                logger.error(f"❌ Keyword search fallback failed: {e}")
                return []
        
        logger.warning("⏭️ Keyword search not available (no fulltext_search or execute_sql method)")
        return []
    
    def _reciprocal_rank_fusion(
        self,
        ranked_lists: Dict[str, List[SearchResult]],
        k: int = 60,
        weights: Optional[Dict[str, float]] = None
    ) -> List[SearchResult]:
        """
        Reciprocal Rank Fusion (RRF) - Industry-standard result fusion
        
        RRF combines multiple ranked lists using:
        RRF_score(d) = Σ (weight_i / (k + rank_i(d)))
        
        Benefits over simple weighted sum:
        - More robust to score scale differences between systems
        - Better handling of missing documents in some lists
        - Proven effective for hybrid search (Cormack et al., 2009)
        
        Args:
            ranked_lists: Dict mapping source to ranked SearchResults
                          e.g., {"vector": [...], "graph": [...], "keyword": [...]}
            k: RRF constant (default: 60, industry standard)
            weights: Optional source weights (default: equal weights)
            
        Returns:
            Fused and re-ranked list of SearchResults
        """
        if weights is None:
            weights = {source: 1.0 for source in ranked_lists.keys()}
        
        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        # Calculate RRF scores
        rrf_scores: Dict[str, float] = {}
        doc_data: Dict[str, SearchResult] = {}  # Store best result for each doc
        
        for source, results in ranked_lists.items():
            source_weight = weights.get(source, 1.0)
            
            for rank, result in enumerate(results, start=1):
                doc_id = result.document_id
                
                # RRF formula: weight / (k + rank)
                rrf_contribution = source_weight / (k + rank)
                
                if doc_id in rrf_scores:
                    rrf_scores[doc_id] += rrf_contribution
                else:
                    rrf_scores[doc_id] = rrf_contribution
                    doc_data[doc_id] = result
                
                # Merge related_docs if available
                if doc_id in doc_data and result.related_docs:
                    existing = doc_data[doc_id].related_docs
                    for rel_doc in result.related_docs:
                        if rel_doc not in existing:
                            existing.append(rel_doc)
        
        # Create final results with RRF scores
        fused_results = []
        for doc_id, rrf_score in rrf_scores.items():
            result = doc_data[doc_id]
            # Create new result with RRF score
            fused_results.append(SearchResult(
                document_id=result.document_id,
                content=result.content,
                metadata=result.metadata,
                score=rrf_score,
                source="rrf_fusion",
                related_docs=result.related_docs
            ))
        
        # Sort by RRF score (descending)
        fused_results.sort(key=lambda r: r.score, reverse=True)
        
        logger.info(f"✅ RRF Fusion: {len(fused_results)} unique documents from {len(ranked_lists)} sources")
        
        return fused_results
    
    async def hybrid_search(
        self,
        search_query: SearchQuery
    ) -> List[SearchResult]:
        """
        Hybrid search combining Vector + Graph + Keyword with RRF fusion
        
        v1.6.0 Enhanced Workflow:
        1. Execute searches in parallel (Vector, Graph, Keyword/BM25)
        2. Apply fusion method:
           - "rrf": Reciprocal Rank Fusion (industry standard)
           - "weighted": Simple weighted score sum (legacy)
        3. Re-rank by fused score
        4. Return top_k results
        
        Args:
            search_query: SearchQuery configuration including:
                - fusion_method: "rrf" (default) or "weighted"
                - rrf_k: RRF constant (default: 60)
            
        Returns:
            List of SearchResult objects (top_k, ranked by fused score)
            
        Example (v1.6.0):
            query = SearchQuery(
                query_text="§ 58 LBO Abstandsflächen",
                top_k=10,
                search_types=["vector", "graph", "keyword"],
                fusion_method="rrf",
                weights={"vector": 0.4, "graph": 0.3, "keyword": 0.3}
            )
            results = await api.hybrid_search(query)
        """
        weights = search_query.weights or {
            "vector": 0.4,
            "graph": 0.3,
            "keyword": 0.3
        }
        
        # Start timing for metrics (v1.6.0)
        start_time = time.time()
        status = "success"
        
        # Collect results per source for RRF
        ranked_lists: Dict[str, List[SearchResult]] = {}
        
        # Determine fetch count (fetch more for better fusion)
        fetch_count = search_query.top_k * 3 if search_query.fusion_method == "rrf" else search_query.top_k * 2
        
        try:
            # 1. Vector Search (if enabled)
            if "vector" in search_query.search_types and weights.get("vector", 0) > 0:
                model = self._get_embedding_model()
                if model:
                    embedding = model.encode(search_query.query_text).tolist()
                    vector_results = await self.vector_search(
                        embedding,
                        fetch_count,
                        search_query.collection
                    )
                    if vector_results:
                        ranked_lists["vector"] = vector_results
                    logger.info(f"Vector search: {len(vector_results)} results")
            
            # 2. Graph Search (if enabled)
            if "graph" in search_query.search_types and weights.get("graph", 0) > 0:
                graph_results = await self.graph_search(
                    search_query.query_text,
                    fetch_count
                )
                if graph_results:
                    ranked_lists["graph"] = graph_results
                logger.info(f"Graph search: {len(graph_results)} results")
            
            # 3. Keyword/BM25 Search (if enabled)
            if "keyword" in search_query.search_types and weights.get("keyword", 0) > 0:
                keyword_results = await self.keyword_search(
                    search_query.query_text,
                    fetch_count,
                    search_query.filters
                )
                if keyword_results:
                    ranked_lists["keyword"] = keyword_results
                logger.info(f"Keyword/BM25 search: {len(keyword_results)} results")
            
            # 4. Fusion based on method
            fusion_start = time.time()
            if search_query.fusion_method == "rrf":
                # Reciprocal Rank Fusion (v1.6.0)
                final_results = self._reciprocal_rank_fusion(
                    ranked_lists=ranked_lists,
                    k=search_query.rrf_k,
                    weights=weights
                )
                logger.info(f"✅ RRF Hybrid search: {len(final_results)} unique results")
            else:
                # Legacy: Simple weighted sum
                all_results = []
                for source, results in ranked_lists.items():
                    source_weight = weights.get(source, 1.0)
                    for result in results:
                        result.score *= source_weight
                    all_results.extend(results)
                
                # Merge by document_id
                merged = {}
                for result in all_results:
                    doc_id = result.document_id
                    if doc_id in merged:
                        merged[doc_id].score += result.score
                        merged[doc_id].related_docs.extend(result.related_docs)
                    else:
                        merged[doc_id] = result
                
                final_results = sorted(merged.values(), key=lambda r: r.score, reverse=True)
            
            # Track fusion latency (v1.6.0)
            if METRICS_AVAILABLE:
                fusion_duration = time.time() - fusion_start
                metrics.fusion_latency.labels(method=search_query.fusion_method).observe(fusion_duration)
                metrics.fusion_requests.labels(
                    method=search_query.fusion_method,
                    sources=",".join(sorted(ranked_lists.keys()))
                ).inc()
            
            logger.info(f"✅ Weighted Hybrid search: {len(final_results)} unique results")
            
            # 5. Cross-Encoder Reranking (v1.6.0)
            if search_query.reranker != "none" and final_results:
                reranker = self._get_reranker(search_query.reranker)
                if reranker:
                    rerank_start = time.time()
                    final_results = await reranker.rerank(
                        query=search_query.query_text,
                        candidates=final_results,
                        top_k=search_query.top_k,
                        content_field="content"
                    )
                    rerank_duration = time.time() - rerank_start
                    logger.info(f"✅ Cross-Encoder reranking: {rerank_duration:.3f}s")
        
        except Exception as e:
            status = "error"
            if METRICS_AVAILABLE:
                metrics.search_errors.labels(
                    search_type="hybrid",
                    error_type=type(e).__name__
                ).inc()
            raise
        
        finally:
            # Track overall search metrics (v1.6.0)
            if METRICS_AVAILABLE:
                duration = time.time() - start_time
                metrics.search_latency.labels(
                    search_type="hybrid",
                    fusion_method=search_query.fusion_method
                ).observe(duration)
                metrics.search_requests.labels(
                    search_type="hybrid",
                    status=status,
                    fusion_method=search_query.fusion_method
                ).inc()
                metrics.search_results.labels(search_type="hybrid").observe(len(final_results) if 'final_results' in locals() else 0)
        
        return final_results[:search_query.top_k]
    
    async def search_by_text(
        self,
        query_text: str,
        top_k: int = 10,
        search_type: str = "hybrid"
    ) -> List[SearchResult]:
        """
        Convenience method for text-based search
        
        Args:
            query_text: Query string
            top_k: Number of results to return
            search_type: "vector", "graph", "keyword", or "hybrid"
            
        Returns:
            List of SearchResult objects
        """
        if search_type == "vector":
            model = self._get_embedding_model()
            if model:
                embedding = model.encode(query_text).tolist()
                return await self.vector_search(embedding, top_k)
            else:
                logger.warning("Embedding model not available - fallback to graph search")
                return await self.graph_search(query_text, top_k)
        
        elif search_type == "graph":
            return await self.graph_search(query_text, top_k)
        
        elif search_type == "keyword":
            return await self.keyword_search(query_text, top_k)
        
        elif search_type == "hybrid":
            query = SearchQuery(
                query_text=query_text,
                top_k=top_k,
                search_types=["vector", "graph", "keyword"]
            )
            return await self.hybrid_search(query)
        
        else:
            raise ValueError(f"Unknown search_type: {search_type}")


# Convenience Functions

def create_search_api(strategy) -> UDS3SearchAPI:
    """
    Factory function to create UDS3SearchAPI
    
    Args:
        strategy: UnifiedDatabaseStrategy instance
        
    Returns:
        UDS3SearchAPI instance
    """
    return UDS3SearchAPI(strategy)


async def quick_search(query_text: str, top_k: int = 10, search_type: str = "hybrid"):
    """
    Quick search using default UDS3 strategy
    
    Args:
        query_text: Query string
        top_k: Number of results
        search_type: "vector", "graph", "keyword", or "hybrid"
        
    Returns:
        List of SearchResult objects
    """
    from uds3.legacy.core import get_optimized_unified_strategy
    
    strategy = get_optimized_unified_strategy()
    api = UDS3SearchAPI(strategy)
    
    return await api.search_by_text(query_text, top_k, search_type)
