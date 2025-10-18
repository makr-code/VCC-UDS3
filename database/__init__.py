"""Database adapters and utilities package."""

from database.database_manager import DatabaseManager
from database.extensions import (
    DatabaseManagerExtensions,
    create_extended_database_manager,
    ExtensionStatus
)

__all__ = [
    'DatabaseManager',
    'DatabaseManagerExtensions',
    'create_extended_database_manager',
    'ExtensionStatus',
]
