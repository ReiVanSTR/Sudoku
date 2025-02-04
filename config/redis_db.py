from dataclasses import dataclass
from typing import List

from .default_config import DefaultConfig


@dataclass
class RedisConfig(DefaultConfig):
    host: str
    port: int
    decode_responses: bool
    username: str
    password: str
    
    @staticmethod
    def from_env(env):
        host = env.str("HOST")
        port = env.int("PORT")
        decode_resposes = env.bool("DECODE_RESPONSES")
        username = env.str("USERNAME")
        password = env.str("PASSWORD")
        
        return RedisConfig(
            host = host,
            port = port,
            decode_responses = decode_resposes,
            username = username,
            password = password
        )