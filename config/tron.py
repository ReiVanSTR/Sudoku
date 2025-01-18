from dataclasses import dataclass
from environs import Env
from typing import List
from ast import literal_eval
import logging

from .default_config import DefaultConfig


def parse_user_agents(path: str):
    try:
        with open(path, "r") as file:
            content = file.read()
            return [item.get("useragent", "") for item in literal_eval(content)]
    except:
        logging.error(f"Can't read useragents path {path}")
        
@dataclass(init = False)
class TronConfig(DefaultConfig):
    trongrid_api_keys: list
    useragents_path: str
    useragents: List[str]
    proxies = List[dict]
    
    def __init__(
        self, 
        trongrid_api_keys,
        useragents_path,
        proxies
    ):
        self.trongrid_api_keys = trongrid_api_keys
        self.useragents = parse_user_agents(path = useragents_path)
        self.proxies = [{'http':proxy} for proxy in proxies]
        
    
    @staticmethod
    def from_env(env: Env):
        trongrid_api_keys = env.list("TRONGRID_API_KEYS")
        useragents_path = env.str("USERAGENTS_PATH")
        proxies = env.list("PROXIES")
        
        return TronConfig(
            trongrid_api_keys = trongrid_api_keys,
            useragents_path = useragents_path,
            proxies = proxies
        )
    