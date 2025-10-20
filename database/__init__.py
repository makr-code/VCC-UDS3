"""Database adapters and utilities package."""

from uds3.database.database_manager import DatabaseManager
from uds3.database.extensions import (
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
