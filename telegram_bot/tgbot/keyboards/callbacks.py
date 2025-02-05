from aiogram.filters.callback_data import CallbackData
from typing import Optional
from enum import Enum
from pydantic import Field


class MenuActons(Enum):
    IGNORE = "IGNORE"
    NEW_MONITORING = "NEW_MONITORING"
    MY_MONITORINGS = "MY_MONITORINGS"
    BACK = "BACK"
    
    CREATE_MONITORING = "CREATE_MONITORING"
    MANAGE_MONITOR = "MANAGE_MONITOR"

class MenuNavigate(CallbackData, prefix = "menu"):
    action: str
    type: Optional[str] = Field(default="")
    id: Optional[str] = Field(default="")