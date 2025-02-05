import redis.asyncio as redis
from typing import Union, List, Dict
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class SystemKeys(Enum):
    ALL_MONITORS = "ALL_MONITORS"
    RUNNED_MONITORS = "RUNNED_MONITORS"
    AUTHORIZED_USERS = "AUTHORIZED_USERS" 

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
        self.system_prefix = "sudoku:sys:"
        
        
        
    def key_generator(self, user_id) -> str:
        return f"{self.key_prefix}{user_id}"
    
    def system_key_generator(self, key: str) -> str:
        return f"{self.system_prefix}{key}"
    
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
            
            await self.redis.json().arrappend(
                self.system_key_generator(SystemKeys.AUTHORIZED_USERS.value),
                "$",
                {
                    "user_id": user_id,
                }
            )
            return True
        
        return False
            
    async def remove_user(self, user_id) -> bool:
        user = await self.get_user(user_id)
        
        if not user:
            return False
        
        await self.redis.json().delete(self.key_generator(user_id))
        await self.redis.json().delete(self.system_key_generator(SystemKeys.AUTHORIZED_USERS.value), f"$.[?@.user_id=={user_id}]")
        
        return True
    
    
    async def append_monitor(
        self, 
        user_id: int,
        monitor: MonitorData
    ) -> bool:
        key = self.key_generator(user_id)
        if await self.redis.json().get(key, f"$.monitorings[?@.name=='{monitor.name}']"):
            raise ValueError(f"Monitor {monitor.name} already appended!")
        
        await self.redis.json().arrappend(key, "$.monitorings", monitor.__dict__)
        await self.redis.json().arrappend(self.system_key_generator(SystemKeys.ALL_MONITORS.value), "$", monitor.__dict__)
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
        await self.redis.json().delete(self.system_key_generator(SystemKeys.ALL_MONITORS.value), f"$.[?@.name=='{monitor_name}']")
        return True
    
    async def get_all_monitors(self, user_id) -> Union[List[MonitorData], bool]:
        key = self.key_generator(user_id)
        response = await self.redis.json().get(key, "$.monitorings")
        
        if response:
            return [MonitorData(**monitor) for monitor in response[0]]
        
        return False
    
    async def get_monitor_by_private_key(self, user_id, private_key) -> Union[MonitorData, bool]:
        response = await self.redis.json().get(self.key_generator(user_id), f"$.monitorings[?@.private_key=='{private_key}']")
        
        if response:
            return MonitorData(**response[0])
        
        return False
    
    async def get_active_monitors(self, user_id) -> Union[List[MonitorData], bool]:
        key = self.key_generator(user_id)
        response = await self.redis.json().get(key, f"$.monitorings[?@.is_running==true]")
        
        if response:
            return [MonitorData(**monitor) for monitor in response]
        
        return []
    
    async def update_monitor_status(self, user_id, monitor: MonitorData, status: bool) -> bool:
        key = self.key_generator(user_id)
        path = f"$.monitorings[?(@.name=='{monitor.name}')].is_running"
       
        response = await self.redis.json().set(key, path, status)
        if response:
            
            if status:
                await self.redis.json().arrappend(self.system_key_generator(SystemKeys.RUNNED_MONITORS.value), "$", monitor.__dict__)
            else:    
                await self.redis.json().delete(self.system_key_generator(SystemKeys.RUNNED_MONITORS.value), f"$.[?@.name=='{monitor.name}']")
                
            return True
        
        return False
    
    async def get_runned_monitors(self):
        response = await self.redis.json().get(self.system_key_generator(SystemKeys.RUNNED_MONITORS.value))
        return [MonitorData(**monitor) for monitor in response]
    
    async def get_authorized_users(self):
        response = await self.redis.json().get(self.system_key_generator(SystemKeys.AUTHORIZED_USERS.value))
        return [uid.get("user_id") for uid in response]