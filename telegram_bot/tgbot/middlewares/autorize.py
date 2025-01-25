import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message
from config.telegram_bots import TelegramBotsConfig

class UserMiddleware(BaseMiddleware):
    def __init__(self, config) -> None:
        self.config: TelegramBotsConfig = config

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if not event.from_user.id in self.config.admins:
            await event.answer(text = f"You have not permited!", show_alert = True)
            return 

        return await handler(event, data)