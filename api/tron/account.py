import requests
from threading import Thread
from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider

from config.read_env import load_config
from .memonic import generate_tron_private_key
import time
import datetime


class AmountException(ValueError):
    amount: float
    
    def __init__(self, amount: float):
        self.amount = amount

config = load_config(".env")


class Account:

    def __init__(self, mnemonic_phrase: str):
        self.private_key = PrivateKey(bytes.fromhex(generate_tron_private_key(mnemonic_phrase)))
        self.public_key = self.private_key.public_key
        self.address = self.public_key.to_base58check_address()

        self.headers = {
            "Authorization": f"Bearer {config.tron.api_key}"
        }
        self.url = f"https://api.tronscan.org/api/account?address={self.address}"

    def get_balance(self):
        for attemp in range(2):
            try:
                response = requests.get(self.url, self.headers)  # Если ключ передаётся через заголовок
            except:
                print(f"Too more connections, attemp {attemp+1}, sleep 30 sec")
                time.sleep(30)
                print(f"Continue...")

        
        
        if response.status_code == 200:
            data = response.json()
            balance = data.get("balance", 0) / 1_000_000  # Баланс в TRX (Sun -> TRX)
            return balance
        else:
            raise requests.ConnectionError(response)

    

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
                    print(f"[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] Transaction successful! Amount: {amount}, TXID: {result['txid']}")
                    result = True
                else:
                    print("Transaction failed!")
                    return False
            except Exception as e:
                amount -= 0.1

    def run_monitoring(self, recipient_address, threshold = 1.0):

        while True:
            balance = self.get_balance()

            if balance > threshold:
                try:
                    result = self.transaction(recipient_address, balance)
                except AmountException as Error:
                    pass

            time.sleep(3)