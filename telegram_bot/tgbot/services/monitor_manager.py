import asyncio
from .redis_db import MonitorData
from api.tron.account import AsyncAccount
from tronpy.keys import PrivateKey
from logger.tgbot_announcement import tga_logger, broadcaster
from .redis_db import RedisDB

from config import Config
redis_config = Config.load_config().redis

redis_db = RedisDB(redis_config)

class MonitorsManager:
    def __init__(self):
        self.tasks = {}
        self.broadcaster = broadcaster
        self.tga_logger = tga_logger
    
    async def create_monitor(self, monitor: MonitorData):
        try:
            account = AsyncAccount(private_key = monitor.private_key)
            
            if account.address in self.tasks and not self.tasks[account.address].done():
                return (False, f"Monitoring for {account.address} already running!")
            
            async def monitor_wrapper():
                try:
                    await account.run_monitoring(monitor)
                except Exception as e:
                    await self.tga_logger(monitor.created_by, f"[MonitorManager] Monitoring failed for {account.address}: {str(e)}")

            task = asyncio.create_task(
                monitor_wrapper(),
                name=f"monitor_{account.address}"
            )
            self.tasks[account.address] = task
            await self.tga_logger(monitor.created_by,f"[INFO] Started monitoring for {account.address}")
        except Exception as e:
            await self.tga_logger(monitor.created_by,f"[ERROR] Can't run monitoring for {account.address} \n Error:{e}")
            
    async def stop_monitor(self, monitor, user_id):
        address = PrivateKey(bytes.fromhex(monitor.private_key)).public_key.to_base58check_address()
        
        if address not in self.tasks or self.tasks[address].done():
            await self.tga_logger(user_id, f"[MonitorManager] Monitoring not started or already done.")
            return
        
        self.tasks[address].cancel()
        await self.tga_logger(user_id, f"[MonitorManager] Monitoring stoppped for {address}")
