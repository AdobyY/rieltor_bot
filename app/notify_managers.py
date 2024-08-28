# notifications.py
import os
from aiogram import Bot
from sqlalchemy.future import select
from dotenv import load_dotenv

from aiogram.types import Message

from app.database.models import Apartment
from app.database.models import async_session
from app.constants import *


load_dotenv()

API_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=API_TOKEN)

async def notify_managers(apartment_id: int, message: Message, phone_number):
    async with async_session() as session:
        stmt = select(Apartment).where(Apartment.id == apartment_id)
        result = await session.execute(stmt)
        apartment = result.scalar_one_or_none()
        
        if apartment is None:
            print(f"Apartment with ID {apartment_id} not found")
            return

        message_text = (
            f"Користувач {message.from_user.full_name} (ID: {message.from_user.id}) \n{message.from_user.username}\nЗ номером телефону: {phone_number}\nХоче записатись на перегляд квартири:\n\n"
            f"⚡️<a href='{apartment.article}'>{apartment.code}</a>\n"
            f"🏘 Кімнат: {apartment.number_of_rooms}\n"
            f"{apartment.area}m^2\n"
            f"📍{apartment.region} район. {apartment.address}\n"
            f"🌄Житловий комплекс: {apartment.apartment_complex}\n"
            f"💵Ціна: {apartment.price}\n"
            f"🔺Поверх: {apartment.floor}/{apartment.total_floors}\n"
            f"Можна з тваринками!!\n" if apartment.floor == "Так" else ""
            f"Готова до купівлі" if apartment.floor == "Так" else ""
        )

        for manager_id in MANAGERS:
            try:
                await bot.send_message(chat_id=manager_id, text=message_text, parse_mode="HTML")
            except Exception as e:
                print(f"Failed to send message to manager {manager_id}: {e}")
