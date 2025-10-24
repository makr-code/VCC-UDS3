#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
__init__.py

UDS3 Compliance Module - DSGVO, Security, and Identity Services
Dieses Modul ist Teil der UDS3 Polyglot Persistence Architecture.

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

from compliance.dsgvo_core import UDS3DSGVOCore, PIIType, DSGVOProcessingBasis, DSGVOOperationType
from compliance.security_quality import DataSecurityManager, DataQualityManager, SecurityLevel, QualityConfig
from compliance.identity_service import UDS3IdentityService, IdentityRecord
from compliance.adapter import ComplianceAdapter, create_compliance_adapter

__module_name__ = "compliance"
__version__ = "2.0.0"

__all__ = [
    'UDS3DSGVOCore',
    'DataSecurityManager',
    'DataQualityManager',
    'UDS3IdentityService',
    'ComplianceAdapter',
    'create_compliance_adapter',
    'PIIType',
    'DSGVOProcessingBasis',
    'DSGVOOperationType',
    'SecurityLevel',
    'QualityConfig',
    'IdentityRecord',
]
