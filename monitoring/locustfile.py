#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
locustfile.py

VCC-UDS3 Load Testing Framework using Locust
Production-grade load testing for RAG pipeline performance validation.

v1.6.0 Implementation:
- Test scenarios: Read-heavy, Write-heavy, Mixed Workload
- Support for 10, 100, 1000 concurrent users
- Metrics collection for capacity planning
- Distributed load generation support

Test Scenarios:
1. HybridSearchUser: Tests the full RAG pipeline (BM25 + Vector + RRF + Reranking)
2. GraphTraversalUser: Tests multi-hop reasoning performance
3. SAGATransactionUser: Tests cross-database transaction performance
4. MixedWorkloadUser: Realistic production traffic mix

Usage:
    # Single instance (development)
    locust -f locustfile.py --host=http://localhost:8000
    
    # Distributed mode (production load testing)
    # Master:
    locust -f locustfile.py --master --host=http://uds3-api:8000
    # Workers:
    locust -f locustfile.py --worker --master-host=locust-master

    # Headless mode with specific user count
    locust -f locustfile.py --headless -u 100 -r 10 -t 10m --host=http://uds3-api:8000

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

import json
import random
import time
from typing import List, Dict, Any

try:
    from locust import HttpUser, task, between, events, tag
    from locust.runners import MasterRunner, WorkerRunner
    LOCUST_AVAILABLE = True
except ImportError:
    LOCUST_AVAILABLE = False
    # Provide mock classes for syntax checking
    class HttpUser:
        pass
    def task(weight=1):
        def decorator(func):
            return func
        return decorator
    def between(min_wait, max_wait):
        return lambda: random.uniform(min_wait, max_wait)
    def tag(*tags):
        def decorator(func):
            return func
        return decorator


# ============================================================================
# Test Data - German Legal Domain Queries
# ============================================================================

SEARCH_QUERIES = [
    # Building regulations (LBO)
    "§ 58 LBO Abstandsflächen",
    "Baugenehmigung Verfahren",
    "Grenzabstand Gebäude",
    "Brandschutz Anforderungen Wohngebäude",
    "Aufzug Pflicht Geschosse",
    
    # Administrative procedures (VwVfG)
    "Verwaltungsakt Definition",
    "Anhörung Beteiligter",
    "Widerspruchsverfahren Frist",
    "Ermessensentscheidung Grundsätze",
    
    # Environmental regulations
    "Umweltverträglichkeitsprüfung UVP",
    "Immissionsschutz Genehmigung",
    "Naturschutz Eingriffsregelung",
    
    # Data protection (GDPR/DSGVO)
    "Personenbezogene Daten Verarbeitung",
    "Auskunftsrecht DSGVO",
    "Löschung personenbezogener Daten",
    
    # Municipal regulations
    "Bebauungsplan Festsetzungen",
    "Flächennutzungsplan Änderung",
    "Kommunale Satzung",
    
    # Complex multi-hop queries
    "§ 34 BauGB Zulässigkeit Vorhaben",
    "Planungsrecht Abwägung",
    "Bauordnungsrecht Landesrecht",
]

DOCUMENT_IDS = [
    "lbo_bw_58",
    "lbo_bw_59",
    "vwvfg_28",
    "vwvfg_35",
    "baugesetzbuch_34",
    "baugesetzbuch_35",
    "dsgvo_art_15",
    "dsgvo_art_17",
    "uvp_gesetz_3",
    "bimschg_4",
]

DOCUMENT_CONTENT = {
    "title": "Test Document",
    "content": "Dies ist ein Testdokument für die Lasttests.",
    "classification": "regulation",
    "metadata": {
        "source": "load_test",
        "created_at": "2024-01-01T00:00:00Z"
    }
}


# ============================================================================
# Metrics Collection
# ============================================================================

class MetricsCollector:
    """Collect and aggregate load test metrics"""
    
    def __init__(self):
        self.search_latencies: List[float] = []
        self.saga_latencies: List[float] = []
        self.multi_hop_latencies: List[float] = []
        self.errors: Dict[str, int] = {}
    
    def record_search(self, latency_ms: float):
        self.search_latencies.append(latency_ms)
    
    def record_saga(self, latency_ms: float):
        self.saga_latencies.append(latency_ms)
    
    def record_multi_hop(self, latency_ms: float):
        self.multi_hop_latencies.append(latency_ms)
    
    def record_error(self, error_type: str):
        self.errors[error_type] = self.errors.get(error_type, 0) + 1
    
    def get_percentile(self, data: List[float], percentile: int) -> float:
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def get_summary(self) -> Dict[str, Any]:
        return {
            "search": {
                "count": len(self.search_latencies),
                "p50_ms": self.get_percentile(self.search_latencies, 50),
                "p95_ms": self.get_percentile(self.search_latencies, 95),
                "p99_ms": self.get_percentile(self.search_latencies, 99),
                "avg_ms": sum(self.search_latencies) / len(self.search_latencies) if self.search_latencies else 0,
            },
            "saga": {
                "count": len(self.saga_latencies),
                "p50_ms": self.get_percentile(self.saga_latencies, 50),
                "p95_ms": self.get_percentile(self.saga_latencies, 95),
                "p99_ms": self.get_percentile(self.saga_latencies, 99),
            },
            "multi_hop": {
                "count": len(self.multi_hop_latencies),
                "p50_ms": self.get_percentile(self.multi_hop_latencies, 50),
                "p95_ms": self.get_percentile(self.multi_hop_latencies, 95),
            },
            "errors": self.errors,
        }


# Global metrics collector
metrics_collector = MetricsCollector()


# ============================================================================
# Load Test Users
# ============================================================================

if LOCUST_AVAILABLE:
    
    class HybridSearchUser(HttpUser):
        """
        Tests the full RAG pipeline with hybrid search.
        
        Simulates users performing legal document searches with:
        - BM25 keyword search
        - Vector similarity search
        - Graph-based search
        - RRF fusion
        - Cross-Encoder reranking
        """
        weight = 50  # 50% of users
        wait_time = between(1, 3)
        
        @task(10)
        @tag("search", "hybrid")
        def hybrid_search_rrf(self):
            """Hybrid search with RRF fusion"""
            query = random.choice(SEARCH_QUERIES)
            payload = {
                "query_text": query,
                "search_types": ["vector", "keyword", "graph"],
                "fusion_method": "rrf",
                "top_k": 10
            }
            
            start = time.time()
            with self.client.post(
                "/api/v1/search/hybrid",
                json=payload,
                catch_response=True,
                name="/search/hybrid [RRF]"
            ) as response:
                latency = (time.time() - start) * 1000
                metrics_collector.record_search(latency)
                
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 404:
                    response.failure("Endpoint not found")
                else:
                    response.failure(f"Error: {response.status_code}")
                    metrics_collector.record_error(f"search_{response.status_code}")
        
        @task(5)
        @tag("search", "hybrid", "reranking")
        def hybrid_search_with_reranking(self):
            """Hybrid search with Cross-Encoder reranking"""
            query = random.choice(SEARCH_QUERIES)
            payload = {
                "query_text": query,
                "search_types": ["vector", "keyword", "graph"],
                "fusion_method": "rrf",
                "reranker": "cross_encoder",
                "top_k": 10
            }
            
            start = time.time()
            with self.client.post(
                "/api/v1/search/hybrid",
                json=payload,
                catch_response=True,
                name="/search/hybrid [RRF+Rerank]"
            ) as response:
                latency = (time.time() - start) * 1000
                metrics_collector.record_search(latency)
                
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Error: {response.status_code}")
        
        @task(3)
        @tag("search", "vector")
        def vector_search_only(self):
            """Pure vector similarity search"""
            query = random.choice(SEARCH_QUERIES)
            payload = {
                "query_text": query,
                "search_types": ["vector"],
                "top_k": 10
            }
            
            with self.client.post(
                "/api/v1/search/vector",
                json=payload,
                catch_response=True,
                name="/search/vector"
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Error: {response.status_code}")
        
        @task(2)
        @tag("search", "keyword")
        def keyword_search_only(self):
            """BM25 keyword search"""
            query = random.choice(SEARCH_QUERIES)
            payload = {
                "query_text": query,
                "search_types": ["keyword"],
                "top_k": 10
            }
            
            with self.client.post(
                "/api/v1/search/keyword",
                json=payload,
                catch_response=True,
                name="/search/keyword [BM25]"
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Error: {response.status_code}")


    class GraphTraversalUser(HttpUser):
        """
        Tests multi-hop reasoning and graph traversal.
        
        Simulates users exploring legal hierarchies:
        - EU → Bundesrecht → Landesrecht → Kommunalrecht
        - Reference chains between regulations
        - Shortest path queries
        """
        weight = 20  # 20% of users
        wait_time = between(2, 5)
        
        @task(5)
        @tag("graph", "multi_hop")
        def multi_hop_traversal(self):
            """Multi-hop hierarchy traversal"""
            doc_id = random.choice(DOCUMENT_IDS)
            payload = {
                "document_id": doc_id,
                "direction": random.choice(["up", "down", "both"]),
                "max_depth": random.randint(2, 4)
            }
            
            start = time.time()
            with self.client.post(
                "/api/v1/graph/traverse",
                json=payload,
                catch_response=True,
                name="/graph/traverse [multi-hop]"
            ) as response:
                latency = (time.time() - start) * 1000
                metrics_collector.record_multi_hop(latency)
                
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Error: {response.status_code}")
        
        @task(3)
        @tag("graph", "context")
        def legal_context(self):
            """Get full legal context for a document"""
            doc_id = random.choice(DOCUMENT_IDS)
            
            with self.client.get(
                f"/api/v1/graph/context/{doc_id}",
                catch_response=True,
                name="/graph/context/{doc_id}"
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Error: {response.status_code}")
        
        @task(2)
        @tag("graph", "shortest_path")
        def shortest_path(self):
            """Find shortest path between two documents"""
            docs = random.sample(DOCUMENT_IDS, 2)
            payload = {
                "start_id": docs[0],
                "end_id": docs[1],
                "max_depth": 5
            }
            
            with self.client.post(
                "/api/v1/graph/shortest-path",
                json=payload,
                catch_response=True,
                name="/graph/shortest-path"
            ) as response:
                if response.status_code in [200, 404]:
                    response.success()
                else:
                    response.failure(f"Error: {response.status_code}")


    class SAGATransactionUser(HttpUser):
        """
        Tests SAGA transactions across multiple backends.
        
        Simulates write operations that span:
        - PostgreSQL (relational data)
        - Neo4j (graph relationships)
        - ChromaDB (vectors)
        - CouchDB (documents)
        """
        weight = 15  # 15% of users
        wait_time = between(3, 8)
        
        @task(3)
        @tag("saga", "write")
        def create_document_saga(self):
            """Create document with SAGA transaction"""
            payload = {
                "documents": [
                    {
                        **DOCUMENT_CONTENT,
                        "document_id": f"load_test_{random.randint(10000, 99999)}"
                    }
                ],
                "backends": ["postgresql", "neo4j", "chromadb"]
            }
            
            start = time.time()
            with self.client.post(
                "/api/v1/saga/documents",
                json=payload,
                catch_response=True,
                name="/saga/documents [CREATE]"
            ) as response:
                latency = (time.time() - start) * 1000
                metrics_collector.record_saga(latency)
                
                if response.status_code in [200, 201]:
                    response.success()
                else:
                    response.failure(f"Error: {response.status_code}")
        
        @task(2)
        @tag("saga", "update")
        def update_document_saga(self):
            """Update document with SAGA transaction"""
            doc_id = random.choice(DOCUMENT_IDS)
            payload = {
                "document_id": doc_id,
                "updates": {
                    "content": f"Updated content at {time.time()}",
                    "metadata": {"updated_by": "load_test"}
                },
                "backends": ["postgresql", "neo4j"]
            }
            
            with self.client.put(
                f"/api/v1/saga/documents/{doc_id}",
                json=payload,
                catch_response=True,
                name="/saga/documents/{id} [UPDATE]"
            ) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 404:
                    response.success()  # Expected for test documents
                else:
                    response.failure(f"Error: {response.status_code}")


    class MixedWorkloadUser(HttpUser):
        """
        Simulates realistic production traffic mix.
        
        Combines:
        - Search operations (70%)
        - Graph queries (15%)
        - Write operations (10%)
        - Administrative operations (5%)
        """
        weight = 15  # 15% of users
        wait_time = between(1, 5)
        
        @task(7)
        @tag("mixed", "search")
        def mixed_search(self):
            """Various search operations"""
            search_type = random.choice(["hybrid", "vector", "keyword"])
            query = random.choice(SEARCH_QUERIES)
            
            payload = {
                "query_text": query,
                "search_types": [search_type] if search_type != "hybrid" else ["vector", "keyword", "graph"],
                "fusion_method": "rrf" if search_type == "hybrid" else None,
                "top_k": random.choice([5, 10, 20])
            }
            
            with self.client.post(
                f"/api/v1/search/{search_type}",
                json=payload,
                catch_response=True,
                name=f"/search/{search_type} [mixed]"
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Error: {response.status_code}")
        
        @task(2)
        @tag("mixed", "read")
        def get_document(self):
            """Read single document"""
            doc_id = random.choice(DOCUMENT_IDS)
            
            with self.client.get(
                f"/api/v1/documents/{doc_id}",
                catch_response=True,
                name="/documents/{id}"
            ) as response:
                if response.status_code in [200, 404]:
                    response.success()
                else:
                    response.failure(f"Error: {response.status_code}")
        
        @task(1)
        @tag("mixed", "admin")
        def health_check(self):
            """Health check endpoint"""
            with self.client.get(
                "/api/v1/health",
                catch_response=True,
                name="/health"
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Health check failed: {response.status_code}")


# ============================================================================
# Event Handlers
# ============================================================================

if LOCUST_AVAILABLE:
    @events.test_stop.add_listener
    def on_test_stop(environment, **kwargs):
        """Print metrics summary when test stops"""
        summary = metrics_collector.get_summary()
        print("\n" + "=" * 60)
        print("VCC-UDS3 Load Test Summary")
        print("=" * 60)
        print(f"\nSearch Performance:")
        print(f"  Total Requests: {summary['search']['count']}")
        print(f"  p50 Latency: {summary['search']['p50_ms']:.1f}ms")
        print(f"  p95 Latency: {summary['search']['p95_ms']:.1f}ms")
        print(f"  p99 Latency: {summary['search']['p99_ms']:.1f}ms")
        print(f"  Average: {summary['search']['avg_ms']:.1f}ms")
        
        print(f"\nSAGA Transactions:")
        print(f"  Total: {summary['saga']['count']}")
        print(f"  p95 Latency: {summary['saga']['p95_ms']:.1f}ms")
        
        print(f"\nMulti-Hop Traversals:")
        print(f"  Total: {summary['multi_hop']['count']}")
        print(f"  p95 Latency: {summary['multi_hop']['p95_ms']:.1f}ms")
        
        if summary['errors']:
            print(f"\nErrors:")
            for error_type, count in summary['errors'].items():
                print(f"  {error_type}: {count}")
        
        print("=" * 60 + "\n")


# ============================================================================
# CLI for standalone testing
# ============================================================================

if __name__ == "__main__":
    if not LOCUST_AVAILABLE:
        print("❌ Locust not installed. Install with: pip install locust")
        print("\nTo run load tests:")
        print("  pip install locust")
        print("  locust -f monitoring/locustfile.py --host=http://localhost:8000")
    else:
        print("✅ Locust available")
        print("\nRun load tests with:")
        print("  locust -f monitoring/locustfile.py --host=http://localhost:8000")
        print("\nOr run headless:")
        print("  locust -f monitoring/locustfile.py --headless -u 100 -r 10 -t 10m --host=http://localhost:8000")
