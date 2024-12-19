from api.tron.account import AsyncAccount
import asyncio


mnemonic = input("Mnemo: ")
async def main():

    acc = AsyncAccount(mnemonic)
    await acc.run_monitoring(threshold = 12, recipient_address = "TPXauFLfM89qAosiagcGT6WiYtGc8zqdQY")

asyncio.run(main())