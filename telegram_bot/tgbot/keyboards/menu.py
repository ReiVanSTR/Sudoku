import logging
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ..services.redis_db import RedisDB, UserData
from config import Config

from .callbacks import MenuNavigate, MenuActons

redis_config = Config.load_config().redis

redis_db = RedisDB(redis_config)
class MenuKeyboards:
    
    @staticmethod
    async def menu_keyboard(user_id):
        keybord = InlineKeyboardBuilder()

        
        monitors_button = InlineKeyboardBuilder().button(
            text = f"Runned monitorings: {len(await redis_db.get_all_monitors(user_id))}",
            callback_data = MenuNavigate(action = MenuActons.IGNORE)
        )
        monitors_button.adjust(1)
        keybord.attach(monitors_button)
        
        run_monitoring = InlineKeyboardBuilder().button(
            text = f"New monitoring",
            callback_data = MenuNavigate(action = MenuActons.NEW_MONITORING.value)
        )
        run_monitoring.adjust(1)
        keybord.attach(run_monitoring)
        
        return keybord.as_markup()
    
    @staticmethod
    def new_monitoring(data):
        keybord = InlineKeyboardBuilder()
        
        name = InlineKeyboardBuilder().button(
            text = f"Name: {data.get('name', '')}",
            callback_data = MenuNavigate(action = MenuActons.NEW_MONITORING, type = "name")
        )
        name.adjust(1)
        keybord.attach(name)
        
        recipient_address = InlineKeyboardBuilder().button(
            text = f"Recipient address: {data.get('recipient_address', '')}",
            callback_data = MenuNavigate(action = MenuActons.NEW_MONITORING, type = "recipient_address")
        )
        recipient_address.adjust(1)
        keybord.attach(recipient_address)
        
        min_amount = InlineKeyboardBuilder().button(
            text = f"Min amount: {data.get('min_amount', 1)}",
            callback_data = MenuNavigate(action = MenuActons.NEW_MONITORING, type = "min_amount")
        )
        min_amount.adjust(1)
        keybord.attach(min_amount)
        
        threshold = InlineKeyboardBuilder().button(
            text = f"Threshold: {data.get('threshold', 1)}",
            callback_data = MenuNavigate(action = MenuActons.NEW_MONITORING, type = "threshold")
        )
        threshold.adjust(1)
        keybord.attach(threshold)
        
        mnemonic = InlineKeyboardBuilder().button(
            text = f"Recovery frase: {data.get('mnemonic', '')}" if data.get('mnemonic', '') == "Required" else f"Recovery frase: private key",
            callback_data = MenuNavigate(action = MenuActons.NEW_MONITORING, type = "mnemonic")
        )
        mnemonic.adjust(1)
        keybord.attach(mnemonic)
        
        commit_keyboard = InlineKeyboardBuilder()
        
        commit_keyboard.button(
            text = "Create & run",
            callback_data = MenuNavigate(action = MenuActons.CREATE_MONITORING, type = "create_and_run")
        )
        commit_keyboard.button(
            text = "Create",
            callback_data = MenuNavigate(action = MenuActons.CREATE_MONITORING, type = "create")
        )
        
        commit_keyboard.button(
            text = "Clear",
            callback_data = MenuNavigate(action = MenuActons.CREATE_MONITORING, type = "clear")
        )
        commit_keyboard.adjust(3)
        keybord.attach(commit_keyboard)
        
        back = InlineKeyboardBuilder().button(
            text = f"<<Back<<",
            callback_data = MenuNavigate(action = MenuActons.BACK)
        )
        back.adjust(1)
        keybord.attach(back)
        
        return keybord.as_markup()