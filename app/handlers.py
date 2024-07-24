from typing import Union
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
import app.database.requests as rq
from app.database.models import async_session, Apartment
from app.states import RentFlow

from sqlalchemy.future import select

from data import get_data


router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    await rq.set_user(user.id, user.first_name, user.last_name, user.username)
    await message.answer(f'{user.username}, ти хочеш...', reply_markup=kb.main)


@router.callback_query(F.data == "rent")
async def rent(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RentFlow.number_of_rooms)
    await callback.message.answer("Скільки кімнат у квартирі?", reply_markup=await kb.get_rooms_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("room_"))
async def select_room(callback: CallbackQuery, state: FSMContext):
    room_number = callback.data.split("_")[1]
    data = await state.get_data()
    selected_rooms = data.get("selected_rooms", set())
    
    if room_number in selected_rooms:
        selected_rooms.remove(room_number)
    else:
        selected_rooms.add(room_number)
    
    await state.update_data(selected_rooms=selected_rooms)
    await callback.message.edit_reply_markup(reply_markup=await kb.get_rooms_keyboard(selected_rooms))
    await callback.answer()

@router.callback_query(F.data == "rooms_done")
async def rooms_done(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RentFlow.region)
    await callback.message.answer("В якому регіоні ви шукаєте квартиру?", reply_markup=await kb.get_regions_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("region_"))
async def select_region(callback: CallbackQuery, state: FSMContext):
    region = callback.data.split("_")[1]
    data = await state.get_data()
    selected_regions = data.get("selected_regions", set())
    
    if region in selected_regions:
        selected_regions.remove(region)
    else:
        selected_regions.add(region)
    
    await state.update_data(selected_regions=selected_regions)
    await callback.message.edit_reply_markup(reply_markup=await kb.get_regions_keyboard(selected_regions))
    await callback.answer()

@router.callback_query(F.data == "regions_done")
async def regions_done(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RentFlow.price)
    await callback.message.answer("Яку суму ви бажаєте витратити? Наприклад: 1000-2000")
    await callback.answer()

@router.message(RentFlow.price)
async def rent_price(message: Message, state: FSMContext):
    price_range = message.text
    try:
        min_price, max_price = map(int, price_range.split("-"))
        # Оновлюємо стан з мінімальною та максимальною ціною
        await state.update_data(min_price=min_price, max_price=max_price)
    except ValueError:
        await message.answer("Неправильний формат ціни. Використовуйте формат '1000-2000'.")
        return

    # Переходимо до наступного етапу
    await state.set_state(RentFlow.results)
    await message.answer("Виконано пошук за вашими критеріями. Ось результати:")
    await search_results(message, state)  # Виклик функції для обробки результатів

@router.callback_query(F.data == "prev")
async def prev_apartment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    apartments = data.get("apartments", [])
    current_index = data.get("current_index", 0)

    if current_index > 0:
        new_index = current_index - 1
        await state.update_data(current_index=new_index)
        await send_apartment_message(callback, apartments, new_index)
    await callback.answer()

@router.callback_query(F.data == "next")
async def next_apartment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    apartments = data.get("apartments", [])
    current_index = data.get("current_index", 0)

    if current_index < len(apartments) - 1:
        new_index = current_index + 1
        await state.update_data(current_index=new_index)
        await send_apartment_message(callback, apartments, new_index)
    await callback.answer()

@router.callback_query(F.data == "save")
async def next_apartment(callback: CallbackQuery, state: FSMContext):
    await callback.answer(text='Зберегти')
    await callback.answer()

@router.callback_query(F.data == "saved")
async def next_apartment(callback: CallbackQuery, state: FSMContext):
    await callback.answer(text='Збережено')
    await callback.answer()



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
        await message.answer("Квартири не знайдено, що відповідають вашим критеріям.")
        await state.clear()
        return

    await state.update_data(apartments=apartments, current_index=0)

    # Надсилання першого повідомлення
    await send_apartment_message(message, apartments, 0)



async def send_apartment_message(entity: Union[Message, CallbackQuery], apartments: list, index: int):
    apartment = apartments[index]
    total_count = len(apartments)
    result_text = (
        f"Результат {index + 1}/{total_count}\n\n"
        f"Адреса: {apartment.address}\n"
        f"Ціна: {apartment.price}\n"
        f"Регіон: {apartment.region}\n"
        f"Кількість кімнат: {apartment.number_of_rooms}\n"
        f"Стаття: {apartment.article}\n"
        f"Поверх: {apartment.floor}\n"
        f"Метро: {apartment.metro}\n"
        f"Додаткова інформація: {apartment.additional_info}"
    )


    if isinstance(entity, Message):
        try:
            await entity.edit_text(result_text, reply_markup=await kb.get_prev_next_keyboard(False))
        except TelegramBadRequest:
            await entity.answer(result_text, reply_markup=await kb.get_prev_next_keyboard(False))
    elif isinstance(entity, CallbackQuery):
        try:
            await entity.message.edit_text(result_text, reply_markup=await kb.get_prev_next_keyboard(False))
        except TelegramBadRequest:
            await entity.message.answer(result_text, reply_markup=await kb.get_prev_next_keyboard(False))


@router.message(Command("help"))
async def cmd_start(message: Message):
    await message.answer('Hepl!')
    await message.reply('hepl')

@router.message(Command("update_data"))
async def update_data(message: Message):
    data = get_data()
    await rq.set_apartments(data)
    await message.answer("Дякую! Дані оновлено")
    await message.answer(data.to_string())


    