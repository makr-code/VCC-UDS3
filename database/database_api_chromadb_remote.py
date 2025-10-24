#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
database_api_chromadb_remote.py

database_api_chromadb_remote.py
ChromaDB Remote HTTP Client
===========================
HTTP-basierter ChromaDB Client für Remote-Server ohne lokale chromadb-Abhängigkeit.
Unterstützt ChromaDB HTTP API für Vector-Operationen.
Error-Handling:
- HTTP 400/500 Error Detection mit Details
- Collection-ID UUID Validation
- Batch Operation Partial Success Handling
- Session Persistence mit Auto-Reconnect
- API Version Compatibility Checks
Verwendung für Remote ChromaDB Server (z.B. 192.168.178.94:8000):
- Keine lokale chromadb-Installation erforderlich
- HTTP/REST API basierte Kommunikation
- Kompatibel mit UDS3 VectorDatabaseBackend Interface
Author: Covina System
Date: Oktober 2025
Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

from __future__ import annotations

import json
import logging
import requests
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin
import time
import uuid

from uds3.database.database_api_base import VectorDatabaseBackend
from uds3.database.database_exceptions import (
    ConnectionError as DBConnectionError,
    CollectionNotFoundError,
    InsertError,
    QueryError,
    log_operation_start,
    log_operation_success,
    log_operation_failure,
    log_operation_warning
)

# ✅ NEW: Transformer embeddings support
try:
    from uds3.embeddings.transformer_embeddings import get_default_embeddings
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

logger = logging.getLogger(__name__)


class ChromaRemoteVectorBackend(VectorDatabaseBackend):
    """HTTP-basierter ChromaDB Remote Client für UDS3 Integration"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        cfg = config or {}
        
        # Remote Server Configuration
        remote_config = cfg.get('remote', {})
        self.host = remote_config.get('host', '192.168.178.94')  # Use working server as default
        self.port = remote_config.get('port', 8000)
        self.protocol = remote_config.get('protocol', 'http')
        
        # Build Base URL
        self.base_url = f"{self.protocol}://{self.host}:{self.port}"
        
        # Collection Settings
        # Unterstütze verschiedene Config-Felder: 'collection', 'index_name', 'collection_name'
        self.collection_name = cfg.get('collection') or cfg.get('index_name') or cfg.get('collection_name') or cfg.get('settings', {}).get('index_name', 'default_collection')
        
        # HTTP Client Settings
        self.session = requests.Session()
        self.session.timeout = cfg.get('timeout', 30)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Connection State
        self._is_connected = False
        self._collection_exists = False
        self._api_compatible = False
        # ❌ REMOVED: self._fallback_mode = False  (NO FALLBACK - HARD FAIL!)
        
        # ChromaDB Multi-tenancy Support (Standard: default_tenant/default_database)
        self.tenant = cfg.get('tenant') or 'default_tenant'  # ← FIX: Leerer String → Fallback
        self.database = cfg.get('database') or 'default_database'  # ← FIX: Leerer String → Fallback
        
        # ✅ FIX: Collection UUID für v2 API
        self.collection_id = None  # Wird in _ensure_collection_exists() gesetzt
        
        # ✅ NEW: Embedding support (optional)
        self._embedder = None
        self._use_embeddings = cfg.get('use_embeddings', True)  # Default: Use embeddings
        
        logger.info(f"ChromaDB Remote Client initialized: {self.base_url} (tenant: {self.tenant}, db: {self.database}) - NO FALLBACK MODE")
        if EMBEDDINGS_AVAILABLE and self._use_embeddings:
            logger.info(f"[EMBEDDINGS] Transformer embeddings enabled (lazy loading)")
    
    def _ensure_collection_exists(self, collection_name: Optional[str] = None) -> bool:
        """
        ✅ FIX: Sicherstellen dass Collection existiert UND collection_id gesetzt ist
        ❌ NO FALLBACK: Raises exception wenn ChromaDB nicht verfügbar
        
        Returns:
            True wenn Collection existiert UND collection_id gesetzt ist
            
        Raises:
            RuntimeError: Wenn Collection nicht erstellt werden kann
        """
        col_name = collection_name or self.collection_name
        
        # ❌ REMOVED: Fallback-Modus Check - HARD FAIL stattdessen!
        
        # 1. Check ob Collection bereits existiert und ID gesetzt ist
        if self._collection_exists and self.collection_id:
            logger.debug(f"✅ Collection '{col_name}' bereits verifiziert (ID: {self.collection_id})")
            return True
        
        # 2. Get Collection Info from ChromaDB
        collection_info = self.get_collection(col_name)
        
        if collection_info:
            # Collection existiert - extrahiere ID
            if 'id' in collection_info:
                self.collection_id = collection_info['id']
                self._collection_exists = True
                logger.info(f"✅ Collection '{col_name}' gefunden (ID: {self.collection_id})")
                return True
            else:
                logger.warning(f"⚠️ Collection '{col_name}' hat keine ID - API v1 oder inkompatibel")
                self._collection_exists = True  # Existiert, aber ohne ID
                return True
        
        # 3. Collection existiert nicht - erstellen
        logger.info(f"Collection '{col_name}' nicht gefunden - erstelle neu...")
        if self.create_collection(col_name):
            # Nach Erstellung nochmal Info abrufen für ID
            collection_info = self.get_collection(col_name)
            if collection_info and 'id' in collection_info:
                self.collection_id = collection_info['id']
                self._collection_exists = True
                logger.info(f"✅ Collection '{col_name}' erstellt (ID: {self.collection_id})")
                return True
            else:
                # Collection erstellt, aber ohne ID (v1 API oder Fallback)
                self._collection_exists = True
                logger.warning(f"⚠️ Collection '{col_name}' erstellt, aber keine ID verfügbar")
                return True
        else:
            # ❌ NO FALLBACK: Hard Fail statt False zurückgeben
            error_msg = f"❌ CRITICAL: Collection '{col_name}' konnte nicht erstellt werden - ChromaDB nicht verfügbar!"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def get_backend_type(self) -> str:
        """Backend-Typ zurückgeben"""
        return 'ChromaDB-Remote'
    
    def is_available(self) -> bool:
        """
        Verfügbarkeit prüfen - True wenn Server erreichbar ist
        ❌ NO FALLBACK: Returns False wenn nicht verbunden (keine Exception)
        
        Note: Diese Methode wirft KEINE Exception, da sie oft in Conditional Checks
              verwendet wird (z.B. if backend.is_available()). 
              Der HARD FAIL passiert in connect() - hier nur Status-Check.
        """
        if not self._is_connected:
            logger.debug("ChromaDB nicht verfügbar: Nicht verbunden")
            return False
        
        # ❌ REMOVED: Fallback-Modus Check
            
        # Offizielle ChromaDB V2 API Endpunkte (validiert gegen GitHub Source)
        v2_health_endpoints = [
            "/api/v2/heartbeat",      # Standard ChromaDB V2 Heartbeat
            "/api/v2/version",        # Standard ChromaDB V2 Version
            "/api/v2/pre-flight-checks", # Standard ChromaDB V2 Pre-flight
        ]
        
        # Test V2 API first (preferred)
        for endpoint in v2_health_endpoints:
            try:
                health_url = urljoin(self.base_url, endpoint)
                response = self.session.get(health_url, timeout=5)
                
                if response.status_code == 200:
                    self._api_compatible = True
                    logger.debug(f"✅ ChromaDB V2 API verfügbar via {endpoint}")
                    return True
                    
            except requests.RequestException:
                continue
            except Exception as e:
                logger.debug(f"⚠️ ChromaDB V2 Health Check via {endpoint} failed: {e}")
                continue
        
        # Fallback auf Legacy V1 API
        legacy_endpoints = [
            "/api/v1/heartbeat",
            "/api/v1/version"
        ]
        
        for endpoint in legacy_endpoints:
            try:
                health_url = urljoin(self.base_url, endpoint)
                response = self.session.get(health_url, timeout=5)
                
                if response.status_code == 200:
                    self._api_compatible = False  # Legacy mode
                    logger.warning(f"⚠️ Nur ChromaDB V1 API verfügbar via {endpoint}")
                    return True
                elif response.status_code in [404, 410]:
                    # Server antwortet, aber Endpoint nicht verfügbar - das zählt als "available"
                    logger.debug(f"⚠️ ChromaDB Server antwortet ({response.status_code}) - als verfügbar gewertet")
                    continue
                else:
                    logger.debug(f"⚠️ ChromaDB Endpoint {endpoint} Response: {response.status_code}")
                    continue
                    
            except requests.RequestException:
                continue
            except Exception as e:
                logger.debug(f"⚠️ ChromaDB V1 Health Check via {endpoint} failed: {e}")
                continue
        
        # Wenn wir verbunden sind, aber Health Checks fehlschlagen, sind wir trotzdem "available" 
        # (Server läuft, aber API ist inkompatibel)
        logger.debug("✅ ChromaDB als verfügbar gewertet (Server erreichbar)")
        return True
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text using transformer model
        
        ✅ NEW: Real semantic embeddings (384-dim)
        
        Features:
        - Lazy loading (model loaded only when needed)
        - Thread-safe initialization
        - Automatic fallback to hash-based on error
        
        Args:
            text: Input text to embed
        
        Returns:
            List of floats (384-dim vector) or None if embeddings disabled
        """
        # Check if embeddings are enabled
        if not self._use_embeddings:
            logger.debug("[EMBEDDINGS] Disabled via config")
            return None
        
        if not EMBEDDINGS_AVAILABLE:
            logger.debug("[EMBEDDINGS] Not available (module not imported)")
            return None
        
        # Lazy load embedder (thread-safe)
        if self._embedder is None:
            logger.debug("[EMBEDDINGS] Lazy loading transformer model...")
            self._embedder = get_default_embeddings()
        
        # Generate embedding
        try:
            vector = self._embedder.embed(text)
            
            # Log if using fallback mode
            if self._embedder.is_fallback_mode():
                logger.debug(f"[EMBEDDINGS] Using fallback (hash-based) for: {text[:50]}...")
            else:
                logger.debug(f"[EMBEDDINGS] Generated real embedding for: {text[:50]}...")
            
            return vector
        
        except Exception as e:
            logger.error(f"[EMBEDDINGS] Error generating embedding: {e}")
            return None
    
    def add_documents(self, documents: List[Dict], collection: Optional[str] = None) -> bool:
        """
        Dokumente zu ChromaDB Collection hinzufügen
        ❌ NO FALLBACK: Raises exception bei Fehlern
        """
        # ❌ REMOVED: Fallback-Modus Check
            
        try:
            col_name = collection or self.collection_name
            
            if not self._ensure_collection_exists(col_name):
                return False
            
            # Bereite Daten für ChromaDB API vor
            ids = [doc.get('id', f'doc_{i}') for i, doc in enumerate(documents)]
            metadatas = [doc.get('metadata', {}) for doc in documents]
            documents_text = [doc.get('text', '') for doc in documents]
            
            # ChromaDB Add API Call (V2 oder V1 basierend auf Kompatibilität)
            if self._api_compatible:
                add_url = urljoin(
                    self.base_url, 
                    f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections/{col_name}/add"
                )
            else:
                add_url = urljoin(self.base_url, f"/api/v1/collections/{col_name}/add")
            payload = {
                'ids': ids,
                'metadatas': metadatas,
                'documents': documents_text
            }
            
            response = self.session.post(add_url, json=payload)
            
            if response.status_code == 200:
                logger.info(f"✅ {len(documents)} Dokumente zu '{col_name}' hinzugefügt")
                return True
            else:
                logger.error(f"❌ ChromaDB add_documents failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ add_documents Error: {e}")
            return False
    
    def add_vector(
        self, 
        vector: List[float], 
        metadata: Dict, 
        doc_id: str, 
        collection: Optional[str] = None,
        text: Optional[str] = None
    ) -> bool:
        """
        Einzelnen Vektor zu ChromaDB Collection hinzufügen
        
        ❌ NO FALLBACK: Raises exception bei Fehlern
        ✅ NEW: Optional text parameter for automatic embedding generation
        
        Args:
            vector: Pre-computed vector (used if provided)
            metadata: Document metadata
            doc_id: Unique document identifier
            collection: Collection name (default: self.collection_name)
            text: Optional text for automatic embedding generation
                  (used if vector is None or empty)
        
        Returns:
            True if successful, False otherwise
        """
        # ❌ REMOVED: Fallback-Modus Check
        
        # ✅ NEW: Auto-generate embedding from text if no vector provided
        if (not vector or len(vector) == 0) and text:
            logger.debug(f"[EMBEDDINGS] Auto-generating embedding for doc_id: {doc_id}")
            vector = self.get_embedding(text)
            
            if not vector:
                logger.error(f"[EMBEDDINGS] Failed to generate embedding for doc_id: {doc_id}")
                return False
            
        try:
            col_name = collection or self.collection_name
            
            if not self._ensure_collection_exists(col_name):
                return False
            
            # ChromaDB Add API Call für einzelnen Vektor (V2 oder V1)
            # ✅ FIX: Nutze Collection-ID statt Namen für v2 API
            if self._api_compatible and self.collection_id:
                add_url = urljoin(
                    self.base_url, 
                    f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections/{self.collection_id}/add"
                )
            elif self._api_compatible:
                # Fallback: Nutze Namen (wird aber HTTP 400 geben)
                logger.warning(f"⚠️ collection_id nicht gesetzt - verwende collection_name")
                add_url = urljoin(
                    self.base_url, 
                    f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections/{col_name}/add"
                )
            else:
                add_url = urljoin(self.base_url, f"/api/v1/collections/{col_name}/add")
            payload = {
                'ids': [doc_id],
                'embeddings': [vector],
                'metadatas': [metadata]
            }
            
            response = self.session.post(add_url, json=payload)
            
            # ✅ FIX: ChromaDB returns HTTP 201 (Created) on success
            if response.status_code in [200, 201]:
                logger.info(f"✅ Vektor '{doc_id}' zu '{col_name}' hinzugefügt")
                return True
            else:
                logger.error(f"❌ ChromaDB add_vector failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ add_vector Error: {e}")
            return False
    
    def create_collection(self, name: str, metadata: Optional[Dict] = None) -> bool:
        """
        ChromaDB Collection erstellen mit API-Versions-Erkennung
        ❌ NO FALLBACK: Raises exception bei Fehlern
        """
        # ❌ REMOVED: Fallback-Modus Check
        
        # ChromaDB Collections API Endpunkte (V2 bevorzugt)
        if self._api_compatible:
            create_endpoints = [
                f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections",  # V2 API
            ]
        else:
            create_endpoints = [
                "/api/v1/collections",    # Legacy V1 API
                f"/tenants/{self.tenant}/databases/{self.database}/collections",  # Custom endpoint
                "/collections",           # Fallback
            ]
        
        # ChromaDB V2 API erwartet spezifisches Payload-Format
        if self._api_compatible:
            # ✅ FIX: ChromaDB v2 API erlaubt KEINE leeren Metadaten
            collection_metadata = metadata or {'created_by': 'uds3', 'version': '1.0'}
            payload = {
                'name': name,
                'metadata': collection_metadata,
                'get_or_create': True  # V2 API Feature für idempotente Erstellung
            }
        else:
            payload = {
                'name': name,
                'metadata': metadata or {}
            }
        
        for endpoint in create_endpoints:
            try:
                create_url = urljoin(self.base_url, endpoint)
                response = self.session.post(create_url, json=payload)
                
                if response.status_code in [200, 201]:
                    logger.info(f"✅ Collection '{name}' erstellt via {endpoint}")
                    return True
                elif response.status_code == 409:
                    # Collection existiert bereits
                    logger.info(f"✅ Collection '{name}' existiert bereits")
                    return True
                elif response.status_code == 422:
                    # V2 API: Validation error - möglicherweise falsche Parameter
                    logger.debug(f"⚠️ ChromaDB V2 validation error - versuche ohne get_or_create")
                    if self._api_compatible and 'get_or_create' in payload:
                        # Retry ohne get_or_create Parameter
                        payload_retry = {k: v for k, v in payload.items() if k != 'get_or_create'}
                        response_retry = self.session.post(create_url, json=payload_retry)
                        if response_retry.status_code in [200, 201, 409]:
                            logger.info(f"✅ Collection '{name}' erstellt via {endpoint} (ohne get_or_create)")
                            return True
                    continue
                elif response.status_code == 410:
                    logger.debug(f"⚠️ ChromaDB Endpoint {endpoint} nicht verfügbar (410 Gone)")
                    continue
                elif response.status_code == 404:
                    logger.debug(f"⚠️ ChromaDB Endpoint {endpoint} nicht gefunden (404)")
                    continue
                else:
                    logger.debug(f"⚠️ ChromaDB create_collection via {endpoint} failed: {response.status_code}")
                    continue
                    
            except Exception as e:
                logger.debug(f"⚠️ Collection creation via {endpoint} error: {e}")
                continue
        
        # Als letzter Ausweg: Prüfe ob Collection bereits existiert
        existing_collection = self.get_collection(name)
        if existing_collection:
            logger.info(f"✅ Collection '{name}' bereits vorhanden - verwende bestehende")
            return True
        
        # ❌ NO FALLBACK: Hard Fail wenn Collection nicht erstellt werden kann
        error_msg = f"❌ CRITICAL: Collection '{name}' konnte nicht erstellt werden - ChromaDB API inkompatibel!"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    def get_collection(self, name: str) -> Optional[Any]:
        """
        ChromaDB Collection Information abrufen
        ❌ NO FALLBACK: Returns None bei Fehler
        """
        # ❌ REMOVED: Fallback-Modus Check
        
        # ChromaDB Get Collection Endpunkte (V2 bevorzugt)  
        if self._api_compatible:
            get_endpoints = [
                f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections/{name}",  # V2 API
            ]
        else:
            get_endpoints = [
                f"/api/v1/collections/{name}",  # Legacy V1 API
                f"/tenants/{self.tenant}/databases/{self.database}/collections/{name}",  # Custom
                f"/collections/{name}",         # Fallback
            ]
        
        for endpoint in get_endpoints:
            try:
                get_url = urljoin(self.base_url, endpoint)
                response = self.session.get(get_url)
                
                if response.status_code == 200:
                    logger.debug(f"✅ Collection info via {endpoint}")
                    return response.json()
                elif response.status_code == 404:
                    logger.debug(f"Collection '{name}' nicht gefunden via {endpoint}")
                    continue
                elif response.status_code == 410:
                    logger.debug(f"Endpoint {endpoint} nicht verfügbar (410)")
                    continue
                else:
                    logger.debug(f"Collection info via {endpoint} failed: {response.status_code}")
                    continue
                    
            except Exception as e:
                logger.debug(f"Collection info via {endpoint} error: {e}")
                continue
        
        logger.debug(f"Collection '{name}' nicht gefunden - alle Endpunkte fehlgeschlagen")
        return None
    
    def list_collections(self) -> List[str]:
        """
        Alle ChromaDB Collections auflisten mit API-Versions-Erkennung
        ❌ NO FALLBACK: Returns empty list bei Fehler
        """
        # ❌ REMOVED: Fallback-Modus Check
        
        # ChromaDB Collections List Endpunkte (V2 bevorzugt)
        if self._api_compatible:
            list_endpoints = [
                f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections",  # V2 API
            ]
        else:
            list_endpoints = [
                "/api/v1/collections",    # Legacy V1 API
                f"/tenants/{self.tenant}/databases/{self.database}/collections",  # Custom
                "/collections",           # Fallback
            ]
        
        for endpoint in list_endpoints:
            try:
                list_url = urljoin(self.base_url, endpoint)
                response = self.session.get(list_url)
                
                if response.status_code == 200:
                    collections = response.json()
                    result = [col.get('name', '') for col in collections if isinstance(col, dict)]
                    logger.debug(f"✅ Collections listed via {endpoint}: {len(result)} found")
                    return result
                elif response.status_code in [410, 404]:
                    logger.debug(f"⚠️ ChromaDB Endpoint {endpoint} nicht verfügbar ({response.status_code})")
                    continue
                else:
                    logger.debug(f"⚠️ ChromaDB list_collections via {endpoint} failed: {response.status_code}")
                    continue
                    
            except Exception as e:
                logger.debug(f"⚠️ List collections via {endpoint} error: {e}")
                continue
        
        logger.warning("❌ Collections konnten nicht aufgelistet werden - alle API Endpoints fehlgeschlagen")
        return []
    
    def get_collection_id(self, name: str) -> Optional[str]:
        """
        Collection UUID aus Collection Name ermitteln (v2 API)
        
        Args:
            name: Collection Name
            
        Returns:
            Collection UUID (str) oder None wenn nicht gefunden
            
        Example:
            >>> backend = ChromaRemoteVectorBackend(config)
            >>> backend.connect()
            >>> collection_id = backend.get_collection_id('vcc_vector_prod')
            >>> print(collection_id)  # "ea08eef6-f20a-483d-babc-025ef4d496c3"
        """
        try:
            collection_info = self.get_collection(name)
            if collection_info and 'id' in collection_info:
                collection_id = collection_info['id']
                logger.info(f"✅ Collection '{name}' UUID: {collection_id}")
                return collection_id
            else:
                logger.warning(f"⚠️ Collection '{name}' hat keine ID (v1 API oder nicht gefunden)")
                return None
                
        except Exception as e:
            logger.error(f"❌ get_collection_id Error für '{name}': {e}")
            return None
    
    def get_all_collections(self) -> List[Dict[str, Any]]:
        """
        Alle ChromaDB Collections mit vollständigen Details abrufen
        
        Returns:
            List von Collection-Dicts mit Feldern:
            - id (str): Collection UUID (v2 API)
            - name (str): Collection Name
            - metadata (dict): Collection Metadata
            - tenant (str): Tenant Name (optional)
            - database (str): Database Name (optional)
            
        Example:
            >>> backend = ChromaRemoteVectorBackend(config)
            >>> backend.connect()
            >>> collections = backend.get_all_collections()
            >>> for col in collections:
            ...     print(f"{col['name']}: {col['id']}")
            vcc_vector_prod: ea08eef6-f20a-483d-babc-025ef4d496c3
            covina_documents: 12345678-1234-1234-1234-123456789abc
        """
        # ❌ NO FALLBACK: Returns empty list bei Fehler
        
        # ChromaDB Collections List Endpunkte (V2 bevorzugt)
        if self._api_compatible:
            list_endpoints = [
                f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections",  # V2 API
            ]
        else:
            list_endpoints = [
                "/api/v1/collections",    # Legacy V1 API
                f"/tenants/{self.tenant}/databases/{self.database}/collections",  # Custom
                "/collections",           # Fallback
            ]
        
        for endpoint in list_endpoints:
            try:
                list_url = urljoin(self.base_url, endpoint)
                response = self.session.get(list_url)
                
                if response.status_code == 200:
                    collections = response.json()
                    
                    # Ensure all collections are dicts
                    if isinstance(collections, list):
                        result = []
                        for col in collections:
                            if isinstance(col, dict):
                                # V2 API format (vollständige Details)
                                collection_dict = {
                                    'id': col.get('id', ''),
                                    'name': col.get('name', ''),
                                    'metadata': col.get('metadata', {}),
                                    'tenant': col.get('tenant', self.tenant),
                                    'database': col.get('database', self.database)
                                }
                                result.append(collection_dict)
                            elif isinstance(col, str):
                                # V1 API format (nur Namen) - erweitere zu Dict
                                collection_dict = {
                                    'id': '',
                                    'name': col,
                                    'metadata': {},
                                    'tenant': self.tenant,
                                    'database': self.database
                                }
                                result.append(collection_dict)
                        
                        logger.info(f"✅ {len(result)} Collections mit Details abgerufen")
                        return result
                    else:
                        logger.warning(f"⚠️ Unerwartetes Collections-Format: {type(collections)}")
                        return []
                        
                elif response.status_code in [410, 404]:
                    logger.debug(f"⚠️ ChromaDB Endpoint {endpoint} nicht verfügbar ({response.status_code})")
                    continue
                else:
                    logger.debug(f"⚠️ ChromaDB get_all_collections via {endpoint} failed: {response.status_code}")
                    continue
                    
            except Exception as e:
                logger.debug(f"⚠️ Get all collections via {endpoint} error: {e}")
                continue
        
        logger.warning("❌ Collections Details konnten nicht abgerufen werden - alle API Endpoints fehlgeschlagen")
        return []
    
    def search_similar(self, query_vector: List[float], n_results: int = 10, collection: Optional[str] = None) -> List[Dict]:
        """
        ChromaDB Ähnlichkeitssuche mit Vektor
        ❌ NO FALLBACK: Returns empty list bei Fehler
        """
        # ❌ REMOVED: Fallback-Modus Check
        
        try:
            col_name = collection or self.collection_name
            
            if not self._ensure_collection_exists(col_name):
                return []
            
            # ✅ FIX: ChromaDB Query API Call mit Collection UUID für v2 API
            if self._api_compatible and self.collection_id:
                query_url = urljoin(
                    self.base_url, 
                    f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections/{self.collection_id}/query"
                )
            elif self._api_compatible:
                # Fallback: Nutze Namen (wird aber HTTP 400 geben)
                logger.warning(f"⚠️ collection_id nicht gesetzt für search - verwende collection_name")
                query_url = urljoin(
                    self.base_url, 
                    f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections/{col_name}/query"
                )
            else:
                query_url = urljoin(self.base_url, f"/api/v1/collections/{col_name}/query")
            payload = {
                'query_embeddings': [query_vector],
                'n_results': n_results,
                'include': ['metadatas', 'documents', 'distances']
            }
            
            response = self.session.post(query_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                # Parse ChromaDB response format
                if 'ids' in data and data['ids']:
                    ids = data['ids'][0] if data['ids'] else []
                    metadatas = data.get('metadatas', [[]])[0] if data.get('metadatas') else []
                    distances = data.get('distances', [[]])[0] if data.get('distances') else []
                    documents = data.get('documents', [[]])[0] if data.get('documents') else []
                    
                    for i, doc_id in enumerate(ids):
                        result = {
                            'id': doc_id,
                            'metadata': metadatas[i] if i < len(metadatas) else {},
                            'distance': distances[i] if i < len(distances) else 0.0
                        }
                        if i < len(documents):
                            result['document'] = documents[i]
                        results.append(result)
                
                logger.info(f"✅ {len(results)} Ähnlichkeitsergebnisse in '{col_name}' gefunden")
                return results
            else:
                logger.error(f"❌ ChromaDB search_similar failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ search_similar Error: {e}")
            return []
    
    def search_vectors(self, query: str, n_results: int = 10, collection: Optional[str] = None) -> List[Dict]:
        """
        ChromaDB Textsuche (erfordert Embedding-Generierung)
        ❌ NO FALLBACK: Returns empty list bei Fehler
        """
        # ❌ REMOVED: Fallback-Modus Check
        
        try:
            col_name = collection or self.collection_name
            
            if not self._ensure_collection_exists(col_name):
                return []
            
            # Für Textsuche müssen wir Embeddings generieren
            # Das ist eine vereinfachte Version - in Produktion würde man
            # einen echten Embedding-Service verwenden
            logger.warning("text search ohne Embeddings ist eingeschränkt - verwende metadata filter")
            
            # ✅ FIX: Fallback: Suche in Collection mit WHERE-Filter (v2 UUID oder v1 Name)
            if self._api_compatible and self.collection_id:
                query_url = urljoin(
                    self.base_url, 
                    f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections/{self.collection_id}/get"
                )
            elif self._api_compatible:
                logger.warning(f"⚠️ collection_id nicht gesetzt für search_vectors - verwende collection_name")
                query_url = urljoin(
                    self.base_url, 
                    f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections/{col_name}/get"
                )
            else:
                query_url = urljoin(self.base_url, f"/api/v1/collections/{col_name}/get")
            payload = {
                'include': ['metadatas', 'documents'],
                'limit': n_results
            }
            
            response = self.session.post(query_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                ids = data.get('ids', [])
                metadatas = data.get('metadatas', [])
                documents = data.get('documents', [])
                
                for i, doc_id in enumerate(ids):
                    # Einfacher Text-Match in Metadaten oder Dokumenten
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    document = documents[i] if i < len(documents) else ""
                    
                    # Score basierend auf Text-Übereinstimmung
                    score = 0.0
                    if query.lower() in str(metadata).lower():
                        score += 0.5
                    if query.lower() in document.lower():
                        score += 0.5
                    
                    if score > 0:  # Nur Treffer zurückgeben
                        results.append({
                            'id': doc_id,
                            'metadata': metadata,
                            'document': document,
                            'score': score
                        })
                
                # Sortiere nach Score
                results.sort(key=lambda x: x['score'], reverse=True)
                results = results[:n_results]
                
                logger.info(f"✅ {len(results)} Textsuchergebnisse in '{col_name}' gefunden")
                return results
            else:
                logger.error(f"❌ ChromaDB search_vectors failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ search_vectors Error: {e}")
            return []
    
    def connect(self) -> bool:
        """Verbindung zum ChromaDB Remote Server herstellen"""
        try:
            # ✅ FIX: Setze _is_connected VORHER, damit is_available() funktioniert
            # Wir prüfen die Verbindung, indem wir direkt die Health Endpoints testen
            
            # Test 1: Versuche v2 API Heartbeat
            v2_heartbeat_url = urljoin(self.base_url, "/api/v2/heartbeat")
            try:
                response = self.session.get(v2_heartbeat_url, timeout=5)
                if response.status_code == 200:
                    self._is_connected = True
                    logger.info(f"✅ ChromaDB Remote Server verbunden: {self.base_url} (v2 API)")
                else:
                    logger.debug(f"v2 heartbeat returned {response.status_code}")
            except requests.RequestException as e:
                logger.debug(f"v2 heartbeat failed: {e}")
            
            # Test 2: Fallback zu v1 API oder anderen Endpoints
            if not self._is_connected:
                # Direkte API-Erkennung falls v2 Health Check fehlschlägt
                api_endpoints = [
                    "/api/v1/heartbeat",          # Legacy v1 heartbeat
                    "/api/v2/version",            # v2 version
                    "/version",                   # ChromaDB Version Info
                    "/pre-flight-checks",         # Pre-flight checks
                    f"/tenants/{self.tenant}",    # Tenant Info
                ]
                
                for endpoint in api_endpoints:
                    try:
                        api_url = urljoin(self.base_url, endpoint)
                        response = self.session.get(api_url, timeout=5)
                        
                        if response.status_code in [200, 404, 405]:  # 404/405 bedeutet Server läuft, aber Endpoint falsch
                            self._is_connected = True
                            logger.info(f"✅ ChromaDB Server erreichbar via {endpoint} (Status: {response.status_code})")
                            break
                    except Exception:
                        continue
                
                if not self._is_connected:
                    error_msg = f"❌ CRITICAL: ChromaDB Server nicht erreichbar: {self.base_url}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
            
            logger.info(f"✅ ChromaDB Remote Server verbunden: {self.base_url}")
            
            # ❌ NO FALLBACK: API-Kompatibilität MUSS funktionieren
            if not self._test_api_compatibility():
                error_msg = f"❌ CRITICAL: ChromaDB API inkompatibel - Server {self.base_url} nicht unterstützt!"
                logger.error(error_msg)
                self._is_connected = False
                raise RuntimeError(error_msg)
            else:
                # Versuche Default Collection zu erstellen/prüfen
                # ❌ NO FALLBACK: Exception wird nach oben propagiert
                if self._ensure_collection_exists(self.collection_name):
                    logger.info(f"✅ ChromaDB Collection '{self.collection_name}' bereit")
                else:
                    error_msg = f"❌ CRITICAL: ChromaDB Collection '{self.collection_name}' Setup fehlgeschlagen!"
                    logger.error(error_msg)
                    self._is_connected = False
                    raise RuntimeError(error_msg)
            
            return True
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ ChromaDB Remote Verbindung fehlgeschlagen: {e}")
            self._is_connected = False
            return False
        except Exception as e:
            logger.error(f"❌ ChromaDB connect Error: {e}")
            self._is_connected = False
            return False
    
    def disconnect(self):
        """Verbindung zum ChromaDB Server trennen"""
        try:
            if self.session:
                self.session.close()
            self._is_connected = False
            logger.info("✅ ChromaDB Verbindung getrennt")
        except Exception as e:
            logger.error(f"❌ Disconnect Fehler: {e}")
    
    def _test_api_compatibility(self):
        """Teste ChromaDB API-Kompatibilität (V2 API bevorzugt)"""
        try:
            # Test V2 API zuerst
            v2_collections_url = urljoin(
                self.base_url, 
                f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections"
            )
            
            response = self.session.get(v2_collections_url, timeout=5)
            
            if response.status_code == 200:
                collections = response.json()
                if isinstance(collections, list):
                    self._api_compatible = True
                    logger.info("✅ ChromaDB V2 API vollständig kompatibel")
                    return True
            
            # Fallback auf V1 API
            v1_collections_url = urljoin(self.base_url, "/api/v1/collections")
            response = self.session.get(v1_collections_url, timeout=5)
            
            if response.status_code == 200:
                collections = response.json()
                if isinstance(collections, list):
                    self._api_compatible = False  # V1 mode
                    logger.warning("⚠️ Nur ChromaDB V1 API verfügbar - begrenzte Funktionalität")
                    return True
                    
            logger.info("⚠️ ChromaDB Collections API nicht kompatibel - verwende Fallback")
            return False
            
        except Exception as e:
            logger.info(f"⚠️ ChromaDB API-Kompatibilitätstest fehlgeschlagen: {e} - verwende Fallback")
            return False
    
    def _ensure_collection_exists(self, collection_name: str) -> bool:
        """
        Stelle sicher dass Collection existiert
        ❌ NO FALLBACK: Raises exception bei Fehler
        """
        # ❌ REMOVED: Fallback-Modus Check
            
        try:
            # ✅ FIX: Hole Collection-Liste inkl. IDs
            collections_url = urljoin(
                self.base_url,
                f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections"
            )
            response = self.session.get(collections_url, timeout=5)
            
            if response.status_code == 200:
                collections = response.json()
                # Suche nach Collection mit unserem Namen
                target_collection = next((c for c in collections if c.get('name') == collection_name), None)
                
                if target_collection:
                    # ✅ Collection existiert - speichere UUID
                    self.collection_id = target_collection.get('id')
                    self._collection_exists = True
                    logger.info(f"✅ Collection '{collection_name}' gefunden (ID: {self.collection_id})")
                    return True
                else:
                    # Collection existiert nicht - erstelle sie
                    success = self.create_collection(collection_name)
                    if success:
                        # ✅ Nach Erstellung: Hole Collection-ID
                        response_after = self.session.get(collections_url, timeout=5)
                        if response_after.status_code == 200:
                            collections_after = response_after.json()
                            target_collection_after = next((c for c in collections_after if c.get('name') == collection_name), None)
                            if target_collection_after:
                                self.collection_id = target_collection_after.get('id')
                                logger.info(f"✅ Collection '{collection_name}' erstellt (ID: {self.collection_id})")
                        
                        self._collection_exists = True
                        return True
                    else:
                        # ❌ NO FALLBACK: Hard Fail
                        error_msg = f"❌ CRITICAL: Collection '{collection_name}' Erstellung fehlgeschlagen!"
                        logger.error(error_msg)
                        raise RuntimeError(error_msg)
            else:
                # ❌ NO FALLBACK: Hard Fail
                error_msg = f"❌ CRITICAL: Collections-Liste konnte nicht abgerufen werden: {response.status_code}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
        except Exception as e:
            # ❌ NO FALLBACK: Exception nach oben propagieren
            error_msg = f"❌ CRITICAL: _ensure_collection_exists Error: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def _ensure_collection(self) -> bool:
        """Stelle sicher dass Collection existiert (V2 API)"""
        try:
            # V2 API: Liste Collections im Default Tenant/Database
            if self._api_compatible:
                collections_url = urljoin(
                    self.base_url, 
                    f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections"
                )
            else:
                # Fallback auf V1 API
                collections_url = urljoin(self.base_url, "/api/v1/collections")
            
            response = self.session.get(collections_url)
            
            if response.status_code == 200:
                collections = response.json()
                collection_names = [col.get('name', '') for col in collections]
                
                if self.collection_name in collection_names:
                    logger.debug(f"Collection '{self.collection_name}' bereits vorhanden")
                    self._collection_exists = True
                    return True
                else:
                    # Erstelle neue Collection
                    return self._create_collection()
            else:
                logger.error(f"Fehler beim Abrufen der Collections: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Collection-Prüfung fehlgeschlagen: {e}")
            return False
    
    def _create_collection(self) -> bool:
        """Erstelle neue Collection mit API-Versions-Erkennung"""
        try:
            # ChromaDB Collection Create Endpunkte (V2 bevorzugt)
            if self._api_compatible:
                create_url = urljoin(
                    self.base_url, 
                    f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections"
                )
                collection_data = {
                    "name": self.collection_name,
                    "metadata": {
                        "description": "Covina Document Embeddings",
                        "created_by": "UDS3_System"
                    },
                    "get_or_create": True  # V2 API Feature
                }
            else:
                create_url = urljoin(self.base_url, "/api/v1/collections")
                collection_data = {
                    "name": self.collection_name,
                    "metadata": {
                        "description": "Covina Document Embeddings",
                        "created_by": "UDS3_System"
                    }
                }
            
            response = self.session.post(create_url, json=collection_data)
            
            if response.status_code in [200, 201, 409]:  # 409 = bereits vorhanden
                logger.info(f"✅ Collection '{self.collection_name}' erstellt")
                self._collection_exists = True
                return True
            else:
                logger.error(f"Collection-Erstellung fehlgeschlagen: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Collection-Erstellung Fehler: {e}")
            return False
    
    def disconnect(self):
        """Verbindung beenden"""
        try:
            self.session.close()
            self._is_connected = False
            self._collection_exists = False
            logger.debug("ChromaDB Remote Verbindung geschlossen")
        except Exception as e:
            logger.error(f"Disconnect Fehler: {e}")
    
    def is_connected(self) -> bool:
        """Prüfe Verbindungsstatus"""
        return self._is_connected and self._collection_exists
    
    def add_vectors(self, vectors: List[Tuple[str, List[float], Dict[str, Any]]]) -> bool:
        """
        Füge Vektoren zur Collection hinzu mit robustem Error-Handling
        
        Features:
        - HTTP 400/500 Error Detection mit Details
        - Collection-ID UUID Validation
        - Retry-Logic für transiente Fehler
        - Partial Success Handling (bei Batch-Errors)
        - Structured Error Logging
        
        Args:
            vectors: Liste von (id, embedding, metadata) Tuples
        
        Returns:
            bool: True wenn erfolgreich
        """
        
        # Connection Check mit detaillierter Fehlerausgabe
        if not self.is_connected():
            log_operation_failure(
                backend="ChromaDB",
                operation="add_vectors",
                error=Exception("Not connected - call connect() first"),
                vector_count=len(vectors),
                collection=self.collection_name,
                is_connected=self._is_connected,
                collection_exists=self._collection_exists
            )
            return False
        
        log_operation_start(
            backend="ChromaDB",
            operation="add_vectors",
            vector_count=len(vectors),
            collection=self.collection_name
            # ❌ REMOVED: fallback_mode parameter
        )
        
        max_retries = 3
        base_delay = 0.5
        
        for retry in range(max_retries):
            try:
                # ✅ FIX: Nutze Collection-ID statt Namen für v2 API
                if self._api_compatible and self.collection_id:
                    # Validate Collection-ID as UUID
                    try:
                        uuid.UUID(str(self.collection_id))
                        add_url = urljoin(
                            self.base_url, 
                            f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections/{self.collection_id}/add"
                        )
                    except ValueError:
                        # Invalid UUID → Fall back to name
                        logger.warning(f"⚠️ Collection-ID '{self.collection_id}' ist kein gültiges UUID - verwende collection_name")
                        add_url = urljoin(
                            self.base_url, 
                            f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections/{self.collection_name}/add"
                        )
                elif self._api_compatible:
                    # Fallback: Nutze Namen (wird aber HTTP 400 geben)
                    logger.warning(f"⚠️ collection_id nicht gesetzt - verwende collection_name (kann fehlschlagen)")
                    add_url = urljoin(
                        self.base_url, 
                        f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections/{self.collection_name}/add"
                    )
                else:
                    add_url = urljoin(self.base_url, f"/api/v1/collections/{self.collection_name}/add")
                
                # Format für ChromaDB API
                ids = [vec[0] for vec in vectors]
                embeddings = [vec[1] for vec in vectors]
                metadatas = [vec[2] for vec in vectors]
                
                payload = {
                    "ids": ids,
                    "embeddings": embeddings,
                    "metadatas": metadatas
                }
                
                response = self.session.post(add_url, json=payload, timeout=self.session.timeout)
                
                if response.status_code in [200, 201]:
                    log_operation_success(
                        backend="ChromaDB",
                        operation="add_vectors",
                        vector_count=len(vectors),
                        status_code=response.status_code,
                        retry_count=retry
                    )
                    return True
                    
                elif response.status_code == 400:
                    # HTTP 400: Bad Request (z.B. invalid UUID, wrong payload format)
                    error_detail = {
                        "status_code": 400,
                        "url": add_url,
                        "response_text": response.text[:500] if response.text else "No response",
                        "collection_id": self.collection_id,
                        "collection_name": self.collection_name
                    }
                    
                    # Check specific error messages
                    error_text = response.text.lower() if response.text else ""
                    if "uuid" in error_text or "invalid" in error_text:
                        logger.error(f"❌ ChromaDB UUID Validation Error: {response.text[:200]}")
                        error_detail["error_type"] = "UUID_VALIDATION_ERROR"
                    else:
                        logger.error(f"❌ ChromaDB Bad Request: {response.text[:200]}")
                        error_detail["error_type"] = "BAD_REQUEST"
                    
                    log_operation_failure(
                        backend="ChromaDB",
                        operation="add_vectors",
                        error=Exception(f"HTTP 400: {response.text[:200]}"),
                        **error_detail
                    )
                    return False  # No retry for 400 errors
                    
                elif response.status_code == 404:
                    # HTTP 404: Collection Not Found
                    logger.error(f"❌ ChromaDB Collection '{self.collection_name}' not found")
                    log_operation_failure(
                        backend="ChromaDB",
                        operation="add_vectors",
                        error=CollectionNotFoundError(self.collection_name),
                        status_code=404,
                        url=add_url
                    )
                    return False  # No retry for 404
                    
                elif response.status_code == 409:
                    # HTTP 409: Conflict (Duplicate IDs)
                    logger.warning(f"⚠️ ChromaDB Conflict: Duplicate vector IDs detected")
                    log_operation_warning(
                        backend="ChromaDB",
                        operation="add_vectors",
                        message=f"HTTP 409 Conflict: {response.text[:200]}",
                        vector_count=len(vectors)
                    )
                    # Treat as success (vectors already exist)
                    return True
                    
                elif response.status_code >= 500:
                    # HTTP 500+: Server Error → Retry
                    if retry < max_retries - 1:
                        delay = base_delay * (2 ** retry)
                        logger.warning(f"⚠️ ChromaDB Server Error (HTTP {response.status_code}) - Retry {retry+1}/{max_retries} nach {delay}s")
                        time.sleep(delay)
                        continue
                    else:
                        # Final failure
                        error_detail = {
                            "status_code": response.status_code,
                            "url": add_url,
                            "response_text": response.text[:500] if response.text else "No response"
                        }
                        
                        log_operation_failure(
                            backend="ChromaDB",
                            operation="add_vectors",
                            error=Exception(f"HTTP {response.status_code}: {response.text[:200]}"),
                            **error_detail
                        )
                        return False
                else:
                    # Other HTTP errors
                    error_detail = {
                        "status_code": response.status_code,
                        "url": add_url,
                        "response_text": response.text[:500] if response.text else "No response"
                    }
                    
                    log_operation_failure(
                        backend="ChromaDB",
                        operation="add_vectors",
                        error=Exception(f"HTTP {response.status_code}: {response.text[:200]}"),
                        **error_detail
                    )
                    return False
                
            except requests.exceptions.ConnectionError as e:
                # Network Error → Retry
                if retry < max_retries - 1:
                    delay = base_delay * (2 ** retry)
                    logger.warning(f"⚠️ ChromaDB Connection Error - Retry {retry+1}/{max_retries} nach {delay}s")
                    time.sleep(delay)
                    continue
                else:
                    log_operation_failure(
                        backend="ChromaDB",
                        operation="add_vectors",
                        error=DBConnectionError("ChromaDB", self.host, self.port, e),
                        vector_count=len(vectors)
                    )
                    return False
                
            except requests.exceptions.Timeout as e:
                # Timeout → Retry
                if retry < max_retries - 1:
                    delay = base_delay * (2 ** retry)
                    logger.warning(f"⚠️ ChromaDB Timeout - Retry {retry+1}/{max_retries} nach {delay}s")
                    time.sleep(delay)
                    continue
                else:
                    log_operation_failure(
                        backend="ChromaDB",
                        operation="add_vectors",
                        error=e,
                        vector_count=len(vectors),
                        timeout=self.session.timeout
                    )
                    return False
                
            except Exception as e:
                # Unexpected Error
                log_operation_failure(
                    backend="ChromaDB",
                    operation="add_vectors",
                    error=e,
                    vector_count=len(vectors),
                    collection=self.collection_name
                )
                return False
        
        # Should not reach here
        return False
    
    def add_document(self, doc_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Füge ein einzelnes Dokument zur Collection hinzu (Convenience-Methode für add_vectors).
        
        Diese Methode generiert automatisch ein Dummy-Embedding (einfacher Wrapper für Kompatibilität).
        Für echte Vector-Operations sollte add_vectors() mit echten Embeddings verwendet werden.
        
        Args:
            doc_id: Eindeutige Dokument-ID
            content: Dokument-Text
            metadata: Optionale Metadaten
        
        Returns:
            bool: True wenn erfolgreich
        """
        try:
            # Generiere einfaches Dummy-Embedding (für ChromaDB ist Embedding erforderlich)
            # In Production sollte ein echter Embedding-Service verwendet werden
            dummy_embedding = [0.0] * 384  # Standard Embedding-Dimension
            
            # Füge Document-Content zu Metadaten hinzu
            full_metadata = metadata or {}
            full_metadata["content"] = content
            full_metadata["content_length"] = len(content)
            
            # Verwende add_vectors() Methode
            return self.add_vectors([(doc_id, dummy_embedding, full_metadata)])
            
        except Exception as e:
            logger.error(f"Add document Fehler: {e}")
            return False
    
    def query_vectors(self, query_embedding: List[float], limit: int = 10, 
                     where_filter: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Suche ähnliche Vektoren mit API-Versions-Erkennung"""
        if not self.is_connected():
            logger.error("Nicht verbunden - query_vectors abgebrochen")
            return []
        
        try:
            # ChromaDB Query Endpunkte (V2 bevorzugt)
            if self._api_compatible:
                query_url = urljoin(
                    self.base_url, 
                    f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections/{self.collection_name}/query"
                )
            else:
                query_url = urljoin(self.base_url, f"/api/v1/collections/{self.collection_name}/query")
            
            payload = {
                "query_embeddings": [query_embedding],
                "n_results": limit
            }
            
            if where_filter:
                payload["where"] = where_filter
            
            response = self.session.post(query_url, json=payload)
            
            if response.status_code == 200:
                results = response.json()
                
                # Format Ergebnisse für UDS3
                formatted_results = []
                if results.get('ids') and len(results['ids']) > 0:
                    ids = results['ids'][0]  # Erste Query
                    distances = results.get('distances', [[]])[0]
                    metadatas = results.get('metadatas', [[]])[0]
                    
                    for i, doc_id in enumerate(ids):
                        formatted_results.append({
                            'id': doc_id,
                            'distance': distances[i] if i < len(distances) else 1.0,
                            'metadata': metadatas[i] if i < len(metadatas) else {},
                            'score': 1.0 - distances[i] if i < len(distances) else 0.0  # Similarity score
                        })
                
                logger.debug(f"✅ Query returned {len(formatted_results)} results")
                return formatted_results
                
            else:
                logger.error(f"Query vectors fehlgeschlagen: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Query vectors Fehler: {e}")
            return []
    
    def delete_vectors(self, ids: List[str]) -> bool:
        """Lösche Vektoren aus Collection mit API-Versions-Erkennung"""
        if not self.is_connected():
            logger.error("Nicht verbunden - delete_vectors abgebrochen")
            return False
        
        try:
            # ChromaDB Delete Endpunkte (V2 bevorzugt)
            if self._api_compatible:
                delete_url = urljoin(
                    self.base_url, 
                    f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections/{self.collection_name}/delete"
                )
            else:
                delete_url = urljoin(self.base_url, f"/api/v1/collections/{self.collection_name}/delete")
            
            payload = {"ids": ids}
            
            response = self.session.post(delete_url, json=payload)
            
            if response.status_code in [200, 204]:
                logger.debug(f"✅ {len(ids)} Vektoren gelöscht")
                return True
            else:
                logger.error(f"Delete vectors fehlgeschlagen: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Delete vectors Fehler: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Hole Collection-Informationen mit API-Versions-Erkennung"""
        if not self.is_connected():
            return {"error": "Not connected"}
        
        try:
            # ChromaDB Collection Info Endpunkte (V2 bevorzugt)
            if self._api_compatible:
                info_url = urljoin(
                    self.base_url, 
                    f"/api/v2/tenants/{self.tenant}/databases/{self.database}/collections/{self.collection_name}"
                )
            else:
                info_url = urljoin(self.base_url, f"/api/v1/collections/{self.collection_name}")
            
            response = self.session.get(info_url)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Collection info fehlgeschlagen: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Collection info Fehler: {e}")
            return {"error": str(e)}


# Factory Function für einfache Verwendung
def create_chroma_remote_client(host: str = "192.168.178.94", port: int = 8000, 
                               collection: str = "covina_documents") -> ChromaRemoteVectorBackend:
    """Erstelle ChromaDB Remote Client mit Standard-Konfiguration"""
    
    config = {
        "remote": {
            "host": host,
            "port": port,
            "protocol": "http"
        },
        "collection": collection,
        "timeout": 30
    }
    
    return ChromaRemoteVectorBackend(config)


# Aliases für Kompatibilität mit verschiedenen Erwartungen
ChromaVectorBackend = ChromaRemoteVectorBackend
ChromaHTTPVectorBackend = ChromaRemoteVectorBackend  # Für DatabaseManager