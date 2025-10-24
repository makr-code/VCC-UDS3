#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
__init__.py

UDS3 Legacy Module
Deprecated code being phased out.
Provides backward compatibility for legacy imports.

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

class LegacyCore:
    """
    Legacy compatibility class
    Provides minimal backward compatibility for old code
    """
    def __init__(self):
        print("Warning: LegacyCore is deprecated. Please use new UDS3 modules.")
    
    @staticmethod
    def get_legacy_warning():
        return "This is legacy code. Please migrate to new UDS3 structure."

__module_name__ = "legacy"
__version__ = "2.0.0"

__all__ = ["LegacyCore"]
