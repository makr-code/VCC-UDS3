"""
Test Suite für VPB Adapter
Testet Integration von VPB Domain Models mit UDS3 Polyglot Manager
"""

import pytest
from datetime import datetime

# UDS3 Core
from uds3.core.polyglot_manager import UDS3PolyglotManager

# VPB
from uds3.vpb.adapter import VPBAdapter, create_vpb_adapter
from uds3.vpb.operations import (
    VPBProcess,
    VPBTask,
    VPBParticipant,
    ProcessStatus,
    TaskStatus,
    ParticipantRole,
    ProcessComplexity,
    LegalContext,
    AuthorityLevel
)


class TestVPBAdapter:
    """Test Suite für VPBAdapter"""
    
    @pytest.fixture
    def mock_polyglot(self):
        """Erstellt Mock Polyglot Manager für Tests"""
        class MockPolyglotManager:
            def save_document(self, data, app_domain):
                data['id'] = f"mock_id_{data.get('process_id', 'unknown')}"
                return data
            
            def get_document(self, doc_id, app_domain):
                return None
            
            def list_documents(self, app_domain, filters=None):
                return []
            
            def delete_document(self, doc_id, app_domain, soft_delete=True):
                return True
            
            def semantic_search(self, query, app_domain, top_k=10, filters=None):
                return {'results': []}
            
            def query_graph(self, pattern, app_domain):
                return []
            
            def query_sql(self, sql, params=None):
                return []
        
        return MockPolyglotManager()
    
    @pytest.fixture
    def adapter(self, mock_polyglot):
        """Erstellt VPBAdapter für Tests"""
        return VPBAdapter(polyglot_manager=mock_polyglot)
    
    @pytest.fixture
    def sample_process(self):
        """Erstellt Sample VPBProcess"""
        return VPBProcess(
            process_id="test_proc_001",
            name="Test Bauantrag Verfahren",
            description="Testprozess für VPBAdapter",
            authority="Bauamt Test",
            authority_level=AuthorityLevel.KOMMUNAL,
            status=ProcessStatus.ACTIVE,
            complexity=ProcessComplexity.MEDIUM,
            legal_context=LegalContext.BAURECHT,
            tasks=[
                VPBTask(
                    task_id="task_001",
                    name="Antrag prüfen",
                    description="Prüfung des Bauantrags",
                    status=TaskStatus.PENDING,
                    estimated_duration_days=5
                )
            ],
            participants=[
                VPBParticipant(
                    participant_id="part_001",
                    name="Max Mustermann",
                    role=ParticipantRole.SACHBEARBEITER,
                    email="max@test.de"
                )
            ],
            tags=["bauantrag", "test"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def test_adapter_creation(self, adapter):
        """Test 1: VPBAdapter Erstellung"""
        assert adapter is not None
        assert isinstance(adapter, VPBAdapter)
        assert adapter.APP_DOMAIN == "vpb"
        assert adapter.polyglot is not None
        print("✅ VPBAdapter erstellt")
    
    def test_save_process(self, adapter, sample_process):
        """Test 2: VPBProcess speichern"""
        saved = adapter.save_process(sample_process)
        
        assert saved is not None
        assert 'id' in saved
        assert saved.get('process_id') == sample_process.process_id
        assert saved.get('name') == sample_process.name
        
        print(f"✅ Process gespeichert: {saved['id']}")
    
    def test_get_process(self, adapter, sample_process):
        """Test 3: VPBProcess laden"""
        # Speichern
        adapter.save_process(sample_process)
        
        # Laden
        loaded = adapter.get_process(sample_process.process_id)
        
        assert loaded is not None
        assert isinstance(loaded, VPBProcess)
        assert loaded.process_id == sample_process.process_id
        assert loaded.name == sample_process.name
        assert loaded.status == sample_process.status
        
        print(f"✅ Process geladen: {loaded.process_id}")
    
    def test_update_process(self, adapter, sample_process):
        """Test 4: VPBProcess aktualisieren"""
        # Speichern
        adapter.save_process(sample_process)
        
        # Aktualisieren
        updated = adapter.update_process(
            sample_process.process_id,
            {'description': 'Aktualisierte Beschreibung'}
        )
        
        assert updated is not None
        assert updated.description == 'Aktualisierte Beschreibung'
        assert updated.process_id == sample_process.process_id
        
        print(f"✅ Process aktualisiert: {updated.process_id}")
    
    def test_delete_process(self, adapter, sample_process):
        """Test 5: VPBProcess löschen"""
        # Speichern
        adapter.save_process(sample_process)
        
        # Soft Delete
        success = adapter.delete_process(sample_process.process_id, soft_delete=True)
        
        assert success is True
        
        print(f"✅ Process gelöscht (soft): {sample_process.process_id}")
    
    def test_list_processes(self, adapter, sample_process):
        """Test 6: VPBProcesses auflisten"""
        # Speichere mehrere Prozesse
        adapter.save_process(sample_process)
        
        process2 = VPBProcess(
            process_id="test_proc_002",
            name="Zweiter Test Prozess",
            description="Test",
            authority="Bauamt Test",
            authority_level=AuthorityLevel.KOMMUNAL,
            status=ProcessStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        adapter.save_process(process2)
        
        # Liste
        processes = adapter.list_processes(status=ProcessStatus.ACTIVE)
        
        assert len(processes) >= 2
        assert all(isinstance(p, VPBProcess) for p in processes)
        
        print(f"✅ {len(processes)} Processes aufgelistet")
    
    def test_list_processes_with_filters(self, adapter, sample_process):
        """Test 7: VPBProcesses mit Filtern"""
        # Speichern
        adapter.save_process(sample_process)
        
        # Filter nach Complexity
        processes = adapter.list_processes(complexity=ProcessComplexity.MEDIUM)
        
        assert len(processes) >= 1
        assert all(p.complexity == ProcessComplexity.MEDIUM for p in processes if p.complexity)
        
        print(f"✅ {len(processes)} Processes mit Filter gefunden")
    
    def test_search_processes(self, adapter, sample_process):
        """Test 8: Semantische Suche"""
        # Speichern
        adapter.save_process(sample_process)
        
        # Suche
        results = adapter.search_processes("Bauantrag", top_k=5)
        
        assert isinstance(results, list)
        # Note: Ergebnisse können leer sein wenn Vector DB nicht initialisiert
        
        print(f"✅ Semantic Search: {len(results)} Ergebnisse")
    
    def test_analyze_process(self, adapter, sample_process):
        """Test 9: Process Mining - Analyse"""
        # Speichern
        adapter.save_process(sample_process)
        
        # Analysieren
        analysis = adapter.analyze_process(sample_process.process_id)
        
        assert analysis is not None
        assert analysis.process_id == sample_process.process_id
        assert analysis.complexity_level is not None
        assert analysis.complexity_score >= 0
        
        print(f"✅ Process analysiert: {analysis.complexity_level.value} ({analysis.complexity_score:.2f})")
    
    def test_calculate_complexity(self, adapter, sample_process):
        """Test 10: Komplexitätsberechnung"""
        # Speichern
        adapter.save_process(sample_process)
        
        # Komplexität berechnen
        complexity, score = adapter.calculate_complexity(sample_process.process_id)
        
        assert complexity is not None
        assert isinstance(complexity, ProcessComplexity)
        assert 0 <= score <= 100
        
        print(f"✅ Komplexität: {complexity.value} (Score: {score:.2f})")
    
    def test_identify_bottlenecks(self, adapter, sample_process):
        """Test 11: Bottleneck-Identifikation"""
        # Speichern
        adapter.save_process(sample_process)
        
        # Bottlenecks finden
        bottlenecks = adapter.identify_bottlenecks(sample_process.process_id)
        
        assert isinstance(bottlenecks, list)
        # Note: Kann leer sein bei einfachen Prozessen
        
        print(f"✅ {len(bottlenecks)} Bottlenecks gefunden")
    
    def test_batch_save_processes(self, adapter):
        """Test 12: Batch-Speicherung"""
        processes = [
            VPBProcess(
                process_id=f"batch_proc_{i}",
                name=f"Batch Process {i}",
                description="Batch Test",
                authority="Bauamt Test",
                authority_level=AuthorityLevel.KOMMUNAL,
                status=ProcessStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            for i in range(5)
        ]
        
        saved = adapter.batch_save_processes(processes)
        
        assert len(saved) == 5
        assert all('id' in doc for doc in saved)
        
        print(f"✅ {len(saved)} Processes im Batch gespeichert")
    
    def test_get_statistics(self, adapter, sample_process):
        """Test 13: Statistiken"""
        # Speichern
        adapter.save_process(sample_process)
        
        # Statistiken holen
        stats = adapter.get_statistics()
        
        assert 'total_processes' in stats
        assert 'by_status' in stats
        assert 'by_complexity' in stats
        assert stats['total_processes'] >= 1
        
        print(f"✅ Statistiken: {stats['total_processes']} Prozesse")
        print(f"   - Nach Status: {stats['by_status']}")
        print(f"   - Nach Komplexität: {stats['by_complexity']}")
    
    def test_query_process_tasks(self, adapter, sample_process):
        """Test 14: Graph Query - Tasks"""
        # Speichern
        adapter.save_process(sample_process)
        
        # Query Tasks (über Graph DB)
        tasks = adapter.query_process_tasks(sample_process.process_id)
        
        # Note: Kann leer sein wenn Graph DB nicht aktiv
        assert isinstance(tasks, list)
        
        print(f"✅ Graph Query (Tasks): {len(tasks)} Ergebnisse")
    
    def test_query_process_participants(self, adapter, sample_process):
        """Test 15: Graph Query - Participants"""
        # Speichern
        adapter.save_process(sample_process)
        
        # Query Participants (über Graph DB)
        participants = adapter.query_process_participants(sample_process.process_id)
        
        # Note: Kann leer sein wenn Graph DB nicht aktiv
        assert isinstance(participants, list)
        
        print(f"✅ Graph Query (Participants): {len(participants)} Ergebnisse")
    
    def test_adapter_repr(self, adapter):
        """Test 16: String Representation"""
        repr_str = repr(adapter)
        
        assert "VPBAdapter" in repr_str
        assert "vpb" in repr_str
        
        print(f"✅ Repr: {repr_str}")


def run_all_tests():
    """Führt alle Tests aus"""
    print("\n" + "="*60)
    print("UDS3 VPB ADAPTER TEST SUITE")
    print("="*60 + "\n")
    
    # Mock Polyglot Manager
    class MockPolyglotManager:
        def __init__(self):
            self._storage = {}
        
        def save_document(self, data, app_domain):
            doc_id = f"mock_id_{data.get('process_id', 'unknown')}"
            data['id'] = doc_id
            self._storage[doc_id] = data
            return data
        
        def get_document(self, doc_id, app_domain):
            return self._storage.get(doc_id)
        
        def list_documents(self, app_domain, filters=None):
            docs = list(self._storage.values())
            if filters:
                # Simple filter matching
                filtered = []
                for doc in docs:
                    match = True
                    for key, value in filters.items():
                        if doc.get(key) != value:
                            match = False
                            break
                    if match:
                        filtered.append(doc)
                return filtered
            return docs
        
        def update_document(self, doc_id, updates, app_domain):
            if doc_id in self._storage:
                self._storage[doc_id].update(updates)
                return self._storage[doc_id]
            return None
        
        def delete_document(self, doc_id, app_domain, soft_delete=True):
            if doc_id in self._storage:
                del self._storage[doc_id]
                return True
            return False
        
        def semantic_search(self, query, app_domain, top_k=10, filters=None):
            return {'results': list(self._storage.values())[:top_k]}
        
        def query_graph(self, pattern, app_domain):
            return []
        
        def query_sql(self, sql, params=None):
            return []
    
    mock_polyglot = MockPolyglotManager()
    adapter = VPBAdapter(polyglot_manager=mock_polyglot)
    test_suite = TestVPBAdapter()
    
    # Sample Process
    sample_process = VPBProcess(
        process_id="test_proc_001",
        name="Test Bauantrag Verfahren",
        description="Testprozess für VPBAdapter",
        authority="Bauamt Test",
        authority_level=AuthorityLevel.KOMMUNAL,
        status=ProcessStatus.ACTIVE,
        complexity=ProcessComplexity.MEDIUM,
        legal_context=LegalContext.BAURECHT,
        tasks=[],
        participants=[],
        tags=["bauantrag", "test"],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    try:
        # Basic Tests
        test_suite.test_adapter_creation(adapter)
        test_suite.test_save_process(adapter, sample_process)
        test_suite.test_get_process(adapter, sample_process)
        test_suite.test_update_process(adapter, sample_process)
        test_suite.test_list_processes(adapter, sample_process)
        test_suite.test_search_processes(adapter, sample_process)
        
        # Process Mining Tests
        test_suite.test_analyze_process(adapter, sample_process)
        test_suite.test_calculate_complexity(adapter, sample_process)
        test_suite.test_identify_bottlenecks(adapter, sample_process)
        
        # Batch & Stats
        test_suite.test_batch_save_processes(adapter)
        test_suite.test_get_statistics(adapter, sample_process)
        
        # Graph Queries
        test_suite.test_query_process_tasks(adapter, sample_process)
        test_suite.test_query_process_participants(adapter, sample_process)
        
        # Misc
        test_suite.test_adapter_repr(adapter)
        
        # Delete Test (am Ende)
        test_suite.test_delete_process(adapter, sample_process)
        
        print("\n" + "="*60)
        print("ALLE TESTS BESTANDEN!")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ Test fehlgeschlagen: {e}")
        raise
    
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
