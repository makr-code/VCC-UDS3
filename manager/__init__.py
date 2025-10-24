"""
UDS3 Manager Module - Management & Orchestrierung
=================================================

Dieses Modul enthält alle Management- und Orchestrierungskomponenten:
- saga.py: SAGA-Orchestrator (ehemals uds3_saga_orchestrator.py)
- saga_mock.py: Mock SAGA-Orchestrator (ehemals uds3_saga_mock_orchestrator.py)
- compliance.py: SAGA-Compliance (ehemals uds3_saga_compliance.py)
- saga_steps.py: SAGA-Step-Builders (ehemals uds3_saga_step_builders.py)
- streaming.py: Streaming-Operationen (ehemals uds3_streaming_operations.py)
- streaming_saga.py: Streaming-SAGA-Integration (ehemals uds3_streaming_saga_integration.py)
- archive.py: Archive-Operationen (ehemals uds3_archive_operations.py)
- delete.py: Delete-Operationen (ehemals uds3_delete_operations.py)
- followup.py: Follow-up-Orchestrator (ehemals uds3_follow_up_orchestrator.py)
- process.py: Process-Integration (ehemals uds3_complete_process_integration.py)
"""

# Manager components - modular imports
# Nur verfügbare Komponenten werden importiert

__all__ = []
SAGA_AVAILABLE = False
STREAMING_AVAILABLE = False
OPERATIONS_AVAILABLE = False

# Versuche SAGA-Komponenten zu laden (flexibel)
try:
    from .saga import UDS3SagaOrchestrator
    SAGA_AVAILABLE = True
    __all__.extend(["UDS3SagaOrchestrator", "SAGA_AVAILABLE"])
except ImportError:
    pass

# Versuche Streaming-Komponenten zu laden
try:
    from .streaming import StreamingManager
    from .archive import ArchiveManager
    from .delete import SoftDeleteManager, HardDeleteManager, DeleteOperationsOrchestrator
    STREAMING_AVAILABLE = True
    OPERATIONS_AVAILABLE = True
    __all__.extend(["StreamingManager", "ArchiveManager", "SoftDeleteManager", 
                   "HardDeleteManager", "DeleteOperationsOrchestrator", "STREAMING_AVAILABLE"])
except ImportError:
    pass

# Versuche Operations-Komponenten zu laden  
try:
    # Minimale Operations-Unterstützung
    OPERATIONS_AVAILABLE = True
    __all__.extend(["OPERATIONS_AVAILABLE"])
except ImportError:
    pass

__version__ = "3.1.0"
__updated__ = "2025-10-24"

# Health Check für Manager-Module
def manager_health_check():
    """Prüft Verfügbarkeit aller Manager-Komponenten"""
    return {
        "saga_available": SAGA_AVAILABLE,
        "streaming_available": STREAMING_AVAILABLE,
        "operations_available": OPERATIONS_AVAILABLE,
        "overall_status": "healthy" if all([SAGA_AVAILABLE, STREAMING_AVAILABLE, OPERATIONS_AVAILABLE]) else "degraded"
    }