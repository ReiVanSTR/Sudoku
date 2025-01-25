from .user import user_router
from .runner import runner_router

routers_list = [
    user_router,
    runner_router
]

__all__ = [
    "routers_list"
]

