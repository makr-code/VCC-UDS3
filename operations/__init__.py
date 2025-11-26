#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VCC-UDS3 Operations Module (v3.0.0)

Production readiness modules for VCC-UDS3:
- Kubernetes deployment (on-premise)
- High Availability (database clustering)
- Security Audit (ISO 27001, SOC 2, BSI C5)

Part of UDS3 (Unified Database Strategy v3)
Author: VCC Development Team
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

__module_name__ = "operations"
__version__ = "3.0.0"

# Kubernetes Deployment
from operations.kubernetes import (
    # Enums
    DeploymentEnvironment,
    ServiceType,
    ResourceTier,
    ComponentType,
    HealthStatus as K8sHealthStatus,
    # Config classes
    ResourceLimits,
    PersistentVolumeConfig,
    ReplicaConfig,
    NetworkPolicy,
    ComponentDeployment,
    # Main classes
    HelmChartGenerator,
    KubernetesDeploymentManager,
    # Factory functions
    create_helm_generator,
    create_deployment_manager,
    generate_production_deployment,
    get_resource_tier_config,
)

# High Availability
from operations.high_availability import (
    # Enums
    HAMode,
    NodeRole,
    HealthStatus as HAHealthStatus,
    FailoverTrigger,
    ReplicationMode,
    DatabaseType,
    # Config classes
    NodeConfig,
    ClusterConfig,
    FailoverEvent,
    ReplicationStatus,
    # Cluster classes
    PatroniCluster,
    Neo4jCausalCluster,
    ChromaDBCluster,
    CouchDBCluster,
    # Main class
    HAManager,
    # Factory functions
    create_ha_manager,
    create_postgresql_ha_config,
    create_neo4j_ha_config,
    setup_vcc_ha,
)

# Security Audit
from operations.security_audit import (
    # Enums
    ComplianceFramework,
    ControlCategory,
    RiskLevel,
    FindingSeverity,
    ControlStatus,
    AuditStatus,
    RemediationStatus,
    # Data classes
    SecurityControl,
    AuditFinding,
    AuditReport,
    RemediationAction,
    # Controls
    ISO27001Controls,
    # Main class
    SecurityAuditEngine,
    # Factory functions
    create_security_audit_engine,
    get_vcc_uds3_controls,
    prepare_iso_27001_audit,
    conduct_pre_audit_assessment,
)

__all__ = [
    # Version
    "__version__",
    "__module_name__",
    
    # Kubernetes
    "DeploymentEnvironment",
    "ServiceType",
    "ResourceTier",
    "ComponentType",
    "K8sHealthStatus",
    "ResourceLimits",
    "PersistentVolumeConfig",
    "ReplicaConfig",
    "NetworkPolicy",
    "ComponentDeployment",
    "HelmChartGenerator",
    "KubernetesDeploymentManager",
    "create_helm_generator",
    "create_deployment_manager",
    "generate_production_deployment",
    "get_resource_tier_config",
    
    # High Availability
    "HAMode",
    "NodeRole",
    "HAHealthStatus",
    "FailoverTrigger",
    "ReplicationMode",
    "DatabaseType",
    "NodeConfig",
    "ClusterConfig",
    "FailoverEvent",
    "ReplicationStatus",
    "PatroniCluster",
    "Neo4jCausalCluster",
    "ChromaDBCluster",
    "CouchDBCluster",
    "HAManager",
    "create_ha_manager",
    "create_postgresql_ha_config",
    "create_neo4j_ha_config",
    "setup_vcc_ha",
    
    # Security Audit
    "ComplianceFramework",
    "ControlCategory",
    "RiskLevel",
    "FindingSeverity",
    "ControlStatus",
    "AuditStatus",
    "RemediationStatus",
    "SecurityControl",
    "AuditFinding",
    "AuditReport",
    "RemediationAction",
    "ISO27001Controls",
    "SecurityAuditEngine",
    "create_security_audit_engine",
    "get_vcc_uds3_controls",
    "prepare_iso_27001_audit",
    "conduct_pre_audit_assessment",
]
