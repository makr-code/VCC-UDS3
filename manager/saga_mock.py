#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
saga_mock.py

UDS3 Mock SAGA Orchestrator
Mock implementation for testing and fallback scenarios when database.saga_orchestrator is not available.
This should only be used for testing or when the real SAGA backend is intentionally disabled.

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class MockSagaOrchestrator:
    """Mock SAGA Orchestrator for testing and fallback scenarios
    
    WARNING: This is a simplified mock implementation.
    - No persistence (all state in memory)
    - No compensation on failure
    - No idempotency
    - No transaction support
    
    Use only for testing or when database.saga_orchestrator is unavailable.
    """
    
    def __init__(self, manager=None):
        self.manager = manager
        self.logger = logging.getLogger("uds3.saga.mock_orchestrator")
        self.sagas = {}  # In-memory storage
        self.logger.warning("⚠️ Using MockSagaOrchestrator - NO PERSISTENCE, NO COMPENSATION!")
    
    def create_saga(self, name: str = None, steps: List[Dict[str, Any]] = None, trace_id: str = None) -> str:
        """Mock implementation of create_saga"""
        saga_id = f"mock_saga_{hash(str(steps or []))}"
        self.sagas[saga_id] = {
            'name': name or 'unnamed',
            'steps': steps or [],
            'trace_id': trace_id,
            'status': 'created'
        }
        self.logger.debug(f"Mock: Created saga {saga_id}")
        return saga_id
    
    def execute_saga(self, saga_id: str, max_retries: int = 3, start_at: int = None) -> Dict[str, Any]:
        """Mock implementation of execute_saga"""
        if saga_id not in self.sagas:
            return {'success': False, 'error': 'Saga not found'}
        
        saga = self.sagas[saga_id]
        steps = saga.get('steps', [])
        context = {}
        
        self.logger.debug(f"Mock: Executing saga {saga_id} with {len(steps)} steps")
        
        # Simple sequential execution (no retries, no compensation)
        for i, step in enumerate(steps):
            try:
                # Mock step execution
                if callable(step.get('action')):
                    result = step['action'](context)
                    if result:
                        context.update(result)
            except Exception as e:
                self.logger.error(f"Mock: Step {i} failed: {e}")
                saga['status'] = 'failed'
                return {
                    'success': False,
                    'error': str(e),
                    'executed': list(range(i))
                }
        
        saga['status'] = 'completed'
        return {
            'success': True,
            'executed': list(range(len(steps)))
        }
    
    def execute(self, definition, context: Dict[str, Any] = None, saga_id: str = None) -> Dict[str, Any]:
        """Legacy execute method for compatibility"""
        ctx = dict(context or {})
        saga_id = saga_id or f"mock_{hash(str(definition))}"
        
        self.logger.debug(f"Mock: Legacy execute for saga {saga_id}")
        
        steps = getattr(definition, 'steps', [])
        
        for step in steps:
            try:
                if hasattr(step, 'action') and step.action:
                    result = step.action(ctx)
                    if result:
                        ctx.update(result)
            except Exception as e:
                return {
                    'saga_id': saga_id,
                    'status': 'FAILED',
                    'context': ctx,
                    'errors': [str(e)],
                    'compensation_errors': []
                }
        
        return {
            'saga_id': saga_id,
            'status': 'COMPLETED',
            'context': ctx,
            'errors': [],
            'compensation_errors': []
        }
    
    def compensate_saga(self, saga_id: str, executed_steps: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Mock compensation (does nothing)"""
        self.logger.warning(f"Mock: Compensation called for {saga_id} - NO ACTUAL COMPENSATION")
        return {'compensated': True}
    
    def abort_saga(self, saga_id: str, reason: str = '') -> None:
        """Mock abort"""
        if saga_id in self.sagas:
            self.sagas[saga_id]['status'] = 'aborted'
        self.logger.debug(f"Mock: Aborted saga {saga_id}: {reason}")
    
    def resume_saga(self, saga_id: str) -> Dict[str, Any]:
        """Mock resume (not supported)"""
        self.logger.warning(f"Mock: Resume not supported for {saga_id}")
        return {'resumed': False, 'reason': 'Mock orchestrator does not support resume'}


def create_mock_orchestrator() -> MockSagaOrchestrator:
    """Factory function to create a mock orchestrator
    
    Returns:
        MockSagaOrchestrator instance
    """
    logger.warning("⚠️ Creating Mock SAGA Orchestrator - Use only for testing!")
    return MockSagaOrchestrator()


__all__ = ['MockSagaOrchestrator', 'create_mock_orchestrator']
