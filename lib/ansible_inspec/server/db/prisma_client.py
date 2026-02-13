"""
Database session management using Prisma Client Python.

This module provides the Prisma client singleton for async database operations.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from prisma import Prisma
from ansible_inspec.server.config import Settings

logger = logging.getLogger(__name__)

# Global Prisma client instance
_prisma_client: Prisma | None = None


async def get_prisma_client() -> Prisma:
    """
    Get or create the global Prisma client instance.
    
    Returns:
        Prisma client instance
        
    Raises:
        RuntimeError: If database is not configured
    """
    global _prisma_client
    
    if _prisma_client is None:
        _prisma_client = Prisma(auto_register=True)
        await _prisma_client.connect()
        logger.info("Prisma client connected to database")
    
    return _prisma_client


async def disconnect_prisma():
    """Disconnect the global Prisma client."""
    global _prisma_client
    
    if _prisma_client is not None:
        await _prisma_client.disconnect()
        _prisma_client = None
        logger.info("Prisma client disconnected from database")
    else:
        logger.debug("Prisma client was not connected, nothing to disconnect")


@asynccontextmanager
async def get_db() -> AsyncGenerator[Prisma, None]:
    """
    Context manager for database operations.
    
    Usage:
        async with get_db() as db:
            user = await db.user.find_unique(where={"email": "user@example.com"})
    
    Yields:
        Prisma client instance
    """
    db = await get_prisma_client()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database operation error: {e}")
        raise


async def initialize_database(settings: Settings) -> None:
    """
    Initialize database connection and ensure schema is up to date.
    
    Args:
        settings: Application settings
    
    Note:
        If no database URL is configured, this function will skip initialization
        and the server will use file-based storage only.
    """
    import os
    
    # Check if DATABASE_URL environment variable is set
    database_url = os.getenv("DATABASE_URL")
    
    # Skip database initialization if no database URL configured
    if not database_url and not settings.database.url:
        logger.info("No database configured - using file-based storage only")
        logger.info("Database-dependent features (auth, VCS) will be unavailable")
        return
    
    # Set DATABASE_URL from settings if not already set
    if not database_url and settings.database.url:
        os.environ["DATABASE_URL"] = settings.database.url
        logger.info("Set DATABASE_URL from settings")
    
    try:
        from prisma import Json
        import bcrypt
        
        # Connect to database
        db = await get_prisma_client()
        logger.info("Database initialized successfully")
        
        # Get admin credentials from environment variables
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@ansible-inspec.local")
        admin_password = os.getenv("ADMIN_PASSWORD")
        admin_name = os.getenv("ADMIN_NAME", "Administrator")
        
        # Create default admin user if none exists
        # Check by username since JSON queries are limited in Prisma
        admin = await db.user.find_first(where={"username": admin_username})
        if not admin:
            # Require password to be set via environment variable
            if not admin_password:
                logger.warning(
                    f"No admin user found and ADMIN_PASSWORD not set. "
                    f"Please set ADMIN_PASSWORD environment variable to create admin user."
                )
            else:
                logger.info(f"Creating admin user: {admin_username}")
                # Hash password using bcrypt
                salt = bcrypt.gensalt()
                hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), salt).decode('utf-8')
                await db.user.create(
                    data={
                        "username": admin_username,
                        "email": admin_email,
                        "name": admin_name,
                        "hashedPassword": hashed_password,
                        "roles": Json(["admin"]),
                        "active": True,
                    }
                )
                logger.info(f"Admin user '{admin_username}' created successfully")
        else:
            logger.info(f"Admin user '{admin_username}' already exists")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("Server will run with file-based storage only")
        logger.warning("Database-dependent features (auth, VCS) will be unavailable")
        # Don't raise - allow server to continue with file storage
        global _prisma_client
        _prisma_client = None


async def shutdown_database() -> None:
    """Shutdown database connection gracefully."""
    await disconnect_prisma()
    logger.info("Database connection closed")
