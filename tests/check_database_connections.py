"""
Database Connection Checker for UDS3
Tests connectivity to all 4 databases before running benchmarks.

Usage:
    python tests/check_database_connections.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def check_postgresql():
    """Check PostgreSQL connection."""
    print("\n📊 Testing PostgreSQL...")
    try:
        import psycopg2
        
        # Direct connection with hardcoded config
        conn = psycopg2.connect(
            host='192.168.178.94',
            port=5432,
            user='postgres',
            password='postgres',
            database='postgres'
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
        table_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"   ✅ Connected: 192.168.178.94:5432")
        print(f"   ✅ Version: {version[:50]}...")
        print(f"   ✅ Tables: {table_count}")
        return True
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False


def check_chromadb():
    """Check ChromaDB connection."""
    print("\n🔍 Testing ChromaDB...")
    try:
        import requests
        
        url = "http://192.168.178.94:8000/api/v1/heartbeat"
        
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            print(f"   ✅ Connected: 192.168.178.94:8000")
            
            # Get collections
            collections_url = "http://192.168.178.94:8000/api/v1/collections"
            coll_response = requests.get(collections_url, timeout=5)
            
            if coll_response.status_code == 200:
                collections = coll_response.json()
                print(f"   ✅ Collections: {len(collections)}")
            
            return True
        else:
            print(f"   ❌ Connection failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False


def check_neo4j():
    """Check Neo4j connection."""
    print("\n🕸️  Testing Neo4j...")
    try:
        from neo4j import GraphDatabase
        
        driver = GraphDatabase.driver(
            "bolt://192.168.178.94:7687",
            auth=("neo4j", "neo4j")
        )
        
        with driver.session() as session:
            result = session.run("CALL dbms.components() YIELD name, versions, edition")
            record = result.single()
            
            # Count nodes
            node_count = session.run("MATCH (n) RETURN count(n) as count").single()['count']
            
        driver.close()
        
        print(f"   ✅ Connected: bolt://192.168.178.94:7687")
        print(f"   ✅ Edition: {record['edition']}")
        print(f"   ✅ Nodes: {node_count}")
        return True
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False


def check_couchdb():
    """Check CouchDB connection."""
    print("\n📄 Testing CouchDB...")
    try:
        import requests
        
        url = "http://192.168.178.94:5984/"
        
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Connected: 192.168.178.94:5984")
            print(f"   ✅ Version: {data.get('version', 'unknown')}")
            
            # Get databases
            dbs_url = "http://192.168.178.94:5984/_all_dbs"
            dbs_response = requests.get(dbs_url, timeout=5)
            
            if dbs_response.status_code == 200:
                databases = dbs_response.json()
                print(f"   ✅ Databases: {len(databases)}")
            
            return True
        else:
            print(f"   ❌ Connection failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False


def main():
    """Check all database connections."""
    print("=" * 80)
    print("UDS3 DATABASE CONNECTION CHECKER")
    print("=" * 80)
    
    results = {
        'PostgreSQL': check_postgresql(),
        'ChromaDB': check_chromadb(),
        'Neo4j': check_neo4j(),
        'CouchDB': check_couchdb()
    }
    
    print("\n" + "=" * 80)
    print("CONNECTION SUMMARY")
    print("=" * 80)
    
    for db, status in results.items():
        icon = "✅" if status else "❌"
        status_text = "CONNECTED" if status else "FAILED"
        print(f"{icon} {db}: {status_text}")
    
    connected = sum(results.values())
    total = len(results)
    
    print(f"\n📊 Total: {connected}/{total} databases connected")
    
    if connected == total:
        print("✅ All databases ready for testing!")
        return 0
    else:
        print(f"⚠️  {total - connected} database(s) unavailable")
        print("\n💡 To start databases:")
        if not results['PostgreSQL']:
            print("   PostgreSQL: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres")
        if not results['ChromaDB']:
            print("   ChromaDB: docker run -d -p 8000:8000 chromadb/chroma")
        if not results['Neo4j']:
            print("   Neo4j: docker run -d -p 7687:7687 -e NEO4J_AUTH=neo4j/neo4j neo4j")
        if not results['CouchDB']:
            print("   CouchDB: docker run -d -p 5984:5984 -e COUCHDB_USER=admin -e COUCHDB_PASSWORD=admin couchdb")
        return 1
    
    print("=" * 80)


if __name__ == "__main__":
    sys.exit(main())
