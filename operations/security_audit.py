#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VCC-UDS3 Security Audit Module (v3.0.0)

Security audit framework for ISO 27001, SOC 2, and BSI C5 compliance.
Supports independent security audits and continuous compliance monitoring.

Author: VCC Development Team
License: MIT with Government Partnership Commons Clause
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional
import hashlib
import json
import logging
import uuid

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================

class ComplianceFramework(str, Enum):
    """Supported compliance frameworks."""
    ISO_27001 = "iso_27001"
    SOC_2_TYPE_II = "soc_2_type_ii"
    BSI_C5 = "bsi_c5"
    BSI_IT_GRUNDSCHUTZ = "bsi_it_grundschutz"
    DSGVO = "dsgvo"
    EU_AI_ACT = "eu_ai_act"


class ControlCategory(str, Enum):
    """Security control categories (ISO 27001 aligned)."""
    ORGANIZATIONAL = "organizational"
    PEOPLE = "people"
    PHYSICAL = "physical"
    TECHNOLOGICAL = "technological"


class RiskLevel(str, Enum):
    """Risk severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"


class FindingSeverity(str, Enum):
    """Audit finding severity."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    OBSERVATION = "observation"
    BEST_PRACTICE = "best_practice"


class ControlStatus(str, Enum):
    """Control implementation status."""
    FULLY_IMPLEMENTED = "fully_implemented"
    PARTIALLY_IMPLEMENTED = "partially_implemented"
    PLANNED = "planned"
    NOT_APPLICABLE = "not_applicable"
    NOT_IMPLEMENTED = "not_implemented"


class AuditStatus(str, Enum):
    """Audit status."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REPORT_PENDING = "report_pending"
    CLOSED = "closed"


class RemediationStatus(str, Enum):
    """Remediation action status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REMEDIATED = "remediated"
    VERIFIED = "verified"
    ACCEPTED_RISK = "accepted_risk"
    CLOSED = "closed"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class SecurityControl:
    """Security control definition."""
    control_id: str
    name: str
    description: str
    category: ControlCategory
    framework: ComplianceFramework
    
    # Implementation details
    status: ControlStatus = ControlStatus.NOT_IMPLEMENTED
    implementation_notes: str = ""
    owner: str = ""
    due_date: Optional[datetime] = None
    
    # Evidence
    evidence_required: List[str] = field(default_factory=list)
    evidence_collected: List[str] = field(default_factory=list)
    
    # Testing
    last_tested: Optional[datetime] = None
    test_result: str = ""
    
    # Risk
    residual_risk: RiskLevel = RiskLevel.MEDIUM


@dataclass
class AuditFinding:
    """Security audit finding."""
    finding_id: str
    title: str
    description: str
    severity: FindingSeverity
    framework: ComplianceFramework
    affected_controls: list[str] = field(default_factory=list)
    
    # Details
    root_cause: str = ""
    evidence: list[str] = field(default_factory=list)
    recommendation: str = ""
    
    # Tracking
    discovered_date: datetime = field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    status: RemediationStatus = RemediationStatus.OPEN
    assignee: str = ""
    
    # Risk assessment
    likelihood: int = 3  # 1-5 scale
    impact: int = 3  # 1-5 scale
    
    @property
    def risk_score(self) -> int:
        """Calculate risk score (likelihood * impact)."""
        return self.likelihood * self.impact


@dataclass
class AuditReport:
    """Security audit report."""
    report_id: str
    audit_type: str
    framework: ComplianceFramework
    scope: str
    
    # Timing
    start_date: datetime
    end_date: datetime
    report_date: datetime = field(default_factory=datetime.utcnow)
    
    # Results
    findings: list[AuditFinding] = field(default_factory=list)
    controls_assessed: int = 0
    controls_passed: int = 0
    controls_failed: int = 0
    
    # Summary
    executive_summary: str = ""
    conclusion: str = ""
    auditor: str = ""
    auditor_organization: str = ""
    
    # Certification
    certification_granted: bool = False
    certification_valid_until: Optional[datetime] = None
    
    @property
    def pass_rate(self) -> float:
        """Calculate control pass rate."""
        if self.controls_assessed == 0:
            return 0.0
        return self.controls_passed / self.controls_assessed * 100


@dataclass
class RemediationAction:
    """Remediation action for a finding."""
    action_id: str
    finding_id: str
    description: str
    assignee: str
    
    # Planning
    planned_date: datetime
    actual_date: Optional[datetime] = None
    
    # Status
    status: RemediationStatus = RemediationStatus.OPEN
    progress_notes: str = ""
    
    # Verification
    verification_method: str = ""
    verified_by: str = ""
    verification_date: Optional[datetime] = None


# =============================================================================
# ISO 27001 Controls
# =============================================================================

class ISO27001Controls:
    """ISO 27001:2022 security controls for VCC-UDS3."""
    
    @staticmethod
    def get_organizational_controls() -> list[SecurityControl]:
        """Get organizational controls (A.5)."""
        return [
            SecurityControl(
                control_id="A.5.1",
                name="Policies for information security",
                description="Information security policy and topic-specific policies shall be defined, approved by management, published, communicated to and acknowledged by relevant personnel and relevant interested parties, and reviewed at planned intervals and if significant changes occur.",
                category=ControlCategory.ORGANIZATIONAL,
                framework=ComplianceFramework.ISO_27001,
                evidence_required=[
                    "Information Security Policy document",
                    "Policy acknowledgment records",
                    "Policy review records",
                ],
            ),
            SecurityControl(
                control_id="A.5.2",
                name="Information security roles and responsibilities",
                description="Information security roles and responsibilities shall be defined and allocated according to the organization needs.",
                category=ControlCategory.ORGANIZATIONAL,
                framework=ComplianceFramework.ISO_27001,
                evidence_required=[
                    "Role definitions",
                    "Responsibility matrix",
                    "Organization chart",
                ],
            ),
            SecurityControl(
                control_id="A.5.3",
                name="Segregation of duties",
                description="Conflicting duties and conflicting areas of responsibility shall be segregated.",
                category=ControlCategory.ORGANIZATIONAL,
                framework=ComplianceFramework.ISO_27001,
                evidence_required=[
                    "Segregation of duties matrix",
                    "Access control records",
                    "Role conflict analysis",
                ],
            ),
            SecurityControl(
                control_id="A.5.7",
                name="Threat intelligence",
                description="Information relating to information security threats shall be collected and analyzed to produce threat intelligence.",
                category=ControlCategory.ORGANIZATIONAL,
                framework=ComplianceFramework.ISO_27001,
                evidence_required=[
                    "Threat intelligence feeds",
                    "Threat analysis reports",
                    "Threat response procedures",
                ],
            ),
            SecurityControl(
                control_id="A.5.8",
                name="Information security in project management",
                description="Information security shall be integrated into project management.",
                category=ControlCategory.ORGANIZATIONAL,
                framework=ComplianceFramework.ISO_27001,
                evidence_required=[
                    "Security requirements in project plans",
                    "Security gate reviews",
                    "Project security assessments",
                ],
            ),
        ]
    
    @staticmethod
    def get_technological_controls() -> list[SecurityControl]:
        """Get technological controls (A.8)."""
        return [
            SecurityControl(
                control_id="A.8.1",
                name="User endpoint devices",
                description="Information stored on, processed by or accessible via user endpoint devices shall be protected.",
                category=ControlCategory.TECHNOLOGICAL,
                framework=ComplianceFramework.ISO_27001,
                evidence_required=[
                    "Endpoint protection configuration",
                    "Device management policy",
                    "Endpoint security scanning results",
                ],
            ),
            SecurityControl(
                control_id="A.8.2",
                name="Privileged access rights",
                description="The allocation and use of privileged access rights shall be restricted and managed.",
                category=ControlCategory.TECHNOLOGICAL,
                framework=ComplianceFramework.ISO_27001,
                evidence_required=[
                    "Privileged access inventory",
                    "Access review records",
                    "PAM tool configuration",
                ],
            ),
            SecurityControl(
                control_id="A.8.3",
                name="Information access restriction",
                description="Access to information and other associated assets shall be restricted in accordance with the established topic-specific policy on access control.",
                category=ControlCategory.TECHNOLOGICAL,
                framework=ComplianceFramework.ISO_27001,
                evidence_required=[
                    "Access control matrix",
                    "RBAC configuration",
                    "Access logs",
                ],
            ),
            SecurityControl(
                control_id="A.8.5",
                name="Secure authentication",
                description="Secure authentication technologies and procedures shall be implemented based on information access restrictions and the topic-specific policy on access control.",
                category=ControlCategory.TECHNOLOGICAL,
                framework=ComplianceFramework.ISO_27001,
                evidence_required=[
                    "Authentication configuration",
                    "MFA implementation",
                    "Password policy",
                ],
            ),
            SecurityControl(
                control_id="A.8.9",
                name="Configuration management",
                description="Configurations, including security configurations, of hardware, software, services and networks shall be established, documented, implemented, monitored and reviewed.",
                category=ControlCategory.TECHNOLOGICAL,
                framework=ComplianceFramework.ISO_27001,
                evidence_required=[
                    "Configuration baselines",
                    "Configuration management procedures",
                    "Configuration audit reports",
                ],
            ),
            SecurityControl(
                control_id="A.8.12",
                name="Data leakage prevention",
                description="Data leakage prevention measures shall be applied to systems, networks and any other devices that process, store or transmit sensitive information.",
                category=ControlCategory.TECHNOLOGICAL,
                framework=ComplianceFramework.ISO_27001,
                evidence_required=[
                    "DLP policy",
                    "DLP tool configuration",
                    "DLP incident reports",
                ],
            ),
            SecurityControl(
                control_id="A.8.15",
                name="Logging",
                description="Logs that record activities, exceptions, faults and other relevant events shall be produced, stored, protected and analyzed.",
                category=ControlCategory.TECHNOLOGICAL,
                framework=ComplianceFramework.ISO_27001,
                evidence_required=[
                    "Logging policy",
                    "Log retention configuration",
                    "Log analysis reports",
                ],
            ),
            SecurityControl(
                control_id="A.8.16",
                name="Monitoring activities",
                description="Networks, systems and applications shall be monitored for anomalous behavior and appropriate actions taken to evaluate potential information security incidents.",
                category=ControlCategory.TECHNOLOGICAL,
                framework=ComplianceFramework.ISO_27001,
                evidence_required=[
                    "Monitoring configuration",
                    "Alert rules",
                    "Incident response procedures",
                ],
            ),
            SecurityControl(
                control_id="A.8.20",
                name="Networks security",
                description="Networks and network devices shall be secured, managed and controlled to protect information in systems and applications.",
                category=ControlCategory.TECHNOLOGICAL,
                framework=ComplianceFramework.ISO_27001,
                evidence_required=[
                    "Network segmentation design",
                    "Firewall rules",
                    "Network security scanning",
                ],
            ),
            SecurityControl(
                control_id="A.8.24",
                name="Use of cryptography",
                description="Rules for the effective use of cryptography, including cryptographic key management, shall be defined and implemented.",
                category=ControlCategory.TECHNOLOGICAL,
                framework=ComplianceFramework.ISO_27001,
                evidence_required=[
                    "Cryptography policy",
                    "Key management procedures",
                    "Encryption configuration",
                ],
            ),
            SecurityControl(
                control_id="A.8.25",
                name="Secure development lifecycle",
                description="Rules for the secure development of software and systems shall be established and applied.",
                category=ControlCategory.TECHNOLOGICAL,
                framework=ComplianceFramework.ISO_27001,
                evidence_required=[
                    "Secure SDLC procedures",
                    "Security code reviews",
                    "Security testing results",
                ],
            ),
            SecurityControl(
                control_id="A.8.28",
                name="Secure coding",
                description="Secure coding principles shall be applied to software development.",
                category=ControlCategory.TECHNOLOGICAL,
                framework=ComplianceFramework.ISO_27001,
                evidence_required=[
                    "Secure coding guidelines",
                    "Static analysis results",
                    "Code review records",
                ],
            ),
        ]
    
    @staticmethod
    def get_all_controls() -> list[SecurityControl]:
        """Get all ISO 27001 controls."""
        return (
            ISO27001Controls.get_organizational_controls() +
            ISO27001Controls.get_technological_controls()
        )


# =============================================================================
# Security Audit Engine
# =============================================================================

class SecurityAuditEngine:
    """
    Security audit engine for VCC-UDS3.
    
    Features:
    - Multi-framework support (ISO 27001, SOC 2, BSI C5)
    - Control assessment tracking
    - Finding management
    - Remediation workflow
    - Certification tracking
    """
    
    def __init__(self):
        self.controls: dict[str, SecurityControl] = {}
        self.findings: dict[str, AuditFinding] = {}
        self.reports: dict[str, AuditReport] = {}
        self.remediation_actions: dict[str, RemediationAction] = {}
        
        # Load default controls
        self._load_default_controls()
    
    def _load_default_controls(self) -> None:
        """Load default security controls."""
        for control in ISO27001Controls.get_all_controls():
            self.controls[control.control_id] = control
        
        logger.info(f"Loaded {len(self.controls)} security controls")
    
    def register_control(self, control: SecurityControl) -> None:
        """Register a security control."""
        self.controls[control.control_id] = control
        logger.debug(f"Registered control: {control.control_id}")
    
    def update_control_status(
        self,
        control_id: str,
        status: ControlStatus,
        implementation_notes: str = "",
        evidence: list[str] = None
    ) -> SecurityControl:
        """Update control implementation status."""
        if control_id not in self.controls:
            raise ValueError(f"Control {control_id} not found")
        
        control = self.controls[control_id]
        control.status = status
        control.implementation_notes = implementation_notes
        
        if evidence:
            control.evidence_collected.extend(evidence)
        
        logger.info(f"Updated control {control_id} status to {status.value}")
        return control
    
    def create_finding(
        self,
        title: str,
        description: str,
        severity: FindingSeverity,
        framework: ComplianceFramework,
        affected_controls: list[str] = None,
        recommendation: str = "",
        root_cause: str = ""
    ) -> AuditFinding:
        """Create a new audit finding."""
        finding_id = f"FIND-{str(uuid.uuid4())[:8].upper()}"
        
        finding = AuditFinding(
            finding_id=finding_id,
            title=title,
            description=description,
            severity=severity,
            framework=framework,
            affected_controls=affected_controls or [],
            recommendation=recommendation,
            root_cause=root_cause,
        )
        
        # Set due date based on severity
        if severity == FindingSeverity.CRITICAL:
            finding.due_date = datetime.utcnow() + timedelta(days=7)
        elif severity == FindingSeverity.MAJOR:
            finding.due_date = datetime.utcnow() + timedelta(days=30)
        elif severity == FindingSeverity.MINOR:
            finding.due_date = datetime.utcnow() + timedelta(days=90)
        else:
            finding.due_date = datetime.utcnow() + timedelta(days=180)
        
        self.findings[finding_id] = finding
        logger.info(f"Created finding: {finding_id} - {title}")
        
        return finding
    
    def create_remediation_action(
        self,
        finding_id: str,
        description: str,
        assignee: str,
        planned_date: datetime
    ) -> RemediationAction:
        """Create a remediation action for a finding."""
        if finding_id not in self.findings:
            raise ValueError(f"Finding {finding_id} not found")
        
        action_id = f"REM-{str(uuid.uuid4())[:8].upper()}"
        
        action = RemediationAction(
            action_id=action_id,
            finding_id=finding_id,
            description=description,
            assignee=assignee,
            planned_date=planned_date,
        )
        
        self.remediation_actions[action_id] = action
        logger.info(f"Created remediation action: {action_id}")
        
        return action
    
    def update_remediation_status(
        self,
        action_id: str,
        status: RemediationStatus,
        progress_notes: str = ""
    ) -> RemediationAction:
        """Update remediation action status."""
        if action_id not in self.remediation_actions:
            raise ValueError(f"Remediation action {action_id} not found")
        
        action = self.remediation_actions[action_id]
        action.status = status
        action.progress_notes = progress_notes
        
        if status == RemediationStatus.REMEDIATED:
            action.actual_date = datetime.utcnow()
        
        logger.info(f"Updated remediation {action_id} to {status.value}")
        return action
    
    def verify_remediation(
        self,
        action_id: str,
        verified_by: str,
        verification_method: str
    ) -> RemediationAction:
        """Verify a remediation action."""
        if action_id not in self.remediation_actions:
            raise ValueError(f"Remediation action {action_id} not found")
        
        action = self.remediation_actions[action_id]
        action.status = RemediationStatus.VERIFIED
        action.verified_by = verified_by
        action.verification_method = verification_method
        action.verification_date = datetime.utcnow()
        
        # Also update finding status
        finding = self.findings.get(action.finding_id)
        if finding:
            # Check if all remediation actions are verified
            related_actions = [
                a for a in self.remediation_actions.values()
                if a.finding_id == action.finding_id
            ]
            if all(a.status == RemediationStatus.VERIFIED for a in related_actions):
                finding.status = RemediationStatus.CLOSED
        
        logger.info(f"Verified remediation {action_id} by {verified_by}")
        return action
    
    def conduct_audit(
        self,
        framework: ComplianceFramework,
        scope: str,
        auditor: str,
        auditor_organization: str = "Internal",
        controls_to_assess: list[str] = None
    ) -> AuditReport:
        """Conduct a security audit."""
        report_id = f"AUDIT-{str(uuid.uuid4())[:8].upper()}"
        start_date = datetime.utcnow()
        
        # Filter controls by framework
        relevant_controls = [
            c for c in self.controls.values()
            if c.framework == framework
        ]
        
        if controls_to_assess:
            relevant_controls = [
                c for c in relevant_controls
                if c.control_id in controls_to_assess
            ]
        
        # Assess controls
        passed = 0
        failed = 0
        findings = []
        
        for control in relevant_controls:
            control.last_tested = datetime.utcnow()
            
            if control.status == ControlStatus.FULLY_IMPLEMENTED:
                passed += 1
                control.test_result = "PASS"
            elif control.status == ControlStatus.NOT_APPLICABLE:
                passed += 1
                control.test_result = "N/A"
            elif control.status == ControlStatus.PARTIALLY_IMPLEMENTED:
                failed += 1
                control.test_result = "PARTIAL"
                
                # Create finding for partial implementation
                finding = self.create_finding(
                    title=f"Partial implementation of {control.control_id}",
                    description=f"Control {control.name} is only partially implemented.",
                    severity=FindingSeverity.MINOR,
                    framework=framework,
                    affected_controls=[control.control_id],
                    recommendation="Complete implementation of all control requirements.",
                )
                findings.append(finding)
            else:
                failed += 1
                control.test_result = "FAIL"
                
                # Create finding for missing implementation
                finding = self.create_finding(
                    title=f"Missing implementation of {control.control_id}",
                    description=f"Control {control.name} is not implemented.",
                    severity=FindingSeverity.MAJOR,
                    framework=framework,
                    affected_controls=[control.control_id],
                    recommendation="Implement the required control.",
                )
                findings.append(finding)
        
        end_date = datetime.utcnow()
        
        # Determine certification eligibility
        pass_rate = passed / len(relevant_controls) * 100 if relevant_controls else 0
        critical_findings = [f for f in findings if f.severity == FindingSeverity.CRITICAL]
        major_findings = [f for f in findings if f.severity == FindingSeverity.MAJOR]
        
        certification_granted = (
            pass_rate >= 90 and
            len(critical_findings) == 0 and
            len(major_findings) <= 3
        )
        
        # Create report
        report = AuditReport(
            report_id=report_id,
            audit_type="Compliance Audit",
            framework=framework,
            scope=scope,
            start_date=start_date,
            end_date=end_date,
            findings=findings,
            controls_assessed=len(relevant_controls),
            controls_passed=passed,
            controls_failed=failed,
            executive_summary=self._generate_executive_summary(
                framework,
                len(relevant_controls),
                passed,
                findings
            ),
            conclusion=self._generate_conclusion(
                certification_granted,
                pass_rate,
                len(critical_findings),
                len(major_findings)
            ),
            auditor=auditor,
            auditor_organization=auditor_organization,
            certification_granted=certification_granted,
            certification_valid_until=(
                datetime.utcnow() + timedelta(days=365)
                if certification_granted else None
            ),
        )
        
        self.reports[report_id] = report
        logger.info(
            f"Audit completed: {report_id}, Pass rate: {pass_rate:.1f}%, "
            f"Certification: {certification_granted}"
        )
        
        return report
    
    def _generate_executive_summary(
        self,
        framework: ComplianceFramework,
        total_controls: int,
        passed: int,
        findings: list[AuditFinding]
    ) -> str:
        """Generate executive summary for audit report."""
        pass_rate = passed / total_controls * 100 if total_controls else 0
        
        critical = len([f for f in findings if f.severity == FindingSeverity.CRITICAL])
        major = len([f for f in findings if f.severity == FindingSeverity.MAJOR])
        minor = len([f for f in findings if f.severity == FindingSeverity.MINOR])
        
        return f"""
EXECUTIVE SUMMARY

Framework: {framework.value.upper()}
Assessment Date: {datetime.utcnow().strftime('%Y-%m-%d')}

Controls Assessed: {total_controls}
Controls Passed: {passed} ({pass_rate:.1f}%)
Controls Failed: {total_controls - passed}

Findings Summary:
- Critical: {critical}
- Major: {major}
- Minor: {minor}
- Total: {len(findings)}

VCC-UDS3 has been assessed against the {framework.value} framework requirements.
The assessment covered {total_controls} security controls across organizational
and technological categories.
"""
    
    def _generate_conclusion(
        self,
        certification_granted: bool,
        pass_rate: float,
        critical_count: int,
        major_count: int
    ) -> str:
        """Generate conclusion for audit report."""
        if certification_granted:
            return f"""
CONCLUSION

Based on the assessment conducted, VCC-UDS3 has demonstrated compliance
with the framework requirements. The organization has achieved a control
pass rate of {pass_rate:.1f}% with no critical findings and {major_count}
major findings.

CERTIFICATION STATUS: GRANTED

The certification is valid for one year from the date of issuance.
Annual surveillance audits are required to maintain certification.
"""
        else:
            return f"""
CONCLUSION

Based on the assessment conducted, VCC-UDS3 has not yet achieved full
compliance with the framework requirements. The organization has achieved
a control pass rate of {pass_rate:.1f}% with {critical_count} critical
and {major_count} major findings.

CERTIFICATION STATUS: NOT GRANTED

The following remediation actions are required before certification
can be granted:
1. Address all critical findings within 7 days
2. Address all major findings within 30 days
3. Achieve a control pass rate of at least 90%

A follow-up assessment will be scheduled after remediation is complete.
"""
    
    def get_compliance_dashboard(self) -> dict[str, Any]:
        """Get compliance dashboard data."""
        total_controls = len(self.controls)
        implemented = len([
            c for c in self.controls.values()
            if c.status == ControlStatus.FULLY_IMPLEMENTED
        ])
        partial = len([
            c for c in self.controls.values()
            if c.status == ControlStatus.PARTIALLY_IMPLEMENTED
        ])
        not_implemented = len([
            c for c in self.controls.values()
            if c.status == ControlStatus.NOT_IMPLEMENTED
        ])
        
        open_findings = len([
            f for f in self.findings.values()
            if f.status in [RemediationStatus.OPEN, RemediationStatus.IN_PROGRESS]
        ])
        
        critical_findings = len([
            f for f in self.findings.values()
            if f.severity == FindingSeverity.CRITICAL and
            f.status not in [RemediationStatus.CLOSED, RemediationStatus.VERIFIED]
        ])
        
        overdue_findings = len([
            f for f in self.findings.values()
            if f.due_date and f.due_date < datetime.utcnow() and
            f.status not in [RemediationStatus.CLOSED, RemediationStatus.VERIFIED]
        ])
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "controls": {
                "total": total_controls,
                "fully_implemented": implemented,
                "partially_implemented": partial,
                "not_implemented": not_implemented,
                "implementation_rate": (
                    implemented / total_controls * 100 if total_controls else 0
                ),
            },
            "findings": {
                "total": len(self.findings),
                "open": open_findings,
                "critical_open": critical_findings,
                "overdue": overdue_findings,
            },
            "audits": {
                "total": len(self.reports),
                "certifications_granted": len([
                    r for r in self.reports.values()
                    if r.certification_granted
                ]),
            },
            "risk_score": self._calculate_overall_risk_score(),
        }
    
    def _calculate_overall_risk_score(self) -> int:
        """Calculate overall risk score (0-100, lower is better)."""
        if not self.findings:
            return 0
        
        # Weight by severity
        weights = {
            FindingSeverity.CRITICAL: 25,
            FindingSeverity.MAJOR: 10,
            FindingSeverity.MINOR: 3,
            FindingSeverity.OBSERVATION: 1,
            FindingSeverity.BEST_PRACTICE: 0,
        }
        
        open_findings = [
            f for f in self.findings.values()
            if f.status not in [RemediationStatus.CLOSED, RemediationStatus.VERIFIED]
        ]
        
        total_weight = sum(weights[f.severity] for f in open_findings)
        
        # Cap at 100
        return min(100, total_weight)


# =============================================================================
# VCC-UDS3 Security Controls
# =============================================================================

def get_vcc_uds3_controls() -> list[SecurityControl]:
    """Get VCC-UDS3 specific security controls."""
    return [
        SecurityControl(
            control_id="VCC.SEC.001",
            name="PKI Certificate Management",
            description="VCC-PKI integration for certificate-based authentication and integrity verification.",
            category=ControlCategory.TECHNOLOGICAL,
            framework=ComplianceFramework.ISO_27001,
            status=ControlStatus.FULLY_IMPLEMENTED,
            evidence_required=[
                "PKI architecture documentation",
                "Certificate issuance procedures",
                "Certificate revocation process",
            ],
            evidence_collected=[
                "security/pki.py implementation",
                "Certificate lifecycle management",
                "CRL/OCSP integration",
            ],
        ),
        SecurityControl(
            control_id="VCC.SEC.002",
            name="RBAC Implementation",
            description="Role-Based Access Control for database and API access.",
            category=ControlCategory.TECHNOLOGICAL,
            framework=ComplianceFramework.ISO_27001,
            status=ControlStatus.FULLY_IMPLEMENTED,
            evidence_required=[
                "RBAC policy documentation",
                "Role definitions",
                "Access matrix",
            ],
            evidence_collected=[
                "security/rbac.py implementation",
                "Role hierarchy configuration",
                "Permission enforcement",
            ],
        ),
        SecurityControl(
            control_id="VCC.SEC.003",
            name="Row-Level Security",
            description="PostgreSQL RLS for tenant and document isolation.",
            category=ControlCategory.TECHNOLOGICAL,
            framework=ComplianceFramework.ISO_27001,
            status=ControlStatus.FULLY_IMPLEMENTED,
            evidence_required=[
                "RLS policy documentation",
                "Policy enforcement testing",
                "Isolation verification",
            ],
            evidence_collected=[
                "database/rls.py implementation",
                "Tenant isolation policies",
                "Security policy configuration",
            ],
        ),
        SecurityControl(
            control_id="VCC.SEC.004",
            name="Audit Logging",
            description="Comprehensive audit logging for all database operations.",
            category=ControlCategory.TECHNOLOGICAL,
            framework=ComplianceFramework.ISO_27001,
            status=ControlStatus.FULLY_IMPLEMENTED,
            evidence_required=[
                "Audit log schema",
                "Log retention policy",
                "Log integrity protection",
            ],
            evidence_collected=[
                "core/audit.py implementation",
                "PostgreSQL audit triggers",
                "Log analysis capabilities",
            ],
        ),
        SecurityControl(
            control_id="VCC.SEC.005",
            name="Data Encryption",
            description="Encryption at rest and in transit for all sensitive data.",
            category=ControlCategory.TECHNOLOGICAL,
            framework=ComplianceFramework.ISO_27001,
            status=ControlStatus.FULLY_IMPLEMENTED,
            evidence_required=[
                "Encryption standards",
                "Key management procedures",
                "TLS configuration",
            ],
            evidence_collected=[
                "TLS 1.3 enforcement",
                "PostgreSQL encryption",
                "VCC-PKI key management",
            ],
        ),
        SecurityControl(
            control_id="VCC.SEC.006",
            name="DSGVO Compliance",
            description="GDPR/DSGVO compliance features including PII tracking, anonymization, and data subject rights.",
            category=ControlCategory.ORGANIZATIONAL,
            framework=ComplianceFramework.DSGVO,
            status=ControlStatus.FULLY_IMPLEMENTED,
            evidence_required=[
                "Data processing register",
                "Privacy impact assessment",
                "Data subject rights procedures",
            ],
            evidence_collected=[
                "compliance/gdpr.py implementation",
                "PII tracking system",
                "Anonymization functions",
                "Data retention policies",
            ],
        ),
        SecurityControl(
            control_id="VCC.SEC.007",
            name="SAGA Transaction Security",
            description="Security controls for distributed SAGA transactions.",
            category=ControlCategory.TECHNOLOGICAL,
            framework=ComplianceFramework.ISO_27001,
            status=ControlStatus.FULLY_IMPLEMENTED,
            evidence_required=[
                "SAGA security model",
                "Compensation handling",
                "Transaction isolation",
            ],
            evidence_collected=[
                "saga/saga_coordinator.py implementation",
                "Atomic operations",
                "Rollback security",
            ],
        ),
        SecurityControl(
            control_id="VCC.SEC.008",
            name="LoRA Adapter Integrity",
            description="PKI-signed LoRA adapters for ML model integrity verification.",
            category=ControlCategory.TECHNOLOGICAL,
            framework=ComplianceFramework.EU_AI_ACT,
            status=ControlStatus.FULLY_IMPLEMENTED,
            evidence_required=[
                "Adapter signing process",
                "Signature verification",
                "Revocation handling",
            ],
            evidence_collected=[
                "training/peft_manager.py implementation",
                "PKI signature integration",
                "Adapter lifecycle management",
            ],
        ),
    ]


# =============================================================================
# Factory Functions
# =============================================================================

def create_security_audit_engine() -> SecurityAuditEngine:
    """Create a new security audit engine."""
    engine = SecurityAuditEngine()
    
    # Register VCC-UDS3 specific controls
    for control in get_vcc_uds3_controls():
        engine.register_control(control)
    
    return engine


def prepare_iso_27001_audit(engine: SecurityAuditEngine) -> None:
    """Prepare for ISO 27001 audit by updating control status."""
    vcc_controls = get_vcc_uds3_controls()
    
    for control in vcc_controls:
        engine.update_control_status(
            control.control_id,
            control.status,
            control.implementation_notes,
            control.evidence_collected,
        )


def conduct_pre_audit_assessment(
    engine: SecurityAuditEngine,
    framework: ComplianceFramework = ComplianceFramework.ISO_27001
) -> dict:
    """Conduct a pre-audit assessment to identify gaps."""
    controls = [
        c for c in engine.controls.values()
        if c.framework == framework
    ]
    
    gaps = []
    ready = []
    
    for control in controls:
        if control.status == ControlStatus.FULLY_IMPLEMENTED:
            if len(control.evidence_collected) >= len(control.evidence_required):
                ready.append(control.control_id)
            else:
                gaps.append({
                    "control_id": control.control_id,
                    "issue": "Missing evidence",
                    "required": len(control.evidence_required),
                    "collected": len(control.evidence_collected),
                })
        elif control.status != ControlStatus.NOT_APPLICABLE:
            gaps.append({
                "control_id": control.control_id,
                "issue": f"Status: {control.status.value}",
                "status": control.status.value,
            })
    
    return {
        "framework": framework.value,
        "total_controls": len(controls),
        "ready_for_audit": len(ready),
        "gaps_identified": len(gaps),
        "gaps": gaps,
        "readiness_percentage": (
            len(ready) / len(controls) * 100 if controls else 0
        ),
    }
