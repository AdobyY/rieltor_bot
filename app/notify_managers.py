# notifications.py
import os
from aiogram import Bot
from aiogram.types import ParseMode
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv

from database.models import Apartment, SavedApartment
from database import async_session

load_dotenv()  # Load environment variables from a .env file

API_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=API_TOKEN)

async def notify_managers(apartment_id: int, user_id: int):
    async with async_session() as session:
        # Fetch apartment details
        stmt = select(Apartment).where(Apartment.id == apartment_id)
        result = await session.execute(stmt)
        apartment = result.scalar_one_or_none()
        
        if apartment is None:
            return
        
        # Prepare the message
        message = (
            f"Користувач (ID: {user_id}) вибрав квартиру:\n"
            f"Адреса: {apartment.address}\n"
            f"Ціна: {apartment.price} грн\n"
            "Зв'яжіться з користувачем, щоб домовитися про перегляд."
        )

        # Send the message to managers
        manager_ids = [625856657]  # Replace with actual manager IDs
        for manager_id in manager_ids:
            await bot.send_message(chat_id=manager_id, text=message, parse_mode="HTML")
