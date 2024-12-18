from dataclasses import dataclass
from environs import Env


from .default_config import DefaultConfig

@dataclass
class TronConfig(DefaultConfig):
    api_key: str
    trongrid_api_key: str
    
    @staticmethod
    def from_env(env: Env):
        api_key = env.str("TRON_API_KEY")
        trongrid_api_key = env.str("TRONGRID_API_KEY")
        return TronConfig(
            api_key = api_key,
            trongrid_api_key = trongrid_api_key
        )
    