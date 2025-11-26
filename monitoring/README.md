# VCC-UDS3 Monitoring & Load Testing

Production-grade monitoring and load testing infrastructure for UDS3 (v1.6.0).

## Overview

This directory contains:

- **Grafana Dashboards** - Pre-configured dashboards for KPI monitoring
- **Prometheus Configuration** - Scrape targets and alert rules
- **Locust Load Tests** - Distributed load testing framework

All components are designed for **on-premise deployment** with no cloud dependencies.

## Components

### 1. Grafana Dashboards (`grafana_dashboards.json`)

Four pre-built dashboards:

| Dashboard | UID | Purpose |
|-----------|-----|---------|
| **Executive Overview** | `uds3-executive` | High-level KPIs for stakeholders |
| **Operations** | `uds3-operations` | Detailed metrics for DevOps/SRE |
| **Security** | `uds3-security` | Security and compliance monitoring |
| **RAG Pipeline** | `uds3-rag` | v1.6.0 RAG performance metrics |

#### Key Metrics Tracked

- **Search Latency** (p50, p95, p99)
- **SAGA Completion Rate** (target: >99.9%)
- **Error Rates** by type
- **Database Connection Pools**
- **Cache Hit Rates**
- **Cross-Encoder Reranking Performance**
- **Multi-Hop Traversal Depth**
- **Recall@10 / NDCG@10** (retrieval quality)

#### Import to Grafana

```bash
# Via Grafana API
curl -X POST -H "Content-Type: application/json" \
  -d @grafana_dashboards.json \
  http://admin:admin@localhost:3000/api/dashboards/import

# Or use Grafana UI: Dashboards → Import → Upload JSON
```

### 2. Prometheus Configuration (`prometheus.yml`)

Complete scrape configuration for UDS3 components:

```yaml
scrape_configs:
  - job_name: 'uds3'           # Main API metrics
  - job_name: 'uds3-search'    # Search-specific metrics
  - job_name: 'postgresql'     # PostgreSQL exporter
  - job_name: 'neo4j'          # Neo4j metrics
  - job_name: 'couchdb'        # CouchDB exporter
  - job_name: 'node'           # Host metrics
  - job_name: 'kubernetes-nodes' # K8s metrics (on-premise)
```

#### Deploy

```bash
# Copy to Prometheus config directory
cp prometheus.yml /etc/prometheus/prometheus.yml
cp prometheus_alerts.yml /etc/prometheus/rules/uds3_alerts.yml

# Reload Prometheus
curl -X POST http://localhost:9090/-/reload
```

### 3. Alert Rules (`prometheus_alerts.yml`)

Pre-configured alerts aligned with KPIs from ENTWICKLUNGSSTRATEGIE.md:

| Alert | Threshold | Severity |
|-------|-----------|----------|
| `UDS3SearchLatencyWarning` | p95 > 100ms | warning |
| `UDS3SearchLatencyCritical` | p95 > 200ms | critical |
| `UDS3SAGACompletionRateLow` | < 99.9% | warning |
| `UDS3HighErrorRate` | > 1% | warning |
| `UDS3DatabaseDown` | down 1m | critical |
| `UDS3CertificateExpirySoon` | < 30 days | warning |
| `UDS3RerankerLatencyHigh` | p95 > 500ms | warning |
| `UDS3RetrievalQualityDrop` | Recall@10 < 90% | warning |

### 4. Load Testing (`locustfile.py`)

Locust-based distributed load testing framework.

#### Test Users

| User Class | Weight | Description |
|------------|--------|-------------|
| `HybridSearchUser` | 50% | Full RAG pipeline testing |
| `GraphTraversalUser` | 20% | Multi-hop reasoning tests |
| `SAGATransactionUser` | 15% | Cross-database transactions |
| `MixedWorkloadUser` | 15% | Realistic traffic mix |

#### Run Load Tests

```bash
# Install Locust
pip install locust

# Interactive mode (web UI at http://localhost:8089)
locust -f locustfile.py --host=http://uds3-api:8000

# Headless mode (10 users, 10 minute test)
locust -f locustfile.py --headless -u 10 -r 2 -t 10m \
  --host=http://uds3-api:8000

# Distributed mode (for high load)
# Master:
locust -f locustfile.py --master --host=http://uds3-api:8000
# Workers (run on multiple machines):
locust -f locustfile.py --worker --master-host=locust-master
```

#### Test Scenarios

```bash
# 10 concurrent users (development)
locust -f locustfile.py --headless -u 10 -r 2 -t 5m --host=http://localhost:8000

# 100 concurrent users (staging)
locust -f locustfile.py --headless -u 100 -r 10 -t 15m --host=http://uds3-staging:8000

# 1000 concurrent users (production capacity test)
locust -f locustfile.py --headless -u 1000 -r 50 -t 30m \
  --master --expect-workers=5 --host=http://uds3-prod:8000
```

## KPI Targets (v1.6.0)

| Metric | Target | Dashboard |
|--------|--------|-----------|
| retrieval_latency_ms (p95) | < 100ms | Executive, Operations |
| saga_completion_rate | > 99.9% | Executive, Operations |
| service_availability | > 99.9% | Executive |
| Recall@10 | > 95% | RAG Pipeline |
| NDCG@10 | > 0.85 | RAG Pipeline |
| Error Rate | < 1% | Executive, Operations |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    On-Premise Infrastructure                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌─────────────┐    ┌───────────────────┐   │
│  │  UDS3    │───▶│  Prometheus │───▶│     Grafana       │   │
│  │  API     │    │  (metrics)  │    │   (dashboards)    │   │
│  │ :9090    │    │   :9090     │    │     :3000         │   │
│  └──────────┘    └─────────────┘    └───────────────────┘   │
│       │                │                     │               │
│       │         ┌──────┴──────┐              │               │
│       │         │             │              │               │
│       │    ┌────┴────┐  ┌─────┴─────┐       │               │
│       │    │ Alert   │  │ Recording │       │               │
│       │    │ Manager │  │   Rules   │       │               │
│       │    └─────────┘  └───────────┘       │               │
│       │                                      │               │
│  ┌────┴─────────────────────────────────────┴────┐          │
│  │               Locust Load Testing              │          │
│  │            (distributed workers)               │          │
│  └────────────────────────────────────────────────┘          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Start Prometheus (with UDS3 config)
docker run -d --name prometheus \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v $(pwd)/prometheus_alerts.yml:/etc/prometheus/rules/uds3_alerts.yml \
  -p 9090:9090 \
  prom/prometheus

# 2. Start Grafana
docker run -d --name grafana \
  -p 3000:3000 \
  grafana/grafana

# 3. Import dashboards
# Access Grafana at http://localhost:3000 (admin/admin)
# Import grafana_dashboards.json

# 4. Run load tests
pip install locust
locust -f locustfile.py --host=http://localhost:8000
```

## Files

```
monitoring/
├── README.md                  # This file
├── grafana_dashboards.json    # Grafana dashboard definitions
├── prometheus.yml             # Prometheus scrape configuration
├── prometheus_alerts.yml      # Alert rules
└── locustfile.py              # Locust load testing framework
```

## References

- [ENTWICKLUNGSSTRATEGIE.md](../ENTWICKLUNGSSTRATEGIE.md) - KPI definitions
- [core/metrics.py](../core/metrics.py) - Prometheus metrics module
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Locust Documentation](https://docs.locust.io/)

---

Part of UDS3 (Unified Database Strategy v3)  
Repository: https://github.com/makr-code/VCC-UDS3
