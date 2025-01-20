import random
from typing import Union, List, Dict, Any
from tronpy.providers import AsyncHTTPProvider
from urllib.parse import urljoin
import sys, os

import httpx
from httpx import Timeout


class AsyncProxymityProvider(AsyncHTTPProvider):
    def __init__(
        self,
        endpoint_uri: str = None,
        timeout: int = 1,
        api_key: Union[str, List[str]] = None,
        jw_token: str = None,
        proxies: List[Dict[str, str]] = None,
        user_agents: Union[List[str], str] = None,
    ):
        super().__init__(endpoint_uri, timeout, jw_token)
        self.api_key = api_key
        self.timeout = timeout
        self.user_agents = [user_agents] if isinstance(user_agents, str) else list(user_agents) if user_agents else []
        self.proxies = list(proxies) if proxies else []
        self.use_api_key = True
        

  
    async def make_request(self, method: str, params: Any = None) -> dict:
        if self.use_api_key:
            self.client.headers["Tron-Pro-Api-Key"] = self.random_api_key

        if params is None:
            params = {}

        # Используем случайные proxy и user-agent
        if self.proxies:
            self.client.proxies = self._choose_proxy()
            # logger.info(f"Used proxy: {self.client.proxies['http']}")

        if self.user_agents:
            self.client.headers["User-Agent"] = self._choose_user_agent()
            # logger.info(f"Used agent: {self.client.headers['User-Agent']}")


        url = urljoin(self.endpoint_uri, method)
        resp = await self.client.post(url, json=params, timeout=self.timeout)

        if self.use_api_key:
            if resp.status_code == 403 and b"Exceed the user daily usage" in resp.content:
                print("W:", resp.json().get("Error", "rate limit!"), file=sys.stderr)
                self._handle_rate_limit()
                return self.make_request(method, params)

        resp.raise_for_status()
        return resp.json()

    def _choose_proxy(self):
        return random.choice(self.proxies)

    def _choose_user_agent(self):
        return random.choice(self.user_agents)
    
    @property
    def random_api_key(self):
        return random.choice(self.api_key)
