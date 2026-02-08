from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings


# Engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,                # set True for debug
    future=True,
)

# Session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Base for all models
class Base(DeclarativeBase):
    pass


# Dependency to get DB session in routes
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session