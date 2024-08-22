from sqlalchemy import Integer, BigInteger, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger)
    first_name: Mapped[str] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=True)
    username: Mapped[str] = mapped_column(String(50), nullable=True)

class Apartment(Base):
    __tablename__ = 'apartments'

    id: Mapped[int] = mapped_column(primary_key=True)
    area: Mapped[int] = mapped_column(nullable=True)
    address: Mapped[str] = mapped_column(String(125), nullable=True)
    region: Mapped[str] = mapped_column(String(125), nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=True)
    number_of_rooms: Mapped[int] = mapped_column(nullable=True)
    article: Mapped[str] = mapped_column(String(225), nullable=True)
    floor: Mapped[int] = mapped_column(nullable=True)
    metro: Mapped[str] = mapped_column(String(100), nullable=True)
    additional_info: Mapped[str] = mapped_column(String(100), nullable=True)

    # Реляція з SavedApartment
    saved_apartments = relationship('SavedApartment', back_populates='apartment')

class SavedApartment(Base):
    __tablename__ = 'saved_apartments'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    apartment_id: Mapped[int] = mapped_column(Integer, ForeignKey('apartments.id'), nullable=False)
    
    # Реляція з Apartment
    apartment = relationship('Apartment', back_populates='saved_apartments')

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
