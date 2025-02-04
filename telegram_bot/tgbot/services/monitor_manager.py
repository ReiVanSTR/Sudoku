import asyncio
from .redis_db import MonitorData
from api.tron.account import AsyncAccount
from logger.tgbot_announcement import tga_logger, broadcaster

class MonitorsManager:
    def __init__(self):
        self.tasks = {}
        self.broadcaster = broadcaster
        self.tga_logger = tga_logger
    
    async def create_monitor(self, private_key: str, monitor: MonitorData):
        try:
            account = AsyncAccount(private_key = private_key)
            
            if account.address in self.tasks and not self.tasks[account.address].done():
                return (False, f"Monitoring for {account.address} already running!")
            
            async def monitor_wrapper():
                try:
                    await account.run_monitoring(
                        recipient_address=monitor.recipient_address,
                        min_amount=monitor.min_amount,
                        threshold=monitor.threshold
                    )
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