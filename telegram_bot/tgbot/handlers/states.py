from aiogram.fsm.state import State, StatesGroup


class MenuStates(StatesGroup):
    _main = State()
    processing_new_monitoring = State()