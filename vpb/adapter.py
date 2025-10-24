#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adapter.py

adapter.py
UDS3 VPB Adapter
Bridge zwischen VPB Domain Models und UDS3 Polyglot Manager
Dieser Adapter integriert die VPB-spezifischen Domain Models
(VPBProcess, VPBTask, VPBDocument, VPBParticipant) mit der
UDS3 Polyglot Persistence Architecture.
Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import asdict
import logging

# UDS3 Core
from uds3.core.polyglot_manager import UDS3PolyglotManager

# VPB Domain Models
from uds3.vpb.operations import (
    VPBProcess,
    VPBTask,
    VPBDocument,
    VPBParticipant,
    ProcessStatus,
    TaskStatus,
    ParticipantRole,
    ProcessComplexity,
    LegalContext,
    VPBProcessMiningEngine,
    ProcessAnalysisResult
)

logger = logging.getLogger(__name__)


class VPBAdapter:
    """
    Adapter zwischen VPB Domain Models und UDS3 Polyglot Manager.
    
    Features:
    - Domain Model Mapping (VPB → UDS3 Base Schema)
    - VPB-spezifische CRUD Operations
    - Process Mining Integration
    - Graph-basierte Relationship Queries
    - Semantic Search für VPB-Prozesse
    
    Usage:
        adapter = VPBAdapter()
        process = VPBProcess(...)
        saved = adapter.save_process(process)
        results = adapter.search_processes("Bauantrag")
    """
    
    APP_DOMAIN = "vpb"
    
    def __init__(self, polyglot_manager: Optional[UDS3PolyglotManager] = None):
        """
        Initialisiert VPBAdapter.
        
        Args:
            polyglot_manager: UDS3PolyglotManager Instanz (optional)
        
        Note: Wenn polyglot_manager None ist, muss er extern erstellt und übergeben werden.
        """
        if polyglot_manager is None:
            raise ValueError(
                "polyglot_manager is required. Create with: "
                "UDS3PolyglotManager(backend_config=...)"
            )
        
        self.polyglot = polyglot_manager
        self.mining_engine = VPBProcessMiningEngine()
        
        logger.info("VPBAdapter initialized with Polyglot Manager")
    
    # ========================================
    # VPBProcess Operations
    # ========================================
    
    def save_process(self, process: VPBProcess) -> Dict[str, Any]:
        """
        Speichert VPBProcess in UDS3.
        
        Args:
            process: VPBProcess Instanz
        
        Returns:
            Gespeichertes Dokument mit ID und Metadaten
        """
        # VPB → UDS3 Base Schema Mapping
        data = self._map_process_to_uds3(process)
        
        # Speichern über Polyglot Manager
        saved = self.polyglot.save_document(data, app_domain=self.APP_DOMAIN)
        
        logger.info(f"Saved VPBProcess: {process.process_id} → {saved.get('id')}")
        
        return saved
    
    def get_process(self, process_id: str) -> Optional[VPBProcess]:
        """
        Lädt VPBProcess aus UDS3.
        
        Args:
            process_id: Process ID
        
        Returns:
            VPBProcess Instanz oder None
        """
        # Suche nach process_id in Metadaten
        results = self.polyglot.list_documents(
            app_domain=self.APP_DOMAIN,
            filters={'process_id': process_id}
        )
        
        if not results:
            logger.warning(f"Process not found: {process_id}")
            return None
        
        # UDS3 → VPB Domain Model Mapping
        doc = results[0]
        process = self._map_uds3_to_process(doc)
        
        logger.info(f"Loaded VPBProcess: {process_id}")
        
        return process
    
    def update_process(
        self, 
        process_id: str, 
        updates: Dict[str, Any]
    ) -> Optional[VPBProcess]:
        """
        Aktualisiert VPBProcess.
        
        Args:
            process_id: Process ID
            updates: Dictionary mit Updates
        
        Returns:
            Aktualisiertes VPBProcess oder None
        """
        # Hole existierenden Process
        existing = self.get_process(process_id)
        if not existing:
            return None
        
        # Aktualisiere Felder
        process_dict = asdict(existing)
        process_dict.update(updates)
        
        # Erstelle neuen Process
        updated_process = VPBProcess(**process_dict)
        
        # Speichern
        self.save_process(updated_process)
        
        logger.info(f"Updated VPBProcess: {process_id}")
        
        return updated_process
    
    def delete_process(self, process_id: str, soft_delete: bool = True) -> bool:
        """
        Löscht VPBProcess.
        
        Args:
            process_id: Process ID
            soft_delete: Soft Delete (Standard) oder Hard Delete
        
        Returns:
            True wenn erfolgreich
        """
        # Finde Dokument
        results = self.polyglot.list_documents(
            app_domain=self.APP_DOMAIN,
            filters={'process_id': process_id}
        )
        
        if not results:
            logger.warning(f"Process not found for deletion: {process_id}")
            return False
        
        doc_id = results[0].get('id')
        
        # Lösche über Polyglot Manager
        success = self.polyglot.delete_document(
            doc_id=doc_id,
            app_domain=self.APP_DOMAIN,
            soft_delete=soft_delete
        )
        
        logger.info(f"Deleted VPBProcess: {process_id} (soft={soft_delete})")
        
        return success
    
    def list_processes(
        self,
        status: Optional[ProcessStatus] = None,
        complexity: Optional[ProcessComplexity] = None,
        limit: int = 100
    ) -> List[VPBProcess]:
        """
        Listet VPBProcesses mit optionalen Filtern.
        
        Args:
            status: Filter nach Status
            complexity: Filter nach Komplexität
            limit: Maximale Anzahl Ergebnisse
        
        Returns:
            Liste von VPBProcess Instanzen
        """
        # Build Filters
        filters = {}
        if status:
            filters['status'] = status.value
        if complexity:
            filters['complexity'] = complexity.value
        
        # Query über Polyglot Manager
        docs = self.polyglot.list_documents(
            app_domain=self.APP_DOMAIN,
            filters=filters
        )
        
        # Map zu VPBProcess
        processes = [
            self._map_uds3_to_process(doc)
            for doc in docs[:limit]
        ]
        
        logger.info(f"Listed {len(processes)} VPBProcesses")
        
        return processes
    
    # ========================================
    # Semantic Search
    # ========================================
    
    def search_processes(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantische Suche über VPBProcesses.
        
        Args:
            query: Suchquery (z.B. "Bauantrag Genehmigung")
            top_k: Anzahl Ergebnisse
            filters: Zusätzliche Filter
        
        Returns:
            Liste von Ergebnissen mit Similarity-Scores
        """
        results = self.polyglot.semantic_search(
            query=query,
            app_domain=self.APP_DOMAIN,
            top_k=top_k,
            filters=filters
        )
        
        logger.info(f"Semantic search for '{query}': {len(results.get('results', []))} results")
        
        return results.get('results', [])
    
    # ========================================
    # Process Mining Integration
    # ========================================
    
    def analyze_process(self, process_id: str) -> Optional[ProcessAnalysisResult]:
        """
        Analysiert VPBProcess mit Mining Engine.
        
        Args:
            process_id: Process ID
        
        Returns:
            ProcessAnalysisResult oder None
        """
        process = self.get_process(process_id)
        if not process:
            return None
        
        # Nutze VPB Mining Engine
        analysis = self.mining_engine.analyze_process(process)
        
        logger.info(f"Analyzed process: {process_id}")
        
        return analysis
    
    def calculate_complexity(
        self, 
        process_id: str
    ) -> Optional[Tuple[ProcessComplexity, float]]:
        """
        Berechnet Komplexität eines Prozesses.
        
        Args:
            process_id: Process ID
        
        Returns:
            (ProcessComplexity, Score) oder None
        """
        process = self.get_process(process_id)
        if not process:
            return None
        
        complexity, score = self.mining_engine.analyze_complexity(process)
        
        logger.info(f"Complexity for {process_id}: {complexity.value} ({score:.2f})")
        
        return complexity, score
    
    def identify_bottlenecks(self, process_id: str) -> Optional[List]:
        """
        Identifiziert Bottlenecks in einem Prozess.
        
        Args:
            process_id: Process ID
        
        Returns:
            Liste von BottleneckAnalysis oder None
        """
        process = self.get_process(process_id)
        if not process:
            return None
        
        bottlenecks = self.mining_engine.identify_bottlenecks(process)
        
        logger.info(f"Found {len(bottlenecks)} bottlenecks in {process_id}")
        
        return bottlenecks
    
    # ========================================
    # Graph Queries (Relationships)
    # ========================================
    
    def query_process_tasks(self, process_id: str) -> List[Dict[str, Any]]:
        """
        Lädt alle Tasks eines Prozesses über Graph DB.
        
        Args:
            process_id: Process ID
        
        Returns:
            Liste von Task-Dictionaries
        """
        # Graph Query: Prozess → Tasks
        pattern = {
            'match': '(p:Process {process_id: $process_id})-[:HAS_TASK]->(t:Task)',
            'return': 't',
            'params': {'process_id': process_id}
        }
        
        results = self.polyglot.query_graph(pattern, app_domain=self.APP_DOMAIN)
        
        logger.info(f"Found {len(results)} tasks for process {process_id}")
        
        return results
    
    def query_process_participants(self, process_id: str) -> List[Dict[str, Any]]:
        """
        Lädt alle Participants eines Prozesses über Graph DB.
        
        Args:
            process_id: Process ID
        
        Returns:
            Liste von Participant-Dictionaries
        """
        # Graph Query: Prozess → Participants
        pattern = {
            'match': '(p:Process {process_id: $process_id})-[:HAS_PARTICIPANT]->(part:Participant)',
            'return': 'part',
            'params': {'process_id': process_id}
        }
        
        results = self.polyglot.query_graph(pattern, app_domain=self.APP_DOMAIN)
        
        logger.info(f"Found {len(results)} participants for process {process_id}")
        
        return results
    
    def query_related_processes(
        self, 
        process_id: str,
        relationship_type: str = "RELATED_TO"
    ) -> List[Dict[str, Any]]:
        """
        Findet verwandte Prozesse über Graph DB.
        
        Args:
            process_id: Process ID
            relationship_type: Art der Beziehung
        
        Returns:
            Liste von verwandten Prozessen
        """
        # Graph Query: Prozess → Related Processes
        pattern = {
            'match': f'(p1:Process {{process_id: $process_id}})-[:{relationship_type}]-(p2:Process)',
            'return': 'p2',
            'params': {'process_id': process_id}
        }
        
        results = self.polyglot.query_graph(pattern, app_domain=self.APP_DOMAIN)
        
        logger.info(f"Found {len(results)} related processes for {process_id}")
        
        return results
    
    # ========================================
    # Batch Operations
    # ========================================
    
    def batch_save_processes(self, processes: List[VPBProcess]) -> List[Dict[str, Any]]:
        """
        Speichert mehrere Prozesse in einem Batch.
        
        Args:
            processes: Liste von VPBProcess
        
        Returns:
            Liste von gespeicherten Dokumenten
        """
        saved = []
        for process in processes:
            try:
                doc = self.save_process(process)
                saved.append(doc)
            except Exception as e:
                logger.error(f"Failed to save process {process.process_id}: {e}")
        
        logger.info(f"Batch saved {len(saved)}/{len(processes)} processes")
        
        return saved
    
    # ========================================
    # Statistics & Reporting
    # ========================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Holt Statistiken über alle VPB-Prozesse.
        
        Returns:
            Dictionary mit Statistiken
        """
        all_processes = self.list_processes()
        
        stats = {
            'total_processes': len(all_processes),
            'by_status': {},
            'by_complexity': {},
            'by_legal_context': {}
        }
        
        # Gruppiere nach Status
        for process in all_processes:
            status = process.status.value
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            if process.complexity:
                complexity = process.complexity.value
                stats['by_complexity'][complexity] = stats['by_complexity'].get(complexity, 0) + 1
            
            if process.legal_context:
                context = process.legal_context.value
                stats['by_legal_context'][context] = stats['by_legal_context'].get(context, 0) + 1
        
        return stats
    
    # ========================================
    # Helper Methods (Mapping)
    # ========================================
    
    def _map_process_to_uds3(self, process: VPBProcess) -> Dict[str, Any]:
        """
        Mappt VPBProcess zu UDS3 Base Schema.
        
        Args:
            process: VPBProcess Instanz
        
        Returns:
            Dictionary im UDS3 Base Schema Format
        """
        data = process.to_dict()
        
        # Füge UDS3-spezifische Metadaten hinzu
        data['_metadata'] = {
            'domain': 'vpb',
            'entity_type': 'process',
            'version': '1.0'
        }
        
        return data
    
    def _map_uds3_to_process(self, doc: Dict[str, Any]) -> VPBProcess:
        """
        Mappt UDS3 Dokument zu VPBProcess.
        
        Args:
            doc: UDS3 Dokument (Dictionary)
        
        Returns:
            VPBProcess Instanz
        """
        # Extrahiere relevante Felder
        process_data = {
            k: v for k, v in doc.items()
            if not k.startswith('_') and k != 'id'
        }
        
        # Konvertiere Enums zurück
        if 'status' in process_data:
            process_data['status'] = ProcessStatus(process_data['status'])
        if 'complexity' in process_data:
            process_data['complexity'] = ProcessComplexity(process_data['complexity'])
        if 'legal_context' in process_data:
            process_data['legal_context'] = LegalContext(process_data['legal_context'])
        
        # Erstelle VPBProcess
        return VPBProcess(**process_data)
    
    def __repr__(self) -> str:
        return f"VPBAdapter(app_domain='{self.APP_DOMAIN}', polyglot={self.polyglot})"


# ========================================
# Convenience Functions
# ========================================

def create_vpb_adapter(polyglot_manager: UDS3PolyglotManager) -> VPBAdapter:
    """
    Factory-Funktion zum Erstellen eines VPBAdapter.
    
    Args:
        polyglot_manager: UDS3PolyglotManager Instanz (erforderlich)
    
    Returns:
        VPBAdapter Instanz
    
    Example:
        from uds3.database.database_manager import DatabaseManager
        from uds3.core.polyglot_manager import UDS3PolyglotManager
        
        db_manager = DatabaseManager(backend_dict={...})
        polyglot = UDS3PolyglotManager(backend_config=db_manager)
        adapter = create_vpb_adapter(polyglot)
    """
    return VPBAdapter(polyglot_manager=polyglot_manager)
