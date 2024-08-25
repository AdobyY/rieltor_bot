from aiogram.fsm.state import State, StatesGroup

class RentFlow(StatesGroup):
    number_of_rooms = State()
    region = State()
    price = State()
    confirm = State()
    results = State()
    waiting_for_confirmation = State()
    phone_number = State()
