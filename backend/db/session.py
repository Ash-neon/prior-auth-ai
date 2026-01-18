"""
Database Session Management
============================

Handles SQLAlchemy engine creation, session management,
and dependency injection for FastAPI.

Author: Prior Auth AI Team
Version: 1.0.0
"""

from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool

from core.config import settings
from core.logging import get_logger


logger = get_logger(__name__)


# Create database engine
def create_db_engine():
    """
    Create SQLAlchemy engine with appropriate configuration.
    
    Returns:
        SQLAlchemy engine instance
    """
    # Connection pool configuration
    pool_config = {
        "pool_pre_ping": True,  # Test connections before using
        "pool_recycle": 3600,   # Recycle connections after 1 hour
        "echo": settings.DEBUG,  # Log SQL queries in debug mode
    }
    
    # Use different pooling strategies based on environment
    if settings.APP_ENV == "testing":
        # Use NullPool for testing (no connection pooling)
        pool_config["poolclass"] = NullPool
    else:
        # Use QueuePool for production
        pool_config["poolclass"] = QueuePool
        pool_config["pool_size"] = settings.DB_POOL_SIZE
        pool_config["max_overflow"] = settings.DB_MAX_OVERFLOW
    
    # Create engine
    engine = create_engine(
        settings.DATABASE_URL,
        **pool_config
    )
    
    logger.info(
        f"Database engine created: "
        f"pool_size={settings.DB_POOL_SIZE}, "
        f"max_overflow={settings.DB_MAX_OVERFLOW}"
    )
    
    return engine


# Create engine instance
engine = create_db_engine()


# Configure session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Event listeners for connection management
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Set SQLite pragmas if using SQLite.
    
    This is mainly for testing scenarios.
    """
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """
    Log connection checkout for debugging.
    """
    if settings.DEBUG:
        logger.debug("Database connection checked out from pool")


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """
    Log connection checkin for debugging.
    """
    if settings.DEBUG:
        logger.debug("Database connection returned to pool")


# Dependency injection for FastAPI
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    
    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Context manager for manual session handling
class DatabaseSession:
    """
    Context manager for database sessions outside FastAPI context.
    
    Usage:
        with DatabaseSession() as db:
            user = db.query(User).first()
    """
    
    def __enter__(self) -> Session:
        """Enter context: create session."""
        self.db = SessionLocal()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context: close session."""
        if exc_type is not None:
            # Rollback on exception
            self.db.rollback()
        self.db.close()
        return False  # Don't suppress exceptions


# Async session support (for future use)
try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker as async_sessionmaker
    
    # Create async engine if using async driver
    if "+asyncpg" in settings.DATABASE_URL or "+aiomysql" in settings.DATABASE_URL:
        async_engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        AsyncSessionLocal = async_sessionmaker(
            async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        async def get_async_db() -> Generator[AsyncSession, None, None]:
            """
            Async version of get_db for async endpoints.
            
            Usage:
                @app.get("/users")
                async def get_users(db: AsyncSession = Depends(get_async_db)):
                    result = await db.execute(select(User))
                    return result.scalars().all()
            """
            async with AsyncSessionLocal() as session:
                yield session
    else:
        # No async support
        AsyncSessionLocal = None
        
        async def get_async_db():
            raise NotImplementedError(
                "Async database sessions require async driver "
                "(e.g., postgresql+asyncpg://)"
            )

except ImportError:
    # SQLAlchemy async not available
    AsyncSessionLocal = None
    
    async def get_async_db():
        raise NotImplementedError(
            "Async database sessions require SQLAlchemy 2.0+ "
            "with async drivers"
        )


# Health check utility
def check_database_connection() -> bool:
    """
    Check if database is accessible.
    
    Returns:
        True if database connection successful
    """
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("Database connection check: OK")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


# Database initialization
def init_db() -> None:
    """
    Initialize database schema.
    
    Creates all tables defined in models.
    Should only be used for testing - use Alembic for production.
    """
    from db.base import Base
    
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized")


# Database cleanup (for testing)
def drop_db() -> None:
    """
    Drop all database tables.
    
    WARNING: This destroys all data. Only use for testing!
    """
    from db.base import Base
    
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("All tables dropped")


# Connection pool monitoring
def get_pool_status() -> dict:
    """
    Get current connection pool status.
    
    Returns:
        Dictionary with pool statistics
    """
    pool = engine.pool
    
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "max_overflow": settings.DB_MAX_OVERFLOW,
    }


# Transaction utilities
def commit_or_rollback(db: Session, operation_name: str = "operation") -> bool:
    """
    Helper to commit or rollback a transaction with logging.
    
    Args:
        db: Database session
        operation_name: Name of operation for logging
        
    Returns:
        True if commit succeeded, False if rolled back
    """
    try:
        db.commit()
        logger.debug(f"{operation_name} committed successfully")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"{operation_name} failed, rolled back: {e}")
        raise