#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eu_ai_act.py

VCC-UDS3 EU AI Act Compliance Module
Part of v2.5.0 Governance & Compliance

Implementiert:
- EU AI Act Risikoklassifizierung (Art. 6, Anhang III)
- High-Risk AI System Requirements (Art. 9-15)
- Transparenzpflichten (Art. 13)
- Human Oversight (Art. 14)
- Konformitätsbewertung (Art. 43)
- Dokumentationspflichten (Art. 11)

Author: VCC Development Team
License: MIT with Government Partnership Commons Clause
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# Enums für EU AI Act Klassifizierung
# =============================================================================

class AIRiskCategory(Enum):
    """
    EU AI Act Risikokategorien (Art. 6, Anhang III).
    
    VCC-UDS3 klassifiziert als HIGH_RISK aufgrund:
    - Einsatz in öffentlicher Verwaltung
    - Rechtliche Entscheidungsunterstützung
    - Zugang zu öffentlichen Dienstleistungen
    """
    UNACCEPTABLE = 4  # Verboten (Art. 5)
    HIGH_RISK = 3     # Hohes Risiko (Art. 6, Anhang III)
    LIMITED_RISK = 2  # Begrenztes Risiko (Transparenzpflichten)
    MINIMAL_RISK = 1  # Minimales Risiko (keine Anforderungen)


class AISystemType(Enum):
    """Typen von KI-Systemen im VCC-Kontext."""
    LEGAL_RESEARCH = auto()      # Rechtsrecherche (Veritas)
    DOCUMENT_GENERATION = auto()  # Dokumentgenerierung
    DECISION_SUPPORT = auto()     # Entscheidungsunterstützung
    PROCESS_AUTOMATION = auto()   # Prozessautomatisierung
    KNOWLEDGE_RETRIEVAL = auto()  # Wissensabruf (RAG)


class TransparencyLevel(Enum):
    """Transparenzstufen für KI-Interaktionen."""
    FULL = auto()      # Vollständige Offenlegung
    STANDARD = auto()  # Standard-Hinweise
    MINIMAL = auto()   # Minimale Hinweise
    NONE = auto()      # Keine Transparenz erforderlich


class HumanOversightMode(Enum):
    """Modi der menschlichen Aufsicht (Art. 14)."""
    HUMAN_IN_THE_LOOP = auto()   # Mensch entscheidet
    HUMAN_ON_THE_LOOP = auto()   # Mensch überwacht
    HUMAN_OUT_OF_THE_LOOP = auto()  # Keine direkte Aufsicht


class ConformityStatus(Enum):
    """Konformitätsstatus."""
    CONFORMANT = auto()     # Konform
    NON_CONFORMANT = auto() # Nicht konform
    PENDING_REVIEW = auto() # Prüfung ausstehend
    EXEMPT = auto()         # Ausgenommen


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class AISystemMetadata:
    """
    Metadaten für ein KI-System gemäß EU AI Act Dokumentationspflichten.
    
    Entspricht Art. 11 (Technische Dokumentation).
    """
    system_id: UUID = field(default_factory=uuid4)
    name: str = ""
    version: str = ""
    description: str = ""
    system_type: AISystemType = AISystemType.KNOWLEDGE_RETRIEVAL
    risk_category: AIRiskCategory = AIRiskCategory.HIGH_RISK
    
    # Anbieter-Informationen
    provider_name: str = "VCC (Veritas-Covina-Clara)"
    provider_contact: str = ""
    
    # Technische Spezifikationen
    intended_purpose: str = ""
    capabilities: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    
    # Daten und Training
    training_data_description: str = ""
    training_methodology: str = ""
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Risikomanagement
    identified_risks: List[str] = field(default_factory=list)
    mitigation_measures: List[str] = field(default_factory=list)
    
    # Konformität
    conformity_status: ConformityStatus = ConformityStatus.PENDING_REVIEW
    last_assessment_date: Optional[datetime] = None
    next_assessment_due: Optional[datetime] = None
    
    # Audit
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TransparencyRecord:
    """
    Transparenzaufzeichnung für KI-Interaktionen (Art. 13).
    """
    record_id: UUID = field(default_factory=uuid4)
    session_id: str = ""
    user_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # KI-Interaktion
    ai_system_id: UUID = field(default_factory=uuid4)
    interaction_type: str = ""
    query: str = ""
    response_summary: str = ""
    
    # Transparenz-Disclosure
    disclosure_provided: bool = True
    disclosure_text: str = ""
    transparency_level: TransparencyLevel = TransparencyLevel.STANDARD
    
    # Erklärbarkeit
    explanation_available: bool = True
    explanation_requested: bool = False
    sources_provided: bool = True


@dataclass
class HumanOversightDecision:
    """
    Aufzeichnung menschlicher Aufsichtsentscheidungen (Art. 14).
    """
    decision_id: UUID = field(default_factory=uuid4)
    ai_system_id: UUID = field(default_factory=uuid4)
    session_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # AI-Empfehlung
    ai_recommendation: str = ""
    ai_confidence: float = 0.0
    
    # Menschliche Entscheidung
    oversight_mode: HumanOversightMode = HumanOversightMode.HUMAN_IN_THE_LOOP
    human_decision: str = ""
    human_override: bool = False
    override_reason: Optional[str] = None
    
    # Verantwortlicher
    decision_maker_id: str = ""
    decision_maker_role: str = ""


@dataclass
class ConformityAssessment:
    """
    Konformitätsbewertung gemäß Art. 43.
    """
    assessment_id: UUID = field(default_factory=uuid4)
    ai_system_id: UUID = field(default_factory=uuid4)
    assessment_date: datetime = field(default_factory=datetime.utcnow)
    assessor: str = ""
    
    # Bewertungsergebnisse
    overall_status: ConformityStatus = ConformityStatus.PENDING_REVIEW
    
    # Einzelne Anforderungen (Art. 9-15)
    risk_management_compliant: bool = False  # Art. 9
    data_governance_compliant: bool = False  # Art. 10
    documentation_compliant: bool = False    # Art. 11
    logging_compliant: bool = False          # Art. 12
    transparency_compliant: bool = False     # Art. 13
    human_oversight_compliant: bool = False  # Art. 14
    accuracy_compliant: bool = False         # Art. 15
    
    # Details
    findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    non_conformities: List[str] = field(default_factory=list)
    
    # Nächste Schritte
    remediation_deadline: Optional[datetime] = None
    next_assessment_date: Optional[datetime] = None


# =============================================================================
# EU AI Act Compliance Engine
# =============================================================================

class EUAIActComplianceEngine:
    """
    Engine für EU AI Act Compliance.
    
    Implementiert die Anforderungen für High-Risk AI Systems:
    - Risikomanagementsystem (Art. 9)
    - Daten-Governance (Art. 10)
    - Technische Dokumentation (Art. 11)
    - Protokollierung (Art. 12)
    - Transparenz (Art. 13)
    - Menschliche Aufsicht (Art. 14)
    - Genauigkeit und Robustheit (Art. 15)
    """
    
    def __init__(self):
        """Initialisiert die Compliance Engine."""
        self.ai_systems: Dict[UUID, AISystemMetadata] = {}
        self.transparency_records: List[TransparencyRecord] = []
        self.oversight_decisions: List[HumanOversightDecision] = []
        self.assessments: Dict[UUID, List[ConformityAssessment]] = {}
        
        # Standard-Transparenztexte
        self.disclosure_templates = self._setup_disclosure_templates()
    
    def _setup_disclosure_templates(self) -> Dict[str, str]:
        """Konfiguriert Standard-Transparenztexte."""
        return {
            "standard": (
                "Diese Antwort wurde mit Unterstützung eines KI-Systems (VCC-UDS3) "
                "generiert. Die Informationen basieren auf automatisierter Recherche "
                "in Rechtsdokumenten. Bitte überprüfen Sie wichtige rechtliche "
                "Entscheidungen mit einem Fachexperten."
            ),
            "legal_research": (
                "HINWEIS: Diese rechtliche Recherche wurde durch das VCC-Veritas "
                "KI-System unterstützt. Die angezeigten Quellen wurden automatisch "
                "aus der Rechtsdatenbank abgerufen. Die Interpretation und "
                "Anwendung obliegt dem verantwortlichen Juristen."
            ),
            "decision_support": (
                "ACHTUNG: Dies ist eine KI-gestützte Entscheidungsempfehlung. "
                "Die finale Entscheidung muss von einer autorisierten Person "
                "getroffen werden. Das KI-System dient nur zur Unterstützung."
            ),
            "document_generation": (
                "Dieses Dokument wurde mit KI-Unterstützung (VCC-Clara) erstellt. "
                "Bitte überprüfen Sie den Inhalt vor der Verwendung sorgfältig."
            )
        }
    
    # =========================================================================
    # AI System Registration (Art. 11 - Documentation)
    # =========================================================================
    
    def register_ai_system(
        self,
        name: str,
        description: str,
        system_type: AISystemType,
        intended_purpose: str,
        capabilities: List[str],
        limitations: List[str],
        training_data_description: str = "",
        training_methodology: str = "",
        version: str = "1.0.0"
    ) -> AISystemMetadata:
        """
        Registriert ein KI-System mit vollständiger Dokumentation.
        
        Args:
            name: Name des Systems
            description: Beschreibung
            system_type: Typ des KI-Systems
            intended_purpose: Bestimmungsgemäße Verwendung
            capabilities: Fähigkeiten
            limitations: Bekannte Einschränkungen
            training_data_description: Beschreibung der Trainingsdaten
            training_methodology: Trainingsmethodik
            version: Versionsnummer
            
        Returns:
            AISystemMetadata
        """
        # Risikokategorie basierend auf Typ bestimmen
        risk_category = self._determine_risk_category(system_type)
        
        metadata = AISystemMetadata(
            name=name,
            version=version,
            description=description,
            system_type=system_type,
            risk_category=risk_category,
            intended_purpose=intended_purpose,
            capabilities=capabilities,
            limitations=limitations,
            training_data_description=training_data_description,
            training_methodology=training_methodology,
            next_assessment_due=datetime.utcnow() + timedelta(days=365)
        )
        
        self.ai_systems[metadata.system_id] = metadata
        self.assessments[metadata.system_id] = []
        
        logger.info(
            f"Registered AI system: {name} (ID: {metadata.system_id}), "
            f"Risk: {risk_category.name}"
        )
        
        return metadata
    
    def _determine_risk_category(self, system_type: AISystemType) -> AIRiskCategory:
        """Bestimmt die Risikokategorie basierend auf dem Systemtyp."""
        # VCC-Systeme im Verwaltungskontext sind typischerweise HIGH_RISK
        high_risk_types = {
            AISystemType.DECISION_SUPPORT,
            AISystemType.LEGAL_RESEARCH,
            AISystemType.DOCUMENT_GENERATION
        }
        
        if system_type in high_risk_types:
            return AIRiskCategory.HIGH_RISK
        elif system_type == AISystemType.PROCESS_AUTOMATION:
            return AIRiskCategory.LIMITED_RISK
        else:
            return AIRiskCategory.LIMITED_RISK
    
    # =========================================================================
    # Transparency (Art. 13)
    # =========================================================================
    
    def record_interaction(
        self,
        ai_system_id: UUID,
        session_id: str,
        user_id: str,
        interaction_type: str,
        query: str,
        response_summary: str,
        transparency_level: TransparencyLevel = TransparencyLevel.STANDARD,
        sources_provided: bool = True
    ) -> TransparencyRecord:
        """
        Zeichnet eine KI-Interaktion mit Transparenz-Disclosure auf.
        
        Args:
            ai_system_id: ID des KI-Systems
            session_id: Session-ID
            user_id: Benutzer-ID (anonymisiert)
            interaction_type: Art der Interaktion
            query: Anfrage
            response_summary: Zusammenfassung der Antwort
            transparency_level: Transparenzstufe
            sources_provided: Wurden Quellen angegeben
            
        Returns:
            TransparencyRecord
        """
        # Passenden Disclosure-Text wählen
        system = self.ai_systems.get(ai_system_id)
        if system:
            template_key = {
                AISystemType.LEGAL_RESEARCH: "legal_research",
                AISystemType.DECISION_SUPPORT: "decision_support",
                AISystemType.DOCUMENT_GENERATION: "document_generation"
            }.get(system.system_type, "standard")
        else:
            template_key = "standard"
        
        disclosure_text = self.disclosure_templates.get(template_key, "")
        
        record = TransparencyRecord(
            session_id=session_id,
            user_id=user_id,
            ai_system_id=ai_system_id,
            interaction_type=interaction_type,
            query=query,
            response_summary=response_summary[:500],  # Truncate für Privacy
            disclosure_provided=True,
            disclosure_text=disclosure_text,
            transparency_level=transparency_level,
            sources_provided=sources_provided
        )
        
        self.transparency_records.append(record)
        
        return record
    
    def get_disclosure_text(
        self,
        system_type: AISystemType,
        custom_context: Optional[str] = None
    ) -> str:
        """
        Gibt den passenden Transparenz-Hinweis zurück.
        
        Args:
            system_type: Typ des KI-Systems
            custom_context: Optionaler Kontext für angepassten Text
            
        Returns:
            Disclosure-Text
        """
        template_key = {
            AISystemType.LEGAL_RESEARCH: "legal_research",
            AISystemType.DECISION_SUPPORT: "decision_support",
            AISystemType.DOCUMENT_GENERATION: "document_generation"
        }.get(system_type, "standard")
        
        base_text = self.disclosure_templates.get(template_key, "")
        
        if custom_context:
            return f"{base_text}\n\nKontext: {custom_context}"
        
        return base_text
    
    # =========================================================================
    # Human Oversight (Art. 14)
    # =========================================================================
    
    def record_oversight_decision(
        self,
        ai_system_id: UUID,
        session_id: str,
        ai_recommendation: str,
        ai_confidence: float,
        human_decision: str,
        decision_maker_id: str,
        decision_maker_role: str,
        human_override: bool = False,
        override_reason: Optional[str] = None,
        oversight_mode: HumanOversightMode = HumanOversightMode.HUMAN_IN_THE_LOOP
    ) -> HumanOversightDecision:
        """
        Zeichnet eine menschliche Aufsichtsentscheidung auf.
        
        Args:
            ai_system_id: ID des KI-Systems
            session_id: Session-ID
            ai_recommendation: KI-Empfehlung
            ai_confidence: Konfidenz der KI
            human_decision: Menschliche Entscheidung
            decision_maker_id: ID des Entscheiders
            decision_maker_role: Rolle des Entscheiders
            human_override: Wurde KI überstimmt
            override_reason: Begründung für Override
            oversight_mode: Aufsichtsmodus
            
        Returns:
            HumanOversightDecision
        """
        decision = HumanOversightDecision(
            ai_system_id=ai_system_id,
            session_id=session_id,
            ai_recommendation=ai_recommendation,
            ai_confidence=ai_confidence,
            oversight_mode=oversight_mode,
            human_decision=human_decision,
            human_override=human_override,
            override_reason=override_reason,
            decision_maker_id=decision_maker_id,
            decision_maker_role=decision_maker_role
        )
        
        self.oversight_decisions.append(decision)
        
        if human_override:
            logger.info(
                f"Human override recorded: System {ai_system_id}, "
                f"Reason: {override_reason}"
            )
        
        return decision
    
    def get_override_statistics(
        self,
        ai_system_id: Optional[UUID] = None,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Gibt Statistiken zu menschlichen Overrides zurück.
        
        Args:
            ai_system_id: Optional - nur für dieses System
            since: Optional - nur seit diesem Datum
            
        Returns:
            Statistik-Dictionary
        """
        decisions = self.oversight_decisions
        
        if ai_system_id:
            decisions = [d for d in decisions if d.ai_system_id == ai_system_id]
        
        if since:
            decisions = [d for d in decisions if d.timestamp >= since]
        
        total = len(decisions)
        overrides = sum(1 for d in decisions if d.human_override)
        
        return {
            "total_decisions": total,
            "total_overrides": overrides,
            "override_rate": overrides / total if total > 0 else 0.0,
            "by_oversight_mode": self._group_by_oversight_mode(decisions),
            "common_override_reasons": self._get_common_reasons(decisions)
        }
    
    def _group_by_oversight_mode(
        self,
        decisions: List[HumanOversightDecision]
    ) -> Dict[str, int]:
        """Gruppiert Entscheidungen nach Aufsichtsmodus."""
        result: Dict[str, int] = {}
        for d in decisions:
            mode = d.oversight_mode.name
            result[mode] = result.get(mode, 0) + 1
        return result
    
    def _get_common_reasons(
        self,
        decisions: List[HumanOversightDecision]
    ) -> List[str]:
        """Extrahiert häufige Override-Gründe."""
        reasons = [d.override_reason for d in decisions if d.override_reason]
        return list(set(reasons))[:10]  # Top 10
    
    # =========================================================================
    # Conformity Assessment (Art. 43)
    # =========================================================================
    
    def perform_conformity_assessment(
        self,
        ai_system_id: UUID,
        assessor: str
    ) -> ConformityAssessment:
        """
        Führt eine Konformitätsbewertung durch.
        
        Args:
            ai_system_id: ID des zu bewertenden Systems
            assessor: Name des Bewerters
            
        Returns:
            ConformityAssessment
        """
        system = self.ai_systems.get(ai_system_id)
        if not system:
            raise ValueError(f"AI System {ai_system_id} not found")
        
        assessment = ConformityAssessment(
            ai_system_id=ai_system_id,
            assessor=assessor
        )
        
        findings = []
        recommendations = []
        non_conformities = []
        
        # Art. 9 - Risikomanagementsystem
        if system.identified_risks and system.mitigation_measures:
            assessment.risk_management_compliant = True
        else:
            assessment.risk_management_compliant = False
            non_conformities.append(
                "Art. 9: Risikomanagement unvollständig dokumentiert"
            )
            recommendations.append(
                "Identifizierte Risiken und Mitigationsmaßnahmen dokumentieren"
            )
        
        # Art. 10 - Daten-Governance
        if system.training_data_description:
            assessment.data_governance_compliant = True
        else:
            assessment.data_governance_compliant = False
            non_conformities.append(
                "Art. 10: Trainingsdaten nicht dokumentiert"
            )
        
        # Art. 11 - Technische Dokumentation
        if (system.description and system.intended_purpose and 
            system.capabilities and system.limitations):
            assessment.documentation_compliant = True
        else:
            assessment.documentation_compliant = False
            non_conformities.append(
                "Art. 11: Technische Dokumentation unvollständig"
            )
        
        # Art. 12 - Protokollierung
        # Prüfen ob Transparency Records vorhanden
        system_records = [
            r for r in self.transparency_records 
            if r.ai_system_id == ai_system_id
        ]
        if len(system_records) > 0:
            assessment.logging_compliant = True
        else:
            assessment.logging_compliant = False
            findings.append("Art. 12: Keine Protokollierung aktiv")
        
        # Art. 13 - Transparenz
        # Prüfen ob Disclosures konfiguriert
        if system.system_type.name.lower() in [
            k for k in self.disclosure_templates.keys()
        ] or "standard" in self.disclosure_templates:
            assessment.transparency_compliant = True
        else:
            assessment.transparency_compliant = False
            non_conformities.append(
                "Art. 13: Transparenzhinweise nicht konfiguriert"
            )
        
        # Art. 14 - Menschliche Aufsicht
        # Prüfen ob Oversight-Entscheidungen aufgezeichnet werden
        system_oversight = [
            d for d in self.oversight_decisions 
            if d.ai_system_id == ai_system_id
        ]
        if len(system_oversight) > 0 or system.risk_category != AIRiskCategory.HIGH_RISK:
            assessment.human_oversight_compliant = True
        else:
            assessment.human_oversight_compliant = False
            recommendations.append(
                "Art. 14: Human Oversight Prozesse implementieren"
            )
        
        # Art. 15 - Genauigkeit und Robustheit
        if system.performance_metrics:
            assessment.accuracy_compliant = True
        else:
            assessment.accuracy_compliant = False
            non_conformities.append(
                "Art. 15: Performance-Metriken nicht dokumentiert"
            )
        
        # Gesamtstatus
        all_compliant = all([
            assessment.risk_management_compliant,
            assessment.data_governance_compliant,
            assessment.documentation_compliant,
            assessment.logging_compliant,
            assessment.transparency_compliant,
            assessment.human_oversight_compliant,
            assessment.accuracy_compliant
        ])
        
        if all_compliant:
            assessment.overall_status = ConformityStatus.CONFORMANT
        elif len(non_conformities) > 3:
            assessment.overall_status = ConformityStatus.NON_CONFORMANT
            assessment.remediation_deadline = datetime.utcnow() + timedelta(days=90)
        else:
            assessment.overall_status = ConformityStatus.PENDING_REVIEW
        
        assessment.findings = findings
        assessment.recommendations = recommendations
        assessment.non_conformities = non_conformities
        assessment.next_assessment_date = datetime.utcnow() + timedelta(days=365)
        
        # Speichern
        if ai_system_id not in self.assessments:
            self.assessments[ai_system_id] = []
        self.assessments[ai_system_id].append(assessment)
        
        # System aktualisieren
        system.conformity_status = assessment.overall_status
        system.last_assessment_date = assessment.assessment_date
        system.updated_at = datetime.utcnow()
        
        logger.info(
            f"Conformity assessment completed for {system.name}: "
            f"{assessment.overall_status.name}"
        )
        
        return assessment
    
    def get_compliance_report(
        self,
        ai_system_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Generiert einen EU AI Act Compliance Report.
        
        Args:
            ai_system_id: Optional - nur für dieses System
            
        Returns:
            Compliance Report Dictionary
        """
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "report_type": "EU_AI_ACT_COMPLIANCE",
            "systems": []
        }
        
        systems = (
            [self.ai_systems[ai_system_id]] if ai_system_id 
            else list(self.ai_systems.values())
        )
        
        for system in systems:
            assessments = self.assessments.get(system.system_id, [])
            latest_assessment = assessments[-1] if assessments else None
            
            system_report = {
                "system_id": str(system.system_id),
                "name": system.name,
                "version": system.version,
                "risk_category": system.risk_category.name,
                "system_type": system.system_type.name,
                "conformity_status": system.conformity_status.name,
                "last_assessment": (
                    system.last_assessment_date.isoformat() 
                    if system.last_assessment_date else None
                ),
                "next_assessment_due": (
                    system.next_assessment_due.isoformat() 
                    if system.next_assessment_due else None
                ),
                "transparency_records_count": sum(
                    1 for r in self.transparency_records 
                    if r.ai_system_id == system.system_id
                ),
                "oversight_decisions_count": sum(
                    1 for d in self.oversight_decisions 
                    if d.ai_system_id == system.system_id
                )
            }
            
            if latest_assessment:
                system_report["latest_assessment_details"] = {
                    "date": latest_assessment.assessment_date.isoformat(),
                    "assessor": latest_assessment.assessor,
                    "status": latest_assessment.overall_status.name,
                    "non_conformities": len(latest_assessment.non_conformities),
                    "recommendations": len(latest_assessment.recommendations)
                }
            
            report["systems"].append(system_report)
        
        # Aggregierte Statistiken
        total_systems = len(systems)
        conformant = sum(
            1 for s in systems 
            if s.conformity_status == ConformityStatus.CONFORMANT
        )
        
        report["summary"] = {
            "total_systems": total_systems,
            "conformant_systems": conformant,
            "conformity_rate": conformant / total_systems if total_systems > 0 else 0,
            "high_risk_systems": sum(
                1 for s in systems 
                if s.risk_category == AIRiskCategory.HIGH_RISK
            ),
            "total_transparency_records": len(self.transparency_records),
            "total_oversight_decisions": len(self.oversight_decisions)
        }
        
        return report


# =============================================================================
# Factory Functions
# =============================================================================

def create_eu_ai_act_engine() -> EUAIActComplianceEngine:
    """
    Erstellt eine EU AI Act Compliance Engine.
    
    Returns:
        Konfigurierte EUAIActComplianceEngine
    """
    return EUAIActComplianceEngine()


def register_vcc_systems(engine: EUAIActComplianceEngine) -> Dict[str, UUID]:
    """
    Registriert die VCC-Systeme (Veritas, Covina, Clara).
    
    Args:
        engine: EU AI Act Compliance Engine
        
    Returns:
        Dictionary mit System-IDs
    """
    system_ids = {}
    
    # Veritas - Legal Research
    veritas = engine.register_ai_system(
        name="VCC-Veritas",
        description=(
            "Rechtlicher KI-Assistent für die öffentliche Verwaltung. "
            "Unterstützt Mitarbeiter bei der Recherche von Rechtsfragen "
            "durch RAG-basierte Wissensabfrage."
        ),
        system_type=AISystemType.LEGAL_RESEARCH,
        intended_purpose=(
            "Unterstützung von Verwaltungsmitarbeitern bei der rechtlichen "
            "Recherche und Entscheidungsfindung. Nicht für autonome "
            "Rechtsentscheidungen vorgesehen."
        ),
        capabilities=[
            "Semantische Suche in Rechtsdatenbanken",
            "Quellenbasierte Antwortgenerierung (RAG)",
            "Multi-Hop Reasoning über Rechtshierarchien",
            "Zitieren relevanter Rechtsgrundlagen"
        ],
        limitations=[
            "Keine autonome Rechtsentscheidung",
            "Erfordert menschliche Überprüfung",
            "Abhängig von Aktualität der Datenbasis",
            "Kann Kontext missverstehen"
        ],
        training_data_description=(
            "Öffentlich zugängliche Gesetzestexte, Verordnungen, "
            "Verwaltungsvorschriften und Gerichtsentscheidungen."
        ),
        training_methodology="RAG mit vortrainierten Sprachmodellen"
    )
    system_ids["veritas"] = veritas.system_id
    
    # Clara - Document Generation
    clara = engine.register_ai_system(
        name="VCC-Clara",
        description=(
            "KI-System zur Unterstützung der Dokumentenerstellung "
            "in der öffentlichen Verwaltung."
        ),
        system_type=AISystemType.DOCUMENT_GENERATION,
        intended_purpose=(
            "Assistenz bei der Erstellung von Verwaltungsdokumenten "
            "unter menschlicher Aufsicht."
        ),
        capabilities=[
            "Vorlagengenerierung",
            "Textvorschläge basierend auf Kontext",
            "Konsistenzprüfung"
        ],
        limitations=[
            "Generierter Text erfordert Review",
            "Domänenspezifisches Training notwendig",
            "Kann formale Fehler enthalten"
        ],
        training_data_description=(
            "Anonymisierte Verwaltungsdokumente und Vorlagen."
        ),
        training_methodology="Fine-Tuning mit PEFT/LoRA"
    )
    system_ids["clara"] = clara.system_id
    
    # Covina - Process Automation
    covina = engine.register_ai_system(
        name="VCC-Covina",
        description=(
            "Prozessautomatisierung und Workflow-Management "
            "für die öffentliche Verwaltung."
        ),
        system_type=AISystemType.PROCESS_AUTOMATION,
        intended_purpose=(
            "Automatisierung routinemäßiger Verwaltungsprozesse "
            "mit menschlicher Aufsicht für Entscheidungen."
        ),
        capabilities=[
            "Workflow-Automatisierung",
            "Aufgabenverteilung",
            "Fristüberwachung"
        ],
        limitations=[
            "Keine autonomen Entscheidungen",
            "Erfordert Prozessdefinitionen",
            "Abhängig von korrekter Konfiguration"
        ],
        training_data_description="Prozessmodelle und Workflow-Definitionen",
        training_methodology="Regelbasiert mit ML-Unterstützung"
    )
    system_ids["covina"] = covina.system_id
    
    return system_ids


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "AIRiskCategory",
    "AISystemType",
    "TransparencyLevel",
    "HumanOversightMode",
    "ConformityStatus",
    # Data Models
    "AISystemMetadata",
    "TransparencyRecord",
    "HumanOversightDecision",
    "ConformityAssessment",
    # Engine
    "EUAIActComplianceEngine",
    # Factory Functions
    "create_eu_ai_act_engine",
    "register_vcc_systems",
]
