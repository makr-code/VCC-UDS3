#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conftest.py

Conftest module with shared test fixtures

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

import sys
import pytest
import tempfile
import os
import shutil
from pathlib import Path
from typing import Optional, Generator

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


# ============================================================================
# Shared Test Fixtures
# ============================================================================

from database.database_api_sqlite import SQLiteDatabaseAPI


@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test session"""
    temp_path = Path(tempfile.mkdtemp(prefix="uds3_test_"))
    yield temp_path
    # Cleanup
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sqlite_db() -> Generator[SQLiteDatabaseAPI, None, None]:
    """Create temporary SQLite database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db = SQLiteDatabaseAPI(db_path)
    yield db
    
    # Cleanup
    db.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def populated_db() -> Generator[SQLiteDatabaseAPI, None, None]:
    """Create SQLite database with test data"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db = SQLiteDatabaseAPI(db_path)
    
    # Create standard test tables
    db.execute_query("""
        CREATE TABLE test_documents (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT,
            category TEXT,
            created_date TEXT,
            status TEXT DEFAULT 'draft'
        )
    """)
    
    db.execute_query("""
        CREATE TABLE test_users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user'
        )
    """)
    
    # Insert test data
    test_docs = [
        ("Finance Report 2024", "Q1 financial analysis", "Finance", "2024-01-01", "published"),
        ("HR Policy Update", "New remote work policy", "HR", "2024-01-15", "published"),
        ("IT Security Guide", "Security best practices", "IT", "2024-02-01", "draft"),
        ("Marketing Plan", "2024 marketing strategy", "Marketing", "2024-02-15", "published"),
        ("Product Roadmap", "Q2-Q4 product plans", "Product", "2024-03-01", "draft")
    ]
    
    for doc in test_docs:
        db.execute_query(
            "INSERT INTO test_documents (title, content, category, created_date, status) VALUES (?, ?, ?, ?, ?)",
            doc
        )
    
    test_users = [
        ("admin", "admin@example.com", "admin"),
        ("user1", "user1@example.com", "user"),
        ("user2", "user2@example.com", "user"),
        ("manager", "manager@example.com", "manager")
    ]
    
    for user in test_users:
        db.execute_query(
            "INSERT INTO test_users (username, email, role) VALUES (?, ?, ?)",
            user
        )
    
    yield db
    
    # Cleanup
    db.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_text_data():
    """Generate sample text data for testing"""
    return {
        "short": "Short text sample.",
        "medium": "This is a medium-length text sample for testing purposes. " * 5,
        "long": "This is a long text sample for testing purposes. " * 50,
        "special_chars": "Text with special chars: äöü ß €@#$%^&*()",
        "unicode": "Unicode test: 你好 مرحبا Привет 🚀",
        "code": "def test():\n    return 'code sample'",
        "json": '{"key": "value", "number": 123}',
        "xml": '<?xml version="1.0"?><root><item>test</item></root>'
    }


@pytest.fixture
def sample_numeric_data():
    """Generate sample numeric data"""
    return {
        "integers": list(range(100)),
        "floats": [i * 0.1 for i in range(100)],
        "negatives": list(range(-50, 50)),
        "large": [10**i for i in range(10)]
    }


@pytest.fixture
def mock_embeddings():
    """Generate mock embedding vectors"""
    import numpy as np
    
    return {
        "vec1": np.array([1.0, 0.0, 0.0]),
        "vec2": np.array([0.0, 1.0, 0.0]),
        "vec3": np.array([0.0, 0.0, 1.0]),
        "vec4": np.array([0.707, 0.707, 0.0]),
        "vec5": np.array([0.577, 0.577, 0.577])
    }


@pytest.fixture
def sample_file_data(temp_dir):
    """Create sample files for testing"""
    files = {}
    
    # Text file
    text_file = temp_dir / "sample.txt"
    text_file.write_text("Sample text content")
    files["text"] = text_file
    
    # JSON file
    json_file = temp_dir / "sample.json"
    json_file.write_text('{"test": "data"}')
    files["json"] = json_file
    
    # Binary file
    bin_file = temp_dir / "sample.bin"
    bin_file.write_bytes(b"\x00\x01\x02\x03\x04")
    files["binary"] = bin_file
    
    yield files
    
    # Cleanup handled by temp_dir fixture


# Helper functions as fixtures

@pytest.fixture
def create_test_table():
    """Factory fixture to create test tables"""
    def _create_table(db: SQLiteDatabaseAPI, table_name: str, columns: dict):
        """
        Create a test table
        
        Args:
            db: Database connection
            table_name: Name of table
            columns: Dict of {column_name: column_type}
        """
        cols = ", ".join(f"{name} {dtype}" for name, dtype in columns.items())
        db.execute_query(f"CREATE TABLE {table_name} ({cols})")
    
    return _create_table


@pytest.fixture
def insert_test_data():
    """Factory fixture to insert test data"""
    def _insert_data(db: SQLiteDatabaseAPI, table_name: str, data: list):
        """
        Insert test data
        
        Args:
            db: Database connection
            table_name: Name of table
            data: List of tuples with values
        """
        if not data:
            return
        
        placeholders = ", ".join("?" * len(data[0]))
        query = f"INSERT INTO {table_name} VALUES ({placeholders})"
        
        for record in data:
            db.execute_query(query, record)
    
    return _insert_data


# Performance testing fixtures

@pytest.fixture
def benchmark_timer():
    """Simple benchmark timer"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time is None or self.end_time is None:
                return None
            return self.end_time - self.start_time
    
    return Timer()


# Markers for test categorization

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "database: Database backend tests"
    )
    config.addinivalue_line(
        "markers", "saga: SAGA orchestration tests"
    )
    config.addinivalue_line(
        "markers", "streaming: Streaming operation tests"
    )
    config.addinivalue_line(
        "markers", "filters: Query filter tests"
    )
    config.addinivalue_line(
        "markers", "compliance: Compliance and security tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow-running tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance regression tests"
    )
