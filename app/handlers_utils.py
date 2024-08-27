from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

import pandas as pd
from typing import Union

import app.keyboards as kb
from app.database.models import async_session, Apartment, SavedApartment


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
        f"<b>Результат</b> {index + 1}/{total_count}\n\n"
        f"📍Адреса: {apartment.address}\n"
        f"💵Ціна: {apartment.price}$\n"
        f"🌄Регіон: {apartment.region}\n"
        f"🏘Кількість кімнат: {apartment.number_of_rooms}\n"
        f"🔺Поверх: {apartment.floor}\n"
        f"〽️Метро: {apartment.metro}\n"
        f"{'' if apartment.additional_info is None else f'❕{apartment.additional_info}'}\n"
        f'⚡️<a href="{apartment.article}">Стаття</a>\n'
    )

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