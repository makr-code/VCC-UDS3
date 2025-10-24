#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extensions.py

extensions.py
UDS3 DatabaseManager Extensions - Multi-DB Features Integration
Extends DatabaseManager with opt-in integration features:
- SAGA Pattern for distributed transactions
- Adaptive Query Routing for performance
- Multi-DB Distributor for load balancing
These features are loaded on-demand and can be enabled/disabled at runtime.
Usage:
from database.database_manager import DatabaseManager
from database.extensions import DatabaseManagerExtensions
# Initialize DatabaseManager
db_manager = DatabaseManager(backend_dict)
# Create extensions wrapper
extensions = DatabaseManagerExtensions(db_manager)
# Enable SAGA Pattern
extensions.enable_saga()
# Use SAGA for multi-DB transaction
result = extensions.execute_saga_transaction(
transaction_name="save_process_multi_db",
steps=[
{"db": "relational", "operation": "insert", "data": {...}},
{"db": "vector", "operation": "add_document", "data": {...}},
Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ExtensionStatus(Enum):
    """Status of extension modules"""
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class ExtensionInfo:
    """Information about an extension module"""
    name: str
    status: ExtensionStatus
    version: Optional[str] = None
    error: Optional[str] = None
    config: Dict[str, Any] = None


class DatabaseManagerExtensions:
    """
    Extensions wrapper for DatabaseManager.
    
    Provides opt-in integration with:
    - SAGA Pattern (integration/saga_integration.py)
    - Adaptive Routing (integration/adaptive_strategy.py)
    - Multi-DB Distributor (integration/distributor.py)
    
    Extensions are lazy-loaded and can be enabled/disabled at runtime.
    """

    def __init__(self, database_manager):
        """
        Initialize extensions wrapper.

        Args:
            database_manager: DatabaseManager instance to extend
        """
        self.db_manager = database_manager
        
        # Extension status tracking
        self.extensions = {
            "saga": ExtensionInfo(name="SAGA Pattern", status=ExtensionStatus.NOT_LOADED),
            "routing": ExtensionInfo(name="Adaptive Routing", status=ExtensionStatus.NOT_LOADED),
            "distributor": ExtensionInfo(name="Multi-DB Distributor", status=ExtensionStatus.NOT_LOADED)
        }
        
        # Extension instances (lazy-loaded)
        self._saga_orchestrator = None
        self._adaptive_strategy = None
        self._multi_db_distributor = None
        
        logger.info("DatabaseManagerExtensions initialized")

    # ========================================================================
    # SAGA Pattern Integration
    # ========================================================================

    def enable_saga(
        self,
        config: Optional[Dict[str, Any]] = None,
        auto_rollback: bool = True
    ) -> bool:
        """
        Enable SAGA Pattern for distributed transactions.

        Args:
            config: SAGA configuration (optional)
            auto_rollback: Automatically rollback on failure

        Returns:
            True if enabled successfully
        """
        try:
            self.extensions["saga"].status = ExtensionStatus.LOADING
            
            # Lazy import
            from integration.saga_integration import SAGAMultiDBOrchestrator
            
            # Create SAGA orchestrator
            self._saga_orchestrator = SAGAMultiDBOrchestrator(
                database_manager=self.db_manager,
                auto_rollback=auto_rollback,
                **(config or {})
            )
            
            self.extensions["saga"].status = ExtensionStatus.ENABLED
            self.extensions["saga"].config = config or {}
            
            logger.info("✅ SAGA Pattern enabled")
            return True
            
        except ImportError as e:
            error_msg = f"SAGA module not found: {e}"
            logger.error(f"❌ {error_msg}")
            self.extensions["saga"].status = ExtensionStatus.ERROR
            self.extensions["saga"].error = error_msg
            return False
            
        except Exception as e:
            error_msg = f"SAGA initialization failed: {e}"
            logger.error(f"❌ {error_msg}")
            self.extensions["saga"].status = ExtensionStatus.ERROR
            self.extensions["saga"].error = error_msg
            return False

    def disable_saga(self) -> bool:
        """Disable SAGA Pattern."""
        if self._saga_orchestrator:
            self._saga_orchestrator = None
            self.extensions["saga"].status = ExtensionStatus.DISABLED
            logger.info("SAGA Pattern disabled")
            return True
        return False

    def execute_saga_transaction(
        self,
        transaction_name: str,
        steps: List[Dict[str, Any]],
        timeout_seconds: float = 300.0
    ) -> Dict[str, Any]:
        """
        Execute a SAGA transaction with automatic compensation on failure.

        Args:
            transaction_name: Name for the transaction
            steps: List of transaction steps
                   Each step: {"db": "relational|vector|graph", 
                              "operation": "insert|update|delete|...",
                              "data": {...},
                              "compensation": {...}}
            timeout_seconds: Transaction timeout

        Returns:
            Dict with transaction result

        Example:
            result = extensions.execute_saga_transaction(
                transaction_name="save_process_multi_db",
                steps=[
                    {
                        "db": "relational",
                        "operation": "insert",
                        "collection": "processes",
                        "data": {"id": "p1", "name": "Test"},
                        "compensation": {"operation": "delete", "id": "p1"}
                    },
                    {
                        "db": "vector",
                        "operation": "add_document",
                        "collection": "process_embeddings",
                        "data": {"id": "p1_emb", "text": "Test"},
                        "compensation": {"operation": "delete", "id": "p1_emb"}
                    }
                ],
                timeout_seconds=60.0
            )
        """
        if not self._saga_orchestrator:
            raise RuntimeError("SAGA Pattern not enabled. Call enable_saga() first.")
        
        try:
            result = self._saga_orchestrator.execute_transaction(
                transaction_name=transaction_name,
                steps=steps,
                timeout_seconds=timeout_seconds
            )
            
            return result
            
        except Exception as e:
            logger.error(f"SAGA transaction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "transaction_name": transaction_name
            }

    # ========================================================================
    # Adaptive Routing Integration
    # ========================================================================

    def enable_adaptive_routing(
        self,
        config: Optional[Dict[str, Any]] = None,
        enable_monitoring: bool = True
    ) -> bool:
        """
        Enable Adaptive Query Routing for performance optimization.

        Args:
            config: Routing configuration (optional)
            enable_monitoring: Enable performance monitoring

        Returns:
            True if enabled successfully
        """
        try:
            self.extensions["routing"].status = ExtensionStatus.LOADING
            
            # Lazy import
            from integration.adaptive_strategy import AdaptiveMultiDBStrategy
            
            # Create adaptive strategy
            self._adaptive_strategy = AdaptiveMultiDBStrategy(
                database_manager=self.db_manager,
                enable_monitoring=enable_monitoring,
                **(config or {})
            )
            
            self.extensions["routing"].status = ExtensionStatus.ENABLED
            self.extensions["routing"].config = config or {}
            
            logger.info("✅ Adaptive Routing enabled")
            return True
            
        except ImportError as e:
            error_msg = f"Adaptive Routing module not found: {e}"
            logger.error(f"❌ {error_msg}")
            self.extensions["routing"].status = ExtensionStatus.ERROR
            self.extensions["routing"].error = error_msg
            return False
            
        except Exception as e:
            error_msg = f"Adaptive Routing initialization failed: {e}"
            logger.error(f"❌ {error_msg}")
            self.extensions["routing"].status = ExtensionStatus.ERROR
            self.extensions["routing"].error = error_msg
            return False

    def disable_adaptive_routing(self) -> bool:
        """Disable Adaptive Routing."""
        if self._adaptive_strategy:
            self._adaptive_strategy = None
            self.extensions["routing"].status = ExtensionStatus.DISABLED
            logger.info("Adaptive Routing disabled")
            return True
        return False

    def route_query(
        self,
        query_type: str,
        query_data: Dict[str, Any],
        prefer_performance: bool = True
    ) -> Dict[str, Any]:
        """
        Route query to optimal database backend.

        Args:
            query_type: Type of query (search, get, aggregate, etc.)
            query_data: Query parameters
            prefer_performance: Prefer performance over consistency

        Returns:
            Dict with query result and routing info

        Example:
            result = extensions.route_query(
                query_type="semantic_search",
                query_data={"query": "Baugenehmigung", "top_k": 10},
                prefer_performance=True
            )
            # Routes to ChromaDB (fastest for semantic search)
        """
        if not self._adaptive_strategy:
            raise RuntimeError("Adaptive Routing not enabled. Call enable_adaptive_routing() first.")
        
        try:
            result = self._adaptive_strategy.route_query(
                query_type=query_type,
                query_data=query_data,
                prefer_performance=prefer_performance
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Query routing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query_type": query_type
            }

    def get_routing_statistics(self) -> Dict[str, Any]:
        """
        Get routing performance statistics.

        Returns:
            Dict with routing stats (queries routed, performance metrics, etc.)
        """
        if not self._adaptive_strategy:
            return {"error": "Adaptive Routing not enabled"}
        
        try:
            return self._adaptive_strategy.get_statistics()
        except Exception as e:
            logger.error(f"Failed to get routing statistics: {e}")
            return {"error": str(e)}

    # ========================================================================
    # Multi-DB Distributor Integration
    # ========================================================================

    def enable_distributor(
        self,
        config: Optional[Dict[str, Any]] = None,
        enable_load_balancing: bool = True
    ) -> bool:
        """
        Enable Multi-DB Distributor for load balancing.

        Args:
            config: Distributor configuration (optional)
            enable_load_balancing: Enable automatic load balancing

        Returns:
            True if enabled successfully
        """
        try:
            self.extensions["distributor"].status = ExtensionStatus.LOADING
            
            # Lazy import
            from integration.distributor import UDS3MultiDBDistributor
            
            # Create distributor
            self._multi_db_distributor = UDS3MultiDBDistributor(
                database_manager=self.db_manager,
                enable_load_balancing=enable_load_balancing,
                **(config or {})
            )
            
            self.extensions["distributor"].status = ExtensionStatus.ENABLED
            self.extensions["distributor"].config = config or {}
            
            logger.info("✅ Multi-DB Distributor enabled")
            return True
            
        except ImportError as e:
            error_msg = f"Distributor module not found: {e}"
            logger.error(f"❌ {error_msg}")
            self.extensions["distributor"].status = ExtensionStatus.ERROR
            self.extensions["distributor"].error = error_msg
            return False
            
        except Exception as e:
            error_msg = f"Distributor initialization failed: {e}"
            logger.error(f"❌ {error_msg}")
            self.extensions["distributor"].status = ExtensionStatus.ERROR
            self.extensions["distributor"].error = error_msg
            return False

    def disable_distributor(self) -> bool:
        """Disable Multi-DB Distributor."""
        if self._multi_db_distributor:
            self._multi_db_distributor = None
            self.extensions["distributor"].status = ExtensionStatus.DISABLED
            logger.info("Multi-DB Distributor disabled")
            return True
        return False

    def distribute_operation(
        self,
        operation_type: str,
        operation_data: Dict[str, Any],
        target_databases: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Distribute operation across multiple databases.

        Args:
            operation_type: Type of operation (save, update, delete, etc.)
            operation_data: Operation parameters
            target_databases: List of target DBs (None = all configured)

        Returns:
            Dict with distribution result

        Example:
            result = extensions.distribute_operation(
                operation_type="save",
                operation_data={
                    "collection": "processes",
                    "data": {"id": "p1", "name": "Test"}
                },
                target_databases=["relational", "vector", "graph"]
            )
        """
        if not self._multi_db_distributor:
            raise RuntimeError("Multi-DB Distributor not enabled. Call enable_distributor() first.")
        
        try:
            result = self._multi_db_distributor.distribute(
                operation_type=operation_type,
                operation_data=operation_data,
                target_databases=target_databases
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Distribution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation_type": operation_type
            }

    def get_distributor_statistics(self) -> Dict[str, Any]:
        """
        Get distributor performance statistics.

        Returns:
            Dict with distributor stats (operations distributed, load metrics, etc.)
        """
        if not self._multi_db_distributor:
            return {"error": "Multi-DB Distributor not enabled"}
        
        try:
            return self._multi_db_distributor.get_statistics()
        except Exception as e:
            logger.error(f"Failed to get distributor statistics: {e}")
            return {"error": str(e)}

    # ========================================================================
    # Extension Management
    # ========================================================================

    def get_extension_status(self, extension_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get status of extensions.

        Args:
            extension_name: Specific extension ("saga", "routing", "distributor")
                           None = all extensions

        Returns:
            Dict with extension status
        """
        if extension_name:
            if extension_name in self.extensions:
                ext = self.extensions[extension_name]
                return {
                    "name": ext.name,
                    "status": ext.status.value,
                    "version": ext.version,
                    "error": ext.error,
                    "config": ext.config
                }
            else:
                return {"error": f"Unknown extension: {extension_name}"}
        else:
            # Return all extensions
            return {
                name: {
                    "name": ext.name,
                    "status": ext.status.value,
                    "version": ext.version,
                    "error": ext.error,
                    "config": ext.config
                }
                for name, ext in self.extensions.items()
            }

    def enable_all(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
        """
        Enable all extensions.

        Args:
            config: Configuration dict with keys: saga, routing, distributor

        Returns:
            Dict with success status for each extension
        """
        config = config or {}
        
        results = {
            "saga": self.enable_saga(config.get("saga")),
            "routing": self.enable_adaptive_routing(config.get("routing")),
            "distributor": self.enable_distributor(config.get("distributor"))
        }
        
        enabled_count = sum(results.values())
        logger.info(f"Extensions enabled: {enabled_count}/3")
        
        return results

    def disable_all(self) -> Dict[str, bool]:
        """
        Disable all extensions.

        Returns:
            Dict with success status for each extension
        """
        results = {
            "saga": self.disable_saga(),
            "routing": self.disable_adaptive_routing(),
            "distributor": self.disable_distributor()
        }
        
        return results

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics for all enabled extensions.

        Returns:
            Dict with statistics from all enabled extensions
        """
        stats = {
            "extensions_status": self.get_extension_status(),
            "saga": self.get_saga_statistics() if self._saga_orchestrator else None,
            "routing": self.get_routing_statistics() if self._adaptive_strategy else None,
            "distributor": self.get_distributor_statistics() if self._multi_db_distributor else None
        }
        
        return stats

    def get_saga_statistics(self) -> Dict[str, Any]:
        """Get SAGA statistics."""
        if not self._saga_orchestrator:
            return {"error": "SAGA not enabled"}
        
        try:
            return self._saga_orchestrator.get_statistics()
        except Exception as e:
            logger.error(f"Failed to get SAGA statistics: {e}")
            return {"error": str(e)}


# ============================================================================
# Helper Function
# ============================================================================

def create_extended_database_manager(
    backend_dict: Dict[str, Any],
    enable_saga: bool = False,
    enable_routing: bool = False,
    enable_distributor: bool = False,
    extension_config: Optional[Dict[str, Any]] = None
) -> DatabaseManagerExtensions:
    """
    Factory function to create DatabaseManager with extensions.

    Args:
        backend_dict: DatabaseManager backend configuration
        enable_saga: Enable SAGA Pattern
        enable_routing: Enable Adaptive Routing
        enable_distributor: Enable Multi-DB Distributor
        extension_config: Configuration for extensions

    Returns:
        DatabaseManagerExtensions instance

    Example:
        extended_db = create_extended_database_manager(
            backend_dict={
                "vector": {"enabled": True, ...},
                "graph": {"enabled": True, ...},
                "relational": {"enabled": True, ...}
            },
            enable_saga=True,
            enable_routing=True,
            enable_distributor=True
        )
        
        # Use SAGA
        result = extended_db.execute_saga_transaction(...)
        
        # Use Routing
        result = extended_db.route_query(...)
        
        # Use Distributor
        result = extended_db.distribute_operation(...)
    """
    from database.database_manager import DatabaseManager
    
    # Create DatabaseManager
    db_manager = DatabaseManager(backend_dict, autostart=True)
    
    # Create extensions wrapper
    extensions = DatabaseManagerExtensions(db_manager)
    
    # Enable requested extensions
    extension_config = extension_config or {}
    
    if enable_saga:
        extensions.enable_saga(config=extension_config.get("saga"))
    
    if enable_routing:
        extensions.enable_adaptive_routing(config=extension_config.get("routing"))
    
    if enable_distributor:
        extensions.enable_distributor(config=extension_config.get("distributor"))
    
    logger.info(
        f"Extended DatabaseManager created "
        f"(SAGA: {enable_saga}, Routing: {enable_routing}, Distributor: {enable_distributor})"
    )
    
    return extensions
