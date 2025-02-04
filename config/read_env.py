from dataclasses import dataclass
from typing import Optional
from environs import Env

from .tron import TronConfig
from .telegram_bots import TelegramBotsConfig
from .redis_db import RedisConfig


@dataclass
class Config:
    """
    variable: Optional[Config]
    """

    tron: Optional[TronConfig]
    telegram_bots: Optional[TelegramBotsConfig]
    redis: Optional[RedisConfig]

    @staticmethod
    def load_config(env_path: str = ".env"):
        
        """
        return Config(
            config_class.from_env(env)
        )
        """

        env = Env()
        try:
            env.read_env(env_path)
        except:
            raise f"Can't read {env_path}"
        
        return Config(
            tron = TronConfig.from_env(env),
            telegram_bots = TelegramBotsConfig.from_env(env),
            redis = RedisConfig.from_env(env)
        )