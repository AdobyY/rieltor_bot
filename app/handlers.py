from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, FSInputFile

from sqlalchemy.future import select

import app.keyboards as kb
import app.database.requests as rq
from app.constants import *
from app.states import RentFlow
from app.notify_managers import notify_managers
from app.database.models import async_session, Apartment, SavedApartment, User
from app.handlers_utils import *

import os
import pandas as pd


router = Router()


@router.message(CommandStart())
async def start(message: Message):
    user = message.from_user
    await rq.set_user(user.id, user.first_name, user.last_name, user.username)
    
    if user.id in MANAGERS:
        msg = await message.answer(
            f"""Привіт, {user.first_name}! 
Я тебе знаю, ти є менеджером, отже у тебе є додаткові права!
Тут ти можеш переглянути нові заявки на перегляди квартир.
            
<b>Ось команди, які тобі знадобляться:</b>

/update_data - щоб синхронізувати дані з ексель листом, якщо ти вніс туди зміни

/get_data - щоб отримати поточний стан користувачів

Ексель лист, в який потрібно добавляти квартирки знаходиться <a href='{GOOGLE_SHEET_URL}'>туть!</a>
            

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
    await message.answer(f'Гаразд, давай щось змінимо.\nОтже, {user.first_name or user.username}, ти хочеш...', reply_markup=kb.start)


@router.callback_query(F.data == "rent")
async def rent(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RentFlow.number_of_rooms)
    await callback.message.answer("Скільки кімнат повинно бути у квартирі?", reply_markup=await kb.get_rooms_keyboard())
    await callback.answer()


# Здаємо квартиру
@router.callback_query(F.data == "sell")
async def sell(callback: CallbackQuery):
    await callback.message.answer("Напишіть нашому менеджеру \nmanager.username \nТам ви зможете розмістити свою квартиру у нашому боті!", reply_markup=kb.back)
    await callback.answer()


@router.callback_query(F.data == "back")
async def cmd_start(callback: CallbackQuery):
    user = callback.from_user

    await callback.message.answer(f'Гаразд, давай щось змінимо.\nОтже, {user.first_name or user.username}, ти хочеш...', reply_markup=kb.start)
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
        await state.update_data(min_price=min_price, max_price=max_price)
    except ValueError:
        await message.answer("Неправильний формат ціни. Використовуйте формат '1000-2000'.")
        return

    await state.set_state(RentFlow.results)
    await message.answer("Виконано пошук за вашими критеріями. Ось результати:")
    await search_results(message, state) 


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
        await message.answer("Ви ще не зберегли жодної квартири.\nПотрібно це виправити якнайшвидше‼️\n\n Натискай 🌟 під оголошенням для додавання")
        return

    await message.answer("<b>Ось ваші збереження:</b>", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    await state.update_data(apartments=saved_apartments, current_index=0)
    await send_apartment_message(message, saved_apartments, 0)


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


@router.message(F.text == "отримати")
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
    try:
        # Send the file directly using the file path
        await message.answer_document(
            document=FSInputFile(path="database_data.xlsx"),
            caption="Ось теперішня база"
            )
    except Exception as e:
        await message.answer(f"Помилка при відправці файлу: {str(e)}")


@router.message(F.text)
async def handle_unknown_message(message: Message):
    await message.answer(f"Я не розумію... \nЯкщо потрібна допомога, пиши нашому менеджеру {MANAGER_USERNAME}!", reply_markup=kb.main)

    