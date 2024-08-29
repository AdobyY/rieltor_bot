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
 

async def set_apartments(df: pd.DataFrame):
    async with async_session() as session:
        existing_apartments = await session.execute(select(Apartment))
        existing_apartments = existing_apartments.scalars().all()

        df_codes = set(df['Код'])

        # Видалити квартири з бази даних, яких немає в DataFrame
        for apartment in existing_apartments:
            if apartment.code not in df_codes:
                await session.delete(apartment)
        
        await session.commit()

        for index, row in df.iterrows():
            apartment = await session.scalar(select(Apartment).where(Apartment.code == row['Код']))
            
            if not apartment:
                new_apartment = Apartment(
                    code=row['Код'],
                    address=row['Адреса'],
                    region=row['Район'],
                    residential_complex=row['ЖК'],
                    area=row['Квадратура'],
                    price=row['Ціна ($)'],
                    number_of_rooms=row['Кількість кімнат'],
                    floor=row['Поверх'] if pd.notnull(row['Поверх']) else None,
                    total_floors=row['Всього поверхів'] if pd.notnull(row['Всього поверхів']) else None,
                    pets_allowed=row['Тваринки (так/ні)'],
                    can_purchase=row['Чи можна купити квартиру?'],
                    article=row['Посилання на статтю']
                )
                session.add(new_apartment)
            else:
                apartment.address = row['Адреса']
                apartment.region = row['Район']
                apartment.residential_complex = row['ЖК']
                apartment.area = row['Квадратура']
                apartment.price = row['Ціна ($)']
                apartment.number_of_rooms = row['Кількість кімнат']
                apartment.floor = row['Поверх'] if pd.notnull(row['Поверх']) else None
                apartment.total_floors = row['Всього поверхів'] if pd.notnull(row['Всього поверхів']) else None
                apartment.pets_allowed = row['Тваринки (так/ні)']
                apartment.can_purchase = row['Чи можна купити квартиру?']
                apartment.article = row['Посилання на статтю']
        
        await session.commit()

