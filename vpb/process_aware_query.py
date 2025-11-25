# VCC-UDS3 VPB Process-Aware Queries
# Copyright 2024-2025 VCC Development Team
# SPDX-License-Identifier: Apache-2.0

"""
VPB Process-Aware Queries for VCC-UDS3 v2.0.0

Provides:
- Process-context enriched queries
- Multi-hop reasoning across process and legal hierarchies
- Process step identification in search results
- Legal hierarchy traversal aligned with VPB processes

Aligned with v2.0.0 requirements:
- VPB Integration for process-native AI
- Process-aware search that understands administrative workflows
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


class ProcessStatus(Enum):
    """Status of a process instance."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class ProcessStepType(Enum):
    """Type of process step in administrative workflows."""
    START = "start"
    END = "end"
    TASK = "task"
    DECISION = "decision"  # XOR Gateway
    PARALLEL = "parallel"  # AND Gateway
    EVENT = "event"
    SUBPROCESS = "subprocess"


@dataclass
class ProcessContext:
    """
    Process context for query enrichment.
    
    Contains information about the current process step and workflow state
    to provide context-aware search results.
    """
    process_id: str
    process_name: str
    current_step_id: str
    current_step_name: str
    step_type: ProcessStepType
    
    # Process metadata
    process_owner: str = ""
    started_at: Optional[datetime] = None
    status: ProcessStatus = ProcessStatus.NOT_STARTED
    
    # Step context
    previous_steps: List[str] = field(default_factory=list)
    possible_next_steps: List[str] = field(default_factory=list)
    
    # Legal context
    applicable_laws: List[str] = field(default_factory=list)  # § references
    required_documents: List[str] = field(default_factory=list)
    
    # Process variables
    variables: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "process_id": self.process_id,
            "process_name": self.process_name,
            "current_step_id": self.current_step_id,
            "current_step_name": self.current_step_name,
            "step_type": self.step_type.value,
            "process_owner": self.process_owner,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "status": self.status.value,
            "previous_steps": self.previous_steps,
            "possible_next_steps": self.possible_next_steps,
            "applicable_laws": self.applicable_laws,
            "required_documents": self.required_documents,
            "variables": self.variables,
        }


@dataclass
class ProcessAwareSearchResult:
    """
    Search result enriched with process context.
    
    Links search results to relevant process steps and provides
    contextual information for administrative workflows.
    """
    result_id: str
    content: str
    score: float
    
    # Process relevance
    relevant_process_steps: List[str] = field(default_factory=list)
    process_phase: str = ""  # e.g., "Antragsprüfung", "Entscheidung"
    
    # Legal relevance
    legal_references: List[str] = field(default_factory=list)
    legal_hierarchy_path: List[str] = field(default_factory=list)
    
    # Source metadata
    source_document_id: str = ""
    source_type: str = ""  # "law", "regulation", "guideline", "process"
    
    # Process-specific scoring
    process_relevance_score: float = 0.0
    legal_relevance_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "result_id": self.result_id,
            "content": self.content,
            "score": self.score,
            "relevant_process_steps": self.relevant_process_steps,
            "process_phase": self.process_phase,
            "legal_references": self.legal_references,
            "legal_hierarchy_path": self.legal_hierarchy_path,
            "source_document_id": self.source_document_id,
            "source_type": self.source_type,
            "process_relevance_score": self.process_relevance_score,
            "legal_relevance_score": self.legal_relevance_score,
        }


class ProcessAwareQuery:
    """
    Process-Aware Query Builder for VCC-UDS3 v2.0.0
    
    Enriches search queries with process context for more relevant results:
    - Extracts process step from context
    - Identifies applicable laws
    - Builds multi-hop traversal queries
    - Ranks results by process relevance
    
    Integration points:
    - VPBAdapter: Process definition access
    - MultiHopReasoner: Legal hierarchy traversal
    - UDS3SearchAPI: Hybrid search execution
    """
    
    def __init__(
        self,
        vpb_adapter: Any = None,
        multi_hop_reasoner: Any = None,
        search_api: Any = None,
    ):
        """
        Initialize Process-Aware Query builder.
        
        Args:
            vpb_adapter: VPB process adapter
            multi_hop_reasoner: Multi-hop legal reasoner
            search_api: UDS3 Search API
        """
        self.vpb = vpb_adapter
        self.multi_hop = multi_hop_reasoner
        self.search_api = search_api
        
        # Process-to-law mappings (configured per deployment)
        self._process_law_mappings: Dict[str, List[str]] = {}
        
    def configure_process_law_mapping(
        self,
        process_id: str,
        applicable_laws: List[str],
    ) -> None:
        """
        Configure mapping between processes and applicable laws.
        
        Args:
            process_id: Process identifier
            applicable_laws: List of § references applicable to this process
        """
        self._process_law_mappings[process_id] = applicable_laws
        logger.debug(f"Configured {len(applicable_laws)} laws for process {process_id}")
    
    async def build_process_aware_query(
        self,
        query_text: str,
        process_context: Optional[ProcessContext] = None,
    ) -> Dict[str, Any]:
        """
        Build a process-aware search query.
        
        Enriches the base query with:
        - Process step context
        - Applicable laws from process mapping
        - Legal hierarchy paths
        - Weighted search parameters
        
        Args:
            query_text: User's search query
            process_context: Current process context
            
        Returns:
            Enriched query configuration for search API
        """
        query_config = {
            "query_text": query_text,
            "search_types": ["vector", "graph", "keyword"],
            "fusion_method": "rrf",
            "top_k": 20,
        }
        
        if not process_context:
            return query_config
        
        # Add process-specific search terms
        enriched_terms = self._extract_process_terms(query_text, process_context)
        query_config["enriched_query"] = enriched_terms
        
        # Add applicable law filters
        applicable_laws = self._get_applicable_laws(process_context)
        if applicable_laws:
            query_config["legal_filters"] = applicable_laws
        
        # Configure multi-hop for legal hierarchy
        query_config["multi_hop"] = True
        query_config["multi_hop_depth"] = self._determine_hop_depth(process_context)
        
        # Adjust weights based on process phase
        query_config["weights"] = self._calculate_weights(process_context)
        
        logger.debug(
            f"Built process-aware query for process {process_context.process_id}, "
            f"step {process_context.current_step_name}"
        )
        
        return query_config
    
    def _extract_process_terms(
        self,
        query_text: str,
        context: ProcessContext,
    ) -> str:
        """Extract and enrich query terms from process context."""
        terms = [query_text]
        
        # Add current step name
        if context.current_step_name:
            terms.append(context.current_step_name)
        
        # Add applicable laws
        for law in context.applicable_laws[:3]:  # Limit to top 3
            terms.append(law)
        
        # Add process name for context
        if context.process_name:
            terms.append(context.process_name)
        
        return " ".join(terms)
    
    def _get_applicable_laws(self, context: ProcessContext) -> List[str]:
        """Get applicable laws for the current process context."""
        laws = list(context.applicable_laws)
        
        # Add laws from process mapping
        if context.process_id in self._process_law_mappings:
            laws.extend(self._process_law_mappings[context.process_id])
        
        # Deduplicate
        return list(set(laws))
    
    def _determine_hop_depth(self, context: ProcessContext) -> int:
        """Determine optimal multi-hop depth based on process step."""
        # Decision steps need deeper legal exploration
        if context.step_type == ProcessStepType.DECISION:
            return 4
        
        # Subprocess steps may need broader context
        if context.step_type == ProcessStepType.SUBPROCESS:
            return 3
        
        # Standard depth for other steps
        return 2
    
    def _calculate_weights(self, context: ProcessContext) -> Dict[str, float]:
        """Calculate search weights based on process phase."""
        # Default weights
        weights = {"vector": 0.4, "graph": 0.3, "keyword": 0.3}
        
        # Decision steps: more weight on legal graph
        if context.step_type == ProcessStepType.DECISION:
            weights = {"vector": 0.3, "graph": 0.4, "keyword": 0.3}
        
        # Task steps: more weight on specific content
        elif context.step_type == ProcessStepType.TASK:
            weights = {"vector": 0.45, "graph": 0.25, "keyword": 0.3}
        
        return weights
    
    async def search_with_process_context(
        self,
        query_text: str,
        process_context: Optional[ProcessContext] = None,
    ) -> List[ProcessAwareSearchResult]:
        """
        Execute process-aware search.
        
        Args:
            query_text: User's search query
            process_context: Current process context
            
        Returns:
            List of process-aware search results
        """
        # Build enriched query
        query_config = await self.build_process_aware_query(query_text, process_context)
        
        # Execute search (mock if search_api not available)
        if self.search_api:
            raw_results = await self.search_api.hybrid_search(**query_config)
        else:
            raw_results = self._mock_search_results(query_text)
        
        # Enrich results with process context
        enriched_results = []
        for result in raw_results:
            enriched = await self._enrich_result_with_process(result, process_context)
            enriched_results.append(enriched)
        
        # Sort by combined score
        enriched_results.sort(
            key=lambda r: r.score * 0.6 + r.process_relevance_score * 0.4,
            reverse=True,
        )
        
        return enriched_results
    
    async def _enrich_result_with_process(
        self,
        result: Dict[str, Any],
        context: Optional[ProcessContext],
    ) -> ProcessAwareSearchResult:
        """Enrich a search result with process context."""
        
        # Calculate process relevance
        process_score = 0.0
        relevant_steps = []
        
        if context:
            # Check if result mentions current process step
            content = result.get("content", "").lower()
            step_name = context.current_step_name.lower()
            
            if step_name in content:
                process_score += 0.5
                relevant_steps.append(context.current_step_id)
            
            # Check for applicable law mentions
            for law in context.applicable_laws:
                if law.lower() in content:
                    process_score += 0.2
        
        # Extract legal references from content
        legal_refs = self._extract_legal_references(result.get("content", ""))
        
        return ProcessAwareSearchResult(
            result_id=result.get("id", ""),
            content=result.get("content", ""),
            score=result.get("score", 0.0),
            relevant_process_steps=relevant_steps,
            process_phase=context.current_step_name if context else "",
            legal_references=legal_refs,
            source_document_id=result.get("document_id", ""),
            source_type=result.get("source_type", "unknown"),
            process_relevance_score=min(1.0, process_score),
            legal_relevance_score=result.get("legal_score", 0.0),
        )
    
    def _extract_legal_references(self, content: str) -> List[str]:
        """Extract § references from content."""
        import re
        
        # Pattern for German legal references
        pattern = r'§\s*\d+(?:\s*(?:Abs\.?\s*\d+)?(?:\s*(?:Satz|S\.)\s*\d+)?(?:\s*Nr\.?\s*\d+)?)?(?:\s+[A-Z][A-Za-z]+)?'
        
        matches = re.findall(pattern, content)
        return list(set(matches))[:10]  # Limit to 10 unique references
    
    def _mock_search_results(self, query: str) -> List[Dict[str, Any]]:
        """Generate mock search results for testing."""
        return [
            {
                "id": f"result-1",
                "content": f"Relevant content for: {query}. § 58 LBO Abstandsflächen sind einzuhalten.",
                "score": 0.85,
                "document_id": "doc-001",
                "source_type": "law",
            },
            {
                "id": f"result-2",
                "content": f"Additional information about: {query}. Gemäß § 54 LBO ist ein Bauantrag erforderlich.",
                "score": 0.72,
                "document_id": "doc-002",
                "source_type": "regulation",
            },
        ]
    
    async def get_process_legal_hierarchy(
        self,
        process_id: str,
    ) -> Dict[str, Any]:
        """
        Get complete legal hierarchy for a process.
        
        Uses multi-hop reasoning to traverse from process to all
        applicable laws and their hierarchical relationships.
        
        Args:
            process_id: Process identifier
            
        Returns:
            Legal hierarchy tree for the process
        """
        applicable_laws = self._process_law_mappings.get(process_id, [])
        
        hierarchy = {
            "process_id": process_id,
            "applicable_laws": applicable_laws,
            "hierarchy": {},
        }
        
        if self.multi_hop:
            for law in applicable_laws:
                try:
                    law_hierarchy = await self.multi_hop.traverse_hierarchy(
                        start_id=law,
                        direction="both",
                        max_depth=3,
                    )
                    hierarchy["hierarchy"][law] = law_hierarchy
                except Exception as e:
                    logger.warning(f"Failed to get hierarchy for {law}: {e}")
        
        return hierarchy


# Factory function
def create_process_aware_query(
    vpb_adapter: Any = None,
    multi_hop_reasoner: Any = None,
    search_api: Any = None,
) -> ProcessAwareQuery:
    """
    Create a ProcessAwareQuery instance.
    
    Args:
        vpb_adapter: VPB process adapter
        multi_hop_reasoner: Multi-hop legal reasoner
        search_api: UDS3 Search API
        
    Returns:
        Configured ProcessAwareQuery instance
    """
    return ProcessAwareQuery(
        vpb_adapter=vpb_adapter,
        multi_hop_reasoner=multi_hop_reasoner,
        search_api=search_api,
    )
