# UDS3 Development TODO

**Letzte Aktualisierung:** 17. November 2025  
**Quelle:** [DOCUMENTATION_GAP_ANALYSIS.md](DOCUMENTATION_GAP_ANALYSIS.md)

---

## 🔥 Kritisch (Sofort) - Dokumentations-Konsolidierung

Diese Aufgaben adressieren kritische Inkonsistenzen zwischen Code und Dokumentation, identifiziert durch systematische Analyse.

### 1. Versionsnummer-Synchronisation ⭐⭐⭐
**Priorität:** KRITISCH  
**Aufwand:** 1-2 Stunden  
**Impact:** Hoch (Konsistenz)

- [x] README.md auf v1.5.0 aktualisieren (aktuell: v1.4.0)
- [x] Changelog-Eintrag für v1.5.0 in README.md hinzufügen
- [x] Alle v1.4.0-spezifischen Inhalte als "vergangene Version" markieren
- [x] Versionsreferenzen konsistent verwenden (immer "v1.5.0" Format)

**Hintergrund:** 
- setup.py, pyproject.toml, __init__.py: v1.5.0 ✅
- README.md: v1.4.0 ❌ (veraltet)
- Siehe DOCUMENTATION_GAP_ANALYSIS.md Abschnitt 1.1

### 2. LOC-Angaben korrigieren ⭐⭐⭐
**Priorität:** HOCH  
**Aufwand:** 2-3 Stunden  
**Impact:** Mittel (Glaubwürdigkeit)

- [x] IMPLEMENTATION_STATUS.md LOC-Zahlen aktualisieren
- [x] README.md LOC-Angaben korrigieren
- [ ] Automatisiertes LOC-Counting-Script erstellen (`scripts/count_loc.py`)
- [ ] Dokumentieren, wie LOC-Statistiken berechnet wurden

**Kritische Abweichungen gefunden:**
- secure_api.py: 580 (Docs) vs. 694 (Code) = +20%
- search_api.py: 850 (Docs) vs. 557 (Code) = -34%
- saga_crud.py: 450 (Docs) vs. 1569 (Code) = +249% ❌
- Gesamt-LOC: ~18,590 (Docs) vs. >39,798 (Code) = +114% ❌

**Details:** DOCUMENTATION_GAP_ANALYSIS.md Abschnitt 2

### 3. Test-Coverage aktualisieren ⭐⭐
**Priorität:** HOCH  
**Aufwand:** 1-2 Stunden  
**Impact:** Mittel

- [x] Korrekte Anzahl Test-Suites dokumentieren (48 statt "31/31")
- [ ] Coverage-Report generieren (`pytest --cov`)
- [ ] Coverage-Badge in README.md einbauen
- [ ] Klarstellen, was "31/31" bedeutet (Test-Kategorien?)

**Details:** DOCUMENTATION_GAP_ANALYSIS.md Abschnitt 5.1

---

## 🚀 Hoch (Diese Woche) - Feature-Dokumentation

### 4. Undokumentierte Features dokumentieren ⭐⭐⭐
**Priorität:** HOCH  
**Aufwand:** 1-2 Tage  
**Impact:** Hoch (Vollständigkeit)

Folgende implementierte Features sind nicht oder kaum dokumentiert:

- [x] **Caching System** dokumentieren
  - 46 Dateien mit Cache-Referenzen
  - core/cache.py (24KB), core/rag_cache.py vorhanden
  - Guide erstellt: docs/features/caching.md

- [x] **Geo/Spatial Features** dokumentieren
  - 27 Dateien mit Geo-Referenzen
  - api/geo.py (36KB), api/geo_config.json vorhanden
  - Guide erstellt: docs/features/geo-spatial.md

- [ ] **Streaming API** dokumentieren (falls öffentliche API)
  - 26 Dateien mit Streaming-Referenzen
  - manager/streaming.py vorhanden
  - Guide erstellen: docs/features/streaming.md

- [ ] **Workflow/Process Management** detaillierter dokumentieren
  - 104 Dateien mit Workflow-Referenzen
  - api/workflow.py, api/petrinet.py vorhanden
  - Guide erweitern: docs/features/workflows.md

**Details:** DOCUMENTATION_GAP_ANALYSIS.md Abschnitt 3.2

### 5. Dokumentations-Archivierung ⭐⭐
**Priorität:** HOCH  
**Aufwand:** 2-3 Stunden  
**Impact:** Mittel (Übersichtlichkeit)

- [x] docs/archive/ Verzeichnis erstellen
- [x] Unterverzeichnisse: phase-reports/, migration-reports/, historical/
- [x] Folgende Dokumente archivieren:
  - PHASE1_COMPLETE.md, PHASE2_COMPLETION_SUMMARY.md, PHASE2_PLANNING.md
  - PHASE3_BATCH_READ_COMPLETE.md, COMMIT_MESSAGE_PHASE3.md
  - UDS3_MIGRATION_PROGRESS_REPORT.md
  - Alle "*_COMPLETE.md" und "*_SUCCESS.md" Dateien
- [x] docs/README.md erstellen mit Navigation zu aktiver Dokumentation

**Begründung:** 76+ historische Dokumente erschweren Navigation

**Details:** DOCUMENTATION_GAP_ANALYSIS.md Abschnitt 4.3

### 6. Backend-Status-Klarstellung ⭐⭐
**Priorität:** HOCH  
**Aufwand:** 3-4 Stunden  
**Impact:** Hoch (Klarheit)

- [x] Backend-Status-Matrix erstellen (Production/Development/Experimental)
- [x] SQLite-Rolle klar dokumentieren (Development only)
- [x] VCC-Integration-Status für VERITAS, CLARA, COVINA aktualisieren
- [x] PKI-Integrationsarchitektur dokumentieren

**Gefundene Gaps:**
- CLARA: Nur 1 Code-Referenz (ggf. extern oder geplant)
- PKI: Nur 3 Code-Referenzen (ggf. externe Integration)

**Details:** DOCUMENTATION_GAP_ANALYSIS.md Abschnitt 5.2, 5.3

---

## 📚 Mittel (Dieser Monat) - Strukturverbesserungen

### 7. API-Referenz erstellen ⭐⭐⭐
**Priorität:** MITTEL  
**Aufwand:** 2-3 Tage  
**Impact:** Hoch (Entwickler-Erfahrung)

- [ ] Sphinx aufsetzen für automatische API-Docs
- [ ] API-Docs aus Docstrings generieren
- [ ] In mkdocs.yml integrieren (bereits vorhanden)
- [ ] docs/api/reference/ mit auto-generated Docs füllen
- [ ] OpenAPI/Swagger Spec erstellen (falls REST API)

**Aktuell:** Keine strukturierte API-Referenz vorhanden

**Details:** DOCUMENTATION_GAP_ANALYSIS.md Abschnitt 6.1

### 8. Dokumentations-Reorganisation ⭐⭐
**Priorität:** MITTEL  
**Aufwand:** 3-5 Tage  
**Impact:** Hoch (Langfristige Wartbarkeit)

- [ ] Neue Struktur implementieren (siehe DOCUMENTATION_GAP_ANALYSIS.md Abschnitt 7.1)
- [ ] Verzeichnisse erstellen: getting-started/, guides/, api/, architecture/, features/
- [ ] Dokumente in neue Struktur umorganisieren
- [ ] docs/README.md als Index/Navigation
- [ ] Interne Links aktualisieren

**Ziel:** Reduzierung von 89 unstrukturierten auf ~30 organisierte Docs

### 9. Deployment-Beispiele ergänzen ⭐
**Priorität:** MITTEL  
**Aufwand:** 2-3 Tage  
**Impact:** Mittel (Adoption)

- [ ] examples/ Verzeichnis im Repository erstellen
- [ ] docker-compose.yml für lokales Setup
- [ ] Kubernetes Beispiele (Helm Charts)
- [ ] Beispiel-Konfigurationen für alle Backends
- [ ] README in examples/ mit Erklärungen

**Aktuell:** UDS3_PRODUCTION_DEPLOYMENT_GUIDE.md vorhanden, aber keine konkreten Beispiele

**Details:** DOCUMENTATION_GAP_ANALYSIS.md Abschnitt 6.3

---

## 🔧 Niedrig (Nächstes Quarter) - Automatisierung

### 10. Automatisierungs-Scripts erstellen ⭐
**Priorität:** NIEDRIG  
**Aufwand:** 3-5 Tage  
**Impact:** Mittel (Langfristige Qualität)

- [ ] scripts/count_loc.py - Automatisches LOC-Tracking
- [ ] scripts/check_doc_coverage.py - Dokumentations-Coverage
- [ ] scripts/version_check.py - Version-Consistency-Check
- [ ] CI: Link-Checker für Dokumentation
- [ ] CI: Automatischer API-Docs-Build

**Ziel:** Verhinderung zukünftiger Dokumentations-Drifts

**Details:** DOCUMENTATION_GAP_ANALYSIS.md Abschnitt 7.3

### 11. Performance-Benchmarks dokumentieren ⭐
**Priorität:** NIEDRIG  
**Aufwand:** 2-3 Tage  
**Impact:** Niedrig (Nice-to-have)

- [ ] Benchmark-Script erstellen (tests/benchmarks/)
- [ ] Benchmark-Report generieren mit Testbedingungen
- [ ] Performance-Vergleiche dokumentieren
- [ ] In CI integrieren für Regression-Detection

**Aktuell:** Claims wie "20-100x speedup" ohne detaillierte Reports

**Details:** DOCUMENTATION_GAP_ANALYSIS.md Abschnitt 6.2

### 12. Migration Guides vervollständigen ⭐
**Priorität:** NIEDRIG  
**Aufwand:** 2-3 Tage  
**Impact:** Mittel (bei Updates wichtig)

- [ ] UPGRADING.md erstellen mit Version-zu-Version Guides
- [ ] DEPRECATIONS.md für deprecated Features
- [ ] Breaking Changes in CHANGELOG.md deutlich markieren
- [ ] v1.4.0 → v1.5.0 Upgrade Guide

**Aktuell:** UDS3_SEARCH_API_MIGRATION.md vorhanden, aber keine generellen Upgrade Guides

**Details:** DOCUMENTATION_GAP_ANALYSIS.md Abschnitt 6.4

---

## 📦 Release v1.4.0 - Search API Integration (Archiviert)

**Status:** ✅ Abgeschlossen (archiviert als historische Referenz)  
**Target Date:** November 2025  
**Priority:** ⭐⭐⭐ HIGH (Completed)

### ✅ Completed Tasks (Phase 1-4)

#### Phase 1: Architecture Decision ✅
- [x] Analyzed integration approaches (external vs. internal)
- [x] Decided on property-based access pattern
- [x] Created integration decision document
- [x] Validated benefits (-50% imports, -33% LOC, +100% discoverability)

#### Phase 2: Core Integration ✅
- [x] Created `uds3/search/` module structure
- [x] Moved `uds3_search_api.py` → `search/search_api.py` (563 LOC)
- [x] Added `search_api` property to `UnifiedDatabaseStrategy` (lazy-loading)
- [x] Created backward-compatible deprecation wrapper
- [x] Updated `uds3/__init__.py` exports
- [x] Created integration tests (5/5 PASSED)

#### Phase 3: Client Migration ✅
- [x] Updated VERITAS agent (`veritas_uds3_hybrid_agent.py`)
- [x] Updated VERITAS test scripts (2 files)
- [x] Updated VERITAS examples (6 examples)
- [x] Validated migration (3/3 test suites PASSED, 100%)

#### Phase 4: Documentation ✅
- [x] Created `README.md` (500 LOC) - Search API as featured example
- [x] Created `CHANGELOG.md` (200 LOC) - v1.4.0 entry with migration guide
- [x] Created `docs/UDS3_SEARCH_API_MIGRATION.md` (800 LOC) - Complete migration guide

**Documentation Metrics:**
- Total: 1,500 LOC (README 500, CHANGELOG 200, Migration 800)
- Examples: 15+ code snippets
- Coverage: All 4 import methods documented

### 📋 Pending Tasks - Release v1.4.0

#### Release Preparation (Next Steps)
- [ ] **Version Bump**
  - [ ] Update `uds3/__init__.py` version string
  - [ ] Update `pyproject.toml` version (v1.4.0)
  
- [ ] **Git Operations**
  - [ ] Commit all changes
  - [ ] Create git tag: `v1.4.0`
  - [ ] Create release notes

- [ ] **Post-Release Monitoring**
  - [ ] Monitor `uds3.uds3_search_api` usage (old import)
  - [ ] Track migration progress
  - [ ] Plan v1.5.0 deprecation removal (3 months)

---

## 🚦 Migration Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| **v1.4.0 (Now)** | - | ✅ Both APIs work (old shows warning) |
| **Month 1-2** | 60 days | 🔄 Migration period |
| **v1.5.0** | ~3 months | ⏭️ Remove old API (breaking change) |

---

## 📊 v1.4.0 Code Metrics

| Metric | Value |
|--------|-------|
| **Module LOC** | 563 (search_api.py) |
| **Documentation** | 1,500 LOC |
| **Tests** | 8/8 PASSED (100%) |
| **Import Reduction** | -50% (2 → 1) |
| **LOC Reduction** | -33% (3 → 2) |

---

# UDS3 - Offene To-dos (Legacy)

Diese Datei fasst alle offenen Aufgaben und Punkte zusammen, wie im Repository-Scan identifiziert.

Stand: 01.10.2025

---

## Aktueller ToDo-Status (kurz)
- `Lücken & Risiken identifizieren` — in progress
- `Konkrete ToDos & Verbesserungen vorschlagen` — not started

---

## Aufgaben (Priorisiert)

1) Health-Check: Umgebung & Basistests (Priority: High)
- Status: vorgeschlagen / noch nicht ausgeführt
- Beschreibung: Lokale Python-Umgebung konfigurieren, Dependencies aus `requirements.txt` installieren, `pytest` ausführen, `ruff`-Check.
- Geschätzter Aufwand: 30–90 Minuten (abhängig von Netzwerk/Build)
- Akzeptanzkriterien:
  - `pip install -r requirements.txt` läuft ohne fatalen Fehler
  - `pytest -q` läuft (mindestens ohne Syntax-Fehler); Output mit Liste fehlschlagender Tests wird erzeugt
  - `ruff` meldet style-Warnungen (optional: Fix-Vorschläge)
- Nächster Schritt: Ich kann das jetzt starten (vorausgesetzt Installation in Arbeitsumgebung ist erlaubt)


2) Sensible Schlüssel / Lizenzhärtung (Priority: High)
- Status: open
- Beschreibung: Dateien enthalten `module_licence_key` / `module_file_key` (VERITAS protected markers). Diese dürfen nicht im Klartext verändert oder entfernt werden ohne rechtliche Freigabe.
- Arbeitspunkte:
  - Inventar aller Dateien mit protection keys
  - Rücksprache mit Lizenzhalter (VERITAS) / Legal bevor Änderungen
  - Falls freigegeben: Schlüssel in Konfiguration / Secrets verschieben (z. B. env, Vault)
- Geschätzter Aufwand: 1–4 Stunden inkl. Abstimmung
- Akzeptanzkriterien: Keine Plaintext-Lizenzschlüssel in bearbeiteten Quell-Dateien; dokumentierter Übergang in Secret-Management


3) Tests & CI (Priority: Medium)
- Status: open
- Beschreibung:
  - Erweitern der Unit-Tests (Kern-Helper + Security/Identity basic tests)
  - GitHub Actions workflow (pytest + ruff + optional mypy)
- Arbeitspunkte:
  - Minimaltests für `_generate_document_id`, `_format_document_id`, Security ID generation
  - CI workflow `python: setup -> pip install -r -> ruff -> pytest`
- Geschätzter Aufwand: 1–2 Tage
- Akzeptanzkriterien: CI läuft grün bei Basis-Checks; neue Tests vorhanden


4) Adapter Interfaces & Mocks (Priority: Medium)
- Status: open
- Beschreibung: Definierte Protocols/Interfaces (z. B. SagaCrudProtocol, DatabaseManagerProtocol) und Mock-Implementierungen für Tests erstellen.
- Arbeitspunkte:
  - Minimal-Protokolle in `third_party_stubs` oder `uds3_admin_types.py`
  - Mocks in `tests/fixtures`
- Geschätzter Aufwand: 0.5–1 Tag
- Akzeptanzkriterien: Unit-Tests laufen mit Mocks ohne reale DB


5) Typisierung & Linter (Priority: Medium)
- Status: open
- Beschreibung: `ruff` und ggf. `mypy` einführen, Typhinweise in kritischen Teilen verbessern.
- Arbeitspunkte: `pyproject.toml`/`mypy.ini` minimal, `ruff`-Konfiguration, erste Fixes
- Geschätzter Aufwand: 2–6 Stunden
- Akzeptanzkriterien: `ruff` ohne Fehler (oder dokumentierte Ausnahmen); `mypy` ohne showstopper-Fehler


6) API-Dokumentation & Adapter-Beispiele (Priority: Low)
- Status: open
- Beschreibung: `docs/API_REFERENCE.md` mit Beispielen für Adapter-Implementierung (saga_crud, vector adapter, graph adapter)
- Geschätzter Aufwand: 4–8 Stunden
- Akzeptanzkriterien: Mindestens ein vollständiges Adapter-Beispiel in `docs/`


7) Langfristig: Performance, Observability, Distributed (Roadmap)
- Status: open
- Beschreibung: Profilerstellung, integration of metrics, distributed orchestration, caching strategies.

---

## Vorgehensweise / Workflow Vorschlag
1. Zustimmung hier im Chat: ich starte den Health-Check (Install & pytest).
2. Ergebnisreport (Erfolg/Fehler). Bei Fehlern: gezielte Fix-Tickets (Priorität: High/Medium/Low).
3. Sobald Health-Check grün (oder Mängel priorisiert), gehen wir Punkt für Punkt die Liste ab; ich übernehme die Umsetzung der ersten kleinen Tasks (Tests, CI) und melde jeweils Ergebnisse.

---

## Änderungsvermerk
- Datei automatisch erstellt am 01.10.2025 per Anforderung des Maintainers.



