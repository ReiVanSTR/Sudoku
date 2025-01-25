from api.tron.account import AsyncAccount
import asyncio
# from telegram_bot.bot import main as bot
from logger import broadcaster

# async def main():

#     acc = AsyncAccount(".mnemo/anal")
#     try:
#         await asyncio.gather(acc.run_monitoring(threshold = 0.5, recipient_address = "TSfQfJx6bAyCSYELfHcgvDQGQJPC7Nrv7z", min_amount = 5, spread = 1), bot())
#     except (KeyboardInterrupt, SystemExit):
#         broadcaster("Bot stopped")
    
    
# if __name__ == "__main__":
#     asyncio.run(main())
from telegram_bot.bot import main as bot

async def main():
    try:
        await bot()
    except (KeyboardInterrupt, SystemExit):
        broadcaster("Bot stopped")

if __name__ == "__main__":
    asyncio.run(main())