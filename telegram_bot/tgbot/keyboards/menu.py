import logging
from aiogram.utils.keyboard import InlineKeyboardBuilder
from api.tron.account import AsyncAccount
from config import Config

from ..services.redis_db import RedisDB, MonitorData
from .callbacks import MenuNavigate, MenuActons

redis_config = Config.load_config().redis

redis_db = RedisDB(redis_config)
class MenuKeyboards:
    
    @staticmethod
    async def menu_keyboard(user_id):
        keybord = InlineKeyboardBuilder()

        
        monitors_button = InlineKeyboardBuilder().button(
            text = f"Runned monitorings: {len(await redis_db.get_active_monitors(user_id))}",
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
        
        show_monitorings = InlineKeyboardBuilder().button(
            text = f"My monitorings",
            callback_data = MenuNavigate(action = MenuActons.MY_MONITORINGS.value)
        )
        show_monitorings.adjust(1)
        keybord.attach(show_monitorings)
        
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
    
    @staticmethod
    async def show_montorings(user_id, query):
        monitorings = await redis_db.get_all_monitors(user_id)
        
        if not monitorings:
            back = InlineKeyboardBuilder().button(
            text = f"<<Back<<",
            callback_data = MenuNavigate(action = MenuActons.BACK)
            )
            back.adjust(1)
            
            query.message.answer(text = "No montorings", reply_markup = back.as_markup())
        
        for monitor in monitorings:
            keyboard = InlineKeyboardBuilder()
            account = AsyncAccount(private_key = monitor.private_key)
            
            trx_balance = float(await account.tron.get_account_balance(account.address))
            usdt_trc20_balance = await account.get_trc20_balance(account.address)
            account_resources = await account.tron.get_account_resource(account.address)
            current_transactions = await account.fetch_tron_transactions(account.address)
            
            message = f"""
            Monitor: {monitor.name} | Address: {account.address[:8]}
            TRX: {trx_balance} | USDt-TRC20: {usdt_trc20_balance}$
            Brandwidth: {account_resources.get("freeNetLimit", 0) - account_resources.get("freeNetUsed", 0)} | Energy: {account_resources.get("EnergyLimit", 0) - account_resources.get("EnergyUsed", 0)}
            Current transacions: {current_transactions}
            Is running: {monitor.is_running}
            """
            
            keyboard.button(
                text = f"{'Start' if not monitor.is_running else 'Stop'}",
                callback_data = MenuNavigate(action = MenuActons.MANAGE_MONITOR, type = "start" if not monitor.is_running else "stop", id = monitor.name)
            )
            
            keyboard.button(
                text = f"Remove",
                callback_data = MenuNavigate(action = MenuActons.MANAGE_MONITOR, type = "remove", id = monitor.name)
            )
            
            keyboard.button(
                text = f"Edit",
                callback_data = MenuNavigate(action = MenuActons.MANAGE_MONITOR, type = "edit", id = monitor.name)
            )
            
            keyboard.adjust(3)
            
            await query.message.answer(text = message, reply_markup = keyboard.as_markup())
            
    @staticmethod
    async def show_monitor(user_id, monitor_name, query):
        monitor = await redis_db.get_monitor(user_id, monitor_name)
        
        keyboard = InlineKeyboardBuilder()
        account = AsyncAccount(private_key = monitor.private_key)
        
        trx_balance = float(await account.tron.get_account_balance(account.address))
        usdt_trc20_balance = await account.get_trc20_balance(account.address)
        account_resources = await account.tron.get_account_resource(account.address)
        current_transactions = await account.fetch_tron_transactions(account.address)
        
        message = f"""
        Monitor: {monitor.name} | Address: {account.address[:8]}
        TRX: {trx_balance} | USDt-TRC20: {usdt_trc20_balance}$
        Brandwidth: {account_resources.get("freeNetLimit", 0) - account_resources.get("freeNetUsed", 0)} | Energy: {account_resources.get("EnergyLimit", 0) - account_resources.get("EnergyUsed", 0)}\n
        Current transacions: {current_transactions}
        Is running: {monitor.is_running}
        """
        keyboard.button(
            text = f"{'Start' if not monitor.is_running else 'Stop'}",
            callback_data = MenuNavigate(action = MenuActons.MANAGE_MONITOR, type = "start" if not monitor.is_running else "stop", id = monitor.name)
        )
        
        keyboard.button(
            text = f"Remove",
            callback_data = MenuNavigate(action = MenuActons.MANAGE_MONITOR, type = "remove", id = monitor.name)
        )
        
        keyboard.button(
            text = f"Edit",
            callback_data = MenuNavigate(action = MenuActons.MANAGE_MONITOR, type = "edit", id = monitor.name)
        )
        
        keyboard.adjust(3)
        
        await query.message.edit_text(text = message, reply_markup = keyboard.as_markup())