#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
__init__.py

UDS3 Compliance Module - DSGVO, Security, Identity Services, EU AI Act, and Ethics
Dieses Modul ist Teil der UDS3 Polyglot Persistence Architecture.

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3

v2.5.0 Governance & Compliance:
- Data Classification and Retention
- EU AI Act Compliance
- Bias Monitoring
- AI Ethics Committee Integration
"""

from compliance.dsgvo_core import UDS3DSGVOCore, PIIType, DSGVOProcessingBasis, DSGVOOperationType
from compliance.security_quality import DataSecurityManager, DataQualityManager, SecurityLevel, QualityConfig
from compliance.identity_service import UDS3IdentityService, IdentityRecord
from compliance.adapter import ComplianceAdapter, create_compliance_adapter

# v2.5.0 - Data Classification
from compliance.data_classification import (
    DataClassificationEngine,
    RetentionManager,
    ClassificationLevel,
    DataCategory,
    RetentionType,
    DeletionMethod,
    create_classification_engine,
    create_retention_manager,
)

# v2.5.0 - EU AI Act Compliance
from compliance.eu_ai_act import (
    EUAIActComplianceEngine,
    AIRiskCategory,
    AISystemType,
    TransparencyLevel,
    HumanOversightMode,
    ConformityStatus,
    create_eu_ai_act_engine,
    register_vcc_systems,
)

# v2.5.0 - Bias Monitoring
from compliance.bias_monitoring import (
    BiasMonitoringEngine,
    BiasType,
    ProtectedAttribute,
    AlertSeverity,
    create_bias_monitoring_engine,
    setup_vcc_monitoring,
)

# v2.5.0 - AI Ethics Committee
from compliance.ai_ethics_committee import (
    AIEthicsCommittee,
    ReviewType,
    ReviewStatus,
    RiskLevel,
    CommitteeRole,
    create_ai_ethics_committee,
    setup_default_committee,
)

__module_name__ = "compliance"
__version__ = "2.5.0"

__all__ = [
    # DSGVO Core
    'UDS3DSGVOCore',
    'PIIType',
    'DSGVOProcessingBasis',
    'DSGVOOperationType',
    # Security & Quality
    'DataSecurityManager',
    'DataQualityManager',
    'SecurityLevel',
    'QualityConfig',
    # Identity
    'UDS3IdentityService',
    'IdentityRecord',
    # Adapter
    'ComplianceAdapter',
    'create_compliance_adapter',
    # v2.5.0 - Data Classification
    'DataClassificationEngine',
    'RetentionManager',
    'ClassificationLevel',
    'DataCategory',
    'RetentionType',
    'DeletionMethod',
    'create_classification_engine',
    'create_retention_manager',
    # v2.5.0 - EU AI Act
    'EUAIActComplianceEngine',
    'AIRiskCategory',
    'AISystemType',
    'TransparencyLevel',
    'HumanOversightMode',
    'ConformityStatus',
    'create_eu_ai_act_engine',
    'register_vcc_systems',
    # v2.5.0 - Bias Monitoring
    'BiasMonitoringEngine',
    'BiasType',
    'ProtectedAttribute',
    'AlertSeverity',
    'create_bias_monitoring_engine',
    'setup_vcc_monitoring',
    # v2.5.0 - AI Ethics Committee
    'AIEthicsCommittee',
    'ReviewType',
    'ReviewStatus',
    'RiskLevel',
    'CommitteeRole',
    'create_ai_ethics_committee',
    'setup_default_committee',
]
