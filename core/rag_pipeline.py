#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rag_pipeline.py

rag_pipeline.py
UDS3 Generic RAG Pipeline - Retrieval-Augmented Generation
Kombiniert:
- Vector DB (semantische Suche via Embeddings)
- Graph DB (Relationship Traversal)
- Relational DB (strukturierte Details)
- LLM (Reasoning & Generation)
Pipeline:
1. Query Classification → Identifiziere Query-Typ
2. Multi-DB Retrieval → Hole relevante Daten
3. Context Assembly → Baue LLM-Context
4. Prompt Engineering → Format für LLM
5. LLM Generation → Generiere Antwort
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
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass


class QueryType(Enum):
    """Generische Query-Typen für RAG"""
    SEMANTIC_SEARCH = "semantic_search"          # "Finde ähnliche Prozesse"
    DETAIL_LOOKUP = "detail_lookup"              # "Zeige Details zu Prozess X"
    PATH_FINDING = "path_finding"                # "Wie komme ich von A nach B?"
    RELATIONSHIP = "relationship"                # "Welche Prozesse sind verbunden?"
    AGGREGATION = "aggregation"                  # "Wie viele Prozesse gibt es?"
    COMPLIANCE_CHECK = "compliance_check"        # "Ist Prozess X compliant?"
    COMPARISON = "comparison"                    # "Vergleiche Prozess A und B"
    GENERAL = "general"                          # Allgemeine Frage


@dataclass
class RAGContext:
    """Context für LLM-Generation"""
    query: str
    query_type: QueryType
    retrieved_data: Dict[str, Any]
    metadata: Dict[str, Any]
    token_count: int


class UDS3GenericRAG:
    """
    Generic RAG Pipeline für UDS3
    
    Nutzt existierenden DatabaseManager + neue Komponenten
    
    Beispiel:
    ```python
    from uds3.database.database_manager import DatabaseManager
    from uds3.core.embeddings import UDS3GermanEmbeddings
    from uds3.core.llm_ollama import OllamaClient
    
    # Setup
    db_manager = DatabaseManager(config)
    embeddings = UDS3GermanEmbeddings()
    llm = OllamaClient()
    
    rag = UDS3GenericRAG(
        db_manager=db_manager,
        embeddings=embeddings,
        llm_client=llm
    )
    
    # Query
    result = rag.answer_query("Wie läuft der Baugenehmigungsprozess ab?")
    print(result["answer"])
    ```
    """
    
    def __init__(
        self,
        db_manager,
        embeddings,
        llm_client,
        max_context_tokens: int = 4000,
        top_k_results: int = 10
    ):
        """
        Initialisiert RAG Pipeline
        
        Args:
            db_manager: DatabaseManager-Instanz (existierend)
            embeddings: UDS3GermanEmbeddings-Instanz
            llm_client: LLM Client (OllamaClient oder OpenAI)
            max_context_tokens: Maximale Token für LLM-Context
            top_k_results: Maximale Anzahl Ergebnisse pro Retrieval
        """
        self.logger = logging.getLogger('UDS3GenericRAG')
        
        self.db_manager = db_manager
        self.embeddings = embeddings
        self.llm = llm_client
        
        self.max_context_tokens = max_context_tokens
        self.top_k_results = top_k_results
        
        # Statistics
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "avg_retrieval_time": 0.0,
            "avg_generation_time": 0.0
        }
        
        self.logger.info("✅ UDS3GenericRAG initialisiert")
    
    def answer_query(
        self,
        query: str,
        domain: Optional[str] = None,
        include_sources: bool = True,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Beantwortet Query via RAG Pipeline
        
        Args:
            query: User-Query (deutsch)
            domain: Optionale Domain-Einschränkung (z.B. "vpb", "legal")
            include_sources: Quellen in Antwort inkludieren
            temperature: LLM Temperature
        
        Returns:
            Dict mit:
            - answer: Generierte Antwort
            - sources: Liste der genutzten Quellen (optional)
            - query_type: Erkannter Query-Typ
            - confidence: Confidence-Score (0.0 - 1.0)
        """
        import time
        
        self.stats["total_queries"] += 1
        
        try:
            # 1. Query Classification
            query_type = self._classify_query(query)
            self.logger.info(f"📊 Query-Typ: {query_type.value}")
            
            # 2. Multi-DB Retrieval
            retrieval_start = time.time()
            retrieved_data = self._retrieve_data(query, query_type, domain)
            retrieval_time = time.time() - retrieval_start
            self.stats["avg_retrieval_time"] = (
                self.stats["avg_retrieval_time"] * self.stats["successful_queries"] + retrieval_time
            ) / (self.stats["successful_queries"] + 1)
            
            # 3. Context Assembly
            context = self._assemble_context(
                query=query,
                query_type=query_type,
                retrieved_data=retrieved_data
            )
            
            # 4. Prompt Engineering
            prompt = self._build_prompt(context)
            
            # 5. LLM Generation
            generation_start = time.time()
            answer = self.llm.generate(
                prompt=prompt,
                system_prompt=self._get_system_prompt(),
                temperature=temperature,
                max_tokens=1000
            )
            generation_time = time.time() - generation_start
            self.stats["avg_generation_time"] = (
                self.stats["avg_generation_time"] * self.stats["successful_queries"] + generation_time
            ) / (self.stats["successful_queries"] + 1)
            
            self.stats["successful_queries"] += 1
            
            # Build Result
            result = {
                "answer": answer.strip(),
                "query_type": query_type.value,
                "confidence": self._calculate_confidence(context, answer),
                "retrieval_time": retrieval_time,
                "generation_time": generation_time
            }
            
            if include_sources:
                result["sources"] = self._extract_sources(retrieved_data)
            
            return result
        
        except Exception as e:
            self.stats["failed_queries"] += 1
            self.logger.error(f"❌ RAG Query fehlgeschlagen: {e}")
            raise
    
    def semantic_search(
        self,
        query: str,
        domain: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantische Suche (ohne LLM-Generation)
        
        Args:
            query: Suchquery
            domain: Domain-Filter
            top_k: Anzahl Ergebnisse
        
        Returns:
            Liste von Suchergebnissen mit Scores
        """
        top_k = top_k or self.top_k_results
        
        # Vector DB Search
        if self.db_manager.vector_backend:
            try:
                # ChromaDB search_similar nimmt Text-Query direkt (macht intern Embedding)
                collection_name = domain or self.db_manager.vector_backend.collection_name
                results = self.db_manager.vector_backend.search_similar(
                    collection_name=collection_name,
                    query=query,
                    n_results=top_k
                )
                
                return results
            except Exception as e:
                self.logger.error(f"❌ Vector Search fehlgeschlagen: {e}")
                return []
        else:
            self.logger.warning("⚠️ Vector Backend nicht verfügbar")
            return []
    
    def _classify_query(self, query: str) -> QueryType:
        """
        Klassifiziert Query-Typ (Rule-based + optional LLM)
        
        Args:
            query: User-Query
        
        Returns:
            QueryType
        """
        query_lower = query.lower()
        
        # Rule-based Classification
        if any(kw in query_lower for kw in ["ähnlich", "vergleichbar", "wie", "finde"]):
            return QueryType.SEMANTIC_SEARCH
        
        elif any(kw in query_lower for kw in ["details", "zeige", "was ist", "beschreibe"]):
            return QueryType.DETAIL_LOOKUP
        
        elif any(kw in query_lower for kw in ["pfad", "weg", "route", "von", "nach"]):
            return QueryType.PATH_FINDING
        
        elif any(kw in query_lower for kw in ["verbunden", "beziehung", "zusammenhang"]):
            return QueryType.RELATIONSHIP
        
        elif any(kw in query_lower for kw in ["wie viele", "anzahl", "statistik", "summe"]):
            return QueryType.AGGREGATION
        
        elif any(kw in query_lower for kw in ["compliant", "rechtmäßig", "gesetzeskonform", "dsgvo"]):
            return QueryType.COMPLIANCE_CHECK
        
        elif any(kw in query_lower for kw in ["vergleich", "unterschied", "vs", "versus"]):
            return QueryType.COMPARISON
        
        else:
            return QueryType.GENERAL
    
    def _retrieve_data(
        self,
        query: str,
        query_type: QueryType,
        domain: Optional[str]
    ) -> Dict[str, Any]:
        """
        Multi-DB Retrieval basierend auf Query-Typ
        
        Args:
            query: User-Query
            query_type: Klassifizierter Query-Typ
            domain: Domain-Filter
        
        Returns:
            Dict mit retrieved data aus allen DBs
        """
        data = {
            "vector_results": [],
            "graph_results": [],
            "relational_results": [],
            "metadata": {}
        }
        
        # Vector DB: Semantic Search
        if query_type in [QueryType.SEMANTIC_SEARCH, QueryType.GENERAL, QueryType.COMPARISON]:
            data["vector_results"] = self.semantic_search(query, domain, self.top_k_results)
        
        # Graph DB: Path Finding / Relationships
        if query_type in [QueryType.PATH_FINDING, QueryType.RELATIONSHIP]:
            # TODO: Implement Graph Traversal
            pass
        
        # Relational DB: Aggregations / Details
        if query_type in [QueryType.AGGREGATION, QueryType.DETAIL_LOOKUP]:
            # TODO: Implement SQL Queries
            pass
        
        return data
    
    def _assemble_context(
        self,
        query: str,
        query_type: QueryType,
        retrieved_data: Dict[str, Any]
    ) -> RAGContext:
        """
        Assembliert Context für LLM
        
        Args:
            query: User-Query
            query_type: Query-Typ
            retrieved_data: Retrieved Data
        
        Returns:
            RAGContext
        """
        context_parts = []
        
        # Add Vector Results
        for idx, result in enumerate(retrieved_data.get("vector_results", [])[:5]):
            metadata = result.get("metadata", {})
            doc_id = result.get("id", f"doc_{idx}")
            score = result.get("score", 0.0)
            
            # Extract relevant fields
            name = metadata.get("name", "Unbekannt")
            description = metadata.get("description", "")
            
            context_parts.append(f"[Quelle {idx+1}, Score: {score:.3f}]")
            context_parts.append(f"Name: {name}")
            if description:
                context_parts.append(f"Beschreibung: {description}")
            context_parts.append("")
        
        context_text = "\n".join(context_parts)
        
        # Approximate Token Count (1 token ≈ 4 chars for German)
        token_count = len(context_text) // 4
        
        # Truncate if too long
        if token_count > self.max_context_tokens:
            # Keep only first N results
            max_results = int(self.max_context_tokens / (token_count / len(retrieved_data.get("vector_results", [1]))))
            self.logger.warning(f"⚠️ Context zu groß ({token_count} tokens), reduziere auf {max_results} Ergebnisse")
            
            # Re-assemble with fewer results
            return self._assemble_context(
                query,
                query_type,
                {"vector_results": retrieved_data.get("vector_results", [])[:max_results]}
            )
        
        return RAGContext(
            query=query,
            query_type=query_type,
            retrieved_data=retrieved_data,
            metadata={},
            token_count=token_count
        )
    
    def _build_prompt(self, context: RAGContext) -> str:
        """
        Baut finalen Prompt für LLM
        
        Args:
            context: RAGContext
        
        Returns:
            Formatierter Prompt
        """
        # Extract context text
        context_text = "\n".join([
            f"[Quelle {idx+1}] {result.get('metadata', {}).get('name', 'Unbekannt')}: "
            f"{result.get('metadata', {}).get('description', '')[:200]}"
            for idx, result in enumerate(context.retrieved_data.get("vector_results", [])[:5])
        ])
        
        prompt = f"""Basierend auf folgenden Informationen:

{context_text}

Beantworte die Frage: {context.query}

Antworte präzise und strukturiert. Nutze die Informationen aus den Quellen.
"""
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """
        System-Prompt für LLM
        
        Returns:
            System-Prompt
        """
        return """Du bist ein KI-Assistent für deutsche Verwaltungsprozesse.

Deine Aufgabe:
- Beantworte Fragen präzise und strukturiert
- Nutze die bereitgestellten Quellen
- Wenn Informationen fehlen, sage es explizit
- Verwende klare, verständliche Sprache
- Strukturiere lange Antworten mit Aufzählungen

Sprache: Deutsch
Zielgruppe: Behörden-Mitarbeiter & Bürger
"""
    
    def _calculate_confidence(self, context: RAGContext, answer: str) -> float:
        """
        Berechnet Confidence-Score für Antwort
        
        Args:
            context: RAGContext
            answer: Generierte Antwort
        
        Returns:
            Confidence (0.0 - 1.0)
        """
        # Simple heuristic: Basiert auf Anzahl & Scores der Quellen
        vector_results = context.retrieved_data.get("vector_results", [])
        
        if not vector_results:
            return 0.0
        
        # Average score der Top-3 Ergebnisse
        top_3_scores = [r.get("score", 0.0) for r in vector_results[:3]]
        avg_score = sum(top_3_scores) / len(top_3_scores) if top_3_scores else 0.0
        
        # Anzahl der Quellen als Faktor
        source_factor = min(len(vector_results) / 5.0, 1.0)
        
        # Combined Confidence
        confidence = avg_score * 0.7 + source_factor * 0.3
        
        return min(confidence, 1.0)
    
    def _extract_sources(self, retrieved_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extrahiert Quellen-Informationen
        
        Args:
            retrieved_data: Retrieved Data
        
        Returns:
            Liste von Source-Dicts
        """
        sources = []
        
        for result in retrieved_data.get("vector_results", [])[:5]:
            metadata = result.get("metadata", {})
            sources.append({
                "id": result.get("id"),
                "name": metadata.get("name", "Unbekannt"),
                "type": metadata.get("type", "unknown"),
                "score": result.get("score", 0.0)
            })
        
        return sources
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt RAG-Statistiken zurück
        
        Returns:
            Dict mit Statistiken
        """
        success_rate = 0.0
        if self.stats["total_queries"] > 0:
            success_rate = self.stats["successful_queries"] / self.stats["total_queries"]
        
        return {
            **self.stats,
            "success_rate": success_rate,
            "max_context_tokens": self.max_context_tokens,
            "top_k_results": self.top_k_results
        }
    
    def __repr__(self):
        stats = self.get_stats()
        return (
            f"UDS3GenericRAG("
            f"queries={stats['total_queries']}, "
            f"success_rate={stats['success_rate']:.1%}, "
            f"avg_retrieval={stats['avg_retrieval_time']:.3f}s, "
            f"avg_generation={stats['avg_generation_time']:.3f}s)"
        )


if __name__ == "__main__":
    # Test (requires DatabaseManager, Embeddings, LLM)
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing UDS3GenericRAG...")
    print("⚠️ Requires DatabaseManager, Embeddings & LLM Client")
    
    # Mock Test
    print("✅ Module loaded successfully")
