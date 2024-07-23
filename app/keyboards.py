from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                           InlineKeyboardMarkup, InlineKeyboardButton)

main = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Орендувати квартиру 🏠", callback_data="orenda")],
                                     [InlineKeyboardButton(text="Купити квартиру 💵", callback_data="buy")],
                                     [InlineKeyboardButton(text="Здати/Продати квартиру 💸", callback_data="sell")]],
                            input_field_placeholder="Зрозумів тебе")

catalog = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="1", callback_data="one")],
                                                [InlineKeyboardButton(text="2", callback_data="two")],
                                                [InlineKeyboardButton(text="3", callback_data="three")]])

get_number = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Відправити контакт',
                                                           request_contact=True)]], 
                                                           resize_keyboard=True)