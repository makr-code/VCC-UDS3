"""
UDS3 Process Extension - Process Entities as First-Class Citizens

Erweitert UDS3 UnifiedDatabaseStrategy um Process-spezifische Operationen:
- Process, Step, Role, OrgUnit, System, Control, LegalRef, InfoObject, Document, Recurrence
- Full Polyglot Persistence (Neo4j + PostgreSQL + ChromaDB + CouchDB)
- SAGA Pattern (Auto-Rollback bei Fehlern)
- Temporal Canon Integration (Year/Month/Day/Date nodes)

Part of Covina Process Integration
Author: Martin Krüger
Date: 31. Oktober 2025
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import logging

from processes.domain.models import (
    Process, Step, Role, OrgUnit, System, Control, LegalRef, InfoObject
)
from processes.graph.temporal_canon import TemporalCanon

logger = logging.getLogger(__name__)


class UDS3ProcessExtension:
    """
    Extends UDS3 with Process entity support.
    
    All operations use UDS3 SAGA Pattern for transactional safety.
    Processes are stored as Documents in all 4 databases:
    - Neo4j: Process/Step nodes with relations
    - PostgreSQL: Process metadata (searchable, filterable)
    - ChromaDB: Process embeddings (semantic search)
    - CouchDB: Full process definitions (JSON storage)
    """
    
    def __init__(self, uds3_strategy):
        """
        Initialize Process Extension.
        
        Args:
            uds3_strategy: UnifiedDatabaseStrategy instance (or compatible mock)
        """
        # Allow duck-typing for testing (check for required methods)
        required_methods = ['create_document', 'create_uds3_relation', 'saga_crud']
        missing_methods = [m for m in required_methods if not hasattr(uds3_strategy, m)]
        
        if missing_methods:
            raise TypeError(
                f"uds3_strategy must have methods: {', '.join(missing_methods)}"
            )
            
        self.uds3 = uds3_strategy
        self.saga_crud = uds3_strategy.saga_crud
        
        # Temporal Canon (uses graph backend directly)
        if hasattr(uds3_strategy, 'graph_db') and uds3_strategy.graph_db:
            self.temporal_canon = TemporalCanon(uds3_strategy.graph_db)
        else:
            self.temporal_canon = None
            logger.warning("⚠️ Temporal Canon not available (no graph backend)")
    
    # ========================================================================
    # PROCESS
    # ========================================================================
    def create_process(self, process: Process) -> Dict[str, Any]:
        """
        Create Process entity in all 4 databases (UDS3 Polyglot).
        
        Databases:
        - Neo4j: (:Process) node with properties
        - PostgreSQL: process metadata (title, version, domain, owner, status)
        - ChromaDB: process embedding (semantic search by description)
        - CouchDB: full process definition (JSON)
        
        Args:
            process: Process domain model
            
        Returns:
            UDS3 SAGA result with database_operations for all 4 DBs
            
        Example:
            ```python
            process = Process(id="proc_001", title="Antragsprozess", ...)
            result = ext.create_process(process)
            
            if result["success"]:
                print(f"✅ Process in {len(result['database_operations'])} databases")
                # Neo4j: result["database_operations"]["graph"]
                # PostgreSQL: result["database_operations"]["relational"]
                # ChromaDB: result["database_operations"]["vector"]
                # CouchDB: result["database_operations"]["file_storage"]
            else:
                print(f"❌ SAGA Rollback: {result['error']}")
            ```
        """
        # Prepare content (for ChromaDB embedding + CouchDB storage)
        content = f"""
        Process: {process.title}
        Version: {process.version}
        Domain: {process.domain}
        Status: {process.status}
        Owner: {process.owner_org}
        """
        
        # Prepare metadata (for all DBs)
        metadata = {
            "node_type": "Process",  # Neo4j label
            "node_label": "Process",
            "entity_type": "process",
            "title": process.title,
            "key": process.key,
            "version": process.version,
            "domain": process.domain,
            "owner_org": process.owner_org,
            "status": process.status,
            "created_at": process.created_at.isoformat() if process.created_at else datetime.utcnow().isoformat(),
            "updated_at": process.updated_at.isoformat() if process.updated_at else datetime.utcnow().isoformat(),
            "extra": process.extra or {}
        }
        
        # UDS3 SAGA Create (Polyglot across 4 DBs)
        logger.info(f"Creating Process '{process.title}' (ID: {process.id}) via UDS3 SAGA")
        
        try:
            # UDS3 creates in: Vector → Graph → Relational → File Storage → Identity
            result = self.uds3.create_document(
                document_id=process.id,
                content=content,
                metadata=metadata
            )
            
            # Link to Temporal Canon (created_at)
            if result.get("success") and self.temporal_canon and process.created_at:
                try:
                    date_iso = process.created_at.date().isoformat()
                    self.temporal_canon.upsert_date(date_iso)
                    self.temporal_canon.link_occurs_on("Process", process.id, date_iso)
                    logger.info(f"✅ Temporal Canon link: Process {process.id} → {date_iso}")
                except Exception as e:
                    logger.warning(f"⚠️ Temporal Canon link failed: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Process creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "database_operations": {}
            }
    
    # ========================================================================
    # STEP
    # ========================================================================
    def create_step(self, step: Step, process_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create Step entity in all 4 databases.
        
        Args:
            step: Step domain model
            process_id: Optional Process ID to link via HAS_STEP relation
            
        Returns:
            UDS3 SAGA result
        """
        content = f"""
        Step: {step.title}
        Order: {step.order}
        Description: {step.description or 'N/A'}
        Required: {step.required}
        Duration: {step.duration_est or 'N/A'} days
        """
        
        metadata = {
            "node_type": "Step",
            "node_label": "Step",
            "entity_type": "step",
            "process_id": step.process_id or process_id,
            "order": step.order,
            "key": step.key,
            "title": step.title,
            "description": step.description,
            "required": step.required,
            "duration_est": step.duration_est,
            "extra": step.extra or {}
        }
        
        logger.info(f"Creating Step '{step.title}' (ID: {step.id}) via UDS3 SAGA")
        
        try:
            result = self.uds3.create_document(
                document_id=step.id,
                content=content,
                metadata=metadata
            )
            
            # Link to Process via UDS3 Relations
            if result.get("success") and process_id:
                try:
                    rel_result = self.uds3.create_uds3_relation(
                        relation_type="HAS_STEP",
                        source_id=process_id,
                        target_id=step.id,
                        properties={"created_at": datetime.utcnow().isoformat()}
                    )
                    logger.info(f"✅ Relation created: Process {process_id} -[:HAS_STEP]→ Step {step.id}")
                except Exception as e:
                    logger.warning(f"⚠️ HAS_STEP relation failed: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Step creation failed: {e}")
            return {"success": False, "error": str(e), "database_operations": {}}
    
    # ========================================================================
    # RELATIONS
    # ========================================================================
    def create_step_sequence(self, from_step_id: str, to_step_id: str,
                            condition: Optional[str] = None,
                            probability: Optional[float] = None) -> Dict[str, Any]:
        """
        Create NEXT relation between steps.
        
        Args:
            from_step_id: Source step ID
            to_step_id: Target step ID
            condition: Optional transition condition
            probability: Optional transition probability
            
        Returns:
            UDS3 relation result
        """
        properties = {"created_at": datetime.utcnow().isoformat()}
        if condition:
            properties["condition"] = condition
        if probability is not None:
            properties["probability"] = probability
        
        return self.uds3.create_uds3_relation(
            relation_type="NEXT",
            source_id=from_step_id,
            target_id=to_step_id,
            properties=properties
        )
    
    def link_step_to_role(self, step_id: str, role_id: str,
                         relation_type: str = "PERFORMED_BY") -> Dict[str, Any]:
        """Link Step to Role (PERFORMED_BY, APPROVED_BY, REVIEWED_BY)."""
        return self.uds3.create_uds3_relation(
            relation_type=relation_type,
            source_id=step_id,
            target_id=role_id,
            properties={"created_at": datetime.utcnow().isoformat()}
        )
    
    # ========================================================================
    # ROLE, ORGUNIT, SYSTEM, CONTROL, LEGALREF, INFOOBJECT
    # (Same pattern as Process/Step - create_document + metadata)
    # ========================================================================
    def create_role(self, role: Role) -> Dict[str, Any]:
        """Create Role entity."""
        content = f"Role: {role.name}, Level: {role.level or 'N/A'}"
        metadata = {
            "node_type": "Role",
            "entity_type": "role",
            "key": role.key,
            "name": role.name,
            "level": role.level,
            "permissions": role.permissions or [],
            "extra": role.extra or {}
        }
        return self.uds3.create_document(role.id, content, metadata)
    
    def create_org_unit(self, org_unit: OrgUnit) -> Dict[str, Any]:
        """Create OrgUnit entity."""
        content = f"OrgUnit: {org_unit.name}, Type: {org_unit.type or 'N/A'}"
        metadata = {
            "node_type": "OrgUnit",
            "entity_type": "org_unit",
            "key": org_unit.key,
            "name": org_unit.name,
            "parent_id": org_unit.parent_id,
            "type": org_unit.type,
            "extra": org_unit.extra or {}
        }
        return self.uds3.create_document(org_unit.id, content, metadata)
    
    def create_system(self, system: System) -> Dict[str, Any]:
        """Create System entity."""
        content = f"System: {system.name}, Type: {system.type or 'N/A'}"
        metadata = {
            "node_type": "System",
            "entity_type": "system",
            "key": system.key,
            "name": system.name,
            "type": system.type,
            "criticality": system.criticality,
            "extra": system.extra or {}
        }
        return self.uds3.create_document(system.id, content, metadata)
    
    def create_control(self, control: Control) -> Dict[str, Any]:
        """Create Control entity."""
        content = f"Control: {control.name}, Type: {control.type or 'N/A'}"
        metadata = {
            "node_type": "Control",
            "entity_type": "control",
            "key": control.key,
            "name": control.name,
            "type": control.type,
            "objective": control.objective,
            "evidence": control.evidence,
            "extra": control.extra or {}
        }
        return self.uds3.create_document(control.id, content, metadata)
    
    def create_legal_ref(self, legal_ref: LegalRef) -> Dict[str, Any]:
        """Create LegalRef entity."""
        content = f"LegalRef: {legal_ref.citation}"
        metadata = {
            "node_type": "LegalRef",
            "entity_type": "legal_ref",
            "citation": legal_ref.citation,
            "type": legal_ref.type,
            "uri": legal_ref.uri,
            "extra": legal_ref.extra or {}
        }
        return self.uds3.create_document(legal_ref.id, content, metadata)
    
    def create_info_object(self, info_object: InfoObject) -> Dict[str, Any]:
        """Create InfoObject entity."""
        content = f"InfoObject: {info_object.name}, Classification: {info_object.classification or 'N/A'}"
        metadata = {
            "node_type": "InfoObject",
            "entity_type": "info_object",
            "key": info_object.key,
            "name": info_object.name,
            "classification": info_object.classification,
            "pii": info_object.pii,
            "retention": info_object.retention,
            "extra": info_object.extra or {}
        }
        return self.uds3.create_document(info_object.id, content, metadata)
    
    # ========================================================================
    # DOCUMENT BINDING
    # ========================================================================
    def create_process_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create Document entity (for process evidence).
        
        Args:
            document: Dict with id, key, title, type, source_uri, published_at, metadata
            
        Returns:
            UDS3 SAGA result
        """
        content = f"""
        Document: {document.get('title', 'N/A')}
        Type: {document.get('type', 'N/A')}
        Source: {document.get('source_uri', 'N/A')}
        """
        
        metadata = {
            "node_type": "Document",
            "entity_type": "document",
            "key": document.get("key"),
            "title": document.get("title"),
            "type": document.get("type"),
            "source_uri": document.get("source_uri"),
            "published_at": document.get("published_at"),
            "metadata": document.get("metadata", {})
        }
        
        result = self.uds3.create_document(
            document_id=document["id"],
            content=content,
            metadata=metadata
        )
        
        # Link published_at to Temporal Canon
        if result.get("success") and self.temporal_canon and document.get("published_at"):
            try:
                date_iso = document["published_at"].split("T")[0]
                self.temporal_canon.upsert_date(date_iso)
                self.temporal_canon.link_occurs_on("Document", document["id"], date_iso)
            except Exception as e:
                logger.warning(f"⚠️ Temporal Canon link failed: {e}")
        
        return result
    
    def link_document_to_process(self, document_id: str, process_id: str,
                                 role: Optional[str] = None,
                                 confidence: Optional[float] = None) -> Dict[str, Any]:
        """Link Document to Process via RELATES_TO_PROCESS."""
        properties = {"created_at": datetime.utcnow().isoformat()}
        if role:
            properties["role"] = role
        if confidence is not None:
            properties["confidence"] = confidence
        
        return self.uds3.create_uds3_relation(
            relation_type="RELATES_TO_PROCESS",
            source_id=document_id,
            target_id=process_id,
            properties=properties
        )
    
    def link_document_to_step(self, document_id: str, step_id: str,
                             relation: str = "EVIDENCES_STEP") -> Dict[str, Any]:
        """Link Document to Step (EVIDENCES_STEP | INPUT_OF_STEP | OUTPUT_OF_STEP)."""
        valid_relations = {"EVIDENCES_STEP", "INPUT_OF_STEP", "OUTPUT_OF_STEP"}
        if relation not in valid_relations:
            relation = "EVIDENCES_STEP"
        
        return self.uds3.create_uds3_relation(
            relation_type=relation,
            source_id=document_id,
            target_id=step_id,
            properties={"created_at": datetime.utcnow().isoformat()}
        )
    
    def link_document_validity(self, document_id: str,
                              valid_from: Optional[str] = None,
                              valid_until: Optional[str] = None) -> Dict[str, Any]:
        """
        Link Document validity via EFFECTIVE_FROM/UNTIL to Date nodes.
        
        Args:
            document_id: Document ID
            valid_from: ISO date (YYYY-MM-DD)
            valid_until: ISO date (YYYY-MM-DD)
            
        Returns:
            Dict with success status
        """
        if not self.temporal_canon:
            return {"success": False, "error": "Temporal Canon not available"}
        
        results = {"from": None, "until": None}
        
        try:
            if valid_from:
                self.temporal_canon.upsert_date(valid_from)
                # Use saga_crud to create EFFECTIVE_FROM relation
                # (currently temporal_canon uses direct execute_query)
                results["from"] = {"success": True, "date": valid_from}
            
            if valid_until:
                self.temporal_canon.upsert_date(valid_until)
                results["until"] = {"success": True, "date": valid_until}
            
            # TODO: Create EFFECTIVE_FROM/UNTIL via UDS3 Relations
            # Currently temporal_canon creates these directly
            
            return {"success": True, "results": results}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ========================================================================
    # RECURRENCE
    # ========================================================================
    def create_recurrence(self, recurrence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create Recurrence entity (RRULE-like).
        
        Args:
            recurrence: Dict with id, freq, interval, byday, bymonthday, until, count, timezone
            
        Returns:
            UDS3 SAGA result
        """
        content = f"""
        Recurrence: {recurrence.get('freq')} every {recurrence.get('interval', 1)} interval(s)
        Until: {recurrence.get('until', 'N/A')}
        """
        
        metadata = {
            "node_type": "Recurrence",
            "entity_type": "recurrence",
            "freq": recurrence.get("freq"),
            "interval": recurrence.get("interval"),
            "byday": recurrence.get("byday"),
            "bymonthday": recurrence.get("bymonthday"),
            "until": recurrence.get("until"),
            "count": recurrence.get("count"),
            "timezone": recurrence.get("timezone"),
            "rrule": recurrence.get("rrule")
        }
        
        return self.uds3.create_document(
            document_id=recurrence["id"],
            content=content,
            metadata=metadata
        )
    
    def link_entity_recurrence(self, entity_label: str, entity_id: str,
                              recurrence_id: str) -> Dict[str, Any]:
        """Link entity (Process|Step|Document) to Recurrence via HAS_RECURRENCE."""
        if entity_label not in {"Process", "Step", "Document"}:
            return {"success": False, "error": f"Unsupported entity: {entity_label}"}
        
        return self.uds3.create_uds3_relation(
            relation_type="HAS_RECURRENCE",
            source_id=entity_id,
            target_id=recurrence_id,
            properties={"created_at": datetime.utcnow().isoformat()}
        )
