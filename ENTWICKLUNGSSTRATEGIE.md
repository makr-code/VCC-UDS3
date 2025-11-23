# VCC-UDS3 Weiterentwicklungsstrategie
# Development Strategy for VCC-UDS3

**Version:** 1.0  
**Datum:** 23. November 2025  
**Status:** Draft  
**Autor:** VCC Development Team

---

## Executive Summary

Dieses Dokument definiert die strategische Weiterentwicklung des **VCC-UDS3 (Unified Database Strategy v3.0)** als zentrales Rückgrat des VCC-Ökosystems (Veritas-Covina-Clara). Die Strategie adressiert die Tatsache, dass UDS3 derzeit nicht vollständig final umgesetzt ist, und legt einen klaren Weg zur Produktionsreife gemäß Stand der Technik und Best Practices fest.

### Kernziele

1. **Technische Exzellenz:** Schließung der Lücke zu Hyperscaler-Lösungen bei Wahrung digitaler Souveränität
2. **VCC-Integration:** Nahtlose Integration aller VCC-Komponenten (Veritas, Covina, Clara)
3. **Skalierbarkeit:** Enterprise-Grade Skalierung für Behörden auf Landes- und Bundesebene
4. **Compliance:** Vollständige EU AI Act, DSGVO und eIDAS Konformität
5. **Innovation:** State-of-the-art RAG-Pipeline, Continuous Learning, Process-native AI

---

## 1. Situationsanalyse

### 1.1 Aktueller Stand (v1.5.0)

**✅ Erreichte Meilensteine:**

- **Backend-Infrastruktur:** Alle 4 Datenbanken produktionsreif (PostgreSQL, Neo4j, ChromaDB, CouchDB)
- **Sicherheitsarchitektur:** PKI-integrierte RBAC/RLS mit vollständigem Audit-Logging
- **Search API:** Vector, Graph und Hybrid-Search implementiert
- **SAGA Pattern:** Distributed Transactions mit automatischer Kompensation
- **DSGVO-Compliance:** PII-Tracking, Anonymisierung, Retention Policies
- **Python Package:** Installierbar via pip, CLI-Interface vorhanden

**⚠️ Identifizierte Gaps:**

| Bereich | Gap | Impact | Priorität |
|---------|-----|--------|-----------|
| **RAG-Pipeline** | Keine Cross-Encoder Reranking | Suboptimale Suchergebnisse | Hoch |
| **Monitoring** | Kein Prometheus/Grafana | Fehlende Observability | Kritisch |
| **Hochverfügbarkeit** | Single-Instance Deployment | SPOF-Risiko | Kritisch |
| **Clara Integration** | Kein PEFT/LoRA Training | Kein Continuous Learning | Mittel |
| **VPB Integration** | Limitierte Process-Awareness | Suboptimale Prozess-KI | Mittel |
| **Load Testing** | Nicht durchgeführt | Unbekannte Skalierungsgrenzen | Hoch |

### 1.2 Vergleich: VCC vs. Hyperscaler

| Komponente | VCC (UDS3) | AWS/Azure/GCP | Handlungsbedarf |
|------------|------------|---------------|-----------------|
| **Retrieval** | Pure Vector Search | Native Hybrid (Keyword+Vector) | v1.6.0 |
| **Fusion** | Score Normalization | Reciprocal Rank Fusion (RRF) | v1.6.0 |
| **Reranking** | Generic LLM | Specialized Cross-Encoder | v1.6.0 |
| **Multi-hop** | Basic Graph Traversal | Optimized Knowledge Graph | v2.0.0 |
| **Monitoring** | Basic Logging | Prometheus/Grafana | v1.6.0 |
| **HA** | Single Instance | Auto-Scaling, Managed Services | v3.0.0 |
| **Security** | PKI, RBAC, RLS | Hyperscaler + Compliance | ✅ Par |

**Strategische Entscheidung:** Souveränitätswahrende Eigenentwicklung bei systematischer Aufholung technischer Lücken.

---

## 2. Strategische Säulen

### 2.1 Technologische Exzellenz

#### 2.1.1 RAG-Pipeline Maturity (v1.6.0 - Q1 2026)

**Ziel:** Schließung der Lücke zu Hyperscaler-Retrieval-Qualität

**Maßnahmen:**

1. **Hybrid Search Implementation**
   - Native Keyword Search (BM25) parallel zu Vector Search
   - Query Understanding für strukturierte Queries (§-Referenzen)
   - Dual Index (Vector + Inverted Index) mit Synchronisation
   - **KPI:** Recall@10 > 95% für Paragraphen-Referenzen

2. **Reciprocal Rank Fusion (RRF)**
   - Industry-Standard Rank-Fusion Algorithm (k=60)
   - Multi-Source Fusion (Neo4j Graph + ChromaDB Vector)
   - Adaptive Gewichtung basierend auf Query-Typ
   - **KPI:** NDCG@10 > 0.85

3. **Specialized Re-Ranking (Cross-Encoder)**
   - Fine-tuned Cross-Encoder Model (German BERT)
   - Two-Stage Retrieval (Bi-Encoder → Cross-Encoder)
   - ONNX-optimierter Inference-Service
   - **KPI:** MRR > 0.90, Latenz < 50ms (100 candidates)

4. **Multi-Hop Reasoning Enhancement**
   - Cypher Query Templates für Rechtshierarchien
   - Adaptive Traversierungstiefe
   - Path Scoring nach Relevanz
   - **KPI:** Korrekte Hierarchie-Traversierung in 95% der Fälle

**Technischer Ansatz:**
```python
# Erweiterte Search API (v1.6.0)
results = await strategy.search_api.hybrid_search(
    query="§ 58 LBO BW Abstandsflächen",
    search_types=["vector", "keyword", "graph"],
    fusion_method="rrf",  # Reciprocal Rank Fusion
    reranker="cross_encoder",
    weights={"vector": 0.4, "keyword": 0.3, "graph": 0.3},
    top_k=10
)
```

#### 2.1.2 Operational Excellence (RAGOps) (v1.6.0 - Q1 2026)

**Ziel:** Production-Grade Monitoring und Reliability

**Maßnahmen:**

1. **Automated Performance Monitoring**
   - Prometheus Metrics Export (retrieval_latency_ms, saga_completion_rate, model_accuracy)
   - Grafana Dashboards (Executive, Operations, Security)
   - AlertManager für SLA-Verletzungen
   - **KPI:** retrieval_latency_ms < 100ms (p95), saga_completion_rate > 99.9%

2. **Load Testing Framework**
   - Locust-basierte distributed Load Generation
   - Test Scenarios: Read-heavy, Write-heavy, Mixed Workload
   - Capacity Planning mit empirischen Skalierungskurven
   - **Deliverable:** Load Test Reports (10, 100, 1000 concurrent users)

3. **Backup & Recovery**
   - Automatisierte Daily Incremental + Weekly Full Backups
   - SAGA-aware Backup-Koordination (Cross-DB Consistency)
   - Disaster Recovery Plans (RTO < 4h, RPO < 15min)
   - **Deliverable:** Quarterly DR-Drills

4. **Comprehensive Logging**
   - ELK Stack (Elasticsearch, Logstash, Kibana)
   - Correlation IDs für Request-Tracing
   - Structured Logging (JSON Format)
   - **KPI:** 100% Request Traceability

#### 2.1.3 Continuous Learning Architecture (v2.0.0 - Q2-Q3 2026)

**Ziel:** Clara-Integration für selbstlernende Verwaltungs-KI

**Maßnahmen:**

1. **Parameter-Efficient Fine-Tuning (PEFT)**
   - LoRA/QLoRA Adapter Management (Versionierung, Storage, Loading)
   - Training Pipeline: Feedback → Validation → Training → Deployment
   - Resource Efficiency (< 5% zusätzlicher GPU-RAM)
   - **KPI:** Training Time < 2h, Accuracy +2% on Golden Dataset

2. **Golden Dataset Validation**
   - 1000 Expert-Validated Question-Answer-Pairs
   - Automatisierte Pre-Deployment Validierung
   - Regression Detection (Alert bei Accuracy-Drop > 5%)
   - **Metriken:** Accuracy, F1-Score, BLEU, Latency

3. **Feedback Loop Integration (Veritas → Clara)**
   - Feedback Capture in Veritas UI (Thumbs-Up/Down + Kommentare)
   - Anonymisierte Data Pipeline (PostgreSQL → Training Queue)
   - Human-in-the-Loop Expert Review für kritische Fälle
   - **DSGVO:** Pseudonymisierung, Opt-Out

4. **Just-in-Time Integrity Verification**
   - Digitale Signatur aller LoRA-Adapter (PKI Private Key)
   - Runtime-Verification vor GPU-Loading
   - Revocation List für kompromittierte Adapter
   - **KPI:** Verification Overhead < 10ms, Zero False Positives

**Technischer Ansatz:**
```python
# Clara Training Loop
veritas_feedback = saga_crud.read_feedback(filters={"validated": True})
quality_checked = covina.validate_data_quality(veritas_feedback)
adapter = clara.train_lora_adapter(quality_checked, base_model="llama-3-70b")
accuracy = clara.evaluate_on_golden_dataset(adapter)

if accuracy > 0.90:
    adapter_bytes = adapter.to_bytes()
    signature = pki.sign(adapter_bytes, private_key)
    couchdb.store_adapter(adapter_id, adapter_bytes, signature)
    clara.deploy_adapter(adapter_id)  # Zero-downtime swap
else:
    logger.warning(f"Adapter accuracy {accuracy} below threshold, not deployed")
```

### 2.2 VCC-Ökosystem Integration

#### 2.2.1 VPB Integration (Verwaltungsprozess-Backbone) (v2.0.0 - Q2-Q3 2026)

**Ziel:** Prozess-native KI durch tiefe VPB-Integration

**Maßnahmen:**

1. **Process-Aware Queries**
   - Process Context Injection in Search Queries
   - BPMN-Integration (Import von Covina-Prozessmodellen)
   - Stage-Specific Retrieval (Anpassung an Prozessphase)
   - **Use Case:** "Erforderliche Unterlagen Baugenehmigung" → filtert auf Checklisten-Dokumente

2. **Multi-Hop Reasoning (Cross-Entity Logical Paths)**
   - Query Planner für automatische Cypher-Generierung
   - Result Synthesis (LLM aggregiert Pfade zu kohärenter Antwort)
   - **Beispiel:** "Welche Genehmigungen für Photovoltaik auf denkmalgeschütztem Gebäude?"

3. **Legal Hierarchy Navigation**
   - Hierarchy Indexing (Vorbefüllte Pfade: BauGB → LBO BW → Gemeindesatzung)
   - Conflict Resolution (Automatische Erkennung widersprüchlicher Regelungen)
   - **KPI:** Korrekte Hierarchie-Traversierung in 95% der Fälle

4. **Actor & Entity Modeling (Verwaltungsakt Networks)**
   - Entity Recognition (NER-Modelle)
   - Relationship Mining (Pattern-basiert)
   - Graph Enrichment durch Covina
   - **Use Case:** "Alle offenen Anträge von Antragsteller X mit fehlenden Gutachten"

**Technischer Ansatz:**
```cypher
// Legal Hierarchy Query
MATCH path = (building:Building {heritage_protected: true})
  -[:REQUIRES_PERMIT]->(:BuildingModification {type: "solar_panel"})
  -[:GOVERNED_BY]->(law:Law)
  -[:DELEGATES_TO*1..2]->(regulation:Regulation)
WHERE regulation.jurisdiction = building.jurisdiction
RETURN path, law.name, regulation.name
```

#### 2.2.2 Veritas Integration Enhancement (v1.6.0 - Q1 2026)

**Status Quo:** Veritas nutzt UDS3 für RAG-Retrieval (Neo4j + ChromaDB + PostgreSQL)

**Verbesserungen:**

1. **Optimierte Query Patterns**
   - Vordefinierte Query Templates für häufige Veritas-Anfragen
   - Caching-Layer für wiederholte Rechtsfragen
   - **KPI:** Latenz-Reduktion 30% für cached Queries

2. **Enhanced Source References**
   - Präzise Paragraph-Zitation mit Versionsinformation
   - Link zu Original-Dokumenten in CouchDB
   - **User Value:** Nachvollziehbare Rechtsgrundlagen

3. **Feedback-Qualität**
   - Strukturierte Feedback-Erfassung (Relevanz, Korrektheit, Vollständigkeit)
   - Automatische Priorisierung für Clara-Training
   - **KPI:** 80% Feedback-Rate auf Veritas-Antworten

#### 2.2.3 Covina Integration (v2.0.0 - Q2-Q3 2026)

**Ziel:** Bidirektionale Integration für Knowledge Update und Process Mining

**Maßnahmen:**

1. **Automated Knowledge Ingestion**
   - Worker-basierte Pipeline (Asynchronous Processing)
   - SAGA-Kompensation für fehlerhafte Importe
   - **GDPR:** Automatische Pseudonymisierung
   - **KPI:** < 24h von Covina-Daten bis UDS3-Verfügbarkeit

2. **Process Mining Data Export**
   - Neo4j Process Graphs für Covina-Analysen
   - PostgreSQL Event Logs für Performance-Metriken
   - **Use Case:** Bottleneck-Detection in Genehmigungsverfahren

3. **Quality Control Integration**
   - Pre-Ingestion Data Quality Checks
   - Anomaly Detection (statistische Ausreißer)
   - **Mitigation:** Bias Amplification Prevention

### 2.3 Governance & Compliance

#### 2.3.1 Formal Data Governance (v2.5.0 - Q4 2026)

**Ziel:** Strukturierte Data Governance für Behördenumfeld

**Deliverables:**

1. **Data Classification Schema**
   - 4 Stufen: Öffentlich, Intern, Vertraulich, Geheim
   - Automatische Klassifizierung basierend auf PII-Detection
   - **Compliance:** BSI IT-Grundschutz

2. **Retention Policies**
   - Automatische Löschfristen (DSGVO Art. 5 Abs. 1 lit. e)
   - Aufbewahrungsfristen nach Fachrecht (z.B. Bauakten: 10 Jahre)
   - **Implementation:** Scheduled Jobs in PostgreSQL

3. **Data Lineage**
   - Nachvollziehbarkeit aller Datenflüsse (Covina → UDS3 → Veritas)
   - Visualisierung in Grafana
   - **Compliance:** DPIA-Anforderungen

4. **Dokumentation**
   - Written Policies (Board-approved)
   - Data Protection Impact Assessment (DPIA)
   - Data Processing Register (Verzeichnis von Verarbeitungstätigkeiten)

#### 2.3.2 EU AI Act Compliance (v2.5.0 - Q4 2026)

**Status:** UDS3 als Teil eines High-Risk AI Systems (Verwaltungs-KI)

**Anforderungen & Maßnahmen:**

1. **Robustheit (Art. 15 AI Act)**
   - ✅ SAGA-Kompensation (bereits implementiert)
   - ✅ Fehlertoleranz (Retry Logic, Graceful Degradation)
   - [ ] Adversarial Testing (v2.5.0)

2. **Transparenz (Art. 13 AI Act)**
   - ✅ Lückenlose Protokollierung (Audit Logs)
   - [ ] Explainability für AI-Entscheidungen (v2.0.0 - Clara Integration)
   - [ ] Public Documentation (Technical Documentation gemäß Art. 11)

3. **Menschliche Aufsicht (Art. 14 AI Act)**
   - ✅ Human-in-the-Loop in Veritas (bereits implementiert)
   - [ ] Override-Mechanismen für KI-Entscheidungen (v2.0.0)
   - [ ] Eskalationspfade für kritische Fälle

4. **Bias-Monitoring (Art. 10 AI Act)**
   - [ ] Kontinuierliche Metriken (Gender, Alter, Herkunft) (v2.5.0)
   - [ ] AI Ethics Committee Integration (v2.5.0)
   - [ ] Bias-Audits (Quarterly)

5. **Conformity Assessment (Art. 43 AI Act)**
   - [ ] Externe Zertifizierung durch Notified Body (v3.0.0)
   - [ ] Quality Management System (Art. 17)
   - [ ] Risk Management System (Art. 9)

**Deliverables:**

- Technical Documentation (Art. 11 AI Act)
- Risk Management System (Art. 9)
- Quality Management System (Art. 17)
- Conformity Assessment Report

#### 2.3.3 RBAC Matrix Enhancement (v2.5.0 - Q4 2026)

**Ziel:** Detaillierte Rollendokumentation und Governance

**Maßnahmen:**

1. **Role Assignment Guidelines**
   - Dokumentierte Zuweisungskriterien pro Rolle
   - Approval-Workflow für kritische Rollen (ADMIN, SYSTEM)
   - **Compliance:** Least-Privilege-Prinzip

2. **Quarterly Access Reviews**
   - Automatisierte Reports über Rollenzuweisungen
   - Manuelle Review durch Security Officer
   - **KPI:** 100% Rollen-Review-Coverage

3. **Permission Matrix Documentation**
   - Erweiterte Matrix mit Beispiel-Use-Cases
   - Risikobewertung pro Permission
   - **Deliverable:** `docs/RBAC_PERMISSION_MATRIX.md`

### 2.4 Production Readiness

#### 2.4.1 Kubernetes Deployment (v3.0.0 - 2027+)

**Ziel:** Enterprise-Grade Orchestrierung für Skalierung und HA

**Komponenten:**

1. **Helm Charts**
   - Templated Deployments für alle Services
   - ConfigMaps/Secrets für externalisierte Konfiguration
   - **Repository:** `charts/uds3/`

2. **Auto-Scaling**
   - Horizontal Pod Autoscaler (HPA) basierend auf CPU/Memory/Custom Metrics
   - Cluster Autoscaler für Node-Pool-Anpassung
   - **KPI:** Auto-Scale Reaktionszeit < 2min

3. **Rolling Updates**
   - Zero-Downtime Deployments
   - Canary Deployments für risikoreiche Updates
   - **KPI:** 99.95% Availability während Updates

4. **Cluster Setup**
   - Multi-Zone für High Availability
   - Dedicated Node Pools (Compute, Storage, GPU)
   - Ingress Controller (NGINX) mit TLS Termination

**Technischer Ansatz:**
```yaml
# Helm Values (values.yaml)
uds3:
  replicaCount: 3
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 20
    targetCPUUtilizationPercentage: 70
  
  databases:
    postgresql:
      replicaCount: 3
      patroni:
        enabled: true
    neo4j:
      causalClustering:
        coreMembers: 3
        readReplicas: 2
```

#### 2.4.2 High Availability (Database Clustering) (v3.0.0 - 2027+)

**Ziel:** Redundante Database-Infrastruktur

**PostgreSQL:**
- Patroni Cluster (3-Node Setup: Leader + 2 Replicas)
- Automatic Failover (< 30s RTO)
- PgBouncer Connection Pooling

**Neo4j:**
- Causal Clustering (3 Core Members + Read Replicas)
- Driver-Level Load Balancing
- Incremental Backups to S3-Compatible Storage

**ChromaDB:**
- Sharding (Horizontal Partitioning by Collection)
- 2x Redundancy
- Distributed Queries (Scatter-Gather Pattern)

**CouchDB:**
- Multi-Master Replication (3-Node Cluster)
- Application-Level Conflict Resolution
- Continuous Replication to Cold Storage

**KPI:** 99.95% Service Availability, RTO < 4h, RPO < 15min

#### 2.4.3 Security Hardening (v2.0.0 - Q2-Q3 2026)

**Ziel:** Zero-Trust Architecture Completion

**Maßnahmen:**

1. **mTLS Everywhere**
   - Alle Service-to-Service Kommunikation verschlüsselt + authentifiziert
   - Automatisierte Certificate Rotation (Cert-Manager)
   - Kubernetes NetworkPolicies für Segmentierung
   - **KPI:** 100% mTLS Coverage

2. **Just-in-Time Adapter Validation**
   - Siehe Clara-Sektion (bereits beschrieben)

3. **Cascading Integrity Protection (Anti-Poisoning)**
   - Multi-Source Validation von Feedback
   - Anomaly Detection (Z-Score > 3)
   - Expert-Review Queue für verdächtige Feedback-Muster

4. **Qualified Electronic Timestamps (QET)**
   - TSA Integration für qualifizierte Zeitstempel
   - Periodic Hashing (SAGA Log → Timestamping täglich)
   - Verification Endpoint für historische Log-Integrität
   - **Compliance:** eIDAS-konform, Beweiskraft im Gerichtsverfahren

#### 2.4.4 Independent Security Audit (v3.0.0 - 2027+)

**Scope:**

1. **Penetration Testing (External)**
   - OWASP Top 10 Validierung
   - Network Perimeter Testing
   - Social Engineering Assessment

2. **Code Audit**
   - Static Code Analysis (SAST)
   - Dynamic Application Security Testing (DAST)
   - Dependency Vulnerability Scanning

3. **Architecture Review**
   - Zero-Trust Validation
   - Threat Modeling (STRIDE Framework)
   - Compliance Check (DSGVO, AI Act, BSI IT-Grundschutz)

**Deliverables:**

- Audit Report with Findings (Kritisch, Hoch, Mittel, Niedrig)
- Remediation Roadmap mit Priorisierung
- Re-Audit after Fixes (Final Certification)

**Certification Targets:**

- ISO 27001 (Information Security Management)
- SOC 2 Type II (Service Organization Control)
- BSI C5 (Cloud Computing Compliance Controls Catalogue)

---

## 3. Roadmap & Timeline

### 3.1 Phasen-Übersicht

```
Q4 2025         Q1 2026         Q2 2026         Q3 2026         Q4 2026         2027+
   │               │               │               │               │               │
   ▼               ▼               ▼               ▼               ▼               ▼
v1.5.0         v1.6.0         v2.0.0         v2.0.0         v2.5.0         v3.0.0
  GA         RAG Maturity    Clara PEFT     VPB Integ.    Governance     Production
   │           RAGOps         JIT Verify     Complete       EU AI Act      Security
   │         Monitoring       Feedback                     Data Gov        K8s HA
   │         Load Test                                     RBAC Matrix     Audit
```

### 3.2 Detaillierter Zeitplan

#### Phase 1: v1.6.0 - RAG-Pipeline Maturity (Q1 2026)

**Dauer:** 12 Wochen  
**Team:** 4 FTE (2 Backend, 1 ML, 1 DevOps)

| Woche | Deliverable | Owner |
|-------|------------|-------|
| 1-3 | Hybrid Search (BM25 + Vector) | Backend |
| 4-5 | RRF Implementation | ML |
| 6-8 | Cross-Encoder Reranking | ML |
| 9-10 | Multi-Hop Reasoning Enhancement | Backend |
| 11 | Prometheus/Grafana Setup | DevOps |
| 12 | Load Testing & Report | DevOps |

**Akzeptanzkriterien:**

- ✅ Recall@10 > 95% auf Testdatensatz
- ✅ NDCG@10 > 0.85
- ✅ MRR > 0.90
- ✅ Monitoring Dashboards operational
- ✅ Load Test Report (10, 100, 1000 users)

#### Phase 2: v2.0.0 - Continuous Learning (Q2-Q3 2026)

**Dauer:** 24 Wochen  
**Team:** 6 FTE (2 Backend, 2 ML, 1 Security, 1 DevOps)

| Woche | Deliverable | Owner |
|-------|------------|-------|
| 1-4 | PEFT/LoRA Infrastructure | ML |
| 5-8 | Golden Dataset Creation (1000 Pairs) | ML |
| 9-12 | Feedback Loop (Veritas → Clara) | Backend |
| 13-16 | JIT Integrity Verification | Security |
| 17-20 | VPB Process-Aware Queries | Backend |
| 21-22 | Multi-Hop Reasoning (Graph) | Backend |
| 23-24 | Integration Testing & Validation | All |

**Akzeptanzkriterien:**

- ✅ LoRA Adapter Training < 2h
- ✅ Model Accuracy +2% on Golden Dataset
- ✅ JIT Verification < 10ms overhead
- ✅ Process-Aware Queries functional
- ✅ Veritas → Clara Feedback Loop operational

#### Phase 3: v2.5.0 - Governance & Compliance (Q4 2026)

**Dauer:** 12 Wochen  
**Team:** 5 FTE (1 Backend, 1 Compliance, 1 Legal, 1 Security, 1 PM)

| Woche | Deliverable | Owner |
|-------|------------|-------|
| 1-2 | Data Classification Schema | Compliance |
| 3-4 | Retention Policies Implementation | Backend |
| 5-6 | Data Lineage Tracking | Backend |
| 7-8 | EU AI Act Documentation | Legal |
| 9-10 | Bias Monitoring System | ML/Security |
| 11-12 | AI Ethics Committee Setup | PM |

**Akzeptanzkriterien:**

- ✅ Data Classification operational
- ✅ Automatic Retention Enforcement
- ✅ EU AI Act Technical Documentation complete
- ✅ Bias Metrics Dashboard
- ✅ AI Ethics Committee established

#### Phase 4: v3.0.0 - Production Readiness (2027+)

**Dauer:** 26 Wochen  
**Team:** 7 FTE (2 Backend, 1 Security, 2 DevOps, 1 QA, 1 PM)

| Woche | Deliverable | Owner |
|-------|------------|-------|
| 1-4 | Helm Charts Development | DevOps |
| 5-8 | PostgreSQL Patroni Setup | DevOps |
| 9-12 | Neo4j Causal Clustering | DevOps |
| 13-16 | ChromaDB/CouchDB HA | DevOps |
| 17-18 | Performance Benchmarks | QA |
| 19-22 | Independent Security Audit | Security |
| 23-24 | Remediation | All |
| 25-26 | Final Certification | PM |

**Akzeptanzkriterien:**

- ✅ Kubernetes Deployment operational
- ✅ All Databases in HA mode
- ✅ 99.95% Availability achieved
- ✅ Security Audit passed
- ✅ ISO 27001 / SOC 2 Certification obtained

### 3.3 Dependency Management

**Kritische Abhängigkeiten:**

- v2.0.0 Clara requires v1.6.0 Monitoring (für Feedback-Metrics)
- v3.0.0 K8s requires v2.5.0 Monitoring (für Auto-Scaling)
- v2.0.0 VPB requires Covina Process Mining (external dependency)
- v3.0.0 Security Audit requires v2.5.0 Governance (Dokumentation)

**Risikomanagement:**

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| Covina Verzögerung | Mittel | Hoch | VPB Mockdaten für UDS3-Entwicklung |
| Cross-Encoder Performance | Niedrig | Mittel | CPU-Fallback, Model-Optimierung |
| HA-Komplexität | Hoch | Kritisch | Externe DevOps-Beratung, Pilotphase |
| Security Audit Findings | Mittel | Hoch | Buffer-Zeit für Remediation |

---

## 4. Technische Best Practices

### 4.1 Architektur-Prinzipien

1. **Polyglot Persistence**
   - Right Tool for the Job: Jede Datenbank für ihre Stärke
   - No Single Point of Failure durch Multi-Backend
   - SAGA Pattern für transaktionale Integrität

2. **Zero-Trust Architecture**
   - Never Trust, Always Verify
   - mTLS für alle Service-Kommunikationen
   - PKI als Trust Anchor

3. **API-First Design**
   - OpenAPI/Swagger Specification
   - Versionierung (Semantic Versioning)
   - Backward Compatibility für 2 Major Versions

4. **12-Factor App Methodology**
   - Codebase: Ein Repo, viele Deployments
   - Dependencies: Explizite Deklaration
   - Config: Externalisierung in Environment
   - Backing Services: Austauschbare Ressourcen
   - Disposability: Fast Startup, Graceful Shutdown
   - Dev/Prod Parity: Minimale Unterschiede

### 4.2 Code Quality Standards

**Linting & Formatting:**
- **Ruff:** Python Linter (ersetzt flake8, isort, pylint)
- **Black:** Code Formatter
- **MyPy:** Static Type Checking (Minimum 80% Coverage)

**Testing:**
- **Unit Tests:** pytest, Minimum 85% Coverage
- **Integration Tests:** Multi-Backend Szenarien
- **Performance Tests:** pytest-benchmark
- **Security Tests:** bandit (SAST), safety (Dependency Check)

**CI/CD Pipeline:**
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: ruff check .
      - run: black --check .
      - run: mypy .
  
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pytest --cov=. --cov-report=xml
      - run: bandit -r .
  
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: safety check
      - run: trivy fs .
```

**Code Review:**
- Minimum 2 Approvals für Main Branch
- Security-relevante PRs: Zusätzliches Security Team Review
- Performance-kritische PRs: Benchmark-Vergleich

### 4.3 Documentation Standards

**Struktur:**
```
docs/
├── getting-started/
│   ├── installation.md
│   ├── quickstart.md
│   └── configuration.md
├── guides/
│   ├── search-api.md
│   ├── saga-transactions.md
│   ├── security.md
│   └── deployment.md
├── api/
│   ├── reference/       # Auto-generated from code
│   └── openapi.yaml
├── architecture/
│   ├── overview.md
│   ├── decisions/       # ADRs (Architecture Decision Records)
│   └── diagrams/
└── features/
    ├── caching.md
    ├── geo-spatial.md
    └── workflows.md
```

**Standards:**
- **Markdown:** Alle Dokumentation in Markdown
- **Diagrams:** Mermaid.js für inline Diagramme
- **API Docs:** Auto-generated via mkdocstrings
- **Versioning:** Dokumentation versioniert mit Code (git tags)

**Review-Prozess:**
- Technische Dokumentation: Code Review
- Architektur-Dokumente: Architecture Review Board
- User-Facing Docs: Technical Writing Review

### 4.4 Monitoring & Observability

**Metriken (RED Metrics):**
- **Rate:** Requests per second
- **Errors:** Error rate percentage
- **Duration:** Latency distribution (p50, p95, p99)

**Zusätzliche Metriken:**
- **Business:** searches/hour, feedback_rate, model_accuracy
- **System:** CPU, Memory, Disk I/O, Network
- **Database:** query_latency, connection_pool_usage, saga_completion_rate

**Alerting:**
```yaml
# Prometheus Alert Rules
groups:
  - name: uds3_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 10m
        annotations:
          summary: "p95 latency > 500ms"
```

**Distributed Tracing:**
- OpenTelemetry für Instrumentation
- Jaeger für Trace Visualization
- Correlation IDs für Request-Tracing

---

## 5. Erfolgskriterien & KPIs

### 5.1 Technische KPIs

| Metrik | v1.5.0 (Ist) | v1.6.0 (Ziel) | v2.0.0 (Ziel) | v3.0.0 (Ziel) |
|--------|--------------|---------------|---------------|---------------|
| **retrieval_latency_ms (p95)** | ~150ms | <100ms | <80ms | <50ms |
| **saga_completion_rate** | 99.5% | 99.8% | 99.9% | 99.95% |
| **model_accuracy (Golden Dataset)** | 85% | 88% | 92% | 95% |
| **search_recall@10** | 88% | 95% | 97% | 98% |
| **service_availability** | 99.0% | 99.5% | 99.9% | 99.95% |
| **test_coverage** | 85% | 88% | 90% | 92% |

### 5.2 Operative KPIs

| Metrik | v1.5.0 (Ist) | v3.0.0 (Ziel) |
|--------|--------------|---------------|
| **RTO (Recovery Time Objective)** | 8h | <4h |
| **RPO (Recovery Point Objective)** | 1h | <15min |
| **MTTR (Mean Time To Repair)** | 2h | <30min |
| **Deployment Frequency** | Weekly | Daily |
| **Change Failure Rate** | 10% | <5% |

### 5.3 Geschäftswert-KPIs

| Metrik | Baseline | v3.0.0 (Ziel) |
|--------|----------|---------------|
| **Zeitersparnis pro Rechtsanfrage** | 20-30% | 40-50% |
| **Reduktion Rechtsfehler** | 25-35% | 50-60% |
| **Mitarbeiter-Zufriedenheit** | 3.5/5.0 | >4.0/5.0 |
| **System Adoption Rate** | 40% | >80% |
| **User Retention (Veritas)** | 60% | >85% |

### 5.4 Compliance-KPIs

| Metrik | v1.5.0 (Ist) | v2.5.0 (Ziel) | v3.0.0 (Ziel) |
|--------|--------------|---------------|---------------|
| **DSGVO-Compliance** | Grundlegend | Vollständig | Zertifiziert |
| **EU AI Act Readiness** | 60% | 90% | 100% (Certified) |
| **Security Audit Score** | n/a | 85% | >90% |
| **Data Classification Coverage** | 0% | 100% | 100% |

---

## 6. Ressourcenplanung

### 6.1 Personalbedarf

#### v1.6.0 (Q1 2026) - 12 Wochen

| Rolle | FTE | Aufgaben |
|-------|-----|----------|
| **Backend Engineer** | 2.0 | Hybrid Search, Multi-Hop Reasoning |
| **ML Engineer** | 1.0 | RRF, Cross-Encoder |
| **DevOps Engineer** | 1.0 | Monitoring, Load Testing |
| **QA Engineer** | 0.5 | Test Coverage, Validation |
| **Gesamt** | **4.5 FTE** | |

#### v2.0.0 (Q2-Q3 2026) - 24 Wochen

| Rolle | FTE | Aufgaben |
|-------|-----|----------|
| **Backend Engineer** | 2.0 | VPB Integration, Feedback Loop |
| **ML Engineer** | 2.0 | PEFT/LoRA, Golden Dataset |
| **Security Engineer** | 1.0 | JIT Verification |
| **DevOps Engineer** | 1.0 | Infrastructure Scaling |
| **Gesamt** | **6.0 FTE** | |

#### v2.5.0 (Q4 2026) - 12 Wochen

| Rolle | FTE | Aufgaben |
|-------|-----|----------|
| **Backend Engineer** | 1.0 | Data Lineage, Retention |
| **Compliance Specialist** | 1.0 | Data Classification |
| **Legal Counsel** | 0.5 | EU AI Act Documentation |
| **Security Engineer** | 1.0 | Bias Monitoring |
| **Project Manager** | 1.0 | AI Ethics Committee |
| **Gesamt** | **4.5 FTE** | |

#### v3.0.0 (2027+) - 26 Wochen

| Rolle | FTE | Aufgaben |
|-------|-----|----------|
| **Backend Engineer** | 2.0 | Application Layer HA |
| **DevOps Engineer** | 2.0 | Kubernetes, Database Clustering |
| **Security Engineer** | 1.0 | Security Audit Support |
| **QA Engineer** | 1.0 | Performance Benchmarks |
| **Project Manager** | 1.0 | Certification Management |
| **Gesamt** | **7.0 FTE** | |

### 6.2 Infrastruktur-Kosten (Schätzung)

#### v1.6.0 - v2.5.0 (Development/Staging)

**Hinweis:** Alle Kostenangaben in Euro (€), Stand November 2025. Schätzungen basierend auf europäischen Cloud-Provider-Preisen (mittleres Preisniveau). On-Premise-Deployment reduziert laufende Kosten (Opex) bei höheren Anschaffungskosten (Capex). Preise können je nach Provider, Region und Verhandlung variieren.

| Ressource | Spezifikation | Monatlich (€) | Jährlich (€) |
|-----------|--------------|---------------|--------------|
| **Compute (VMs)** | 8 vCPU, 32 GB RAM (x3) | 450 | 5,400 |
| **Storage** | 2 TB SSD | 200 | 2,400 |
| **Databases** | PostgreSQL, Neo4j, ChromaDB | 600 | 7,200 |
| **Monitoring** | Prometheus, Grafana | 100 | 1,200 |
| **Gesamt Development** | | **1,350** | **16,200** |

#### v3.0.0 (Production - Year 1)

| Ressource | Spezifikation | Monatlich (€) | Jährlich (€) |
|-----------|--------------|---------------|--------------|
| **Kubernetes Cluster** | 20 Nodes (Multi-Zone) | 3,000 | 36,000 |
| **Database HA** | PostgreSQL Patroni, Neo4j Cluster | 2,500 | 30,000 |
| **Storage** | 10 TB SSD (Replicated) | 1,000 | 12,000 |
| **GPU** | 2x NVIDIA A100 (Clara Training) | 4,000 | 48,000 |
| **Load Balancers** | Multi-Region | 500 | 6,000 |
| **Monitoring/Logging** | ELK Stack, Prometheus, Jaeger | 800 | 9,600 |
| **Backup/DR** | S3-Compatible Storage (50 TB) | 400 | 4,800 |
| **Gesamt Production** | | **12,200** | **146,400** |

**Hinweis:** On-Premise Alternative reduziert laufende Kosten (Opex), erhöht aber Anschaffungskosten (Capex). Schätzungen unterliegen Marktpreisschwankungen und sollten vor Budgetfreigabe aktualisiert werden.

### 6.3 Externe Dienstleistungen

**Hinweis:** Alle Preisangaben in Euro (€), Stand November 2025. Schätzungen basierend auf durchschnittlichen Marktpreisen für entsprechende Dienstleistungen in Deutschland/EU. Tatsächliche Kosten können je nach Anbieter, Umfang und Verhandlung erheblich variieren.

| Service | Phase | Kosten (Schätzung, €) |
|---------|-------|-----------------------|
| **Security Audit** | v3.0.0 | 50,000 - 80,000 |
| **ISO 27001 Certification** | v3.0.0 | 30,000 - 50,000 |
| **DevOps Consulting (Kubernetes)** | v3.0.0 | 40,000 - 60,000 |
| **Legal Consulting (EU AI Act)** | v2.5.0 | 20,000 - 30,000 |
| **ML Consulting (Cross-Encoder)** | v1.6.0 | 15,000 - 25,000 |
| **Gesamt Externe Services** | | **155,000 - 245,000** |

---

## 7. Risikomanagement

### 7.1 Risikomatrix

| ID | Risiko | Wahrscheinlichkeit | Impact | Mitigation | Owner |
|----|--------|-------------------|--------|------------|-------|
| R1 | Covina Integration Verzögerung | Mittel | Hoch | Mockdaten, Independent Development | PM |
| R2 | Cross-Encoder Performance Issues | Niedrig | Mittel | CPU-Fallback, Model Optimization | ML |
| R3 | HA-Komplexität unterschätzt | Hoch | Kritisch | Externe DevOps-Expertise, Pilotphase | DevOps |
| R4 | Security Audit Critical Findings | Mittel | Hoch | Buffer-Zeit, Proaktive Reviews | Security |
| R5 | EU AI Act Anforderungen ändern sich | Mittel | Hoch | Continuous Monitoring, Legal Counsel | Legal |
| R6 | Clara PEFT Training instabil | Niedrig | Mittel | Golden Dataset Validation, Fallback | ML |
| R7 | Budget-Überschreitung | Mittel | Mittel | Quartalsweise Reviews, Contingency Reserve | PM |
| R8 | Fachkräftemangel (ML, Security) | Hoch | Hoch | Externe Contractor, Training | HR |

### 7.2 Mitigation-Strategien

#### R1: Covina Integration Verzögerung

**Mitigation:**
- Mockdaten für UDS3-seitige VPB-Entwicklung
- Parallel-Entwicklung ohne harte Abhängigkeit
- Regelmäßige Sync-Meetings mit Covina-Team

**Contingency:**
- v2.0.0 Partial Release ohne vollständige VPB-Integration
- VPB-Features als v2.1.0 nachgeliefert

#### R3: HA-Komplexität unterschätzt

**Mitigation:**
- Externe DevOps-Beratung ab v3.0.0 Start
- Pilotphase mit Single-Zone HA vor Multi-Zone
- Proof-of-Concept für kritische Komponenten (Patroni, Neo4j Clustering)

**Contingency:**
- Phased HA Rollout (PostgreSQL → Neo4j → ChromaDB → CouchDB)
- Acceptance Criteria pro Database (statt "All or Nothing")

#### R4: Security Audit Critical Findings

**Mitigation:**
- Interne Security Reviews vor externem Audit
- Red Team Exercises in v2.5.0
- Buffer-Zeit (4 Wochen) nach Audit für Remediation

**Contingency:**
- Priorisierung: Kritisch/Hoch vor v3.0.0 Launch
- Mittel/Niedrig in Post-Launch-Phase
- Transparente Kommunikation an Stakeholder

#### R8: Fachkräftemangel

**Mitigation:**
- Frühzeitige Rekrutierung (6 Monate vor Bedarf)
- Externe Contractors für Spezial-Skills (Cross-Encoder, Kubernetes)
- Interne Weiterbildung (Udemy, Coursera, Konferenzen)

**Contingency:**
- Priorisierung: Core Features vor Nice-to-Have
- Staffing Augmentation durch externe Dienstleister
- Timeline-Anpassung bei kritischen Engpässen

---

## 8. Stakeholder Management

### 8.1 Stakeholder-Matrix

| Stakeholder | Interesse | Einfluss | Strategie |
|-------------|-----------|----------|-----------|
| **Behörden-Anwender** | Hoch | Mittel | Regelmäßige User-Feedback-Sessions |
| **VCC Product Owner** | Hoch | Hoch | Wöchentliche Status-Updates |
| **IT-Leitung Behörde** | Mittel | Hoch | Monatliche Executive Briefings |
| **Data Protection Officer** | Hoch | Hoch | Quartalsweise Compliance Reviews |
| **AI Ethics Committee** | Hoch | Mittel | Bias Metrics Dashboard, Veto-Recht |
| **Externe Auditoren** | Niedrig | Hoch | Proaktive Dokumentation, Transparenz |
| **Entwicklungsteam** | Hoch | Niedrig | Daily Standups, Sprint Retrospectives |

### 8.2 Kommunikationsplan

#### Wöchentlich
- **Daily Standups:** Entwicklungsteam (15 min)
- **Tech Sync:** Backend, ML, DevOps Leads (30 min)
- **Status Report:** An Product Owner (schriftlich)

#### Monatlich
- **Executive Briefing:** IT-Leitung, 1h Präsentation
  - Fortschritt gegen Roadmap
  - KPI-Dashboard
  - Risks & Issues
  - Budget-Status

- **User Feedback Session:** Behörden-Anwender, 2h Workshop
  - Feature Demos
  - Usability Testing
  - Priorisierungs-Input

#### Quartalsweise
- **Compliance Review:** DPO, AI Ethics Committee, 2h Meeting
  - DSGVO-Status
  - Bias-Metriken
  - Incident-Reports (falls vorhanden)

- **Roadmap Review:** Alle Stakeholder, 4h Workshop
  - Fortschritt vs. Plan
  - Priorisierungs-Anpassungen
  - Nächste 3 Monate im Detail

#### Jährlich
- **Strategic Planning:** Product Owner, IT-Leitung, 2 Tage Offsite
  - Rückblick auf vergangenes Jahr
  - Strategische Ausrichtung für Folgejahr
  - Budget-Planung

### 8.3 Change Management

**Ziel:** Adoption sicherstellen, Widerstände minimieren

**Maßnahmen:**

1. **Kommunikation**
   - Transparenz über Änderungen (Was, Warum, Wann)
   - Multiple Kanäle (E-Mail, Intranet, Workshops)
   - Erfolgsgeschichten (Use Cases, Testimonials)

2. **Training**
   - Stufenplan: Basis → Fortgeschritten → Expert
   - Formate: Online (Videos), Präsenz (Workshops), Dokumentation
   - Zertifizierung für Power-User

3. **Support**
   - Helpdesk (Ticket-System)
   - Office Hours (wöchentlich 2h live Q&A)
   - Community (Internes Forum, Slack-Channel)

4. **Incentives**
   - Early Adopter Program (exklusiver Zugang zu neuen Features)
   - Gamification (Achievements für Nutzung)
   - Recognition (Top Contributors Hall of Fame)

---

## 9. Innovation & Forschung

### 9.1 Forschungskooperationen

**Strategische Partner:**

1. **Universitäten**
   - **KI-Forschung:** TU Berlin, DFKI (Deutsches Forschungszentrum für Künstliche Intelligenz)
   - **Themen:** Explainable AI, Backdoor Detection, Federated Learning
   - **Format:** Master-Arbeiten, Promotionen, Joint Papers

2. **Open-Source-Community**
   - **Neo4j, ChromaDB:** Feature Requests, Bugfixes, Contributions
   - **Format:** GitHub Issues, Pull Requests, Sponsorship

3. **EU-Förderprogramme**
   - **Digital Europe Programme:** AI Testing and Experimentation Facilities
   - **Horizon Europe:** Cluster 4 (Digital, Industry, Space)
   - **Format:** Konsortial-Projekte, Demonstratoren

### 9.2 Forschungsthemen (v3.0.0+)

#### 9.2.1 Explainable AI für Rechtsentscheidungen

**Problem:** Black-Box-KI-Entscheidungen nicht akzeptabel für Verwaltungsakte

**Forschungsfrage:** Wie kann Clara nachvollziehbare Begründungen liefern?

**Ansätze:**
- Attention-Mechanismus-Visualisierung
- LIME/SHAP für lokale Erklärbarkeit
- Counterfactual Explanations ("Wenn X anders wäre, würde Y gelten")

**Deliverable:** Explainability Dashboard in Veritas UI

#### 9.2.2 Privacy-Preserving Federated Learning

**Problem:** Behörden-übergreifendes Training ohne Daten-Sharing

**Forschungsfrage:** Können mehrere Behörden gemeinsam Clara trainieren ohne sensible Daten zu teilen?

**Ansätze:**
- Federated Learning (zentrale Aggregation, lokale Updates)
- Differential Privacy (Noise-Injection)
- Secure Multi-Party Computation (MPC)

**Deliverable:** Federated Clara Prototype

#### 9.2.3 Quantum-Resistant Cryptography

**Problem:** Zukünftige Quantencomputer brechen heutige PKI

**Forschungsfrage:** Wie bereiten wir UDS3 auf Post-Quantum-Ära vor?

**Ansätze:**
- NIST Post-Quantum Crypto Standards (CRYSTALS-Kyber, CRYSTALS-Dilithium)
- Hybride Signaturen (klassisch + quantum-resistant)
- Migration-Strategie für bestehende PKI

**Deliverable:** Post-Quantum PKI Migration Plan

### 9.3 Innovation Budget

**Allocation:** 10% des Gesamtbudgets für Forschung & Innovation

**Verwendung:**
- Proof-of-Concepts für neue Technologien
- Konferenz-Teilnahmen (NeurIPS, ICML, ACL)
- Open-Source-Contributions
- Hackathons (intern/extern)

---

## 10. Anhang

### 10.1 Glossar

| Begriff | Definition |
|---------|------------|
| **BM25** | Best Matching 25, keyword-basierter Retrieval-Algorithmus |
| **DPIA** | Data Protection Impact Assessment (Datenschutz-Folgenabschätzung) |
| **eIDAS** | Electronic Identification, Authentication and Trust Services (EU-Verordnung) |
| **LoRA** | Low-Rank Adaptation, parameter-effiziente Fine-Tuning-Methode |
| **mTLS** | Mutual TLS, bidirektionale Zertifikats-Authentifizierung |
| **NDCG** | Normalized Discounted Cumulative Gain, Retrieval-Qualitätsmetrik |
| **PEFT** | Parameter-Efficient Fine-Tuning |
| **RRF** | Reciprocal Rank Fusion, Rank-Aggregations-Algorithmus |
| **SAGA** | Distributed Transaction Pattern |
| **VPB** | Verwaltungsprozess-Backbone, Graph-basierte Prozessdarstellung |

### 10.2 Referenzen

**Technische Standards:**
- ISO/IEC 27001:2022 - Information Security Management
- SOC 2 Type II - Service Organization Control
- BSI IT-Grundschutz - Deutscher Sicherheitsstandard
- OWASP Top 10 - Web Application Security Risks

**Rechtliche Grundlagen:**
- EU AI Act (Regulation (EU) 2024/1689)
- DSGVO (Regulation (EU) 2016/679)
- eIDAS (Regulation (EU) 910/2014)
- Verwaltungsverfahrensgesetz (VwVfG)

**Wissenschaftliche Literatur:**
- Retrieval-Augmented Generation (Lewis et al., 2020)
- LoRA: Low-Rank Adaptation (Hu et al., 2021)
- Reciprocal Rank Fusion (Cormack et al., 2009)
- SAGA: Distributed Transactions (Garcia-Molina & Salem, 1987)

### 10.3 Änderungsprotokoll

| Version | Datum | Änderungen | Autor |
|---------|-------|-----------|-------|
| 1.0 | 2025-11-23 | Initiale Erstellung | VCC Development Team |

---

**Genehmigung:**

Diese Strategie bedarf der Freigabe durch:

- [ ] VCC Product Owner
- [ ] IT-Leitung
- [ ] Data Protection Officer
- [ ] AI Ethics Committee

**Nächste Review:** Q2 2026 (nach v1.6.0 Release)

---

**Kontakt:**

Für Rückfragen zu dieser Entwicklungsstrategie:

**VCC Development Team**  
Repository: https://github.com/makr-code/VCC-UDS3  
Issues: https://github.com/makr-code/VCC-UDS3/issues

**Lizenz:** Dieses Dokument ist Teil des VCC-UDS3-Projekts und unterliegt der MIT-Lizenz mit Government Partnership Commons Clause.

