#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
__init__.py

__init__.py
Database adapters and utilities package.
# Database Manager & Extensions
from uds3.database.database_manager import DatabaseManager
from uds3.database.extensions import (
DatabaseManagerExtensions,
create_extended_database_manager,
ExtensionStatus
)
# Database Adapters (with batch operations support)
from uds3.database.database_api_postgresql import PostgreSQLRelationalBackend
from uds3.database.database_api_neo4j import Neo4jGraphBackend
from uds3.database.database_api_couchdb import CouchDBAdapter
from uds3.database.database_api_chromadb_remote import ChromaRemoteVectorBackend
__all__ = [
# Manager
'DatabaseManager',
'DatabaseManagerExtensions',
'create_extended_database_manager',
'ExtensionStatus',
# Adapters (with batch operations)
'PostgreSQLRelationalBackend',
'Neo4jGraphBackend',
'CouchDBAdapter',
'ChromaRemoteVectorBackend',
]

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

# Database Manager & Extensions
from uds3.database.database_manager import DatabaseManager
from uds3.database.extensions import (
    DatabaseManagerExtensions,
    create_extended_database_manager,
    ExtensionStatus
)

# Database Adapters (with batch operations support)
from uds3.database.database_api_postgresql import PostgreSQLRelationalBackend
from uds3.database.database_api_neo4j import Neo4jGraphBackend
from uds3.database.database_api_couchdb import CouchDBAdapter
from uds3.database.database_api_chromadb_remote import ChromaRemoteVectorBackend

__all__ = [
    # Manager
    'DatabaseManager',
    'DatabaseManagerExtensions',
    'create_extended_database_manager',
    'ExtensionStatus',
    # Adapters (with batch operations)
    'PostgreSQLRelationalBackend',
    'Neo4jGraphBackend',
    'CouchDBAdapter',
    'ChromaRemoteVectorBackend',
]
