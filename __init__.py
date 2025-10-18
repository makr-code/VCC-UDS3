"""
UDS3 - Unified Data Strategy 3.0
Polyglot Persistence Architecture

Auto-generiert von generate_init_files.py
"""

# High-Level Exports
from .core.polyglot_manager import UDS3PolyglotManager

# Version Info
__version__ = "2.0.0"
__author__ = "UDS3 Team"

# Convenience Exports
__all__ = [
    "UDS3PolyglotManager",
]

# Module Discovery
__modules__ = [
    "core",
    "vpb",
    "compliance",
    "integration",
    "operations",
    "query",
    "domain",
    "saga",
    "relations",
    "performance",
    "legacy",
]
