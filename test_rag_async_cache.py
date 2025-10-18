"""
Test Suite für UDS3 RAG Async & Caching Layer
Testet erweiterte RAG-Funktionen: Async, Caching, Parallel Queries
"""

import asyncio
import time
from pathlib import Path

# UDS3 Core Imports
from uds3.core.embeddings import create_german_embeddings
from uds3.core.llm_ollama import OllamaClient
from uds3.core.polyglot_manager import UDS3PolyglotManager
from uds3.core.rag_cache import RAGCache, PersistentRAGCache
from uds3.core.rag_async import UDS3AsyncRAG, create_async_rag


def test_rag_cache():
    """Test 1: RAG Cache Funktionalität"""
    print("\n" + "="*60)
    print("TEST 1: RAG Cache")
    print("="*60)
    
    cache = RAGCache(max_size=100, default_ttl_minutes=5)
    
    # Test Put & Get
    cache.put(
        query="Was ist ein Verwaltungsverfahren?",
        answer="Ein Verwaltungsverfahren ist...",
        confidence=0.85,
        sources=[{"id": "doc1", "title": "VwVfG"}],
        query_type="PROCESS_SEARCH"
    )
    
    # Cache Hit
    result = cache.get("Was ist ein Verwaltungsverfahren?")
    assert result is not None, "❌ Cache Hit fehlgeschlagen"
    assert result['answer'] == "Ein Verwaltungsverfahren ist...", "❌ Falscher Cache-Inhalt"
    print("✅ Cache Hit erfolgreich")
    
    # Cache Miss
    result = cache.get("Andere Query")
    assert result is None, "❌ Cache Miss sollte None zurückgeben"
    print("✅ Cache Miss erfolgreich")
    
    # Stats
    stats = cache.get_stats()
    print(f"📊 Cache Stats: {stats}")
    assert stats['hits'] == 1, "❌ Hit-Count falsch"
    assert stats['misses'] == 1, "❌ Miss-Count falsch"
    assert stats['hit_rate_percent'] == 50.0, "❌ Hit-Rate falsch"
    print("✅ Cache Stats korrekt")
    
    # LRU Eviction Test
    print("\n📦 Teste LRU Eviction (max_size=5)...")
    small_cache = RAGCache(max_size=5)
    
    for i in range(10):
        small_cache.put(
            query=f"Query {i}",
            answer=f"Answer {i}",
            confidence=0.8,
            sources=[],
            query_type="GENERAL"
        )
    
    assert small_cache.get_stats()['size'] == 5, "❌ Cache-Size nicht begrenzt"
    assert small_cache.get_stats()['evictions'] == 5, "❌ Eviction-Count falsch"
    print("✅ LRU Eviction funktioniert")
    
    print("\n🎉 RAG Cache Tests bestanden!")


def test_persistent_cache():
    """Test 2: Persistent RAG Cache"""
    print("\n" + "="*60)
    print("TEST 2: Persistent RAG Cache")
    print("="*60)
    
    cache_dir = ".test_rag_cache"
    
    # Erstelle Cache und füge Eintrag hinzu
    cache1 = PersistentRAGCache(cache_dir=cache_dir, max_size=100)
    cache1.put(
        query="Persistent Test Query",
        answer="Persistent Test Answer",
        confidence=0.9,
        sources=[],
        query_type="TEST"
    )
    
    print("✅ Cache erstellt und Eintrag gespeichert")
    
    # Erstelle neuen Cache (sollte von Disk laden)
    cache2 = PersistentRAGCache(cache_dir=cache_dir, max_size=100)
    result = cache2.get("Persistent Test Query")
    
    assert result is not None, "❌ Disk-Persistence fehlgeschlagen"
    assert result['answer'] == "Persistent Test Answer", "❌ Falscher Inhalt nach Reload"
    print("✅ Disk-Persistence funktioniert")
    
    # Cleanup
    cache2.clear()
    Path(cache_dir).rmdir()
    print("✅ Cleanup erfolgreich")
    
    print("\n🎉 Persistent Cache Tests bestanden!")


async def test_async_rag():
    """Test 3: Async RAG Pipeline"""
    print("\n" + "="*60)
    print("TEST 3: Async RAG Pipeline")
    print("="*60)
    
    # Initialisiere UDS3 Components
    print("🔧 Initialisiere UDS3 Components...")
    
    # Embeddings
    embeddings = create_german_embeddings()
    print("✅ Embeddings initialisiert")
    
    # LLM Client
    llm = OllamaClient(base_url="http://localhost:11434")
    if not llm.is_available():
        print("⚠️  Ollama nicht verfügbar - überspringe Async RAG Test")
        return
    print("✅ LLM Client initialisiert")
    
    # Polyglot Manager (mit Test-DB)
    polyglot = UDS3PolyglotManager()
    print("✅ Polyglot Manager initialisiert")
    
    # Async RAG
    async_rag = await create_async_rag(
        polyglot_manager=polyglot,
        llm_client=llm,
        embeddings=embeddings,
        enable_cache=True,
        cache_ttl_minutes=5
    )
    print("✅ Async RAG initialisiert")
    
    # Test Query
    print("\n🔍 Führe Async Query aus...")
    query = "Was ist ein Bauantrag?"
    
    start = time.time()
    result1 = await async_rag.answer_query_async(query, app_domain="vpb")
    time1 = time.time() - start
    
    print(f"📊 Query 1 (Cache Miss):")
    print(f"   - Antwort: {result1.answer[:100]}...")
    print(f"   - Konfidenz: {result1.confidence}")
    print(f"   - Query Type: {result1.query_type}")
    print(f"   - Ausführungszeit: {result1.execution_time_ms:.1f}ms")
    print(f"   - Cache Hit: {result1.cache_hit}")
    
    assert not result1.cache_hit, "❌ Erster Query sollte kein Cache Hit sein"
    print("✅ Cache Miss erkannt")
    
    # Wiederhole Query (sollte aus Cache kommen)
    print("\n🔍 Wiederhole Query (sollte Cache Hit sein)...")
    start = time.time()
    result2 = await async_rag.answer_query_async(query, app_domain="vpb")
    time2 = time.time() - start
    
    print(f"📊 Query 2 (Cache Hit):")
    print(f"   - Ausführungszeit: {result2.execution_time_ms:.1f}ms")
    print(f"   - Cache Hit: {result2.cache_hit}")
    print(f"   - Speedup: {time1/time2:.1f}x schneller")
    
    assert result2.cache_hit, "❌ Zweiter Query sollte Cache Hit sein"
    assert result2.execution_time_ms < result1.execution_time_ms, "❌ Cache sollte schneller sein"
    print("✅ Cache Hit erfolgreich")
    
    # Batch Query Test
    print("\n🔍 Teste Batch Queries (parallel)...")
    queries = [
        "Was ist ein Verwaltungsakt?",
        "Wie läuft ein Genehmigungsverfahren ab?",
        "Was bedeutet Widerspruch?"
    ]
    
    start = time.time()
    batch_results = await async_rag.batch_query_async(queries, app_domain="vpb")
    batch_time = time.time() - start
    
    print(f"📊 Batch Results:")
    print(f"   - Anzahl Queries: {len(batch_results)}")
    print(f"   - Gesamt-Zeit: {batch_time:.2f}s")
    print(f"   - Durchschnitt: {batch_time/len(queries):.2f}s pro Query")
    
    for i, result in enumerate(batch_results):
        print(f"   - Query {i+1}: {result.query_type.value}, Konfidenz: {result.confidence:.2f}")
    
    assert len(batch_results) == 3, "❌ Batch sollte 3 Ergebnisse haben"
    print("✅ Batch Queries erfolgreich")
    
    # Stats
    print("\n📊 Async RAG Stats:")
    stats = async_rag.get_stats()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"   - {key}:")
            for k, v in value.items():
                print(f"      - {k}: {v}")
        else:
            print(f"   - {key}: {value}")
    
    # Cleanup
    async_rag.shutdown()
    print("\n✅ Cleanup erfolgreich")
    
    print("\n🎉 Async RAG Tests bestanden!")


async def test_parallel_multi_db_search():
    """Test 4: Parallele Multi-DB Suche"""
    print("\n" + "="*60)
    print("TEST 4: Parallele Multi-DB Suche")
    print("="*60)
    
    # Initialisiere Components
    embeddings = create_german_embeddings()
    llm = OllamaClient(base_url="http://localhost:11434")
    
    if not llm.is_available():
        print("⚠️  Ollama nicht verfügbar - überspringe Multi-DB Test")
        return
    
    polyglot = UDS3PolyglotManager()
    
    async_rag = await create_async_rag(
        polyglot_manager=polyglot,
        llm_client=llm,
        embeddings=embeddings
    )
    
    # Parallele Suche
    print("🔍 Starte parallele Multi-DB Suche...")
    query = "Bauantrag Genehmigung"
    databases = ['chromadb', 'neo4j', 'sqlite']
    
    start = time.time()
    results = await async_rag.parallel_multi_db_search(query, databases, top_k=3)
    search_time = time.time() - start
    
    print(f"📊 Multi-DB Search Results ({search_time:.2f}s):")
    for db_name, db_results in results.items():
        print(f"   - {db_name}: {len(db_results)} Ergebnisse")
    
    assert len(results) == len(databases), "❌ Nicht alle DBs abgefragt"
    print("✅ Parallele Multi-DB Suche erfolgreich")
    
    async_rag.shutdown()
    print("\n🎉 Multi-DB Search Tests bestanden!")


def run_all_tests():
    """Führt alle Tests aus"""
    print("\n" + "="*60)
    print("🧪 UDS3 RAG ASYNC & CACHING TEST SUITE")
    print("="*60)
    
    try:
        # Sync Tests
        test_rag_cache()
        test_persistent_cache()
        
        # Async Tests
        asyncio.run(test_async_rag())
        asyncio.run(test_parallel_multi_db_search())
        
        print("\n" + "="*60)
        print("🎉 ALLE TESTS BESTANDEN!")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ Test fehlgeschlagen: {e}")
        raise
    
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
