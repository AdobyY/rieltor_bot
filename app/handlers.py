from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from aiogram.fsm.context import FSMContext

import app.keyboards as kb
import app.database.requests as rq
from app.states import Register

from data import get_data

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    await rq.set_user(user.id, user.first_name, user.last_name, user.username)
    await message.answer(f'{user.username}, ти хочеш...', reply_markup=kb.main)

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


@router.message(F.text == 'Katalog')
async def katalog(message: Message):
    await message.answer('katalog!', reply_markup=kb.catalog)

@router.callback_query(F.data == 'one')
async def one(callback: CallbackQuery):
    await callback.answer("onee")
    await callback.message.answer('onee!', reply_markup=kb.catalog)

@router.message(Command('register'))
async def register(message: Message, state: FSMContext):
    await state.set_state(Register.name)
    await message.answer('Name?')

@router.message(Register.name)
async def register_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Register.age)
    await message.answer("Введіть вік:")

@router.message(Register.age)
async def register_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(Register.number)
    await message.answer("Введіть number:", reply_markup=kb.get_number)

@router.message(Register.number, F.contact)
async def register_number(message: Message, state: FSMContext):
    await state.update_data(number=message.contact.phone_number)
    data = await state.get_data()
    await message.answer(f"name: {data['name']}\nYears: {data['age']}\nNumber: {data['number']}")
    await state.clear()

    