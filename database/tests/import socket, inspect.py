#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import socket, inspect.py

Import Socket, Inspect module

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

import socket, inspect
print(socket.__file__)
print(hasattr(socket, 'EAI_ADDRFAMILY'), getattr(socket, 'EAI_ADDRFAMILY', None))