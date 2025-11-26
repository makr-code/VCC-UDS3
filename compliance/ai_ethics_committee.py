#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai_ethics_committee.py

VCC-UDS3 AI Ethics Committee Integration
Part of v2.5.0 Governance & Compliance

Implementiert:
- AI Ethics Committee Workflow
- Ethische Prüfungsanfragen
- Entscheidungsdokumentation
- Eskalationspfade
- Periodische Reviews

Author: VCC Development Team
License: MIT with Government Partnership Commons Clause
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================

class ReviewType(Enum):
    """Typen von Ethik-Reviews."""
    INITIAL_ASSESSMENT = auto()    # Erstbewertung neuer KI-Systeme
    PERIODIC_REVIEW = auto()       # Periodische Überprüfung
    INCIDENT_REVIEW = auto()       # Vorfallsbasierte Prüfung
    CHANGE_ASSESSMENT = auto()     # Bewertung bei Änderungen
    BIAS_ESCALATION = auto()       # Eskalation von Bias-Alerts
    COMPLAINT_INVESTIGATION = auto()  # Beschwerdeverfahren


class ReviewStatus(Enum):
    """Status eines Ethics Reviews."""
    SUBMITTED = auto()
    ASSIGNED = auto()
    IN_REVIEW = auto()
    PENDING_DECISION = auto()
    APPROVED = auto()
    APPROVED_WITH_CONDITIONS = auto()
    REJECTED = auto()
    DEFERRED = auto()


class RiskLevel(Enum):
    """Ethische Risikostufe."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class CommitteeRole(Enum):
    """Rollen im AI Ethics Committee."""
    CHAIR = auto()
    MEMBER = auto()
    TECHNICAL_ADVISOR = auto()
    LEGAL_ADVISOR = auto()
    CITIZEN_REPRESENTATIVE = auto()
    DATA_PROTECTION_OFFICER = auto()


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class CommitteeMember:
    """Ein Mitglied des AI Ethics Committee."""
    member_id: UUID = field(default_factory=uuid4)
    name: str = ""
    role: CommitteeRole = CommitteeRole.MEMBER
    department: str = ""
    email: str = ""
    expertise_areas: List[str] = field(default_factory=list)
    active: bool = True
    term_start: datetime = field(default_factory=datetime.utcnow)
    term_end: Optional[datetime] = None


@dataclass
class EthicsReviewRequest:
    """Anfrage für ein Ethics Review."""
    request_id: UUID = field(default_factory=uuid4)
    ai_system_id: UUID = field(default_factory=uuid4)
    ai_system_name: str = ""
    
    # Antragsteller
    requestor_id: str = ""
    requestor_name: str = ""
    requestor_department: str = ""
    
    # Review-Details
    review_type: ReviewType = ReviewType.INITIAL_ASSESSMENT
    risk_level: RiskLevel = RiskLevel.MEDIUM
    
    # Beschreibung
    title: str = ""
    description: str = ""
    justification: str = ""
    
    # Betroffene Bereiche
    affected_groups: List[str] = field(default_factory=list)
    potential_impacts: List[str] = field(default_factory=list)
    mitigation_measures: List[str] = field(default_factory=list)
    
    # Anhänge/Referenzen
    attachments: List[str] = field(default_factory=list)
    related_documents: List[str] = field(default_factory=list)
    
    # Status
    status: ReviewStatus = ReviewStatus.SUBMITTED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Zuweisung
    assigned_to: Optional[UUID] = None
    assigned_at: Optional[datetime] = None
    
    # Deadline
    deadline: Optional[datetime] = None
    priority: str = "normal"  # low, normal, high, urgent


@dataclass
class CommitteeDecision:
    """Entscheidung des AI Ethics Committee."""
    decision_id: UUID = field(default_factory=uuid4)
    request_id: UUID = field(default_factory=uuid4)
    
    # Entscheidung
    status: ReviewStatus = ReviewStatus.APPROVED
    decision_date: datetime = field(default_factory=datetime.utcnow)
    
    # Begründung
    rationale: str = ""
    findings: List[str] = field(default_factory=list)
    
    # Bedingungen (bei APPROVED_WITH_CONDITIONS)
    conditions: List[str] = field(default_factory=list)
    conditions_deadline: Optional[datetime] = None
    
    # Empfehlungen
    recommendations: List[str] = field(default_factory=list)
    required_actions: List[str] = field(default_factory=list)
    
    # Follow-up
    next_review_date: Optional[datetime] = None
    monitoring_requirements: List[str] = field(default_factory=list)
    
    # Voting
    votes_for: int = 0
    votes_against: int = 0
    votes_abstain: int = 0
    
    # Genehmigung
    approved_by: List[str] = field(default_factory=list)


@dataclass
class EthicsGuideline:
    """Eine ethische Richtlinie."""
    guideline_id: UUID = field(default_factory=uuid4)
    title: str = ""
    category: str = ""
    description: str = ""
    requirements: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    related_regulations: List[str] = field(default_factory=list)
    effective_date: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0"


@dataclass
class MeetingMinutes:
    """Protokoll einer Committee-Sitzung."""
    meeting_id: UUID = field(default_factory=uuid4)
    meeting_date: datetime = field(default_factory=datetime.utcnow)
    meeting_type: str = "regular"  # regular, special, emergency
    
    # Teilnehmer
    attendees: List[str] = field(default_factory=list)
    absent: List[str] = field(default_factory=list)
    
    # Agenda
    agenda_items: List[str] = field(default_factory=list)
    
    # Behandelte Anfragen
    reviewed_requests: List[UUID] = field(default_factory=list)
    decisions_made: List[UUID] = field(default_factory=list)
    
    # Protokoll
    discussion_notes: str = ""
    action_items: List[str] = field(default_factory=list)
    
    # Genehmigung
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


# =============================================================================
# AI Ethics Committee
# =============================================================================

class AIEthicsCommittee:
    """
    AI Ethics Committee für VCC-UDS3.
    
    Verantwortlich für:
    - Ethische Prüfung von KI-Systemen
    - Richtlinienentwicklung
    - Incident Response
    - Periodische Reviews
    - Beschwerdeverfahren
    """
    
    def __init__(self):
        """Initialisiert das AI Ethics Committee."""
        self.members: Dict[UUID, CommitteeMember] = {}
        self.requests: Dict[UUID, EthicsReviewRequest] = {}
        self.decisions: Dict[UUID, CommitteeDecision] = {}
        self.guidelines: Dict[UUID, EthicsGuideline] = {}
        self.meetings: List[MeetingMinutes] = []
        
        # Standard-Richtlinien laden
        self._setup_default_guidelines()
    
    def _setup_default_guidelines(self) -> None:
        """Konfiguriert Standard-Ethikrichtlinien."""
        guidelines = [
            EthicsGuideline(
                title="Transparenz und Erklärbarkeit",
                category="transparency",
                description=(
                    "KI-Systeme müssen transparent und erklärbar sein. "
                    "Nutzer müssen verstehen können, wie Entscheidungen zustande kommen."
                ),
                requirements=[
                    "Klare Kennzeichnung von KI-generierten Inhalten",
                    "Nachvollziehbare Quellenangaben",
                    "Erklärung der Entscheidungslogik auf Anfrage",
                    "Dokumentation der Modellfunktionsweise"
                ],
                examples=[
                    "Veritas zeigt immer die Rechtsquellen an",
                    "Clara kennzeichnet generierte Texte als KI-erstellt"
                ],
                related_regulations=["EU AI Act Art. 13", "DSGVO Art. 22"]
            ),
            EthicsGuideline(
                title="Fairness und Nicht-Diskriminierung",
                category="fairness",
                description=(
                    "KI-Systeme dürfen keine Diskriminierung aufgrund geschützter "
                    "Merkmale verursachen oder verstärken."
                ),
                requirements=[
                    "Regelmäßiges Bias-Monitoring",
                    "Ausgewogene Trainingsdaten",
                    "Prüfung auf Disparitäten zwischen Gruppen",
                    "Dokumentation von Fairness-Metriken"
                ],
                examples=[
                    "Keine unterschiedliche Behandlung nach Geschlecht",
                    "Gleichwertige Qualität für alle Regionen"
                ],
                related_regulations=["AGG", "EU AI Act Art. 10", "GG Art. 3"]
            ),
            EthicsGuideline(
                title="Menschliche Aufsicht",
                category="human_oversight",
                description=(
                    "KI-Systeme müssen unter menschlicher Aufsicht stehen. "
                    "Kritische Entscheidungen erfordern menschliche Überprüfung."
                ),
                requirements=[
                    "Human-in-the-Loop für kritische Entscheidungen",
                    "Möglichkeit zur Überstimmung von KI-Empfehlungen",
                    "Dokumentation menschlicher Eingriffe",
                    "Schulung der aufsichtführenden Personen"
                ],
                examples=[
                    "Rechtliche Entscheidungen nur nach menschlicher Prüfung",
                    "Dokumentengenehmigung durch Fachpersonal"
                ],
                related_regulations=["EU AI Act Art. 14", "DSGVO Art. 22"]
            ),
            EthicsGuideline(
                title="Datenschutz und Privatsphäre",
                category="privacy",
                description=(
                    "KI-Systeme müssen den Datenschutz wahren und die "
                    "Privatsphäre der Betroffenen schützen."
                ),
                requirements=[
                    "Datenminimierung",
                    "Anonymisierung/Pseudonymisierung wo möglich",
                    "Sichere Datenspeicherung",
                    "Einwilligungsmanagement"
                ],
                examples=[
                    "Feedback wird anonymisiert gespeichert",
                    "Nutzer können Opt-out wählen"
                ],
                related_regulations=["DSGVO", "BDSG"]
            ),
            EthicsGuideline(
                title="Sicherheit und Robustheit",
                category="security",
                description=(
                    "KI-Systeme müssen sicher und robust gegen Angriffe "
                    "und Fehlfunktionen sein."
                ),
                requirements=[
                    "Regelmäßige Sicherheitsaudits",
                    "Schutz gegen Adversarial Attacks",
                    "Fallback-Mechanismen",
                    "Incident Response Prozesse"
                ],
                examples=[
                    "PKI-Signatur für Modelle",
                    "Automatische Degradation bei Problemen"
                ],
                related_regulations=["EU AI Act Art. 15", "BSI IT-Grundschutz"]
            )
        ]
        
        for guideline in guidelines:
            self.guidelines[guideline.guideline_id] = guideline
    
    # =========================================================================
    # Member Management
    # =========================================================================
    
    def add_member(
        self,
        name: str,
        role: CommitteeRole,
        department: str,
        email: str,
        expertise_areas: Optional[List[str]] = None,
        term_years: int = 2
    ) -> CommitteeMember:
        """
        Fügt ein Mitglied zum Committee hinzu.
        
        Args:
            name: Name des Mitglieds
            role: Rolle im Committee
            department: Abteilung
            email: E-Mail
            expertise_areas: Expertise-Bereiche
            term_years: Amtszeit in Jahren
            
        Returns:
            CommitteeMember
        """
        member = CommitteeMember(
            name=name,
            role=role,
            department=department,
            email=email,
            expertise_areas=expertise_areas or [],
            term_end=datetime.utcnow() + timedelta(days=365 * term_years)
        )
        
        self.members[member.member_id] = member
        
        logger.info(f"Added committee member: {name} ({role.name})")
        return member
    
    def get_active_members(self) -> List[CommitteeMember]:
        """Gibt alle aktiven Mitglieder zurück."""
        now = datetime.utcnow()
        return [
            m for m in self.members.values()
            if m.active and (m.term_end is None or m.term_end > now)
        ]
    
    def get_chair(self) -> Optional[CommitteeMember]:
        """Gibt den Vorsitzenden zurück."""
        chairs = [
            m for m in self.get_active_members()
            if m.role == CommitteeRole.CHAIR
        ]
        return chairs[0] if chairs else None
    
    # =========================================================================
    # Review Request Management
    # =========================================================================
    
    def submit_review_request(
        self,
        ai_system_id: UUID,
        ai_system_name: str,
        requestor_id: str,
        requestor_name: str,
        requestor_department: str,
        review_type: ReviewType,
        title: str,
        description: str,
        justification: str,
        affected_groups: Optional[List[str]] = None,
        potential_impacts: Optional[List[str]] = None,
        mitigation_measures: Optional[List[str]] = None,
        priority: str = "normal"
    ) -> EthicsReviewRequest:
        """
        Reicht eine Review-Anfrage ein.
        
        Args:
            ai_system_id: ID des KI-Systems
            ai_system_name: Name des Systems
            requestor_id: ID des Antragstellers
            requestor_name: Name des Antragstellers
            requestor_department: Abteilung
            review_type: Art des Reviews
            title: Titel der Anfrage
            description: Beschreibung
            justification: Begründung
            affected_groups: Betroffene Gruppen
            potential_impacts: Potenzielle Auswirkungen
            mitigation_measures: Mitigationsmaßnahmen
            priority: Priorität
            
        Returns:
            EthicsReviewRequest
        """
        # Risikostufe basierend auf Review-Typ bestimmen
        risk_level = self._assess_risk_level(review_type, potential_impacts or [])
        
        # Deadline basierend auf Priorität und Risiko
        deadline = self._calculate_deadline(priority, risk_level)
        
        request = EthicsReviewRequest(
            ai_system_id=ai_system_id,
            ai_system_name=ai_system_name,
            requestor_id=requestor_id,
            requestor_name=requestor_name,
            requestor_department=requestor_department,
            review_type=review_type,
            risk_level=risk_level,
            title=title,
            description=description,
            justification=justification,
            affected_groups=affected_groups or [],
            potential_impacts=potential_impacts or [],
            mitigation_measures=mitigation_measures or [],
            deadline=deadline,
            priority=priority
        )
        
        self.requests[request.request_id] = request
        
        logger.info(
            f"Ethics review request submitted: {title} "
            f"(Type: {review_type.name}, Risk: {risk_level.name})"
        )
        
        return request
    
    def _assess_risk_level(
        self,
        review_type: ReviewType,
        potential_impacts: List[str]
    ) -> RiskLevel:
        """Bewertet die Risikostufe einer Anfrage."""
        # Basis-Risiko nach Review-Typ
        base_risk = {
            ReviewType.INITIAL_ASSESSMENT: RiskLevel.HIGH,
            ReviewType.INCIDENT_REVIEW: RiskLevel.CRITICAL,
            ReviewType.BIAS_ESCALATION: RiskLevel.HIGH,
            ReviewType.COMPLAINT_INVESTIGATION: RiskLevel.HIGH,
            ReviewType.CHANGE_ASSESSMENT: RiskLevel.MEDIUM,
            ReviewType.PERIODIC_REVIEW: RiskLevel.LOW
        }.get(review_type, RiskLevel.MEDIUM)
        
        # Erhöhung bei vielen betroffenen Gruppen
        if len(potential_impacts) > 5:
            if base_risk.value < RiskLevel.CRITICAL.value:
                base_risk = RiskLevel(base_risk.value + 1)
        
        return base_risk
    
    def _calculate_deadline(
        self,
        priority: str,
        risk_level: RiskLevel
    ) -> datetime:
        """Berechnet die Deadline für eine Anfrage."""
        base_days = {
            "urgent": 7,
            "high": 14,
            "normal": 30,
            "low": 60
        }.get(priority, 30)
        
        # Beschleunigung bei hohem Risiko
        if risk_level == RiskLevel.CRITICAL:
            base_days = min(base_days, 7)
        elif risk_level == RiskLevel.HIGH:
            base_days = min(base_days, 14)
        
        return datetime.utcnow() + timedelta(days=base_days)
    
    def assign_request(
        self,
        request_id: UUID,
        assigned_to: UUID
    ) -> Optional[EthicsReviewRequest]:
        """
        Weist eine Anfrage einem Mitglied zu.
        
        Args:
            request_id: Anfrage-ID
            assigned_to: Mitglied-ID
            
        Returns:
            Aktualisierte Anfrage oder None
        """
        request = self.requests.get(request_id)
        if not request:
            return None
        
        member = self.members.get(assigned_to)
        if not member:
            return None
        
        request.assigned_to = assigned_to
        request.assigned_at = datetime.utcnow()
        request.status = ReviewStatus.ASSIGNED
        request.updated_at = datetime.utcnow()
        
        logger.info(f"Request {request_id} assigned to {member.name}")
        return request
    
    def update_request_status(
        self,
        request_id: UUID,
        status: ReviewStatus
    ) -> Optional[EthicsReviewRequest]:
        """Aktualisiert den Status einer Anfrage."""
        request = self.requests.get(request_id)
        if not request:
            return None
        
        request.status = status
        request.updated_at = datetime.utcnow()
        return request
    
    # =========================================================================
    # Decision Making
    # =========================================================================
    
    def record_decision(
        self,
        request_id: UUID,
        status: ReviewStatus,
        rationale: str,
        findings: Optional[List[str]] = None,
        conditions: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None,
        required_actions: Optional[List[str]] = None,
        votes_for: int = 0,
        votes_against: int = 0,
        votes_abstain: int = 0,
        next_review_months: int = 12,
        approved_by: Optional[List[str]] = None
    ) -> CommitteeDecision:
        """
        Zeichnet eine Committee-Entscheidung auf.
        
        Args:
            request_id: Anfrage-ID
            status: Entscheidungsstatus
            rationale: Begründung
            findings: Feststellungen
            conditions: Bedingungen
            recommendations: Empfehlungen
            required_actions: Erforderliche Maßnahmen
            votes_for: Ja-Stimmen
            votes_against: Nein-Stimmen
            votes_abstain: Enthaltungen
            next_review_months: Monate bis zur nächsten Überprüfung
            approved_by: Liste der Genehmigenden
            
        Returns:
            CommitteeDecision
        """
        request = self.requests.get(request_id)
        if request:
            request.status = status
            request.updated_at = datetime.utcnow()
        
        decision = CommitteeDecision(
            request_id=request_id,
            status=status,
            rationale=rationale,
            findings=findings or [],
            conditions=conditions or [],
            recommendations=recommendations or [],
            required_actions=required_actions or [],
            votes_for=votes_for,
            votes_against=votes_against,
            votes_abstain=votes_abstain,
            next_review_date=datetime.utcnow() + timedelta(days=30 * next_review_months),
            approved_by=approved_by or []
        )
        
        if conditions:
            decision.conditions_deadline = datetime.utcnow() + timedelta(days=90)
        
        self.decisions[decision.decision_id] = decision
        
        logger.info(
            f"Ethics decision recorded for request {request_id}: "
            f"{status.name} (Votes: {votes_for}/{votes_against}/{votes_abstain})"
        )
        
        return decision
    
    # =========================================================================
    # Meetings
    # =========================================================================
    
    def record_meeting(
        self,
        meeting_type: str,
        attendees: List[str],
        agenda_items: List[str],
        discussion_notes: str,
        reviewed_requests: Optional[List[UUID]] = None,
        decisions_made: Optional[List[UUID]] = None,
        action_items: Optional[List[str]] = None,
        absent: Optional[List[str]] = None
    ) -> MeetingMinutes:
        """
        Protokolliert eine Committee-Sitzung.
        
        Args:
            meeting_type: Art der Sitzung
            attendees: Anwesende
            agenda_items: Tagesordnungspunkte
            discussion_notes: Diskussionsnotizen
            reviewed_requests: Behandelte Anfragen
            decisions_made: Getroffene Entscheidungen
            action_items: Aktionspunkte
            absent: Abwesende
            
        Returns:
            MeetingMinutes
        """
        minutes = MeetingMinutes(
            meeting_type=meeting_type,
            attendees=attendees,
            absent=absent or [],
            agenda_items=agenda_items,
            reviewed_requests=reviewed_requests or [],
            decisions_made=decisions_made or [],
            discussion_notes=discussion_notes,
            action_items=action_items or []
        )
        
        self.meetings.append(minutes)
        
        logger.info(
            f"Meeting minutes recorded: {meeting_type} "
            f"({len(attendees)} attendees, {len(decisions_made or [])} decisions)"
        )
        
        return minutes
    
    # =========================================================================
    # Reporting
    # =========================================================================
    
    def get_pending_requests(self) -> List[EthicsReviewRequest]:
        """Gibt alle offenen Anfragen zurück."""
        return [
            r for r in self.requests.values()
            if r.status not in [
                ReviewStatus.APPROVED,
                ReviewStatus.APPROVED_WITH_CONDITIONS,
                ReviewStatus.REJECTED
            ]
        ]
    
    def get_overdue_requests(self) -> List[EthicsReviewRequest]:
        """Gibt alle überfälligen Anfragen zurück."""
        now = datetime.utcnow()
        pending = self.get_pending_requests()
        return [r for r in pending if r.deadline and r.deadline < now]
    
    def get_committee_report(
        self,
        period_days: int = 90
    ) -> Dict[str, Any]:
        """
        Generiert einen Committee-Report.
        
        Args:
            period_days: Berichtszeitraum in Tagen
            
        Returns:
            Report Dictionary
        """
        period_start = datetime.utcnow() - timedelta(days=period_days)
        
        # Anfragen im Zeitraum
        period_requests = [
            r for r in self.requests.values()
            if r.created_at >= period_start
        ]
        
        # Entscheidungen im Zeitraum
        period_decisions = [
            d for d in self.decisions.values()
            if d.decision_date >= period_start
        ]
        
        # Meetings im Zeitraum
        period_meetings = [
            m for m in self.meetings
            if m.meeting_date >= period_start
        ]
        
        # Statistiken
        status_counts: Dict[str, int] = {}
        for d in period_decisions:
            status = d.status.name
            status_counts[status] = status_counts.get(status, 0) + 1
        
        review_type_counts: Dict[str, int] = {}
        for r in period_requests:
            rtype = r.review_type.name
            review_type_counts[rtype] = review_type_counts.get(rtype, 0) + 1
        
        return {
            "report_generated": datetime.utcnow().isoformat(),
            "period_days": period_days,
            "period_start": period_start.isoformat(),
            "committee": {
                "active_members": len(self.get_active_members()),
                "has_chair": self.get_chair() is not None,
                "total_guidelines": len(self.guidelines)
            },
            "requests": {
                "total_in_period": len(period_requests),
                "by_type": review_type_counts,
                "currently_pending": len(self.get_pending_requests()),
                "currently_overdue": len(self.get_overdue_requests())
            },
            "decisions": {
                "total_in_period": len(period_decisions),
                "by_status": status_counts,
                "approval_rate": (
                    sum(1 for d in period_decisions 
                        if d.status in [ReviewStatus.APPROVED, ReviewStatus.APPROVED_WITH_CONDITIONS])
                    / len(period_decisions) if period_decisions else 0
                )
            },
            "meetings": {
                "total_in_period": len(period_meetings),
                "average_attendees": (
                    sum(len(m.attendees) for m in period_meetings) / len(period_meetings)
                    if period_meetings else 0
                )
            }
        }
    
    def get_guidelines_summary(self) -> List[Dict[str, Any]]:
        """Gibt eine Zusammenfassung aller Richtlinien zurück."""
        return [
            {
                "id": str(g.guideline_id),
                "title": g.title,
                "category": g.category,
                "version": g.version,
                "requirements_count": len(g.requirements),
                "last_updated": g.last_updated.isoformat()
            }
            for g in self.guidelines.values()
        ]


# =============================================================================
# Factory Functions
# =============================================================================

def create_ai_ethics_committee() -> AIEthicsCommittee:
    """
    Erstellt ein AI Ethics Committee.
    
    Returns:
        Konfiguriertes AIEthicsCommittee
    """
    return AIEthicsCommittee()


def setup_default_committee(committee: AIEthicsCommittee) -> Dict[str, UUID]:
    """
    Richtet ein Standard-Committee ein.
    
    Args:
        committee: AI Ethics Committee
        
    Returns:
        Dictionary mit Mitglieder-IDs
    """
    member_ids = {}
    
    # Vorsitzender
    chair = committee.add_member(
        name="Dr. Ethics Chair",
        role=CommitteeRole.CHAIR,
        department="Rechtsabteilung",
        email="ethics-chair@example.org",
        expertise_areas=["KI-Ethik", "Verwaltungsrecht", "Datenschutz"]
    )
    member_ids["chair"] = chair.member_id
    
    # Technischer Berater
    tech = committee.add_member(
        name="Tech Advisor",
        role=CommitteeRole.TECHNICAL_ADVISOR,
        department="IT",
        email="tech-advisor@example.org",
        expertise_areas=["Machine Learning", "NLP", "Systemarchitektur"]
    )
    member_ids["tech_advisor"] = tech.member_id
    
    # Datenschutzbeauftragter
    dpo = committee.add_member(
        name="Datenschutzbeauftragter",
        role=CommitteeRole.DATA_PROTECTION_OFFICER,
        department="Datenschutz",
        email="dpo@example.org",
        expertise_areas=["DSGVO", "BDSG", "Datenschutz"]
    )
    member_ids["dpo"] = dpo.member_id
    
    # Rechtsberater
    legal = committee.add_member(
        name="Legal Advisor",
        role=CommitteeRole.LEGAL_ADVISOR,
        department="Rechtsabteilung",
        email="legal@example.org",
        expertise_areas=["EU AI Act", "Verwaltungsrecht", "AGG"]
    )
    member_ids["legal_advisor"] = legal.member_id
    
    # Bürgervertreter
    citizen = committee.add_member(
        name="Bürgervertreter",
        role=CommitteeRole.CITIZEN_REPRESENTATIVE,
        department="Extern",
        email="citizen-rep@example.org",
        expertise_areas=["Bürgerperspektive", "Barrierefreiheit"]
    )
    member_ids["citizen_rep"] = citizen.member_id
    
    # Zwei weitere Mitglieder
    for i in range(2):
        member = committee.add_member(
            name=f"Committee Member {i+1}",
            role=CommitteeRole.MEMBER,
            department="Fachbereich",
            email=f"member{i+1}@example.org",
            expertise_areas=["KI-Anwendungen", "Prozessoptimierung"]
        )
        member_ids[f"member_{i+1}"] = member.member_id
    
    return member_ids


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "ReviewType",
    "ReviewStatus",
    "RiskLevel",
    "CommitteeRole",
    # Data Models
    "CommitteeMember",
    "EthicsReviewRequest",
    "CommitteeDecision",
    "EthicsGuideline",
    "MeetingMinutes",
    # Committee
    "AIEthicsCommittee",
    # Factory Functions
    "create_ai_ethics_committee",
    "setup_default_committee",
]
