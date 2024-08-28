from sqlalchemy import Integer, BigInteger, String, ForeignKey, Column
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.constants import DATABASE_URL

engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine)

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, unique=True)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=True)
    username = Column(String(32), nullable=True)
    min_price = Column(Integer, nullable=True)
    max_price = Column(Integer, nullable=True)
    phone_number = Column(Integer, nullable=True)


class Apartment(Base):
    __tablename__ = 'apartments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=True)
    address = Column(String(200), nullable=True)
    region = Column(String(50), nullable=True)
    residential_complex = Column(String(50), nullable=True)
    area = Column(Integer, nullable=True)
    price = Column(Integer, nullable=True)
    number_of_rooms = Column(Integer, nullable=True)
    floor = Column(Integer, nullable=True)
    total_floors = Column(Integer, nullable=True)
    pets_allowed = Column(String(5), nullable=True)
    can_purchase = Column(String(5), nullable=True)
    article = Column(String(225), nullable=True)

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
