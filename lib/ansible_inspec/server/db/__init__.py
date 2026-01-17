"""
Database package for ansible-inspec server.

This package provides Prisma client management and utilities
for interacting with the PostgreSQL database using Prisma ORM.
"""

from ansible_inspec.server.db.prisma_client import (
    get_prisma_client,
    disconnect_prisma,
    get_db,
    initialize_database,
    shutdown_database,
)

__all__ = [
    "get_prisma_client",
    "disconnect_prisma",
    "get_db",
    "initialize_database",
    "shutdown_database",
]

