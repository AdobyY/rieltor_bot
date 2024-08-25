# notifications.py
import os
from aiogram import Bot
from sqlalchemy.future import select
from dotenv import load_dotenv

from aiogram.types import Message

from app.database.models import Apartment
from app.database.models import async_session
from app.constants import *


load_dotenv()  # Load environment variables from a .env file

API_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=API_TOKEN)

async def notify_managers(apartment_id: int, message: Message, phone_number):
    async with async_session() as session:
        # Fetch apartment details
        stmt = select(Apartment).where(Apartment.id == apartment_id)
        result = await session.execute(stmt)
        apartment = result.scalar_one_or_none()
        
        if apartment is None:
            # If apartment is not found, log the error or handle it as needed
            print(f"Apartment with ID {apartment_id} not found")
            return

        # Log the fetched apartment details
        # print(f"Found apartment: {apartment}")

        # Prepare the message
        message_text = (
            f"Користувач {message.from_user.full_name} (ID: {message.from_user.id}) \n{message.from_user.username}\nЗ номером телефону: {phone_number}\nХоче записатись на перегляд квартири:\n\n"
            f"📍Адреса: {apartment.address}\n"
            f"💵Ціна: {apartment.price} грн\n"
            f"🌄Регіон: {apartment.region}\n"
            f"🏘Кількість кімнат: {apartment.number_of_rooms}\n"
            f"🔺Поверх: {apartment.floor}\n"
            f"〽️Метро: {apartment.metro}\n"
            f"{'' if apartment.additional_info is None else f'❕{apartment.additional_info}'}\n"
            f'⚡️<a href="{apartment.article}">Стаття</a>\n'
        )

        for manager_id in MANAGERS:
            try:
                await bot.send_message(chat_id=manager_id, text=message_text, parse_mode="HTML")
            except Exception as e:
                # Log or handle the exception as needed
                print(f"Failed to send message to manager {manager_id}: {e}")
