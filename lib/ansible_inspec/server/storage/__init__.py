"""
Storage package for ansible-inspec server.

This package provides storage backends for persisting job templates, jobs,
workflows, VCS credentials, and users. Supports file-based, database (Prisma),
and hybrid storage modes.
"""

from ansible_inspec.server.storage.base import StorageBackend
from ansible_inspec.server.storage.file_backend import FileStorageBackend
from ansible_inspec.server.storage.prisma_backend import PrismaStorageBackend

__all__ = [
    "StorageBackend",
    "FileStorageBackend",
    "PrismaStorageBackend",
    "create_storage",
]


def create_storage(storage_backend: str = "file", data_dir: str = "data") -> StorageBackend:
    """
    Factory function to create storage backend based on configuration.
    
    Args:
        storage_backend: Backend type ('file', 'database', or 'hybrid')
        data_dir: Data directory for file backend
        
    Returns:
        Storage backend instance
    """
    backend_type = storage_backend.lower()
    
    if backend_type == 'database':
        return PrismaStorageBackend()
    elif backend_type == 'file':
        return FileStorageBackend(data_dir=data_dir)
    elif backend_type == 'hybrid':
        # Import here to avoid circular dependency
        from ansible_inspec.server.storage.hybrid import HybridStorage
        return HybridStorage(
            file_backend=FileStorageBackend(data_dir=data_dir),
            db_backend=PrismaStorageBackend(),
        )
    else:
        raise ValueError(f"Unknown storage backend: {backend_type}")

