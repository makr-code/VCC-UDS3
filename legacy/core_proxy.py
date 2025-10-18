"""
UDS3 Legacy Core Proxy
Deprecation-Wrapper für legacy/core.py → core/polyglot_manager.py

Dieser Proxy ermöglicht Backwards Compatibility für bestehenden Code,
der noch UnifiedDatabaseStrategy nutzt, leitet aber zur neuen API weiter.

WICHTIG: Dieser Code ist DEPRECATED und wird in zukünftigen Versionen entfernt.
Migrieren Sie zu: from uds3.core.polyglot_manager import UDS3PolyglotManager
"""

import warnings
from typing import Any, Dict, List, Optional
from functools import wraps

# Neue API Imports
from uds3.core.polyglot_manager import UDS3PolyglotManager


def deprecated(reason: str):
    """
    Decorator für deprecated Methoden.
    
    Args:
        reason: Grund für Deprecation + Migration-Hinweis
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"⚠️  DEPRECATED: {func.__name__} ist veraltet. {reason}",
                category=DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator


class UnifiedDatabaseStrategyProxy:
    """
    Proxy-Wrapper für UnifiedDatabaseStrategy.
    
    Leitet alle Aufrufe zu UDS3PolyglotManager weiter und gibt
    Deprecation Warnings aus.
    
    Migration Guide:
    ----------------
    ALT:
        from uds3_core import UnifiedDatabaseStrategy
        uds = UnifiedDatabaseStrategy(...)
        uds.create_secure_document(...)
    
    NEU:
        from uds3.core.polyglot_manager import UDS3PolyglotManager
        polyglot = UDS3PolyglotManager()
        polyglot.save_document(...)
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialisiert Proxy mit UDS3PolyglotManager.
        
        DEPRECATED: Nutzen Sie direkt UDS3PolyglotManager.
        """
        warnings.warn(
            "⚠️  DEPRECATED: UnifiedDatabaseStrategy ist veraltet.\n"
            "   Migration: from uds3.core.polyglot_manager import UDS3PolyglotManager\n"
            "   Siehe: docs/UDS3_MIGRATION_GUIDE.md",
            category=DeprecationWarning,
            stacklevel=2
        )
        
        # Initialisiere neue API
        self._polyglot = UDS3PolyglotManager()
        
        # Legacy-Kompatibilität: Speichere Args
        self._legacy_args = args
        self._legacy_kwargs = kwargs
    
    # ========================================
    # CRUD Operations (Mapping zu neuer API)
    # ========================================
    
    @deprecated(
        "Nutzen Sie: polyglot_manager.save_document(data, app_domain='vpb')"
    )
    def create_secure_document(
        self, 
        data: Dict[str, Any], 
        metadata: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        DEPRECATED: Erstellt ein Dokument.
        
        Migration:
            polyglot.save_document(data, app_domain='vpb')
        """
        # Merge data + metadata
        if metadata:
            data.update(metadata)
        
        # Map zu neuer API
        app_domain = kwargs.get('app_domain', 'vpb')
        return self._polyglot.save_document(data, app_domain=app_domain)
    
    @deprecated(
        "Nutzen Sie: polyglot_manager.get_document(doc_id, app_domain='vpb')"
    )
    def read_document(
        self, 
        doc_id: str, 
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        DEPRECATED: Liest ein Dokument.
        
        Migration:
            polyglot.get_document(doc_id, app_domain='vpb')
        """
        app_domain = kwargs.get('app_domain', 'vpb')
        return self._polyglot.get_document(doc_id, app_domain=app_domain)
    
    @deprecated(
        "Nutzen Sie: polyglot_manager.update_document(doc_id, updates, app_domain='vpb')"
    )
    def update_secure_document(
        self, 
        doc_id: str, 
        updates: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        DEPRECATED: Aktualisiert ein Dokument.
        
        Migration:
            polyglot.update_document(doc_id, updates, app_domain='vpb')
        """
        app_domain = kwargs.get('app_domain', 'vpb')
        return self._polyglot.update_document(doc_id, updates, app_domain=app_domain)
    
    @deprecated(
        "Nutzen Sie: polyglot_manager.delete_document(doc_id, app_domain='vpb', soft_delete=True)"
    )
    def delete_secure_document(
        self, 
        doc_id: str,
        soft_delete: bool = True,
        **kwargs
    ) -> bool:
        """
        DEPRECATED: Löscht ein Dokument.
        
        Migration:
            polyglot.delete_document(doc_id, soft_delete=True)
        """
        app_domain = kwargs.get('app_domain', 'vpb')
        return self._polyglot.delete_document(
            doc_id, 
            app_domain=app_domain, 
            soft_delete=soft_delete
        )
    
    @deprecated(
        "Nutzen Sie: polyglot_manager.list_documents(app_domain='vpb', filters=...)"
    )
    def list_documents(
        self,
        filters: Optional[Dict] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        DEPRECATED: Listet Dokumente.
        
        Migration:
            polyglot.list_documents(app_domain='vpb', filters=...)
        """
        app_domain = kwargs.get('app_domain', 'vpb')
        return self._polyglot.list_documents(app_domain=app_domain, filters=filters)
    
    # ========================================
    # Batch Operations
    # ========================================
    
    @deprecated(
        "Nutzen Sie: [polyglot_manager.get_document(id) for id in doc_ids]"
    )
    def batch_read_documents(
        self,
        doc_ids: List[str],
        **kwargs
    ) -> List[Optional[Dict[str, Any]]]:
        """
        DEPRECATED: Batch-Read von Dokumenten.
        
        Migration:
            [polyglot.get_document(id) for id in doc_ids]
        """
        app_domain = kwargs.get('app_domain', 'vpb')
        return [
            self._polyglot.get_document(doc_id, app_domain=app_domain)
            for doc_id in doc_ids
        ]
    
    @deprecated(
        "Nutzen Sie: [polyglot_manager.update_document(id, data) for id, data in updates]"
    )
    def batch_update_documents(
        self,
        updates: List[Dict[str, Any]],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        DEPRECATED: Batch-Update von Dokumenten.
        
        Migration:
            [polyglot.update_document(u['id'], u) for u in updates]
        """
        app_domain = kwargs.get('app_domain', 'vpb')
        results = []
        for update in updates:
            doc_id = update.pop('id', update.pop('_id', None))
            if doc_id:
                result = self._polyglot.update_document(
                    doc_id, update, app_domain=app_domain
                )
                results.append(result)
        return results
    
    # ========================================
    # Search Operations
    # ========================================
    
    @deprecated(
        "Nutzen Sie: polyglot_manager.semantic_search(query, app_domain='vpb')"
    )
    def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        DEPRECATED: Semantische Suche.
        
        Migration:
            polyglot.semantic_search(query, top_k=10)
        """
        app_domain = kwargs.get('app_domain', 'vpb')
        results = self._polyglot.semantic_search(
            query=query,
            app_domain=app_domain,
            top_k=top_k
        )
        return results.get('results', [])
    
    @deprecated(
        "Nutzen Sie: polyglot_manager.query_vector_database(query, filters=...)"
    )
    def query_vector_similarity(
        self,
        query_vector: List[float],
        top_k: int = 10,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        DEPRECATED: Vector-Similarity-Suche.
        
        Migration:
            polyglot.query_vector_database(embedding, filters=...)
        """
        # Vector-Suche über neue API
        # (Hinweis: Neue API nutzt Text-Query + automatisches Embedding)
        warnings.warn(
            "Vector-Similarity-Suche sollte über semantic_search() erfolgen",
            DeprecationWarning
        )
        return []
    
    @deprecated(
        "Nutzen Sie: polyglot_manager.query_graph(pattern, app_domain='vpb')"
    )
    def query_graph_pattern(
        self,
        pattern: Dict[str, Any],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        DEPRECATED: Graph-Pattern-Suche.
        
        Migration:
            polyglot.query_graph(pattern, app_domain='vpb')
        """
        app_domain = kwargs.get('app_domain', 'vpb')
        return self._polyglot.query_graph(pattern, app_domain=app_domain)
    
    @deprecated(
        "Nutzen Sie: polyglot_manager.query_sql(sql, params=...)"
    )
    def query_sql(
        self,
        sql: str,
        params: Optional[List] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        DEPRECATED: SQL-Query.
        
        Migration:
            polyglot.query_sql(sql, params=[...])
        """
        return self._polyglot.query_sql(sql, params=params)
    
    # ========================================
    # VPB-spezifische Methoden
    # ========================================
    
    @deprecated(
        "Nutzen Sie: from uds3.vpb.operations import VPBProcess; VPBProcess.create(...)"
    )
    def create_vpb_process(
        self,
        process_data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        DEPRECATED: Erstellt VPB-Prozess.
        
        Migration:
            Nutzen Sie VPB Operations Module direkt
        """
        return self._polyglot.save_document(process_data, app_domain='vpb')
    
    @deprecated(
        "Nutzen Sie VPB Operations Module: from uds3.vpb.operations import ..."
    )
    def create_vpb_crud_manager(self):
        """
        DEPRECATED: VPB CRUD Manager.
        
        Migration:
            Nutzen Sie VPB Operations Module direkt
        """
        warnings.warn(
            "VPB CRUD Manager sollte über vpb.operations Module genutzt werden",
            DeprecationWarning
        )
        return None
    
    # ========================================
    # Properties & Helper
    # ========================================
    
    @property
    def search_api(self):
        """DEPRECATED: Search API Property"""
        warnings.warn(
            "search_api Property ist deprecated. Nutzen Sie semantic_search() direkt",
            DeprecationWarning
        )
        return self._polyglot
    
    def __repr__(self) -> str:
        return (
            f"UnifiedDatabaseStrategyProxy(DEPRECATED) -> "
            f"UDS3PolyglotManager({self._polyglot})"
        )


# ========================================
# Backwards Compatibility Aliases
# ========================================

# Für bestehenden Code, der direkt importiert
UnifiedDatabaseStrategy = UnifiedDatabaseStrategyProxy


# Factory Function (Legacy)
@deprecated(
    "Nutzen Sie: from uds3.core.polyglot_manager import UDS3PolyglotManager; "
    "polyglot = UDS3PolyglotManager()"
)
def create_unified_database_strategy(*args, **kwargs) -> UnifiedDatabaseStrategyProxy:
    """
    DEPRECATED: Factory für UnifiedDatabaseStrategy.
    
    Migration:
        from uds3.core.polyglot_manager import UDS3PolyglotManager
        polyglot = UDS3PolyglotManager()
    """
    return UnifiedDatabaseStrategyProxy(*args, **kwargs)


# ========================================
# Migration Helper
# ========================================

def print_migration_guide():
    """Gibt Migration-Guide auf Konsole aus"""
    guide = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║  UDS3 MIGRATION GUIDE: UnifiedDatabaseStrategy → Polyglot    ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    ALT (DEPRECATED):
    -----------------
    from uds3_core import UnifiedDatabaseStrategy
    uds = UnifiedDatabaseStrategy()
    uds.create_secure_document(data)
    uds.semantic_search(query)
    
    NEU (EMPFOHLEN):
    ----------------
    from uds3.core.polyglot_manager import UDS3PolyglotManager
    polyglot = UDS3PolyglotManager()
    polyglot.save_document(data, app_domain='vpb')
    polyglot.semantic_search(query, app_domain='vpb')
    
    VORTEILE:
    ---------
    ✅ Klarere API (keine "secure" Präfixe nötig)
    ✅ Domain-basierte Organisation
    ✅ Bessere Performance (optimierte Queries)
    ✅ Moderne Architektur (Async Support via rag_async)
    ✅ Vollständige Test-Coverage
    
    SUPPORT:
    --------
    Dokumentation: docs/UDS3_MIGRATION_GUIDE.md
    Fragen: GitHub Issues
    """
    print(guide)


if __name__ == "__main__":
    # Zeige Migration-Guide beim direkten Aufruf
    print_migration_guide()
