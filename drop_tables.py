from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData

DATABASE_URL = "sqlite+aiosqlite:///db.sqlite3"  # Replace with your database URL

# Create an asynchronous engine
engine = create_async_engine(DATABASE_URL)

# Create a base class for declarative models
Base = declarative_base()

async def drop_all_tables():
    async with engine.begin() as conn:
        # Reflect the existing database schema
        meta = MetaData()
        await conn.run_sync(meta.reflect)
        
        # Drop all tables
        await conn.run_sync(meta.drop_all)

# Example of how to call the function in an async context
import asyncio

async def main():
    await drop_all_tables()
    print("All tables have been dropped.")

asyncio.run(main())
