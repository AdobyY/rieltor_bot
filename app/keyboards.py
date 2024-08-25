from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                           InlineKeyboardMarkup, InlineKeyboardButton)

from app.database.models import async_session, Apartment
from sqlalchemy.future import select

start = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Орендувати квартиру 🏠", callback_data="rent")],
        [InlineKeyboardButton(text="Купити квартиру 💵", callback_data="buy")],
        [InlineKeyboardButton(text="Здати/Продати квартиру 💸", callback_data="sell")],
    ], input_field_placeholder="Вибери щосьь.."
)  

back = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="◀️ Повернутися назад", callback_data="back")]]
)  

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Змінити параметри пошуку 🔄")],
        [KeyboardButton(text="Збережені 🌟")],
        [KeyboardButton(text="Допомога 🆘")]
    ],
    resize_keyboard=True
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
        text = f"{room}"
        if str(room) in selected_rooms:
            text += " ✅"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"room_{room}")])
    
    if selected_rooms:
        buttons.append([InlineKeyboardButton(text="Далі ✅", callback_data="rooms_done")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    return keyboard



async def get_regions_keyboard(selected_regions=None):
    if selected_regions is None:
        selected_regions = set()
    
    async with async_session() as session:
        stmt = select(Apartment.region).distinct()
        result = await session.execute(stmt)
        regions = result.scalars().all()

    keyboard = []

    for i in range(0, len(regions), 2):
        buttons = [
            InlineKeyboardButton(
                text=f"{region} {'✅' if region in selected_regions else ''}",
                callback_data=f"region_{region}"
            ) for region in regions[i:i + 2]
        ]
        keyboard.append(buttons)
    
    select_all_button = InlineKeyboardButton(text="Обрати все", callback_data="select_all_regions")
    deselect_all_button = InlineKeyboardButton(text="Обрати нічого", callback_data="deselect_all_regions")
    
    # Add select all and deselect all buttons in one row
    keyboard.append([select_all_button, deselect_all_button])
    
    # Add the "Далі" button on a separate row if at least one region is selected
    if selected_regions:
        next_button = InlineKeyboardButton(text="Далі ✅", callback_data="regions_done")
        keyboard.append([next_button])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)



async def get_prev_next_keyboard(saved=True, apartment_id=None):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="prev"),
                InlineKeyboardButton(text="Збережено 🌟" if saved else "Зберегти", callback_data="saved" if saved else "save"),
                
                InlineKeyboardButton(text="Вперед ➡️", callback_data="next")
            ],
            [
                InlineKeyboardButton(text="Записатися на перегляд", callback_data=f"schedule_viewing_{apartment_id}")
            ]
        ]
    )
    return keyboard

confirmation = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Так, хочу", callback_data="confirm_viewing")],
                [InlineKeyboardButton(text="Ні, повернутися назад", callback_data="cancel_viewing")]
            ]
        )
