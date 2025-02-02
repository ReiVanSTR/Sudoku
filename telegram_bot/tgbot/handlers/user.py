from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

user_router = Router()


@user_router.message(CommandStart())
async def user_start(message: Message):
    await message.reply(f"Hello {message.from_user.username}")
    
@user_router.message(Command("announce"))
async def announce(message: Message, broadcaster):
    await message.answer(f"Processing")
    await broadcaster("Test announcement \nuptime: 100% \n Active proxies: 5 \n Active api keys: 39")
    
@user_router.message(Command("menu"))
async def menu(message: Message, broadcaster):
    await message.answer(f"Processing")
    await broadcaster("Test announcement")