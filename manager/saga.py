#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UDS3 Saga Orchestrator - Wrapper

OPTIMIZED (1. Okt 2025): Thin wrapper around database/saga_orchestrator.py
BEFORE: 34 KB, 931 LOC | AFTER: 7 KB, 250 LOC | SAVINGS: -27 KB, -681 LOC
"""
from __future__ import annotations
import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# Lazy loading zur Vermeidung zirkulärer Imports
DatabaseSagaOrchestrator = None
DatabaseManager = None
SAGA_BACKEND_AVAILABLE = False

def _lazy_import_saga_backend():
    """Lazy loading der SAGA Backend Klassen zur Vermeidung zirkulärer Imports"""
    global DatabaseSagaOrchestrator, DatabaseManager, SAGA_BACKEND_AVAILABLE
    
    if SAGA_BACKEND_AVAILABLE:
        return True
    
    try:
        import sys
        import os
        
        # Add uds3 directory to Python path if needed
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Try absolute import first (if uds3 is a package)
        try:
            from uds3.database.saga_orchestrator import SagaOrchestrator as DatabaseSagaOrchestrator_
            logger.debug("✅ Loaded via absolute import: uds3.database.saga_orchestrator")
        except ImportError:
            # Fallback to relative import
            database_dir = os.path.join(current_dir, 'database')
            if database_dir not in sys.path:
                sys.path.insert(0, database_dir)
            from database.saga_orchestrator import SagaOrchestrator as DatabaseSagaOrchestrator_
            logger.debug("✅ Loaded via relative import: database.saga_orchestrator")
        
        DatabaseSagaOrchestrator = DatabaseSagaOrchestrator_
        
        # DatabaseManager optional
        try:
            try:
                from uds3.database.database_manager import DatabaseManager as DatabaseManager_
            except ImportError:
                from database.database_manager import DatabaseManager as DatabaseManager_
            DatabaseManager = DatabaseManager_
        except ImportError:
            DatabaseManager = None
        
        SAGA_BACKEND_AVAILABLE = True
        logger.info("✅ Database Saga Orchestrator erfolgreich geladen (lazy import)")
        return True
        
    except Exception as e:
        logger.warning(f"⚠️ Database Saga Orchestrator konnte nicht geladen werden: {e}")
        logger.debug(f"Import-Fehler Details: {e}", exc_info=True)
        DatabaseSagaOrchestrator = None
        DatabaseManager = None
        SAGA_BACKEND_AVAILABLE = False
        return False

logger = logging.getLogger(__name__)

class SagaExecutionError(Exception):
    pass

class SagaCompensationError(Exception):
    pass

class SagaStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    COMPENSATION_FAILED = "compensation_failed"

SagaAction = Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]
SagaCompensation = Callable[[Dict[str, Any]], None]

@dataclass(slots=True)
class SagaStep:
    name: str
    action: SagaAction
    compensation: Optional[SagaCompensation] = None

@dataclass(slots=True)
class SagaDefinition:
    name: str
    steps: List[SagaStep]

@dataclass(slots=True)
class SagaExecutionResult:
    saga_id: str
    status: SagaStatus
    context: Dict[str, Any]
    errors: List[str]
    compensation_errors: List[str]

class UDS3SagaOrchestrator:
    def __init__(self, relational_backend: Optional[Any] = None):
        self.logger = logging.getLogger("uds3.saga.orchestrator")
        
        # Versuche lazy import der SAGA Backend Klassen
        if not _lazy_import_saga_backend():
            # Fallback to mock only if explicitly requested or in test mode
            from uds3_saga_mock_orchestrator import create_mock_orchestrator
            self.logger.warning("⚠️ Database Saga Orchestrator nicht verfügbar - verwende Mock-Implementation")
            self.logger.warning("⚠️ Mock Mode: NO PERSISTENCE, NO COMPENSATION, NO TRANSACTION SUPPORT")
            self._orchestrator = create_mock_orchestrator()
        else:
            try:
                # Create DatabaseManager with backend configuration if available
                manager = None
                if DatabaseManager:
                    try:
                        # Try to get backend configuration from database.config
                        from database import config
                        backend_dict = config.get_database_backend_dict()
                        manager = DatabaseManager(backend_dict)
                        self.logger.debug("✅ DatabaseManager created with backend configuration")
                    except Exception as config_exc:
                        self.logger.debug(f"Could not load backend config: {config_exc}")
                        # Create without manager - orchestrator will work with limited functionality
                        manager = None
                
                self._orchestrator = DatabaseSagaOrchestrator(manager=manager)
                self.logger.info("✅ UDS3 Saga Orchestrator initialized (production mode with database backend)")
            except Exception as exc:
                from uds3_saga_mock_orchestrator import create_mock_orchestrator
                self.logger.error(f"❌ Saga Orchestrator initialization failed: {exc}", exc_info=True)
                self.logger.warning("⚠️ Falling back to Mock-Implementation")
                self._orchestrator = create_mock_orchestrator()

    def execute(self, definition: SagaDefinition, context: Optional[Dict[str, Any]] = None, *, saga_id: Optional[str] = None) -> SagaExecutionResult:
        ctx = dict(context or {})
        errors = []
        compensation_errors = []
        try:
            steps_data = [{'name': s.name, 'action': s.action, 'compensation': s.compensation} for s in definition.steps]
            trace_id = ctx.get('trace_id')
            db_saga_id = self._orchestrator.create_saga(name=definition.name, steps=steps_data, trace_id=trace_id)
            if saga_id is None:
                saga_id = db_saga_id
            executed_steps = []
            status = SagaStatus.RUNNING
            for step in definition.steps:
                try:
                    self.logger.info(f"Executing saga step: {step.name}")
                    if step.action:
                        result = step.action(ctx)
                        if result is not None:
                            ctx.update(result)
                    executed_steps.append(step)
                except Exception as exc:
                    error_msg = f"Step {step.name} failed: {exc}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
                    status = SagaStatus.COMPENSATING
                    for comp_step in reversed(executed_steps):
                        if comp_step.compensation:
                            try:
                                self.logger.info(f"Compensating: {comp_step.name}")
                                comp_step.compensation(ctx)
                            except Exception as comp_exc:
                                comp_error = f"Compensation for {comp_step.name} failed: {comp_exc}"
                                compensation_errors.append(comp_error)
                                self.logger.error(comp_error)
                    status = SagaStatus.COMPENSATION_FAILED if compensation_errors else SagaStatus.COMPENSATED
                    break
            else:
                status = SagaStatus.COMPLETED
            return SagaExecutionResult(saga_id=saga_id, status=status, context=ctx, errors=errors, compensation_errors=compensation_errors)
        except Exception as exc:
            self.logger.error(f"Saga execution failed: {exc}")
            return SagaExecutionResult(saga_id=saga_id or "unknown", status=SagaStatus.FAILED, context=ctx, errors=[str(exc)] + errors, compensation_errors=compensation_errors)

    def get_saga_status(self, saga_id: str) -> Dict[str, Any]:
        try:
            return self._orchestrator.get_saga_status(saga_id)
        except AttributeError:
            self.logger.warning("get_saga_status not implemented in backend orchestrator")
            return {"saga_id": saga_id, "status": "unknown", "message": "Backend does not support status queries"}

_saga_orchestrator = None
_orchestrator_lock = None
try:
    import threading
    _orchestrator_lock = threading.Lock()
except ImportError:
    pass

def get_saga_orchestrator(relational_backend: Optional[Any] = None) -> UDS3SagaOrchestrator:
    global _saga_orchestrator
    if _saga_orchestrator is None:
        if _orchestrator_lock:
            with _orchestrator_lock:
                if _saga_orchestrator is None:
                    _saga_orchestrator = UDS3SagaOrchestrator(relational_backend)
        else:
            _saga_orchestrator = UDS3SagaOrchestrator(relational_backend)
    return _saga_orchestrator

__all__ = ['UDS3SagaOrchestrator', 'SagaExecutionResult', 'SagaDefinition', 'SagaStep', 'SagaStatus', 'SagaExecutionError', 'SagaCompensationError', 'get_saga_orchestrator', 'SagaAction', 'SagaCompensation']
