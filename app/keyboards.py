from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                           InlineKeyboardMarkup, InlineKeyboardButton)

from app.database.models import async_session, Apartment
from sqlalchemy.future import select

main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Орендувати квартиру 🏠", callback_data="rent")],
        [InlineKeyboardButton(text="Купити квартиру 💵", callback_data="buy")],
        [InlineKeyboardButton(text="Здати/Продати квартиру 💸", callback_data="submit")],
    ], input_field_placeholder="Зрозумів тебе"
)   

async def get_rooms_keyboard(selected_rooms=None):
    if selected_rooms is None:
        selected_rooms = set()
    
    async with async_session() as session:
        stmt = select(Apartment.number_of_rooms).distinct()
        result = await session.execute(stmt)
        room_numbers = result.scalars().all()
    
    buttons = []
    for room in room_numbers:
        text = f"Room {room}"
        if str(room) in selected_rooms:
            text += " ✅"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"room_{room}")])
    
    buttons.append([InlineKeyboardButton(text="Done", callback_data="rooms_done")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    return keyboard


async def get_regions_keyboard(selected_regions=None):
    if selected_regions is None:
        selected_regions = set()
    
    async with async_session() as session:
        stmt = select(Apartment.region).distinct()
        result = await session.execute(stmt)
        regions = result.scalars().all()
    
    buttons = []
    for region in regions:
        text = f"Region {region}"
        if region in selected_regions:
            text += " ✅"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"region_{region}")])
    
    buttons.append([InlineKeyboardButton(text="Done", callback_data="regions_done")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    return keyboard

async def get_prev_next_keyboard(saved=True):
    keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="⬅️ Назад", callback_data="prev"),
                    InlineKeyboardButton(text="Збережено" if saved else "Зберегти", callback_data="saved" if saved else "save"),
                    InlineKeyboardButton(text="Вперед ➡️", callback_data="next")
                ]
            ]
        )
    return keyboard