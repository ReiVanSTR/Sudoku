import random
from typing import Union, List, Dict, Any
from tronpy.providers import HTTPProvider
from urllib.parse import urljoin
import sys

class ProxymityProvider(HTTPProvider):
    def __init__(
        self,
        endpoint_uri: str = None,
        timeout=None,
        api_key: Union[str, List[str]] = None,
        jw_token: str = None,
        proxies: List[Dict[str, str]] = None,
        user_agents: Union[List[str], str] = None,
    ):
        super().__init__(endpoint_uri, timeout, api_key, jw_token)

        # Преобразуем proxies и user_agents в списки
        self.proxies = list(proxies) if proxies else []
        self.user_agents = [user_agents] if isinstance(user_agents, str) else list(user_agents) if user_agents else []

    def make_request(self, method: str, params: Any = None) -> dict:
        if self.use_api_key:
            self.sess.headers["Tron-Pro-Api-Key"] = self.random_api_key

        if self.jw_token is not None:
            self.sess.headers["Authorization"] = f"Bearer {self.jw_token}"

        if params is None:
            params = {}

        # Используем случайные proxy и user-agent
        if self.proxies:
            self.sess.proxies = self._choose_proxy()
            # logger.info(f"Used proxy: {self.sess.proxies['http']}")

        if self.user_agents:
            self.sess.headers["User-Agent"] = self._choose_user_agent()
            # logger.info(f"Used agent: {self.sess.headers['User-Agent']}")


        url = urljoin(self.endpoint_uri, method)
        resp = self.sess.post(url, json=params, timeout=self.timeout)

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
