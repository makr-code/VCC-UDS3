#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conftest.py

Conftest module

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

import sys
from pathlib import Path
from typing import Optional

# Ensure repository root (the directory containing project modules and __init__.py)
# is on sys.path so local module imports (e.g. `uds3_adapters`) work during tests.
# Ensure the parent folder that contains the `uds3` package directory is on sys.path
# so that imports like `uds3.uds3_core` resolve correctly.
this_file = Path(__file__).resolve()
repo_parent: Optional[Path] = None

for candidate in this_file.parents:
    if (candidate / "uds3" / "__init__.py").exists():
        repo_parent = candidate
        break

if repo_parent is None:
    # Fallback: add two levels up
    repo_parent = this_file.parents[2]

parent_str = str(repo_parent)
if parent_str not in sys.path:
    sys.path.insert(0, parent_str)
