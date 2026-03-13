import pytest
import asyncio
from database import async_session, engine, Base
from sqlalchemy.ext.asyncio import create_async_engine

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session():
    async with async_session() as session:
        yield session
        await session.rollback()