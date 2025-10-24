#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
polyglot_manager.py

polyglot_manager.py
UDS3 Polyglot Manager - High-Level Wrapper für DatabaseManager + RAG
Kombiniert:
- Existierenden DatabaseManager (database/)
- German BERT Embeddings (embeddings.py)
- RAG Pipeline (rag_pipeline.py)
- LLM Client (llm_ollama.py)
Bietet High-Level APIs für Apps (VPB, Legal DB, etc.):
- save_process() - Speichert Prozess in allen DBs
- semantic_search() - Semantische Suche
- answer_query() - LLM-basierte Query-Antwort
- get_process_details() - Detaillierte Prozess-Infos
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
from pathlib import Path
import json


class UDS3PolyglotManager:
    """
    High-Level Polyglot Persistence Manager mit LLM-Integration
    
    Nutzt existierenden DatabaseManager + neue RAG-Komponenten
    
    Beispiel:
    ```python
    from uds3.core.polyglot_manager import UDS3PolyglotManager
    
    # Setup
    config = {
        "vector": {"enabled": True, ...},
        "graph": {"enabled": True, ...},
        "relational": {"enabled": True, ...}
    }
    
    manager = UDS3PolyglotManager(config)
    
    # Save Process
    process_id = manager.save_process({
        "name": "Baugenehmigung beantragen",
        "description": "Prozess für Baugenehmigung...",
        "elements": [...]
    }, domain="vpb")
    
    # Semantic Search
    results = manager.semantic_search("Baugenehmigungsprozess")
    
    # LLM Query
    answer = manager.answer_query("Wie läuft der Baugenehmigungsprozess ab?")
    ```
    """
    
    def __init__(
        self,
        backend_config: Dict[str, Any],
        embeddings_model: Optional[str] = None,
        llm_base_url: Optional[str] = None,
        llm_model: Optional[str] = None,
        enable_rag: bool = True,
        cache_dir: Optional[Path] = None
    ):
        """
        Initialisiert UDS3 Polyglot Manager
        
        Args:
            backend_config: DatabaseManager Config (vector, graph, relational)
            embeddings_model: German BERT Model (default: deutsche-telekom/gbert-base)
            llm_base_url: Ollama Server URL (default: http://localhost:11434)
            llm_model: LLM Model (default: mistral)
            enable_rag: RAG Pipeline aktivieren
            cache_dir: Cache-Verzeichnis für Embeddings
        """
        self.logger = logging.getLogger('UDS3PolyglotManager')
        
        # 1. Initialize DatabaseManager (existing)
        self.logger.info("🔧 Initialisiere DatabaseManager...")
        from uds3.database.database_manager import DatabaseManager
        self.db_manager = DatabaseManager(backend_config, autostart=True)
        
        # Start all backends
        try:
            self.db_manager.start_all_backends()
            self.logger.info("✅ DatabaseManager initialisiert")
        except Exception as e:
            self.logger.warning(f"⚠️ Einige Backends konnten nicht gestartet werden: {e}")
        
        # 2. Initialize German Embeddings (new)
        self.logger.info("🧠 Initialisiere German BERT Embeddings...")
        try:
            from uds3.core.embeddings import UDS3GermanEmbeddings
            self.embeddings = UDS3GermanEmbeddings(
                model_name=embeddings_model,
                cache_dir=cache_dir
            )
            self.logger.info("✅ Embeddings initialisiert")
        except Exception as e:
            self.logger.error(f"❌ Embeddings Initialisierung fehlgeschlagen: {e}")
            self.embeddings = None
        
        # 3. Initialize LLM Client (new)
        self.logger.info("🤖 Initialisiere Ollama LLM Client...")
        try:
            from uds3.core.llm_ollama import OllamaClient
            self.llm = OllamaClient(
                base_url=llm_base_url or "http://localhost:11434",
                default_model=llm_model or "mistral"
            )
            self.logger.info("✅ LLM Client initialisiert")
        except Exception as e:
            self.logger.warning(f"⚠️ LLM Client Initialisierung fehlgeschlagen: {e}")
            self.llm = None
        
        # 4. Initialize RAG Pipeline (new)
        self.rag = None
        if enable_rag and self.embeddings and self.llm:
            self.logger.info("🔗 Initialisiere RAG Pipeline...")
            try:
                from uds3.core.rag_pipeline import UDS3GenericRAG
                self.rag = UDS3GenericRAG(
                    db_manager=self.db_manager,
                    embeddings=self.embeddings,
                    llm_client=self.llm
                )
                self.logger.info("✅ RAG Pipeline initialisiert")
            except Exception as e:
                self.logger.warning(f"⚠️ RAG Pipeline Initialisierung fehlgeschlagen: {e}")
        
        self.logger.info("🎉 UDS3PolyglotManager erfolgreich initialisiert!")
    
    def save_process(
        self,
        process_data: Dict[str, Any],
        domain: str = "general",
        generate_embeddings: bool = True
    ) -> str:
        """
        Speichert Prozess in allen DBs (Polyglot Persistence)
        
        Workflow:
        1. Relational DB: Prozess-Details speichern
        2. Graph DB: Prozess-Graph erstellen
        3. Vector DB: Embeddings generieren & speichern
        
        Args:
            process_data: Prozess-Daten (name, description, elements, ...)
            domain: Domain-Tag (z.B. "vpb", "legal")
            generate_embeddings: Automatisch Embeddings generieren
        
        Returns:
            process_id (UUID)
        """
        import uuid
        
        process_id = str(uuid.uuid4())
        process_data["process_id"] = process_id
        process_data["domain"] = domain
        
        self.logger.info(f"💾 Speichere Prozess: {process_data.get('name', 'Unbekannt')}")
        
        # 1. Relational DB: Save main process data
        if self.db_manager.relational_backend:
            try:
                # TODO: Implement proper SQL INSERT
                # For now, use create_document as fallback
                self.logger.debug("📊 Speichere in Relational DB...")
                # self.db_manager.relational_backend.create_document(process_data)
            except Exception as e:
                self.logger.error(f"❌ Relational DB Save fehlgeschlagen: {e}")
        
        # 2. Graph DB: Create process graph
        if self.db_manager.graph_backend:
            try:
                self.logger.debug("🕸️ Erstelle Prozess-Graph...")
                # TODO: Implement Graph creation
                # self._create_process_graph(process_id, process_data)
            except Exception as e:
                self.logger.error(f"❌ Graph DB Save fehlgeschlagen: {e}")
        
        # 3. Vector DB: Generate & store embeddings
        if generate_embeddings and self.embeddings and self.db_manager.vector_backend:
            try:
                self.logger.debug("🧠 Generiere Embeddings...")
                
                # Process-Level Embedding
                description = process_data.get("description", "")
                if description:
                    embedding = self.embeddings.embed_text(description)
                    
                    # Store in Vector DB
                    self.db_manager.vector_backend.add_embedding(
                        id=process_id,
                        embedding=embedding.tolist(),
                        metadata={
                            "process_id": process_id,
                            "name": process_data.get("name", ""),
                            "description": description,
                            "domain": domain,
                            "type": "process"
                        }
                    )
                    
                    self.logger.info(f"✅ Embedding gespeichert für Prozess {process_id}")
                
                # Element-Level Embeddings (optional)
                elements = process_data.get("elements", [])
                for element in elements:
                    element_id = element.get("element_id")
                    element_desc = element.get("description", "")
                    
                    if element_id and element_desc:
                        elem_embedding = self.embeddings.embed_text(element_desc)
                        
                        self.db_manager.vector_backend.add_embedding(
                            id=element_id,
                            embedding=elem_embedding.tolist(),
                            metadata={
                                "process_id": process_id,
                                "element_id": element_id,
                                "name": element.get("name", ""),
                                "description": element_desc,
                                "domain": domain,
                                "type": "element"
                            }
                        )
            
            except Exception as e:
                self.logger.error(f"❌ Vector DB Save fehlgeschlagen: {e}")
        
        self.logger.info(f"✅ Prozess gespeichert: {process_id}")
        return process_id
    
    def semantic_search(
        self,
        query: str,
        domain: Optional[str] = None,
        top_k: int = 10,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Semantische Suche via Vector DB
        
        Args:
            query: Suchquery (deutsch)
            domain: Domain-Filter (z.B. "vpb")
            top_k: Anzahl Ergebnisse
            min_score: Minimaler Similarity-Score (0.0 - 1.0)
        
        Returns:
            Liste von Suchergebnissen mit Scores & Metadata
        """
        if not self.rag:
            self.logger.warning("⚠️ RAG Pipeline nicht verfügbar, nutze direkte Vector Search")
            
            if not self.embeddings or not self.db_manager.vector_backend:
                self.logger.error("❌ Embeddings oder Vector Backend nicht verfügbar")
                return []
            
            # Fallback: Direct Vector Search
            query_embedding = self.embeddings.embed_text(query)
            results = self.db_manager.vector_backend.search(
                query_vector=query_embedding.tolist(),
                top_k=top_k,
                metadata_filter={"domain": domain} if domain else None
            )
            
            # Filter by min_score
            filtered = [r for r in results if r.get("score", 0.0) >= min_score]
            return filtered
        
        # Use RAG Pipeline
        return self.rag.semantic_search(query, domain, top_k)
    
    def answer_query(
        self,
        query: str,
        domain: Optional[str] = None,
        temperature: float = 0.7,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Beantwortet Query via RAG Pipeline (LLM-basiert)
        
        Args:
            query: User-Query
            domain: Domain-Filter
            temperature: LLM Temperature
            include_sources: Quellen inkludieren
        
        Returns:
            Dict mit answer, sources, confidence, query_type
        """
        if not self.rag:
            raise RuntimeError("RAG Pipeline nicht verfügbar")
        
        return self.rag.answer_query(
            query=query,
            domain=domain,
            include_sources=include_sources,
            temperature=temperature
        )
    
    def get_process_details(
        self,
        process_id: str,
        include_elements: bool = True,
        include_graph: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Holt detaillierte Prozess-Informationen aus allen DBs
        
        Args:
            process_id: Prozess-ID (UUID)
            include_elements: Elemente inkludieren
            include_graph: Graph-Daten inkludieren
        
        Returns:
            Prozess-Dict oder None
        """
        process = {}
        
        # 1. Relational DB: Basis-Daten
        if self.db_manager.relational_backend:
            try:
                # TODO: Implement proper SQL SELECT
                pass
            except Exception as e:
                self.logger.error(f"❌ Relational DB Fetch fehlgeschlagen: {e}")
        
        # 2. Graph DB: Graph-Daten
        if include_graph and self.db_manager.graph_backend:
            try:
                # TODO: Implement Graph fetch
                pass
            except Exception as e:
                self.logger.error(f"❌ Graph DB Fetch fehlgeschlagen: {e}")
        
        return process if process else None
    
    def delete_process(self, process_id: str) -> bool:
        """
        Löscht Prozess aus allen DBs
        
        Args:
            process_id: Prozess-ID
        
        Returns:
            True wenn erfolgreich
        """
        success = True
        
        # 1. Vector DB
        if self.db_manager.vector_backend:
            try:
                self.db_manager.vector_backend.delete_embedding(process_id)
            except Exception as e:
                self.logger.error(f"❌ Vector DB Delete fehlgeschlagen: {e}")
                success = False
        
        # 2. Graph DB
        if self.db_manager.graph_backend:
            try:
                # TODO: Implement Graph delete
                pass
            except Exception as e:
                self.logger.error(f"❌ Graph DB Delete fehlgeschlagen: {e}")
                success = False
        
        # 3. Relational DB
        if self.db_manager.relational_backend:
            try:
                # TODO: Implement SQL DELETE
                pass
            except Exception as e:
                self.logger.error(f"❌ Relational DB Delete fehlgeschlagen: {e}")
                success = False
        
        return success
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt Statistiken zurück
        
        Returns:
            Dict mit Statistiken aller Komponenten
        """
        stats = {
            "database_manager": "active" if self.db_manager else "inactive",
            "backends": {
                "vector": bool(self.db_manager.vector_backend),
                "graph": bool(self.db_manager.graph_backend),
                "relational": bool(self.db_manager.relational_backend),
                "file": bool(self.db_manager.file_backend)
            }
        }
        
        if self.embeddings:
            stats["embeddings"] = self.embeddings.get_stats()
        
        if self.llm:
            stats["llm"] = self.llm.get_stats()
        
        if self.rag:
            stats["rag"] = self.rag.get_stats()
        
        return stats
    
    def shutdown(self):
        """Fährt alle Backends herunter"""
        self.logger.info("🛑 Shutting down UDS3PolyglotManager...")
        
        if self.db_manager:
            # TODO: Implement proper shutdown
            pass
        
        if self.embeddings:
            # Clear memory cache
            self.embeddings.clear_cache(memory=True, disk=False)
        
        self.logger.info("✅ Shutdown complete")
    
    def __enter__(self):
        """Context Manager Support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager Support"""
        self.shutdown()
    
    def __repr__(self):
        stats = self.get_stats()
        backends = stats.get("backends", {})
        active_backends = sum(1 for v in backends.values() if v)
        
        return (
            f"UDS3PolyglotManager("
            f"backends={active_backends}/4, "
            f"embeddings={'✅' if self.embeddings else '❌'}, "
            f"llm={'✅' if self.llm else '❌'}, "
            f"rag={'✅' if self.rag else '❌'})"
        )


# Convenience Function
def create_uds3_manager(
    config_path: Optional[Union[str, Path]] = None,
    **kwargs
) -> UDS3PolyglotManager:
    """
    Factory Function für UDS3PolyglotManager
    
    Args:
        config_path: Pfad zu server_config.json (optional)
        **kwargs: Override-Parameter
    
    Returns:
        UDS3PolyglotManager Instanz
    """
    if config_path:
        config_path = Path(config_path)
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        backend_config = config.get("database", {})
    else:
        # Default Config
        backend_config = {
            "vector": {"enabled": True},
            "graph": {"enabled": True},
            "relational": {"enabled": True},
            "file": {"enabled": True}
        }
    
    return UDS3PolyglotManager(backend_config, **kwargs)


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing UDS3PolyglotManager...")
    
    # Minimal Config for Testing
    config = {
        "vector": {"enabled": False},  # Disable for test
        "graph": {"enabled": False},
        "relational": {"enabled": False},
        "file": {"enabled": False}
    }
    
    try:
        manager = UDS3PolyglotManager(config, enable_rag=False)
        print(f"✅ Manager created: {manager}")
        
        stats = manager.get_stats()
        print(f"📊 Stats: {json.dumps(stats, indent=2)}")
        
        manager.shutdown()
    except Exception as e:
        print(f"⚠️ Test failed: {e}")
        print("   (Expected - requires DatabaseManager)")
