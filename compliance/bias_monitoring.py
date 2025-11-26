#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bias_monitoring.py

VCC-UDS3 Bias Monitoring System
Part of v2.5.0 Governance & Compliance

Implementiert:
- Bias-Erkennung in KI-Ausgaben
- Fairness-Metriken (Demographic Parity, Equalized Odds)
- Kontinuierliches Monitoring
- Alerting bei Bias-Detection
- Reporting für AI Ethics Committee

Author: VCC Development Team
License: MIT with Government Partnership Commons Clause
"""

import hashlib
import logging
import statistics
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# Enums für Bias Monitoring
# =============================================================================

class BiasType(Enum):
    """Typen von KI-Bias."""
    DEMOGRAPHIC = auto()      # Demographischer Bias
    GEOGRAPHIC = auto()       # Geographischer Bias
    TEMPORAL = auto()         # Zeitlicher Bias (alte vs. neue Daten)
    SELECTION = auto()        # Auswahlbias in Trainingsdaten
    CONFIRMATION = auto()     # Bestätigungsbias
    ANCHORING = auto()        # Ankerbias (erste Information dominiert)
    OUTCOME = auto()          # Ergebnisbias


class ProtectedAttribute(Enum):
    """Geschützte Attribute gemäß AGG/EU-Recht."""
    GENDER = "gender"
    AGE = "age"
    ETHNICITY = "ethnicity"
    RELIGION = "religion"
    DISABILITY = "disability"
    NATIONALITY = "nationality"
    POLITICAL_OPINION = "political_opinion"
    GEOGRAPHIC_ORIGIN = "geographic_origin"


class AlertSeverity(Enum):
    """Schweregrade für Bias-Alerts."""
    INFO = 1
    WARNING = 2
    CRITICAL = 3
    EMERGENCY = 4


class MonitoringStatus(Enum):
    """Status des Bias-Monitorings."""
    ACTIVE = auto()
    PAUSED = auto()
    ALERT_TRIGGERED = auto()
    UNDER_REVIEW = auto()


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class BiasMetric:
    """
    Eine einzelne Bias-Metrik.
    """
    metric_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    bias_type: BiasType = BiasType.DEMOGRAPHIC
    protected_attribute: Optional[ProtectedAttribute] = None
    
    # Werte
    current_value: float = 0.0
    baseline_value: float = 0.0
    threshold_warning: float = 0.1  # 10% Abweichung
    threshold_critical: float = 0.2  # 20% Abweichung
    
    # Zeitstempel
    measured_at: datetime = field(default_factory=datetime.utcnow)
    
    def get_deviation(self) -> float:
        """Berechnet die Abweichung vom Baseline."""
        if self.baseline_value == 0:
            return abs(self.current_value)
        return abs(self.current_value - self.baseline_value) / abs(self.baseline_value)
    
    def get_severity(self) -> AlertSeverity:
        """Bestimmt den Schweregrad basierend auf Abweichung."""
        deviation = self.get_deviation()
        if deviation >= self.threshold_critical:
            return AlertSeverity.CRITICAL
        elif deviation >= self.threshold_warning:
            return AlertSeverity.WARNING
        return AlertSeverity.INFO


@dataclass
class BiasAlert:
    """
    Ein Bias-Alert.
    """
    alert_id: UUID = field(default_factory=uuid4)
    ai_system_id: UUID = field(default_factory=uuid4)
    metric: BiasMetric = field(default_factory=BiasMetric)
    severity: AlertSeverity = AlertSeverity.WARNING
    
    # Details
    message: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    affected_groups: List[str] = field(default_factory=list)
    
    # Status
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None


@dataclass
class FairnessReport:
    """
    Fairness-Report für ein KI-System.
    """
    report_id: UUID = field(default_factory=uuid4)
    ai_system_id: UUID = field(default_factory=uuid4)
    report_date: datetime = field(default_factory=datetime.utcnow)
    reporting_period_start: datetime = field(default_factory=datetime.utcnow)
    reporting_period_end: datetime = field(default_factory=datetime.utcnow)
    
    # Metriken
    metrics: List[BiasMetric] = field(default_factory=list)
    
    # Aggregierte Werte
    demographic_parity_score: float = 0.0
    equalized_odds_score: float = 0.0
    overall_fairness_score: float = 0.0
    
    # Alerts im Berichtszeitraum
    alerts_triggered: int = 0
    alerts_resolved: int = 0
    alerts_pending: int = 0
    
    # Empfehlungen
    recommendations: List[str] = field(default_factory=list)
    
    # Status
    review_status: str = "pending"  # pending, reviewed, approved, rejected
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None


@dataclass
class MonitoringConfiguration:
    """
    Konfiguration für das Bias-Monitoring.
    """
    config_id: UUID = field(default_factory=uuid4)
    ai_system_id: UUID = field(default_factory=uuid4)
    
    # Monitoring-Parameter
    enabled: bool = True
    sampling_rate: float = 1.0  # 100% aller Interaktionen
    
    # Metriken
    monitored_attributes: List[ProtectedAttribute] = field(default_factory=list)
    monitored_bias_types: List[BiasType] = field(default_factory=list)
    
    # Schwellenwerte
    thresholds: Dict[str, float] = field(default_factory=dict)
    
    # Alerting
    alert_recipients: List[str] = field(default_factory=list)
    alert_cooldown_minutes: int = 60  # Keine wiederholten Alerts
    
    # Reporting
    report_frequency_days: int = 30
    auto_escalate_after_hours: int = 24


# =============================================================================
# Bias Detectors
# =============================================================================

class BiasDetector(ABC):
    """Abstrakte Basisklasse für Bias-Detektoren."""
    
    @abstractmethod
    def detect(
        self,
        interactions: List[Dict[str, Any]],
        protected_attribute: Optional[ProtectedAttribute] = None
    ) -> List[BiasMetric]:
        """
        Erkennt Bias in den gegebenen Interaktionen.
        
        Args:
            interactions: Liste von KI-Interaktionen
            protected_attribute: Zu prüfendes geschütztes Attribut
            
        Returns:
            Liste von BiasMetrics
        """
        pass


class DemographicParityDetector(BiasDetector):
    """
    Prüft auf Demographic Parity.
    
    Demographic Parity: Die Wahrscheinlichkeit eines positiven Ergebnisses
    sollte für alle Gruppen gleich sein.
    """
    
    def detect(
        self,
        interactions: List[Dict[str, Any]],
        protected_attribute: Optional[ProtectedAttribute] = None
    ) -> List[BiasMetric]:
        metrics = []
        
        if not interactions or not protected_attribute:
            return metrics
        
        # Gruppiere nach geschütztem Attribut
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for interaction in interactions:
            group_value = interaction.get(protected_attribute.value, "unknown")
            if group_value not in groups:
                groups[group_value] = []
            groups[group_value].append(interaction)
        
        if len(groups) < 2:
            return metrics
        
        # Berechne positive Outcome-Rate pro Gruppe
        group_rates: Dict[str, float] = {}
        for group_name, group_interactions in groups.items():
            positive = sum(
                1 for i in group_interactions 
                if i.get("outcome_positive", False)
            )
            rate = positive / len(group_interactions) if group_interactions else 0
            group_rates[group_name] = rate
        
        # Vergleiche Raten
        rates = list(group_rates.values())
        if not rates:
            return metrics
        
        avg_rate = statistics.mean(rates)
        max_deviation = max(abs(r - avg_rate) for r in rates) if rates else 0
        
        metric = BiasMetric(
            name=f"demographic_parity_{protected_attribute.value}",
            description=(
                f"Demographic Parity für {protected_attribute.value}: "
                f"Maximale Abweichung von {max_deviation:.2%}"
            ),
            bias_type=BiasType.DEMOGRAPHIC,
            protected_attribute=protected_attribute,
            current_value=max_deviation,
            baseline_value=0.0,  # Ideal: keine Abweichung
            threshold_warning=0.1,
            threshold_critical=0.2
        )
        
        metrics.append(metric)
        return metrics


class OutcomeDisparityDetector(BiasDetector):
    """
    Prüft auf Outcome-Disparitäten zwischen Gruppen.
    """
    
    def detect(
        self,
        interactions: List[Dict[str, Any]],
        protected_attribute: Optional[ProtectedAttribute] = None
    ) -> List[BiasMetric]:
        metrics = []
        
        if not interactions or not protected_attribute:
            return metrics
        
        # Gruppiere nach geschütztem Attribut
        groups: Dict[str, List[float]] = {}
        for interaction in interactions:
            group_value = interaction.get(protected_attribute.value, "unknown")
            outcome_score = interaction.get("outcome_score", 0.5)
            
            if group_value not in groups:
                groups[group_value] = []
            groups[group_value].append(outcome_score)
        
        if len(groups) < 2:
            return metrics
        
        # Berechne durchschnittlichen Outcome-Score pro Gruppe
        group_means: Dict[str, float] = {}
        for group_name, scores in groups.items():
            group_means[group_name] = statistics.mean(scores) if scores else 0
        
        # Finde maximale Disparität
        means = list(group_means.values())
        if len(means) < 2:
            return metrics
        
        max_disparity = max(means) - min(means)
        
        metric = BiasMetric(
            name=f"outcome_disparity_{protected_attribute.value}",
            description=(
                f"Outcome-Disparität für {protected_attribute.value}: "
                f"{max_disparity:.2%} Unterschied"
            ),
            bias_type=BiasType.OUTCOME,
            protected_attribute=protected_attribute,
            current_value=max_disparity,
            baseline_value=0.0,
            threshold_warning=0.15,
            threshold_critical=0.25
        )
        
        metrics.append(metric)
        return metrics


class GeographicBiasDetector(BiasDetector):
    """
    Erkennt geographischen Bias (z.B. Bundesland-Unterschiede).
    """
    
    def detect(
        self,
        interactions: List[Dict[str, Any]],
        protected_attribute: Optional[ProtectedAttribute] = None
    ) -> List[BiasMetric]:
        metrics = []
        
        if not interactions:
            return metrics
        
        # Gruppiere nach Region
        regions: Dict[str, List[float]] = {}
        for interaction in interactions:
            region = interaction.get("region", interaction.get("bundesland", "unknown"))
            quality_score = interaction.get("quality_score", interaction.get("outcome_score", 0.5))
            
            if region not in regions:
                regions[region] = []
            regions[region].append(quality_score)
        
        if len(regions) < 2:
            return metrics
        
        # Berechne regionale Unterschiede
        region_means: Dict[str, float] = {}
        for region_name, scores in regions.items():
            region_means[region_name] = statistics.mean(scores) if scores else 0
        
        means = list(region_means.values())
        if len(means) < 2:
            return metrics
        
        max_disparity = max(means) - min(means)
        std_dev = statistics.stdev(means) if len(means) > 1 else 0
        
        metric = BiasMetric(
            name="geographic_bias",
            description=(
                f"Geographische Qualitätsunterschiede: "
                f"Max. Disparität {max_disparity:.2%}, StdDev {std_dev:.2%}"
            ),
            bias_type=BiasType.GEOGRAPHIC,
            current_value=max_disparity,
            baseline_value=0.0,
            threshold_warning=0.1,
            threshold_critical=0.2
        )
        
        metrics.append(metric)
        return metrics


# =============================================================================
# Bias Monitoring Engine
# =============================================================================

class BiasMonitoringEngine:
    """
    Engine für kontinuierliches Bias-Monitoring.
    
    Features:
    - Kontinuierliche Überwachung von KI-Interaktionen
    - Mehrere Bias-Detektoren
    - Alerting bei erkanntem Bias
    - Reporting für AI Ethics Committee
    """
    
    def __init__(self):
        """Initialisiert die Bias Monitoring Engine."""
        self.configurations: Dict[UUID, MonitoringConfiguration] = {}
        self.detectors: List[BiasDetector] = []
        self.alerts: List[BiasAlert] = []
        self.reports: List[FairnessReport] = []
        self.interaction_buffer: Dict[UUID, List[Dict[str, Any]]] = {}
        
        # Standard-Detektoren registrieren
        self._register_default_detectors()
    
    def _register_default_detectors(self) -> None:
        """Registriert Standard-Bias-Detektoren."""
        self.detectors = [
            DemographicParityDetector(),
            OutcomeDisparityDetector(),
            GeographicBiasDetector()
        ]
    
    def add_detector(self, detector: BiasDetector) -> None:
        """Fügt einen Bias-Detektor hinzu."""
        self.detectors.append(detector)
    
    def configure_monitoring(
        self,
        ai_system_id: UUID,
        monitored_attributes: Optional[List[ProtectedAttribute]] = None,
        sampling_rate: float = 1.0,
        thresholds: Optional[Dict[str, float]] = None,
        alert_recipients: Optional[List[str]] = None
    ) -> MonitoringConfiguration:
        """
        Konfiguriert das Monitoring für ein KI-System.
        
        Args:
            ai_system_id: ID des KI-Systems
            monitored_attributes: Zu überwachende geschützte Attribute
            sampling_rate: Anteil der zu prüfenden Interaktionen
            thresholds: Schwellenwerte für Alerts
            alert_recipients: Empfänger von Alerts
            
        Returns:
            MonitoringConfiguration
        """
        if monitored_attributes is None:
            monitored_attributes = [
                ProtectedAttribute.GENDER,
                ProtectedAttribute.AGE,
                ProtectedAttribute.GEOGRAPHIC_ORIGIN
            ]
        
        config = MonitoringConfiguration(
            ai_system_id=ai_system_id,
            monitored_attributes=monitored_attributes,
            sampling_rate=sampling_rate,
            thresholds=thresholds or {},
            alert_recipients=alert_recipients or []
        )
        
        self.configurations[ai_system_id] = config
        self.interaction_buffer[ai_system_id] = []
        
        logger.info(
            f"Bias monitoring configured for system {ai_system_id}: "
            f"Attributes: {[a.value for a in monitored_attributes]}"
        )
        
        return config
    
    def record_interaction(
        self,
        ai_system_id: UUID,
        interaction: Dict[str, Any]
    ) -> None:
        """
        Zeichnet eine Interaktion für das Monitoring auf.
        
        Args:
            ai_system_id: ID des KI-Systems
            interaction: Interaktionsdaten mit Attributen und Outcome
        """
        config = self.configurations.get(ai_system_id)
        if not config or not config.enabled:
            return
        
        # Sampling
        import random
        if random.random() > config.sampling_rate:
            return
        
        # Zur Buffer hinzufügen
        if ai_system_id not in self.interaction_buffer:
            self.interaction_buffer[ai_system_id] = []
        
        # Timestamp hinzufügen falls nicht vorhanden
        if "timestamp" not in interaction:
            interaction["timestamp"] = datetime.utcnow().isoformat()
        
        self.interaction_buffer[ai_system_id].append(interaction)
        
        # Buffer begrenzen (z.B. letzte 10.000 Interaktionen)
        if len(self.interaction_buffer[ai_system_id]) > 10000:
            self.interaction_buffer[ai_system_id] = \
                self.interaction_buffer[ai_system_id][-10000:]
    
    def run_detection(
        self,
        ai_system_id: UUID,
        since: Optional[datetime] = None
    ) -> List[BiasMetric]:
        """
        Führt Bias-Detection für ein System durch.
        
        Args:
            ai_system_id: ID des KI-Systems
            since: Nur Interaktionen seit diesem Zeitpunkt
            
        Returns:
            Liste erkannter BiasMetrics
        """
        config = self.configurations.get(ai_system_id)
        if not config:
            return []
        
        interactions = self.interaction_buffer.get(ai_system_id, [])
        
        # Nach Zeitraum filtern
        if since:
            interactions = [
                i for i in interactions
                if datetime.fromisoformat(i.get("timestamp", "2000-01-01")) >= since
            ]
        
        if not interactions:
            return []
        
        all_metrics: List[BiasMetric] = []
        
        # Alle Detektoren ausführen
        for detector in self.detectors:
            for attribute in config.monitored_attributes:
                metrics = detector.detect(interactions, attribute)
                all_metrics.extend(metrics)
        
        # Alerts für kritische Metriken generieren
        for metric in all_metrics:
            if metric.get_severity() in [AlertSeverity.WARNING, AlertSeverity.CRITICAL]:
                self._generate_alert(ai_system_id, metric)
        
        return all_metrics
    
    def _generate_alert(
        self,
        ai_system_id: UUID,
        metric: BiasMetric
    ) -> BiasAlert:
        """Generiert einen Bias-Alert."""
        config = self.configurations.get(ai_system_id)
        
        # Prüfe Cooldown
        recent_alerts = [
            a for a in self.alerts
            if a.ai_system_id == ai_system_id
            and a.metric.name == metric.name
            and (datetime.utcnow() - a.created_at).total_seconds() < 
                (config.alert_cooldown_minutes * 60 if config else 3600)
        ]
        
        if recent_alerts:
            return recent_alerts[-1]  # Letzten Alert zurückgeben
        
        severity = metric.get_severity()
        
        alert = BiasAlert(
            ai_system_id=ai_system_id,
            metric=metric,
            severity=severity,
            message=(
                f"Bias erkannt: {metric.name} - "
                f"Abweichung von {metric.get_deviation():.1%} "
                f"(Schwelle: {metric.threshold_warning:.1%})"
            ),
            context={
                "current_value": metric.current_value,
                "baseline_value": metric.baseline_value,
                "deviation": metric.get_deviation()
            },
            affected_groups=[metric.protected_attribute.value] if metric.protected_attribute else []
        )
        
        self.alerts.append(alert)
        
        logger.warning(
            f"Bias Alert [{severity.name}] for system {ai_system_id}: "
            f"{metric.name} - {metric.get_deviation():.1%} deviation"
        )
        
        return alert
    
    def acknowledge_alert(
        self,
        alert_id: UUID,
        acknowledged_by: str
    ) -> Optional[BiasAlert]:
        """
        Bestätigt einen Alert.
        
        Args:
            alert_id: Alert-ID
            acknowledged_by: Bearbeiter
            
        Returns:
            Aktualisierter Alert oder None
        """
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged_at = datetime.utcnow()
                alert.acknowledged_by = acknowledged_by
                return alert
        return None
    
    def resolve_alert(
        self,
        alert_id: UUID,
        resolved_by: str,
        resolution_notes: str
    ) -> Optional[BiasAlert]:
        """
        Löst einen Alert.
        
        Args:
            alert_id: Alert-ID
            resolved_by: Bearbeiter
            resolution_notes: Lösungsnotizen
            
        Returns:
            Aktualisierter Alert oder None
        """
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved_at = datetime.utcnow()
                alert.resolved_by = resolved_by
                alert.resolution_notes = resolution_notes
                return alert
        return None
    
    def generate_fairness_report(
        self,
        ai_system_id: UUID,
        period_days: int = 30
    ) -> FairnessReport:
        """
        Generiert einen Fairness-Report.
        
        Args:
            ai_system_id: ID des KI-Systems
            period_days: Berichtszeitraum in Tagen
            
        Returns:
            FairnessReport
        """
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=period_days)
        
        # Aktuelle Metriken abrufen
        metrics = self.run_detection(ai_system_id, since=period_start)
        
        # Alerts im Zeitraum
        period_alerts = [
            a for a in self.alerts
            if a.ai_system_id == ai_system_id
            and a.created_at >= period_start
        ]
        
        alerts_resolved = sum(1 for a in period_alerts if a.resolved_at)
        alerts_pending = sum(1 for a in period_alerts if not a.resolved_at)
        
        # Berechne aggregierte Scores
        demographic_metrics = [
            m for m in metrics if m.bias_type == BiasType.DEMOGRAPHIC
        ]
        outcome_metrics = [
            m for m in metrics if m.bias_type == BiasType.OUTCOME
        ]
        
        # Score = 1 - durchschnittliche Abweichung (höher = fairer)
        demographic_parity = 1.0 - (
            statistics.mean([m.get_deviation() for m in demographic_metrics])
            if demographic_metrics else 0
        )
        
        equalized_odds = 1.0 - (
            statistics.mean([m.get_deviation() for m in outcome_metrics])
            if outcome_metrics else 0
        )
        
        overall_fairness = (demographic_parity + equalized_odds) / 2
        
        # Empfehlungen generieren
        recommendations = []
        
        if overall_fairness < 0.8:
            recommendations.append(
                "Gesamtfairness unter 80%: Umfassende Überprüfung empfohlen"
            )
        
        if demographic_parity < 0.85:
            recommendations.append(
                "Demographic Parity verbessern: Trainingsdaten auf Balance prüfen"
            )
        
        if alerts_pending > 0:
            recommendations.append(
                f"{alerts_pending} offene Alerts bearbeiten"
            )
        
        high_deviation_metrics = [
            m for m in metrics if m.get_deviation() > 0.15
        ]
        for m in high_deviation_metrics[:3]:  # Top 3
            recommendations.append(
                f"Metrik '{m.name}' prüfen: {m.get_deviation():.1%} Abweichung"
            )
        
        report = FairnessReport(
            ai_system_id=ai_system_id,
            reporting_period_start=period_start,
            reporting_period_end=period_end,
            metrics=metrics,
            demographic_parity_score=demographic_parity,
            equalized_odds_score=equalized_odds,
            overall_fairness_score=overall_fairness,
            alerts_triggered=len(period_alerts),
            alerts_resolved=alerts_resolved,
            alerts_pending=alerts_pending,
            recommendations=recommendations
        )
        
        self.reports.append(report)
        
        logger.info(
            f"Fairness report generated for system {ai_system_id}: "
            f"Overall score {overall_fairness:.1%}"
        )
        
        return report
    
    def get_pending_alerts(
        self,
        ai_system_id: Optional[UUID] = None
    ) -> List[BiasAlert]:
        """Gibt alle offenen Alerts zurück."""
        alerts = self.alerts
        
        if ai_system_id:
            alerts = [a for a in alerts if a.ai_system_id == ai_system_id]
        
        return [a for a in alerts if not a.resolved_at]
    
    def get_monitoring_summary(
        self,
        ai_system_id: UUID
    ) -> Dict[str, Any]:
        """
        Gibt eine Zusammenfassung des Monitorings zurück.
        
        Args:
            ai_system_id: ID des KI-Systems
            
        Returns:
            Summary Dictionary
        """
        config = self.configurations.get(ai_system_id)
        interactions = self.interaction_buffer.get(ai_system_id, [])
        system_alerts = [a for a in self.alerts if a.ai_system_id == ai_system_id]
        system_reports = [r for r in self.reports if r.ai_system_id == ai_system_id]
        
        return {
            "ai_system_id": str(ai_system_id),
            "monitoring_enabled": config.enabled if config else False,
            "sampling_rate": config.sampling_rate if config else 0,
            "monitored_attributes": (
                [a.value for a in config.monitored_attributes] 
                if config else []
            ),
            "interactions_buffered": len(interactions),
            "total_alerts": len(system_alerts),
            "pending_alerts": sum(1 for a in system_alerts if not a.resolved_at),
            "critical_alerts": sum(
                1 for a in system_alerts 
                if a.severity == AlertSeverity.CRITICAL and not a.resolved_at
            ),
            "total_reports": len(system_reports),
            "latest_report": (
                system_reports[-1].report_date.isoformat() 
                if system_reports else None
            ),
            "latest_fairness_score": (
                system_reports[-1].overall_fairness_score 
                if system_reports else None
            )
        }


# =============================================================================
# Factory Functions
# =============================================================================

def create_bias_monitoring_engine() -> BiasMonitoringEngine:
    """
    Erstellt eine Bias Monitoring Engine.
    
    Returns:
        Konfigurierte BiasMonitoringEngine
    """
    return BiasMonitoringEngine()


def setup_vcc_monitoring(
    engine: BiasMonitoringEngine,
    system_ids: Dict[str, UUID]
) -> None:
    """
    Konfiguriert Bias-Monitoring für VCC-Systeme.
    
    Args:
        engine: Bias Monitoring Engine
        system_ids: Dictionary mit System-IDs
    """
    # Veritas - Legal Research (alle Attribute)
    if "veritas" in system_ids:
        engine.configure_monitoring(
            ai_system_id=system_ids["veritas"],
            monitored_attributes=[
                ProtectedAttribute.GENDER,
                ProtectedAttribute.AGE,
                ProtectedAttribute.GEOGRAPHIC_ORIGIN,
                ProtectedAttribute.NATIONALITY
            ],
            sampling_rate=1.0,
            alert_recipients=["ai-ethics@example.org"]
        )
    
    # Clara - Document Generation
    if "clara" in system_ids:
        engine.configure_monitoring(
            ai_system_id=system_ids["clara"],
            monitored_attributes=[
                ProtectedAttribute.GENDER,
                ProtectedAttribute.AGE
            ],
            sampling_rate=0.5,
            alert_recipients=["ai-ethics@example.org"]
        )
    
    # Covina - Process Automation
    if "covina" in system_ids:
        engine.configure_monitoring(
            ai_system_id=system_ids["covina"],
            monitored_attributes=[
                ProtectedAttribute.GEOGRAPHIC_ORIGIN
            ],
            sampling_rate=0.25,
            alert_recipients=["ai-ethics@example.org"]
        )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "BiasType",
    "ProtectedAttribute",
    "AlertSeverity",
    "MonitoringStatus",
    # Data Models
    "BiasMetric",
    "BiasAlert",
    "FairnessReport",
    "MonitoringConfiguration",
    # Detectors
    "BiasDetector",
    "DemographicParityDetector",
    "OutcomeDisparityDetector",
    "GeographicBiasDetector",
    # Engine
    "BiasMonitoringEngine",
    # Factory Functions
    "create_bias_monitoring_engine",
    "setup_vcc_monitoring",
]
