import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from api.tron.memonic import generate_tron_private_key
from tronpy.keys import PrivateKey

from ..keyboards.menu import MenuKeyboards
from ..keyboards.callbacks import MenuNavigate, MenuActons
from .states import MenuStates
from ..services.redis_db import RedisDB, MonitorData
from ..services.monitor_manager import MonitorsManager

user_router = Router()


@user_router.message(CommandStart())
async def user_start(message: Message):
    await message.reply(f"Hello {message.from_user.username}")
    
@user_router.message(Command("announce"))
async def announce(message: Message, broadcaster):
    await message.answer(f"Processing")
    await broadcaster("Test announcement \nuptime: 100% \n Active proxies: 5 \n Active api keys: 39")
    
@user_router.message(Command("menu"))
async def menu(message: Message, broadcaster, state: FSMContext):
    await state.set_state(MenuStates._main)
    await message.answer(f"Menu", reply_markup = await MenuKeyboards.menu_keyboard(message.from_user.id))
    
    
@user_router.callback_query(StateFilter(MenuStates._main), MenuNavigate.filter(F.action == MenuActons.MY_MONITORINGS.value))
async def show_monitorings(query: CallbackQuery, state: FSMContext, redis_db: RedisDB):
    await query.answer()
    await state.set_state(MenuStates.show_monitoring)
    await MenuKeyboards.show_montorings(query.from_user.id, query)


@user_router.callback_query(StateFilter(MenuStates.show_monitoring), MenuNavigate.filter(F.action == MenuActons.MANAGE_MONITOR.value))
async def manage_monitoring(query: CallbackQuery, state: FSMContext, redis_db: RedisDB, manager: MonitorsManager, callback_data: MenuNavigate):    
    activity_type = callback_data.type
    monitor = await redis_db.get_monitor(query.from_user.id, callback_data.id) # monitor name
    
    if activity_type == "stop":
        await manager.stop_monitor(monitor, query.from_user.id)
        await redis_db.update_monitor_status(query.from_user.id, monitor, False)
        await MenuKeyboards.show_monitor(query.from_user.id, monitor.name, query)
        
    if activity_type == "start":
        await manager.create_monitor(monitor = monitor)
        await redis_db.update_monitor_status(query.from_user.id, monitor, True)
        await MenuKeyboards.show_monitor(query.from_user.id, monitor.name, query)
        
    if activity_type == "remove":
        try:
            await manager.stop_monitor(monitor, query.from_user.id)
            await redis_db.remove_monitor(query.from_user.id, monitor.name)
            await query.message.delete()
            await MenuKeyboards.show_montorings(query.from_user.id, query)
        except:
            await query.answer(text = "Error", show_alert = True)
            
    if activity_type == "edit":
        if monitor.is_running:
            await query.answer(text = "Monitor must be stopped!", show_alert = True)
            return
        
        return await query.answer(text = "Будет время допишу", show_alert = True)
        
    await query.answer()
            
        
    
@user_router.callback_query(StateFilter(MenuStates._main), MenuNavigate.filter(F.action == MenuActons.NEW_MONITORING.value))
async def new_monitorig(query: CallbackQuery, state: FSMContext, redis_db: RedisDB, default_recipient):
    await query.answer()
    await state.set_state(MenuStates.processing_new_monitoring)
    await state.set_data({
        "name":f"{query.from_user.full_name}_monitor:{len(await redis_db.get_all_monitors(query.from_user.id))+1}",
        "recipient_address":default_recipient,
        "min_amount":1,
        "threshold":1,
        "mnemonic":"Required",
        "created_by":query.from_user.id
    })
    
    await query.message.answer(text = "New monitoring", reply_markup = MenuKeyboards.new_monitoring(await state.get_data()))
    
@user_router.callback_query(StateFilter(MenuStates.processing_new_monitoring), MenuNavigate.filter(F.action == MenuActons.NEW_MONITORING.value))
async def processing_new_monitoring(query: CallbackQuery, state: FSMContext, callback_data: MenuNavigate):
    await query.answer()
    await state.update_data({"current_key":callback_data.type})
    await query.message.answer(f"Input new value for {callback_data.type}")
        

@user_router.message(StateFilter(MenuStates.processing_new_monitoring), F.text.is_not(None))
async def validate_processing_input(message: Message, state: FSMContext, redis_db: RedisDB):
    data = await state.get_data()
    key = data.get("current_key", "")
    
    def is_valid_float(input_string):
        try:
            float(input_string)
            return True
        except ValueError:
            return False
    
    if key == "name":
        name = message.text.strip()
        
        if name.__len__() > 32 or name.__len__() < 3:
            await message.answer(f"Name can't be less than 3 and more than 32")
            return 
        
        if await redis_db.get_monitor(message.from_user.id, data.get("name")):
            await message.answer(f"Monitoring with this name already runned!")
            return
        
        await state.update_data({key:name})
        await message.answer(text = "New monitoring", reply_markup = MenuKeyboards.new_monitoring(await state.get_data()))
        
    if key == "recipient_address":
        recipient_address = message.text.strip()
        
        if recipient_address[0] != "T" or len(recipient_address) < 30:
            await message.answer(f"Incorrect recipient address")
            return 
        
        await state.update_data({key:recipient_address})
        await message.answer(text = "New monitoring", reply_markup = MenuKeyboards.new_monitoring(await state.get_data()))
        
    if key == "min_amount":
        min_amount = message.text.strip()
        
        if not is_valid_float(min_amount):
            await message.answer(f"Minimal amount must be int(1...999) or float(0.1...0.01)")
            return 
        
        await state.update_data({key:float(min_amount)})
        await message.answer(text = "New monitoring", reply_markup = MenuKeyboards.new_monitoring(await state.get_data()))
        
    if key == "threshold":
        threshold = message.text.strip()
        
        if not is_valid_float(threshold):
            await message.answer(f"Threshold amount must be int(1...999) or float(0.1...0.01)")
            return 
        
        await state.update_data({key:float(threshold)})
        await message.answer(text = "New monitoring", reply_markup = MenuKeyboards.new_monitoring(await state.get_data()))
        
    if key == "mnemonic":
        mnemonic = message.text.strip()
        
        if len(mnemonic.split(" ")) < 12:
            await message.answer("Mnemonic phrase must be equal 12 18 24 words")
            return
        
        private_key = generate_tron_private_key(mnemonic)
        if not private_key:
            await message.answer("Incorrect mnemonic frase")
            return
        
        if monitor:= await redis_db.get_monitor_by_private_key(message.from_user.id, private_key):
            await message.answer(f"Monitor with this private key already exists. {monitor.name}")
            return
        
        await state.update_data({key:private_key})
        await message.delete()
        await message.answer(text = "New monitoring", reply_markup = MenuKeyboards.new_monitoring(await state.get_data()))
        
    await state.update_data({
        "current_key":""
    })
        
@user_router.callback_query(StateFilter(MenuStates.processing_new_monitoring), MenuNavigate.filter(F.action == MenuActons.CREATE_MONITORING.value))
async def running_control(query: CallbackQuery, state: FSMContext, callback_data: MenuNavigate, manager: MonitorsManager, redis_db: RedisDB, default_recipient):
    data = await state.get_data()
    action_type = callback_data.type
    
    if action_type in ["create_and_run", "create"] and data.get("mnemonic") == "Required":
        await query.answer(text = "Field recovery frase is requred!", show_alert = True)
        return
    
    if action_type == "create_and_run":
        monitor = MonitorData(
                name = data.get("name"),
                date = datetime.now().isoformat(),
                recipient_address = data.get("recipient_address"),
                min_amount = data.get("min_amount"),
                threshold = data.get("threshold"),
                private_key = data.get("mnemonic"),
                created_by = data.get("created_by"),
                is_running = True
            )
        try:
            await manager.create_monitor(
                monitor = monitor
            )
            await redis_db.append_monitor(query.from_user.id, monitor)
            
            await query.answer()
            await query.message.answer(f"Menu", reply_markup = await MenuKeyboards.menu_keyboard(query.from_user.id))
            await state.set_state(MenuStates._main)
            
        except Exception as e:
            logging.log(30, e)
            await query.answer(f"Error with run monitoring. Send error log to @ivangooder", show_alert = True)
            
    if action_type == "create":
        monitor = MonitorData(
                name = data.get("name"),
                date = datetime.now().isoformat(),
                recipient_address = data.get("recipient_address"),
                min_amount = data.get("min_amount"),
                threshold = data.get("threshold"),
                private_key = data.get("mnemonic"),
                created_by = data.get("created_by"),
                is_running = False
            )
        
        await redis_db.append_monitor(query.from_user.id, monitor)
        
        await query.answer(text = f"Monitor {monitor.name} created! You can run it in 'My monitors'")
        
        await query.message.answer(f"Menu", reply_markup = await MenuKeyboards.menu_keyboard(query.from_user.id))
        await state.set_state(MenuStates._main)
        
    
    if action_type == "clear":
        await state.set_data({
            "name":f"{query.from_user.full_name}_monitor:{len(await redis_db.get_all_monitors(query.from_user.id))+1}",
            "recipient_address":default_recipient,
            "min_amount":1,
            "threshold":1,
            "mnemonic":"Required",
            "created_by":query.from_user.id
        })
        
        await query.message.delete()
        await query.message.answer(text = "New monitoring", reply_markup = MenuKeyboards.new_monitoring(await state.get_data()))
        
 
        
    


    
@user_router.callback_query(StateFilter(MenuStates), MenuNavigate.filter(F.action == MenuActons.BACK.value))
async def back(query: CallbackQuery, state: FSMContext):
    await query.answer()
    await state.set_state(MenuStates._main)
    await query.message.answer(f"Menu", reply_markup = await MenuKeyboards.menu_keyboard(query.from_user.id))
    
@user_router.message(StateFilter(MenuStates), Command("back"))
async def back(message: Message, state: FSMContext):
    await state.set_state(MenuStates._main)
    await message.answer(f"Menu", reply_markup = await MenuKeyboards.menu_keyboard(message.from_user.id))