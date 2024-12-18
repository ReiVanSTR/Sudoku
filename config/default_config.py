from abc import ABC, abstractmethod
from environs import Env

class DefaultConfig(ABC):

    @abstractmethod
    def from_env(env: Env):
        """
        env_variable = env.str / env.int / env.bool
        """
        pass