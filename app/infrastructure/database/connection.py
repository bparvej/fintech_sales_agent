"""
Async SQLAlchemy database connection management.

Provides engine creation, session factory, and connection lifecycle management.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.shared.config.settings import get_settings
from app.shared.logging.logger import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""
    pass


class DatabaseManager:
    """Manages async database connections and sessions."""

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    async def initialize(self) -> None:
        """Create the database engine and session factory."""
        settings = get_settings()
        self._engine = create_async_engine(
            settings.database_url,
            echo=settings.app_debug,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info("Database engine initialized", url=settings.database_url.split("@")[-1])

    async def create_tables(self) -> None:
        """Create all tables from ORM models (development only)."""
        if self._engine is None:
            await self.initialize()
        async with self._engine.begin() as conn:  # type: ignore[union-attr]
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")

    async def close(self) -> None:
        """Dispose the engine and release connections."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database engine closed")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide a transactional database session."""
        if self._session_factory is None:
            await self.initialize()
        session = self._session_factory()  # type: ignore[misc]
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Global singleton — initialized during app startup
db_manager = DatabaseManager()
