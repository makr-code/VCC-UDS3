#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
database_manager.py

API manager and orchestration

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

class DatabaseManager:
    def __init__(self, cfg=None):
        self._cfg = cfg or {}

    def get_adapter_governance(self):
        return None

    def get_database_manager(self):
        return self
