import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message
from config.telegram_bots import TelegramBotsConfig
from ..services.redis_db import RedisDB


class UserMiddleware(BaseMiddleware):
    def __init__(self, config: TelegramBotsConfig, redis_db: RedisDB) -> None:
        self.config: TelegramBotsConfig = config
        self.redis_db: RedisDB = redis_db
        
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if not event.from_user.id in await self.redis_db.get_authorized_users():
            await event.answer(text = f"You have not permited!", show_alert = True)
            return
        
        if not await self.redis_db.get_user(event.from_user.id):
            await self.redis_db.create_user(event.from_user.id)

        return await handler(event, data)