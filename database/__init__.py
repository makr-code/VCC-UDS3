#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
__init__.py

__init__.py
Database adapters and utilities package.

v1.6.0 Features:
- Multi-Hop Reasoning for legal hierarchy traversal

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

# Multi-Hop Reasoning (v1.6.0)
MULTI_HOP_AVAILABLE = False
try:
    from database.multi_hop import (
        MultiHopReasoner,
        LegalLevel,
        RelationType,
        LegalNode,
        LegalPath,
        TraversalResult,
        CypherTemplates,
        create_multi_hop_reasoner,
        check_multi_hop_available,
    )
    MULTI_HOP_AVAILABLE = check_multi_hop_available()
except ImportError:
    # Multi-hop reasoning feature is optional; ignore if not available.
    # If the import fails, MULTI_HOP_AVAILABLE remains False.
    # Optionally, log the import failure for debugging:
    # import logging; logging.warning("Multi-hop reasoning feature not available (ImportError).")

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
    # Multi-Hop Reasoning (v1.6.0)
    'MultiHopReasoner',
    'LegalLevel',
    'RelationType',
    'LegalNode',
    'LegalPath',
    'TraversalResult',
    'CypherTemplates',
    'create_multi_hop_reasoner',
    'check_multi_hop_available',
    'MULTI_HOP_AVAILABLE',
]
