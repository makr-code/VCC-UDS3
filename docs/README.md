# UDS3 Documentation Index

**Last Updated:** 17. November 2025

---

## 📚 Current Documentation

### Getting Started
- [Quick Start Guide](QUICKSTART.md) - Get started with UDS3
- [Configuration Guide](CONFIGURATION_GUIDE.md) - Configuration options
- [Developer Howto](DEVELOPER_HOWTO.md) - Development guide

### Core Features
- [Security Architecture](SECURITY.md) - Complete security documentation
- [Batch Operations](BATCH_OPERATIONS.md) - High-performance batch processing
- [SAGA Pattern](COUCHDB_SAGA_PROBLEM_RESOLUTION.md) - Distributed transactions

### API Documentation
- [Search API](api/search/search_api.md) - Search API documentation
- [Database API Integration](UDS3_DATABASE_API_INTEGRATION_ANALYSE.md) - Database API analysis
- [Search API Migration](UDS3_SEARCH_API_MIGRATION.md) - Migration guide

### Architecture & Design
- [Framework Summary](UDS3_FRAMEWORK_SUMMARY.md) - UDS3 framework overview
- [Polyglot Persistence](UDS3_POLYGLOT_PERSISTENCE_CORE.md) - Multi-database architecture
- [VPB Architecture](UDS3_VERWALTUNGSARCHITEKTUR.md) - Administrative architecture
- [Identity Service Design](UDS3_Identity_Service_Design.md) - Identity service architecture

### Production & Deployment
- [Production Deployment Guide](UDS3_PRODUCTION_DEPLOYMENT_GUIDE.md) - Production deployment
- [4D Integration Deployment](UDS3_4D_INTEGRATION_DEPLOYMENT_PLAN.md) - 4D deployment plan
- [Geo Setup Guide](UDS3_GEODATEN_SETUP_GUIDE.md) - Geographic data setup

### Integration & Extensions
- [PostgreSQL/CouchDB Integration](../POSTGRES_COUCHDB_INTEGRATION.md) - Backend integration
- [Verwaltungsakte Extension](UDS3_VERWALTUNGSAKTE_EXTENSION.md) - Administrative acts extension
- [Verwaltungsakte Verallgemeinerung](UDS3_VERWALTUNGSAKTE_VERALLGEMEINERUNG.md) - Generalization

### Reports & Analysis
- [Remote Database Connectivity](REMOTE_DATABASE_CONNECTIVITY_REPORT.md) - Database connectivity
- [Security Audit](BANDIT_SECURITY_REPORT.md) - Bandit security report
- [Dependencies](DEPENDENCIES.md) - Dependency documentation

### Special Topics
- [Geo/4D Concepts](UDS3_4D_GEODATEN_VOLLKONZEPT.md) - 4D geographic data concept
- [VPB Naming Conventions](UDS3_VBP_NAMENSKONVENTIONEN.md) - Naming conventions
- [Petrinet Workflow Analyzer](UDS3_PETRINET_WORKFLOW_ANALYZER.md) - Workflow analysis
- [RAG Requirements](uds3_rag_requirements.txt) - RAG pipeline requirements

### Change History
- [Changelog](CHANGELOG.md) - Version history and changes
- [Project Overview](PROJECT_OVERVIEW.md) - Project overview

---

## 📦 Archived Documentation

Historical documents have been organized for better navigation:

### Phase Reports
Location: `archive/phase-reports/`
- PHASE1_COMPLETE.md
- PHASE2_PLANNING.md, PHASE2_COMPLETION_SUMMARY.md, PHASE2_VALIDATION_REPORT.md
- PHASE3_BATCH_READ_PLAN.md, PHASE3_BATCH_READ_COMPLETE.md
- PHASE3_PRODUCTION_TEST_RESULTS.md, PHASE3_PERFORMANCE_BENCHMARK_REPORT.md
- COMMIT_MESSAGE_PHASE3.md

### Migration Reports
Location: `archive/migration-reports/`
- UDS3_MIGRATION_ANALYSIS_REPORT.md
- UDS3_MIGRATION_PROGRESS_REPORT.md

### Historical Completion Reports
Location: `archive/historical/`
- UDS3_CROSS_REFERENCE_STANDARDISIERUNG_COMPLETE.md
- UDS3_INGESTION_INTEGRATION_SUCCESS.md
- UDS3_LANDESRECHT_BUNDESRECHTSPRECHUNG_SUCCESS.md
- UDS3_OPTIMIZATION_SUMMARY_PHASE_1_COMPLETE.md
- UDS3_RELATIONS_INTEGRATION_COMPLETE.md
- UDS3_SEARCH_API_PHASE4_COMPLETION_REPORT.md
- UDS3_SUCCESS_SUMMARY.md
- UDS3_VECTORFILTER_SUCCESS.md
- UDS3_BUILD_v1.4.0_COMPLETION_REPORT.md
- UDS3_SESSION_SUMMARY_20251001.md
- UDS3_UPDATE_REPORT.md
- UDS3_OPTIMIZATION_SUMMARY_TODO_01.md
- UDS3_OPTIMIZATION_SUMMARY_TODO_02.md
- CLEANUP_PLAN.md, CLEANUP_SUMMARY.md
- REORGANISATION_PLAN.md, REORGANISATION_ABSCHLUSSBERICHT.md

### Other Archives
Location: `archive/`
- `releases/` - Release-related documents
- `sessions/` - Session summaries
- `todos/` - Completed TODO documents

---

## 🔗 Related Documentation

**Root Level Documentation:**
- [Main README](../README.md) - Project overview and quick start
- [Implementation Status](../IMPLEMENTATION_STATUS.md) - Current implementation status
- [Roadmap](../ROADMAP.md) - Development roadmap
- [Contributing](../CONTRIBUTING.md) - Contribution guidelines
- [Development](../DEVELOPMENT.md) - Development setup
- [Security Audit](../SECURITY_AUDIT.md) - Security audit summary

**Documentation Consolidation (November 2025):**
- [Documentation Gap Analysis](../DOCUMENTATION_GAP_ANALYSIS.md) - Comprehensive gap analysis
- [Documentation Summary](../DOCUMENTATION_CONSOLIDATION_SUMMARY.md) - Executive summary
- [Implementation Guide](../DOCUMENTATION_IMPLEMENTATION_GUIDE.md) - How to implement improvements
- [Consolidation README](../DOCUMENTATION_CONSOLIDATION_README.md) - Master navigation

---

## 📝 Documentation Guidelines

### For Contributors

When creating new documentation:

1. **Current Documentation:** Place active documentation in the appropriate category above
2. **Historical Documentation:** Completed phase reports, migration summaries, and completion reports should go in `archive/`
3. **Naming Convention:** 
   - Guides: `*_GUIDE.md`
   - Reports: `*_REPORT.md`
   - Architecture: `*_DESIGN.md`, `*_ARCHITECTURE.md`
   - Completion: `*_COMPLETE.md` (archive immediately)
4. **Update this Index:** Add new documents to the appropriate section

### For Users

- **Start Here:** [Main README](../README.md) for project overview
- **Getting Started:** Use the "Getting Started" section above
- **API Documentation:** Check the "API Documentation" section
- **Troubleshooting:** See production/deployment guides
- **Historical Context:** Browse `archive/` directories

---

**Note:** This index is maintained as part of the documentation consolidation effort. For the complete analysis of documentation gaps and improvement plans, see [DOCUMENTATION_GAP_ANALYSIS.md](../DOCUMENTATION_GAP_ANALYSIS.md).
