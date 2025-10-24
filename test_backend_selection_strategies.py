#!/usr/bin/env python3
"""
UDS3 Backend Selection Strategy Examples

Zeigt verschiedene Strategien für die Auswahl von Backends in Multi-Backend Umgebungen.
"""

from database.config import BaseDatabaseManager, DatabaseType, DatabaseBackend
from typing import List, Optional
import random
import time

class SmartBackendSelector:
    """Intelligente Backend-Auswahl mit verschiedenen Strategien."""
    
    def __init__(self, database_manager: BaseDatabaseManager):
        self.manager = database_manager
        self.load_counters = {}  # Simulierte Load-Zähler
        self.round_robin_counters = {}  # Round-Robin Zähler
    
    def select_by_purpose(self, db_type: DatabaseType, purpose: str) -> Optional:
        """Wählt Backend basierend auf Zweck."""
        databases = self.manager.get_databases_by_type(db_type)
        
        for db in databases:
            if db.settings.get('purpose') == purpose:
                return db
        
        # Fallback: Erstes verfügbares Backend
        return databases[0] if databases else None
    
    def select_by_priority(self, db_type: DatabaseType) -> Optional:
        """Wählt Backend mit höchster Priorität (niedrigste Nummer).""" 
        databases = self.manager.get_databases_by_type(db_type)
        
        if not databases:
            return None
        
        # Sortiere nach Priorität (niedrigste = höchste Priorität)
        return min(databases, key=lambda x: x.settings.get('priority', 999))
    
    def select_round_robin(self, db_type: DatabaseType) -> Optional:
        """Round-Robin Auswahl für Load Balancing."""
        databases = self.manager.get_databases_by_type(db_type)
        
        if not databases:
            return None
        
        # Initialisiere Counter falls nötig
        type_key = db_type.value
        if type_key not in self.round_robin_counters:
            self.round_robin_counters[type_key] = 0
        
        # Wähle nächstes Backend
        selected = databases[self.round_robin_counters[type_key] % len(databases)]
        self.round_robin_counters[type_key] += 1
        
        return selected
    
    def select_by_load(self, db_type: DatabaseType) -> Optional:
        """Wählt Backend mit geringster Last."""
        databases = self.manager.get_databases_by_type(db_type)
        
        if not databases:
            return None
        
        # Simuliere Last (in echter Implementierung: echte Metriken)
        def get_simulated_load(db):
            key = f"{db.host}:{db.port}"
            if key not in self.load_counters:
                self.load_counters[key] = random.randint(0, 100)
            return self.load_counters[key]
        
        # Wähle Backend mit geringster Last
        return min(databases, key=get_simulated_load)
    
    def select_by_region(self, db_type: DatabaseType, preferred_region: str = "eu-central-1") -> Optional:
        """Wählt Backend basierend auf geografischer Nähe."""
        databases = self.manager.get_databases_by_type(db_type)
        
        if not databases:
            return None
        
        # Suche Backend in bevorzugter Region
        for db in databases:
            if db.settings.get('region') == preferred_region:
                return db
        
        # Fallback: Erstes verfügbares
        return databases[0]

class UDS3OperationExamples:
    """Beispiele für UDS3 Operationen mit Multi-Backend Setup."""
    
    def __init__(self, selector: SmartBackendSelector):
        self.selector = selector
    
    def vector_search_example(self, query: str, language: str = "de"):
        """Vector Search mit sprachspezifischem Backend."""
        print(f"🔍 Vector Search: '{query}' (Language: {language})")
        
        # Wähle sprachspezifisches Vector Backend
        if language == "de":
            backend = self.selector.select_by_purpose(DatabaseType.VECTOR, "german_embeddings")
        elif language == "en":
            backend = self.selector.select_by_purpose(DatabaseType.VECTOR, "english_embeddings")
        else:
            # Fallback: Bestes verfügbares Backend
            backend = self.selector.select_by_priority(DatabaseType.VECTOR)
        
        if backend:
            print(f"   → Using: {backend.backend.value} @ {backend.host}")
            print(f"   → Model: {backend.settings.get('model', 'N/A')}")
            return f"vector_search_result_from_{backend.backend.value}"
        else:
            print("   → No vector backend available!")
            return None
    
    def user_operation_example(self, user_id: str, operation: str):
        """User-Operation mit dedizierter User-DB."""
        print(f"👤 User Operation: {operation} for user {user_id}")
        
        # Wähle User-spezifische Datenbank
        backend = self.selector.select_by_purpose(DatabaseType.RELATIONAL, "user_data")
        
        if backend:
            print(f"   → Using: {backend.backend.value} @ {backend.host}")
            print(f"   → Database: {backend.database}")
            return f"user_operation_result"
        else:
            print("   → No user database available!")
            return None
    
    def analytics_query_example(self, query: str):
        """Analytics Query mit dedizierter Analytics-DB."""
        print(f"📊 Analytics Query: {query}")
        
        # Wähle Analytics-spezifische Datenbank
        backend = self.selector.select_by_purpose(DatabaseType.RELATIONAL, "analytics")
        
        if backend:
            print(f"   → Using: {backend.backend.value} @ {backend.host}")
            print(f"   → Schema: {backend.settings.get('schema', 'N/A')}")
            return f"analytics_result"
        else:
            print("   → No analytics database available!")
            return None
    
    def file_storage_example(self, filename: str, file_type: str, size_mb: int):
        """File Storage mit größen- und typspezifischer Auswahl."""
        print(f"📁 File Storage: {filename} ({file_type}, {size_mb}MB)")
        
        # Wähle Backend basierend auf Dateigröße und -typ
        if size_mb > 1000:  # Große Dateien → Cold Archive
            backend = self.selector.select_by_purpose(DatabaseType.FILE, "cold_archive")
        elif file_type in ['jpg', 'png', 'mp4']:  # Media → Media Storage
            backend = self.selector.select_by_purpose(DatabaseType.FILE, "media_storage") 
        else:  # Dokumente → Document Storage
            backend = self.selector.select_by_purpose(DatabaseType.FILE, "documents")
        
        if backend:
            print(f"   → Using: {backend.backend.value} @ {backend.host}")
            print(f"   → Purpose: {backend.settings.get('purpose', 'N/A')}")
            max_size = backend.settings.get('max_file_size', 'N/A')
            print(f"   → Max Size: {max_size}")
            return f"file_stored_in_{backend.backend.value}"
        else:
            print("   → No file backend available!")
            return None
    
    def graph_traversal_example(self, start_node: str, relationship: str):
        """Graph Traversal mit Load Balancing."""
        print(f"🔗 Graph Traversal: {start_node} → {relationship}")
        
        # Round-Robin für Load Balancing zwischen Graph DBs
        backend = self.selector.select_round_robin(DatabaseType.GRAPH)
        
        if backend:
            print(f"   → Using: {backend.backend.value} @ {backend.host}")
            print(f"   → Role: {backend.settings.get('role', 'N/A')}")
            return f"graph_traversal_result"
        else:
            print("   → No graph backend available!")
            return None
    
    def high_availability_example(self, operation: str):
        """High Availability mit Fallback-Strategien."""
        print(f"🔄 HA Operation: {operation}")
        
        # 1. Versuche Primary Backend
        primary = self.selector.select_by_priority(DatabaseType.GRAPH)
        
        if primary and self._simulate_availability(primary):
            print(f"   → Primary: {primary.backend.value} @ {primary.host}")
            return "primary_result"
        
        # 2. Fallback zu Secondary
        databases = self.selector.manager.get_databases_by_type(DatabaseType.GRAPH)
        for db in sorted(databases, key=lambda x: x.settings.get('priority', 999)):
            if db != primary and self._simulate_availability(db):
                print(f"   → Fallback: {db.backend.value} @ {db.host}")
                return "fallback_result"
        
        print("   → All backends unavailable!")
        return None
    
    def _simulate_availability(self, backend) -> bool:
        """Simuliert Backend-Verfügbarkeit (90% Chance)."""
        return random.random() > 0.1

def demonstrate_uds3_flexibility():
    """Demonstriert die Flexibilität des UDS3 Systems."""
    print("=== UDS3 MULTI-BACKEND OPERATION EXAMPLES ===")
    print()
    
    # Setup Enterprise Manager (aus vorherigem Test)
    from test_multi_backend_flexibility import EnterpriseDatabaseManager
    
    manager = EnterpriseDatabaseManager()
    selector = SmartBackendSelector(manager)
    operations = UDS3OperationExamples(selector)
    
    print("🚀 Testing verschiedene UDS3 Operationen:")
    print()
    
    # 1. Vector Search Beispiele
    print("=" * 60)
    operations.vector_search_example("Machine Learning Grundlagen", "de")
    operations.vector_search_example("Natural Language Processing", "en")
    operations.vector_search_example("def calculate_similarity()", "code")
    
    print()
    
    # 2. Relational Database Beispiele
    print("=" * 60)
    operations.user_operation_example("user123", "UPDATE profile")
    operations.analytics_query_example("SELECT * FROM user_interactions WHERE date > '2025-01-01'")
    
    print()
    
    # 3. File Storage Beispiele  
    print("=" * 60)
    operations.file_storage_example("presentation.pdf", "pdf", 5)
    operations.file_storage_example("video.mp4", "mp4", 500) 
    operations.file_storage_example("archive.zip", "zip", 2000)
    
    print()
    
    # 4. Graph Database Beispiele mit Load Balancing
    print("=" * 60)
    for i in range(3):
        operations.graph_traversal_example(f"user_{i}", "KNOWS")
    
    print()
    
    # 5. High Availability Beispiel
    print("=" * 60)
    operations.high_availability_example("Critical graph query")
    
    print()
    print("=" * 60)
    print("✅ UDS3 Multi-Backend Operations Complete!")
    print()
    print("📊 Demonstrated Capabilities:")
    print("   ✅ Purpose-based backend selection")
    print("   ✅ Priority-based failover")
    print("   ✅ Round-robin load balancing") 
    print("   ✅ Language-specific vector backends")
    print("   ✅ File-type specific storage backends")
    print("   ✅ High availability with fallbacks")
    print()
    print("🎯 UDS3 successfully handles complex multi-backend scenarios!")

if __name__ == "__main__":
    demonstrate_uds3_flexibility()