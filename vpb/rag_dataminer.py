#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rag_dataminer.py

rag_dataminer.py
VPB RAG DataMiner
=================
Automatische Extraktion von Prozess-Wissen aus VPB-Dokumenten für RAG Pipeline:
- BPMN/EPK Parser Integration
- Knowledge Graph Construction
- Semantic Embedding Generation
- Gap Detection Algorithms
- Process Mining & Analytics
Autor: UDS3 Team
Version: 1.0.0
Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json

# UDS3 Core
from uds3.core.polyglot_manager import UDS3PolyglotManager
from uds3.core.embeddings import create_german_embeddings
from uds3.core.rag_pipeline import UDS3GenericRAG

# VPB Components
# VPBAdapter import moved to avoid circular import
from vpb.parser_bpmn import BPMNProcessParser
from vpb.parser_epk import EPKProcessParser

# Logging
logger = logging.getLogger(__name__)


@dataclass
class ProcessKnowledgeNode:
    """Node im Process Knowledge Graph"""
    node_id: str
    node_type: str  # process, task, decision, participant, regulation
    name: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[List[float]] = None
    related_nodes: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class ProcessKnowledgeGraph:
    """Knowledge Graph für VPB Prozesse"""
    nodes: Dict[str, ProcessKnowledgeNode] = field(default_factory=dict)
    edges: List[Tuple[str, str, str]] = field(default_factory=list)  # (source, target, relation_type)
    statistics: Dict[str, Any] = field(default_factory=dict)
    
    def add_node(self, node: ProcessKnowledgeNode):
        """Füge Node zum Graph hinzu"""
        self.nodes[node.node_id] = node
    
    def add_edge(self, source_id: str, target_id: str, relation_type: str):
        """Füge Edge zum Graph hinzu"""
        self.edges.append((source_id, target_id, relation_type))
        
        # Update related_nodes
        if source_id in self.nodes:
            if target_id not in self.nodes[source_id].related_nodes:
                self.nodes[source_id].related_nodes.append(target_id)
    
    def get_node(self, node_id: str) -> Optional[ProcessKnowledgeNode]:
        """Hole Node aus Graph"""
        return self.nodes.get(node_id)
    
    def get_related_nodes(self, node_id: str, relation_type: Optional[str] = None) -> List[ProcessKnowledgeNode]:
        """Hole verwandte Nodes"""
        related = []
        for source, target, rel_type in self.edges:
            if source == node_id:
                if relation_type is None or rel_type == relation_type:
                    if target in self.nodes:
                        related.append(self.nodes[target])
        return related
    
    def compute_statistics(self):
        """Berechne Graph-Statistiken"""
        self.statistics = {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": {},
            "relation_types": {},
            "avg_degree": 0
        }
        
        # Node Types
        for node in self.nodes.values():
            node_type = node.node_type
            self.statistics["node_types"][node_type] = self.statistics["node_types"].get(node_type, 0) + 1
        
        # Relation Types
        for _, _, rel_type in self.edges:
            self.statistics["relation_types"][rel_type] = self.statistics["relation_types"].get(rel_type, 0) + 1
        
        # Average Degree
        if self.nodes:
            total_degree = sum(len(node.related_nodes) for node in self.nodes.values())
            self.statistics["avg_degree"] = total_degree / len(self.nodes)


@dataclass
class DataMiningResult:
    """Ergebnis des Data Mining Prozesses"""
    processes_extracted: int
    knowledge_graph: ProcessKnowledgeGraph
    documents_created: int
    embeddings_generated: int
    gaps_detected: List[Dict[str, Any]]
    execution_time_ms: float
    statistics: Dict[str, Any]


class VPBRAGDataMiner:
    """
    VPB RAG Data Miner
    
    Automatische Extraktion von Prozess-Wissen aus BPMN/EPK-Dokumenten
    und Integration in UDS3 Knowledge Base.
    """
    
    def __init__(
        self,
        polyglot_manager: Optional[UDS3PolyglotManager] = None,

        enable_embeddings: bool = True
    ):
        """
        Initialisiere VPB RAG DataMiner
        
        Args:
            polyglot_manager: UDS3 PolyglotManager für Datenspeicherung

            enable_embeddings: Generiere Embeddings für semantic search
        """
        self.polyglot = polyglot_manager or UDS3PolyglotManager({})  # Empty config for default setup
        # VPBAdapter optional - not required for core functionality
        self.bpmn_parser = BPMNProcessParser()
        self.epk_parser = EPKProcessParser()
        
        self.enable_embeddings = enable_embeddings
        if enable_embeddings:
            self.embeddings_model = create_german_embeddings()
        
        self.knowledge_graph = ProcessKnowledgeGraph()
        
        logger.info("VPBRAGDataMiner initialisiert")
    
    def extract_from_bpmn(self, bpmn_xml: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Extrahiere Prozess-Wissen aus BPMN XML
        
        Args:
            bpmn_xml: BPMN XML String
            filename: Optional filename für Metadaten
        
        Returns:
            Extrahierte Prozess-Daten
        """
        logger.info(f"Extrahiere Prozess aus BPMN: {filename or 'unnamed'}")
        
        try:
            # Parse BPMN
            process_data = self.bpmn_parser.parse_bpmn_to_uds3(bpmn_xml, filename)
            
            # Erstelle Knowledge Nodes
            self._create_knowledge_nodes_from_process(process_data)
            
            return process_data
        
        except Exception as e:
            logger.error(f"BPMN Extraction fehlgeschlagen: {e}")
            return {}
    
    def extract_from_epk(self, epk_data: Dict[str, Any], filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Extrahiere Prozess-Wissen aus EPK Daten
        
        Args:
            epk_data: EPK Daten-Dictionary
            filename: Optional filename für Metadaten
        
        Returns:
            Extrahierte Prozess-Daten
        """
        logger.info(f"Extrahiere Prozess aus EPK: {filename or 'unnamed'}")
        
        try:
            # Parse EPK
            process_data = self.epk_parser.parse_epk_to_uds3(epk_data, filename)
            
            # Erstelle Knowledge Nodes
            self._create_knowledge_nodes_from_process(process_data)
            
            return process_data
        
        except Exception as e:
            logger.error(f"EPK Extraction fehlgeschlagen: {e}")
            return {}
    
    def extract_from_directory(self, directory_path: Path, file_pattern: str = "*.bpmn") -> DataMiningResult:
        """
        Extrahiere Prozess-Wissen aus allen Dateien in einem Verzeichnis
        
        Args:
            directory_path: Verzeichnis-Pfad
            file_pattern: Datei-Pattern (*.bpmn, *.epk, etc.)
        
        Returns:
            DataMiningResult mit Statistiken
        """
        start_time = datetime.now()
        
        logger.info(f"Starte Data Mining: {directory_path} ({file_pattern})")
        
        processes_extracted = 0
        documents_created = 0
        embeddings_generated = 0
        
        # Finde alle Dateien
        files = list(directory_path.glob(file_pattern))
        logger.info(f"Gefunden: {len(files)} Dateien")
        
        for file_path in files:
            try:
                # Lese Datei
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extrahiere basierend auf Dateiendung
                if file_path.suffix == '.bpmn':
                    process_data = self.extract_from_bpmn(content, file_path.name)
                elif file_path.suffix == '.epk':
                    # EPK als JSON
                    epk_data = json.loads(content)
                    process_data = self.extract_from_epk(epk_data, file_path.name)
                else:
                    logger.warning(f"Unbekanntes Dateiformat: {file_path.suffix}")
                    continue
                
                if process_data:
                    processes_extracted += 1
                    
                    # Speichere in UDS3
                    doc_id = self._save_to_uds3(process_data)
                    if doc_id:
                        documents_created += 1
                        
                        # Generiere Embeddings
                        if self.enable_embeddings:
                            emb_count = self._generate_embeddings_for_process(process_data)
                            embeddings_generated += emb_count
            
            except Exception as e:
                logger.error(f"Fehler beim Verarbeiten von {file_path}: {e}")
        
        # Berechne Graph-Statistiken
        self.knowledge_graph.compute_statistics()
        
        # Detect Gaps
        gaps = self.detect_knowledge_gaps()
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        result = DataMiningResult(
            processes_extracted=processes_extracted,
            knowledge_graph=self.knowledge_graph,
            documents_created=documents_created,
            embeddings_generated=embeddings_generated,
            gaps_detected=gaps,
            execution_time_ms=execution_time,
            statistics=self.knowledge_graph.statistics
        )
        
        logger.info(f"Data Mining abgeschlossen: {processes_extracted} Prozesse in {execution_time:.1f}ms")
        
        return result
    
    def _create_knowledge_nodes_from_process(self, process_data: Dict[str, Any]):
        """
        Erstelle Knowledge Graph Nodes aus Prozess-Daten
        
        Args:
            process_data: Prozess-Daten Dictionary
        """
        process_id = process_data.get('process_id', 'unknown')
        process_name = process_data.get('name', 'Unbekannter Prozess')
        
        # Process Node
        process_node = ProcessKnowledgeNode(
            node_id=process_id,
            node_type='process',
            name=process_name,
            description=process_data.get('description', ''),
            metadata={
                'domain': process_data.get('domain', 'vpb'),
                'complexity': process_data.get('metadata', {}).get('complexity_score', 0),
                'completeness': process_data.get('metadata', {}).get('completeness_score', 0)
            },
            tags=process_data.get('metadata', {}).get('tags', [])
        )
        self.knowledge_graph.add_node(process_node)
        
        # Task Nodes
        steps = process_data.get('steps', [])
        for step in steps:
            task_id = f"{process_id}_task_{step.get('step_number', 0)}"
            task_node = ProcessKnowledgeNode(
                node_id=task_id,
                node_type='task',
                name=step.get('action', 'Unbekannte Aufgabe'),
                description=step.get('description', ''),
                metadata={
                    'step_number': step.get('step_number'),
                    'responsible': step.get('responsible', '')
                }
            )
            self.knowledge_graph.add_node(task_node)
            
            # Edge: Process -> Task
            self.knowledge_graph.add_edge(process_id, task_id, 'contains')
        
        # Participant Nodes
        participants = process_data.get('metadata', {}).get('participants', [])
        for participant in participants:
            participant_id = f"{process_id}_participant_{participant}"
            participant_node = ProcessKnowledgeNode(
                node_id=participant_id,
                node_type='participant',
                name=participant,
                metadata={'process_id': process_id}
            )
            self.knowledge_graph.add_node(participant_node)
            
            # Edge: Process -> Participant
            self.knowledge_graph.add_edge(process_id, participant_id, 'involves')
        
        # Regulation Nodes (if any)
        regulations = process_data.get('metadata', {}).get('legal_references', [])
        for regulation in regulations:
            regulation_id = f"regulation_{regulation.replace(' ', '_')}"
            
            # Nur hinzufügen wenn noch nicht existiert
            if regulation_id not in self.knowledge_graph.nodes:
                regulation_node = ProcessKnowledgeNode(
                    node_id=regulation_id,
                    node_type='regulation',
                    name=regulation,
                    metadata={'type': 'legal_reference'}
                )
                self.knowledge_graph.add_node(regulation_node)
            
            # Edge: Process -> Regulation
            self.knowledge_graph.add_edge(process_id, regulation_id, 'governed_by')
    
    def _save_to_uds3(self, process_data: Dict[str, Any]) -> Optional[str]:
        """
        Speichere Prozess-Daten in UDS3
        
        Args:
            process_data: Prozess-Daten
        
        Returns:
            Document ID oder None bei Fehler
        """
        try:
            # Erstelle UDS3 Document
            doc_id = self.polyglot.save(
                data=process_data,
                app_domain='vpb',
                metadata={
                    'source': 'rag_dataminer',
                    'extraction_time': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Prozess gespeichert: {doc_id}")
            return doc_id
        
        except Exception as e:
            logger.error(f"Fehler beim Speichern: {e}")
            return None
    
    def _generate_embeddings_for_process(self, process_data: Dict[str, Any]) -> int:
        """
        Generiere Embeddings für Prozess-Elemente
        
        Args:
            process_data: Prozess-Daten
        
        Returns:
            Anzahl generierter Embeddings
        """
        if not self.enable_embeddings:
            return 0
        
        count = 0
        
        try:
            # Process-Level Embedding
            process_text = f"{process_data.get('name', '')} {process_data.get('description', '')}"
            if process_text.strip():
                embedding = self.embeddings_model.embed_query(process_text)
                
                # Speichere im Knowledge Graph
                process_id = process_data.get('process_id', 'unknown')
                if process_id in self.knowledge_graph.nodes:
                    self.knowledge_graph.nodes[process_id].embeddings = embedding
                    count += 1
            
            # Task-Level Embeddings
            steps = process_data.get('steps', [])
            for step in steps:
                task_text = f"{step.get('action', '')} {step.get('description', '')}"
                if task_text.strip():
                    embedding = self.embeddings_model.embed_query(task_text)
                    
                    task_id = f"{process_data.get('process_id', 'unknown')}_task_{step.get('step_number', 0)}"
                    if task_id in self.knowledge_graph.nodes:
                        self.knowledge_graph.nodes[task_id].embeddings = embedding
                        count += 1
        
        except Exception as e:
            logger.error(f"Fehler beim Generieren von Embeddings: {e}")
        
        return count
    
    def detect_knowledge_gaps(self) -> List[Dict[str, Any]]:
        """
        Erkenne Lücken in der Wissensbasis
        
        Returns:
            Liste von Gap-Beschreibungen
        """
        gaps = []
        
        # 1. Prozesse ohne Beschreibung
        for node_id, node in self.knowledge_graph.nodes.items():
            if node.node_type == 'process':
                if not node.description or len(node.description.strip()) < 10:
                    gaps.append({
                        'type': 'missing_description',
                        'node_id': node_id,
                        'node_name': node.name,
                        'severity': 'medium',
                        'recommendation': 'Füge aussagekräftige Prozessbeschreibung hinzu'
                    })
        
        # 2. Prozesse ohne Tasks
        for node_id, node in self.knowledge_graph.nodes.items():
            if node.node_type == 'process':
                related_tasks = self.knowledge_graph.get_related_nodes(node_id, 'contains')
                if len(related_tasks) == 0:
                    gaps.append({
                        'type': 'missing_tasks',
                        'node_id': node_id,
                        'node_name': node.name,
                        'severity': 'high',
                        'recommendation': 'Definiere mindestens eine Aufgabe für diesen Prozess'
                    })
        
        # 3. Tasks ohne Verantwortliche
        for node_id, node in self.knowledge_graph.nodes.items():
            if node.node_type == 'task':
                if not node.metadata.get('responsible'):
                    gaps.append({
                        'type': 'missing_responsible',
                        'node_id': node_id,
                        'node_name': node.name,
                        'severity': 'medium',
                        'recommendation': 'Weise dieser Aufgabe eine verantwortliche Person/Rolle zu'
                    })
        
        # 4. Prozesse ohne rechtliche Grundlage
        for node_id, node in self.knowledge_graph.nodes.items():
            if node.node_type == 'process':
                related_regulations = self.knowledge_graph.get_related_nodes(node_id, 'governed_by')
                if len(related_regulations) == 0:
                    gaps.append({
                        'type': 'missing_legal_basis',
                        'node_id': node_id,
                        'node_name': node.name,
                        'severity': 'low',
                        'recommendation': 'Füge rechtliche Grundlagen hinzu (optional aber empfohlen)'
                    })
        
        # 5. Nodes ohne Embeddings
        if self.enable_embeddings:
            for node_id, node in self.knowledge_graph.nodes.items():
                if node.embeddings is None:
                    gaps.append({
                        'type': 'missing_embeddings',
                        'node_id': node_id,
                        'node_name': node.name,
                        'severity': 'low',
                        'recommendation': 'Generiere Embeddings für Semantic Search'
                    })
        
        logger.info(f"Knowledge Gaps erkannt: {len(gaps)}")
        
        return gaps
    
    def query_knowledge_graph(
        self,
        query: str,
        node_type: Optional[str] = None,
        top_k: int = 5
    ) -> List[ProcessKnowledgeNode]:
        """
        Query Knowledge Graph mit Semantic Search
        
        Args:
            query: Query-String
            node_type: Optional filter nach Node-Typ
            top_k: Anzahl Top-Ergebnisse
        
        Returns:
            Liste von relevanten Knowledge Nodes
        """
        if not self.enable_embeddings:
            logger.warning("Embeddings nicht aktiviert - Semantic Search nicht möglich")
            return []
        
        try:
            # Generiere Query Embedding
            query_embedding = self.embeddings_model.embed_query(query)
            
            # Berechne Similarity zu allen Nodes
            similarities = []
            for node_id, node in self.knowledge_graph.nodes.items():
                # Filter nach Node-Typ
                if node_type and node.node_type != node_type:
                    continue
                
                # Skip wenn keine Embeddings
                if node.embeddings is None:
                    continue
                
                # Cosine Similarity
                similarity = self._cosine_similarity(query_embedding, node.embeddings)
                similarities.append((node, similarity))
            
            # Sortiere nach Similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Return Top-K
            return [node for node, _ in similarities[:top_k]]
        
        except Exception as e:
            logger.error(f"Query fehlgeschlagen: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Berechne Cosine Similarity zwischen zwei Vektoren"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def export_knowledge_graph(self, output_path: Path):
        """
        Exportiere Knowledge Graph als JSON
        
        Args:
            output_path: Ausgabe-Pfad
        """
        export_data = {
            'nodes': [
                {
                    'id': node.node_id,
                    'type': node.node_type,
                    'name': node.name,
                    'description': node.description,
                    'metadata': node.metadata,
                    'tags': node.tags,
                    'has_embeddings': node.embeddings is not None
                }
                for node in self.knowledge_graph.nodes.values()
            ],
            'edges': [
                {
                    'source': source,
                    'target': target,
                    'relation': relation
                }
                for source, target, relation in self.knowledge_graph.edges
            ],
            'statistics': self.knowledge_graph.statistics
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Knowledge Graph exportiert: {output_path}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Hole DataMiner Statistiken"""
        return {
            'knowledge_graph': self.knowledge_graph.statistics,
            'embeddings_enabled': self.enable_embeddings,
            'total_processes': len([n for n in self.knowledge_graph.nodes.values() if n.node_type == 'process']),
            'total_tasks': len([n for n in self.knowledge_graph.nodes.values() if n.node_type == 'task']),
            'total_participants': len([n for n in self.knowledge_graph.nodes.values() if n.node_type == 'participant']),
            'total_regulations': len([n for n in self.knowledge_graph.nodes.values() if n.node_type == 'regulation'])
        }


def create_vpb_dataminer(
    polyglot_manager: Optional[UDS3PolyglotManager] = None,
    enable_embeddings: bool = True
) -> VPBRAGDataMiner:
    """
    Factory Function: Erstelle VPB RAG DataMiner
    
    Args:
        polyglot_manager: Optional UDS3PolyglotManager
        enable_embeddings: Aktiviere Embedding-Generierung
    
    Returns:
        VPBRAGDataMiner Instanz
    """
    return VPBRAGDataMiner(
        polyglot_manager=polyglot_manager,
        enable_embeddings=enable_embeddings
    )
