from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os
from contextlib import asynccontextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./finbot.db")

engine = create_async_engine(DATABASE_URL, echo=True)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

@asynccontextmanager
async def get_session() -> AsyncSession:
    """Cria uma sessão assíncrona do banco de dados"""
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise 