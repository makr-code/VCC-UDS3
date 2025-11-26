#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_classification.py

VCC-UDS3 Data Classification and Retention Policies
Part of v2.5.0 Governance & Compliance

Implementiert:
- Datenklassifizierungssystem (Öffentlich → Geheim)
- Automatische Klassifizierung für Verwaltungsdaten
- Retention Policies gemäß rechtlicher Vorgaben
- Löschungsmanagement und Audit-Trail
- Integration mit DSGVO-Core für PII-Handling

Author: VCC Development Team
License: MIT with Government Partnership Commons Clause
"""

import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# Enums für Klassifizierungssystem
# =============================================================================

class ClassificationLevel(Enum):
    """
    Datenklassifizierungsstufen gemäß BSI Grundschutz und Verwaltungsvorschriften.
    
    Stufen:
    - PUBLIC: Öffentlich zugängliche Daten
    - INTERNAL: Interne Verwaltungsdaten
    - CONFIDENTIAL: Vertrauliche Daten mit Schutzanforderungen
    - SECRET: Geheime Daten mit hoher Schutzstufe
    - TOP_SECRET: Streng geheime Daten (höchste Schutzstufe)
    """
    PUBLIC = 1  # Öffentlich
    INTERNAL = 2  # VS-NfD (Nur für den Dienstgebrauch)
    CONFIDENTIAL = 3  # VS-VERTRAULICH
    SECRET = 4  # VS-GEHEIM
    TOP_SECRET = 5  # STRENG GEHEIM


class DataCategory(Enum):
    """Kategorien von Verwaltungsdaten."""
    # Rechtsdaten
    LEGAL_TEXT = auto()  # Gesetzestexte, Verordnungen
    LEGAL_COMMENTARY = auto()  # Kommentare, Erläuterungen
    COURT_DECISION = auto()  # Gerichtsentscheidungen
    
    # Prozessdaten
    PROCESS_DEFINITION = auto()  # Prozessdefinitionen (VPB)
    PROCESS_INSTANCE = auto()  # Laufende Prozessinstanzen
    PROCESS_LOG = auto()  # Prozessprotokoll
    
    # Nutzerdaten
    USER_PROFILE = auto()  # Benutzerprofile
    USER_ACTIVITY = auto()  # Nutzeraktivitäten
    USER_FEEDBACK = auto()  # Feedback für Training
    
    # KI-Daten
    AI_MODEL = auto()  # Trainierte Modelle
    AI_TRAINING_DATA = auto()  # Trainingsdaten
    AI_INFERENCE_LOG = auto()  # Inferenz-Protokolle
    
    # System-Daten
    AUDIT_LOG = auto()  # Audit-Protokolle
    SYSTEM_CONFIG = auto()  # Systemkonfiguration
    METRICS = auto()  # Metriken und Performance-Daten


class RetentionType(Enum):
    """Aufbewahrungstypen."""
    INDEFINITE = auto()  # Unbefristete Aufbewahrung
    LEGAL_MINIMUM = auto()  # Gesetzliche Mindestdauer
    PROCESS_DURATION = auto()  # Bis Prozessende
    AUDIT_PERIOD = auto()  # Prüfungszeitraum
    USER_CONSENT = auto()  # Bis Widerruf der Einwilligung
    TIME_BASED = auto()  # Zeitbasiert (explizite Dauer)


class DeletionMethod(Enum):
    """Löschmethoden gemäß Sicherheitsanforderungen."""
    SOFT_DELETE = auto()  # Markierung als gelöscht
    HARD_DELETE = auto()  # Tatsächliche Löschung
    ANONYMIZE = auto()  # Anonymisierung statt Löschung
    SECURE_WIPE = auto()  # Sicheres Überschreiben (BSI-konform)
    CRYPTO_SHRED = auto()  # Kryptographische Vernichtung


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class RetentionPolicy:
    """
    Aufbewahrungsrichtlinie für eine Datenkategorie.
    
    Attributes:
        category: Datenkategorie
        retention_type: Art der Aufbewahrung
        duration_days: Dauer in Tagen (falls zeitbasiert)
        legal_basis: Rechtliche Grundlage
        deletion_method: Vorgeschriebene Löschmethode
        requires_approval: Erfordert Genehmigung vor Löschung
        notify_before_deletion_days: Tage vor Löschung benachrichtigen
        exceptions: Ausnahmebedingungen
    """
    category: DataCategory
    retention_type: RetentionType
    duration_days: Optional[int] = None
    legal_basis: str = ""
    deletion_method: DeletionMethod = DeletionMethod.HARD_DELETE
    requires_approval: bool = False
    notify_before_deletion_days: int = 30
    exceptions: List[str] = field(default_factory=list)
    
    def calculate_deletion_date(self, creation_date: datetime) -> Optional[datetime]:
        """Berechnet das Löschdatum basierend auf der Policy."""
        if self.retention_type == RetentionType.INDEFINITE:
            return None
        if self.retention_type == RetentionType.TIME_BASED and self.duration_days:
            return creation_date + timedelta(days=self.duration_days)
        return None


@dataclass
class ClassificationMetadata:
    """
    Metadaten für klassifizierte Daten.
    
    Attributes:
        classification_id: Eindeutige ID
        document_id: Referenz zum Dokument
        level: Klassifizierungsstufe
        category: Datenkategorie
        classification_date: Datum der Klassifizierung
        classified_by: Klassifiziert durch (System/User)
        auto_classified: Automatisch klassifiziert
        confidence: Konfidenz bei automatischer Klassifizierung
        review_required: Review erforderlich
        review_by: Geprüft durch
        review_date: Prüfdatum
        retention_policy_id: Zugeordnete Aufbewahrungsrichtlinie
        deletion_scheduled: Geplantes Löschdatum
        pii_present: PII vorhanden
        pii_types: Typen von PII
        access_groups: Berechtigte Gruppen
        tags: Zusätzliche Tags
    """
    classification_id: UUID = field(default_factory=uuid4)
    document_id: str = ""
    level: ClassificationLevel = ClassificationLevel.INTERNAL
    category: DataCategory = DataCategory.LEGAL_TEXT
    classification_date: datetime = field(default_factory=datetime.utcnow)
    classified_by: str = "SYSTEM"
    auto_classified: bool = True
    confidence: float = 1.0
    review_required: bool = False
    review_by: Optional[str] = None
    review_date: Optional[datetime] = None
    retention_policy_id: Optional[str] = None
    deletion_scheduled: Optional[datetime] = None
    pii_present: bool = False
    pii_types: List[str] = field(default_factory=list)
    access_groups: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class DeletionRequest:
    """Anfrage zur Datenlöschung."""
    request_id: UUID = field(default_factory=uuid4)
    document_id: str = ""
    classification_id: UUID = field(default_factory=uuid4)
    requested_by: str = ""
    requested_at: datetime = field(default_factory=datetime.utcnow)
    reason: str = ""
    deletion_method: DeletionMethod = DeletionMethod.HARD_DELETE
    status: str = "pending"  # pending, approved, rejected, executed
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    verification_hash: Optional[str] = None


# =============================================================================
# Classification Engine
# =============================================================================

class ClassificationRule(ABC):
    """Abstrakte Basisklasse für Klassifizierungsregeln."""
    
    @abstractmethod
    def evaluate(self, content: Dict[str, Any]) -> Optional[Tuple[ClassificationLevel, DataCategory, float]]:
        """
        Evaluiert die Regel für gegebenen Inhalt.
        
        Returns:
            Tuple (Level, Category, Confidence) oder None wenn nicht anwendbar.
        """
        pass


class ContentPatternRule(ClassificationRule):
    """Regelbasierte Klassifizierung nach Inhaltsmustern."""
    
    def __init__(
        self,
        patterns: List[str],
        level: ClassificationLevel,
        category: DataCategory,
        base_confidence: float = 0.8
    ):
        self.patterns = [p.lower() for p in patterns]
        self.level = level
        self.category = category
        self.base_confidence = base_confidence
    
    def evaluate(self, content: Dict[str, Any]) -> Optional[Tuple[ClassificationLevel, DataCategory, float]]:
        """Prüft ob Muster im Inhalt gefunden werden."""
        text = str(content.get("content", "")).lower()
        text += " " + str(content.get("title", "")).lower()
        
        matches = sum(1 for p in self.patterns if p in text)
        if matches > 0:
            confidence = min(self.base_confidence + (matches * 0.05), 1.0)
            return (self.level, self.category, confidence)
        return None


class MetadataRule(ClassificationRule):
    """Klassifizierung basierend auf Metadaten."""
    
    def __init__(
        self,
        metadata_key: str,
        expected_values: Set[str],
        level: ClassificationLevel,
        category: DataCategory
    ):
        self.metadata_key = metadata_key
        self.expected_values = expected_values
        self.level = level
        self.category = category
    
    def evaluate(self, content: Dict[str, Any]) -> Optional[Tuple[ClassificationLevel, DataCategory, float]]:
        """Prüft Metadaten auf erwartete Werte."""
        metadata = content.get("metadata", {})
        value = metadata.get(self.metadata_key, "")
        
        if str(value) in self.expected_values:
            return (self.level, self.category, 0.95)
        return None


class DataClassificationEngine:
    """
    Engine für automatische und manuelle Datenklassifizierung.
    
    Features:
    - Regelbasierte automatische Klassifizierung
    - Konfidenzbasierte Review-Anforderung
    - Integration mit Retention Policies
    - Audit-Trail für alle Klassifizierungen
    """
    
    def __init__(
        self,
        auto_classify_threshold: float = 0.7,
        review_threshold: float = 0.85
    ):
        """
        Initialisiert die Classification Engine.
        
        Args:
            auto_classify_threshold: Mindest-Konfidenz für automatische Klassifizierung
            review_threshold: Konfidenz unter der Review erforderlich ist
        """
        self.auto_classify_threshold = auto_classify_threshold
        self.review_threshold = review_threshold
        self.rules: List[ClassificationRule] = []
        self.retention_policies: Dict[DataCategory, RetentionPolicy] = {}
        self.classifications: Dict[str, ClassificationMetadata] = {}
        
        self._setup_default_rules()
        self._setup_default_retention_policies()
    
    def _setup_default_rules(self) -> None:
        """Konfiguriert Standardregeln für Verwaltungsdaten."""
        # Rechtsdaten
        self.rules.append(ContentPatternRule(
            patterns=["gesetz", "verordnung", "§", "paragraph", "artikel"],
            level=ClassificationLevel.PUBLIC,
            category=DataCategory.LEGAL_TEXT
        ))
        
        self.rules.append(ContentPatternRule(
            patterns=["kommentar", "erläuterung", "begründung", "auslegung"],
            level=ClassificationLevel.INTERNAL,
            category=DataCategory.LEGAL_COMMENTARY
        ))
        
        self.rules.append(ContentPatternRule(
            patterns=["urteil", "beschluss", "entscheidung", "aktenzeichen"],
            level=ClassificationLevel.PUBLIC,
            category=DataCategory.COURT_DECISION
        ))
        
        # Personenbezogene Daten → höhere Klassifizierung
        self.rules.append(ContentPatternRule(
            patterns=["name", "adresse", "geburtsdatum", "sozialversicherung", "personalausweis"],
            level=ClassificationLevel.CONFIDENTIAL,
            category=DataCategory.USER_PROFILE,
            base_confidence=0.9
        ))
        
        # VS-Kennzeichnungen
        self.rules.append(ContentPatternRule(
            patterns=["vs-nfd", "nur für den dienstgebrauch"],
            level=ClassificationLevel.INTERNAL,
            category=DataCategory.SYSTEM_CONFIG,
            base_confidence=0.95
        ))
        
        self.rules.append(ContentPatternRule(
            patterns=["vs-vertraulich", "vertraulich"],
            level=ClassificationLevel.CONFIDENTIAL,
            category=DataCategory.SYSTEM_CONFIG,
            base_confidence=0.95
        ))
        
        self.rules.append(ContentPatternRule(
            patterns=["vs-geheim", "geheim"],
            level=ClassificationLevel.SECRET,
            category=DataCategory.SYSTEM_CONFIG,
            base_confidence=0.95
        ))
    
    def _setup_default_retention_policies(self) -> None:
        """Konfiguriert Standard-Aufbewahrungsrichtlinien."""
        # Rechtsdaten: Unbefristete Aufbewahrung
        self.retention_policies[DataCategory.LEGAL_TEXT] = RetentionPolicy(
            category=DataCategory.LEGAL_TEXT,
            retention_type=RetentionType.INDEFINITE,
            legal_basis="Rechtssicherheit, öffentliches Interesse",
            deletion_method=DeletionMethod.SOFT_DELETE
        )
        
        self.retention_policies[DataCategory.COURT_DECISION] = RetentionPolicy(
            category=DataCategory.COURT_DECISION,
            retention_type=RetentionType.INDEFINITE,
            legal_basis="Rechtsprechungsdokumentation",
            deletion_method=DeletionMethod.SOFT_DELETE
        )
        
        # Audit-Logs: 10 Jahre (gemäß HGB/AO)
        self.retention_policies[DataCategory.AUDIT_LOG] = RetentionPolicy(
            category=DataCategory.AUDIT_LOG,
            retention_type=RetentionType.TIME_BASED,
            duration_days=3650,  # 10 Jahre
            legal_basis="§ 147 AO, § 257 HGB",
            deletion_method=DeletionMethod.SECURE_WIPE,
            requires_approval=True
        )
        
        # Nutzerdaten: DSGVO-konform
        self.retention_policies[DataCategory.USER_PROFILE] = RetentionPolicy(
            category=DataCategory.USER_PROFILE,
            retention_type=RetentionType.USER_CONSENT,
            legal_basis="Art. 17 DSGVO (Recht auf Löschung)",
            deletion_method=DeletionMethod.ANONYMIZE,
            requires_approval=False,
            notify_before_deletion_days=14
        )
        
        self.retention_policies[DataCategory.USER_ACTIVITY] = RetentionPolicy(
            category=DataCategory.USER_ACTIVITY,
            retention_type=RetentionType.TIME_BASED,
            duration_days=365,  # 1 Jahr
            legal_basis="Legitimes Interesse, Art. 6(1)(f) DSGVO",
            deletion_method=DeletionMethod.ANONYMIZE
        )
        
        # KI-Trainingsdaten: Spezielle Aufbewahrung
        self.retention_policies[DataCategory.AI_TRAINING_DATA] = RetentionPolicy(
            category=DataCategory.AI_TRAINING_DATA,
            retention_type=RetentionType.TIME_BASED,
            duration_days=730,  # 2 Jahre (für Reproduzierbarkeit)
            legal_basis="EU AI Act, Nachvollziehbarkeit",
            deletion_method=DeletionMethod.SECURE_WIPE,
            requires_approval=True
        )
        
        # Prozessinstanzen: Nach Abschluss + 2 Jahre
        self.retention_policies[DataCategory.PROCESS_INSTANCE] = RetentionPolicy(
            category=DataCategory.PROCESS_INSTANCE,
            retention_type=RetentionType.PROCESS_DURATION,
            duration_days=730,  # 2 Jahre nach Abschluss
            legal_basis="Verwaltungsverfahrensrecht",
            deletion_method=DeletionMethod.ANONYMIZE
        )
    
    def add_rule(self, rule: ClassificationRule) -> None:
        """Fügt eine Klassifizierungsregel hinzu."""
        self.rules.append(rule)
    
    def add_retention_policy(self, policy: RetentionPolicy) -> None:
        """Fügt eine Aufbewahrungsrichtlinie hinzu."""
        self.retention_policies[policy.category] = policy
    
    def classify(
        self,
        document_id: str,
        content: Dict[str, Any],
        force_manual: bool = False
    ) -> ClassificationMetadata:
        """
        Klassifiziert ein Dokument.
        
        Args:
            document_id: Dokument-ID
            content: Dokumentinhalt mit Metadaten
            force_manual: Erzwingt manuelle Klassifizierung
            
        Returns:
            ClassificationMetadata mit Ergebnis
        """
        if force_manual:
            return self._create_manual_classification(document_id)
        
        # Alle Regeln evaluieren
        results: List[Tuple[ClassificationLevel, DataCategory, float]] = []
        for rule in self.rules:
            result = rule.evaluate(content)
            if result:
                results.append(result)
        
        if not results:
            # Fallback: INTERNAL/LEGAL_TEXT mit niedriger Konfidenz
            return self._create_classification(
                document_id,
                ClassificationLevel.INTERNAL,
                DataCategory.LEGAL_TEXT,
                confidence=0.5,
                review_required=True
            )
        
        # Höchste Klassifizierung gewinnt (Sicherheitsprinzip)
        best_result = max(results, key=lambda r: (r[0].value, r[2]))
        level, category, confidence = best_result
        
        # Review erforderlich bei niedriger Konfidenz
        review_required = confidence < self.review_threshold
        
        return self._create_classification(
            document_id,
            level,
            category,
            confidence=confidence,
            review_required=review_required,
            auto_classified=True
        )
    
    def _create_classification(
        self,
        document_id: str,
        level: ClassificationLevel,
        category: DataCategory,
        confidence: float = 1.0,
        review_required: bool = False,
        auto_classified: bool = True
    ) -> ClassificationMetadata:
        """Erstellt ClassificationMetadata mit zugehöriger Retention Policy."""
        # Retention Policy zuordnen
        policy = self.retention_policies.get(category)
        deletion_date = None
        if policy:
            deletion_date = policy.calculate_deletion_date(datetime.utcnow())
        
        metadata = ClassificationMetadata(
            document_id=document_id,
            level=level,
            category=category,
            confidence=confidence,
            review_required=review_required,
            auto_classified=auto_classified,
            retention_policy_id=str(category.name) if policy else None,
            deletion_scheduled=deletion_date
        )
        
        # Speichern
        self.classifications[document_id] = metadata
        
        logger.info(
            f"Classified document {document_id}: "
            f"Level={level.name}, Category={category.name}, "
            f"Confidence={confidence:.2f}, Review={review_required}"
        )
        
        return metadata
    
    def _create_manual_classification(self, document_id: str) -> ClassificationMetadata:
        """Erstellt Platzhalter für manuelle Klassifizierung."""
        metadata = ClassificationMetadata(
            document_id=document_id,
            level=ClassificationLevel.CONFIDENTIAL,  # Sicherer Default
            category=DataCategory.LEGAL_TEXT,
            confidence=0.0,
            review_required=True,
            auto_classified=False
        )
        self.classifications[document_id] = metadata
        return metadata
    
    def update_classification(
        self,
        document_id: str,
        level: Optional[ClassificationLevel] = None,
        category: Optional[DataCategory] = None,
        reviewed_by: Optional[str] = None
    ) -> Optional[ClassificationMetadata]:
        """
        Aktualisiert eine bestehende Klassifizierung.
        
        Args:
            document_id: Dokument-ID
            level: Neue Klassifizierungsstufe (optional)
            category: Neue Kategorie (optional)
            reviewed_by: Reviewer (markiert als geprüft)
            
        Returns:
            Aktualisierte Metadaten oder None
        """
        metadata = self.classifications.get(document_id)
        if not metadata:
            return None
        
        if level:
            metadata.level = level
        if category:
            metadata.category = category
            # Neue Retention Policy zuordnen
            policy = self.retention_policies.get(category)
            if policy:
                metadata.retention_policy_id = str(category.name)
                metadata.deletion_scheduled = policy.calculate_deletion_date(
                    metadata.classification_date
                )
        
        if reviewed_by:
            metadata.review_required = False
            metadata.review_by = reviewed_by
            metadata.review_date = datetime.utcnow()
        
        logger.info(f"Updated classification for document {document_id}")
        return metadata
    
    def get_classification(self, document_id: str) -> Optional[ClassificationMetadata]:
        """Holt die Klassifizierung für ein Dokument."""
        return self.classifications.get(document_id)
    
    def get_pending_reviews(self) -> List[ClassificationMetadata]:
        """Gibt alle Klassifizierungen zurück, die Review benötigen."""
        return [m for m in self.classifications.values() if m.review_required]
    
    def get_scheduled_deletions(
        self,
        before_date: Optional[datetime] = None
    ) -> List[ClassificationMetadata]:
        """
        Gibt alle Dokumente zurück, deren Löschung geplant ist.
        
        Args:
            before_date: Nur Löschungen vor diesem Datum
            
        Returns:
            Liste der betroffenen Klassifizierungen
        """
        result = []
        for metadata in self.classifications.values():
            if metadata.deletion_scheduled:
                if before_date is None or metadata.deletion_scheduled <= before_date:
                    result.append(metadata)
        return sorted(result, key=lambda m: m.deletion_scheduled or datetime.max)


# =============================================================================
# Retention Manager
# =============================================================================

class RetentionManager:
    """
    Manager für Aufbewahrungsrichtlinien und automatische Löschung.
    
    Features:
    - Automatische Löschplanung basierend auf Policies
    - Genehmigungsworkflow für kritische Löschungen
    - Audit-Trail für alle Löschvorgänge
    - Benachrichtigungen vor geplanten Löschungen
    """
    
    def __init__(
        self,
        classification_engine: DataClassificationEngine,
        deletion_callback: Optional[Callable[[str, DeletionMethod], bool]] = None
    ):
        """
        Initialisiert den Retention Manager.
        
        Args:
            classification_engine: Referenz zur Classification Engine
            deletion_callback: Callback für tatsächliche Löschung
        """
        self.engine = classification_engine
        self.deletion_callback = deletion_callback or self._default_deletion
        self.deletion_requests: Dict[UUID, DeletionRequest] = {}
        self.deletion_log: List[Dict[str, Any]] = []
    
    def _default_deletion(self, document_id: str, method: DeletionMethod) -> bool:
        """Standard-Löschcallback (simuliert)."""
        logger.info(f"[SIMULATED] Deleting document {document_id} with method {method.name}")
        return True
    
    def schedule_deletion(
        self,
        document_id: str,
        requested_by: str,
        reason: str = ""
    ) -> Optional[DeletionRequest]:
        """
        Plant eine Löschung für ein Dokument.
        
        Args:
            document_id: Zu löschendes Dokument
            requested_by: Antragsteller
            reason: Begründung
            
        Returns:
            DeletionRequest oder None
        """
        metadata = self.engine.get_classification(document_id)
        if not metadata:
            logger.warning(f"Cannot schedule deletion: Document {document_id} not classified")
            return None
        
        # Policy für die Kategorie abrufen
        policy = self.engine.retention_policies.get(metadata.category)
        if not policy:
            policy = RetentionPolicy(
                category=metadata.category,
                retention_type=RetentionType.TIME_BASED,
                deletion_method=DeletionMethod.HARD_DELETE
            )
        
        request = DeletionRequest(
            document_id=document_id,
            classification_id=metadata.classification_id,
            requested_by=requested_by,
            reason=reason,
            deletion_method=policy.deletion_method,
            status="pending" if policy.requires_approval else "approved"
        )
        
        self.deletion_requests[request.request_id] = request
        
        logger.info(
            f"Deletion scheduled for {document_id}: "
            f"Method={policy.deletion_method.name}, "
            f"RequiresApproval={policy.requires_approval}"
        )
        
        return request
    
    def approve_deletion(
        self,
        request_id: UUID,
        approved_by: str
    ) -> Optional[DeletionRequest]:
        """
        Genehmigt eine Löschanfrage.
        
        Args:
            request_id: Anfrage-ID
            approved_by: Genehmigender
            
        Returns:
            Aktualisierte Anfrage oder None
        """
        request = self.deletion_requests.get(request_id)
        if not request:
            return None
        
        if request.status != "pending":
            logger.warning(f"Deletion request {request_id} is not pending")
            return request
        
        request.status = "approved"
        request.approved_by = approved_by
        request.approved_at = datetime.utcnow()
        
        logger.info(f"Deletion request {request_id} approved by {approved_by}")
        return request
    
    def reject_deletion(
        self,
        request_id: UUID,
        rejected_by: str,
        reason: str = ""
    ) -> Optional[DeletionRequest]:
        """
        Lehnt eine Löschanfrage ab.
        
        Args:
            request_id: Anfrage-ID
            rejected_by: Ablehnender
            reason: Begründung
            
        Returns:
            Aktualisierte Anfrage oder None
        """
        request = self.deletion_requests.get(request_id)
        if not request:
            return None
        
        request.status = "rejected"
        request.approved_by = rejected_by  # Wiederverwendung für Ablehnenden
        request.approved_at = datetime.utcnow()
        request.reason = f"{request.reason} | REJECTED: {reason}"
        
        logger.info(f"Deletion request {request_id} rejected by {rejected_by}: {reason}")
        return request
    
    def execute_deletion(self, request_id: UUID) -> bool:
        """
        Führt eine genehmigte Löschung aus.
        
        Args:
            request_id: Anfrage-ID
            
        Returns:
            True bei Erfolg
        """
        request = self.deletion_requests.get(request_id)
        if not request:
            logger.error(f"Deletion request {request_id} not found")
            return False
        
        if request.status != "approved":
            logger.error(f"Deletion request {request_id} not approved (status: {request.status})")
            return False
        
        # Löschung ausführen
        success = self.deletion_callback(request.document_id, request.deletion_method)
        
        if success:
            request.status = "executed"
            request.executed_at = datetime.utcnow()
            request.verification_hash = hashlib.sha256(
                f"{request.document_id}:{request.executed_at.isoformat()}".encode()
            ).hexdigest()
            
            # Audit-Log
            self.deletion_log.append({
                "request_id": str(request.request_id),
                "document_id": request.document_id,
                "method": request.deletion_method.name,
                "executed_at": request.executed_at.isoformat(),
                "requested_by": request.requested_by,
                "approved_by": request.approved_by,
                "verification_hash": request.verification_hash
            })
            
            # Klassifizierung entfernen
            if request.document_id in self.engine.classifications:
                del self.engine.classifications[request.document_id]
            
            logger.info(
                f"Deletion executed for {request.document_id}: "
                f"Hash={request.verification_hash[:16]}..."
            )
        
        return success
    
    def get_upcoming_deletions(self, days: int = 30) -> List[ClassificationMetadata]:
        """
        Gibt alle in den nächsten X Tagen zur Löschung anstehenden Dokumente zurück.
        
        Args:
            days: Zeitraum in Tagen
            
        Returns:
            Liste der betroffenen Klassifizierungen
        """
        deadline = datetime.utcnow() + timedelta(days=days)
        return self.engine.get_scheduled_deletions(before_date=deadline)
    
    def get_deletion_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Gibt das Löschprotokoll zurück."""
        return self.deletion_log[-limit:]


# =============================================================================
# Factory Functions
# =============================================================================

def create_classification_engine(
    auto_classify_threshold: float = 0.7,
    review_threshold: float = 0.85
) -> DataClassificationEngine:
    """
    Erstellt eine konfigurierte Classification Engine.
    
    Args:
        auto_classify_threshold: Mindest-Konfidenz für Auto-Klassifizierung
        review_threshold: Konfidenz-Schwelle für Review-Anforderung
        
    Returns:
        Konfigurierte DataClassificationEngine
    """
    return DataClassificationEngine(
        auto_classify_threshold=auto_classify_threshold,
        review_threshold=review_threshold
    )


def create_retention_manager(
    classification_engine: DataClassificationEngine,
    deletion_callback: Optional[Callable[[str, DeletionMethod], bool]] = None
) -> RetentionManager:
    """
    Erstellt einen Retention Manager.
    
    Args:
        classification_engine: Classification Engine
        deletion_callback: Callback für Löschvorgänge
        
    Returns:
        Konfigurierter RetentionManager
    """
    return RetentionManager(
        classification_engine=classification_engine,
        deletion_callback=deletion_callback
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "ClassificationLevel",
    "DataCategory",
    "RetentionType",
    "DeletionMethod",
    # Data Models
    "RetentionPolicy",
    "ClassificationMetadata",
    "DeletionRequest",
    # Rules
    "ClassificationRule",
    "ContentPatternRule",
    "MetadataRule",
    # Engines
    "DataClassificationEngine",
    "RetentionManager",
    # Factory Functions
    "create_classification_engine",
    "create_retention_manager",
]
