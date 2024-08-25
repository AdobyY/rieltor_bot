from typing import Union
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, FSInputFile, ReplyKeyboardMarkup, KeyboardButton, ContentType
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

import pandas as pd

import os

import app.keyboards as kb
import app.database.requests as rq
from app.database.models import async_session, Apartment, SavedApartment, User
from app.states import RentFlow
from app.notify_managers import notify_managers
from app.constants import *

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from data import get_data

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    
    if user_id in MANAGERS:
        msg = await message.answer(
            f"""Привіт, {message.from_user.first_name}! 
Я тебе знаю, ти є менеджером, отже у тебе є додаткові права!
Тут ти можеш переглянути нові заявки на перегляди квартир.
            
<b>Ось команди, які тобі знадобляться:</b>

/update_data - щоб синхронізувати дані з ексель листом, якщо ти вніс туди зміни

/get_data - щоб отримати поточний стан користувачів
            

Як виникнуть якісь питання, звертайся до розробника: {DEVELOPER}""", parse_mode="HTML"
        )
        # Закріплення повідомлення для менеджера
        await msg.pin()
    else:
        await message.answer(
            "Привіт, давай я допоможу тобі вибрати квартиру мрії!\nВибери те, що тобі потрібно!",
            reply_markup=kb.start  # Клавіатура для звичайних користувачів
        )

@router.message(Command("change_settings"))
@router.message(F.text == "Змінити параметри пошуку 🔄")
async def change(message: Message):
    user = message.from_user
    await rq.set_user(user.id, user.first_name, user.last_name, user.username)
    await message.answer(f'Гаразд, давай щось змінимо.\nОтже, {user.first_name or user.username}, ти хочеш...', reply_markup=kb.start)


# Орендуємо і купуємо квартиру, поки дві кнопки виконують одне і теж
@router.callback_query(F.data == "rent")
@router.callback_query(F.data == "buy")
async def rent(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RentFlow.number_of_rooms)
    await callback.message.answer("Скільки кімнат у квартирі?", reply_markup=await kb.get_rooms_keyboard())
    await callback.answer()


# Здаємо квартиру
@router.callback_query(F.data == "sell")
async def sell(callback: CallbackQuery):
    await callback.message.answer("Напишіть нашому менеджеру \nmanager.username \nТам ви зможете розмістити свою квартиру у нашому боті!", reply_markup=kb.back)
    await callback.answer()


@router.callback_query(F.data == "back")
async def cmd_start(callback: CallbackQuery):
    user = callback.from_user 
    username = user.first_name or user.username 

    await callback.message.answer(f'Отже, {username}, ти хочеш...', reply_markup=kb.start)
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


@router.callback_query(F.data == "select_all_regions")
async def select_all_regions(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        stmt = select(Apartment.region).distinct()
        result = await session.execute(stmt)
        regions = result.scalars().all()
        
    all_regions = set(regions)
    current_data = await state.get_data()
    selected_regions = current_data.get('selected_regions', set())
    
    if selected_regions != all_regions:
        await state.update_data(selected_regions=all_regions)
        new_markup = await kb.get_regions_keyboard(all_regions)
        await callback.message.edit_reply_markup(reply_markup=new_markup)
        
    await callback.answer()


@router.callback_query(F.data == "deselect_all_regions")
async def deselect_all_regions(callback: CallbackQuery, state: FSMContext):
    current_data = await state.get_data()
    selected_regions = current_data.get('selected_regions', set())

    if selected_regions:
        await state.update_data(selected_regions=set())
        new_markup = await kb.get_regions_keyboard(set())
        await callback.message.edit_reply_markup(reply_markup=new_markup)
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

@router.callback_query(F.data.in_({"save", "saved"}))
async def handle_apartment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    apartments = data.get("apartments", [])
    current_index = data.get("current_index", 0)
    apartment = apartments[current_index]
    action = callback.data  # "save" або "saved"
    
    async with async_session() as session:
        async with session.begin():
            user_id = callback.from_user.id
            stmt = select(SavedApartment).where(
                SavedApartment.user_id == user_id,
                SavedApartment.apartment_id == apartment.id
            )
            result = await session.execute(stmt)
            saved_apartment = result.scalars().first()

            if action == "save":
                new_saved_apartment = SavedApartment(
                    user_id=user_id,
                    apartment_id=apartment.id
                )
                session.add(new_saved_apartment)
                await session.commit()

                await send_apartment_message(callback, apartments, current_index)  # Оновлення повідомлення
                await callback.answer(text='Збережено')

            elif action == "saved":
                await session.delete(saved_apartment)
                await session.commit()

                await send_apartment_message(callback, apartments, current_index)  # Оновлення повідомлення
                await callback.answer(text='Вилучено з збережених')


@router.message(F.text == "Збережені 🌟")
@router.message(Command("show_saved"))
async def view_saved_apartments(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        stmt = select(Apartment).join(SavedApartment).where(SavedApartment.user_id == user_id)
        result = await session.execute(stmt)
        saved_apartments = result.scalars().all()

    if not saved_apartments:
        await message.answer("Ви ще не зберегли жодної квартири.\n\n‼️Потрібно це виправити якнайшвидше‼️")
        return

    await message.answer("<b>Ось ваші збереження:</b>", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    await state.update_data(apartments=saved_apartments, current_index=0)
    await send_apartment_message(message, saved_apartments, 0)


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


@router.callback_query(F.data.startswith("schedule_viewing"))
async def schedule_viewing(callback: CallbackQuery, state: FSMContext):
    # Extract apartment ID from the callback data
    apartment_id = callback.data.split('_')[2]  # Assuming the ID is the last part after the last '_'
    print(apartment_id)
    # Convert apartment_id to integer if necessary
    try:
        apartment_id = int(apartment_id)
    except ValueError:
        await callback.answer("Невірний формат ID квартири.")
        return
    
    # Save the apartment ID in the state
    await state.update_data(apartment_id=apartment_id)
    
    # Set the state to wait for confirmation
    await state.set_state("waiting_for_confirmation")
    
    # Send confirmation message
    await callback.message.answer(
        "Ви дійсно бажаєте записатися на перегляд цієї квартири?\n\n"
        "Виберіть один з варіантів:",
        reply_markup=kb.confirmation 
    )
    await callback.answer()



@router.callback_query(F.data == "confirm_viewing")
async def confirm_viewing(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    apartment_id = data.get('apartment_id')

    # # Запит номера телефону у користувача
    # keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    # button = KeyboardButton(text="Поділитися номером телефону", request_contact=True)
    # keyboard.add(button)

    await callback.message.answer(
        "Будь ласка, надайте свій номер телефону для контакту з менеджером:",
        reply_markup=kb.rq_contact
    )
    # Збереження apartment_id в стані
    await state.update_data(apartment_id=apartment_id)
    await state.set_state(RentFlow.phone_number)  # Перехід до наступного стану
    
    await callback.answer()

@router.message(RentFlow.phone_number)
async def process_phone_number(message: Message, state: FSMContext):
    contact = message.contact
    phone_number = contact.phone_number
    data = await state.get_data()
    apartment_id = data.get('apartment_id')

    await notify_managers(apartment_id, message, phone_number)
    
    # Повідомлення користувачу про успішну відправку    
    await message.answer("Дякуємо! \nМенеджер зв'яжеться з вами!", reply_markup=kb.main)

    
    await state.clear()

@router.callback_query(F.data == "cancel_viewing")
async def cancel_viewing(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Запис на перегляд скасовано.", reply_markup=kb.main)
    await state.clear()
    await callback.answer()


@router.message(F.text == "Допомога 🆘")
@router.message(Command("help"))
async def cmd_start(message: Message):
    await message.answer(f'Якщо є питання, пиши нашому менеджеру {MANAGER_USERNAME}!', reply_markup=kb.main)

@router.message(F.text == "оновити")
@router.message(Command("update_data"))
async def update_data(message: Message):
    user_id = message.from_user.id

    # Перевірка, чи є користувач менеджером
    if user_id not in MANAGERS:
        await message.answer("У вас немає прав для цього(")
        return
    
    data = get_data()
    await rq.set_apartments(data)
    await message.answer("‼️ Готово! Дані синхронізовано ‼️")


@router.message(Command("get_data"))
async def get_user_data(message: Message):
    user_id = message.from_user.id
    
    # Перевірка, чи є користувач менеджером
    if user_id not in MANAGERS:
        await message.answer("У вас немає прав для отримання цих даних(")
        return
    
    # Отримання даних з бази та створення ексель файлу
    excel_file_path = os.path.join(os.getcwd(), "database_data.xlsx")
    async with async_session() as session:
        with pd.ExcelWriter(excel_file_path, engine='xlsxwriter') as writer:
            await save_table_to_excel(session, writer, Apartment, "Apartments")
            await save_table_to_excel(session, writer, User, "Users")
            await save_table_to_excel(session, writer, SavedApartment, "SavedApartments")
    # Відправка ексель файла менеджеру
    try:
        # Send the file directly using the file path
        await message.answer_document(
            document=FSInputFile(path="database_data.xlsx"),
            caption="Ось теперішня база"
            )
    except Exception as e:
        await message.answer(f"Помилка при відправці файлу: {str(e)}")


async def save_table_to_excel(session: AsyncSession, writer: pd.ExcelWriter, model, sheet_name: str):
    """Отримує всі записи з вказаної таблиці та зберігає їх в ексель файл."""
    stmt = select(model)
    result = await session.execute(stmt)
    df = pd.DataFrame([row.__dict__ for row in result.scalars().all()])
    df.to_excel(writer, sheet_name=sheet_name, index=False)

    