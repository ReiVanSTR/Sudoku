from redis import Redis
from typing import Union, List, Dict
from datetime import datetime
from dataclasses import dataclass

@dataclass
class MonitoringData:
    name: str
    date: datetime
    recipient_address: str
    min_amount: int
    threshold: float
    

@dataclass(init=False)
class UserData:
    user_id: int
    monitorings: List[MonitoringData]
    is_admin: bool
    
    def __init__(self, user_id, monitorings, is_admin):
        self.user_id = user_id
        self.monitorings = []
        self.is_admin = is_admin
        if monitorings:
            for monitoring in monitorings:
                self.monitorings.append(MonitoringData(**monitoring))



class RedisDB:
    def __init__(self, config):
        self.config = config
        self.redis = Redis(
            host = config.host,
            port=config.post,
            decode_responses=True,
            username=config.username,
            password=config.password,
        )
        self.key_prefix = "sudoku:"
        
        
    def key_generator(self, user_id) -> str:
        return f"{self.key_prefix}{user_id}"
    
    def get_user(self, user_id) -> Union[dict, bool]:
        response = self.redis.json().get(self.key_generator(user_id))
        if not response:
            return False
        
        return UserData(**response)
    
    def create_user(self, user_id) -> bool:
        if not self.get_user(user_id):
            self.redis.json().set(
                name = self.key_generator(user_id),
                path = "$",
                obj = {
                    "user_id": user_id,
                    "monitorings": [],
                    "is_admin": False
                }
            )