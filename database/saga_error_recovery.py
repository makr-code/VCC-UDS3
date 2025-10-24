#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
saga_error_recovery.py

saga_error_recovery.py
SAGA Orchestrator Error-Handling Hardening
===========================================
Erweiterte Error-Recovery-Logic für SAGA Pattern:
- Compensation Retry mit Exponential Backoff (3 Retries)
- Transaction Timeout Management (300s)
- Lock-Acquisition mit Retry-Logic
- SAGA Status Transitions mit Error-States
Author: UDS3 System
Date: 2025-10-09
Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

import time
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


def execute_compensation_with_retry(
    compensation_handler,
    payload: Dict[str, Any],
    backends: Dict[str, Any],
    saga_id: str,
    step_id: str,
    compensation_name: str,
    max_retries: int = 3,
    base_delay: float = 1.0
) -> Dict[str, Any]:
    """
    Execute Compensation-Function mit Retry-Logic und Exponential Backoff
    
    Args:
        compensation_handler: Compensation-Funktion
        payload: Compensation-Payload
        backends: Dict mit Backend-Instanzen (relational, graph, vector)
        saga_id: SAGA-ID
        step_id: Step-ID
        compensation_name: Name der Compensation-Funktion
        max_retries: Maximale Anzahl Retries (default: 3)
        base_delay: Basis-Delay für Exponential Backoff (default: 1.0s)
    
    Returns:
        Dict mit {'success': bool, 'retry_count': int, 'error': str}
    """
    from database.database_exceptions import (
        SagaCompensationError,
        log_operation_start,
        log_operation_success,
        log_operation_failure
    )
    
    log_operation_start("SAGA", "compensate", saga_id=saga_id, step_id=step_id, 
                       compensation=compensation_name)
    
    for retry in range(max_retries + 1):
        try:
            # Execute Compensation
            success = compensation_handler(payload, backends)
            
            if success:
                log_operation_success("SAGA", "compensate", saga_id=saga_id, 
                                    step_id=step_id, retry_count=retry)
                return {
                    'success': True,
                    'retry_count': retry,
                    'error': None
                }
            else:
                # Compensation returned False
                raise Exception(f"Compensation handler returned False")
                
        except Exception as e:
            logger.warning(f"⚠️ Compensation attempt {retry + 1}/{max_retries + 1} failed: {e}")
            
            if retry < max_retries:
                # Exponential Backoff
                delay = base_delay * (2 ** retry)
                logger.info(f"🔄 Retrying compensation in {delay}s...")
                time.sleep(delay)
            else:
                # Alle Retries erschöpft
                log_operation_failure("SAGA", "compensate", e, saga_id=saga_id, 
                                    step_id=step_id, retry_count=retry)
                
                # Raise SagaCompensationError für kritisches Error-Handling
                raise SagaCompensationError(
                    saga_id=saga_id,
                    step_id=step_id,
                    compensation_name=compensation_name,
                    original_error=e,
                    retry_count=retry
                )
    
    # Sollte nie erreicht werden
    return {
        'success': False,
        'retry_count': max_retries,
        'error': 'Max retries reached'
    }


def acquire_lock_with_retry(
    orchestrator,
    saga_id: str,
    max_retries: int = 3,
    base_delay: float = 1.0,
    timeout_seconds: float = 30.0
) -> Any:
    """
    Acquire SAGA Lock mit Retry-Logic
    
    Args:
        orchestrator: SagaOrchestrator-Instanz
        saga_id: SAGA-ID
        max_retries: Maximale Anzahl Retries (default: 3)
        base_delay: Basis-Delay für Exponential Backoff (default: 1.0s)
        timeout_seconds: Gesamtes Timeout (default: 30s)
    
    Returns:
        Lock-Objekt oder None
    
    Raises:
        SagaLockError: Wenn Lock-Acquisition nach allen Retries fehlschlägt
    """
    from database.database_exceptions import (
        SagaLockError,
        log_operation_start,
        log_operation_success
    )
    
    log_operation_start("SAGA", "acquire_lock", saga_id=saga_id)
    
    start_time = time.time()
    
    for retry in range(max_retries + 1):
        # Check Timeout
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            raise SagaLockError(
                saga_id=saga_id,
                timeout_seconds=elapsed
            )
        
        try:
            # Versuche Lock zu holen
            lock = orchestrator._acquire_lock(saga_id)
            
            if lock:
                log_operation_success("SAGA", "acquire_lock", saga_id=saga_id, 
                                    retry_count=retry)
                return lock
            
            # Lock nicht verfügbar
            if retry < max_retries:
                delay = base_delay * (2 ** retry)
                logger.warning(f"⚠️ Lock not available, retry {retry + 1}/{max_retries + 1} in {delay}s")
                time.sleep(delay)
            
        except Exception as e:
            logger.warning(f"⚠️ Lock acquisition attempt {retry + 1}/{max_retries + 1} failed: {e}")
            
            if retry < max_retries:
                delay = base_delay * (2 ** retry)
                time.sleep(delay)
    
    # Alle Retries erschöpft
    elapsed = time.time() - start_time
    raise SagaLockError(
        saga_id=saga_id,
        timeout_seconds=elapsed
    )


def validate_saga_timeout(
    saga_id: str,
    start_time: float,
    timeout_threshold: float = 300.0
) -> None:
    """
    Validate SAGA Transaction Timeout
    
    Args:
        saga_id: SAGA-ID
        start_time: Start-Timestamp (time.time())
        timeout_threshold: Timeout-Schwelle in Sekunden (default: 300s = 5min)
    
    Raises:
        SagaTimeoutError: Wenn Timeout überschritten
    """
    from database.database_exceptions import SagaTimeoutError
    
    elapsed = time.time() - start_time
    
    if elapsed > timeout_threshold:
        logger.error(f"🚨 SAGA Timeout: {saga_id} - {elapsed:.1f}s elapsed (threshold: {timeout_threshold}s)")
        raise SagaTimeoutError(
            saga_id=saga_id,
            elapsed_seconds=elapsed,
            timeout_threshold=timeout_threshold
        )


def compensate_saga_with_recovery(
    orchestrator,
    saga_id: str,
    executed_steps: List[Dict[str, Any]],
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Compensate SAGA mit Error-Recovery
    
    Führt Compensation für alle executed Steps in umgekehrter Reihenfolge aus.
    Bei Compensation-Failures: 3 Retries mit Exponential Backoff.
    
    Args:
        orchestrator: SagaOrchestrator-Instanz
        saga_id: SAGA-ID
        executed_steps: Liste der ausgeführten Steps
        max_retries: Maximale Retries pro Compensation (default: 3)
    
    Returns:
        Dict mit Compensation-Results:
        {
            'compensated': bool,
            'total_steps': int,
            'successful_compensations': int,
            'failed_compensations': int,
            'errors': List[str]
        }
    """
    from database.database_exceptions import (
        SagaCompensationError,
        log_operation_start,
        log_operation_success,
        log_operation_failure
    )
    from database.saga_compensations import get as get_compensation
    
    log_operation_start("SAGA", "compensate_saga", saga_id=saga_id, 
                       total_steps=len(executed_steps))
    
    rel = orchestrator._get_relational()
    graph = orchestrator.manager.get_graph_backend() if hasattr(orchestrator, 'manager') else None
    vector = orchestrator.manager.get_vector_backend() if hasattr(orchestrator, 'manager') else None
    
    backends = {
        'relational_backend': rel,
        'graph_backend': graph,
        'vector_backend': vector
    }
    
    total_steps = len(executed_steps)
    successful_compensations = 0
    failed_compensations = 0
    errors = []
    
    # Reverse order compensation
    for step in reversed(executed_steps):
        # Skip bereits geskippte Steps
        if step.get('skipped'):
            continue
        
        step_id = step.get('step_id', 'unknown')
        payload = step.get('payload', {})
        compensation_name = step.get('compensation') or payload.get('compensation')
        
        if not compensation_name:
            logger.warning(f"⚠️ No compensation registered for step {step_id}")
            continue
        
        # Hole Compensation-Handler
        handler = get_compensation(compensation_name)
        if not handler:
            logger.warning(f"⚠️ No compensation handler found: {compensation_name}")
            failed_compensations += 1
            errors.append(f"No handler for {compensation_name}")
            continue
        
        try:
            # Execute Compensation mit Retry-Logic
            result = execute_compensation_with_retry(
                compensation_handler=handler,
                payload=payload,
                backends=backends,
                saga_id=saga_id,
                step_id=step_id,
                compensation_name=compensation_name,
                max_retries=max_retries
            )
            
            if result['success']:
                successful_compensations += 1
                
                # Write COMPENSATED event
                if hasattr(orchestrator, 'crud'):
                    orchestrator.crud.write_saga_event(
                        saga_id, step_id, 'COMPENSATED', payload
                    )
            else:
                failed_compensations += 1
                errors.append(f"Compensation {compensation_name} failed: {result.get('error')}")
                
        except SagaCompensationError as e:
            # Kritischer Compensation-Fehler nach allen Retries
            failed_compensations += 1
            errors.append(str(e))
            logger.error(f"🚨 CRITICAL: Compensation failed for step {step_id}: {e}")
    
    # Update SAGA Status
    if rel:
        try:
            if failed_compensations > 0:
                status = 'compensation_failed'
            else:
                status = 'compensated'
            
            rel.execute_query(
                'UPDATE uds3_sagas SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE saga_id = ?',
                (status, saga_id)
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to update SAGA status: {e}")
    
    # Log Results
    if failed_compensations > 0:
        log_operation_failure("SAGA", "compensate_saga", 
                            Exception(f"{failed_compensations} compensations failed"),
                            saga_id=saga_id, 
                            successful=successful_compensations,
                            failed=failed_compensations)
    else:
        log_operation_success("SAGA", "compensate_saga", saga_id=saga_id,
                            total_steps=total_steps,
                            successful=successful_compensations)
    
    return {
        'compensated': failed_compensations == 0,
        'total_steps': total_steps,
        'successful_compensations': successful_compensations,
        'failed_compensations': failed_compensations,
        'errors': errors
    }


__all__ = [
    'execute_compensation_with_retry',
    'acquire_lock_with_retry',
    'validate_saga_timeout',
    'compensate_saga_with_recovery'
]
