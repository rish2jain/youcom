from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# Create async engine with connection pooling configuration
engine = create_async_engine(
    settings.database_url,
    echo=settings.environment == "development",
    future=True,
    pool_size=20,          # Maximum number of connections to keep in pool
    max_overflow=10,       # Maximum overflow connections beyond pool_size
    pool_pre_ping=True,    # Verify connections before using them (prevents stale connections)
    pool_recycle=3600,     # Recycle connections after 1 hour to prevent stale connections
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
class Base(DeclarativeBase):
    pass

# Dependency to get database session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()