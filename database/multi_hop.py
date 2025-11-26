#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
multi_hop.py

UDS3 Multi-Hop Reasoning - Legal Hierarchy Traversal
Provides advanced graph traversal for legal document hierarchies.

v1.6.0 Implementation:
- Cypher query templates for German legal hierarchies
- Adaptive traversal depth based on document type
- Path scoring and relevance ranking
- Support for Bundesrecht → Landesrecht → Kommunalrecht hierarchies

Legal Hierarchy Structure:
    Bundesrecht (Federal)
    ├── Grundgesetz (GG)
    ├── Bundesgesetze (BGB, StGB, etc.)
    └── Bundesverordnungen
    
    Landesrecht (State) 
    ├── Landesverfassung
    ├── Landesgesetze (LBO, etc.)
    └── Landesverordnungen
    
    Kommunalrecht (Municipal)
    ├── Satzungen
    └── Bebauungspläne

Usage:
    from database.multi_hop import MultiHopReasoner, LegalHierarchy
    
    reasoner = MultiHopReasoner(neo4j_backend)
    
    # Find related regulations with hierarchy traversal
    results = await reasoner.traverse_legal_hierarchy(
        start_node="§ 58 LBO",
        max_depth=3,
        direction="both"
    )
    
    # Get full legal context for a paragraph
    context = await reasoner.get_legal_context(
        document_id="lbo_bw_58",
        include_references=True,
        include_implementing=True
    )

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

# Import metrics if available
try:
    from core.metrics import metrics
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False


# ============================================================================
# Legal Hierarchy Definitions
# ============================================================================

class LegalLevel(Enum):
    """German legal hierarchy levels"""
    EU = "eu"  # EU-Recht
    BUND = "bund"  # Bundesrecht
    LAND = "land"  # Landesrecht
    KOMMUNE = "kommune"  # Kommunalrecht
    UNKNOWN = "unknown"


class RelationType(Enum):
    """Types of legal relationships"""
    REFERENCES = "REFERENCES"  # Verweist auf
    IMPLEMENTS = "IMPLEMENTS"  # Setzt um / konkretisiert
    SUPERSEDES = "SUPERSEDES"  # Ersetzt / überholt
    AMENDS = "AMENDS"  # Ändert
    DERIVED_FROM = "DERIVED_FROM"  # Abgeleitet von
    RELATED_TO = "RELATED_TO"  # Verwandt mit
    PART_OF = "PART_OF"  # Teil von (z.B. § zu Gesetz)


@dataclass
class LegalNode:
    """Represents a node in the legal hierarchy"""
    node_id: str
    document_id: str
    title: str
    level: LegalLevel
    node_type: str  # "gesetz", "verordnung", "paragraph", "satzung"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_neo4j_record(cls, record: Dict[str, Any]) -> "LegalNode":
        """Create LegalNode from Neo4j query result"""
        return cls(
            node_id=record.get("id", record.get("node_id", "")),
            document_id=record.get("document_id", ""),
            title=record.get("title", record.get("name", "")),
            level=LegalLevel(record.get("level", "unknown")),
            node_type=record.get("type", record.get("node_type", "unknown")),
            metadata={k: v for k, v in record.items() 
                     if k not in ["id", "node_id", "document_id", "title", "name", "level", "type", "node_type"]}
        )


@dataclass
class LegalPath:
    """Represents a path through the legal hierarchy"""
    nodes: List[LegalNode]
    relationships: List[str]  # Relationship types between nodes
    score: float = 0.0
    depth: int = 0
    
    def __post_init__(self):
        self.depth = len(self.nodes) - 1 if self.nodes else 0


@dataclass
class TraversalResult:
    """Result of a multi-hop traversal"""
    paths: List[LegalPath]
    total_nodes: int
    max_depth_reached: int
    query_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Cypher Query Templates
# ============================================================================

class CypherTemplates:
    """
    Cypher query templates for legal hierarchy traversal
    
    Templates use parameterized queries for security and performance.
    """
    
    # Find nodes that reference a given document
    FIND_REFERENCES = """
        MATCH (source)-[r:REFERENCES|IMPLEMENTS|DERIVED_FROM]->(target)
        WHERE source.document_id = $document_id OR target.document_id = $document_id
        RETURN source, type(r) as relationship, target
        LIMIT $limit
    """
    
    # Traverse hierarchy upward (to more general laws)
    TRAVERSE_UP = """
        MATCH path = (start)-[:IMPLEMENTS|DERIVED_FROM*1..{max_depth}]->(ancestor)
        WHERE start.document_id = $document_id
        RETURN 
            nodes(path) as nodes,
            [r in relationships(path) | type(r)] as relationships,
            length(path) as depth
        ORDER BY depth
        LIMIT $limit
    """
    
    # Traverse hierarchy downward (to more specific regulations)
    TRAVERSE_DOWN = """
        MATCH path = (start)<-[:IMPLEMENTS|DERIVED_FROM*1..{max_depth}]-(descendant)
        WHERE start.document_id = $document_id
        RETURN 
            nodes(path) as nodes,
            [r in relationships(path) | type(r)] as relationships,
            length(path) as depth
        ORDER BY depth
        LIMIT $limit
    """
    
    # Bidirectional traversal
    TRAVERSE_BOTH = """
        MATCH path = (start)-[:REFERENCES|IMPLEMENTS|DERIVED_FROM|RELATED_TO*1..{max_depth}]-(connected)
        WHERE start.document_id = $document_id
        RETURN 
            nodes(path) as nodes,
            [r in relationships(path) | type(r)] as relationships,
            length(path) as depth
        ORDER BY depth
        LIMIT $limit
    """
    
    # Find shortest path between two legal documents
    SHORTEST_PATH = """
        MATCH path = shortestPath(
            (a)-[*1..{max_depth}]-(b)
        )
        WHERE a.document_id = $start_id AND b.document_id = $end_id
        RETURN 
            nodes(path) as nodes,
            [r in relationships(path) | type(r)] as relationships,
            length(path) as depth
    """
    
    # Get full legal context (all related documents)
    LEGAL_CONTEXT = """
        MATCH (doc)
        WHERE doc.document_id = $document_id
        
        OPTIONAL MATCH (doc)-[r1:REFERENCES]->(referenced)
        OPTIONAL MATCH (doc)<-[r2:REFERENCES]-(referencing)
        OPTIONAL MATCH (doc)-[r3:IMPLEMENTS]->(implementing)
        OPTIONAL MATCH (doc)<-[r4:IMPLEMENTS]-(implemented_by)
        OPTIONAL MATCH (doc)-[r5:PART_OF]->(parent)
        OPTIONAL MATCH (doc)<-[r6:PART_OF]-(child)
        
        RETURN doc,
            collect(DISTINCT referenced) as references,
            collect(DISTINCT referencing) as referenced_by,
            collect(DISTINCT implementing) as implements,
            collect(DISTINCT implemented_by) as implemented_by,
            collect(DISTINCT parent) as parent_docs,
            collect(DISTINCT child) as child_docs
    """
    
    # Search for legal term mentions across hierarchy
    TERM_SEARCH = """
        MATCH (n)
        WHERE n.content CONTAINS $search_term OR n.title CONTAINS $search_term
        WITH n
        OPTIONAL MATCH (n)-[r:REFERENCES|IMPLEMENTS*0..2]-(related)
        RETURN n, collect(DISTINCT related) as related_nodes
        LIMIT $limit
    """
    
    # Find documents by legal level
    BY_LEVEL = """
        MATCH (n)
        WHERE n.level = $level
        RETURN n
        ORDER BY n.title
        LIMIT $limit
    """


# ============================================================================
# Multi-Hop Reasoner
# ============================================================================

class MultiHopReasoner:
    """
    Multi-hop reasoning engine for legal document hierarchies
    
    Provides intelligent traversal of legal relationships with:
    - Adaptive depth based on document type
    - Path scoring for relevance ranking
    - Caching for frequently accessed hierarchies
    """
    
    # Default traversal depths by legal level
    DEFAULT_DEPTHS = {
        LegalLevel.EU: 4,
        LegalLevel.BUND: 3,
        LegalLevel.LAND: 3,
        LegalLevel.KOMMUNE: 2,
        LegalLevel.UNKNOWN: 2
    }
    
    def __init__(self, neo4j_backend, config: Optional[Dict] = None):
        """
        Initialize Multi-Hop Reasoner
        
        Args:
            neo4j_backend: Neo4jGraphBackend instance
            config: Optional configuration dict
        """
        self.backend = neo4j_backend
        self.config = config or {}
        self.templates = CypherTemplates()
        
        # Path scoring weights
        self.path_weights = {
            RelationType.IMPLEMENTS.value: 1.0,
            RelationType.DERIVED_FROM.value: 0.9,
            RelationType.REFERENCES.value: 0.7,
            RelationType.AMENDS.value: 0.8,
            RelationType.RELATED_TO.value: 0.5,
            RelationType.PART_OF.value: 0.6,
        }
        
        logger.info("✅ MultiHopReasoner initialized")
    
    def _get_adaptive_depth(self, level: LegalLevel) -> int:
        """Get adaptive traversal depth based on legal level"""
        return self.config.get("max_depth", self.DEFAULT_DEPTHS.get(level, 2))
    
    def _calculate_path_score(self, relationships: List[str], depth: int) -> float:
        """
        Calculate relevance score for a path
        
        Scoring factors:
        - Relationship types (IMPLEMENTS > REFERENCES > RELATED_TO)
        - Path depth (shorter = more relevant)
        - Decay factor for each hop
        """
        if not relationships:
            return 0.0
        
        # Base score from relationship types
        rel_scores = [self.path_weights.get(r, 0.3) for r in relationships]
        base_score = sum(rel_scores) / len(rel_scores)
        
        # Depth decay (shorter paths are more relevant)
        depth_decay = 0.85 ** depth
        
        return base_score * depth_decay
    
    async def traverse_hierarchy(
        self,
        document_id: str,
        direction: str = "both",
        max_depth: Optional[int] = None,
        limit: int = 50
    ) -> TraversalResult:
        """
        Traverse the legal hierarchy from a starting document
        
        Args:
            document_id: Starting document ID
            direction: "up" (to general), "down" (to specific), "both"
            max_depth: Maximum traversal depth (None = adaptive)
            limit: Maximum number of paths to return
            
        Returns:
            TraversalResult with paths and metadata
        """
        import time
        start_time = time.time()
        
        # Determine adaptive depth if not specified
        if max_depth is None:
            # Try to detect level from document
            max_depth = 3  # Default
        
        # Select appropriate template
        if direction == "up":
            template = self.templates.TRAVERSE_UP
        elif direction == "down":
            template = self.templates.TRAVERSE_DOWN
        else:
            template = self.templates.TRAVERSE_BOTH
        
        # Format query with max_depth
        query = template.format(max_depth=max_depth)
        
        try:
            results = self.backend.execute_query(
                query,
                {"document_id": document_id, "limit": limit}
            )
            
            paths = []
            max_depth_reached = 0
            
            for record in results:
                nodes_data = record.get("nodes", [])
                relationships = record.get("relationships", [])
                depth = record.get("depth", 0)
                
                # Convert nodes to LegalNode objects
                nodes = []
                for node_data in nodes_data:
                    if isinstance(node_data, dict):
                        nodes.append(LegalNode.from_neo4j_record(node_data))
                
                # Calculate path score
                score = self._calculate_path_score(relationships, depth)
                
                paths.append(LegalPath(
                    nodes=nodes,
                    relationships=relationships,
                    score=score,
                    depth=depth
                ))
                
                max_depth_reached = max(max_depth_reached, depth)
            
            # Sort by score
            paths.sort(key=lambda p: p.score, reverse=True)
            
            query_time = (time.time() - start_time) * 1000
            
            # Track metrics
            if METRICS_AVAILABLE:
                metrics.search_latency.labels(
                    search_type="multi_hop",
                    fusion_method="graph"
                ).observe(query_time / 1000)
            
            logger.info(
                f"✅ Multi-hop traversal: {len(paths)} paths found "
                f"(max_depth={max_depth_reached}, time={query_time:.1f}ms)"
            )
            
            return TraversalResult(
                paths=paths,
                total_nodes=sum(len(p.nodes) for p in paths),
                max_depth_reached=max_depth_reached,
                query_time_ms=query_time,
                metadata={"direction": direction, "document_id": document_id}
            )
            
        except Exception as e:
            logger.error(f"❌ Multi-hop traversal failed: {e}")
            if METRICS_AVAILABLE:
                metrics.search_errors.labels(
                    search_type="multi_hop",
                    error_type=type(e).__name__
                ).inc()
            return TraversalResult(
                paths=[],
                total_nodes=0,
                max_depth_reached=0,
                query_time_ms=0,
                metadata={"error": str(e)}
            )
    
    async def get_legal_context(
        self,
        document_id: str,
        include_references: bool = True,
        include_implementing: bool = True,
        include_hierarchy: bool = True
    ) -> Dict[str, Any]:
        """
        Get full legal context for a document
        
        Returns all related documents organized by relationship type.
        
        Args:
            document_id: Document ID to get context for
            include_references: Include documents this one references
            include_implementing: Include implementing regulations
            include_hierarchy: Include parent/child documents
            
        Returns:
            Dict with categorized related documents
        """
        try:
            results = self.backend.execute_query(
                self.templates.LEGAL_CONTEXT,
                {"document_id": document_id}
            )
            
            if not results:
                return {"document_id": document_id, "found": False}
            
            record = results[0]
            
            context = {
                "document_id": document_id,
                "found": True,
                "document": record.get("doc"),
            }
            
            if include_references:
                context["references"] = record.get("references", [])
                context["referenced_by"] = record.get("referenced_by", [])
            
            if include_implementing:
                context["implements"] = record.get("implements", [])
                context["implemented_by"] = record.get("implemented_by", [])
            
            if include_hierarchy:
                context["parent_documents"] = record.get("parent_docs", [])
                context["child_documents"] = record.get("child_docs", [])
            
            logger.info(f"✅ Legal context retrieved for {document_id}")
            return context
            
        except Exception as e:
            logger.error(f"❌ Failed to get legal context: {e}")
            return {"document_id": document_id, "found": False, "error": str(e)}
    
    async def find_shortest_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 5
    ) -> Optional[LegalPath]:
        """
        Find shortest path between two legal documents
        
        Args:
            start_id: Starting document ID
            end_id: Target document ID
            max_depth: Maximum path length
            
        Returns:
            LegalPath if found, None otherwise
        """
        try:
            query = self.templates.SHORTEST_PATH.format(max_depth=max_depth)
            results = self.backend.execute_query(
                query,
                {"start_id": start_id, "end_id": end_id}
            )
            
            if not results:
                logger.info(f"No path found between {start_id} and {end_id}")
                return None
            
            record = results[0]
            nodes_data = record.get("nodes", [])
            relationships = record.get("relationships", [])
            depth = record.get("depth", 0)
            
            nodes = [LegalNode.from_neo4j_record(n) for n in nodes_data if isinstance(n, dict)]
            score = self._calculate_path_score(relationships, depth)
            
            path = LegalPath(
                nodes=nodes,
                relationships=relationships,
                score=score,
                depth=depth
            )
            
            logger.info(f"✅ Shortest path found: {depth} hops")
            return path
            
        except Exception as e:
            logger.error(f"❌ Shortest path search failed: {e}")
            return None
    
    async def search_term_in_hierarchy(
        self,
        search_term: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for a term across the legal hierarchy
        
        Finds documents containing the term and their related documents.
        
        Args:
            search_term: Term to search for (e.g., "Abstandsfläche")
            limit: Maximum results
            
        Returns:
            List of matching documents with related nodes
        """
        try:
            results = self.backend.execute_query(
                self.templates.TERM_SEARCH,
                {"search_term": search_term, "limit": limit}
            )
            
            documents = []
            for record in results:
                doc = record.get("n", {})
                related = record.get("related_nodes", [])
                documents.append({
                    "document": doc,
                    "related_count": len(related),
                    "related_nodes": related[:5]  # Top 5 related
                })
            
            logger.info(f"✅ Term search: {len(documents)} results for '{search_term}'")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Term search failed: {e}")
            return []


# ============================================================================
# Factory Functions
# ============================================================================

def create_multi_hop_reasoner(neo4j_backend, config: Optional[Dict] = None) -> MultiHopReasoner:
    """
    Factory function to create MultiHopReasoner
    
    Args:
        neo4j_backend: Neo4jGraphBackend instance
        config: Optional configuration
        
    Returns:
        MultiHopReasoner instance
    """
    return MultiHopReasoner(neo4j_backend, config)


def check_multi_hop_available() -> bool:
    """Check if multi-hop reasoning is available (Neo4j required)"""
    try:
        from neo4j import GraphDatabase
        return True
    except ImportError:
        return False


# ============================================================================
# Module Test
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    print(f"Multi-hop reasoning available: {check_multi_hop_available()}")
    print(f"Legal levels: {[l.value for l in LegalLevel]}")
    print(f"Relation types: {[r.value for r in RelationType]}")
    
    # Example usage (mock)
    print("\nExample Cypher queries:")
    print(f"TRAVERSE_UP: {CypherTemplates.TRAVERSE_UP[:100]}...")
    print(f"LEGAL_CONTEXT: {CypherTemplates.LEGAL_CONTEXT[:100]}...")
