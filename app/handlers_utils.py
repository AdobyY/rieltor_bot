from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

import re
import pandas as pd
from typing import Union

import app.keyboards as kb
from app.database.models import async_session, Apartment, SavedApartment
from app.constants import GOOGLE_SHEET_URL


def convert_google_sheet_url(url):
    # Regular expression to match and capture the necessary part of the URL
    pattern = r'https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)(/edit#gid=(\d+)|/edit.*)?'

    # Replace function to construct the new URL for CSV export
    # If gid is present in the URL, it includes it in the export URL, otherwise, it's omitted
    replacement = lambda m: f'https://docs.google.com/spreadsheets/d/{m.group(1)}/export?' + (f'gid={m.group(3)}&' if m.group(3) else '') + 'format=csv'

    # Replace using regex
    new_url = re.sub(pattern, replacement, url)

    return new_url

def get_data():
    url = convert_google_sheet_url(GOOGLE_SHEET_URL)
    df = pd.read_csv(url)
    return(df)


async def search_results(message: Message, state: FSMContext):
    data = await state.get_data()
    selected_rooms = data.get("selected_rooms", set())
    selected_regions = data.get("selected_regions", set())
    min_price = data.get("min_price", 0)
    max_price = data.get("max_price", float('inf'))

    async with async_session() as session:
        stmt = select(Apartment).where(
            Apartment.number_of_rooms.in_(selected_rooms),
            Apartment.region.in_(selected_regions),
            Apartment.price.between(min_price, max_price)
        )
        result = await session.execute(stmt)
        apartments = result.scalars().all()

    if not apartments:
        await message.answer("На жаль, у нас нічого немає для тебе. Можливо, спробуй пізніше. \n Ти завжди можеш змінити параметри пошуку за допомогою кнопки знизу ⬇️",
                             reply_markup=kb.main)
        await state.clear()
        return

    await state.update_data(apartments=apartments, current_index=0)

    await send_apartment_message(message, apartments, 0)


async def send_apartment_message(entity: Union[Message, CallbackQuery], apartments: list, index: int):
    apartment = apartments[index]
    total_count = len(apartments)
    
    result_text = (
        f"📝 <b>Результат</b> {index + 1}/{total_count}\n\n"
        f"⚡️ <a href='{apartment.article}'>{apartment.code}</a>\n"
        f"🏠 Кімнат: {apartment.number_of_rooms}\n"
        f"📐 {apartment.area}m^2\n"
        f"📍 {apartment.region} район. {apartment.address}\n"
        f"🏢 Житловий комплекс: {apartment.residential_complex}\n"
        f"💵 Ціна: {apartment.price}\n"
        f"🔺 Поверх: {apartment.floor}/{apartment.total_floors}"
    )
    
    # Add conditional information
    if apartment.pets_allowed == "Так":
        result_text += "\n🐾 Можна з тваринками!!"
    if apartment.can_purchase == "Так":
        result_text += "\n✅ Готова до купівлі"

    user_id = entity.from_user.id if isinstance(entity, Message) else entity.message.chat.id
    async with async_session() as session:
        stmt = select(SavedApartment).where(
            SavedApartment.user_id == user_id,
            SavedApartment.apartment_id == apartment.id
        )
        result = await session.execute(stmt)
        is_saved = result.scalars().first() is not None

    if isinstance(entity, Message):
        try:
            await entity.edit_text(result_text, reply_markup=await kb.get_prev_next_keyboard(saved=is_saved, apartment_id=apartment.id), parse_mode="HTML")
        except TelegramBadRequest:
            await entity.answer(result_text, reply_markup=await kb.get_prev_next_keyboard(saved=is_saved, apartment_id=apartment.id), parse_mode="HTML")
    elif isinstance(entity, CallbackQuery):
        try:
            await entity.message.edit_text(result_text, reply_markup=await kb.get_prev_next_keyboard(saved=is_saved, apartment_id=apartment.id), parse_mode="HTML")
        except TelegramBadRequest:
            await entity.message.answer(result_text, reply_markup=await kb.get_prev_next_keyboard(saved=is_saved, apartment_id=apartment.id), parse_mode="HTML")


async def save_table_to_excel(session: AsyncSession, writer: pd.ExcelWriter, model, sheet_name: str):
    """Отримує всі записи з вказаної таблиці та зберігає їх в ексель файл."""
    stmt = select(model)
    result = await session.execute(stmt)
    df = pd.DataFrame([row.__dict__ for row in result.scalars().all()])
    df.to_excel(writer, sheet_name=sheet_name, index=False)