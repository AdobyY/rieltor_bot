from app.database.models import async_session
from app.database.models import User, Apartment
from sqlalchemy import select, update, delete
import pandas as pd

async def set_user(tg_id, first_name, last_name, username):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            new_user = User(tg_id=tg_id, first_name=first_name, last_name=last_name, username=username)
            session.add(new_user)
            await session.commit()
        else:
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
            await session.commit()
 

async def set_apartments(df):
    async with async_session() as session:
        for index, row in df.iterrows():
            apartment = await session.scalar(select(Apartment).where(Apartment.address == row['Адреса']))
            
            if not apartment:
                new_apartment = Apartment(
                    area=row['Площа'],
                    address=row['Адреса'],
                    region=row['Регіон'],
                    price=row['Ціна'],
                    price_category=row['Цінова категорія'],
                    number_of_rooms=row[' Кількість кімнат'],
                    article=row['Посилання на статтю'],
                    floor=row['Поверх'] if pd.notnull(row['Поверх']) else None,
                    metro=row['Метро'] if pd.notnull(row['Метро']) else None,
                    additional_info=row['Додаткова інформація'] if pd.notnull(row['Додаткова інформація']) else None
                )
                session.add(new_apartment)
                await session.commit()
            else:
                apartment.area = row['Площа']
                apartment.region = row['Регіон']
                apartment.price = row['Ціна']
                apartment.price_category = row['Цінова категорія']
                apartment.number_of_rooms = row[' Кількість кімнат']
                apartment.article = row['Посилання на статтю']
                apartment.floor = row['Поверх'] if pd.notnull(row['Поверх']) else None
                apartment.metro = row['Метро'] if pd.notnull(row['Метро']) else None
                apartment.additional_info = row['Додаткова інформація'] if pd.notnull(row['Додаткова інформація']) else None
                await session.commit()

