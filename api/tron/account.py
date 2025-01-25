import logging
import time
import datetime
from pathlib import Path
from urllib3.exceptions import ReadTimeoutError
import random
import asyncio

from tronpy import AsyncTron, Tron
from tronpy.keys import PrivateKey
from dataclasses import dataclass
from trontxsize import get_tx_size

from config import Config
from .memonic import generate_tron_private_key
from .proxymity_provider import ProxymityProvider
from .async_proxymity_provider import AsyncProxymityProvider

from logger import setup_logging, tga_logger, broadcaster

config = Config.load_config()
setup_logging(loggig_level = logging.WARNING)


class Account:
    def __init__(self, mnemonic_phrase: str):
        if Path(mnemonic_phrase).is_file():
            with open(mnemonic_phrase, "r") as file:
                mnemonic_phrase = file.read()
        self.private_key = PrivateKey(bytes.fromhex(generate_tron_private_key(mnemonic_phrase)))
        self.public_key = self.private_key.public_key
        self.address = self.public_key.to_base58check_address()

        self.tron = Tron(provider = ProxymityProvider(
            timeout=1,
            api_key=config.tron.trongrid_api_keys,
            proxies=config.tron.proxies,
            user_agents=config.tron.useragents
        ))
    
    def get_bandwidth_price(self):
        try:
            response = self.tron.provider.make_request("wallet/getchainparameters")
            bandwidth_price = response['chainParameter'][3]['value'] / 1_000_000
            return bandwidth_price
        except Exception as e:
            logging.warning(f"Can't request current branwdth price. {e}")
        
    def calculate_transaction_fee(self, transaction):
        bandwidth_price = self.get_bandwidth_price()
        txsize = get_tx_size({"raw_data": transaction._raw_data, "signature": transaction._signature})
        resourse = self.tron.get_account_resource(self.address)
        available_brandwidth = resourse.get("freeNetLimit") - resourse.get("freeNetUsed")
        
        if available_brandwidth > txsize:
            return 0
        
        total_fee = txsize * bandwidth_price
        return total_fee
    
    def broadcast_transaction(self, recipient_address, amount):
        transaction = (
            self.tron.trx.transfer(self.address, recipient_address, int(amount * 1_000_000))
            .build()
            .sign(self.private_key)
        )
        transaction_fee = self.calculate_transaction_fee(transaction)
        new_amount = amount - transaction_fee
        
        return self.tron.trx.transfer(self.address, recipient_address, int(new_amount * 1_000_000)).build().sign(self.private_key).broadcast()
        
    def run_monitoring(self, recipient_address:str, min_amount: int, spread: int = 0, threshold: int = 1):
        while True:
            current_time = None
            try:
                current_time = datetime.datetime.now()
                balance = float(self.tron.get_account_balance(self.address))
                if balance > random.randint(min_amount - spread, min_amount + spread):
                    self.broadcast_transaction(recipient_address, balance)
                    logging.info(f"Successfull transfer {balance}")
                    tga_logger()
                if current_time + datetime.timedelta(seconds = 3) < datetime.datetime.now():
                    logging.warning("Too long request!")

            except ReadTimeoutError as e:
                logging.warning(f"Time out error {e}")

            except Exception as e:
                logging.warning(e)

            time.sleep(threshold)
    
    # def get_balance(self, max_attempts: int = 3, delay: float = 5.0):

    #     for attempt in range(max_attempts):
    #         try:
    #             response = requests.get(self.url, headers=self.headers)

    #             if response.status_code == 200:
    #                 data = response.json()
    #                 balance = data.get("balance", 0) / 1_000_000  # Конвертация Sun -> TRX
    #                 return balance
                
    #             if response.status_code == 429:  # Too Many Requests
    #                 logging.warning(f"Too many requests (429). Attempt {attempt + 1}/{max_attempts}. Retrying in 30 seconds...")

    #             else:
    #                 logging.error(f"Unexpected error: {response.status_code}. Response: {response.text}")
    #                 response.raise_for_status()

    #         except requests.RequestException as e:
    #             logging.error(f"Request failed: {e}. Attempt {attempt + 1}/{max_attempts}. Retrying in 30 seconds...")

    #         # Ожидание перед следующей попыткой
    #         if attempt < max_attempts - 1:
    #             time.sleep(delay)
        
    #     # Если все попытки исчерпаны, выбрасываем исключение
    #     raise requests.ConnectionError(f"Failed to fetch balance after {max_attempts} attempts")

    

    # def transaction(self, recipient_address, amount):
    #     client = Tron(provider=HTTPProvider(api_key=config.tron.trongrid_api_key))
    #     result = False

    #     attemps = 22
    #     counter = 1

    #     while not result and counter <= attemps:
    #         counter += 1
    #         try:
    #             # Create a transaction
    #             txn = (
    #                 client.trx.transfer(self.address, recipient_address, int(amount * 1_000_000))  # Convert TRX to SUN (1 TRX = 1,000,000 SUN)
    #                 .build()
    #                 .sign(self.private_key)
    #             )
                
    #             # Broadcast the transaction
    #             result = txn.broadcast()
                
    #             # Check the transaction result
    #             if result["result"]:
    #                 return AmountData(amount, counter, result['txid'])
                
    #             else:
    #                 logging.warning(f"Transaction failed! Attemps {counter}")
    #                 return False
                
    #         except Exception as e:
    #             amount -= 0.1

    # def run_monitoring(self, recipient_address, threshold = 1.0):

    #     while True:
    #         balance = self.get_balance()

    #         if balance > threshold:
    #             try:
    #                 result = self.transaction(recipient_address, balance)
    #                 if not result:
    #                     "call tgbot"
    #                     pass

    #                 if result:
    #                     logging.info(f"[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] Transaction successful! Amount: {result.amount}, Attempts: {result.attempts} ,TXID: {result.txid}")
                        
    #             except Exception as e:
    #                 logging.error(e)

    #         time.sleep(3)


class AsyncAccount:
    def __init__(self, mnemonic_phrase: str):
        if Path(mnemonic_phrase).is_file():
            with open(mnemonic_phrase, "r") as file:
                mnemonic_phrase = file.read()
        self.private_key = PrivateKey(bytes.fromhex(generate_tron_private_key(mnemonic_phrase)))
        self.public_key = self.private_key.public_key
        self.address = self.public_key.to_base58check_address()

        self.tron = AsyncTron(provider = AsyncProxymityProvider(
            timeout=5,
            api_key=config.tron.trongrid_api_keys,
            proxies=config.tron.proxies,
            user_agents=config.tron.useragents
        ))
    
    async def get_bandwidth_price(self):
        try:
            response = await self.tron.provider.make_request("wallet/getchainparameters")
            bandwidth_price = response['chainParameter'][3]['value'] / 1_000_000
            return bandwidth_price
        except Exception as e:
            await broadcaster(f"[WARNING] Can't request current branwdth price. \n{e.__str__() if not type(e) == str else e}")      
            logging.warning(f"Can't request current branwdth price. {e}")
        
    async def calculate_transaction_fee(self, transaction):
        bandwidth_price = await self.get_bandwidth_price()
        txsize = get_tx_size({"raw_data": transaction._raw_data, "signature": transaction._signature})
        resourse = await self.tron.get_account_resource(self.address)
        available_brandwidth = resourse.get("freeNetLimit") - resourse.get("freeNetUsed", 0)
        
        if available_brandwidth > txsize:
            return 0
        
        total_fee = txsize * bandwidth_price
        return total_fee
    
    async def broadcast_transaction(self, recipient_address, amount):
        transaction = (
            await self.tron.trx.transfer(self.address, recipient_address, int(amount * 1_000_000))
            .build()
        ).sign(self.private_key)
        transaction_fee = await self.calculate_transaction_fee(transaction)
        new_amount = amount - transaction_fee
        new_txn = await self.tron.trx.transfer(self.address, recipient_address, int(new_amount * 1_000_000)).build()
        return await new_txn.sign(self.private_key).broadcast()
        
    async def run_monitoring(self, recipient_address:str, min_amount: int, spread: int = 0, threshold: int = 1):
        while True:
            current_time = None
            try:
                current_time = datetime.datetime.now()
                balance = float(await self.tron.get_account_balance(self.address))
                if balance > random.randint(min_amount - spread, min_amount + spread):
                    await self.broadcast_transaction(recipient_address, balance)
                    await broadcaster(f"Successfull transfer {balance}")
                    logging.info(f"[INFO] Successfull transfer {balance}")
                if current_time + datetime.timedelta(seconds = 3) < datetime.datetime.now():
                    await broadcaster(f"[WARNING] Too long request!")
                    logging.warning("Too long request!")               
         
            except ReadTimeoutError as e:
                await broadcaster(f"[WARNING] Time out error \{e}")
                logging.warning(f"Time out error {e}")

            except Exception as e:
                await broadcaster(f"[ERROR] Time out error \n{e.__str__()}")
                logging.warning(e)

            await asyncio.sleep(threshold)
            

# class AsyncAccount:
    # def __init__(self, mnemonic_phrase: str):
    #     self.private_key = PrivateKey(bytes.fromhex(generate_tron_private_key(mnemonic_phrase)))
    #     self.public_key = self.private_key.public_key
    #     self.address = self.public_key.to_base58check_address()

    #     self.headers = {
    #         "Authorization": f"Bearer {config.tron.api_key}",
    #     }
    #     self.url = f"https://api.tronscan.org/api/account?address={self.address}"
    #     self.is_reconnection = False

    # async def get_balance(self, max_attempts: int = 3, delay: float = 30.0) -> float:
    #     for attempt in range(max_attempts):
    #         try:
    #             if self.is_reconnection:
    #                 logging.info(f"Trying to reconnect ...")

    #             async with aiohttp.ClientSession() as session:
    #                 async with session.get(self.url, headers=self.headers) as response:
    #                     if response.status == 200:
    #                         if self.is_reconnection:
    #                             self.is_reconnection = False
    #                             logging.info(f"Connection established!")

    #                         data = await response.json()
    #                         balance = data.get("balance", 0) / 1_000_000  # Конвертация Sun -> TRX
    #                         return balance

    #                     elif response.status == 429:  # Too Many Requests
    #                         logging.warning(
    #                             f"Too many requests (429). Attempt {attempt + 1}/{max_attempts}. Retrying in {delay} seconds..."
    #                         )
    #                     else:
    #                         logging.error(f"Unexpected error: {response.status}. Response: {await response.text()}")
    #                         response.raise_for_status()

    #         except aiohttp.ClientError as e:
    #             logging.error(f"Request failed: {e}. Attempt {attempt + 1}/{max_attempts}. Retrying in {delay*1.5*(attempt + 1)} seconds...")
    #             self.is_reconnection = True

    #         if attempt < max_attempts - 1:
    #             await asyncio.sleep(delay*1.5*(attempt + 1))

    #     raise aiohttp.ClientError(f"Failed to fetch balance after {max_attempts} attempts")

    # async def transaction(self, recipient_address: str, amount: float) -> AmountData | None:
    #     client = Tron(provider=HTTPProvider(api_key=config.tron.trongrid_api_key))
    #     result = False

    #     attempts = 22
    #     counter = 1

    #     while not result and counter <= attempts:
    #         counter += 1
    #         try:
    #             txn = (
    #                 client.trx.transfer(self.address, recipient_address, int(amount * 1_000_000))  # TRX -> SUN
    #                 .build()
    #                 .sign(self.private_key)
    #             )
    #             result = txn.broadcast()

    #             if result.get("result"):
    #                 return AmountData(amount, counter, result["txid"])

    #             else:
    #                 logging.warning(f"Transaction failed! Attempt {counter}")
    #                 return None

    #         except Exception as e:
    #             amount -= 0.1

    # async def run_monitoring(self, recipient_address: str, threshold: float = 1.0):
    #     logging.info("Starting monitoring...")
    #     while True:
    #         try:
    #             balance = await self.get_balance()
    #             if balance > threshold:
    #                 logging.info(f"Balance {balance:.2f} TRX exceeds threshold {threshold}. Initiating transaction...")
    #                 result = await self.transaction(recipient_address, balance)

    #                 if result:
    #                     logging.info(
    #                         f"Transaction successful! Amount: {result.amount}, Attempts: {result.attempts}, TXID: {result.txid}"
    #                     )
    #                 else:
    #                     logging.error("Transaction failed. Consider notifying via Telegram bot.")
    #         except Exception as e:
    #             logging.error(f"Error during monitoring: {e}")

    #         await asyncio.sleep(3)

