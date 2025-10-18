#!/usr/bin/env python3
"""
UDS3 Search API - High-Level Search Interface

Provides unified search APIs across Vector, Graph and Relational backends.

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
    results = await search_api.graph_search("Photovoltaik", top_k=10)
    
    # Hybrid search
    query = SearchQuery(
        query_text="Was regelt § 58 LBO BW?",
        top_k=10,
        search_types=["vector", "graph"],
        weights={"vector": 0.5, "graph": 0.5}
    )
    results = await search_api.hybrid_search(query)
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class SearchType(Enum):
    """Available search types"""
    VECTOR = "vector"
    GRAPH = "graph"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


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
    """
    query_text: str
    top_k: int = 10
    filters: Optional[Dict] = None
    search_types: List[str] = field(default_factory=lambda: ["vector", "graph"])
    weights: Optional[Dict[str, float]] = None
    collection: Optional[str] = None
    
    def __post_init__(self):
        """Validate and set default weights"""
        if self.weights is None:
            # Default weights
            self.weights = {
                "vector": 0.5,
                "graph": 0.3,
                "keyword": 0.2
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
    
    Architecture:
        Application → UDS3SearchAPI → Database API → Backend
        
    Example:
        strategy = get_optimized_unified_strategy()
        api = UDS3SearchAPI(strategy)
        results = await api.graph_search("Photovoltaik", top_k=10)
    """
    
    def __init__(self, strategy):
        """
        Initialize Search API
        
        Args:
            strategy: UnifiedDatabaseStrategy instance
        """
        self.strategy = strategy
        self._embedding_model = None  # Lazy load sentence-transformers
        
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
        Keyword search using PostgreSQL full-text search
        
        Uses: strategy.relational_backend.execute_sql() (if available)
        
        Args:
            query_text: Query string
            top_k: Number of results to return
            filters: Optional filters (e.g., {"document_type": "regulation"})
            
        Returns:
            List of SearchResult objects
            
        Note: Currently not implemented (PostgreSQL has no execute_sql API)
        """
        if not self.has_relational:
            logger.warning("Relational backend not available")
            return []
        
        backend = self.strategy.relational_backend
        
        # Check if SQL query API exists
        if not hasattr(backend, 'execute_sql'):
            logger.warning("PostgreSQL backend has no execute_sql() - skipping keyword search")
            return []
        
        # TODO: Implement when PostgreSQL execute_sql() is available
        logger.warning("⏭️ Keyword search not yet implemented (PostgreSQL API missing)")
        return []
    
    async def hybrid_search(
        self,
        search_query: SearchQuery
    ) -> List[SearchResult]:
        """
        Hybrid search combining Vector + Graph + Keyword
        
        Workflow:
        1. Execute searches in parallel (Vector, Graph, Keyword)
        2. Apply weights to scores
        3. Merge results by document_id
        4. Re-rank by final score
        5. Return top_k results
        
        Args:
            search_query: SearchQuery configuration
            
        Returns:
            List of SearchResult objects (top_k, ranked by weighted score)
            
        Example:
            query = SearchQuery(
                query_text="Photovoltaik",
                top_k=10,
                search_types=["vector", "graph"],
                weights={"vector": 0.5, "graph": 0.5}
            )
            results = await api.hybrid_search(query)
        """
        weights = search_query.weights or {
            "vector": 0.5,
            "graph": 0.3,
            "keyword": 0.2
        }
        
        all_results = []
        
        # 1. Vector Search (if enabled)
        if "vector" in search_query.search_types and weights.get("vector", 0) > 0:
            # Generate embedding from query_text
            model = self._get_embedding_model()
            if model:
                embedding = model.encode(search_query.query_text).tolist()
                vector_results = await self.vector_search(
                    embedding, 
                    search_query.top_k * 2,
                    search_query.collection
                )
                
                # Apply weight
                for result in vector_results:
                    result.score *= weights["vector"]
                
                all_results.extend(vector_results)
                logger.info(f"Vector search: {len(vector_results)} results (weight={weights['vector']:.2f})")
        
        # 2. Graph Search (if enabled)
        if "graph" in search_query.search_types and weights.get("graph", 0) > 0:
            graph_results = await self.graph_search(
                search_query.query_text, 
                search_query.top_k * 2
            )
            
            # Apply weight
            for result in graph_results:
                result.score *= weights["graph"]
            
            all_results.extend(graph_results)
            logger.info(f"Graph search: {len(graph_results)} results (weight={weights['graph']:.2f})")
        
        # 3. Keyword Search (if enabled)
        if "keyword" in search_query.search_types and weights.get("keyword", 0) > 0:
            keyword_results = await self.keyword_search(
                search_query.query_text, 
                search_query.top_k * 2,
                search_query.filters
            )
            
            # Apply weight
            for result in keyword_results:
                result.score *= weights["keyword"]
            
            all_results.extend(keyword_results)
            logger.info(f"Keyword search: {len(keyword_results)} results (weight={weights['keyword']:.2f})")
        
        # 4. Merge and Re-Rank
        merged = {}
        for result in all_results:
            doc_id = result.document_id
            if doc_id in merged:
                # Combine scores (sum weighted scores)
                merged[doc_id].score += result.score
                # Merge related docs
                merged[doc_id].related_docs.extend(result.related_docs)
            else:
                merged[doc_id] = result
        
        # Sort by final score (descending)
        final_results = sorted(merged.values(), key=lambda r: r.score, reverse=True)
        
        logger.info(f"✅ Hybrid search: {len(final_results)} unique results (top_k={search_query.top_k})")
        
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
