"""
Database session management for ansible-inspec server.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy import create_engine
from typing import AsyncGenerator, Optional
import logging

from .models import Base

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration and session management"""
    
    def __init__(
        self,
        url: str,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_pre_ping: bool = True,
        echo: bool = False
    ):
        """
        Initialize database configuration
        
        Args:
            url: Database connection URL (async format: postgresql+asyncpg://...)
            pool_size: Connection pool size
            max_overflow: Max overflow connections
            pool_pre_ping: Verify connections before use
            echo: Log SQL statements
        """
        self.url = url
        
        # Determine if using SQLite or PostgreSQL
        is_sqlite = 'sqlite' in url.lower()
        
        # Create async engine
        self.engine = create_async_engine(
            url,
            poolclass=NullPool if is_sqlite else QueuePool,
            pool_size=pool_size if not is_sqlite else None,
            max_overflow=max_overflow if not is_sqlite else None,
            pool_pre_ping=pool_pre_ping if not is_sqlite else False,
            echo=echo
        )
        
        # Create session maker
        self.session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info(f"Database engine initialized: {url.split('@')[-1] if '@' in url else url}")
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session (async context manager)
        
        Yields:
            AsyncSession: Database session
        """
        async with self.session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def create_tables(self):
        """Create all tables in the database"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")
    
    async def drop_tables(self):
        """Drop all tables from the database (use with caution!)"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("Database tables dropped")
    
    async def close(self):
        """Close database engine"""
        await self.engine.dispose()
        logger.info("Database engine disposed")


# Global database instance
_db_instance: Optional[DatabaseConfig] = None


def init_database(
    url: str,
    pool_size: int = 20,
    max_overflow: int = 10,
    pool_pre_ping: bool = True,
    echo: bool = False
) -> DatabaseConfig:
    """
    Initialize global database instance
    
    Args:
        url: Database connection URL
        pool_size: Connection pool size
        max_overflow: Max overflow connections
        pool_pre_ping: Verify connections before use
        echo: Log SQL statements
        
    Returns:
        DatabaseConfig: Database configuration instance
    """
    global _db_instance
    _db_instance = DatabaseConfig(
        url=url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=pool_pre_ping,
        echo=echo
    )
    return _db_instance


def get_database() -> DatabaseConfig:
    """
    Get global database instance
    
    Returns:
        DatabaseConfig: Database configuration instance
        
    Raises:
        RuntimeError: If database not initialized
    """
    if _db_instance is None:
        raise RuntimeError(
            "Database not initialized. Call init_database() first."
        )
    return _db_instance


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI route injection
    
    Yields:
        AsyncSession: Database session
    """
    db = get_database()
    async for session in db.get_session():
        yield session
