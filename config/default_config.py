from abc import ABC, abstractmethod
from environs import Env
from dataclasses import dataclass

class DefaultConfig(ABC):

    @abstractmethod
    def from_env(env: Env) -> dataclass:
        """
        env_variable = env.str / env.int / env.bool
        """
        pass