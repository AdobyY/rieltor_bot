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
            apartment = await session.scalar(select(Apartment).where(Apartment.code == row['Код']))  # Check by code
            
            if not apartment:
                new_apartment = Apartment(
                    code=row['Код'],  # Unique identifier
                    address=row['Адреса'],
                    region=row['Район'],  # New field updated
                    residential_complex=row['ЖК'],  # New field added
                    area=row['Квадратура'],  # Updated field
                    price=row['Ціна ($)'],  # Updated field
                    number_of_rooms=row['Кількість кімнат'],  # Updated field
                    floor=row['Поверх'] if pd.notnull(row['Поверх']) else None,
                    total_floors=row['Всього поверхів'] if pd.notnull(row['Всього поверхів']) else None,  # New field added
                    pets_allowed=row['Тваринки (так/ні)'] == 'Так',  # New field added, converted to boolean
                    can_purchase=row['Чи можна купити квартиру?'] == 'Так',  # New field added, converted to boolean
                    article=row['Посилання на статтю']
                )
                session.add(new_apartment)
                await session.commit()
            else:
                apartment.address = row['Адреса']
                apartment.region = row['Район']  # Update existing field
                apartment.residential_complex = row['ЖК']  # Update existing field
                apartment.area = row['Квадратура']  # Update existing field
                apartment.price = row['Ціна ($)']  # Update existing field
                apartment.number_of_rooms = row['Кількість кімнат']  # Update existing field
                apartment.floor = row['Поверх'] if pd.notnull(row['Поверх']) else None
                apartment.total_floors = row['Всього поверхів'] if pd.notnull(row['Всього поверхів']) else None  # Update existing field
                apartment.pets_allowed = row['Тваринки (так/ні)'] == 'Так'  # Update existing field, converted to boolean
                apartment.can_purchase = row['Чи можна купити квартиру?'] == 'Так'  # Update existing field, converted to boolean
                apartment.article = row['Посилання на статтю']  # Update existing field
                await session.commit()

