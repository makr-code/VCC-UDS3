#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
metrics.py

UDS3 Prometheus Metrics - Production-Grade Observability
Provides Prometheus-compatible metrics for monitoring UDS3 performance.

v1.6.0 Implementation (RAGOps):
- RED Metrics (Rate, Errors, Duration)
- Database backend metrics
- Search API metrics (latency, results, fusion)
- SAGA transaction metrics
- Cache hit/miss rates

Metrics Export:
- HTTP endpoint: /metrics (Prometheus scrape target)
- Push Gateway support for batch jobs
- Labels for multi-instance deployments

Usage:
    from core.metrics import metrics
    
    # Track search latency
    with metrics.search_latency.labels(search_type="hybrid").time():
        results = await search_api.hybrid_search(query)
    
    # Increment counters
    metrics.search_requests.labels(search_type="vector", status="success").inc()

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

import logging
import time
from typing import Optional, Dict, Any, Callable
from functools import wraps
from contextlib import contextmanager
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Try to import prometheus_client, provide fallback if not available
try:
    from prometheus_client import (
        Counter, Histogram, Gauge, Summary,
        CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST,
        push_to_gateway, start_http_server
    )
    PROMETHEUS_AVAILABLE = True
    logger.info("✅ Prometheus client available")
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("⚠️ prometheus_client not installed - metrics will be no-op")


# ============================================================================
# Fallback Classes (when prometheus_client is not available)
# ============================================================================

class NoOpMetric:
    """No-op metric for when Prometheus is not available"""
    def labels(self, **kwargs):
        return self
    
    def inc(self, amount=1):
        pass
    
    def dec(self, amount=1):
        pass
    
    def set(self, value):
        pass
    
    def observe(self, value):
        pass
    
    @contextmanager
    def time(self):
        yield


class NoOpRegistry:
    """No-op registry for when Prometheus is not available"""
    pass


# ============================================================================
# Metric Definitions
# ============================================================================

@dataclass
class UDS3Metrics:
    """
    UDS3 Prometheus Metrics Collection
    
    Organized by category:
    - Search: Latency, requests, results
    - Database: Connections, queries, errors
    - SAGA: Transactions, completions, compensations
    - Cache: Hits, misses, size
    - System: Memory, CPU, uptime
    """
    
    registry: Any = field(default=None)
    _initialized: bool = field(default=False)
    
    # Search Metrics
    search_requests: Any = field(default=None)
    search_latency: Any = field(default=None)
    search_results: Any = field(default=None)
    search_errors: Any = field(default=None)
    
    # Database Metrics
    db_connections: Any = field(default=None)
    db_queries: Any = field(default=None)
    db_query_latency: Any = field(default=None)
    db_errors: Any = field(default=None)
    
    # SAGA Metrics
    saga_transactions: Any = field(default=None)
    saga_completions: Any = field(default=None)
    saga_compensations: Any = field(default=None)
    saga_latency: Any = field(default=None)
    
    # Cache Metrics
    cache_hits: Any = field(default=None)
    cache_misses: Any = field(default=None)
    cache_size: Any = field(default=None)
    
    # RRF/Fusion Metrics
    fusion_requests: Any = field(default=None)
    fusion_latency: Any = field(default=None)
    
    def __post_init__(self):
        """Initialize metrics with Prometheus or fallbacks"""
        if PROMETHEUS_AVAILABLE:
            self._init_prometheus_metrics()
        else:
            self._init_noop_metrics()
        self._initialized = True
    
    def _init_prometheus_metrics(self):
        """Initialize real Prometheus metrics"""
        self.registry = CollectorRegistry()
        
        # ========== Search Metrics ==========
        self.search_requests = Counter(
            'uds3_search_requests_total',
            'Total number of search requests',
            ['search_type', 'status', 'fusion_method'],
            registry=self.registry
        )
        
        self.search_latency = Histogram(
            'uds3_search_latency_seconds',
            'Search request latency in seconds',
            ['search_type', 'fusion_method'],
            buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )
        
        self.search_results = Histogram(
            'uds3_search_results_count',
            'Number of results returned per search',
            ['search_type'],
            buckets=[0, 1, 5, 10, 20, 50, 100],
            registry=self.registry
        )
        
        self.search_errors = Counter(
            'uds3_search_errors_total',
            'Total number of search errors',
            ['search_type', 'error_type'],
            registry=self.registry
        )
        
        # ========== Database Metrics ==========
        self.db_connections = Gauge(
            'uds3_db_connections',
            'Number of database connections',
            ['backend', 'state'],
            registry=self.registry
        )
        
        self.db_queries = Counter(
            'uds3_db_queries_total',
            'Total number of database queries',
            ['backend', 'operation', 'status'],
            registry=self.registry
        )
        
        self.db_query_latency = Histogram(
            'uds3_db_query_latency_seconds',
            'Database query latency in seconds',
            ['backend', 'operation'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
            registry=self.registry
        )
        
        self.db_errors = Counter(
            'uds3_db_errors_total',
            'Total number of database errors',
            ['backend', 'error_type'],
            registry=self.registry
        )
        
        # ========== SAGA Metrics ==========
        self.saga_transactions = Counter(
            'uds3_saga_transactions_total',
            'Total number of SAGA transactions',
            ['status'],
            registry=self.registry
        )
        
        self.saga_completions = Counter(
            'uds3_saga_completions_total',
            'Total number of SAGA completions',
            ['result'],
            registry=self.registry
        )
        
        self.saga_compensations = Counter(
            'uds3_saga_compensations_total',
            'Total number of SAGA compensations executed',
            ['step', 'reason'],
            registry=self.registry
        )
        
        self.saga_latency = Histogram(
            'uds3_saga_latency_seconds',
            'SAGA transaction latency in seconds',
            ['operation'],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
            registry=self.registry
        )
        
        # ========== Cache Metrics ==========
        self.cache_hits = Counter(
            'uds3_cache_hits_total',
            'Total number of cache hits',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'uds3_cache_misses_total',
            'Total number of cache misses',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_size = Gauge(
            'uds3_cache_size_bytes',
            'Current cache size in bytes',
            ['cache_type'],
            registry=self.registry
        )
        
        # ========== RRF/Fusion Metrics ==========
        self.fusion_requests = Counter(
            'uds3_fusion_requests_total',
            'Total number of fusion operations',
            ['method', 'sources'],
            registry=self.registry
        )
        
        self.fusion_latency = Histogram(
            'uds3_fusion_latency_seconds',
            'Fusion operation latency in seconds',
            ['method'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1],
            registry=self.registry
        )
        
        logger.info("✅ Prometheus metrics initialized")
    
    def _init_noop_metrics(self):
        """Initialize no-op metrics when Prometheus is not available"""
        self.registry = NoOpRegistry()
        self.search_requests = NoOpMetric()
        self.search_latency = NoOpMetric()
        self.search_results = NoOpMetric()
        self.search_errors = NoOpMetric()
        self.db_connections = NoOpMetric()
        self.db_queries = NoOpMetric()
        self.db_query_latency = NoOpMetric()
        self.db_errors = NoOpMetric()
        self.saga_transactions = NoOpMetric()
        self.saga_completions = NoOpMetric()
        self.saga_compensations = NoOpMetric()
        self.saga_latency = NoOpMetric()
        self.cache_hits = NoOpMetric()
        self.cache_misses = NoOpMetric()
        self.cache_size = NoOpMetric()
        self.fusion_requests = NoOpMetric()
        self.fusion_latency = NoOpMetric()
        
        logger.info("✅ No-op metrics initialized (prometheus_client not available)")
    
    def get_metrics(self) -> bytes:
        """
        Generate Prometheus metrics output
        
        Returns:
            bytes: Prometheus-formatted metrics text
        """
        if PROMETHEUS_AVAILABLE:
            return generate_latest(self.registry)
        return b"# Prometheus client not available\n"
    
    def start_http_server(self, port: int = 9090, addr: str = "0.0.0.0"):
        """
        Start HTTP server for Prometheus scraping
        
        Args:
            port: Port to listen on (default: 9090)
            addr: Address to bind to (default: 0.0.0.0)
        """
        if PROMETHEUS_AVAILABLE:
            start_http_server(port, addr, registry=self.registry)
            logger.info(f"✅ Prometheus metrics server started on {addr}:{port}")
        else:
            logger.warning("⚠️ Cannot start metrics server - prometheus_client not available")
    
    def push_to_gateway(self, gateway: str, job: str, grouping_key: Optional[Dict] = None):
        """
        Push metrics to Prometheus Push Gateway
        
        Args:
            gateway: Push Gateway URL (e.g., 'localhost:9091')
            job: Job name for grouping
            grouping_key: Additional grouping labels
        """
        if PROMETHEUS_AVAILABLE:
            push_to_gateway(gateway, job, self.registry, grouping_key)
            logger.info(f"✅ Metrics pushed to gateway {gateway}")
        else:
            logger.warning("⚠️ Cannot push metrics - prometheus_client not available")


# ============================================================================
# Decorators for Easy Instrumentation
# ============================================================================

def track_search_latency(search_type: str = "hybrid", fusion_method: str = "rrf"):
    """
    Decorator to track search latency
    
    Usage:
        @track_search_latency(search_type="vector")
        async def vector_search(self, query):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                metrics.search_errors.labels(
                    search_type=search_type,
                    error_type=type(e).__name__
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                metrics.search_latency.labels(
                    search_type=search_type,
                    fusion_method=fusion_method
                ).observe(duration)
                metrics.search_requests.labels(
                    search_type=search_type,
                    status=status,
                    fusion_method=fusion_method
                ).inc()
        return wrapper
    return decorator


def track_db_query(backend: str, operation: str):
    """
    Decorator to track database query latency
    
    Usage:
        @track_db_query(backend="postgresql", operation="select")
        def execute_query(self, sql):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                metrics.db_errors.labels(
                    backend=backend,
                    error_type=type(e).__name__
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                metrics.db_query_latency.labels(
                    backend=backend,
                    operation=operation
                ).observe(duration)
                metrics.db_queries.labels(
                    backend=backend,
                    operation=operation,
                    status=status
                ).inc()
        return wrapper
    return decorator


def track_saga_transaction(operation: str = "full"):
    """
    Decorator to track SAGA transaction latency
    
    Usage:
        @track_saga_transaction(operation="create_document")
        async def execute_saga(self):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "started"
            metrics.saga_transactions.labels(status=status).inc()
            try:
                result = await func(*args, **kwargs)
                metrics.saga_completions.labels(result="success").inc()
                return result
            except Exception as e:
                metrics.saga_completions.labels(result="failure").inc()
                raise
            finally:
                duration = time.time() - start_time
                metrics.saga_latency.labels(operation=operation).observe(duration)
        return wrapper
    return decorator


# ============================================================================
# Context Managers for Manual Instrumentation
# ============================================================================

@contextmanager
def measure_latency(metric_histogram, **labels):
    """
    Context manager for measuring latency
    
    Usage:
        with measure_latency(metrics.search_latency, search_type="hybrid"):
            results = await search(query)
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        metric_histogram.labels(**labels).observe(duration)


# ============================================================================
# Global Metrics Instance
# ============================================================================

# Singleton metrics instance
metrics = UDS3Metrics()


def get_metrics() -> UDS3Metrics:
    """Get the global metrics instance"""
    return metrics


def get_metrics_output() -> bytes:
    """Get Prometheus-formatted metrics output"""
    return metrics.get_metrics()


# ============================================================================
# Flask/FastAPI Integration
# ============================================================================

def create_metrics_endpoint():
    """
    Create a metrics endpoint handler for Flask/FastAPI
    
    Flask usage:
        app.add_url_rule('/metrics', 'metrics', create_metrics_endpoint())
    
    FastAPI usage:
        @app.get('/metrics')
        async def metrics_endpoint():
            return Response(content=get_metrics_output(), media_type=CONTENT_TYPE_LATEST)
    """
    def metrics_handler():
        if PROMETHEUS_AVAILABLE:
            from flask import Response
            return Response(
                get_metrics_output(),
                mimetype=CONTENT_TYPE_LATEST
            )
        else:
            from flask import Response
            return Response(
                b"# Prometheus client not available\n",
                mimetype="text/plain"
            )
    return metrics_handler


# ============================================================================
# Initialization Check
# ============================================================================

def check_prometheus_available() -> bool:
    """Check if Prometheus client is available"""
    return PROMETHEUS_AVAILABLE


if __name__ == "__main__":
    # Demo usage
    print(f"Prometheus available: {PROMETHEUS_AVAILABLE}")
    
    # Test metrics
    metrics.search_requests.labels(
        search_type="hybrid",
        status="success",
        fusion_method="rrf"
    ).inc()
    
    metrics.search_latency.labels(
        search_type="hybrid",
        fusion_method="rrf"
    ).observe(0.123)
    
    print("\nGenerated metrics:")
    print(metrics.get_metrics().decode('utf-8')[:500])
