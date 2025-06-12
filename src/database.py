import os
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from models import Base

# Configure logging
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Create async engine with connection pooling optimized for Lambda
engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Disable connection pooling for Lambda
    echo=False,  # Set to True for SQL debugging
    connect_args={
        "server_settings": {
            "application_name": "competitor-tracking-lambda",
            "jit": "off",  # Disable JIT for faster cold starts
        },
        "command_timeout": 30,
        "server_settings": {"tcp_keepalives_idle": "600"}
    }
)

# Create session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.
    
    Usage:
        async with get_session() as session:
            result = await session.execute(select(Competitor))
    """
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

async def init_database():
    """Initialize database tables. Call this from migration handler."""
    try:
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

async def check_database_connection():
    """Check if database connection is working."""
    try:
        async with get_session() as session:
            result = await session.execute(text("SELECT 1"))
            row = result.scalar()
            if row == 1:
                logger.info("Database connection successful")
                return True
            else:
                logger.error("Database connection check failed")
                return False
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return False

async def close_database():
    """Close database connections. Call this for cleanup."""
    await engine.dispose()
    logger.info("Database connections closed")

# Utility functions for common database operations
async def get_user_by_email(email: str):
    """Get user by email address."""
    from models import User
    from sqlalchemy import select
    
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

async def get_competitors_for_user(user_id: str, active_only: bool = True):
    """Get all competitors for a user."""
    from models import Competitor
    from sqlalchemy import select
    
    async with get_session() as session:
        query = select(Competitor).where(Competitor.user_id == user_id)
        if active_only:
            query = query.where(Competitor.is_active == True)
        
        result = await session.execute(query)
        return result.scalars().all()

async def get_recent_scrape_results(competitor_id: str, limit: int = 10):
    """Get recent scrape results for a competitor."""
    from models import ScrapeResult
    from sqlalchemy import select, desc
    
    async with get_session() as session:
        query = (
            select(ScrapeResult)
            .where(ScrapeResult.competitor_id == competitor_id)
            .order_by(desc(ScrapeResult.scraped_at))
            .limit(limit)
        )
        
        result = await session.execute(query)
        return result.scalars().all()

# Connection retry logic for Lambda cold starts
async def ensure_connection():
    """Ensure database connection is ready, with retry logic."""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            if await check_database_connection():
                return True
        except Exception as e:
            logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
    
    raise Exception("Failed to establish database connection after retries") 