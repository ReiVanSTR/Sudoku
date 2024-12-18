from dataclasses import dataclass
from typing import Optional
from environs import Env

from .tron import TronConfig


@dataclass
class Config:
    """
    variable: Optional[Config]
    """

    tron: Optional[TronConfig]

    
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
        tron = TronConfig.from_env(env)
    )