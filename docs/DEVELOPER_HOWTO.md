# UDS3 Developer HowTo Guide
**Unified Database Strategy v3 - Developer Initialization Guide**

## 🚀 Quick Start

### 1. Basic UDS3 Instance (Localhost/Stubs)

```python
# Schnellste Initialisierung - verwendet Stub-Konfiguration
from uds3 import config
from core import UnifiedDatabaseStrategy
from manager import UDS3SagaOrchestrator

# Automatische Stub-Konfiguration (localhost, test-passwords)
uds3 = UnifiedDatabaseStrategy()
print("✅ UDS3 initialized with stub backends")

# Verfügbare Services
saga = UDS3SagaOrchestrator()
print("✅ SAGA orchestrator ready")
```

### 2. UDS3 Instance mit Remote Backends

```python
# Mit config_local.py (automatische Remote-Konfiguration)
from uds3 import config
from core import UnifiedDatabaseStrategy

# config_local.py wird automatisch geladen wenn vorhanden
uds3 = UnifiedDatabaseStrategy()
print("✅ UDS3 initialized with remote backends")

# Prüfe aktive Konfiguration
print("Graph Host:", config.DATABASES['graph']['host'])
print("Production Mode:", config.FEATURES['expect_uds3_backend'])
```

### 3. UDS3 mit expliziten Credentials

```python
# Direkte Übergabe von DB-Zugangsdaten
from core import UnifiedDatabaseStrategy
from database.config import DatabaseConnection, DatabaseType, DatabaseBackend

# Custom Backend-Konfiguration
custom_backends = [
    DatabaseConnection(
        db_type=DatabaseType.GRAPH,
        backend=DatabaseBackend.NEO4J,
        host="my-neo4j-server.com",
        port=7687,
        username="neo4j_user",
        password="secure_password",
        database="production_graph"
    ),
    DatabaseConnection(
        db_type=DatabaseType.RELATIONAL,
        backend=DatabaseBackend.POSTGRESQL,
        host="my-postgres-server.com", 
        port=5432,
        username="pg_user",
        password="secure_pg_password",
        database="production_db"
    )
]

# UDS3 mit Custom Backends
uds3 = UnifiedDatabaseStrategy(custom_backends=custom_backends)
print("✅ UDS3 initialized with custom credentials")
```

## 🔧 Initialisierungsszenarien

### Szenario 1: Development Environment
```bash
# Keine config_local.py vorhanden
# → Automatisch localhost/stub backends
git clone uds3-repo
cd uds3
python -c "from core import UnifiedDatabaseStrategy; uds3 = UnifiedDatabaseStrategy()"
# ✅ Läuft mit ChromaDB/Neo4j/PostgreSQL localhost stubs
```

### Szenario 2: Production Environment  
```bash
# Mit config_local.py für Remote-Server
git clone uds3-repo
cd uds3
cp config_local.py.example config_local.py
# Editiere config_local.py mit echten Credentials
python -c "from core import UnifiedDatabaseStrategy; uds3 = UnifiedDatabaseStrategy()"
# ✅ Läuft mit Remote-Servern aus config_local.py
```

### Szenario 3: CI/CD Pipeline
```bash
# Mit Environment Variables
export NEO4J_HOST="ci-neo4j.internal"
export NEO4J_PASSWORD="ci_password" 
export POSTGRES_HOST="ci-postgres.internal"
export POSTGRES_PASSWORD="ci_pg_password"

python -c "from core import UnifiedDatabaseStrategy; uds3 = UnifiedDatabaseStrategy()"
# ✅ Environment Variables überschreiben config_local.py
```

### Szenario 4: Microservice mit Service Discovery
```python
# Integration mit Service Discovery
from core import UnifiedDatabaseStrategy
from database.config import DatabaseManager, ProductionDatabaseManager

class ServiceDiscoveryDatabaseManager(ProductionDatabaseManager):
    def get_databases(self):
        # Service Discovery Logic hier
        neo4j_host = discover_service("neo4j")
        postgres_host = discover_service("postgresql")
        
        return self._create_discovered_databases(neo4j_host, postgres_host)

# Custom Manager verwenden
custom_manager = ServiceDiscoveryDatabaseManager()
uds3 = UnifiedDatabaseStrategy(database_manager=custom_manager)
```

## 🔀 Multi-Backend Konfigurationen

### Standard Single-Backend Setup
```python
# Eine Datenbank pro Typ (Standard)
backends = [
    DatabaseConnection(DatabaseType.GRAPH, DatabaseBackend.NEO4J, ...),
    DatabaseConnection(DatabaseType.RELATIONAL, DatabaseBackend.POSTGRESQL, ...),
    DatabaseConnection(DatabaseType.VECTOR, DatabaseBackend.CHROMADB, ...),
    DatabaseConnection(DatabaseType.FILE, DatabaseBackend.COUCHDB, ...)
]
```

### Multi-Graph Backend Setup
```python
# 2 Graph Databases für Load Balancing/Redundancy
backends = [
    # Primary Graph DB
    DatabaseConnection(
        db_type=DatabaseType.GRAPH,
        backend=DatabaseBackend.NEO4J,
        host="neo4j-primary.com",
        settings={'role': 'primary', 'priority': 1}
    ),
    # Secondary Graph DB
    DatabaseConnection(
        db_type=DatabaseType.GRAPH, 
        backend=DatabaseBackend.ARANGODB,
        host="arangodb-secondary.com",
        settings={'role': 'secondary', 'priority': 2}
    )
]
```

### Multi-Relational Backend Setup
```python
# 6 Relational Databases für verschiedene Zwecke
backends = [
    # User Data
    DatabaseConnection(DatabaseType.RELATIONAL, DatabaseBackend.POSTGRESQL, 
                      host="users-db.com", database="users", 
                      settings={'purpose': 'user_data'}),
    
    # Analytics Data  
    DatabaseConnection(DatabaseType.RELATIONAL, DatabaseBackend.POSTGRESQL,
                      host="analytics-db.com", database="analytics",
                      settings={'purpose': 'analytics'}),
                      
    # Audit Logs
    DatabaseConnection(DatabaseType.RELATIONAL, DatabaseBackend.POSTGRESQL,
                      host="audit-db.com", database="audit",
                      settings={'purpose': 'audit'}),
                      
    # Cache/Sessions
    DatabaseConnection(DatabaseType.RELATIONAL, DatabaseBackend.POSTGRESQL,
                      host="cache-db.com", database="sessions", 
                      settings={'purpose': 'cache'}),
                      
    # Reporting
    DatabaseConnection(DatabaseType.RELATIONAL, DatabaseBackend.POSTGRESQL,
                      host="reports-db.com", database="reports",
                      settings={'purpose': 'reporting'}),
                      
    # Archive
    DatabaseConnection(DatabaseType.RELATIONAL, DatabaseBackend.POSTGRESQL, 
                      host="archive-db.com", database="archive",
                      settings={'purpose': 'archive'})
]
```

### Multi-Vector Backend Setup
```python
# 4 Vector Databases für verschiedene Embedding-Modelle
backends = [
    # German Embeddings
    DatabaseConnection(DatabaseType.VECTOR, DatabaseBackend.CHROMADB,
                      host="german-vectors.com",
                      settings={'model': 'german-bert', 'language': 'de'}),
                      
    # English Embeddings  
    DatabaseConnection(DatabaseType.VECTOR, DatabaseBackend.PINECONE,
                      settings={'model': 'openai-ada', 'language': 'en',
                               'api_key': 'pinecone_key'}),
                               
    # Code Embeddings
    DatabaseConnection(DatabaseType.VECTOR, DatabaseBackend.WEAVIATE,
                      host="code-vectors.com",
                      settings={'model': 'code-bert', 'purpose': 'code_search'}),
                      
    # Image Embeddings
    DatabaseConnection(DatabaseType.VECTOR, DatabaseBackend.CHROMADB,
                      host="image-vectors.com", 
                      settings={'model': 'clip', 'purpose': 'image_search'})
]
```

### Multi-File Backend Setup
```python
# 3 File Servers für verschiedene Dateitypen
backends = [
    # Document Storage
    DatabaseConnection(DatabaseType.FILE, DatabaseBackend.COUCHDB,
                      host="docs-couchdb.com",
                      settings={'purpose': 'documents', 'max_size': '100MB'}),
                      
    # Media Storage
    DatabaseConnection(DatabaseType.FILE, DatabaseBackend.S3,
                      settings={'bucket': 'media-files', 'region': 'eu-central-1',
                               'purpose': 'media'}),
                               
    # Archive Storage
    DatabaseConnection(DatabaseType.FILE, DatabaseBackend.S3,
                      settings={'bucket': 'archive-files', 'region': 'eu-central-1',
                               'storage_class': 'GLACIER', 'purpose': 'archive'})
]
```

## 🎯 Backend Selection Strategies

### Strategy 1: Round Robin
```python
class RoundRobinDatabaseManager(BaseDatabaseManager):
    def select_backend(self, db_type: DatabaseType, operation: str):
        backends = self.get_databases_by_type(db_type)
        return backends[self.round_robin_counter % len(backends)]
```

### Strategy 2: Load-Based Selection
```python
class LoadBalancedDatabaseManager(BaseDatabaseManager):
    def select_backend(self, db_type: DatabaseType, operation: str):
        backends = self.get_databases_by_type(db_type)
        return min(backends, key=lambda b: b.get_current_load())
```

### Strategy 3: Purpose-Based Selection
```python
class PurposeDatabaseManager(BaseDatabaseManager):
    def select_backend(self, db_type: DatabaseType, purpose: str):
        backends = self.get_databases_by_type(db_type)
        return next(b for b in backends 
                   if b.settings.get('purpose') == purpose)
```

## 📊 Configuration Examples

### Minimal Development Setup
```python
# config.py - nur localhost stubs
config_factory = UDS3ConfigFactory()  # 4 backends, alle localhost
uds3 = UnifiedDatabaseStrategy()      # ✅ 2 minutes setup
```

### Standard Production Setup  
```python
# config_local.py - eine DB pro Typ
backends = 4  # Graph, Relational, Vector, File
uds3 = UnifiedDatabaseStrategy()  # ✅ Production ready
```

### Enterprise Multi-Backend Setup
```python
# Custom Manager - viele DBs pro Typ
enterprise_manager = EnterpriseDatabaseManager()
backends = 15  # 2 Graph + 6 Relational + 4 Vector + 3 File
uds3 = UnifiedDatabaseStrategy(database_manager=enterprise_manager)
# ✅ Enterprise scale
```

## 🔍 Debugging & Monitoring

### Check Active Backends
```python
from database.config import database_manager

# Liste alle aktiven Backends
print(database_manager.list_databases())

# Prüfe spezifische Backend-Typen
vector_dbs = database_manager.get_databases_by_type(DatabaseType.VECTOR)
print(f"Vector DBs: {len(vector_dbs)}")

for db in vector_dbs:
    print(f"  - {db.backend.value} @ {db.host}:{db.port}")
```

### Test Backend Connectivity
```python
def test_all_backends():
    for db_type in DatabaseType:
        backends = database_manager.get_databases_by_type(db_type)
        print(f"{db_type.value.upper()}: {len(backends)} backends")
        
        for backend in backends:
            try:
                # Test connection
                success = backend.test_connection()
                status = "✅" if success else "❌"
                print(f"  {status} {backend.backend.value} @ {backend.host}")
            except Exception as e:
                print(f"  ❌ {backend.backend.value}: {e}")

test_all_backends()
```

## 🚀 Performance Tips

### 1. Connection Pooling
```python
# Größere Pools für Multi-Backend Setups
DatabaseConnection(
    connection_pool_size=50,  # Statt default 10
    query_timeout=120,        # Längere Timeouts
    cache_ttl=1800           # Längeres Caching
)
```

### 2. Async Operations
```python
# UDS3 unterstützt async für Multi-Backend Operations
async def parallel_operations():
    tasks = [
        uds3.vector_search_async("query1"),
        uds3.graph_traversal_async("query2"), 
        uds3.relational_query_async("query3")
    ]
    results = await asyncio.gather(*tasks)
    return results
```

### 3. Caching Strategies
```python
# Backend-spezifisches Caching
DatabaseConnection(
    settings={
        'cache_strategy': 'redis',
        'cache_ttl': 3600,
        'cache_prefix': f'{purpose}_{model}'
    }
)
```

## 📋 Checklist für Produktive Deployments

### ✅ Konfiguration
- [ ] `config_local.py` erstellt und konfiguriert
- [ ] Alle Passwörter aus Default-Werten geändert
- [ ] SSL/TLS für Remote-Verbindungen aktiviert
- [ ] Connection Pools angemessen dimensioniert

### ✅ Backends
- [ ] Alle Backend-Services erreichbar
- [ ] Authentifizierung funktioniert
- [ ] Backup-Strategien implementiert
- [ ] Monitoring eingerichtet

### ✅ UDS3 Application
- [ ] Backend-Selection Strategy definiert
- [ ] Error Handling für Backend-Ausfälle
- [ ] Health Checks implementiert
- [ ] Logging konfiguriert

---
**Ready to scale**: UDS3 unterstützt von 1 bis 100+ Backends pro Typ! 🚀