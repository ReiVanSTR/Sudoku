import redis.asyncio as redis
from typing import Union, List, Dict
from datetime import datetime
from dataclasses import dataclass

@dataclass
class MonitorData:
    name: str
    date: datetime
    recipient_address: str
    min_amount: int
    threshold: float
    private_key: str
    created_by: int
    is_running: bool
    

@dataclass(init=False)
class UserData:
    user_id: int
    monitorings: List[MonitorData]
    is_admin: bool
    
    def __init__(self, user_id, monitorings, is_admin):
        self.user_id = user_id
        self.monitorings = []
        self.is_admin = is_admin
        if monitorings:
            for monitoring in monitorings:
                self.monitorings.append(MonitorData(**monitoring))



class RedisDB:
    def __init__(self, config):
        self.config = config
        self.redis = redis.Redis(
            host = config.host,
            port=config.port,
            decode_responses=True,
            username=config.username,
            password=config.password,
        )
        self.key_prefix = "sudoku:"
        
        
    def key_generator(self, user_id) -> str:
        return f"{self.key_prefix}{user_id}"
    
    async def get_user(self, user_id) -> Union[dict, bool]:
        response = await self.redis.json().get(self.key_generator(user_id))
        if not response:
            return False
        
        return UserData(**response)
    
    async def create_user(self, user_id) -> bool:
        if not await self.get_user(user_id):
            await self.redis.json().set(
                name = self.key_generator(user_id),
                path = "$",
                obj = {
                    "user_id": user_id,
                    "monitorings": [],
                    "is_admin": False
                }
            )
            return True
        
        return False
            
    async def remove_user(self, user_id) -> bool:
        user = await self.get_user(user_id)
        
        if not user:
            return False
        
        await self.redis.json().delete(self.key_generator(user_id))
        
        return True
    
    
    async def append_monitor(
        self, 
        user_id: int,
        monitor: MonitorData
    ) -> bool:
        key = self.key_generator(user_id)
        if await self.redis.json().get(key, f"$.monitorings[?@.name=='{monitor.name}']"):
            raise ValueError(f"Monitor {monitor.name} already appended!")
        
        await self.redis.json().arrappend("sudoku:585708940", "$.monitorings", monitor.__dict__)
        
        return True
    
    async def get_monitor(self, user_id, monitor_name) -> Union[MonitorData, bool]:
        response = await self.redis.json().get(self.key_generator(user_id), f"$.monitorings[?@.name=='{monitor_name}']")
        
        if response:
            return MonitorData(**response[0])
        
        return False
    
    async def remove_monitor(self, user_id, monitor_name) -> bool:
        if not await self.get_monitor(user_id, monitor_name):
            raise ValueError(f"Monitor {monitor_name} not exists!")
        
        await self.redis.json().delete(self.key_generator(user_id), f"$.monitorings[?@.name=='{monitor_name}']")
        return True
    
    async def get_all_monitors(self, user_id) -> Union[List[Dict], bool]:
        key = self.key_generator(user_id)
        response = await self.redis.json().get(key, "$.monitorings")
        
        if response:
            return response[0]
        
        return False
    
    async def get_monitor_by_private_key(self, user_id, private_key) -> Union[MonitorData, bool]:
        response = await self.redis.json().get(self.key_generator(user_id), f"$.monitorings[?@.private_key=='{private_key}']")
        
        if response:
            return MonitorData(**response[0])
        
        return False
        