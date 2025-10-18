"""
UDS3 VPB Module

Dieses Modul ist Teil der UDS3 Polyglot Persistence Architecture.
VPB = Verwaltungsprozessbeschreibung
"""

# Core Adapter
from .adapter import VPBAdapter, create_vpb_adapter

__module_name__ = "vpb"
__version__ = "2.0.0"

__all__ = [
    "VPBAdapter",
    "create_vpb_adapter",
]
