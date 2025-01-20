import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from pytz import timezone
import os, sys

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


from config import Config, TelegramBotsConfig
from logger import setup_logging, tga_logger, broadcaster

from .tgbot.handlers import routers_list


config = Config.load_config().telegram_bots
setup_logging(loggig_level=logging.WARNING)

def register_global_middlewares(dp: Dispatcher, config: TelegramBotsConfig, session_pool=None):
    """
    Register global middlewares for the given dispatcher.
    Global middlewares here are the ones that are applied to all the handlers (you specify the type of update)

    :param dp: The dispatcher instance.
    :type dp: Dispatcher
    :param config: The configuration object from the loaded configuration.
    :param session_pool: Optional session pool object for the database using SQLAlchemy.
    :return: None
    """
    middleware_types = [
        # ConfigMiddleware(config),
        # UserMiddleware(),
        # PermissionsMiddleware(),
        # SessionMiddleware()
    ]

    for middleware_type in middleware_types:
        dp.message.outer_middleware(middleware_type)
        dp.callback_query.outer_middleware(middleware_type)
        
def get_storage():
    """
    Return storage based on the provided configuration.

    Args:
        config (Config): The configuration object.

    Returns:
        Storage: The storage object based on the configuration.

    """
    return MemoryStorage()

async def main():
    storage = get_storage()
    bot = Bot(token=config.bot_api_key)
    dp = Dispatcher(storage=storage)
    dp.include_routers(*routers_list)

    register_global_middlewares(dp, config)
    tz = timezone("Europe/Warsaw")
    await broadcaster(f"Started polling for bot {await bot.get_my_name()}")
    
    await dp.start_polling(bot, time = tz, tga_logger = tga_logger)

def restart_bot():
    logging.info("Перезапуск бота...")
    python = sys.executable
    os.execl(python, python, "-m", "telegram_bot.bot")
    
    
    
class FileSystemEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".py"):  # Можно настроить фильтр на конкретные файлы, если нужно
            logging.info("Обнаружено изменение в коде. Перезапуск бота...")
            restart_bot()


async def debug_main():
    if config.dev_mode:
        path_to_watch = 'telegram_bot'
        event_handler = FileSystemEventHandler()
        observer = Observer()
        observer.schedule(event_handler, path=path_to_watch, recursive=True)
        observer.start()
        
    bot_task = asyncio.create_task(
        coro = main(),
        name = "bot_task"
    )
    
    try:
        await bot_task
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped")
        

    if config.dev_mode:
        observer.stop()
        observer.join() 
        
if __name__ == "__main__":
    asyncio.run(debug_main())