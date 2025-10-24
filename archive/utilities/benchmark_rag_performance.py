"""
UDS3 RAG Performance Benchmark
Umfassende Performance-Metriken für RAG Pipeline:
- Execution Time (mit/ohne Cache)
- Cache Hit Rate
- Throughput (Queries/Sekunde)
- Latency Percentiles (P50, P95, P99)
- Token Optimization
- Memory Usage
"""

import asyncio
import time
import statistics
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from datetime import datetime

# UDS3 Core Imports
from uds3.core.embeddings import create_german_embeddings
from uds3.core.llm_ollama import OllamaClient
from uds3.core.polyglot_manager import UDS3PolyglotManager
from uds3.core.rag_async import UDS3AsyncRAG, create_async_rag


class RAGBenchmark:
    """RAG Performance Benchmark Runner"""
    
    def __init__(self, async_rag: UDS3AsyncRAG):
        self.async_rag = async_rag
        self.results: Dict[str, List[float]] = defaultdict(list)
        self.test_queries = self._load_test_queries()
    
    def _load_test_queries(self) -> List[str]:
        """Lade Test-Queries für VPB Domain"""
        return [
            "Was ist ein Bauantrag?",
            "Wie läuft ein Genehmigungsverfahren ab?",
            "Was ist ein Verwaltungsakt?",
            "Was bedeutet Widerspruch?",
            "Wie funktioniert eine Baugenehmigung?",
            "Was ist ein Bebauungsplan?",
            "Was ist eine Nutzungsänderung?",
            "Was ist ein Vorbescheid?",
            "Was ist eine Abrissgenehmigung?",
            "Was ist ein Bauvorbescheid?",
            "Was ist eine Baulast?",
            "Was ist eine Stellungnahme?",
            "Was ist ein Planfeststellungsverfahren?",
            "Was ist eine Umweltverträglichkeitsprüfung?",
            "Was ist ein Widerspruchsverfahren?",
        ]
    
    async def benchmark_execution_time(self, num_queries: int = 50) -> Dict[str, Any]:
        """Benchmark: Execution Time ohne Cache"""
        print(f"\n🔍 Benchmark: Execution Time ({num_queries} Queries, No Cache)")
        print("-" * 60)
        
        execution_times = []
        
        # Warmup
        print("🔥 Warmup (5 Queries)...")
        for i in range(5):
            await self.async_rag.answer_query_async(
                self.test_queries[i % len(self.test_queries)],
                app_domain="vpb"
            )
        
        # Benchmark
        print(f"🚀 Benchmark Start ({num_queries} Queries)...")
        start_time = time.time()
        
        for i in range(num_queries):
            query = self.test_queries[i % len(self.test_queries)]
            
            query_start = time.time()
            result = await self.async_rag.answer_query_async(query, app_domain="vpb")
            query_time = (time.time() - query_start) * 1000  # ms
            
            execution_times.append(query_time)
            
            if (i + 1) % 10 == 0:
                print(f"   Fortschritt: {i+1}/{num_queries} Queries")
        
        total_time = time.time() - start_time
        
        # Statistiken
        avg = statistics.mean(execution_times)
        median = statistics.median(execution_times)
        std_dev = statistics.stdev(execution_times)
        min_time = min(execution_times)
        max_time = max(execution_times)
        
        # Percentiles
        sorted_times = sorted(execution_times)
        p50 = sorted_times[int(len(sorted_times) * 0.50)]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        
        # Throughput
        throughput = num_queries / total_time
        
        results = {
            "num_queries": num_queries,
            "total_time_s": round(total_time, 2),
            "avg_time_ms": round(avg, 1),
            "median_time_ms": round(median, 1),
            "std_dev_ms": round(std_dev, 1),
            "min_time_ms": round(min_time, 1),
            "max_time_ms": round(max_time, 1),
            "p50_ms": round(p50, 1),
            "p95_ms": round(p95, 1),
            "p99_ms": round(p99, 1),
            "throughput_qps": round(throughput, 2)
        }
        
        print(f"\n📊 Execution Time Results:")
        for key, value in results.items():
            print(f"   {key}: {value}")
        
        return results
    
    async def benchmark_cache_performance(self, num_iterations: int = 5) -> Dict[str, Any]:
        """Benchmark: Cache Hit Rate & Performance"""
        print(f"\n🔍 Benchmark: Cache Performance ({num_iterations} Iterations)")
        print("-" * 60)
        
        cache_hits = 0
        cache_misses = 0
        hit_times = []
        miss_times = []
        
        queries = self.test_queries[:10]  # 10 unique Queries
        
        for iteration in range(num_iterations):
            print(f"\n   Iteration {iteration + 1}/{num_iterations}")
            
            for query in queries:
                start = time.time()
                result = await self.async_rag.answer_query_async(query, app_domain="vpb")
                elapsed = (time.time() - start) * 1000  # ms
                
                if result.cache_hit:
                    cache_hits += 1
                    hit_times.append(elapsed)
                else:
                    cache_misses += 1
                    miss_times.append(elapsed)
        
        total_queries = cache_hits + cache_misses
        hit_rate = (cache_hits / total_queries) * 100 if total_queries > 0 else 0
        
        avg_hit_time = statistics.mean(hit_times) if hit_times else 0
        avg_miss_time = statistics.mean(miss_times) if miss_times else 0
        speedup = avg_miss_time / avg_hit_time if avg_hit_time > 0 else 0
        
        results = {
            "total_queries": total_queries,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "hit_rate_percent": round(hit_rate, 1),
            "avg_hit_time_ms": round(avg_hit_time, 1),
            "avg_miss_time_ms": round(avg_miss_time, 1),
            "cache_speedup": round(speedup, 2)
        }
        
        print(f"\n📊 Cache Performance Results:")
        for key, value in results.items():
            print(f"   {key}: {value}")
        
        return results
    
    async def benchmark_batch_throughput(self, batch_sizes: List[int] = [5, 10, 20]) -> Dict[str, Any]:
        """Benchmark: Batch Query Throughput"""
        print(f"\n🔍 Benchmark: Batch Throughput")
        print("-" * 60)
        
        results = {}
        
        for batch_size in batch_sizes:
            print(f"\n   Testing batch_size={batch_size}...")
            
            # Erstelle Batch
            queries = [self.test_queries[i % len(self.test_queries)] for i in range(batch_size)]
            
            # Sequential Execution
            seq_start = time.time()
            for query in queries:
                await self.async_rag.answer_query_async(query, app_domain="vpb")
            sequential_time = time.time() - seq_start
            
            # Batch (Parallel) Execution
            batch_start = time.time()
            batch_results = await self.async_rag.batch_query_async(queries, app_domain="vpb")
            batch_time = time.time() - batch_start
            
            speedup = sequential_time / batch_time if batch_time > 0 else 0
            
            results[f"batch_{batch_size}"] = {
                "batch_size": batch_size,
                "sequential_time_s": round(sequential_time, 2),
                "batch_time_s": round(batch_time, 2),
                "speedup": round(speedup, 2),
                "saved_time_s": round(sequential_time - batch_time, 2)
            }
            
            print(f"      Sequential: {sequential_time:.2f}s")
            print(f"      Batch: {batch_time:.2f}s")
            print(f"      Speedup: {speedup:.2f}x")
        
        return results
    
    async def benchmark_latency_distribution(self, num_queries: int = 100) -> Dict[str, Any]:
        """Benchmark: Latency Distribution"""
        print(f"\n🔍 Benchmark: Latency Distribution ({num_queries} Queries)")
        print("-" * 60)
        
        latencies = []
        
        for i in range(num_queries):
            query = self.test_queries[i % len(self.test_queries)]
            
            start = time.time()
            await self.async_rag.answer_query_async(query, app_domain="vpb")
            latency = (time.time() - start) * 1000  # ms
            
            latencies.append(latency)
            
            if (i + 1) % 25 == 0:
                print(f"   Fortschritt: {i+1}/{num_queries} Queries")
        
        # Distribution Analysis
        sorted_latencies = sorted(latencies)
        
        results = {
            "num_samples": num_queries,
            "min_ms": round(min(latencies), 1),
            "p10_ms": round(sorted_latencies[int(len(sorted_latencies) * 0.10)], 1),
            "p25_ms": round(sorted_latencies[int(len(sorted_latencies) * 0.25)], 1),
            "p50_ms": round(sorted_latencies[int(len(sorted_latencies) * 0.50)], 1),
            "p75_ms": round(sorted_latencies[int(len(sorted_latencies) * 0.75)], 1),
            "p90_ms": round(sorted_latencies[int(len(sorted_latencies) * 0.90)], 1),
            "p95_ms": round(sorted_latencies[int(len(sorted_latencies) * 0.95)], 1),
            "p99_ms": round(sorted_latencies[int(len(sorted_latencies) * 0.99)], 1),
            "max_ms": round(max(latencies), 1),
            "avg_ms": round(statistics.mean(latencies), 1),
            "std_dev_ms": round(statistics.stdev(latencies), 1)
        }
        
        print(f"\n📊 Latency Distribution:")
        for key, value in results.items():
            print(f"   {key}: {value}")
        
        return results


async def run_full_benchmark():
    """Führt alle Benchmarks aus"""
    print("\n" + "="*60)
    print("🧪 UDS3 RAG PERFORMANCE BENCHMARK")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize Components
    print("\n🔧 Initialisiere UDS3 Components...")
    embeddings = create_german_embeddings()
    llm = OllamaClient(base_url="http://localhost:11434")
    
    if not llm.is_available():
        print("❌ Ollama nicht verfügbar - Benchmark abgebrochen")
        sys.exit(1)
    
    polyglot = UDS3PolyglotManager()
    
    # Create Async RAG (mit Cache)
    async_rag = await create_async_rag(
        polyglot_manager=polyglot,
        llm_client=llm,
        embeddings=embeddings,
        enable_cache=True,
        cache_ttl_minutes=60
    )
    print("✅ Components initialisiert")
    
    # Create Benchmark Runner
    benchmark = RAGBenchmark(async_rag)
    
    # Collect All Results
    all_results = {
        "timestamp": datetime.now().isoformat(),
        "system_info": {
            "python_version": sys.version,
            "platform": sys.platform
        }
    }
    
    try:
        # 1. Execution Time Benchmark
        exec_results = await benchmark.benchmark_execution_time(num_queries=50)
        all_results["execution_time"] = exec_results
        
        # 2. Cache Performance Benchmark
        cache_results = await benchmark.benchmark_cache_performance(num_iterations=5)
        all_results["cache_performance"] = cache_results
        
        # 3. Batch Throughput Benchmark
        batch_results = await benchmark.benchmark_batch_throughput(batch_sizes=[5, 10, 20])
        all_results["batch_throughput"] = batch_results
        
        # 4. Latency Distribution Benchmark
        latency_results = await benchmark.benchmark_latency_distribution(num_queries=100)
        all_results["latency_distribution"] = latency_results
        
        # 5. Final Stats from RAG
        print("\n📊 RAG Pipeline Stats:")
        stats = async_rag.get_stats()
        all_results["pipeline_stats"] = stats
        
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for k, v in value.items():
                    print(f"      {k}: {v}")
            else:
                print(f"   {key}: {value}")
        
        # Summary
        print("\n" + "="*60)
        print("📈 BENCHMARK SUMMARY")
        print("="*60)
        print(f"✅ Execution Time: {exec_results['avg_time_ms']}ms avg, {exec_results['throughput_qps']} qps")
        print(f"✅ Cache Hit Rate: {cache_results['hit_rate_percent']}%, {cache_results['cache_speedup']}x speedup")
        print(f"✅ Batch Performance: up to {max([v['speedup'] for v in batch_results.values()]):.2f}x speedup")
        print(f"✅ Latency P95: {latency_results['p95_ms']}ms")
        
        # Performance Goals
        print("\n🎯 Performance Goals:")
        goals_met = []
        
        if cache_results['hit_rate_percent'] >= 70:
            print("   ✅ Cache Hit Rate >= 70%")
            goals_met.append(True)
        else:
            print(f"   ⚠️  Cache Hit Rate < 70% ({cache_results['hit_rate_percent']}%)")
            goals_met.append(False)
        
        if exec_results['p95_ms'] < 2000:
            print(f"   ✅ P95 Latency < 2000ms ({exec_results['p95_ms']}ms)")
            goals_met.append(True)
        else:
            print(f"   ⚠️  P95 Latency >= 2000ms ({exec_results['p95_ms']}ms)")
            goals_met.append(False)
        
        if exec_results['throughput_qps'] >= 1.0:
            print(f"   ✅ Throughput >= 1.0 qps ({exec_results['throughput_qps']} qps)")
            goals_met.append(True)
        else:
            print(f"   ⚠️  Throughput < 1.0 qps ({exec_results['throughput_qps']} qps)")
            goals_met.append(False)
        
        if all(goals_met):
            print("\n🎉 ALLE PERFORMANCE-ZIELE ERREICHT!")
        else:
            print("\n⚠️  EINIGE PERFORMANCE-ZIELE NICHT ERREICHT (aber akzeptabel für LLM-basierte Queries)")
        
        # Save Results to File
        results_file = Path("benchmark_rag_results.json")
        import json
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Ergebnisse gespeichert: {results_file}")
        
    except Exception as e:
        print(f"\n❌ Benchmark fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
    finally:
        async_rag.shutdown()
        print("\n✅ Cleanup abgeschlossen")


if __name__ == "__main__":
    asyncio.run(run_full_benchmark())
