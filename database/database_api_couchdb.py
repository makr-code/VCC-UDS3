#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
database_api_couchdb.py

database_api_couchdb.py
CouchDB adapter - lightweight Document DB adapter using `couchdb` package.
Provides full CRUD: create_document, get_document, update_document, delete_document, query.
Config keys:
- url: http://user:pass@host:5984
- db: database name
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

import logging
import datetime
import warnings
from pathlib import Path
from typing import Dict, Any, List, Optional

# Unterdrücke pkg_resources Deprecation Warning von CouchDB Package
warnings.filterwarnings('ignore', message='.*pkg_resources is deprecated.*')

import couchdb  # pip install CouchDB

from uds3.database.database_api_base import DatabaseBackend

logger = logging.getLogger(__name__)


class CouchDBAdapter(DatabaseBackend):
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        cfg = config or {}
        
        # Build URL from components if not provided directly
        if 'url' in cfg:
            self.url = cfg['url']
        else:
            # Build from host, port, username, password
            host = cfg.get('host', 'localhost')
            port = cfg.get('port', 5984)
            username = cfg.get('username', '')
            password = cfg.get('password', '')
            protocol = cfg.get('protocol', 'http')
            
            if username and password:
                self.url = f"{protocol}://{username}:{password}@{host}:{port}"
            else:
                self.url = f"{protocol}://{host}:{port}"
        
        self.db_name = cfg.get('db', cfg.get('database'))
        self.server: Optional[couchdb.Server] = None
        self.db: Optional[couchdb.Database] = None
        self._is_connected = False

    def connect(self) -> bool:
        try:
            self.server = couchdb.Server(self.url)
            # Ensure DB exists
            if self.db_name not in self.server:
                self.server.create(self.db_name)
            self.db = self.server[self.db_name]
            self._is_connected = True
            logger.info('CouchDB connected %s/%s', self.url, self.db_name)
            return True
        except Exception as exc:
            logger.exception('CouchDB connect failed: %s', exc)
            self.server = None
            self.db = None
            self._is_connected = False
            return False

    def disconnect(self):
        self.server = None
        self.db = None
        self._is_connected = False

    def is_available(self) -> bool:
        return bool(self._is_connected and self.db is not None)

    def get_backend_type(self) -> str:
        return 'couchdb'

    # CRUD
    def create_document(self, doc: Dict[str, Any], doc_id: Optional[str] = None) -> str:
        """
        Create document in CouchDB with conflict handling.
        
        If document already exists:
        - Returns existing doc_id (idempotent behavior for SAGA Pattern)
        - Logs warning instead of raising exception
        
        Args:
            doc: Document to create
            doc_id: Optional document ID (if None, CouchDB generates UUID)
        
        Returns:
            Document ID (str)
        
        Raises:
            RuntimeError: If CouchDB not connected
            Exception: For non-conflict CouchDB errors
        """
        if not self.db:
            raise RuntimeError('CouchDB not connected')
        
        try:
            if doc_id:
                # Check if document already exists (idempotency check)
                try:
                    existing_doc = self.db[doc_id]
                    # Document exists → Idempotent behavior (SAGA retry safety)
                    import logging
                    logger = logging.getLogger("uds3.database.couchdb")
                    logger.warning(f"⚠️ CouchDB: Document {doc_id} already exists (idempotent skip)")
                    return doc_id
                except Exception:
                    # Document not found → Create new
                    pass
                
                # Create document with specified ID
                self.db[doc_id] = doc
                return doc_id
            else:
                # Auto-generated ID
                docid, _rev = self.db.save(doc)
                return docid
                
        except Exception as e:
            # Check if ResourceConflict (HTTP 409)
            error_str = str(e)
            if 'conflict' in error_str.lower() or '409' in error_str:
                # Document exists → Return doc_id (idempotent)
                import logging
                logger = logging.getLogger("uds3.database.couchdb")
                logger.warning(f"⚠️ CouchDB Conflict: Document {doc_id} exists (idempotent return)")
                return doc_id if doc_id else None
            else:
                # Other CouchDB error → Re-raise
                raise

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        if not self.db:
            raise RuntimeError('CouchDB not connected')
        try:
            return dict(self.db[doc_id])
        except Exception:
            return None

    def update_document(self, doc_id: str, changes: Dict[str, Any]) -> bool:
        if not self.db:
            raise RuntimeError('CouchDB not connected')
        try:
            doc = self.db[doc_id]
            for k, v in changes.items():
                doc[k] = v
            self.db.save(doc)
            return True
        except Exception as exc:
            logger.exception('CouchDB update failed: %s', exc)
            return False

    def delete_document(self, doc_id: str) -> bool:
        if not self.db:
            raise RuntimeError('CouchDB not connected')
        try:
            doc = self.db[doc_id]
            self.db.delete(doc)
            return True
        except Exception as exc:
            logger.exception('CouchDB delete failed: %s', exc)
            return False

    def query(self, map_fun: str = None, reduce_fun: str = None, **opts) -> List[Dict[str, Any]]:
        """Run a temporary view query (map/reduce) - simplistic helper."""
        if not self.db:
            raise RuntimeError('CouchDB not connected')
        try:
            # Temporary views are discouraged; expect users to define design docs.
            result = []
            if map_fun:
                for row in self.db.query(map_fun, reduce=bool(reduce_fun), **opts):
                    result.append(dict(row))
            return result
        except Exception as exc:
            logger.exception('CouchDB query failed: %s', exc)
            return []

    # File Storage Interface (for saga_crud compatibility)
    def store_asset(
        self,
        source_path: Optional[str] = None,
        data: Optional[bytes] = None,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store a file asset in CouchDB as an attachment.
        Returns dict with asset_id, file_storage_id, and metadata.
        """
        if not self.db:
            raise RuntimeError('CouchDB not connected')
        
        try:
            # Generate unique asset ID
            import uuid
            asset_id = str(uuid.uuid4())
            
            # Read data from source_path if not provided
            if data is None and source_path:
                with open(source_path, 'rb') as f:
                    data = f.read()
            
            if data is None:
                raise ValueError("Either 'data' or 'source_path' must be provided")
            
            # Determine filename
            if not filename:
                if source_path:
                    filename = str(Path(source_path).name)
                else:
                    filename = 'document.bin'
            
            # Create document with metadata
            doc_data = {
                '_id': asset_id,
                'filename': filename,
                'metadata': metadata or {},
                'created_at': str(datetime.datetime.now())
            }
            
            # Save document first
            self.db[asset_id] = doc_data
            
            # Attach file data
            self.db.put_attachment(
                self.db[asset_id],
                data,
                filename=filename,
                content_type='application/octet-stream'
            )
            
            logger.info(f'Stored asset {asset_id} with filename {filename}')
            
            return {
                'success': True,
                'asset_id': asset_id,
                'file_storage_id': asset_id,
                'filename': filename,
                'size': len(data),
                'metadata': metadata
            }
            
        except Exception as exc:
            logger.exception(f'CouchDB store_asset failed: {exc}')
            raise RuntimeError(f'Failed to store asset: {exc}')

    def delete_asset(self, asset_id: str) -> bool:
        """
        Delete a file asset from CouchDB.
        Compatible with saga_crud file_delete().
        """
        return self.delete_document(asset_id)

    # ================================================================
    # BATCH OPERATIONS
    # ================================================================
    
    def batch_update(
        self,
        updates: List[Dict[str, Any]],
        mode: str = "partial"
    ) -> Dict[str, Any]:
        """
        Batch update documents using CouchDB _bulk_docs API
        
        Args:
            updates: List of update dicts with:
                - document_id: Document ID to update
                - fields: Dict of fields to update
            mode: Update mode ("partial" or "full")
            
        Returns:
            Dict with keys: success, updated, failed, errors
        """
        if not updates or not self.is_available():
            return {"success": True, "updated": 0, "failed": 0, "errors": []}
        
        try:
            bulk_docs = []
            errors = []
            
            for update in updates:
                doc_id = update.get("document_id")
                fields = update.get("fields", {})
                
                try:
                    # Get existing document (need _rev for update)
                    if doc_id in self.db:
                        doc = self.db[doc_id]
                        
                        if mode == "partial":
                            # Merge fields
                            doc.update(fields)
                        else:
                            # Replace (keep _id and _rev)
                            doc = {"_id": doc["_id"], "_rev": doc["_rev"]}
                            doc.update(fields)
                        
                        bulk_docs.append(doc)
                    else:
                        errors.append({"document_id": doc_id, "error": "Document not found"})
                        
                except Exception as e:
                    errors.append({"document_id": doc_id, "error": str(e)})
            
            # Execute bulk update
            if bulk_docs:
                results = self.db.update(bulk_docs)
                
                # Count successes and failures
                updated = sum(1 for success, doc_id, rev_or_error in results if success)
                failed = len(bulk_docs) - updated
                
                # Collect errors from bulk operation
                for success, doc_id, rev_or_error in results:
                    if not success:
                        errors.append({"document_id": doc_id, "error": str(rev_or_error)})
                
                logger.info(f"✅ CouchDB batch updated {updated}/{len(updates)} documents")
                
                return {
                    "success": updated > 0,
                    "updated": updated,
                    "failed": failed + len(errors),
                    "errors": errors
                }
            else:
                return {
                    "success": False,
                    "updated": 0,
                    "failed": len(updates),
                    "errors": errors
                }
            
        except Exception as e:
            logger.error(f"❌ CouchDB batch update failed: {e}")
            return {
                "success": False,
                "updated": 0,
                "failed": len(updates),
                "errors": [{"error": str(e)}]
            }
    
    def batch_delete(
        self,
        document_ids: List[str],
        soft_delete: bool = True
    ) -> Dict[str, Any]:
        """
        Batch delete documents using CouchDB _bulk_docs API
        
        Args:
            document_ids: List of document IDs to delete
            soft_delete: If True, mark as deleted; if False, remove documents
            
        Returns:
            Dict with keys: success, deleted, failed, errors
        """
        if not document_ids or not self.is_available():
            return {"success": True, "deleted": 0, "failed": 0, "errors": []}
        
        try:
            bulk_docs = []
            errors = []
            
            for doc_id in document_ids:
                try:
                    if doc_id in self.db:
                        doc = self.db[doc_id]
                        
                        if soft_delete:
                            # Soft delete: Set deleted flag
                            doc["deleted"] = True
                            bulk_docs.append(doc)
                        else:
                            # Hard delete: Set _deleted flag for CouchDB
                            bulk_docs.append({
                                "_id": doc["_id"],
                                "_rev": doc["_rev"],
                                "_deleted": True
                            })
                    else:
                        errors.append({"document_id": doc_id, "error": "Document not found"})
                        
                except Exception as e:
                    errors.append({"document_id": doc_id, "error": str(e)})
            
            # Execute bulk delete
            if bulk_docs:
                results = self.db.update(bulk_docs)
                
                # Count successes
                deleted = sum(1 for success, doc_id, rev_or_error in results if success)
                failed = len(bulk_docs) - deleted
                
                # Collect errors
                for success, doc_id, rev_or_error in results:
                    if not success:
                        errors.append({"document_id": doc_id, "error": str(rev_or_error)})
                
                delete_type = "Soft deleted" if soft_delete else "Hard deleted"
                logger.info(f"✅ CouchDB {delete_type} {deleted}/{len(document_ids)} documents")
                
                return {
                    "success": deleted > 0,
                    "deleted": deleted,
                    "failed": failed + len(errors),
                    "errors": errors
                }
            else:
                return {
                    "success": False,
                    "deleted": 0,
                    "failed": len(document_ids),
                    "errors": errors
                }
            
        except Exception as e:
            logger.error(f"❌ CouchDB batch delete failed: {e}")
            return {
                "success": False,
                "deleted": 0,
                "failed": len(document_ids),
                "errors": [{"error": str(e)}]
            }
    
    def batch_upsert(
        self,
        documents: List[Dict[str, Any]],
        conflict_resolution: str = "update"
    ) -> Dict[str, Any]:
        """
        Batch upsert documents using CouchDB _bulk_docs API
        
        Args:
            documents: List of document dicts with:
                - document_id: Document ID
                - fields: Dict of fields to insert/update
            conflict_resolution: How to handle conflicts ("update", "ignore")
            
        Returns:
            Dict with keys: success, inserted, updated, failed, errors
        """
        if not documents or not self.is_available():
            return {"success": True, "inserted": 0, "updated": 0, "failed": 0, "errors": []}
        
        try:
            bulk_docs = []
            errors = []
            existing_count = 0
            
            for doc in documents:
                doc_id = doc.get("document_id")
                fields = doc.get("fields", {})
                
                try:
                    if doc_id in self.db:
                        # Document exists - update
                        existing_count += 1
                        if conflict_resolution == "update":
                            existing_doc = self.db[doc_id]
                            existing_doc.update(fields)
                            bulk_docs.append(existing_doc)
                        # else: ignore (don't add to bulk)
                    else:
                        # Document doesn't exist - insert
                        new_doc = {"_id": doc_id}
                        new_doc.update(fields)
                        bulk_docs.append(new_doc)
                        
                except Exception as e:
                    errors.append({"document_id": doc_id, "error": str(e)})
            
            # Execute bulk upsert
            if bulk_docs:
                results = self.db.update(bulk_docs)
                
                # Count successes
                success_count = sum(1 for success, doc_id, rev_or_error in results if success)
                failed = len(bulk_docs) - success_count
                
                # Estimate inserts vs updates
                inserted = success_count - existing_count if success_count > existing_count else 0
                updated = success_count - inserted
                
                # Collect errors
                for success, doc_id, rev_or_error in results:
                    if not success:
                        errors.append({"document_id": doc_id, "error": str(rev_or_error)})
                
                logger.info(f"✅ CouchDB batch upserted {success_count} documents (est. {inserted} inserts, {updated} updates)")
                
                return {
                    "success": success_count > 0,
                    "inserted": inserted,
                    "updated": updated,
                    "failed": failed + len(errors),
                    "errors": errors
                }
            else:
                return {
                    "success": False,
                    "inserted": 0,
                    "updated": 0,
                    "failed": len(documents),
                    "errors": errors
                }
            
        except Exception as e:
            logger.error(f"❌ CouchDB batch upsert failed: {e}")
            return {
                "success": False,
                "inserted": 0,
                "updated": 0,
                "failed": len(documents),
                "errors": [{"error": str(e)}]
            }


def get_backend_class():
    return CouchDBAdapter
