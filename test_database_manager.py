#!/usr/bin/env python3
"""Test DatabaseManager Config Loading"""

from database.config import DatabaseManager

print("=== DatabaseManager Config Test ===\n")

mgr = DatabaseManager()
print(f"Total Databases: {len(mgr.databases)}\n")

for db in mgr.databases:
    print(f"{db.db_type.value:12} | {db.backend.value:12} | {db.host:20} | {db.port}")

print("\n=== Expected Production Config ===")
print("vector       | chromadb     | 192.168.178.94       | 8000")
print("graph        | neo4j        | 192.168.178.94       | 7687")
print("relational   | postgresql   | 192.168.178.94       | 5432")
print("file         | couchdb      | 192.168.178.94       | 32770")
