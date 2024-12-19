import requests
import logging
import aiohttp
import asyncio
import logging
from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider
from dataclasses import dataclass

from config.read_env import load_config
from .memonic import generate_tron_private_key
import time
import datetime


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

config = load_config(".env")

@dataclass
class AmountData:
    amount: float
    attempts: int
    txid: str


class Account:

    def __init__(self, mnemonic_phrase: str):
        self.private_key = PrivateKey(bytes.fromhex(generate_tron_private_key(mnemonic_phrase)))
        self.public_key = self.private_key.public_key
        self.address = self.public_key.to_base58check_address()

        self.headers = {
            "Authorization": f"Bearer {config.tron.api_key}"
        }
        self.url = f"https://api.tronscan.org/api/account?address={self.address}"

    def get_balance(self, max_attempts: int = 3, delay: float = 30.0):

        for attempt in range(max_attempts):
            try:
                response = requests.get(self.url, headers=self.headers)

                if response.status_code == 200:
                    data = response.json()
                    balance = data.get("balance", 0) / 1_000_000  # Конвертация Sun -> TRX
                    return balance
                
                if response.status_code == 429:  # Too Many Requests
                    logger.warning(f"Too many requests (429). Attempt {attempt + 1}/{max_attempts}. Retrying in 30 seconds...")

                else:
                    logger.error(f"Unexpected error: {response.status_code}. Response: {response.text}")
                    response.raise_for_status()

            except requests.RequestException as e:
                logger.error(f"Request failed: {e}. Attempt {attempt + 1}/{max_attempts}. Retrying in 30 seconds...")

            # Ожидание перед следующей попыткой
            if attempt < max_attempts - 1:
                time.sleep(delay)
        
        # Если все попытки исчерпаны, выбрасываем исключение
        raise requests.ConnectionError(f"Failed to fetch balance after {max_attempts} attempts")

    

    def transaction(self, recipient_address, amount):
        client = Tron(provider=HTTPProvider(api_key=config.tron.trongrid_api_key))
        result = False

        attemps = 22
        counter = 1

        while not result and counter <= attemps:
            counter += 1
            try:
                # Create a transaction
                txn = (
                    client.trx.transfer(self.address, recipient_address, int(amount * 1_000_000))  # Convert TRX to SUN (1 TRX = 1,000,000 SUN)
                    .build()
                    .sign(self.private_key)
                )
                
                # Broadcast the transaction
                result = txn.broadcast()
                
                # Check the transaction result
                if result["result"]:
                    return AmountData(amount, counter, result['txid'])
                
                else:
                    logger.warning(f"Transaction failed! Attemps {counter}")
                    return False
                
            except Exception as e:
                amount -= 0.1

    def run_monitoring(self, recipient_address, threshold = 1.0):

        while True:
            balance = self.get_balance()

            if balance > threshold:
                try:
                    result = self.transaction(recipient_address, balance)
                    if not result:
                        "call tgbot"
                        pass

                    if result:
                        logger.info(f"[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] Transaction successful! Amount: {result.amount}, Attempts: {result.attempts} ,TXID: {result.txid}")
                        
                except Exception as e:
                    logger.error(e)

            time.sleep(3)




class AsyncAccount:
    def __init__(self, mnemonic_phrase: str):
        self.private_key = PrivateKey(bytes.fromhex(generate_tron_private_key(mnemonic_phrase)))
        self.public_key = self.private_key.public_key
        self.address = self.public_key.to_base58check_address()

        self.headers = {
            "Authorization": f"Bearer {config.tron.api_key}",
        }
        self.url = f"https://api.tronscan.org/api/account?address={self.address}"
        self.is_reconnection = False

    async def get_balance(self, max_attempts: int = 3, delay: float = 30.0) -> float:
        for attempt in range(max_attempts):
            try:
                if self.is_reconnection:
                    logger.info(f"Trying to reconnect ...")

                async with aiohttp.ClientSession() as session:
                    async with session.get(self.url, headers=self.headers) as response:
                        if response.status == 200:
                            if self.is_reconnection:
                                self.is_reconnection = False
                                logger.info(f"Connection established!")

                            data = await response.json()
                            balance = data.get("balance", 0) / 1_000_000  # Конвертация Sun -> TRX
                            return balance

                        elif response.status == 429:  # Too Many Requests
                            logger.warning(
                                f"Too many requests (429). Attempt {attempt + 1}/{max_attempts}. Retrying in {delay} seconds..."
                            )
                        else:
                            logger.error(f"Unexpected error: {response.status}. Response: {await response.text()}")
                            response.raise_for_status()

            except aiohttp.ClientError as e:
                logger.error(f"Request failed: {e}. Attempt {attempt + 1}/{max_attempts}. Retrying in {delay*1.5*(attempt + 1)} seconds...")
                self.is_reconnection = True

            if attempt < max_attempts - 1:
                await asyncio.sleep(delay*1.5*(attempt + 1))

        raise aiohttp.ClientError(f"Failed to fetch balance after {max_attempts} attempts")

    async def transaction(self, recipient_address: str, amount: float) -> AmountData | None:
        client = Tron(provider=HTTPProvider(api_key=config.tron.trongrid_api_key))
        result = False

        attempts = 22
        counter = 1

        while not result and counter <= attempts:
            counter += 1
            try:
                txn = (
                    client.trx.transfer(self.address, recipient_address, int(amount * 1_000_000))  # TRX -> SUN
                    .build()
                    .sign(self.private_key)
                )
                result = txn.broadcast()

                if result.get("result"):
                    return AmountData(amount, counter, result["txid"])

                else:
                    logger.warning(f"Transaction failed! Attempt {counter}")
                    return None

            except Exception as e:
                amount -= 0.1

    async def run_monitoring(self, recipient_address: str, threshold: float = 1.0):
        logger.info("Starting monitoring...")
        while True:
            try:
                balance = await self.get_balance()
                if balance > threshold:
                    logger.info(f"Balance {balance:.2f} TRX exceeds threshold {threshold}. Initiating transaction...")
                    result = await self.transaction(recipient_address, balance)

                    if result:
                        logger.info(
                            f"Transaction successful! Amount: {result.amount}, Attempts: {result.attempts}, TXID: {result.txid}"
                        )
                    else:
                        logger.error("Transaction failed. Consider notifying via Telegram bot.")
            except Exception as e:
                logger.error(f"Error during monitoring: {e}")

            await asyncio.sleep(3)

