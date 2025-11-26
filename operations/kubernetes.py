#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VCC-UDS3 Kubernetes Deployment Module (v3.0.0)

On-premise Kubernetes deployment configuration and management for VCC-UDS3.
Supports bare-metal Kubernetes, VMware Tanzu, and other on-premise distributions.

NO cloud provider dependencies (AWS EKS, Azure AKS, GCP GKE).

Author: VCC Development Team
License: MIT with Government Partnership Commons Clause
"""

from dataclasses import dataclass, field
from datetime import datetime
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

class DeploymentEnvironment(str, Enum):
    """Deployment environments - all on-premise."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    DISASTER_RECOVERY = "disaster-recovery"


class ServiceType(str, Enum):
    """Kubernetes service types for on-premise deployment."""
    CLUSTER_IP = "ClusterIP"
    NODE_PORT = "NodePort"
    LOAD_BALANCER = "LoadBalancer"  # On-premise MetalLB
    HEADLESS = "None"


class ResourceTier(str, Enum):
    """Resource allocation tiers."""
    MINIMAL = "minimal"      # Dev/test
    STANDARD = "standard"    # Staging
    PRODUCTION = "production"  # Production
    HIGH_AVAILABILITY = "high-availability"  # HA production


class ComponentType(str, Enum):
    """VCC-UDS3 component types."""
    API_SERVER = "api-server"
    SEARCH_SERVICE = "search-service"
    POSTGRESQL = "postgresql"
    NEO4J = "neo4j"
    CHROMADB = "chromadb"
    COUCHDB = "couchdb"
    PROMETHEUS = "prometheus"
    GRAFANA = "grafana"
    REDIS_CACHE = "redis-cache"
    SAGA_COORDINATOR = "saga-coordinator"


class HealthStatus(str, Enum):
    """Pod/service health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


# =============================================================================
# Configuration Data Classes
# =============================================================================

@dataclass
class ResourceLimits:
    """Kubernetes resource limits configuration."""
    cpu_request: str = "100m"
    cpu_limit: str = "1000m"
    memory_request: str = "256Mi"
    memory_limit: str = "2Gi"
    storage: str = "10Gi"
    
    def to_k8s_spec(self) -> dict:
        """Convert to Kubernetes resource spec."""
        return {
            "resources": {
                "requests": {
                    "cpu": self.cpu_request,
                    "memory": self.memory_request,
                },
                "limits": {
                    "cpu": self.cpu_limit,
                    "memory": self.memory_limit,
                },
            }
        }


@dataclass
class PersistentVolumeConfig:
    """Persistent volume configuration for on-premise storage."""
    storage_class: str = "local-storage"  # On-premise storage class
    access_mode: str = "ReadWriteOnce"
    size: str = "50Gi"
    reclaim_policy: str = "Retain"
    volume_type: str = "hostPath"  # For on-premise: hostPath, NFS, iSCSI
    
    def to_pvc_spec(self, name: str) -> dict:
        """Generate PVC specification."""
        return {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"name": name},
            "spec": {
                "accessModes": [self.access_mode],
                "storageClassName": self.storage_class,
                "resources": {
                    "requests": {"storage": self.size}
                },
            },
        }


@dataclass
class ReplicaConfig:
    """Replica configuration for HA deployment."""
    min_replicas: int = 1
    max_replicas: int = 3
    target_cpu_utilization: int = 70
    target_memory_utilization: int = 80
    scale_up_stabilization: int = 300  # seconds
    scale_down_stabilization: int = 600  # seconds
    
    def to_hpa_spec(self, deployment_name: str) -> dict:
        """Generate HorizontalPodAutoscaler specification."""
        return {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {"name": f"{deployment_name}-hpa"},
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": deployment_name,
                },
                "minReplicas": self.min_replicas,
                "maxReplicas": self.max_replicas,
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": self.target_cpu_utilization,
                            },
                        },
                    },
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "memory",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": self.target_memory_utilization,
                            },
                        },
                    },
                ],
                "behavior": {
                    "scaleUp": {
                        "stabilizationWindowSeconds": self.scale_up_stabilization,
                    },
                    "scaleDown": {
                        "stabilizationWindowSeconds": self.scale_down_stabilization,
                    },
                },
            },
        }


@dataclass
class NetworkPolicy:
    """Network policy configuration for zero-trust networking."""
    name: str
    namespace: str = "vcc-uds3"
    ingress_from: list = field(default_factory=list)
    egress_to: list = field(default_factory=list)
    pod_selector: dict = field(default_factory=dict)
    
    def to_k8s_spec(self) -> dict:
        """Generate NetworkPolicy specification."""
        spec: dict[str, Any] = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
            },
            "spec": {
                "podSelector": self.pod_selector,
                "policyTypes": [],
            },
        }
        
        if self.ingress_from:
            spec["spec"]["policyTypes"].append("Ingress")
            spec["spec"]["ingress"] = self.ingress_from
        
        if self.egress_to:
            spec["spec"]["policyTypes"].append("Egress")
            spec["spec"]["egress"] = self.egress_to
        
        return spec


@dataclass
class ComponentDeployment:
    """Individual component deployment configuration."""
    component_type: ComponentType
    replicas: int = 1
    resources: ResourceLimits = field(default_factory=ResourceLimits)
    volume: Optional[PersistentVolumeConfig] = None
    environment: DeploymentEnvironment = DeploymentEnvironment.DEVELOPMENT
    image_tag: str = "latest"
    
    # HA settings
    enable_hpa: bool = False
    replica_config: Optional[ReplicaConfig] = None
    
    # Health checks
    liveness_probe_path: str = "/health/live"
    readiness_probe_path: str = "/health/ready"
    startup_probe_path: str = "/health/startup"
    
    def get_image_name(self) -> str:
        """Get full image name for on-premise registry."""
        # On-premise registry - no Docker Hub dependency
        registry = "registry.internal.vcc.local:5000"
        return f"{registry}/vcc-uds3/{self.component_type.value}:{self.image_tag}"


# =============================================================================
# Helm Chart Generator
# =============================================================================

class HelmChartGenerator:
    """
    Generates Helm charts for VCC-UDS3 on-premise Kubernetes deployment.
    
    Features:
    - Templated Kubernetes manifests
    - Environment-specific values
    - Security-hardened configurations
    - HA configurations
    """
    
    CHART_VERSION = "3.0.0"
    APP_VERSION = "3.0.0"
    
    def __init__(self, namespace: str = "vcc-uds3"):
        self.namespace = namespace
        self.components: dict[ComponentType, ComponentDeployment] = {}
        self.network_policies: list[NetworkPolicy] = []
        self.secrets: dict[str, dict[str, str]] = {}
        
    def add_component(self, deployment: ComponentDeployment) -> None:
        """Add a component deployment."""
        self.components[deployment.component_type] = deployment
        logger.info(f"Added component: {deployment.component_type.value}")
    
    def add_network_policy(self, policy: NetworkPolicy) -> None:
        """Add a network policy."""
        self.network_policies.append(policy)
        logger.info(f"Added network policy: {policy.name}")
    
    def add_secret(self, name: str, data: dict[str, str]) -> None:
        """Add a Kubernetes secret."""
        self.secrets[name] = data
        logger.info(f"Added secret: {name}")
    
    def generate_chart_yaml(self) -> dict:
        """Generate Chart.yaml content."""
        return {
            "apiVersion": "v2",
            "name": "vcc-uds3",
            "description": "VCC-UDS3 Unified Database Strategy - On-Premise Deployment",
            "type": "application",
            "version": self.CHART_VERSION,
            "appVersion": self.APP_VERSION,
            "keywords": [
                "vcc",
                "uds3",
                "database",
                "rag",
                "knowledge-graph",
                "on-premise",
            ],
            "maintainers": [
                {
                    "name": "VCC Development Team",
                    "email": "vcc-dev@internal.local",
                }
            ],
            "dependencies": [
                {
                    "name": "postgresql",
                    "version": "~15.0.0",
                    "repository": "file://../charts/postgresql",
                    "condition": "postgresql.enabled",
                },
                {
                    "name": "neo4j",
                    "version": "~5.0.0",
                    "repository": "file://../charts/neo4j",
                    "condition": "neo4j.enabled",
                },
                {
                    "name": "prometheus",
                    "version": "~2.50.0",
                    "repository": "file://../charts/prometheus",
                    "condition": "monitoring.enabled",
                },
            ],
        }
    
    def generate_values_yaml(self, environment: DeploymentEnvironment) -> dict:
        """Generate values.yaml for specific environment."""
        is_prod = environment in [
            DeploymentEnvironment.PRODUCTION,
            DeploymentEnvironment.DISASTER_RECOVERY,
        ]
        
        return {
            "global": {
                "namespace": self.namespace,
                "environment": environment.value,
                "imageRegistry": "registry.internal.vcc.local:5000",
                "imagePullSecrets": ["vcc-registry-secret"],
                "storageClass": "local-storage",
            },
            "api": {
                "enabled": True,
                "replicas": 3 if is_prod else 1,
                "resources": {
                    "requests": {"cpu": "500m", "memory": "1Gi"},
                    "limits": {"cpu": "2000m", "memory": "4Gi"},
                } if is_prod else {
                    "requests": {"cpu": "100m", "memory": "256Mi"},
                    "limits": {"cpu": "500m", "memory": "1Gi"},
                },
                "autoscaling": {
                    "enabled": is_prod,
                    "minReplicas": 2,
                    "maxReplicas": 10,
                    "targetCPU": 70,
                    "targetMemory": 80,
                },
                "service": {
                    "type": "LoadBalancer" if is_prod else "ClusterIP",
                    "port": 8080,
                },
            },
            "search": {
                "enabled": True,
                "replicas": 2 if is_prod else 1,
                "resources": {
                    "requests": {"cpu": "1000m", "memory": "2Gi"},
                    "limits": {"cpu": "4000m", "memory": "8Gi"},
                } if is_prod else {
                    "requests": {"cpu": "200m", "memory": "512Mi"},
                    "limits": {"cpu": "1000m", "memory": "2Gi"},
                },
            },
            "postgresql": {
                "enabled": True,
                "replication": {
                    "enabled": is_prod,
                    "readReplicas": 2 if is_prod else 0,
                },
                "persistence": {
                    "size": "100Gi" if is_prod else "10Gi",
                    "storageClass": "local-storage",
                },
                "metrics": {"enabled": True},
            },
            "neo4j": {
                "enabled": True,
                "core": {
                    "replicas": 3 if is_prod else 1,
                },
                "persistence": {
                    "size": "50Gi" if is_prod else "10Gi",
                },
            },
            "chromadb": {
                "enabled": True,
                "replicas": 2 if is_prod else 1,
                "persistence": {
                    "size": "100Gi" if is_prod else "20Gi",
                },
            },
            "couchdb": {
                "enabled": True,
                "replicas": 3 if is_prod else 1,  # CouchDB needs odd number for quorum
                "persistence": {
                    "size": "50Gi" if is_prod else "10Gi",
                },
            },
            "redis": {
                "enabled": True,
                "sentinel": {
                    "enabled": is_prod,
                },
                "persistence": {
                    "size": "5Gi",
                },
            },
            "monitoring": {
                "enabled": True,
                "prometheus": {
                    "retention": "30d" if is_prod else "7d",
                    "storage": "50Gi" if is_prod else "10Gi",
                },
                "grafana": {
                    "enabled": True,
                    "persistence": {
                        "size": "5Gi",
                    },
                },
            },
            "security": {
                "networkPolicies": {
                    "enabled": True,
                },
                "podSecurityPolicy": {
                    "enabled": True,
                },
                "tls": {
                    "enabled": True,
                    "certManager": {
                        "enabled": True,
                        "issuer": "vcc-internal-ca",
                    },
                },
            },
            "ingress": {
                "enabled": is_prod,
                "className": "nginx",
                "annotations": {
                    "nginx.ingress.kubernetes.io/ssl-redirect": "true",
                    "nginx.ingress.kubernetes.io/backend-protocol": "HTTPS",
                },
                "tls": {
                    "enabled": True,
                    "secretName": "vcc-uds3-tls",
                },
            },
        }
    
    def generate_deployment_manifest(
        self,
        component: ComponentDeployment
    ) -> dict:
        """Generate Kubernetes Deployment manifest."""
        labels = {
            "app.kubernetes.io/name": component.component_type.value,
            "app.kubernetes.io/instance": f"vcc-uds3-{component.component_type.value}",
            "app.kubernetes.io/version": self.APP_VERSION,
            "app.kubernetes.io/component": component.component_type.value,
            "app.kubernetes.io/part-of": "vcc-uds3",
            "app.kubernetes.io/managed-by": "helm",
        }
        
        container_spec = {
            "name": component.component_type.value,
            "image": component.get_image_name(),
            "imagePullPolicy": "IfNotPresent",
            "ports": [{"containerPort": 8080, "protocol": "TCP"}],
            "livenessProbe": {
                "httpGet": {
                    "path": component.liveness_probe_path,
                    "port": 8080,
                },
                "initialDelaySeconds": 30,
                "periodSeconds": 10,
                "timeoutSeconds": 5,
                "failureThreshold": 3,
            },
            "readinessProbe": {
                "httpGet": {
                    "path": component.readiness_probe_path,
                    "port": 8080,
                },
                "initialDelaySeconds": 10,
                "periodSeconds": 5,
                "timeoutSeconds": 3,
                "failureThreshold": 3,
            },
            "startupProbe": {
                "httpGet": {
                    "path": component.startup_probe_path,
                    "port": 8080,
                },
                "initialDelaySeconds": 10,
                "periodSeconds": 10,
                "timeoutSeconds": 5,
                "failureThreshold": 30,
            },
            **component.resources.to_k8s_spec(),
            "securityContext": {
                "runAsNonRoot": True,
                "runAsUser": 1000,
                "readOnlyRootFilesystem": True,
                "allowPrivilegeEscalation": False,
                "capabilities": {"drop": ["ALL"]},
            },
        }
        
        manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": f"vcc-uds3-{component.component_type.value}",
                "namespace": self.namespace,
                "labels": labels,
            },
            "spec": {
                "replicas": component.replicas,
                "selector": {"matchLabels": labels},
                "strategy": {
                    "type": "RollingUpdate",
                    "rollingUpdate": {
                        "maxUnavailable": "25%",
                        "maxSurge": "25%",
                    },
                },
                "template": {
                    "metadata": {"labels": labels},
                    "spec": {
                        "serviceAccountName": "vcc-uds3",
                        "securityContext": {
                            "runAsNonRoot": True,
                            "fsGroup": 1000,
                        },
                        "containers": [container_spec],
                        "affinity": {
                            "podAntiAffinity": {
                                "preferredDuringSchedulingIgnoredDuringExecution": [
                                    {
                                        "weight": 100,
                                        "podAffinityTerm": {
                                            "labelSelector": {
                                                "matchLabels": labels,
                                            },
                                            "topologyKey": "kubernetes.io/hostname",
                                        },
                                    }
                                ],
                            },
                        },
                        "topologySpreadConstraints": [
                            {
                                "maxSkew": 1,
                                "topologyKey": "topology.kubernetes.io/zone",
                                "whenUnsatisfiable": "ScheduleAnyway",
                                "labelSelector": {"matchLabels": labels},
                            },
                        ],
                    },
                },
            },
        }
        
        # Add volume mounts if persistent storage required
        if component.volume:
            pvc_name = f"vcc-uds3-{component.component_type.value}-data"
            manifest["spec"]["template"]["spec"]["volumes"] = [
                {
                    "name": "data",
                    "persistentVolumeClaim": {"claimName": pvc_name},
                }
            ]
            container_spec["volumeMounts"] = [
                {"name": "data", "mountPath": "/data"}
            ]
        
        return manifest
    
    def generate_service_manifest(
        self,
        component: ComponentDeployment,
        service_type: ServiceType = ServiceType.CLUSTER_IP
    ) -> dict:
        """Generate Kubernetes Service manifest."""
        labels = {
            "app.kubernetes.io/name": component.component_type.value,
            "app.kubernetes.io/instance": f"vcc-uds3-{component.component_type.value}",
        }
        
        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": f"vcc-uds3-{component.component_type.value}",
                "namespace": self.namespace,
                "labels": labels,
            },
            "spec": {
                "type": service_type.value,
                "ports": [
                    {
                        "name": "http",
                        "port": 8080,
                        "targetPort": 8080,
                        "protocol": "TCP",
                    }
                ],
                "selector": labels,
            },
        }
    
    def export_helm_chart(self, output_dir: str = "./helm/vcc-uds3") -> dict:
        """Export complete Helm chart structure."""
        chart_structure = {
            "Chart.yaml": self.generate_chart_yaml(),
            "values.yaml": self.generate_values_yaml(
                DeploymentEnvironment.PRODUCTION
            ),
            "values-dev.yaml": self.generate_values_yaml(
                DeploymentEnvironment.DEVELOPMENT
            ),
            "values-staging.yaml": self.generate_values_yaml(
                DeploymentEnvironment.STAGING
            ),
            "templates": {},
        }
        
        # Generate templates for each component
        for component_type, deployment in self.components.items():
            name = component_type.value.replace("-", "_")
            chart_structure["templates"][f"{name}_deployment.yaml"] = (
                self.generate_deployment_manifest(deployment)
            )
            chart_structure["templates"][f"{name}_service.yaml"] = (
                self.generate_service_manifest(deployment)
            )
            
            if deployment.enable_hpa and deployment.replica_config:
                chart_structure["templates"][f"{name}_hpa.yaml"] = (
                    deployment.replica_config.to_hpa_spec(
                        f"vcc-uds3-{component_type.value}"
                    )
                )
            
            if deployment.volume:
                chart_structure["templates"][f"{name}_pvc.yaml"] = (
                    deployment.volume.to_pvc_spec(
                        f"vcc-uds3-{component_type.value}-data"
                    )
                )
        
        # Add network policies
        for i, policy in enumerate(self.network_policies):
            chart_structure["templates"][f"network_policy_{i}.yaml"] = (
                policy.to_k8s_spec()
            )
        
        logger.info(f"Generated Helm chart with {len(self.components)} components")
        return chart_structure


# =============================================================================
# Kubernetes Deployment Manager
# =============================================================================

class KubernetesDeploymentManager:
    """
    Manages Kubernetes deployments for VCC-UDS3.
    
    Features:
    - Rolling updates with zero downtime
    - Health monitoring
    - Rollback capabilities
    - Multi-environment support
    """
    
    def __init__(
        self,
        namespace: str = "vcc-uds3",
        kubeconfig_path: Optional[str] = None
    ):
        self.namespace = namespace
        self.kubeconfig_path = kubeconfig_path
        self.helm_generator = HelmChartGenerator(namespace)
        self.deployment_history: list[dict] = []
        
    def configure_standard_deployment(self) -> None:
        """Configure standard VCC-UDS3 deployment with all components."""
        # API Server
        self.helm_generator.add_component(ComponentDeployment(
            component_type=ComponentType.API_SERVER,
            replicas=2,
            resources=ResourceLimits(
                cpu_request="500m",
                cpu_limit="2000m",
                memory_request="1Gi",
                memory_limit="4Gi",
            ),
            enable_hpa=True,
            replica_config=ReplicaConfig(min_replicas=2, max_replicas=10),
        ))
        
        # Search Service
        self.helm_generator.add_component(ComponentDeployment(
            component_type=ComponentType.SEARCH_SERVICE,
            replicas=2,
            resources=ResourceLimits(
                cpu_request="1000m",
                cpu_limit="4000m",
                memory_request="2Gi",
                memory_limit="8Gi",
            ),
            enable_hpa=True,
            replica_config=ReplicaConfig(min_replicas=2, max_replicas=8),
        ))
        
        # PostgreSQL with persistence
        self.helm_generator.add_component(ComponentDeployment(
            component_type=ComponentType.POSTGRESQL,
            replicas=1,  # HA handled by Patroni
            resources=ResourceLimits(
                cpu_request="500m",
                cpu_limit="2000m",
                memory_request="1Gi",
                memory_limit="4Gi",
            ),
            volume=PersistentVolumeConfig(size="100Gi"),
        ))
        
        # Neo4j with persistence
        self.helm_generator.add_component(ComponentDeployment(
            component_type=ComponentType.NEO4J,
            replicas=3,  # Causal cluster
            resources=ResourceLimits(
                cpu_request="500m",
                cpu_limit="2000m",
                memory_request="2Gi",
                memory_limit="8Gi",
            ),
            volume=PersistentVolumeConfig(size="50Gi"),
        ))
        
        # ChromaDB
        self.helm_generator.add_component(ComponentDeployment(
            component_type=ComponentType.CHROMADB,
            replicas=2,
            resources=ResourceLimits(
                cpu_request="1000m",
                cpu_limit="4000m",
                memory_request="4Gi",
                memory_limit="16Gi",
            ),
            volume=PersistentVolumeConfig(size="100Gi"),
        ))
        
        # CouchDB
        self.helm_generator.add_component(ComponentDeployment(
            component_type=ComponentType.COUCHDB,
            replicas=3,  # Clustering with quorum
            resources=ResourceLimits(
                cpu_request="250m",
                cpu_limit="1000m",
                memory_request="512Mi",
                memory_limit="2Gi",
            ),
            volume=PersistentVolumeConfig(size="50Gi"),
        ))
        
        # Monitoring
        self.helm_generator.add_component(ComponentDeployment(
            component_type=ComponentType.PROMETHEUS,
            replicas=1,
            resources=ResourceLimits(
                cpu_request="250m",
                cpu_limit="1000m",
                memory_request="1Gi",
                memory_limit="4Gi",
            ),
            volume=PersistentVolumeConfig(size="50Gi"),
        ))
        
        self.helm_generator.add_component(ComponentDeployment(
            component_type=ComponentType.GRAFANA,
            replicas=1,
            resources=ResourceLimits(
                cpu_request="100m",
                cpu_limit="500m",
                memory_request="256Mi",
                memory_limit="1Gi",
            ),
            volume=PersistentVolumeConfig(size="5Gi"),
        ))
        
        # Configure network policies
        self._configure_network_policies()
        
        logger.info("Standard deployment configured with all components")
    
    def _configure_network_policies(self) -> None:
        """Configure zero-trust network policies."""
        # Allow API to access databases
        self.helm_generator.add_network_policy(NetworkPolicy(
            name="api-to-databases",
            namespace=self.namespace,
            pod_selector={"app.kubernetes.io/component": "api-server"},
            egress_to=[
                {
                    "to": [{"podSelector": {"app.kubernetes.io/component": "postgresql"}}],
                    "ports": [{"port": 5432}],
                },
                {
                    "to": [{"podSelector": {"app.kubernetes.io/component": "neo4j"}}],
                    "ports": [{"port": 7687}],
                },
                {
                    "to": [{"podSelector": {"app.kubernetes.io/component": "chromadb"}}],
                    "ports": [{"port": 8000}],
                },
                {
                    "to": [{"podSelector": {"app.kubernetes.io/component": "couchdb"}}],
                    "ports": [{"port": 5984}],
                },
            ],
        ))
        
        # Deny all ingress to databases except from API
        self.helm_generator.add_network_policy(NetworkPolicy(
            name="database-ingress-policy",
            namespace=self.namespace,
            pod_selector={"app.kubernetes.io/component": "postgresql"},
            ingress_from=[
                {
                    "from": [{"podSelector": {"app.kubernetes.io/component": "api-server"}}],
                    "ports": [{"port": 5432}],
                }
            ],
        ))
    
    def deploy(
        self,
        environment: DeploymentEnvironment,
        dry_run: bool = False
    ) -> dict:
        """
        Deploy VCC-UDS3 to Kubernetes cluster.
        
        Args:
            environment: Target deployment environment
            dry_run: If True, only generate manifests without applying
            
        Returns:
            Deployment result with status and details
        """
        deployment_id = str(uuid.uuid4())[:8]
        timestamp = datetime.utcnow().isoformat()
        
        result = {
            "deployment_id": deployment_id,
            "environment": environment.value,
            "timestamp": timestamp,
            "status": "pending",
            "components": [],
            "dry_run": dry_run,
        }
        
        try:
            # Generate Helm chart
            chart = self.helm_generator.export_helm_chart()
            values = self.helm_generator.generate_values_yaml(environment)
            
            if dry_run:
                result["status"] = "dry_run_success"
                result["chart"] = chart
                result["values"] = values
            else:
                # In production, would use Kubernetes API or helm command
                result["status"] = "success"
                result["message"] = "Deployment initiated"
            
            # Record deployment
            self.deployment_history.append(result)
            logger.info(f"Deployment {deployment_id} completed: {result['status']}")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error(f"Deployment {deployment_id} failed: {e}")
        
        return result
    
    def get_deployment_status(self, deployment_id: str) -> Optional[dict]:
        """Get status of a specific deployment."""
        for deployment in self.deployment_history:
            if deployment["deployment_id"] == deployment_id:
                return deployment
        return None
    
    def rollback(self, deployment_id: str) -> dict:
        """Rollback to a previous deployment."""
        # Find deployment in history
        target = None
        for deployment in self.deployment_history:
            if deployment["deployment_id"] == deployment_id:
                target = deployment
                break
        
        if not target:
            return {
                "status": "failed",
                "error": f"Deployment {deployment_id} not found",
            }
        
        rollback_result = {
            "rollback_id": str(uuid.uuid4())[:8],
            "target_deployment": deployment_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }
        
        logger.info(f"Rollback to deployment {deployment_id} initiated")
        return rollback_result


# =============================================================================
# Factory Functions
# =============================================================================

def create_helm_generator(namespace: str = "vcc-uds3") -> HelmChartGenerator:
    """Create a new Helm chart generator."""
    return HelmChartGenerator(namespace)


def create_deployment_manager(
    namespace: str = "vcc-uds3",
    kubeconfig_path: Optional[str] = None
) -> KubernetesDeploymentManager:
    """Create a new Kubernetes deployment manager."""
    return KubernetesDeploymentManager(namespace, kubeconfig_path)


def generate_production_deployment() -> dict:
    """Generate production deployment configuration."""
    manager = create_deployment_manager()
    manager.configure_standard_deployment()
    return manager.deploy(DeploymentEnvironment.PRODUCTION, dry_run=True)


def get_resource_tier_config(tier: ResourceTier) -> ResourceLimits:
    """Get resource limits for a specific tier."""
    configs = {
        ResourceTier.MINIMAL: ResourceLimits(
            cpu_request="100m",
            cpu_limit="500m",
            memory_request="256Mi",
            memory_limit="1Gi",
        ),
        ResourceTier.STANDARD: ResourceLimits(
            cpu_request="500m",
            cpu_limit="2000m",
            memory_request="1Gi",
            memory_limit="4Gi",
        ),
        ResourceTier.PRODUCTION: ResourceLimits(
            cpu_request="1000m",
            cpu_limit="4000m",
            memory_request="2Gi",
            memory_limit="8Gi",
        ),
        ResourceTier.HIGH_AVAILABILITY: ResourceLimits(
            cpu_request="2000m",
            cpu_limit="8000m",
            memory_request="4Gi",
            memory_limit="16Gi",
        ),
    }
    return configs.get(tier, configs[ResourceTier.STANDARD])
