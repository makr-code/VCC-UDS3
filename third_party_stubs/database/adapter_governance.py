#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adapter_governance.py

Adapter Governance module

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

class AdapterGovernanceError(Exception):
    pass

class AdapterGovernance:
    def ensure_operation_allowed(self, backend_key, operation):
        return True

    def enforce_payload(self, backend_key, operation, payload):
        return payload
