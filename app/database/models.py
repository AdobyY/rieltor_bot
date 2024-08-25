from sqlalchemy import Integer, BigInteger, String, ForeignKey, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

# PostgreSQL connection string
DATABASE_URL = "postgresql+asyncpg://postgres:adoby@localhost/apartments"

engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, unique=True)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    username = Column(String(50), nullable=True)

class Apartment(Base):
    __tablename__ = 'apartments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    area = Column(Integer, nullable=True)
    address = Column(String(125), nullable=True)
    region = Column(String(125), nullable=True)
    price = Column(Integer, nullable=True)
    number_of_rooms = Column(Integer, nullable=True)
    article = Column(String(225), nullable=True)
    floor = Column(Integer, nullable=True)
    metro = Column(String(100), nullable=True)
    additional_info = Column(String(100), nullable=True)

    saved_apartments = relationship('SavedApartment', back_populates='apartment')

class SavedApartment(Base):
    __tablename__ = 'saved_apartments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    apartment_id = Column(Integer, ForeignKey('apartments.id'), nullable=False)

    apartment = relationship('Apartment', back_populates='saved_apartments')


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
