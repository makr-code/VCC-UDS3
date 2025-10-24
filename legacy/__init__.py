"""
UDS3 Legacy Module

Deprecated code being phased out.
Provides backward compatibility for legacy imports.
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
