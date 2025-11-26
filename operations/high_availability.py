#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VCC-UDS3 High Availability Module (v3.0.0)

Database clustering and high availability configurations for on-premise deployment.
Supports PostgreSQL Patroni, Neo4j Causal Cluster, ChromaDB Sharding, and CouchDB Clustering.

NO cloud provider HA services (AWS RDS Multi-AZ, Azure HA, etc.).

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
import threading
import time
import uuid

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================

class HAMode(str, Enum):
    """High availability modes."""
    STANDALONE = "standalone"       # Single instance
    ACTIVE_PASSIVE = "active-passive"  # Primary + standby
    ACTIVE_ACTIVE = "active-active"    # Multiple active nodes
    QUORUM = "quorum"               # Consensus-based (odd number)


class NodeRole(str, Enum):
    """Database node roles."""
    PRIMARY = "primary"
    REPLICA = "replica"
    STANDBY = "standby"
    ARBITER = "arbiter"
    LEADER = "leader"
    FOLLOWER = "follower"


class HealthStatus(str, Enum):
    """Node health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    RECOVERING = "recovering"


class FailoverTrigger(str, Enum):
    """Failover trigger reasons."""
    MANUAL = "manual"
    HEALTH_CHECK_FAILED = "health_check_failed"
    NETWORK_PARTITION = "network_partition"
    DISK_FULL = "disk_full"
    MAINTENANCE = "maintenance"
    LEADER_ELECTION = "leader_election"


class ReplicationMode(str, Enum):
    """Replication modes."""
    SYNC = "synchronous"
    ASYNC = "asynchronous"
    SEMI_SYNC = "semi-synchronous"


class DatabaseType(str, Enum):
    """Database types in VCC-UDS3."""
    POSTGRESQL = "postgresql"
    NEO4J = "neo4j"
    CHROMADB = "chromadb"
    COUCHDB = "couchdb"


# =============================================================================
# Configuration Data Classes
# =============================================================================

@dataclass
class NodeConfig:
    """Configuration for a database node."""
    node_id: str
    host: str
    port: int
    role: NodeRole
    priority: int = 100  # Higher = more preferred for leader
    zone: str = "zone-1"  # For zone-aware HA
    datacenter: str = "dc-1"  # For multi-DC deployments
    
    # Health check configuration
    health_check_interval: int = 5  # seconds
    health_check_timeout: int = 3  # seconds
    unhealthy_threshold: int = 3  # consecutive failures


@dataclass
class ClusterConfig:
    """Cluster-level configuration."""
    cluster_id: str
    database_type: DatabaseType
    ha_mode: HAMode
    replication_mode: ReplicationMode = ReplicationMode.ASYNC
    
    # Quorum settings
    min_nodes_for_quorum: int = 2
    quorum_write_nodes: int = 2  # Number of nodes for write quorum
    quorum_read_nodes: int = 1   # Number of nodes for read quorum
    
    # Failover settings
    failover_timeout: int = 30  # seconds
    auto_failover: bool = True
    max_failover_attempts: int = 3
    failover_cooldown: int = 300  # seconds between failovers
    
    # Backup settings
    backup_retention_days: int = 30
    backup_schedule: str = "0 2 * * *"  # Daily at 2 AM
    
    nodes: list[NodeConfig] = field(default_factory=list)


@dataclass
class FailoverEvent:
    """Record of a failover event."""
    event_id: str
    cluster_id: str
    timestamp: datetime
    trigger: FailoverTrigger
    old_primary: str
    new_primary: str
    duration_seconds: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class ReplicationStatus:
    """Replication status for a node."""
    node_id: str
    role: NodeRole
    replication_lag_bytes: int = 0
    replication_lag_seconds: float = 0.0
    last_received_lsn: str = ""
    last_applied_lsn: str = ""
    sync_state: str = "async"
    connected_to_primary: bool = True


# =============================================================================
# PostgreSQL Patroni Cluster
# =============================================================================

class PatroniCluster:
    """
    PostgreSQL high availability with Patroni.
    
    Features:
    - Automatic leader election via etcd/consul/ZooKeeper
    - Streaming replication
    - Automatic failover
    - Read replicas for load distribution
    """
    
    def __init__(self, config: ClusterConfig):
        if config.database_type != DatabaseType.POSTGRESQL:
            raise ValueError("PatroniCluster requires PostgreSQL database type")
        
        self.config = config
        self.nodes: dict[str, NodeConfig] = {}
        self.node_health: dict[str, HealthStatus] = {}
        self.replication_status: dict[str, ReplicationStatus] = {}
        self.current_leader: Optional[str] = None
        self.failover_history: list[FailoverEvent] = []
        self._lock = threading.Lock()
        
        # Register nodes
        for node in config.nodes:
            self.nodes[node.node_id] = node
            self.node_health[node.node_id] = HealthStatus.UNKNOWN
        
        logger.info(f"PatroniCluster initialized: {config.cluster_id}")
    
    def get_leader(self) -> Optional[NodeConfig]:
        """Get the current cluster leader."""
        with self._lock:
            if self.current_leader and self.current_leader in self.nodes:
                return self.nodes[self.current_leader]
            return None
    
    def get_replicas(self) -> list[NodeConfig]:
        """Get all replica nodes."""
        with self._lock:
            return [
                node for node_id, node in self.nodes.items()
                if node_id != self.current_leader and 
                self.node_health.get(node_id) == HealthStatus.HEALTHY
            ]
    
    def check_node_health(self, node_id: str) -> HealthStatus:
        """Check health of a specific node."""
        if node_id not in self.nodes:
            return HealthStatus.UNKNOWN
        
        # In production, would check:
        # - PostgreSQL connection
        # - pg_isready
        # - Replication lag
        # - Disk space
        # - CPU/Memory
        
        # Simulated health check
        return HealthStatus.HEALTHY
    
    def update_health_status(self) -> dict[str, HealthStatus]:
        """Update health status for all nodes."""
        with self._lock:
            for node_id in self.nodes:
                self.node_health[node_id] = self.check_node_health(node_id)
        return self.node_health.copy()
    
    def get_replication_status(self) -> dict[str, ReplicationStatus]:
        """Get replication status for all nodes."""
        with self._lock:
            result = {}
            for node_id, node in self.nodes.items():
                result[node_id] = ReplicationStatus(
                    node_id=node_id,
                    role=NodeRole.LEADER if node_id == self.current_leader else NodeRole.REPLICA,
                    replication_lag_bytes=0,
                    replication_lag_seconds=0.0,
                    sync_state="sync" if self.config.replication_mode == ReplicationMode.SYNC else "async",
                    connected_to_primary=True,
                )
            return result
    
    def elect_leader(self) -> Optional[str]:
        """Perform leader election."""
        with self._lock:
            # Sort nodes by priority (highest first)
            candidates = sorted(
                [
                    (node_id, node)
                    for node_id, node in self.nodes.items()
                    if self.node_health.get(node_id) == HealthStatus.HEALTHY
                ],
                key=lambda x: x[1].priority,
                reverse=True
            )
            
            if not candidates:
                logger.error("No healthy nodes available for leader election")
                return None
            
            new_leader = candidates[0][0]
            self.current_leader = new_leader
            logger.info(f"Leader elected: {new_leader}")
            return new_leader
    
    def failover(
        self,
        trigger: FailoverTrigger,
        target_node: Optional[str] = None
    ) -> FailoverEvent:
        """
        Perform failover to a new primary.
        
        Args:
            trigger: Reason for failover
            target_node: Specific node to fail over to (optional)
        """
        start_time = datetime.utcnow()
        old_primary = self.current_leader
        event_id = str(uuid.uuid4())[:8]
        
        try:
            with self._lock:
                if target_node:
                    if target_node not in self.nodes:
                        raise ValueError(f"Node {target_node} not found")
                    if self.node_health.get(target_node) != HealthStatus.HEALTHY:
                        raise ValueError(f"Node {target_node} is not healthy")
                    new_primary = target_node
                else:
                    # Auto-select best replica
                    new_primary = self.elect_leader()
                    if not new_primary:
                        raise RuntimeError("No suitable node for failover")
                
                self.current_leader = new_primary
                
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                event = FailoverEvent(
                    event_id=event_id,
                    cluster_id=self.config.cluster_id,
                    timestamp=start_time,
                    trigger=trigger,
                    old_primary=old_primary or "none",
                    new_primary=new_primary,
                    duration_seconds=duration,
                    success=True,
                )
                
                self.failover_history.append(event)
                logger.info(
                    f"Failover completed: {old_primary} -> {new_primary} "
                    f"({duration:.2f}s)"
                )
                
                return event
                
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            event = FailoverEvent(
                event_id=event_id,
                cluster_id=self.config.cluster_id,
                timestamp=start_time,
                trigger=trigger,
                old_primary=old_primary or "none",
                new_primary="failed",
                duration_seconds=duration,
                success=False,
                error_message=str(e),
            )
            self.failover_history.append(event)
            logger.error(f"Failover failed: {e}")
            raise
    
    def add_replica(self, node: NodeConfig) -> None:
        """Add a new replica to the cluster."""
        with self._lock:
            if node.node_id in self.nodes:
                raise ValueError(f"Node {node.node_id} already exists")
            
            self.nodes[node.node_id] = node
            self.node_health[node.node_id] = HealthStatus.UNKNOWN
            
            logger.info(f"Added replica: {node.node_id}")
    
    def remove_node(self, node_id: str) -> None:
        """Remove a node from the cluster."""
        with self._lock:
            if node_id not in self.nodes:
                raise ValueError(f"Node {node_id} not found")
            
            if node_id == self.current_leader:
                raise ValueError("Cannot remove current leader, failover first")
            
            del self.nodes[node_id]
            del self.node_health[node_id]
            if node_id in self.replication_status:
                del self.replication_status[node_id]
            
            logger.info(f"Removed node: {node_id}")
    
    def get_connection_string(
        self,
        read_only: bool = False
    ) -> str:
        """
        Get connection string for the cluster.
        
        Args:
            read_only: If True, connect to a replica for reads
        """
        if read_only:
            replicas = self.get_replicas()
            if replicas:
                node = replicas[0]
            else:
                node = self.get_leader()
        else:
            node = self.get_leader()
        
        if not node:
            raise RuntimeError("No available nodes")
        
        return f"postgresql://{node.host}:{node.port}/vcc_uds3"
    
    def generate_patroni_config(self) -> dict:
        """Generate Patroni configuration file."""
        leader = self.get_leader()
        
        return {
            "scope": self.config.cluster_id,
            "name": f"postgresql-{leader.node_id if leader else 'node'}",
            "restapi": {
                "listen": "0.0.0.0:8008",
                "connect_address": f"{leader.host if leader else 'localhost'}:8008",
            },
            "etcd": {
                "hosts": "etcd1:2379,etcd2:2379,etcd3:2379",
            },
            "bootstrap": {
                "dcs": {
                    "ttl": 30,
                    "loop_wait": 10,
                    "retry_timeout": 10,
                    "maximum_lag_on_failover": 1048576,
                    "postgresql": {
                        "use_pg_rewind": True,
                        "use_slots": True,
                        "parameters": {
                            "wal_level": "replica",
                            "hot_standby": "on",
                            "max_wal_senders": 10,
                            "max_replication_slots": 10,
                            "wal_keep_size": "1GB",
                            "max_connections": 200,
                        },
                    },
                },
                "initdb": [
                    {"encoding": "UTF8"},
                    {"data-checksums": True},
                ],
            },
            "postgresql": {
                "listen": "0.0.0.0:5432",
                "connect_address": f"{leader.host if leader else 'localhost'}:5432",
                "data_dir": "/var/lib/postgresql/data",
                "pgpass": "/tmp/pgpass",
                "authentication": {
                    "replication": {"username": "replicator"},
                    "superuser": {"username": "postgres"},
                },
                "parameters": {
                    "unix_socket_directories": "/var/run/postgresql",
                },
            },
            "watchdog": {
                "mode": "automatic",
                "device": "/dev/watchdog",
            },
        }


# =============================================================================
# Neo4j Causal Cluster
# =============================================================================

class Neo4jCausalCluster:
    """
    Neo4j high availability with Causal Clustering.
    
    Features:
    - RAFT-based consensus
    - Core servers for writes
    - Read replicas for read scaling
    - Automatic leader election
    """
    
    def __init__(self, config: ClusterConfig):
        if config.database_type != DatabaseType.NEO4J:
            raise ValueError("Neo4jCausalCluster requires Neo4j database type")
        
        self.config = config
        self.core_nodes: dict[str, NodeConfig] = {}
        self.read_replicas: dict[str, NodeConfig] = {}
        self.node_health: dict[str, HealthStatus] = {}
        self.current_leader: Optional[str] = None
        self._lock = threading.Lock()
        
        # Categorize nodes
        for node in config.nodes:
            if node.role in [NodeRole.LEADER, NodeRole.FOLLOWER]:
                self.core_nodes[node.node_id] = node
            else:
                self.read_replicas[node.node_id] = node
            self.node_health[node.node_id] = HealthStatus.UNKNOWN
        
        logger.info(
            f"Neo4jCausalCluster initialized: {config.cluster_id} "
            f"({len(self.core_nodes)} cores, {len(self.read_replicas)} replicas)"
        )
    
    def get_leader(self) -> Optional[NodeConfig]:
        """Get the current cluster leader."""
        with self._lock:
            if self.current_leader and self.current_leader in self.core_nodes:
                return self.core_nodes[self.current_leader]
            return None
    
    def get_core_nodes(self) -> list[NodeConfig]:
        """Get all healthy core nodes."""
        with self._lock:
            return [
                node for node_id, node in self.core_nodes.items()
                if self.node_health.get(node_id) == HealthStatus.HEALTHY
            ]
    
    def get_read_replicas(self) -> list[NodeConfig]:
        """Get all healthy read replicas."""
        with self._lock:
            return [
                node for node_id, node in self.read_replicas.items()
                if self.node_health.get(node_id) == HealthStatus.HEALTHY
            ]
    
    def elect_leader(self) -> Optional[str]:
        """Trigger RAFT leader election."""
        with self._lock:
            healthy_cores = [
                node_id for node_id, node in self.core_nodes.items()
                if self.node_health.get(node_id) == HealthStatus.HEALTHY
            ]
            
            if len(healthy_cores) < self.config.min_nodes_for_quorum:
                logger.error(
                    f"Not enough healthy cores for quorum: "
                    f"{len(healthy_cores)} < {self.config.min_nodes_for_quorum}"
                )
                return None
            
            # In production, RAFT consensus handles this
            # Simulate by selecting first healthy core
            new_leader = healthy_cores[0]
            self.current_leader = new_leader
            logger.info(f"Neo4j leader elected: {new_leader}")
            return new_leader
    
    def get_bolt_routing_url(self) -> str:
        """Get Neo4j Bolt routing URL."""
        cores = self.get_core_nodes()
        if not cores:
            raise RuntimeError("No healthy core nodes")
        
        addresses = ",".join([f"{n.host}:{n.port}" for n in cores])
        return f"neo4j://{addresses}"
    
    def add_read_replica(self, node: NodeConfig) -> None:
        """Add a new read replica."""
        with self._lock:
            node.role = NodeRole.REPLICA
            self.read_replicas[node.node_id] = node
            self.node_health[node.node_id] = HealthStatus.UNKNOWN
            logger.info(f"Added Neo4j read replica: {node.node_id}")
    
    def generate_neo4j_config(self, node_id: str) -> dict:
        """Generate Neo4j configuration for a node."""
        if node_id in self.core_nodes:
            node = self.core_nodes[node_id]
            mode = "CORE"
        elif node_id in self.read_replicas:
            node = self.read_replicas[node_id]
            mode = "READ_REPLICA"
        else:
            raise ValueError(f"Node {node_id} not found")
        
        # Get core node addresses for discovery
        core_addresses = ",".join([
            f"{n.host}:5000"
            for n in self.core_nodes.values()
        ])
        
        return {
            "dbms.mode": mode,
            "dbms.default_listen_address": "0.0.0.0",
            "dbms.default_advertised_address": node.host,
            "dbms.connector.bolt.listen_address": f":7687",
            "dbms.connector.bolt.advertised_address": f"{node.host}:7687",
            "dbms.connector.http.listen_address": f":7474",
            "dbms.connector.http.advertised_address": f"{node.host}:7474",
            "causal_clustering.initial_discovery_members": core_addresses,
            "causal_clustering.minimum_core_cluster_size_at_formation": 3,
            "causal_clustering.discovery_type": "LIST",
            "causal_clustering.raft_messages_log_enable": "true",
            "dbms.memory.heap.initial_size": "2G",
            "dbms.memory.heap.max_size": "4G",
            "dbms.memory.pagecache.size": "2G",
        }


# =============================================================================
# ChromaDB Sharding
# =============================================================================

class ChromaDBCluster:
    """
    ChromaDB high availability with sharding.
    
    Features:
    - Horizontal sharding by collection
    - Replication for read scaling
    - Consistent hashing for shard placement
    """
    
    def __init__(self, config: ClusterConfig):
        if config.database_type != DatabaseType.CHROMADB:
            raise ValueError("ChromaDBCluster requires ChromaDB database type")
        
        self.config = config
        self.nodes: dict[str, NodeConfig] = {}
        self.node_health: dict[str, HealthStatus] = {}
        self.shard_map: dict[str, list[str]] = {}  # collection -> node_ids
        self._lock = threading.Lock()
        
        for node in config.nodes:
            self.nodes[node.node_id] = node
            self.node_health[node.node_id] = HealthStatus.UNKNOWN
        
        logger.info(f"ChromaDBCluster initialized: {config.cluster_id}")
    
    def get_healthy_nodes(self) -> list[NodeConfig]:
        """Get all healthy nodes."""
        with self._lock:
            return [
                node for node_id, node in self.nodes.items()
                if self.node_health.get(node_id) == HealthStatus.HEALTHY
            ]
    
    def compute_shard_placement(
        self,
        collection_id: str,
        replication_factor: int = 2
    ) -> list[str]:
        """
        Compute which nodes should host a collection shard.
        
        Uses consistent hashing for stable placement.
        """
        # Hash the collection ID
        hash_value = int(hashlib.md5(collection_id.encode()).hexdigest(), 16)
        
        healthy_nodes = self.get_healthy_nodes()
        if len(healthy_nodes) < replication_factor:
            replication_factor = len(healthy_nodes)
        
        # Sort nodes by their hash position
        node_positions = sorted(
            [(node.node_id, hash(node.node_id)) for node in healthy_nodes],
            key=lambda x: x[1]
        )
        
        # Find starting position
        start_idx = hash_value % len(node_positions)
        
        # Select nodes for placement
        selected = []
        for i in range(replication_factor):
            idx = (start_idx + i) % len(node_positions)
            selected.append(node_positions[idx][0])
        
        return selected
    
    def assign_collection(
        self,
        collection_id: str,
        replication_factor: int = 2
    ) -> list[str]:
        """Assign a collection to nodes."""
        with self._lock:
            node_ids = self.compute_shard_placement(
                collection_id,
                replication_factor
            )
            self.shard_map[collection_id] = node_ids
            logger.info(f"Assigned collection {collection_id} to nodes: {node_ids}")
            return node_ids
    
    def get_collection_nodes(self, collection_id: str) -> list[NodeConfig]:
        """Get nodes hosting a collection."""
        with self._lock:
            if collection_id not in self.shard_map:
                return []
            return [
                self.nodes[node_id]
                for node_id in self.shard_map[collection_id]
                if node_id in self.nodes
            ]
    
    def rebalance_shards(self) -> dict[str, list[str]]:
        """Rebalance shards after node changes."""
        with self._lock:
            rebalanced = {}
            for collection_id in self.shard_map:
                new_placement = self.compute_shard_placement(collection_id)
                if set(new_placement) != set(self.shard_map[collection_id]):
                    rebalanced[collection_id] = new_placement
                    self.shard_map[collection_id] = new_placement
            
            if rebalanced:
                logger.info(f"Rebalanced {len(rebalanced)} collections")
            
            return rebalanced


# =============================================================================
# CouchDB Cluster
# =============================================================================

class CouchDBCluster:
    """
    CouchDB high availability with native clustering.
    
    Features:
    - Native multi-master replication
    - Quorum-based reads/writes
    - Automatic sharding
    """
    
    def __init__(self, config: ClusterConfig):
        if config.database_type != DatabaseType.COUCHDB:
            raise ValueError("CouchDBCluster requires CouchDB database type")
        
        self.config = config
        self.nodes: dict[str, NodeConfig] = {}
        self.node_health: dict[str, HealthStatus] = {}
        self._lock = threading.Lock()
        
        for node in config.nodes:
            self.nodes[node.node_id] = node
            self.node_health[node.node_id] = HealthStatus.UNKNOWN
        
        logger.info(f"CouchDBCluster initialized: {config.cluster_id}")
    
    def get_healthy_nodes(self) -> list[NodeConfig]:
        """Get all healthy nodes."""
        with self._lock:
            return [
                node for node_id, node in self.nodes.items()
                if self.node_health.get(node_id) == HealthStatus.HEALTHY
            ]
    
    def check_quorum(self) -> bool:
        """Check if cluster has quorum."""
        healthy_count = len(self.get_healthy_nodes())
        required = self.config.min_nodes_for_quorum
        return healthy_count >= required
    
    def get_connection_url(self) -> str:
        """Get CouchDB connection URL (any healthy node)."""
        healthy = self.get_healthy_nodes()
        if not healthy:
            raise RuntimeError("No healthy CouchDB nodes")
        
        node = healthy[0]
        return f"http://{node.host}:{node.port}"
    
    def get_cluster_nodes_config(self) -> list[str]:
        """Get list of cluster node addresses for setup."""
        return [f"couchdb@{node.host}" for node in self.nodes.values()]
    
    def generate_local_ini(self, node_id: str) -> str:
        """Generate local.ini configuration for a node."""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        
        node = self.nodes[node_id]
        
        return f"""
[couchdb]
uuid = {self.config.cluster_id}
database_dir = /opt/couchdb/data
view_index_dir = /opt/couchdb/data

[chttpd]
port = {node.port}
bind_address = 0.0.0.0

[httpd]
bind_address = 0.0.0.0

[cluster]
q = 2
n = {len(self.nodes)}

[couch_httpd_auth]
require_valid_user = true

[admins]
admin = -pbkdf2-<hashed_password>

[vendor]
name = VCC-UDS3
"""


# =============================================================================
# HA Manager
# =============================================================================

class HAManager:
    """
    High Availability Manager for VCC-UDS3.
    
    Coordinates HA across all database types:
    - PostgreSQL (Patroni)
    - Neo4j (Causal Cluster)
    - ChromaDB (Sharding)
    - CouchDB (Clustering)
    """
    
    def __init__(self):
        self.postgresql_clusters: dict[str, PatroniCluster] = {}
        self.neo4j_clusters: dict[str, Neo4jCausalCluster] = {}
        self.chromadb_clusters: dict[str, ChromaDBCluster] = {}
        self.couchdb_clusters: dict[str, CouchDBCluster] = {}
        self._health_check_interval = 10
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
    
    def register_postgresql_cluster(
        self,
        config: ClusterConfig
    ) -> PatroniCluster:
        """Register a PostgreSQL Patroni cluster."""
        cluster = PatroniCluster(config)
        self.postgresql_clusters[config.cluster_id] = cluster
        return cluster
    
    def register_neo4j_cluster(
        self,
        config: ClusterConfig
    ) -> Neo4jCausalCluster:
        """Register a Neo4j Causal Cluster."""
        cluster = Neo4jCausalCluster(config)
        self.neo4j_clusters[config.cluster_id] = cluster
        return cluster
    
    def register_chromadb_cluster(
        self,
        config: ClusterConfig
    ) -> ChromaDBCluster:
        """Register a ChromaDB cluster."""
        cluster = ChromaDBCluster(config)
        self.chromadb_clusters[config.cluster_id] = cluster
        return cluster
    
    def register_couchdb_cluster(
        self,
        config: ClusterConfig
    ) -> CouchDBCluster:
        """Register a CouchDB cluster."""
        cluster = CouchDBCluster(config)
        self.couchdb_clusters[config.cluster_id] = cluster
        return cluster
    
    def get_overall_health(self) -> dict[str, Any]:
        """Get overall health status of all clusters."""
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "clusters": {},
            "overall_status": HealthStatus.HEALTHY.value,
        }
        
        all_healthy = True
        
        for cluster_id, cluster in self.postgresql_clusters.items():
            health = cluster.update_health_status()
            unhealthy = sum(1 for h in health.values() if h != HealthStatus.HEALTHY)
            result["clusters"][cluster_id] = {
                "type": "postgresql",
                "nodes": len(cluster.nodes),
                "unhealthy": unhealthy,
                "leader": cluster.current_leader,
            }
            if unhealthy > 0:
                all_healthy = False
        
        for cluster_id, cluster in self.neo4j_clusters.items():
            result["clusters"][cluster_id] = {
                "type": "neo4j",
                "cores": len(cluster.core_nodes),
                "replicas": len(cluster.read_replicas),
                "leader": cluster.current_leader,
            }
        
        for cluster_id, cluster in self.chromadb_clusters.items():
            healthy = len(cluster.get_healthy_nodes())
            result["clusters"][cluster_id] = {
                "type": "chromadb",
                "nodes": len(cluster.nodes),
                "healthy": healthy,
                "collections": len(cluster.shard_map),
            }
            if healthy < len(cluster.nodes):
                all_healthy = False
        
        for cluster_id, cluster in self.couchdb_clusters.items():
            result["clusters"][cluster_id] = {
                "type": "couchdb",
                "nodes": len(cluster.nodes),
                "quorum": cluster.check_quorum(),
            }
            if not cluster.check_quorum():
                all_healthy = False
        
        result["overall_status"] = (
            HealthStatus.HEALTHY.value if all_healthy
            else HealthStatus.DEGRADED.value
        )
        
        return result
    
    def start_health_monitoring(self) -> None:
        """Start background health monitoring."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(
            target=self._health_monitor_loop,
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("HA health monitoring started")
    
    def stop_health_monitoring(self) -> None:
        """Stop background health monitoring."""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("HA health monitoring stopped")
    
    def _health_monitor_loop(self) -> None:
        """Background health monitoring loop."""
        while self._monitoring_active:
            try:
                health = self.get_overall_health()
                if health["overall_status"] != HealthStatus.HEALTHY.value:
                    logger.warning(f"Cluster health degraded: {health}")
            except Exception as e:
                logger.error(f"Health check error: {e}")
            
            time.sleep(self._health_check_interval)


# =============================================================================
# Factory Functions
# =============================================================================

def create_ha_manager() -> HAManager:
    """Create a new HA manager."""
    return HAManager()


def create_postgresql_ha_config(
    cluster_id: str,
    nodes: list[tuple[str, str, int]],  # (node_id, host, port)
    replication_mode: ReplicationMode = ReplicationMode.SYNC
) -> ClusterConfig:
    """Create PostgreSQL HA configuration."""
    node_configs = [
        NodeConfig(
            node_id=node_id,
            host=host,
            port=port,
            role=NodeRole.PRIMARY if i == 0 else NodeRole.REPLICA,
            priority=100 - i * 10,
        )
        for i, (node_id, host, port) in enumerate(nodes)
    ]
    
    return ClusterConfig(
        cluster_id=cluster_id,
        database_type=DatabaseType.POSTGRESQL,
        ha_mode=HAMode.ACTIVE_PASSIVE,
        replication_mode=replication_mode,
        min_nodes_for_quorum=len(nodes) // 2 + 1,
        nodes=node_configs,
    )


def create_neo4j_ha_config(
    cluster_id: str,
    core_nodes: list[tuple[str, str, int]],
    read_replicas: list[tuple[str, str, int]] = None
) -> ClusterConfig:
    """Create Neo4j HA configuration."""
    read_replicas = read_replicas or []
    
    node_configs = [
        NodeConfig(
            node_id=node_id,
            host=host,
            port=port,
            role=NodeRole.LEADER if i == 0 else NodeRole.FOLLOWER,
            priority=100 - i * 10,
        )
        for i, (node_id, host, port) in enumerate(core_nodes)
    ]
    
    for node_id, host, port in read_replicas:
        node_configs.append(NodeConfig(
            node_id=node_id,
            host=host,
            port=port,
            role=NodeRole.REPLICA,
            priority=0,
        ))
    
    return ClusterConfig(
        cluster_id=cluster_id,
        database_type=DatabaseType.NEO4J,
        ha_mode=HAMode.QUORUM,
        min_nodes_for_quorum=len(core_nodes) // 2 + 1,
        nodes=node_configs,
    )


def setup_vcc_ha() -> HAManager:
    """
    Set up standard VCC-UDS3 HA configuration.
    
    Creates HA clusters for all databases:
    - PostgreSQL: 1 primary + 2 replicas
    - Neo4j: 3 core nodes + 2 read replicas
    - ChromaDB: 2 shards
    - CouchDB: 3 nodes (quorum)
    """
    manager = create_ha_manager()
    
    # PostgreSQL cluster
    pg_config = create_postgresql_ha_config(
        cluster_id="vcc-postgresql",
        nodes=[
            ("pg-primary", "pg-primary.vcc.local", 5432),
            ("pg-replica-1", "pg-replica-1.vcc.local", 5432),
            ("pg-replica-2", "pg-replica-2.vcc.local", 5432),
        ],
        replication_mode=ReplicationMode.SYNC,
    )
    pg_cluster = manager.register_postgresql_cluster(pg_config)
    pg_cluster.elect_leader()
    
    # Neo4j cluster
    neo4j_config = create_neo4j_ha_config(
        cluster_id="vcc-neo4j",
        core_nodes=[
            ("neo4j-core-1", "neo4j-core-1.vcc.local", 7687),
            ("neo4j-core-2", "neo4j-core-2.vcc.local", 7687),
            ("neo4j-core-3", "neo4j-core-3.vcc.local", 7687),
        ],
        read_replicas=[
            ("neo4j-replica-1", "neo4j-replica-1.vcc.local", 7687),
            ("neo4j-replica-2", "neo4j-replica-2.vcc.local", 7687),
        ],
    )
    neo4j_cluster = manager.register_neo4j_cluster(neo4j_config)
    neo4j_cluster.elect_leader()
    
    # ChromaDB cluster
    chromadb_config = ClusterConfig(
        cluster_id="vcc-chromadb",
        database_type=DatabaseType.CHROMADB,
        ha_mode=HAMode.ACTIVE_ACTIVE,
        nodes=[
            NodeConfig("chromadb-1", "chromadb-1.vcc.local", 8000, NodeRole.PRIMARY),
            NodeConfig("chromadb-2", "chromadb-2.vcc.local", 8000, NodeRole.PRIMARY),
        ],
    )
    manager.register_chromadb_cluster(chromadb_config)
    
    # CouchDB cluster
    couchdb_config = ClusterConfig(
        cluster_id="vcc-couchdb",
        database_type=DatabaseType.COUCHDB,
        ha_mode=HAMode.QUORUM,
        min_nodes_for_quorum=2,
        nodes=[
            NodeConfig("couchdb-1", "couchdb-1.vcc.local", 5984, NodeRole.PRIMARY),
            NodeConfig("couchdb-2", "couchdb-2.vcc.local", 5984, NodeRole.PRIMARY),
            NodeConfig("couchdb-3", "couchdb-3.vcc.local", 5984, NodeRole.PRIMARY),
        ],
    )
    manager.register_couchdb_cluster(couchdb_config)
    
    logger.info("VCC-UDS3 HA setup complete")
    return manager
