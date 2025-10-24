#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
veritas_relations_almanach.py

Veritas Relations Almanach module

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

from enum import Enum

class RelationType(Enum):
    PART_OF = 'PART_OF'
    UDS3_LEGAL_REFERENCE = 'UDS3_LEGAL_REFERENCE'

class GraphLevel(Enum):
    DOCUMENT = 'document'

class RelationDefinition:
    def __init__(self, name:str, attrs:dict=None):
        self.name = name
        self.attrs = attrs or {}

class VERITASRelationAlmanach:
    def get_definition(self, name):
        return RelationDefinition(name)
