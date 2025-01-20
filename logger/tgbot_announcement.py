from aiogram import Bot, exceptions
from aiogram.types.inline_keyboard_markup import InlineKeyboardMarkup


import logging
import betterlogging as bl
import json
from datetime import date, datetime
from typing import Union
import asyncio
from typing import List

from config.read_env import Config
from .file_logger import file_logger

TGA_LOG_LEVEL = 25
TGA_LEVEL_NAME = "TGAnnouncement"
logging.addLevelName(TGA_LOG_LEVEL, TGA_LEVEL_NAME)
tg_config = Config.load_config().telegram_bots

bot = Bot(tg_config.bot_announcement_api_key)

async def send_message(
    bot: Bot,
    user_id: Union[int, str],
    text: str,
    disable_notification: bool = False,
    reply_markup: InlineKeyboardMarkup = None,
) -> bool:
    """
    Safe messages sender

    :param bot: Bot instance.
    :param user_id: user id. If str - must contain only digits.
    :param text: text of the message.
    :param disable_notification: disable notification or not.
    :param reply_markup: reply markup.
    :return: success.
    """
    try:
        await bot.send_message(
            user_id,
            text,
            disable_notification=disable_notification,
            reply_markup=reply_markup,
        )
    except exceptions.TelegramBadRequest as e:
        file_logger("Telegram server says - Bad Request: chat not found")
    except exceptions.TelegramForbiddenError:
        file_logger(f"Target [ID:{user_id}]: got TelegramForbiddenError")
    except exceptions.TelegramRetryAfter as e:
        file_logger(
            f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.retry_after} seconds."
        )
        await asyncio.sleep(e.retry_after)
        return await send_message(
            bot, user_id, text, disable_notification, reply_markup
        )  # Recursive call
    except exceptions.TelegramAPIError:
        file_logger(f"Target [ID:{user_id}]: failed")
    else:
        file_logger(f"Target [ID:{user_id}]: success")
        return True
    return False

def setup_tgbot_logger(bot):
    async def tga_logger(self, user_id, message):
        if self.isEnabledFor(TGA_LOG_LEVEL):
            await send_message(bot = bot, user_id = user_id, text = message)

    logging.Logger.tgannouncement = tga_logger

    logger = logging.getLogger('TGAnnouncement')
    logger.setLevel(TGA_LOG_LEVEL)

    return logger

async def broadcaster(text: str, users_list: List[int] = None, disable_notification: bool = False, ):
    if not users_list:
        users_list = tg_config.admins
    count = 0
    try:
        for user_id in users_list:
            if await send_message(
                bot, user_id, text, disable_notification
            ):
                count += 1
            await asyncio.sleep(
                0.05
            )  # 20 messages per second (Limit: 30 messages per second)
    finally:
        logging.info(f"{count} messages successful sent.")


tga_logger = setup_tgbot_logger(bot = bot).tgannouncement