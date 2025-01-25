from dataclasses import dataclass
from typing import List

from .default_config import DefaultConfig


@dataclass
class TelegramBotsConfig(DefaultConfig):
    bot_api_key: str
    bot_announcement_api_key: str
    admins: List[int]
    dev_mode: bool
    default_recipient: str
    
    @staticmethod
    def from_env(env):
        bot_api_key = env.str("BOT_API_KEY")
        bot_announcement_api_key = env.str("BOT_ANNOUNCEMENT_KEY")
        admins = env.list("ADMINS", subcast = int)
        dev_mode = env.bool("DEV_MODE")
        default_recipient= env.str("DEFAULT_RECIPIENT")
        
        return TelegramBotsConfig(
            bot_api_key = bot_api_key,
            bot_announcement_api_key = bot_announcement_api_key,
            admins = admins,
            dev_mode = dev_mode,
            default_recipient = default_recipient
        )